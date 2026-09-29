#include "cfg_store.h"
#include "pid.h"
#include <avr/eeprom.h>

/*
 * EEPROM v8: global (+ bandas preheat) + ee_heat/tune + rampas.
 * Ver distinta → defaults, sin migración.
 */

typedef struct {
    uint8_t  magic;
    uint8_t  ver;
    int16_t  kp_x10, ki_x10, kd_x10;
    uint8_t  buzz_nav_en, buzz_nav_reps, preheat_en, ramps_en;
    uint16_t stabilize_s, alarm_duration_s, alarm_period_s;
    uint8_t  cooldown_air_en;
    uint16_t temp_min_c, temp_max_c;
    uint8_t  atune_cycles_target;
    int16_t  atune_hyst_c_x10;
    uint8_t  preheat_pct;
    uint16_t atune_max_s;
    uint8_t  preheat_band_c;
    uint8_t  preheat_band_exit_c;
    uint8_t  cs;
} cfg_g_t;

typedef struct {
    uint16_t a, b;   /* t_set / delay */
    uint8_t  flags;
    uint8_t  cs;
} cfg_p2_t;

typedef struct {
    uint8_t  n;
    uint16_t t[RAMP_STEPS_MAX];
    uint16_t s[RAMP_STEPS_MAX];
    uint8_t  cs;
} cfg_ramp_t;

static uint8_t EEMEM ee_g[sizeof(cfg_g_t)];
static uint8_t EEMEM ee_heat[sizeof(cfg_p2_t)];
static uint8_t EEMEM ee_ramp[sizeof(cfg_ramp_t)];
static uint8_t EEMEM ee_tune[sizeof(cfg_p2_t)];

static uint8_t xor_cs(const uint8_t *p, uint8_t n)
{
    uint8_t s = 0, i;
    for (i = 0; i < n; i++)
        s ^= p[i];
    return s;
}

#define CS(b) xor_cs((const uint8_t *)&(b), (uint8_t)(sizeof(b) - 1u))

static uint16_t clamp_u16(uint16_t v, uint16_t lo, uint16_t hi)
{
    if (v < lo)
        return lo;
    if (v > hi)
        return hi;
    return v;
}

void cfg_store_defaults(app_state_t *st)
{
    uint8_t i;
    if (!st)
        return;
    st->pid_kp_x10 = PID_KP_DEFAULT;
    st->pid_ki_x10 = PID_KI_DEFAULT;
    st->pid_kd_x10 = PID_KD_DEFAULT;
    st->buzz_nav_en = 1;
    st->buzz_nav_reps = 1;
    st->preheat_en = 1;
    st->preheat_pct = PREHEAT_PCT_DEFAULT;
    st->preheat_band_c = PREHEAT_BAND_C_DEFAULT;
    st->preheat_band_exit_c = PREHEAT_BAND_EXIT_C_DEFAULT;
    st->ramps_en = 1;
    st->stabilize_s = PREHEAT_STABLE_S_DEFAULT;
    st->alarm_duration_s = ALARM_DURATION_S_DEFAULT;
    st->alarm_period_s = ALARM_PERIOD_S_DEFAULT;
    st->cooldown_air_en = 1;
    st->temp_min_c = TEMP_MIN_C_DEFAULT;
    st->temp_max_c = TEMP_MAX_C_DEFAULT;
    st->atune_cycles_target = ATUNE_CYCLES_DEFAULT;
    st->atune_hyst_c_x10 = ATUNE_HYST_C_X10;
    st->atune_max_s = ATUNE_MAX_S_DEFAULT;
    st->t_set_c = 150;
    st->delay_s = 60;
    st->ramp_n = 2;
    for (i = 0; i < RAMP_STEPS_MAX; i++) {
        st->ramp_step[i].temp_c = (uint16_t)(100u + 25u * i);
        st->ramp_step[i].hold_s = 60;
    }
}

uint8_t cfg_load_global(app_state_t *st)
{
    cfg_g_t b;
    if (!st)
        return 0;
    eeprom_read_block(&b, ee_g, sizeof(b));
    if (b.magic != CFG_EEPROM_MAGIC || b.ver != CFG_EEPROM_VER || b.cs != CS(b)
        || b.kp_x10 < 0 || b.kp_x10 > 999
        || b.ki_x10 < 0 || b.ki_x10 > 999) {
        cfg_store_defaults(st);
        return 0;
    }
    st->pid_kp_x10 = b.kp_x10;
    st->pid_ki_x10 = b.ki_x10;
    st->pid_kd_x10 = b.kd_x10;
    st->buzz_nav_en = b.buzz_nav_en ? 1u : 0u;
    st->buzz_nav_reps = (b.buzz_nav_reps >= 1u && b.buzz_nav_reps <= 4u)
        ? b.buzz_nav_reps : 1u;
    st->preheat_en = b.preheat_en ? 1u : 0u;
    st->preheat_pct = (b.preheat_pct >= PREHEAT_PCT_LO
                       && b.preheat_pct <= PREHEAT_PCT_HI)
        ? b.preheat_pct : PREHEAT_PCT_DEFAULT;
    st->preheat_band_c = PREHEAT_BAND_C_DEFAULT;
    st->preheat_band_exit_c = PREHEAT_BAND_EXIT_C_DEFAULT;
    if (b.preheat_band_c >= PREHEAT_BAND_C_LO
        && b.preheat_band_c <= PREHEAT_BAND_C_HI)
        st->preheat_band_c = b.preheat_band_c;
    if (b.preheat_band_exit_c >= st->preheat_band_c
        && b.preheat_band_exit_c <= PREHEAT_BAND_EXIT_C_HI)
        st->preheat_band_exit_c = b.preheat_band_exit_c;
    st->ramps_en = 1u;
    st->stabilize_s = b.stabilize_s ? b.stabilize_s : PREHEAT_STABLE_S_DEFAULT;
    st->alarm_duration_s = b.alarm_duration_s
        ? b.alarm_duration_s : ALARM_DURATION_S_DEFAULT;
    st->alarm_period_s = b.alarm_period_s
        ? b.alarm_period_s : ALARM_PERIOD_S_DEFAULT;
    st->cooldown_air_en = b.cooldown_air_en ? 1u : 0u;
    st->temp_min_c = clamp_u16(b.temp_min_c, TEMP_MIN_C_LO, TEMP_MIN_C_HI);
    st->temp_max_c = clamp_u16(b.temp_max_c, TEMP_MAX_C_LO, TEMP_MAX_C_HI);
    if (st->temp_min_c > st->temp_max_c)
        st->temp_min_c = TEMP_MIN_C_DEFAULT;
    st->atune_cycles_target = (b.atune_cycles_target >= ATUNE_MIN_CYCLES
                               && b.atune_cycles_target <= ATUNE_MAX_CYCLES)
        ? b.atune_cycles_target : ATUNE_CYCLES_DEFAULT;
    st->atune_hyst_c_x10 = (b.atune_hyst_c_x10 > 0 && b.atune_hyst_c_x10 < 100)
        ? b.atune_hyst_c_x10 : ATUNE_HYST_C_X10;
    st->atune_max_s = clamp_u16(b.atune_max_s, ATUNE_MAX_S_LO, ATUNE_MAX_S_HI);
    return 1;
}

void cfg_save_global(const app_state_t *st)
{
    cfg_g_t b;
    if (!st)
        return;
    b.magic = CFG_EEPROM_MAGIC;
    b.ver = CFG_EEPROM_VER;
    b.kp_x10 = st->pid_kp_x10;
    b.ki_x10 = st->pid_ki_x10;
    b.kd_x10 = st->pid_kd_x10;
    b.buzz_nav_en = st->buzz_nav_en;
    b.buzz_nav_reps = st->buzz_nav_reps;
    b.preheat_en = st->preheat_en;
    b.preheat_pct = st->preheat_pct;
    b.preheat_band_c = st->preheat_band_c;
    b.preheat_band_exit_c = st->preheat_band_exit_c;
    b.ramps_en = 1u;
    b.stabilize_s = st->stabilize_s;
    b.alarm_duration_s = st->alarm_duration_s;
    b.alarm_period_s = st->alarm_period_s;
    b.cooldown_air_en = st->cooldown_air_en;
    b.temp_min_c = st->temp_min_c;
    b.temp_max_c = st->temp_max_c;
    b.atune_cycles_target = st->atune_cycles_target;
    b.atune_hyst_c_x10 = st->atune_hyst_c_x10;
    b.atune_max_s = st->atune_max_s;
    b.cs = CS(b);
    eeprom_update_block(&b, ee_g, sizeof(b));
}

void cfg_load_program(app_state_t *st, program_id_t prog)
{
    cfg_p2_t b;
    void *ee;

    if (!st)
        return;
    switch (prog) {
    case PROG_PID_TUNE:
        ee = ee_tune;
        break;
    case PROG_HEAT:
        ee = ee_heat;
        break;
    default:
        return;
    }
    eeprom_read_block(&b, ee, sizeof(b));
    if (b.cs != CS(b) || b.a < st->temp_min_c || b.a > st->temp_max_c) {
        st->t_set_c = 150;
        if (prog == PROG_HEAT)
            st->delay_s = 60;
        return;
    }
    st->t_set_c = b.a;
    if (prog == PROG_HEAT)
        st->delay_s = b.b;
}

void cfg_save_program(const app_state_t *st, program_id_t prog)
{
    cfg_p2_t b;
    void *ee;

    if (!st)
        return;
    switch (prog) {
    case PROG_PID_TUNE:
        ee = ee_tune;
        break;
    case PROG_HEAT:
        ee = ee_heat;
        break;
    default:
        return;
    }
    b.a = st->t_set_c;
    b.b = (prog == PROG_HEAT) ? st->delay_s : 0u;
    b.flags = 0;
    b.cs = CS(b);
    eeprom_update_block(&b, ee, sizeof(b));
}

static void ramp_keep_step0(app_state_t *st)
{
    uint16_t lo = st->temp_min_c;
    uint16_t hi = st->temp_max_c;

    if (st->ramp_n < 1u)
        st->ramp_n = 1u;
    if (st->ramp_n > RAMP_STEPS_MAX)
        st->ramp_n = RAMP_STEPS_MAX;
    if (st->ramp_step[0].temp_c < lo || st->ramp_step[0].temp_c > hi)
        st->ramp_step[0].temp_c = clamp_u16(100u, lo, hi);
    if (st->ramp_step[0].hold_s == 0u || st->ramp_step[0].hold_s > TIMER_MAX_S)
        st->ramp_step[0].hold_s = TIMER_STEP_S;
}

void cfg_load_ramps(app_state_t *st)
{
    cfg_ramp_t b;
    uint8_t i;
    if (!st)
        return;
    eeprom_read_block(&b, ee_ramp, sizeof(b));
    if (b.cs == CS(b) && b.n >= 1u && b.n <= RAMP_STEPS_MAX) {
        st->ramp_n = b.n;
        for (i = 0; i < RAMP_STEPS_MAX; i++) {
            st->ramp_step[i].temp_c = b.t[i];
            st->ramp_step[i].hold_s = b.s[i];
        }
    } else {
        st->ramp_n = 2;
        for (i = 0; i < RAMP_STEPS_MAX; i++) {
            st->ramp_step[i].temp_c = (uint16_t)(100u + 25u * i);
            st->ramp_step[i].hold_s = 60;
        }
    }
    ramp_keep_step0(st);
}

void cfg_save_ramps(const app_state_t *st)
{
    cfg_ramp_t b;
    uint8_t i;
    uint16_t lo, hi;
    if (!st)
        return;
    lo = st->temp_min_c;
    hi = st->temp_max_c;
    b.n = st->ramp_n;
    if (b.n < 1u)
        b.n = 1u;
    if (b.n > RAMP_STEPS_MAX)
        b.n = RAMP_STEPS_MAX;
    for (i = 0; i < RAMP_STEPS_MAX; i++) {
        b.t[i] = st->ramp_step[i].temp_c;
        b.s[i] = st->ramp_step[i].hold_s;
    }
    if (b.t[0] < lo || b.t[0] > hi)
        b.t[0] = clamp_u16(100u, lo, hi);
    if (b.s[0] == 0u || b.s[0] > TIMER_MAX_S)
        b.s[0] = TIMER_STEP_S;
    b.cs = CS(b);
    eeprom_update_block(&b, ee_ramp, sizeof(b));
}
