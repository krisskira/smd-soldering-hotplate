#include "at_cmd.h"
#include "process.h"
#include "device_session.h"
#include "telemetry.h"
#include "pid_atune.h"
#include "cfg_store.h"
#include "proto_tokens.h"
#include "proto_codes.h"
#include "ui/ui_router.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

/*
 * UART → s_line → at_parse → cmd id → switch.
 * Errores numéricos (proto_codes). Nombres en blob PROGMEM.
 */

static char s_line[AT_LINE_MAX];
static uint8_t s_len;

/*
 * Cinco verbos. CFG aparece dos veces: '?' lee settings, '=' escribe.
 * El parser exige que el terminador coincida antes de aceptar el nombre.
 */
static const char CMD_NAMES[] PROGMEM =
    "STAT\0"
    "MODE\0"
    "CFG\0"
    "CFG\0"
    "RUN\0"
    "STOP\0";

enum {
    CMD_STAT = 0,
    CMD_MODE,
    CMD_CFG_Q,
    CMD_CFG,
    CMD_RUN,
    CMD_STOP,
    CMD_COUNT
};

/* bits7..1 = terminador ('?'/'='/0), bit0 = need_usb. */
static const uint8_t CMD_META[CMD_COUNT] PROGMEM = {
    (uint8_t)('?' << 1) | 0,
    (uint8_t)('=' << 1) | 0,
    (uint8_t)('?' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('\0' << 1) | 1
};

static void reply_ok(app_state_t *st)
{
    if (st)
        st->usb_last_ok = 1;
    avr_uart_transmit_pstr(PSTR("OK"));
    avr_uart_transmit_pstr(PROTO_CRLF);
}

static void reply_err(app_state_t *st, uint8_t code)
{
    if (st)
        st->usb_last_ok = 0;
    proto_emit_error(code);
}

static void reply_from_proc(app_state_t *st, uint8_t code)
{
    switch (code) {
    case PROG_OK:
        reply_ok(st);
        break;
    case PROG_ERR_SENSOR:
        reply_err(st, (uint8_t)PROTO_ERR_SENSOR_INVALID);
        break;
    case PROG_ERR_OVERTEMP:
        reply_err(st, (uint8_t)PROTO_ERR_OVER_TEMPERATURE);
        break;
    case PROG_ERR_BUSY:
        reply_err(st, (uint8_t)PROTO_ERR_PROGRAM_BUSY);
        break;
    case PROG_ERR_FAULT:
        reply_err(st, (uint8_t)PROTO_ERR_DEVICE_BUSY);
        break;
    default:
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        break;
    }
}

#define ok_dirty(st) do { \
    (st)->row_dirty = ROW_ALL; \
    (st)->telem_dirty = 1u; \
    reply_ok(st); \
} while (0)

static uint8_t parse_u16(const char **pp, uint16_t *out)
{
    const char *p;
    uint16_t v = 0;
    uint8_t n = 0;

    if (!pp || !*pp || !out)
        return 1u;
    p = *pp;
    while (*p >= '0' && *p <= '9' && n < 5u) {
        v = (uint16_t)(v * 10u + (uint16_t)(*p - '0'));
        p++;
        n++;
    }
    if (n == 0u)
        return 1u;
    *out = v;
    *pp = p;
    return 0u;
}

static uint8_t parse_i16(const char **pp, int16_t *out)
{
    const char *p;
    uint16_t u;
    uint8_t neg = 0u;

    if (!pp || !*pp || !out)
        return 1u;
    p = *pp;
    if (*p == '-') {
        neg = 1u;
        p++;
    }
    if (parse_u16(&p, &u))
        return 1u;
    if (u > 999u)
        return 1u;
    *out = neg ? (int16_t)(-(int16_t)u) : (int16_t)u;
    *pp = p;
    return 0u;
}

static uint8_t match_name_P(const char **ram, PGM_P *flash)
{
    const char *r = *ram;
    PGM_P f = *flash;
    char c;

    for (;;) {
        c = (char)pgm_read_byte(f);
        if (c == '\0') {
            *ram = r;
            *flash = f + 1;
            return 1u;
        }
        if (*r != c)
            return 0u;
        r++;
        f++;
    }
}

static PGM_P skip_str_P(PGM_P f)
{
    while (pgm_read_byte(f))
        f++;
    return f + 1;
}

static uint8_t at_parse(const char *p, const char **args, char *term_out)
{
    PGM_P names = CMD_NAMES;
    uint8_t id;

    for (id = 0; id < CMD_COUNT; id++) {
        const char *rp = p;
        PGM_P np = names;

        if (match_name_P(&rp, &np)) {
            char t = *rp;
            uint8_t meta = pgm_read_byte(&CMD_META[id]);
            char want = (char)(meta >> 1);

            if (t == want) {
                *args = (t == '\0') ? rp : (rp + 1);
                *term_out = t;
                return id;
            }
        }
        names = skip_str_P(names);
    }
    return 0xFFu;
}

static uint8_t take_u(const char **p, uint16_t *out, uint8_t last)
{
    if (parse_u16(p, out))
        return 1u;
    if (last)
        return **p ? 1u : 0u;
    if (**p != ',')
        return 1u;
    (*p)++;
    return 0u;
}

static uint8_t bit01(uint16_t v)
{
    return v > 1u;
}

/* AT+CFG=S,min,max */
static uint8_t cfg_safety(app_state_t *st, const char *args)
{
    const char *p = args;
    uint16_t mn, mx;

    if (take_u(&p, &mn, 0u) || take_u(&p, &mx, 1u))
        return 1u;
    if (mn < TEMP_MIN_C_LO || mn > TEMP_MIN_C_HI)
        return 1u;
    if (mx < TEMP_MAX_C_LO || mx > TEMP_MAX_C_HI || mn > mx)
        return 1u;
    st->temp_min_c = mn;
    st->temp_max_c = mx;
    cfg_save_global(st);
    ok_dirty(st);
    return 0u;
}

/* AT+CFG=H,en,pct,stab,delay,air,snd */
static uint8_t cfg_heat(app_state_t *st, const char *args)
{
    const char *p = args;
    uint16_t en, pct, stab, dly, air, snd;

    if (take_u(&p, &en, 0u) || take_u(&p, &pct, 0u) || take_u(&p, &stab, 0u)
        || take_u(&p, &dly, 0u) || take_u(&p, &air, 0u) || take_u(&p, &snd, 1u))
        return 1u;
    if (bit01(en) || bit01(air) || bit01(snd))
        return 1u;
    if (pct < PREHEAT_PCT_LO || pct > PREHEAT_PCT_HI
        || (pct % PREHEAT_PCT_STEP) != 0u)
        return 1u;
    if (stab < 1u || stab > 3600u || dly > 3600u)
        return 1u;
    st->preheat_en = (uint8_t)en;
    st->preheat_pct = (uint8_t)pct;
    st->stabilize_s = stab;
    st->delay_s = dly;
    st->cooldown_air_en = (uint8_t)air;
    st->buzz_nav_en = (uint8_t)snd;
    st->program = PROG_HEAT;
    cfg_save_global(st);
    cfg_save_program(st, PROG_HEAT);
    ok_dirty(st);
    return 0u;
}

/* AT+CFG=P,kp,ki,kd  (×10, 0..999) */
static uint8_t cfg_pid(app_state_t *st, const char *args)
{
    const char *p = args;
    uint16_t kp, ki, kd;

    if (take_u(&p, &kp, 0u) || take_u(&p, &ki, 0u) || take_u(&p, &kd, 1u))
        return 1u;
    if (kp > 999u || ki > 999u || kd > 999u)
        return 1u;
    st->pid_kp_x10 = (int16_t)kp;
    st->pid_ki_x10 = (int16_t)ki;
    st->pid_kd_x10 = (int16_t)kd;
    cfg_save_global(st);
    ok_dirty(st);
    return 0u;
}

/* AT+CFG=R,i,°C,s */
static uint8_t cfg_ramp(app_state_t *st, const char *args)
{
    const char *p = args;
    uint16_t idx, temp, hold;

    if (take_u(&p, &idx, 0u) || take_u(&p, &temp, 0u) || take_u(&p, &hold, 1u))
        return 1u;
    if (idx >= RAMP_STEPS_MAX)
        return 1u;
    if (temp < st->temp_min_c || temp > st->temp_max_c)
        return 1u;
    if (hold < 1u || hold > 3600u)
        return 1u;
    st->ramp_step[(uint8_t)idx].temp_c = temp;
    st->ramp_step[(uint8_t)idx].hold_s = hold;
    if (st->ramp_n < (uint8_t)(idx + 1u))
        st->ramp_n = (uint8_t)(idx + 1u);
    st->ramps_en = 1u;
    cfg_save_ramps(st);
    st->telem_dirty = 1u;
    reply_ok(st);
    return 0u;
}

static uint8_t handle_cfg(app_state_t *st, const char *args)
{
    char g;

    if (!args || !args[0])
        return 1u;
    g = args[0];
    if (g == 'A') {
        if (args[1] != '\0')
            return 1u;
        if (st->atune_phase != ATUNE_DONE)
            return 1u;
        pid_atune_apply(st);
        cfg_save_global(st);
        ok_dirty(st);
        return 0u;
    }
    /* AT+CFG=R? — lectura de escalones (args "R?", sin coma). */
    if (g == 'R' && args[1] == '?' && args[2] == '\0') {
        telemetry_emit_ramps(st);
        reply_ok(st);
        return 0u;
    }
    if (args[1] != ',')
        return 1u;
    args += 2;
    switch (g) {
    case 'S': return cfg_safety(st, args);
    case 'H': return cfg_heat(st, args);
    case 'P': return cfg_pid(st, args);
    case 'R': return cfg_ramp(st, args);
    default:  return 1u;
    }
}

/* AT+RUN=1  |  AT+RUN=2,temp,cycles,hyst */
static void handle_run(app_state_t *st, const char *args)
{
    const char *p = args;
    uint16_t prog, temp, cycles;
    int16_t hyst;

    if (process_is_active(st) || pid_atune_active(st)) {
        reply_err(st, (uint8_t)PROTO_ERR_PROGRAM_BUSY);
        return;
    }
    if (parse_u16(&p, &prog)) {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    if (prog == (uint16_t)PROG_HEAT && *p == '\0') {
        st->program = PROG_HEAT;
        reply_from_proc(st, process_start(st, CTRL_USB));
        st->row_dirty = ROW_ALL;
        return;
    }
    if (prog != (uint16_t)PROG_PID_TUNE || *p != ',') {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    p++;
    if (parse_u16(&p, &temp) || *p != ',') {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    p++;
    if (parse_u16(&p, &cycles) || *p != ',') {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    p++;
    if (parse_i16(&p, &hyst) || *p) {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    if (temp < st->temp_min_c || temp > (uint16_t)(st->temp_max_c - 10u)
        || cycles < ATUNE_MIN_CYCLES || cycles > ATUNE_MAX_CYCLES
        || hyst < 1 || hyst > 99) {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        return;
    }
    st->program = PROG_PID_TUNE;
    st->t_set_c = temp;
    st->atune_cycles_target = (uint8_t)cycles;
    st->atune_hyst_c_x10 = hyst;
    cfg_save_global(st);
    cfg_save_program(st, PROG_PID_TUNE);
    reply_from_proc(st, process_start(st, CTRL_USB));
    st->row_dirty = ROW_ALL;
}

static void handle_line(app_state_t *st, char *line, uint8_t n)
{
    uint8_t id;
    char term;
    const char *args;
    const char *p;
    uint16_t u0;

    if (!st || !line)
        return;

    while (n > 0u && (line[n - 1u] == ' ' || line[n - 1u] == '\t'))
        line[--n] = '\0';
    if (n == 0u)
        return;

    if (n == 2u && line[0] == 'A' && line[1] == 'T') {
        reply_ok(st);
        return;
    }
    if (n < 4u || line[0] != 'A' || line[1] != 'T' || line[2] != '+') {
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_COMMAND);
        return;
    }

    id = at_parse(line + 3, &args, &term);
    if (id == 0xFFu) {
        reply_err(st, device_session_is_usb(st)
                          ? (uint8_t)PROTO_ERR_INVALID_COMMAND
                          : (uint8_t)PROTO_ERR_USB_MODE_REQUIRED);
        return;
    }

    if ((pgm_read_byte(&CMD_META[id]) & 1u) && !device_session_is_usb(st)) {
        reply_err(st, (uint8_t)PROTO_ERR_USB_MODE_REQUIRED);
        return;
    }

    switch (id) {
    case CMD_STAT:
        telemetry_emit(st);
        reply_ok(st);
        break;

    case CMD_MODE:
        p = args;
        if (parse_u16(&p, &u0) || *p || u0 > 1u) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        if (u0 == 1u) {
            if (device_session_enter_usb(st) != 0) {
                reply_err(st, (uint8_t)PROTO_ERR_DEVICE_BUSY);
                break;
            }
            ui_enter_view(st, VIEW_USB);
        } else {
            device_session_leave_manual(st, 0u);
            if (st->view == VIEW_USB)
                ui_enter_view(st, VIEW_HOME);
        }
        telemetry_emit(st);
        reply_ok(st);
        break;

    case CMD_CFG_Q:
        telemetry_emit_cfg(st);
        reply_ok(st);
        break;

    case CMD_CFG:
        if (handle_cfg(st, args))
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        break;

    case CMD_RUN:
        handle_run(st, args);
        break;

    case CMD_STOP:
        process_stop(st, CTRL_USB);
        st->row_dirty = ROW_ALL;
        reply_ok(st);
        break;

    default:
        reply_err(st, (uint8_t)PROTO_ERR_INVALID_COMMAND);
        break;
    }
}

void at_cmd_init(void)
{
    s_len = 0;
    s_line[0] = '\0';
}

void at_cmd_tick(app_state_t *st)
{
    int16_t c;

    if (!st)
        return;

    while ((c = avr_uart_rx_pop()) >= 0) {
        char ch = (char)c;

        if (ch == '\r' || ch == '\n') {
            if (s_len > 0u) {
                s_line[s_len] = '\0';
                handle_line(st, s_line, s_len);
                s_len = 0;
            }
            continue;
        }

        if (s_len < (AT_LINE_MAX - 1u)) {
            if (ch >= 'a' && ch <= 'z')
                ch = (char)(ch - 'a' + 'A');
            s_line[s_len++] = ch;
        } else {
            s_len = 0;
        }
    }
}

void at_cmd_set_stream(app_state_t *st, uint8_t on)
{
    if (st)
        st->atune_stream = on ? 1u : 0u;
}
