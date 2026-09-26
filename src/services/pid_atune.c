#include "pid_atune.h"
#include "pid.h"
#include "outputs.h"
#include "lib/avr_delay/avr_delay.h"

/*
 * Compact relay autotune (Åström–Hägglund style):
 * Below setpoint − hyst → bank ON 100 %
 * Above setpoint + hyst → bank OFF
 * Measure half-period and peak amplitude; after N cycles → Ziegler–Nichols.
 */

static int16_t  s_peak_hi_x10;
static int16_t  s_peak_lo_x10;
static uint16_t s_half_ms;
static uint16_t s_half_sum_ms;
static uint8_t  s_half_count;
static uint8_t  s_looking_hi;
static uint16_t s_t0_ms;

static int16_t temp_x10(const app_state_t *st)
{
    return st->sensor.temp_c_x10;
}

static void clear_trace(app_state_t *st)
{
    s_peak_hi_x10 = 0;
    s_peak_lo_x10 = 0;
    st->atune_peak_hi_x10 = 0;
    st->atune_peak_lo_x10 = 0;
    st->atune_hyst_hi_x10 = 0;
    st->atune_hyst_lo_x10 = 0;
}

/* Copia picos y umbrales de conmutación a st. Aritmética ×10. */
static void publish_trace(app_state_t *st)
{
    int16_t set_x10 = (int16_t)((int16_t)st->t_set_c * 10);

    st->atune_peak_hi_x10 = s_peak_hi_x10;
    st->atune_peak_lo_x10 = s_peak_lo_x10;
    st->atune_hyst_hi_x10 = (int16_t)(set_x10 + ATUNE_HYST_C_X10);
    st->atune_hyst_lo_x10 = (int16_t)(set_x10 - ATUNE_HYST_C_X10);
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
    clear_trace(st);
}

void pid_atune_cancel(app_state_t *st)
{
    if (!st)
        return;
    outputs_bank_set(st->out_state, 0);
    st->duty_pct = 0;
    st->atune_phase = ATUNE_IDLE;
    st->atune_relay_on = 0;
    clear_trace(st);
    pid_reset(st);
}

uint8_t pid_atune_active(const app_state_t *st)
{
    return (st && st->atune_phase == ATUNE_RUN) ? 1u : 0u;
}

void pid_atune_start(app_state_t *st)
{
    if (!st || !st->sensor.valid)
        return;
    if (st->sensor.temp_c_x10 >= TEMP_LIMIT_X10)
        return;
    if (st->t_set_c < TEMP_MIN_SET_C || st->t_set_c > (TEMP_MAX_SET_C - 10u))
        return;

    pid_atune_cancel(st);
    st->atune_phase = ATUNE_RUN;
    st->atune_cycles = 0;
    st->atune_elapsed_s = 0;
    st->atune_relay_on = 1;
    st->duty_pct = 100;
    outputs_bank_set(st->out_state, 1);

    s_peak_hi_x10 = temp_x10(st);
    s_peak_lo_x10 = s_peak_hi_x10;
    s_half_ms = 0;
    s_half_sum_ms = 0;
    s_half_count = 0;
    s_looking_hi = 1;
    s_t0_ms = delay_ms();
    publish_trace(st);
}

static void finish_ok(app_state_t *st, uint16_t tu_ms, int16_t amp_x10)
{
    /* Ku ≈ 4*d/(π*a); d = 50 % of full (relay ±50 around 50) → use 100 % swing
     * a = amp in °C. Use fixed-point ×10.
     * Ku_x10 = 4000 / (π * a_x10/10) ≈ 12732 / a_x10
     */
    int32_t ku_x10;
    int32_t kp, ki, kd;
    int32_t tu_s_x10;

    if (amp_x10 < 5)
        amp_x10 = 5;

    ku_x10 = 12732L / (int32_t)amp_x10;
    if (ku_x10 < 1)
        ku_x10 = 1;
    if (ku_x10 > 999)
        ku_x10 = 999;

    /* Tu in seconds ×10 */
    tu_s_x10 = ((int32_t)tu_ms * 10L) / 1000L;
    if (tu_s_x10 < 10)
        tu_s_x10 = 10;

    /* Classic ZN PID: Kp=0.6 Ku, Ti=0.5 Tu, Td=0.125 Tu
     * Ki = Kp/Ti → ki_x10 ≈ kp_x10 * 10 / (tu_s_x10/10) = kp*100/tu_s_x10
     * Kd = Kp*Td → kd_x10 ≈ kp_x10 * tu_s_x10 / 80
     */
    kp = (ku_x10 * 6L) / 10L;
    if (kp < 1)
        kp = 1;
    if (kp > 999)
        kp = 999;

    ki = (kp * 100L) / tu_s_x10;
    if (ki < 0)
        ki = 0;
    if (ki > 999)
        ki = 999;

    kd = (kp * tu_s_x10) / 80L;
    if (kd < 0)
        kd = 0;
    if (kd > 999)
        kd = 999;

    st->atune_kp_x10 = (int16_t)kp;
    st->atune_ki_x10 = (int16_t)ki;
    st->atune_kd_x10 = (int16_t)kd;
    st->atune_phase = ATUNE_DONE;
    outputs_bank_set(st->out_state, 0);
    st->duty_pct = 0;
    st->atune_relay_on = 0;
    publish_trace(st);
}

void pid_atune_on_sample(app_state_t *st)
{
    int16_t t_x10;
    int16_t set_x10;
    int16_t hi;
    int16_t lo;
    uint16_t now;
    uint16_t dt;

    if (!st || st->atune_phase != ATUNE_RUN)
        return;

    if (!st->sensor.valid) {
        st->atune_phase = ATUNE_FAIL;
        outputs_bank_set(st->out_state, 0);
        st->duty_pct = 0;
        publish_trace(st);
        return;
    }

    if (st->sensor.temp_c_x10 >= TEMP_LIMIT_X10) {
        st->atune_phase = ATUNE_FAIL;
        outputs_bank_set(st->out_state, 0);
        st->duty_pct = 0;
        publish_trace(st);
        return;
    }

    st->atune_elapsed_s++;
    if (st->atune_elapsed_s > ATUNE_MAX_S) {
        st->atune_phase = ATUNE_FAIL;
        outputs_bank_set(st->out_state, 0);
        st->duty_pct = 0;
        publish_trace(st);
        return;
    }

    t_x10 = temp_x10(st);
    set_x10 = (int16_t)(st->t_set_c * 10);
    hi = (int16_t)(set_x10 + ATUNE_HYST_C_X10);
    lo = (int16_t)(set_x10 - ATUNE_HYST_C_X10);

    if (t_x10 > s_peak_hi_x10)
        s_peak_hi_x10 = t_x10;
    if (t_x10 < s_peak_lo_x10)
        s_peak_lo_x10 = t_x10;

    now = delay_ms();
    dt = (uint16_t)(now - s_t0_ms);

    if (st->atune_relay_on) {
        if (t_x10 >= hi) {
            /* half-cycle: ON → OFF */
            outputs_bank_set(st->out_state, 0);
            st->duty_pct = 0;
            st->atune_relay_on = 0;
            if (s_half_count > 0) {
                s_half_sum_ms = (uint16_t)(s_half_sum_ms + dt);
            }
            s_half_count++;
            s_t0_ms = now;
            s_looking_hi = 0;
            if ((s_half_count / 2u) >= ATUNE_MIN_CYCLES
                && s_half_count >= 4u) {
                uint16_t tu = (uint16_t)((s_half_sum_ms * 2u)
                                         / (s_half_count - 1u));
                int16_t amp = (int16_t)((s_peak_hi_x10 - s_peak_lo_x10) / 2);
                finish_ok(st, tu, amp);
                return;
            }
            s_peak_hi_x10 = t_x10;
            s_peak_lo_x10 = t_x10;
        }
    } else {
        if (t_x10 <= lo) {
            outputs_bank_set(st->out_state, 1);
            st->duty_pct = 100;
            st->atune_relay_on = 1;
            if (s_half_count > 0)
                s_half_sum_ms = (uint16_t)(s_half_sum_ms + dt);
            s_half_count++;
            s_t0_ms = now;
            st->atune_cycles = (uint8_t)(s_half_count / 2u);
            s_peak_hi_x10 = t_x10;
            s_peak_lo_x10 = t_x10;
            (void)s_looking_hi;
            (void)s_half_ms;
        }
    }
    publish_trace(st);
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
    clear_trace(st);
    pid_reset(st);
}
