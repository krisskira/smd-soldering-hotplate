#include "cfg_store.h"
#include "pid.h"
#include <avr/eeprom.h>

/*
 * EEPROM v2: bloque global + bloques por programa.
 * Código compacto: checksum XOR, validación mínima.
 */

typedef struct {
    uint8_t  magic;
    uint8_t  ver;
    int16_t  kp_x10, ki_x10, kd_x10;
    uint8_t  buzz_nav_en, buzz_nav_reps, preheat_en, ramps_en;
    uint16_t stabilize_s, alarm_duration_s, alarm_period_s;
    uint8_t  cooldown_air_en;
    uint16_t cooldown_target_c, temp_limit_c;
    uint8_t  cs;
} cfg_g_t;

typedef struct {
    uint16_t a, b;   /* t_set / delay|run */
    uint8_t  flags;  /* bit0 preheat_en */
    uint8_t  cs;
} cfg_p2_t;

typedef struct {
    uint8_t  n;
    uint16_t t[RAMP_STEPS_MAX];
    uint16_t s[RAMP_STEPS_MAX];
    uint8_t  cs;
} cfg_ramp_t;

static uint8_t EEMEM ee_g[sizeof(cfg_g_t)];
static uint8_t EEMEM ee_pre[sizeof(cfg_p2_t)];
static uint8_t EEMEM ee_start[sizeof(cfg_p2_t)];
static uint8_t EEMEM ee_stop[sizeof(cfg_p2_t)];
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
    st->ramps_en = 1;
    st->stabilize_s = PREHEAT_STABLE_S_DEFAULT;
    st->alarm_duration_s = ALARM_DURATION_S_DEFAULT;
    st->alarm_period_s = ALARM_PERIOD_S_DEFAULT;
    st->cooldown_air_en = 1;
    st->cooldown_target_c = COOLDOWN_TARGET_C_DEFAULT;
    st->temp_limit_c = TEMP_LIMIT_C;
    st->t_set_c = 150;
    st->delay_s = 60;
    st->run_s = 300;
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
        || b.kp_x10 < 0 || b.kp_x10 > 999) {
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
    st->ramps_en = 1u;
    st->stabilize_s = b.stabilize_s ? b.stabilize_s : PREHEAT_STABLE_S_DEFAULT;
    st->alarm_duration_s = b.alarm_duration_s
        ? b.alarm_duration_s : ALARM_DURATION_S_DEFAULT;
    st->alarm_period_s = b.alarm_period_s
        ? b.alarm_period_s : ALARM_PERIOD_S_DEFAULT;
    st->cooldown_air_en = b.cooldown_air_en ? 1u : 0u;
    st->cooldown_target_c = b.cooldown_target_c
        ? b.cooldown_target_c : COOLDOWN_TARGET_C_DEFAULT;
    st->temp_limit_c = b.temp_limit_c ? b.temp_limit_c : TEMP_LIMIT_C;
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
    b.ramps_en = 1u;
    b.stabilize_s = st->stabilize_s;
    b.alarm_duration_s = st->alarm_duration_s;
    b.alarm_period_s = st->alarm_period_s;
    b.cooldown_air_en = st->cooldown_air_en;
    b.cooldown_target_c = st->cooldown_target_c;
    b.temp_limit_c = st->temp_limit_c;
    b.cs = CS(b);
    eeprom_update_block(&b, ee_g, sizeof(b));
}

static void load_p2(app_state_t *st, void *ee, uint8_t is_stop)
{
    cfg_p2_t b;
    eeprom_read_block(&b, ee, sizeof(b));
    if (b.cs != CS(b) || b.a < TEMP_MIN_SET_C || b.a > TEMP_MAX_SET_C) {
        st->t_set_c = 150;
        if (is_stop) {
            st->run_s = 300;
            st->delay_s = 300;
        } else {
            st->delay_s = 60;
        }
        return;
    }
    st->t_set_c = b.a;
    if (is_stop) {
        st->run_s = b.b;
        st->delay_s = b.b;
    } else {
        st->delay_s = b.b;
    }
    /* flags reserved; preheat_en / ramps_en son globales */
}

static void save_p2(const app_state_t *st, void *ee, uint8_t is_stop)
{
    cfg_p2_t b;
    b.a = st->t_set_c;
    b.b = is_stop ? (st->run_s ? st->run_s : st->delay_s) : st->delay_s;
    b.flags = 0;
    b.cs = CS(b);
    eeprom_update_block(&b, ee, sizeof(b));
}

void cfg_load_program(app_state_t *st, program_id_t prog)
{
    if (!st)
        return;
    switch (prog) {
    case PROG_PREHEAT:
    case PROG_PID_TUNE: {
        cfg_p2_t b;
        void *ee = (prog == PROG_PREHEAT) ? (void *)ee_pre : (void *)ee_tune;
        eeprom_read_block(&b, ee, sizeof(b));
        st->t_set_c = (b.cs == CS(b)
                       && b.a >= TEMP_MIN_SET_C && b.a <= TEMP_MAX_SET_C)
            ? b.a : 150;
        break;
    }
    case PROG_START_IN:
        load_p2(st, ee_start, 0);
        break;
    case PROG_STOP_IN:
        load_p2(st, ee_stop, 1);
        break;
    default:
        break;
    }
}

void cfg_save_program(const app_state_t *st, program_id_t prog)
{
    if (!st)
        return;
    switch (prog) {
    case PROG_PREHEAT:
    case PROG_PID_TUNE: {
        cfg_p2_t b;
        void *ee = (prog == PROG_PREHEAT) ? (void *)ee_pre : (void *)ee_tune;
        b.a = st->t_set_c;
        b.b = 0;
        b.flags = 0;
        b.cs = CS(b);
        eeprom_update_block(&b, ee, sizeof(b));
        break;
    }
    case PROG_START_IN:
        save_p2(st, ee_start, 0);
        break;
    case PROG_STOP_IN:
        save_p2(st, ee_stop, 1);
        break;
    default:
        break;
    }
}

/* El paso 1 no se apaga: siempre hay temperatura y un tiempo > 0. */
static void ramp_keep_step0(app_state_t *st)
{
    if (st->ramp_n < 1u)
        st->ramp_n = 1u;
    if (st->ramp_n > RAMP_STEPS_MAX)
        st->ramp_n = RAMP_STEPS_MAX;
    if (st->ramp_step[0].temp_c < TEMP_MIN_SET_C
        || st->ramp_step[0].temp_c > TEMP_MAX_SET_C)
        st->ramp_step[0].temp_c = 100u;
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
    if (!st)
        return;
    b.n = st->ramp_n;
    if (b.n < 1u)
        b.n = 1u;
    if (b.n > RAMP_STEPS_MAX)
        b.n = RAMP_STEPS_MAX;
    for (i = 0; i < RAMP_STEPS_MAX; i++) {
        b.t[i] = st->ramp_step[i].temp_c;
        b.s[i] = st->ramp_step[i].hold_s;
    }
    if (b.t[0] < TEMP_MIN_SET_C || b.t[0] > TEMP_MAX_SET_C)
        b.t[0] = 100u;
    if (b.s[0] == 0u || b.s[0] > TIMER_MAX_S)
        b.s[0] = TIMER_STEP_S;
    b.cs = CS(b);
    eeprom_update_block(&b, ee_ramp, sizeof(b));
}
