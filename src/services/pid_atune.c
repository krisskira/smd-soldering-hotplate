#include "pid_atune.h"
#include "pid.h"
#include "outputs.h"
#include "at_cmd.h"
#include "lib/avr_delay/avr_delay.h"

/*
 * Autotune bang-bang SSR (Åström–Hägglund) → Ziegler–Nichols.
 * Salida: MOC3021 + BT136. Ciclos/hyst desde app_state (EEPROM v5).
 */

static int16_t  s_peak_hi;
static int16_t  s_peak_lo;
static uint16_t s_half_sum;
static uint8_t  s_half_n;
static uint16_t s_t0;

static void heaters_off(app_state_t *st)
{
    outputs_bank_set(st->out_state, 0);
    st->duty_pct = 0;
    st->atune_relay_on = 0;
}

static void publish_peaks(app_state_t *st)
{
    st->atune_peak_hi_x10 = s_peak_hi;
    st->atune_peak_lo_x10 = s_peak_lo;
}

void pid_atune_init(app_state_t *st)
{
    if (!st)
        return;
    st->atune_phase = ATUNE_IDLE;
    st->atune_cycles = 0;
    st->atune_relay_on = 0;
    st->atune_elapsed_s = 0;
    st->atune_kp_x10 = 0;
    st->atune_ki_x10 = 0;
    st->atune_kd_x10 = 0;
    st->atune_peak_hi_x10 = 0;
    st->atune_peak_lo_x10 = 0;
    at_cmd_set_stream(st, 0);
}

void pid_atune_cancel(app_state_t *st)
{
    if (!st)
        return;
    heaters_off(st);
    st->atune_phase = ATUNE_IDLE;
    at_cmd_set_stream(st, 0);
    pid_reset(st);
}

uint8_t pid_atune_active(const app_state_t *st)
{
    return (st && st->atune_phase == ATUNE_RUN) ? 1u : 0u;
}

void pid_atune_start(app_state_t *st)
{
    int16_t t;

    if (!st || !st->sensor.valid)
        return;
    if (st->sensor.temp_c_x10 >= (int16_t)(st->temp_max_c * 10))
        return;
    if (st->t_set_c < st->temp_min_c
        || st->t_set_c > (uint16_t)(st->temp_max_c - 10u))
        return;

    pid_atune_cancel(st);
    st->atune_phase = ATUNE_RUN;
    st->atune_cycles = 0;
    st->atune_elapsed_s = 0;
    st->atune_relay_on = 1;
    st->duty_pct = 100;
    outputs_bank_set(st->out_state, 1);

    t = st->sensor.temp_c_x10;
    s_peak_hi = t;
    s_peak_lo = t;
    st->atune_peak_hi_x10 = t;
    st->atune_peak_lo_x10 = t;
    s_half_sum = 0;
    s_half_n = 0;
    s_t0 = delay_ms();
}

static void finish_ok(app_state_t *st, uint16_t tu_ms, int16_t amp)
{
    int32_t ku, kp, ki, kd, tu10;

    if (amp < 5)
        amp = 5;
    ku = 12732L / (int32_t)amp;
    if (ku < 1)
        ku = 1;
    if (ku > 999)
        ku = 999;

    tu10 = ((int32_t)tu_ms * 10L) / 1000L;
    if (tu10 < 10)
        tu10 = 10;

    kp = (ku * 6L) / 10L;
    if (kp < 1)
        kp = 1;
    if (kp > 999)
        kp = 999;
    ki = (kp * 100L) / tu10;
    if (ki < 0)
        ki = 0;
    if (ki > 999)
        ki = 999;
    kd = (kp * tu10) / 80L;
    if (kd < 0)
        kd = 0;
    if (kd > 999)
        kd = 999;

    st->atune_kp_x10 = (int16_t)kp;
    st->atune_ki_x10 = (int16_t)ki;
    st->atune_kd_x10 = (int16_t)kd;
    publish_peaks(st);
    st->atune_phase = ATUNE_DONE;
    heaters_off(st);
}

static void fail(app_state_t *st)
{
    st->atune_phase = ATUNE_FAIL;
    heaters_off(st);
}

void pid_atune_on_sample(app_state_t *st)
{
    int16_t t, set_x10, hi, lo;
    uint16_t now, dt;

    if (!st || st->atune_phase != ATUNE_RUN)
        return;
    if (!st->sensor.valid
        || st->sensor.temp_c_x10 >= (int16_t)(st->temp_max_c * 10)) {
        fail(st);
        return;
    }
    st->atune_elapsed_s++;
    if (st->atune_elapsed_s > ATUNE_MAX_S) {
        fail(st);
        return;
    }

    t = st->sensor.temp_c_x10;
    set_x10 = (int16_t)(st->t_set_c * 10);
    hi = (int16_t)(set_x10 + st->atune_hyst_c_x10);
    lo = (int16_t)(set_x10 - st->atune_hyst_c_x10);
    if (t > s_peak_hi)
        s_peak_hi = t;
    if (t < s_peak_lo)
        s_peak_lo = t;
    publish_peaks(st);

    now = delay_ms();
    dt = (uint16_t)(now - s_t0);

    if (st->atune_relay_on) {
        if (t < hi)
            return;
        heaters_off(st);
        if (s_half_n > 0)
            s_half_sum = (uint16_t)(s_half_sum + dt);
        s_half_n++;
        s_t0 = now;
        if ((s_half_n / 2u) >= st->atune_cycles_target && s_half_n >= 4u) {
            uint16_t tu = (uint16_t)((s_half_sum * 2u) / (s_half_n - 1u));
            int16_t amp = (int16_t)((s_peak_hi - s_peak_lo) / 2);
            finish_ok(st, tu, amp);
            return;
        }
        s_peak_hi = t;
        s_peak_lo = t;
        return;
    }

    if (t > lo)
        return;
    outputs_bank_set(st->out_state, 1);
    st->duty_pct = 100;
    st->atune_relay_on = 1;
    if (s_half_n > 0)
        s_half_sum = (uint16_t)(s_half_sum + dt);
    s_half_n++;
    s_t0 = now;
    st->atune_cycles = (uint8_t)(s_half_n / 2u);
    s_peak_hi = t;
    s_peak_lo = t;
}

void pid_atune_apply(app_state_t *st)
{
    if (!st || st->atune_phase != ATUNE_DONE)
        return;
    st->pid_kp_x10 = st->atune_kp_x10;
    st->pid_ki_x10 = st->atune_ki_x10;
    st->pid_kd_x10 = st->atune_kd_x10;
    st->pid_loop = PID_AUTO;
    st->atune_phase = ATUNE_IDLE;
    pid_reset(st);
}
