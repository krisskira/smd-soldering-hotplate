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

static void hold_enter(app_state_t *st)
{
    /* PI AUTO: approach y meseta. Sin pid_reset (I bumpless). */
    st->pid_loop = PID_AUTO;
}

static void hold_leave(app_state_t *st)
{
    st->pid_loop = PID_OFF;
    st->duty_pct = 0;
    outputs_heaters_off(st->out_state);
}

/* |T−SET| ≤ lim (°C·10). Caller garantiza sensor.valid. */
static uint8_t in_band_x10(const app_state_t *st, int16_t lim)
{
    int16_t err = (int16_t)((int16_t)(st->t_set_c * 10) - st->sensor.temp_c_x10);
    if (err < 0)
        err = (int16_t)(-err);
    return (err <= lim) ? 1u : 0u;
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
    buzzer_seq_beep_cat(BEEP_READY, 3);
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
        buzzer_seq_beep_cat(BEEP_READY, 2);
        TELEM_DIRTY(st);
        st->alarm_beep_left_s = period;
    }
    if (st->alarm_left_s == 0)
        after_alarm(st);
}

static void enter_run_timed(app_state_t *st, uint16_t sec)
{
    st->t_remain_s = sec;
    /* PH_RUN: PI a SET (t_ref+lookahead). hold_s solo en PH_HOLD tras banda. */
    st->phase = PH_RUN;
    hold_enter(st);
    pid_on_set_step(st);
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

static void enter_ramp_step(app_state_t *st)
{
    if (st->ramp_idx >= st->ramp_n || st->ramp_idx >= RAMP_STEPS_MAX) {
        enter_finish(st);
        return;
    }
    st->t_set_c = st->ramp_step[st->ramp_idx].temp_c;
    enter_run_timed(st, st->ramp_step[st->ramp_idx].hold_s);
}

void program_init(app_state_t *st)
{
    uint8_t i;

    if (!st)
        return;

    st->program = PROG_HEAT;
    st->phase = PH_IDLE;
    st->t_set_c = 150;
    st->delay_h = 0;
    st->delay_m = 1;
    st->dly_h = 0;
    st->dly_m = 0;
    st->dly_s = 0;
    st->t_remain_s = 0;
    st->t_elapsed_s = 0;
    st->duty_pct = 0;
    st->t_ref_x10 = 0;
    st->preheat_band_c = PREHEAT_BAND_C_DEFAULT;
    st->preheat_band_exit_c = PREHEAT_BAND_EXIT_C_DEFAULT;
    st->ramps_en = 1;
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
            || st->phase == PH_DELAY)) {
        enter_finish(st);
        st->ctrl_src = src;
        return;
    }
    if (pid_atune_active(st))
        pid_atune_cancel(st);
    hold_leave(st);
    fan_off();
    st->out_state[OUT_FAN] = 0;
    st->phase = PH_IDLE;
    st->t_remain_s = 0;
    st->dly_h = 0;
    st->dly_m = 0;
    st->dly_s = 0;
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

/* HEAT: delay ya cumplido → rampa 1 a su temperatura, luego 2..n. */
static void begin_pipeline(app_state_t *st)
{
    cfg_load_ramps(st);
    st->ramps_en = 1u;
    if (st->ramp_n == 0u)
        st->ramp_n = 1u;
    st->ramp_idx = 0;
    pid_reset(st);
    enter_ramp_step(st);
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
        if (st->delay_h != 0u || st->delay_m != 0u) {
            st->dly_h = st->delay_h;
            st->dly_m = st->delay_m;
            st->dly_s = 0;
            st->t_remain_s = delay_cfg_s(st);
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
        /* Un byte de segundos dentro del minuto; hora y minuto no crecen con las 12 h. */
        if (st->dly_s < 59u)
            st->dly_s++;
        else {
            st->dly_s = 0;
            if (st->dly_m > 0u)
                st->dly_m--;
            else if (st->dly_h > 0u) {
                st->dly_h--;
                st->dly_m = 59u;
            }
        }
        {
            uint16_t left = (uint16_t)((uint16_t)st->dly_h * 3600u
                                       + (uint16_t)st->dly_m * 60u);
            st->t_remain_s = (left >= st->dly_s)
                                 ? (uint16_t)(left - st->dly_s) : 0u;
        }
        if (st->dly_h == 0u && st->dly_m == 0u && st->dly_s == 0u)
            begin_pipeline(st);
    } else if (st->phase == PH_RUN) {
        /* Approach PI; meseta al entrar ±band_c. */
        if (in_band_x10(st, (int16_t)((uint16_t)st->preheat_band_c * 10u)))
            st->phase = PH_HOLD;
    } else if (st->phase == PH_HOLD) {
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

    if (st->phase == PH_HOLD || st->phase == PH_RUN)
        pid_tick(st);

    now = delay_ms();
    if ((uint16_t)(now - s_last_sec) >= 1000u) {
        s_last_sec = now;
        if (program_is_active(st) || st->phase == PH_DONE)
            on_second(st);
    }
}
