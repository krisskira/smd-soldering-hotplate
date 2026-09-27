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
 * Nombres AT+ (sin AT+). Prefijos largos primero
 * (PREHEATPCT>PREHEAT, TEMPMIN/TEMPMAX>TEMP).
 */
/* Nombres cortos (= claves $HP). Prefijos largos primero. */
static const char CMD_NAMES[] PROGMEM =
    "STATUS\0"
    "DEVICEMODE\0"
    "PIDAPPLY\0"
    "PROGRAM\0"
    "PREHEAT\0"
    "PHPCT\0"
    "ATUNE\0"
    "RAMPS\0"
    "DELAY\0"
    "TEMP\0"
    "TMIN\0"
    "TMAX\0"
    "STAB\0"
    "RAMP\0"
    "START\0"
    "STOP\0"
    "SND\0"
    "AIR\0"
    "KP\0"
    "KI\0"
    "KD\0";

enum {
    CMD_STATUS = 0,
    CMD_DEVICEMODE,
    CMD_PIDAPPLY,
    CMD_PROGRAM,
    CMD_PREHEAT,
    CMD_PHPCT,
    CMD_ATUNE,
    CMD_RAMPS,
    CMD_DELAY,
    CMD_TEMP,
    CMD_TMIN,
    CMD_TMAX,
    CMD_STAB,
    CMD_RAMP,
    CMD_START,
    CMD_STOP,
    CMD_SND,
    CMD_AIR,
    CMD_KP,
    CMD_KI,
    CMD_KD,
    CMD_COUNT
};

/* bits7..1 = terminador ('?'/'='/0), bit0 = need_usb. */
static const uint8_t CMD_META[CMD_COUNT] PROGMEM = {
    (uint8_t)('?' << 1) | 0,
    (uint8_t)('=' << 1) | 0,
    (uint8_t)('\0' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('\0' << 1) | 1,
    (uint8_t)('\0' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1,
    (uint8_t)('=' << 1) | 1
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

static uint8_t parse_01(const char *s, uint8_t *out)
{
    if (!s || !out || s[1] != '\0')
        return 1u;
    if (s[0] == '0') {
        *out = 0;
        return 0u;
    }
    if (s[0] == '1') {
        *out = 1;
        return 0u;
    }
    return 1u;
}

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

static uint8_t set_gain(app_state_t *st, int16_t *dst, const char *args)
{
    const char *p = args;
    int16_t v;

    if (parse_i16(&p, &v) || *p || v < 0 || v > 999)
        return 1u;
    *dst = v;
    cfg_save_global(st);
    ok_dirty(st);
    return 0u;
}

static void handle_line(app_state_t *st, char *line, uint8_t n)
{
    uint8_t v;
    uint8_t id;
    char term;
    const char *args;
    const char *p;
    uint16_t u0, u1, u2;
    int16_t i0;

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
    case CMD_STATUS:
        telemetry_emit(st);
        reply_ok(st);
        break;

    case CMD_DEVICEMODE:
        /* 0=MANUAL 1=USB */
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

    case CMD_PROGRAM:
        if (process_is_active(st) || pid_atune_active(st)) {
            reply_err(st, (uint8_t)PROTO_ERR_PROGRAM_BUSY);
            break;
        }
        /* 0=PREHEAT 1=HEAT 2=PID_TUNE (program_id_t). */
        p = args;
        if (parse_u16(&p, &u0) || *p || u0 > (uint16_t)PROG_PID_TUNE) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->program = (program_id_t)u0;
        cfg_load_program(st, st->program);
        ok_dirty(st);
        break;

    case CMD_TEMP:
        p = args;
        if (parse_u16(&p, &u0) || *p
            || u0 < st->temp_min_c || u0 > st->temp_max_c) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->t_set_c = u0;
        cfg_save_program(st, st->program);
        ok_dirty(st);
        break;

    case CMD_TMIN:
        p = args;
        if (parse_u16(&p, &u0) || *p
            || u0 < TEMP_MIN_C_LO || u0 > TEMP_MIN_C_HI
            || u0 > st->temp_max_c) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->temp_min_c = u0;
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_TMAX:
        p = args;
        if (parse_u16(&p, &u0) || *p
            || u0 < TEMP_MAX_C_LO || u0 > TEMP_MAX_C_HI
            || u0 < st->temp_min_c) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->temp_max_c = u0;
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_DELAY:
        p = args;
        if (parse_u16(&p, &u0) || *p || u0 > 3600u) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->delay_s = u0;
        cfg_save_program(st, st->program);
        ok_dirty(st);
        break;

    case CMD_RAMPS:
        if (parse_01(args, &v) == 0u && v == 1u) {
            st->ramps_en = 1u;
            cfg_save_global(st);
            st->telem_dirty = 1u;
            reply_ok(st);
        } else {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        }
        break;

    case CMD_RAMP:
        p = args;
        if (parse_u16(&p, &u0) || *p != ',' || u0 >= RAMP_STEPS_MAX) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        p++;
        if (parse_u16(&p, &u1) || *p != ','
            || u1 < st->temp_min_c || u1 > st->temp_max_c) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        p++;
        if (parse_u16(&p, &u2) || *p || u2 < 1u || u2 > 3600u) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->ramp_step[(uint8_t)u0].temp_c = u1;
        st->ramp_step[(uint8_t)u0].hold_s = u2;
        if (st->ramp_n < (uint8_t)(u0 + 1u))
            st->ramp_n = (uint8_t)(u0 + 1u);
        cfg_save_ramps(st);
        st->telem_dirty = 1u;
        reply_ok(st);
        break;

    case CMD_PREHEAT:
        if (parse_01(args, &v) == 0u) {
            st->preheat_en = v;
            cfg_save_global(st);
            ok_dirty(st);
        } else {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        }
        break;

    case CMD_PHPCT:
        p = args;
        if (parse_u16(&p, &u0) || *p
            || u0 < PREHEAT_PCT_LO || u0 > PREHEAT_PCT_HI
            || (u0 % PREHEAT_PCT_STEP) != 0u) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->preheat_pct = (uint8_t)u0;
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_STAB:
        p = args;
        if (parse_u16(&p, &u0) || *p || u0 < 1u || u0 > 3600u) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->stabilize_s = u0;
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_AIR:
        if (parse_01(args, &v) == 0u) {
            st->cooldown_air_en = v;
            cfg_save_global(st);
            ok_dirty(st);
        } else {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        }
        break;

    case CMD_SND:
        if (parse_01(args, &v) == 0u) {
            st->buzz_nav_en = v;
            cfg_save_global(st);
            ok_dirty(st);
        } else {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        }
        break;

    case CMD_ATUNE:
        p = args;
        if (parse_u16(&p, &u0) || *p != ','
            || u0 < ATUNE_MIN_CYCLES || u0 > ATUNE_MAX_CYCLES) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        p++;
        if (parse_i16(&p, &i0) || *p || i0 < 1 || i0 > 99) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        st->atune_cycles_target = (uint8_t)u0;
        st->atune_hyst_c_x10 = i0;
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_KP:
        if (set_gain(st, &st->pid_kp_x10, args))
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        break;
    case CMD_KI:
        if (set_gain(st, &st->pid_ki_x10, args))
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        break;
    case CMD_KD:
        if (set_gain(st, &st->pid_kd_x10, args))
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
        break;

    case CMD_PIDAPPLY:
        if (st->atune_phase != ATUNE_DONE) {
            reply_err(st, (uint8_t)PROTO_ERR_INVALID_PARAMETER);
            break;
        }
        pid_atune_apply(st);
        cfg_save_global(st);
        ok_dirty(st);
        break;

    case CMD_START:
        reply_from_proc(st, process_start(st, CTRL_USB));
        st->row_dirty = ROW_ALL;
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
