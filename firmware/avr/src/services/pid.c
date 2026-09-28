#include "pid.h"
#include "outputs.h"
#include "lib/avr_delay/avr_delay.h"

static int32_t s_integral_x10;
static int16_t s_prev_err_x10;
static uint16_t s_win_start_ms;
static uint8_t s_bank_on;
static uint8_t s_sample_ready;

void pid_init(app_state_t *st)
{
    if (!st)
        return;
    /* Kp/Ki/Kd los pone cfg_load_global (EEPROM o cfg_store_defaults). */
    st->pid_loop = PID_OFF;
    st->duty_pct = 0;
    pid_reset(st);
}

void pid_reset(app_state_t *st)
{
    (void)st;
    s_integral_x10 = 0;
    s_prev_err_x10 = 0;
    s_win_start_ms = delay_ms();
    s_bank_on = 0;
    s_sample_ready = 0;
}

void pid_notify_sample(void)
{
    s_sample_ready = 1;
}

void pid_compute_sample(app_state_t *st)
{
    int16_t err_x10;
    int32_t out_x10;
    int16_t d_x10;
    int32_t i_term;
    uint8_t saturated;

    if (!st || !st->sensor.valid)
        return;

    if (st->pid_loop != PID_AUTO)
        return;

    /* T_set and T_act in ×10 (°C·10) — avoid float in hot path */
    err_x10 = (int16_t)((int16_t)st->t_set_c * 10 - st->sensor.temp_c_x10);

    /* Anti-windup: only integrate when not saturated against error sign */
    saturated = 0;
    if (st->duty_pct >= 100 && err_x10 > 0)
        saturated = 1;
    if (st->duty_pct == 0 && err_x10 < 0)
        saturated = 1;

    if (!saturated) {
        s_integral_x10 += err_x10; /* one sample ≈ 1 s */
        if (s_integral_x10 > 10000)
            s_integral_x10 = 10000;
        if (s_integral_x10 < -10000)
            s_integral_x10 = -10000;
    }

    d_x10 = (int16_t)(err_x10 - s_prev_err_x10);
    s_prev_err_x10 = err_x10;

    i_term = ((int32_t)st->pid_ki_x10 * (s_integral_x10 / 10));
    out_x10 = ((int32_t)st->pid_kp_x10 * err_x10
               + i_term
               + (int32_t)st->pid_kd_x10 * d_x10) / 10;

    if (out_x10 < 0)
        out_x10 = 0;
    if (out_x10 > 1000)
        out_x10 = 1000;

    st->duty_pct = (uint8_t)(out_x10 / 10);
}

void pid_window_tick(app_state_t *st)
{
    uint16_t now;
    uint16_t elapsed;
    uint16_t on_ms;

    if (!st)
        return;

    if (!st->sensor.valid) {
        if (s_bank_on) {
            outputs_bank_set(st->out_state, 0);
            s_bank_on = 0;
        }
        return;
    }

    if (st->pid_loop == PID_OFF) {
        st->duty_pct = 0;
        if (s_bank_on) {
            outputs_bank_set(st->out_state, 0);
            s_bank_on = 0;
        }
        return;
    }

    /* MAN: duty_pct set externally; AUTO: duty from compute_sample */

    now = delay_ms();
    elapsed = (uint16_t)(now - s_win_start_ms);
    if (elapsed >= PID_WINDOW_MS) {
        s_win_start_ms = now;
        elapsed = 0;
    }

    on_ms = (uint16_t)(((uint32_t)st->duty_pct * PID_WINDOW_MS) / 100u);

    if (st->duty_pct == 0) {
        if (s_bank_on) {
            outputs_bank_set(st->out_state, 0);
            s_bank_on = 0;
        }
    } else if (st->duty_pct >= 100) {
        if (!s_bank_on) {
            outputs_bank_set(st->out_state, 1);
            s_bank_on = 1;
        }
    } else if (elapsed < on_ms) {
        if (!s_bank_on) {
            outputs_bank_set(st->out_state, 1);
            s_bank_on = 1;
        }
    } else {
        if (s_bank_on) {
            outputs_bank_set(st->out_state, 0);
            s_bank_on = 0;
        }
    }
}

void pid_tick(app_state_t *st)
{
    if (!st)
        return;
    if (s_sample_ready) {
        s_sample_ready = 0;
        pid_compute_sample(st);
    }
    pid_window_tick(st);
}
