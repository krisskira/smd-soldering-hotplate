#include "pid_atune.h"
#include "pid.h"
#include "outputs.h"
#include "at_cmd.h"
#include "lib/avr_delay/avr_delay.h"
#include "lib/ports/ports.h"

/*
 * Autotune bang-bang SSR (Åström–Hägglund) → Ziegler–Nichols.
 * Salida: MOC3021 + BT136. Ciclos/hyst/timeout desde app_state (EEPROM v7).
 * Fan ON en medio-ciclo OFF (enfriamiento) para acortar Tu y limitar
 * tiempo de componentes SMD por encima de la consigna.
 */

static int16_t  s_peak_hi;
static int16_t  s_peak_lo;
static int16_t  s_kp;
static int16_t  s_ki;
static int16_t  s_kd;
/* Suma de medio-periodos en s (delay_ms wrap ~65 s; Tu real ≫ eso). */
static uint16_t s_half_sum_s;
static uint8_t  s_half_n;
static uint16_t s_t0_s;

static void heaters_off(app_state_t *st)
{
    outputs_bank_set(st->out_state, 0);
    st->duty_pct = 0;
    st->atune_relay_on = 0;
}

static void cool_assist_on(void)
{
    fan_on();
}

static void cool_assist_off(void)
{
    fan_off();
}

void pid_atune_init(app_state_t *st)
{
    s_kp = 0;
    s_ki = 0;
    s_kd = 0;
    if (!st)
        return;
    st->atune_phase = ATUNE_IDLE;
    st->atune_cycles = 0;
    st->atune_relay_on = 0;
    st->atune_elapsed_s = 0;
    at_cmd_set_stream(st, 0);
    cool_assist_off();
}

void pid_atune_result(int16_t *kp, int16_t *ki, int16_t *kd)
{
    if (kp)
        *kp = s_kp;
    if (ki)
        *ki = s_ki;
    if (kd)
        *kd = s_kd;
}

void pid_atune_cancel(app_state_t *st)
{
    if (!st)
        return;
    heaters_off(st);
    cool_assist_off();
    st->atune_phase = ATUNE_IDLE;
    at_cmd_set_stream(st, 0);
    pid_reset(st);
}

uint8_t pid_atune_active(const app_state_t *st)
{
    return (st && st->atune_phase == ATUNE_RUN) ? 1u : 0u;
}

uint8_t pid_atune_start(app_state_t *st)
{
    int16_t t;

    if (!st || !st->sensor.valid)
        return 1u;
    if (st->sensor.temp_c_x10 >= (int16_t)(st->temp_max_c * 10))
        return 1u;
    if (st->t_set_c < st->temp_min_c
        || st->t_set_c > (uint16_t)(st->temp_max_c - 10u))
        return 1u;

    pid_atune_cancel(st);
    st->atune_phase = ATUNE_RUN;
    st->atune_cycles = 0;
    st->atune_elapsed_s = 0;
    st->atune_relay_on = 1;
    st->duty_pct = 100;
    cool_assist_off();
    outputs_bank_set(st->out_state, 1);

    t = st->sensor.temp_c_x10;
    s_peak_hi = t;
    s_peak_lo = t;
    s_kp = 0;
    s_ki = 0;
    s_kd = 0;
    s_half_sum_s = 0;
    s_half_n = 0;
    s_t0_s = delay_sec();
    return 0u;
}

/* tu_s = periodo medio de oscilación (s). */
static void finish_ok(app_state_t *st, uint16_t tu_s, int16_t amp)
{
    int32_t ku, kp, ki, kd, tu10;

    if (amp < 5)
        amp = 5;
    ku = 12732L / (int32_t)amp;
    if (ku < 1)
        ku = 1;
    if (ku > 999)
        ku = 999;

    if (tu_s < 1u)
        tu_s = 1u;
    tu10 = (int32_t)tu_s * 10L; /* décimas de segundo */
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

    s_kp = (int16_t)kp;
    s_ki = (int16_t)ki;
    s_kd = (int16_t)kd;
    st->atune_phase = ATUNE_DONE;
    heaters_off(st);
    cool_assist_off();
}

static void fail(app_state_t *st)
{
    st->atune_phase = ATUNE_FAIL;
    heaters_off(st);
    cool_assist_off();
}

void pid_atune_on_sample(app_state_t *st)
{
    int16_t t, set_x10, hi, lo;
    uint16_t now_s, dt_s, lim;

    if (!st || st->atune_phase != ATUNE_RUN)
        return;
    if (!st->sensor.valid
        || st->sensor.temp_c_x10 >= (int16_t)(st->temp_max_c * 10)) {
        fail(st);
        return;
    }
    st->atune_elapsed_s++;
    lim = st->atune_max_s;
    if (lim < ATUNE_MAX_S_LO)
        lim = ATUNE_MAX_S_DEFAULT;
    if (st->atune_elapsed_s > lim) {
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

    now_s = delay_sec();
    dt_s = (uint16_t)(now_s - s_t0_s);

    if (st->atune_relay_on) {
        if (t < hi)
            return;
        /* Cruce alto → OFF calentador + fan para acelerar enfriamiento */
        heaters_off(st);
        cool_assist_on();
        if (s_half_n > 0)
            s_half_sum_s = (uint16_t)(s_half_sum_s + dt_s);
        s_half_n++;
        s_t0_s = now_s;
        if ((s_half_n / 2u) >= st->atune_cycles_target && s_half_n >= 4u) {
            uint16_t tu_s = (uint16_t)((s_half_sum_s * 2u) / (uint16_t)(s_half_n - 1u));
            int16_t amp = (int16_t)((s_peak_hi - s_peak_lo) / 2);
            finish_ok(st, tu_s, amp);
            return;
        }
        s_peak_hi = t;
        s_peak_lo = t;
        return;
    }

    if (t > lo)
        return;
    /* Cruce bajo → ON calentador, fan OFF */
    cool_assist_off();
    outputs_bank_set(st->out_state, 1);
    st->duty_pct = 100;
    st->atune_relay_on = 1;
    if (s_half_n > 0)
        s_half_sum_s = (uint16_t)(s_half_sum_s + dt_s);
    s_half_n++;
    s_t0_s = now_s;
    st->atune_cycles = (uint8_t)(s_half_n / 2u);
    s_peak_hi = t;
    s_peak_lo = t;
}

void pid_atune_apply(app_state_t *st)
{
    if (!st || st->atune_phase != ATUNE_DONE)
        return;
    st->pid_kp_x10 = s_kp;
    st->pid_ki_x10 = s_ki;
    st->pid_kd_x10 = s_kd;
    st->pid_loop = PID_AUTO;
    st->atune_phase = ATUNE_IDLE;
    pid_reset(st);
}
