/*
 * HotPanel en el host, fotograma a fotograma. Enlaza el home_view.c real del
 * firmware (como tools/ui_screens) y dibuja un estado por línea de stdin:
 *
 *   phase temp_x10 ramp_idx t_set_c t_remain_s t_elapsed_s
 *
 * Por cada línea escribe en stdout 128×64 bytes (0 = apagado, 1 = encendido).
 */
#include <stdio.h>
#include <string.h>

#include "src/ui/home_view.h"
#include "src/services/process.h"
#include "src/services/cfg_store.h"
#include "src/services/buzzer_seq.h"
#include "src/services/device_session.h"
#include "i18n/i18n_c.h"
#include "lib/st7920/st7920.h"
#include <avr/pgmspace.h>

static unsigned char fb[64][128];

void st7920_write_gdram(uint8_t x, uint8_t y, uint8_t hi, uint8_t lo)
{
    uint8_t i;

    if (x >= 8u || y >= 64u)
        return;
    for (i = 0; i < 8u; i++) {
        fb[y][x * 16u + i] = (uint8_t)((hi >> (7u - i)) & 1u);
        fb[y][x * 16u + 8u + i] = (uint8_t)((lo >> (7u - i)) & 1u);
    }
}

void st7920_clear_gdram(void)
{
    memset(fb, 0, sizeof fb);
}

void cfg_load_ramps(app_state_t *st) { (void)st; }
void cfg_load_program(app_state_t *st, program_id_t prog) { (void)st; (void)prog; }
void cfg_save_ramps(const app_state_t *st) { (void)st; }
void cfg_save_program(const app_state_t *st, program_id_t prog) { (void)st; (void)prog; }
void delay_clamp(app_state_t *st) { (void)st; }
void buzzer_seq_beep_cat(beep_cat_t cat, uint8_t count) { (void)cat; (void)count; }

uint8_t device_session_is_usb(const app_state_t *st)
{
    return (st && st->device_mode == DEVICE_USB) ? 1u : 0u;
}

void device_session_leave_manual(app_state_t *st, uint8_t notify_abort)
{
    (void)notify_abort;
    st->device_mode = DEVICE_MANUAL;
}

void device_session_safe_stop(app_state_t *st, ctrl_src_t src)
{
    (void)src;
    st->phase = PH_IDLE;
}

uint8_t program_start(app_state_t *st, ctrl_src_t src)
{
    (void)src;
    st->phase = PH_RUN;
    return PROG_OK;
}

uint8_t program_user_ack(app_state_t *st)
{
    (void)st;
    return 0u;
}

/* Mismo criterio que program_runner.c. */
uint8_t program_is_active(const app_state_t *st)
{
    switch (st->phase) {
    case PH_DELAY:
    case PH_HOLD:
    case PH_RUN:
    case PH_COOLDOWN:
    case PH_ALARM:
        return 1u;
    default:
        return 0u;
    }
}

const char *program_phase_name(process_phase_t p)
{
    static const uint8_t ids[] = {
        I18N_PHASE_IDLE, I18N_PHASE_WAIT, I18N_PHASE_PREHEAT,
        I18N_PHASE_STABLE, I18N_PHASE_RUN, I18N_PHASE_RUN,
        I18N_PHASE_COOL, I18N_PHASE_READY, I18N_PHASE_DONE,
        I18N_PHASE_FAULT
    };
    uint8_t i = (uint8_t)p;

    if (i >= (uint8_t)sizeof(ids))
        i = 0u;
    return i18n_tr_hash(ids[i]);
}

/* Perfil de hotplate_heat_trace-4.csv: 100/30 · 110/60 · 120/30 · 130/30. */
static void profile(app_state_t *s)
{
    memset(s, 0, sizeof *s);
    s->sensor.valid = 1u;
    s->temp_min_c = 50u;
    s->temp_max_c = 210u;
    s->ramp_n = 4u;
    s->ramp_step[0].temp_c = 100u; s->ramp_step[0].hold_s = 30u;
    s->ramp_step[1].temp_c = 110u; s->ramp_step[1].hold_s = 60u;
    s->ramp_step[2].temp_c = 120u; s->ramp_step[2].hold_s = 30u;
    s->ramp_step[3].temp_c = 130u; s->ramp_step[3].hold_s = 30u;
    s->program = PROG_HEAT;
    s->device_mode = DEVICE_MANUAL;
}

int main(void)
{
    static app_state_t s;
    int phase, temp, ramp, set, remain, elapsed;

    profile(&s);
    home_view_enter(&s);
    while (scanf("%d %d %d %d %d %d", &phase, &temp, &ramp, &set, &remain, &elapsed) == 6) {
        s.phase = (process_phase_t)phase;
        s.sensor.temp_c_x10 = (int16_t)temp;
        s.ramp_idx = (uint8_t)ramp;
        s.t_set_c = (uint16_t)set;
        s.t_remain_s = (uint16_t)remain;
        s.t_elapsed_s = (uint16_t)elapsed;
        s.row_dirty = HOME_DIRTY_ALL;
        home_view_refresh(&s);
        fwrite(fb, 1, sizeof fb, stdout);
    }
    return 0;
}
