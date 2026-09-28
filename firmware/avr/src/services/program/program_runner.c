#include "program.h"
#include "../outputs.h"
#include "../pid.h"
#include "../pid_atune.h"
#include "../telem_dirty.h"
#include "../cfg_store.h"
#include "../buzzer_seq.h"
#include "../at_cmd.h"
#include "../proto_codes.h"
#include "i18n/i18n_c.h"
#include "lib/avr_delay/avr_delay.h"
#include "lib/ports/ports.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

static uint16_t s_last_sec;
static prog_cb_t s_preheat_cb;
/* 0 = sin cola. 1 = timeout vencido. >1 = segundos que faltan. */
static uint8_t s_over_left;

static void hold_enter(app_state_t *st)
{
    /* Bumpless: no pid_reset entre etapas; t_ref e I siguen. */
    st->pid_loop = PID_AUTO;
}

static void hold_leave(app_state_t *st)
{
    st->pid_loop = PID_OFF;
    st->duty_pct = 0;
    outputs_heaters_off(st->out_state);
}

static uint8_t preheat_active(const app_state_t *st)
{
    return (st && (st->phase == PH_PREHEAT || st->phase == PH_STABILIZE)) ? 1u : 0u;
}

static void preheat_fire(app_state_t *st, uint8_t result)
{
    prog_cb_t cb = s_preheat_cb;
    s_preheat_cb = 0;
    if (cb)
        cb(st, result);
}

static void preheat_start(app_state_t *st, prog_cb_t cb)
{
    s_preheat_cb = cb;
    s_over_left = 0;
    st->stabilize_left = st->stabilize_s;
    st->phase = PH_PREHEAT;
    pid_reset(st);
    hold_enter(st);
    TELEM_DIRTY(st);
}

static void preheat_cancel(app_state_t *st)
{
    if (!preheat_active(st))
        return;
    hold_leave(st);
    preheat_fire(st, PROG_CB_CANCEL);
}

static void preheat_tick(app_state_t *st)
{
    int16_t err;
    int16_t t;

    if (!preheat_active(st) || !st->sensor.valid)
        return;
    t = st->sensor.temp_c_x10;
    err = (int16_t)((int16_t)(st->t_set_c * 10) - t);
    /* Cola: pasó el tope + 2 °C, o el timeout sigue y T aún > tope. */
    if (err < -(int16_t)PREHEAT_BAND_C_X10 || (s_over_left && err < 0)) {
        st->phase = PH_PREHEAT;
        if (s_over_left == 0)
            s_over_left = PREHEAT_OVERHEAT_S;
        else if (s_over_left > 1)
            s_over_left--;
        else if (t < (int16_t)(st->ramp_step[0].temp_c * 10)) {
            s_over_left = 0;
            preheat_fire(st, PROG_CB_OK);
        }
        return;
    }
    s_over_left = 0;
    if (err < 0)
        err = (int16_t)(-err);
    if (st->phase == PH_PREHEAT) {
        if (err <= (int16_t)PREHEAT_BAND_C_X10) {
            st->phase = PH_STABILIZE;
            st->stabilize_left = st->stabilize_s;
        }
    } else if (err > (int16_t)PREHEAT_BAND_C_X10) {
        st->phase = PH_PREHEAT;
    } else if (st->stabilize_left > 0) {
        st->stabilize_left--;
    } else {
        preheat_fire(st, PROG_CB_OK);
    }
}

/* Fin de HEAT: PTC off, aire si está habilitado, ALARM:2. */
static void alarm_start(app_state_t *st)
{
    hold_leave(st);
    if (st->cooldown_air_en) {
        fan_on();
        st->out_state[OUT_FAN] = 1;
    }
    st->phase = PH_ALARM;
    st->alarm_left_s = st->alarm_duration_s
        ? st->alarm_duration_s : ALARM_DURATION_S_DEFAULT;
    st->alarm_beep_left_s = 0;
    TELEM_DIRTY(st);
    buzzer_seq_beep_cat(st, BEEP_READY, 3);
    if (st->device_mode == DEVICE_USB)
        proto_emit_alarm((uint8_t)PROTO_ALARM_DONE);
}

static void after_alarm(app_state_t *st)
{
    if (st->cooldown_air_en && st->sensor.valid
        && st->sensor.temp_c_x10 > (int16_t)(st->temp_min_c * 10)) {
        st->phase = PH_COOLDOWN;
        TELEM_DIRTY(st);
    } else {
        fan_off();
        st->out_state[OUT_FAN] = 0;
        st->phase = PH_DONE;
        TELEM_DIRTY(st);
    }
}

static void alarm_on_second(app_state_t *st)
{
    uint16_t period;
    if (st->phase != PH_ALARM)
        return;
    if (st->alarm_left_s > 0)
        st->alarm_left_s--;
    period = st->alarm_period_s ? st->alarm_period_s : ALARM_PERIOD_S_DEFAULT;
    if (st->alarm_beep_left_s > 0)
        st->alarm_beep_left_s--;
    else {
        buzzer_seq_beep_cat(st, BEEP_READY, 2);
        TELEM_DIRTY(st);
        st->alarm_beep_left_s = period;
    }
    if (st->alarm_left_s == 0)
        after_alarm(st);
}

static void enter_run_timed(app_state_t *st, uint16_t sec)
{
    st->t_remain_s = sec;
    st->phase = PH_RUN;
    /* hold_s corre desde el instante de entrada (reloj de pared). */
    hold_enter(st);
    TELEM_DIRTY(st);
}

/* Ramp1..n no decrecientes (fan solo en cooldown). */
static uint8_t ramps_ok(const app_state_t *st)
{
    uint8_t i;
    for (i = 1u; i < st->ramp_n && i < RAMP_STEPS_MAX; i++) {
        if (st->ramp_step[i].temp_c < st->ramp_step[i - 1u].temp_c)
            return 0u;
    }
    return 1u;
}

static void enter_finish(app_state_t *st)
{
    /* Alarma 1 min (o PRESS) + bomba hasta temp_min_c */
    alarm_start(st);
}

static void enter_ramp_step(app_state_t *st);
static void after_preheat_pipeline(app_state_t *st);

/* Tope de PREHEAT/STABILIZE en HEAT: pct% de T(Ramp1). 250*100 cabe en u16. */
static uint16_t preheat_cap_c(const app_state_t *st, uint16_t full_c)
{
    uint8_t pct = st->preheat_pct;
    uint16_t t;

    if (pct < PREHEAT_PCT_LO || pct > PREHEAT_PCT_HI)
        pct = PREHEAT_PCT_DEFAULT;
    t = (uint16_t)(((uint16_t)full_c * (uint16_t)pct) / 100u);
    if (t < st->temp_min_c)
        t = st->temp_min_c;
    if (t > full_c)
        t = full_c;
    return t;
}

static void enter_ramp_step(app_state_t *st)
{
    if (st->ramp_idx >= st->ramp_n || st->ramp_idx >= RAMP_STEPS_MAX) {
        enter_finish(st);
        return;
    }
    st->t_set_c = st->ramp_step[st->ramp_idx].temp_c;
    enter_run_timed(st, st->ramp_step[st->ramp_idx].hold_s);
}

/* Tras estabilizar en el tope (pct% de Ramp1): corre Ramp1..n a T plena. */
static void after_preheat_pipeline(app_state_t *st)
{
    cfg_load_ramps(st);
    st->ramps_en = 1u;
    st->ramp_idx = 0;
    enter_ramp_step(st);
}

static void on_preheat_pipeline(app_state_t *st, uint8_t result)
{
    if (result != PROG_CB_OK) {
        if (result == PROG_CB_FAULT)
            program_fault(st);
        return;
    }
    after_preheat_pipeline(st);
}

void program_init(app_state_t *st)
{
    uint8_t i;

    if (!st)
        return;

    st->program = PROG_HEAT;
    st->phase = PH_IDLE;
    st->t_set_c = 150;
    st->delay_s = 60;
        st->t_remain_s = 0;
    st->t_elapsed_s = 0;
    st->duty_pct = 0;
    st->t_ref_x10 = 0;
    st->preheat_en = 1;
    st->preheat_pct = PREHEAT_PCT_DEFAULT;
    st->ramps_en = 1;
    st->stabilize_s = PREHEAT_STABLE_S_DEFAULT;
    st->stabilize_left = 0;
    st->ramp_n = 2;
    st->ramp_idx = 0;
    for (i = 0; i < RAMP_STEPS_MAX; i++) {
        st->ramp_step[i].temp_c = (uint16_t)(100u + (uint16_t)i * 25u);
        st->ramp_step[i].hold_s = 60;
    }
    st->alarm_duration_s = ALARM_DURATION_S_DEFAULT;
    st->alarm_period_s = ALARM_PERIOD_S_DEFAULT;
    st->alarm_left_s = 0;
    st->alarm_beep_left_s = 0;
    st->cooldown_air_en = 1;
    st->temp_min_c = TEMP_MIN_C_DEFAULT;
    st->temp_max_c = TEMP_MAX_C_DEFAULT;
    st->atune_cycles_target = ATUNE_CYCLES_DEFAULT;
    st->atune_hyst_c_x10 = ATUNE_HYST_C_X10;
    st->atune_max_s = ATUNE_MAX_S_DEFAULT;
    st->atune_stream = 0;
        st->device_mode = DEVICE_MANUAL;
    st->telem_dirty = 0;
    st->pid_loop = PID_OFF;
    st->atune_phase = ATUNE_IDLE;
    st->buzz_nav_en = 1;
    st->buzz_nav_reps = 1;
    st->usb_last_ok = 1;
    st->ctrl_src = CTRL_NONE;
    st->home_page = HOME_PAGE_MENU;
    st->home_sel = 0;
    s_last_sec = delay_ms();
    pid_init(st);
}

uint8_t program_is_active(const app_state_t *st)
{
    if (!st)
        return 0;
    switch (st->phase) {
    case PH_DELAY:
    case PH_PREHEAT:
    case PH_STABILIZE:
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
    /* Índice = process_phase_t; PH_HOLD comparte RUN. */
    static const uint8_t ids[] PROGMEM = {
        I18N_PHASE_IDLE, I18N_PHASE_WAIT, I18N_PHASE_PREHEAT,
        I18N_PHASE_STABLE, I18N_PHASE_RUN, I18N_PHASE_RUN,
        I18N_PHASE_COOL, I18N_PHASE_READY, I18N_PHASE_DONE,
        I18N_PHASE_FAULT
    };
    uint8_t i = (uint8_t)p;

    if (i >= (uint8_t)(sizeof(ids) / sizeof(ids[0])))
        i = 0u;
    return i18n_tr_hash(pgm_read_byte(&ids[i]));
}

void program_fault(app_state_t *st)
{
    if (!st)
        return;
    if (pid_atune_active(st))
        pid_atune_cancel(st);
    if (preheat_active(st))
        preheat_cancel(st);
    hold_leave(st);
    fan_off();
    st->out_state[OUT_FAN] = 0;
    st->phase = PH_FAULT;
    st->ctrl_src = CTRL_NONE;
    TELEM_DIRTY(st);
    pid_reset(st);
}

void program_stop(app_state_t *st, ctrl_src_t src)
{
    if (!st)
        return;
    /* AT+STOP (USB): cierra HEAT como fin → ALARM:2. UI Cancel: abort → IDLE. */
    if (src == CTRL_USB && st->program == PROG_HEAT
        && (st->phase == PH_HOLD || st->phase == PH_RUN
            || st->phase == PH_PREHEAT || st->phase == PH_STABILIZE
            || st->phase == PH_DELAY)) {
        if (preheat_active(st))
            preheat_cancel(st);
        enter_finish(st);
        st->ctrl_src = src;
        return;
    }
    if (preheat_active(st))
        preheat_cancel(st);
    if (pid_atune_active(st))
        pid_atune_cancel(st);
    hold_leave(st);
    fan_off();
    st->out_state[OUT_FAN] = 0;
    st->phase = PH_IDLE;
    st->t_remain_s = 0;
    st->t_elapsed_s = 0;
    st->ctrl_src = src;
    TELEM_DIRTY(st);
    pid_reset(st);
}

uint8_t program_user_ack(app_state_t *st)
{
    if (!st || st->phase != PH_ALARM)
        return 0;
    after_alarm(st);
    return 1;
}

/*
 * HEAT: si preheat_en, PREHEAT/STABILIZE al pct% de T(Ramp1);
 * si no, RUN Ramp1 a temperatura plena. Luego Ramp1..n → aire a temp_min.
 */
static void begin_pipeline(app_state_t *st)
{
    cfg_load_ramps(st);
    st->ramps_en = 1u;
    if (st->ramp_n == 0u)
        st->ramp_n = 1u;
    if (!st->preheat_en) {
        st->ramp_idx = 0;
        pid_reset(st);
        enter_ramp_step(st);
        return;
    }
    st->t_set_c = preheat_cap_c(st, st->ramp_step[0].temp_c);
    preheat_start(st, on_preheat_pipeline);
}

uint8_t program_start(app_state_t *st, ctrl_src_t src)
{
    if (!st)
        return PROG_ERR_PARAM;
    if (st->phase == PH_FAULT)
        return PROG_ERR_FAULT;
    if (program_is_active(st) || pid_atune_active(st))
        return PROG_ERR_BUSY;
    if (!st->sensor.valid)
        return PROG_ERR_SENSOR;

    cfg_load_program(st, st->program);

    st->ctrl_src = src;
    st->t_elapsed_s = 0;
    s_last_sec = delay_ms();

    switch (st->program) {
    case PROG_PID_TUNE:
        if (pid_atune_start(st) != 0u)
            return PROG_ERR_PARAM;
        at_cmd_set_stream(st, (uint8_t)(src == CTRL_USB ? 1u : 0u));
        TELEM_DIRTY(st);
        return PROG_OK;

    case PROG_HEAT:
        cfg_load_ramps(st);
        if (st->ramp_n < 1u || !ramps_ok(st))
            return PROG_ERR_PARAM;
        if (st->delay_s > 0) {
            st->t_remain_s = st->delay_s;
            st->phase = PH_DELAY;
            TELEM_DIRTY(st);
            return PROG_OK;
        }
        begin_pipeline(st);
        return PROG_OK;

    default:
        return PROG_ERR_PARAM;
    }
}

uint8_t program_set_output(app_state_t *st, uint8_t idx, uint8_t on,
                           ctrl_src_t src)
{
    if (!st || idx >= OUTPUT_COUNT)
        return 0;
    if (program_is_active(st) || pid_atune_active(st))
        return 0;
    st->ctrl_src = src;
    output_set(st->out_state, idx, on);
    TELEM_DIRTY(st);
    return 1;
}

uint8_t program_set_bank(app_state_t *st, uint8_t on, ctrl_src_t src)
{
    if (!st)
        return 0;
    if (program_is_active(st) || pid_atune_active(st))
        return 0;
    st->ctrl_src = src;
    outputs_bank_set(st->out_state, on);
    TELEM_DIRTY(st);
    return 1;
}

static void on_second(app_state_t *st)
{
    process_phase_t prev = st->phase;

    if (program_is_active(st) && st->t_elapsed_s < 0xFFFFu)
        st->t_elapsed_s++;

    if (st->phase == PH_ALARM) {
        alarm_on_second(st);
        goto done;
    }

    if (st->phase == PH_DELAY) {
        if (st->t_remain_s > 0)
            st->t_remain_s--;
        if (st->t_remain_s == 0)
            begin_pipeline(st);
    } else if (preheat_active(st)) {
        preheat_tick(st);
    } else if (st->phase == PH_RUN) {
        if (st->t_remain_s > 0)
            st->t_remain_s--;
        if (st->t_remain_s == 0) {
            st->ramp_idx++;
            enter_ramp_step(st);
        }
    } else if (st->phase == PH_COOLDOWN) {
        int16_t target = (int16_t)(st->temp_min_c * 10);
        if (st->sensor.valid && st->sensor.temp_c_x10 <= target) {
            fan_off();
            st->out_state[OUT_FAN] = 0;
            st->phase = PH_DONE;
        }
    }

done:
    if (st->phase != prev)
        TELEM_DIRTY(st);
}

void program_tick(app_state_t *st)
{
    uint16_t now;

    if (!st)
        return;

    if (program_is_active(st) && !st->sensor.valid
        && st->phase != PH_ALARM && st->phase != PH_DELAY) {
        program_fault(st);
        return;
    }

    if (st->phase == PH_HOLD || st->phase == PH_RUN
        || st->phase == PH_PREHEAT || st->phase == PH_STABILIZE)
        pid_tick(st);

    now = delay_ms();
    if ((uint16_t)(now - s_last_sec) >= 1000u) {
        s_last_sec = now;
        if (program_is_active(st) || st->phase == PH_DONE)
            on_second(st);
    }
}
