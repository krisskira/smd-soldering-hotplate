#include "pid.h"
#include "outputs.h"
#include "lib/avr_delay/avr_delay.h"

static int32_t s_integral_x10;
static int16_t s_prev_t_x10;
static int16_t s_rate_x10;
static uint16_t s_win_start_ms;
static uint8_t s_bank_on;
static uint8_t s_sample_ready;
static uint8_t s_have_prev;

void pid_init(app_state_t *st)
{
    if (!st)
        return;
    st->pid_loop = PID_OFF;
    st->duty_pct = 0;
    st->t_ref_x10 = 0;
    pid_reset(st);
}

void pid_reset(app_state_t *st)
{
    s_integral_x10 = 0;
    s_rate_x10 = 0;
    s_have_prev = 0;
    s_win_start_ms = delay_ms();
    s_bank_on = 0;
    s_sample_ready = 0;
    if (st && st->sensor.valid)
        st->t_ref_x10 = st->sensor.temp_c_x10;
}

void pid_notify_sample(void)
{
    s_sample_ready = 1;
}

void pid_compute_sample(app_state_t *st)
{
    int16_t t, err, ref, step;
    int32_t out, d;

    if (!st || !st->sensor.valid || st->pid_loop != PID_AUTO)
        return;

    t = st->sensor.temp_c_x10;
    if (s_have_prev)
        s_rate_x10 = (int16_t)((s_rate_x10 * 3 + (t - s_prev_t_x10)) / 4);
    else {
        s_rate_x10 = 0;
        st->t_ref_x10 = t;
        s_have_prev = 1;
    }
    s_prev_t_x10 = t;

    /* Gobernador: t_ref → t_set a RISE_C_X10_DEFAULT °C/s·10 */
    ref = st->t_ref_x10;
    step = (int16_t)(st->t_set_c * 10);
    if (ref < step) {
        ref = (int16_t)(ref + (int16_t)RISE_C_X10_DEFAULT);
        if (ref > step)
            ref = step;
    } else if (ref > step) {
        ref = (int16_t)(ref - (int16_t)RISE_C_X10_DEFAULT);
        if (ref < step)
            ref = step;
    }
    st->t_ref_x10 = ref;

    /* Predicción de cola: err = ref - (T + rate·lookahead) */
    d = (int32_t)s_rate_x10 * (int32_t)LOOKAHEAD_S_DEFAULT;
    if (d > 5000)
        d = 5000;
    if (d < -5000)
        d = -5000;
    err = (int16_t)(ref - (int16_t)(t + (int16_t)d));

    /* Anti-windup con duty previo */
    if (!((st->duty_pct >= 100 && err > 0) || (st->duty_pct == 0 && err < 0))) {
        s_integral_x10 += err;
        if (s_integral_x10 > 10000)
            s_integral_x10 = 10000;
        if (s_integral_x10 < -10000)
            s_integral_x10 = -10000;
    }

    out = ((int32_t)st->pid_kp_x10 * err
           + ((int32_t)st->pid_ki_x10 * s_integral_x10) / 100) / 10;
    if (out < 0)
        out = 0;
    if (out > 1000)
        out = 1000;
    st->duty_pct = (uint8_t)(out / 10);
}

void pid_window_tick(app_state_t *st)
{
    uint16_t now, elapsed, on_ms;
    uint8_t want = 0;

    if (!st)
        return;
    if (st->sensor.valid && st->pid_loop != PID_OFF) {
        now = delay_ms();
        elapsed = (uint16_t)(now - s_win_start_ms);
        if (elapsed >= PID_WINDOW_MS) {
            s_win_start_ms = now;
            elapsed = 0;
        }
        on_ms = (uint16_t)(((uint32_t)st->duty_pct * PID_WINDOW_MS) / 100u);
        want = (st->duty_pct >= 100) ? 1u
             : (st->duty_pct == 0) ? 0u
             : (elapsed < on_ms) ? 1u : 0u;
    } else
        st->duty_pct = 0;
    if (want != s_bank_on) {
        outputs_bank_set(st->out_state, want);
        s_bank_on = want;
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
