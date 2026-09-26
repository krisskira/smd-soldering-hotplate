#include "program.h"
#include "../outputs.h"
#include "../pid.h"
#include "../pid_atune.h"
#include "../telem_dirty.h"
#include "../cfg_store.h"
#include "../buzzer_seq.h"
#include "i18n/i18n_c.h"
#include "lib/avr_delay/avr_delay.h"
#include "lib/ports/ports.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

static uint16_t s_last_sec;
static prog_cb_t s_preheat_cb;

static void hold_enter(app_state_t *st)
{
    st->pid_loop = PID_AUTO;
    pid_reset(st);
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
    st->stabilize_left = st->stabilize_s;
    st->phase = PH_PREHEAT;
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
    if (!preheat_active(st) || !st->sensor.valid)
        return;
    err = (int16_t)((int16_t)(st->t_set_c * 10) - st->sensor.temp_c_x10);
    if (err < 0)
        err = (int16_t)(-err);
    if (st->phase == PH_PREHEAT) {
        if (err <= (int16_t)PREHEAT_BAND_C_X10) {
            st->phase = PH_STABILIZE;
            st->stabilize_left = st->stabilize_s;
            TELEM_DIRTY(st);
        }
    } else if (err > (int16_t)PREHEAT_BAND_C_X10) {
        st->phase = PH_PREHEAT;
        TELEM_DIRTY(st);
    } else if (st->stabilize_left > 0) {
        st->stabilize_left--;
    } else {
        preheat_fire(st, PROG_CB_OK);
    }
}

static void alarm_uart(uint8_t hold_heat)
{
    if (hold_heat)
        avr_uart_transmit_pstr(PSTR("ALARM:PREHEAT-SUCCESS\r\n"));
    else
        avr_uart_transmit_pstr(PSTR("ALARM:CYCLE-DONE\r\n"));
}

/* Alarma con o sin calor; finish=1 arranca bomba si cooldown_en */
static void alarm_start(app_state_t *st, uint8_t hold_heat, uint8_t finish)
{
    st->alarm_hold_heat = hold_heat ? 1u : 0u;
    if (!hold_heat)
        hold_leave(st);
    if (finish && st->cooldown_air_en) {
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
        alarm_uart(hold_heat);
}

static void after_alarm(app_state_t *st)
{
    if (st->alarm_hold_heat) {
        hold_leave(st);
        st->phase = PH_DONE;
        TELEM_DIRTY(st);
        return;
    }
    if (st->cooldown_air_en && st->sensor.valid
        && st->sensor.temp_c_x10 > (int16_t)(st->cooldown_target_c * 10)) {
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
    hold_enter(st);
    TELEM_DIRTY(st);
}

static void enter_finish(app_state_t *st)
{
    /* Alarma 1 min (o PRESS) + bomba ~40 °C */
    alarm_start(st, 0u, 1u);
}

static void enter_ramp_step(app_state_t *st);
static void after_preheat_pipeline(app_state_t *st);

static void enter_ramp_step(app_state_t *st)
{
    if (st->ramp_idx >= st->ramp_n || st->ramp_idx >= RAMP_STEPS_MAX) {
        enter_finish(st);
        return;
    }
    st->t_set_c = st->ramp_step[st->ramp_idx].temp_c;
    enter_run_timed(st, st->ramp_step[st->ramp_idx].hold_s);
}

static void after_preheat_pipeline(app_state_t *st)
{
    cfg_load_ramps(st);
    st->ramps_en = 1u;
    st->ramp_idx = 0;
    enter_ramp_step(st);
}

static void on_preheat_standalone(app_state_t *st, uint8_t result)
{
    if (result != PROG_CB_OK) {
        if (result == PROG_CB_FAULT)
            program_fault(st);
        return;
    }
    /* Mantener PID + alarma hasta PRESS o timeout */
    alarm_start(st, 1u, 0u);
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

    st->program = PROG_PREHEAT;
    st->phase = PH_IDLE;
    st->t_set_c = 150;
    st->delay_s = 60;
    st->run_s = 300;
    st->t_remain_s = 0;
    st->t_elapsed_s = 0;
    st->duty_pct = 0;
    st->preheat_en = 1;
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
    st->alarm_hold_heat = 0;
    st->cooldown_air_en = 1;
    st->cooldown_target_c = COOLDOWN_TARGET_C_DEFAULT;
    st->temp_limit_c = TEMP_LIMIT_C;
    st->device_mode = DEVICE_MANUAL;
    st->telem_dirty = 0;
    st->pid_kp_x10 = PID_KP_DEFAULT;
    st->pid_ki_x10 = PID_KI_DEFAULT;
    st->pid_kd_x10 = PID_KD_DEFAULT;
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

/* Punteros a literales en PROGMEM (usar con avr_uart_transmit_pstr). */
const char *program_token(program_id_t p)
{
    switch (p) {
    case PROG_START_IN: return PSTR("START_IN");
    case PROG_STOP_IN:  return PSTR("STOP_IN");
    case PROG_PREHEAT:  return PSTR("PREHEAT");
    case PROG_PID_TUNE: return PSTR("PID_TUNE");
    default:            return PSTR("PREHEAT");
    }
}

const char *program_action_token(const app_state_t *st)
{
    if (!st)
        return PSTR("IDLE");
    if (pid_atune_active(st))
        return PSTR("TUNING");
    switch (st->phase) {
    case PH_DELAY:     return PSTR("WAITING");
    case PH_PREHEAT:   return PSTR("PREHEATING");
    case PH_STABILIZE: return PSTR("STABILIZING");
    case PH_HOLD:      return PSTR("HOLDING");
    case PH_RUN:       return PSTR("RUNNING");
    case PH_COOLDOWN:  return PSTR("COOLING");
    case PH_ALARM:     return PSTR("ALARM");
    case PH_DONE:      return PSTR("DONE");
    case PH_FAULT:     return PSTR("FAULT");
    case PH_IDLE:
    default:           return PSTR("IDLE");
    }
}

const char *program_phase_name(process_phase_t p)
{
    switch (p) {
    case PH_DELAY:     return i18n_tr_hash(I18N_PHASE_WAIT);
    case PH_PREHEAT:   return i18n_tr_hash(I18N_PHASE_PREHEAT);
    case PH_STABILIZE: return i18n_tr_hash(I18N_PHASE_STABLE);
    case PH_HOLD:
    case PH_RUN:       return i18n_tr_hash(I18N_PHASE_RUN);
    case PH_COOLDOWN:
    case PH_DONE:      return i18n_tr_hash(I18N_PHASE_DONE);
    case PH_ALARM:     return i18n_tr_hash(I18N_PHASE_READY);
    case PH_FAULT:     return i18n_tr_hash(I18N_PHASE_FAULT);
    case PH_IDLE:
    default:           return i18n_tr_hash(I18N_PHASE_IDLE);
    }
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
    outputs_heaters_off(st->out_state);
    fan_off();
    st->out_state[OUT_FAN] = 0;
    st->phase = PH_FAULT;
    st->duty_pct = 0;
    st->ctrl_src = CTRL_NONE;
    TELEM_DIRTY(st);
    pid_reset(st);
}

void program_stop(app_state_t *st, ctrl_src_t src)
{
    if (!st)
        return;
    /* START_IN en HOLD/RUN: STOP pide final (alarma+bomba), no abort seco */
    if ((st->program == PROG_START_IN || st->program == PROG_STOP_IN)
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
    outputs_heaters_off(st->out_state);
    fan_off();
    st->out_state[OUT_FAN] = 0;
    st->phase = PH_IDLE;
    st->t_remain_s = 0;
    st->t_elapsed_s = 0;
    st->duty_pct = 0;
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

static void begin_pipeline(app_state_t *st)
{
    if (st->preheat_en)
        preheat_start(st, on_preheat_pipeline);
    else
        after_preheat_pipeline(st);
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
        pid_atune_start(st);
        TELEM_DIRTY(st);
        return PROG_OK;

    case PROG_PREHEAT:
        preheat_start(st, on_preheat_standalone);
        return PROG_OK;

    case PROG_START_IN:
        if (st->delay_s > 0) {
            st->t_remain_s = st->delay_s;
            st->phase = PH_DELAY;
            TELEM_DIRTY(st);
            return PROG_OK;
        }
        begin_pipeline(st);
        return PROG_OK;

    case PROG_STOP_IN:
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
        int16_t target = (int16_t)(st->cooldown_target_c * 10);
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
        || st->phase == PH_PREHEAT || st->phase == PH_STABILIZE
        || (st->phase == PH_ALARM && st->alarm_hold_heat))
        pid_tick(st);

    now = delay_ms();
    if ((uint16_t)(now - s_last_sec) >= 1000u) {
        s_last_sec = now;
        if (program_is_active(st) || st->phase == PH_DONE)
            on_second(st);
    }
}
