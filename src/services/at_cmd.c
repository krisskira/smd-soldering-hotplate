#include "at_cmd.h"
#include "process.h"
#include "device_session.h"
#include "telemetry.h"
#include "outputs.h"
#include "pid_atune.h"
#include "cfg_store.h"
#include "ui/ui_router.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>
#include <string.h>

static char s_line[AT_LINE_MAX];
static uint8_t s_len;

static void reply_ok(app_state_t *st)
{
    if (st)
        st->usb_last_ok = 1;
    avr_uart_transmit_pstr(PSTR("OK\r\n"));
}

static void reply_err_P(app_state_t *st, const char *token_P)
{
    if (st)
        st->usb_last_ok = 0;
    avr_uart_transmit_pstr(PSTR("ERROR:"));
    avr_uart_transmit_pstr(token_P);
    avr_uart_transmit_pstr(PSTR("\r\n"));
}

static void reply_from_proc(app_state_t *st, uint8_t code)
{
    switch (code) {
    case PROG_OK:
        reply_ok(st);
        break;
    case PROG_ERR_SENSOR:
        reply_err_P(st, PSTR("SENSOR-INVALID"));
        break;
    case PROG_ERR_OVERTEMP:
        reply_err_P(st, PSTR("OVER-TEMPERATURE"));
        break;
    case PROG_ERR_BUSY:
        reply_err_P(st, PSTR("PROGRAM-BUSY"));
        break;
    case PROG_ERR_FAULT:
        reply_err_P(st, PSTR("DEVICE-BUSY"));
        break;
    default:
        reply_err_P(st, PSTR("INVALID-PARAMETER"));
        break;
    }
}

static int parse_01(const char *s, uint8_t *out)
{
    if (!s || !out)
        return -1;
    if (s[0] == '0' && s[1] == '\0') {
        *out = 0;
        return 0;
    }
    if (s[0] == '1' && s[1] == '\0') {
        *out = 1;
        return 0;
    }
    return -1;
}

/* Decimal u16; avanza *pp hasta no-dígito. Devuelve 0 si ok. */
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

static uint8_t streq_P(const char *a, const char *b_P)
{
    return (uint8_t)(strcmp_P(a, b_P) == 0);
}

static uint8_t require_usb(app_state_t *st)
{
    if (device_session_is_usb(st))
        return 1u;
    reply_err_P(st, PSTR("USB-MODE-REQUIRED"));
    return 0u;
}

static void handle_line(app_state_t *st, char *line)
{
    uint8_t v;
    const char *p;
    uint16_t u0, u1, u2;

    if (!st || !line)
        return;

    {
        uint8_t n = (uint8_t)strlen(line);
        while (n > 0 && (line[n - 1] == ' ' || line[n - 1] == '\t'))
            line[--n] = '\0';
    }

    if (line[0] == '\0')
        return;

    if (streq_P(line, PSTR("AT"))) {
        reply_ok(st);
        return;
    }

    if (streq_P(line, PSTR("AT+STATUS?"))) {
        telemetry_emit(st);
        reply_ok(st);
        return;
    }

    if (streq_P(line, PSTR("AT+DEVICEMODE?"))) {
        avr_uart_transmit_pstr(PSTR("+DEVICEMODE:"));
        avr_uart_transmit_pstr(device_session_is_usb(st)
                                   ? PSTR("USB\r\n")
                                   : PSTR("MANUAL\r\n"));
        reply_ok(st);
        return;
    }

    if (strncmp_P(line, PSTR("AT+DEVICEMODE="), 14) == 0) {
        p = line + 14;
        if (streq_P(p, PSTR("USB"))) {
            if (device_session_enter_usb(st) != 0) {
                reply_err_P(st, PSTR("DEVICE-BUSY"));
                return;
            }
            ui_enter_view(st, VIEW_USB);
            telemetry_emit(st);
            reply_ok(st);
            return;
        }
        if (streq_P(p, PSTR("MANUAL"))) {
            device_session_leave_manual(st, 0u);
            if (st->view == VIEW_USB)
                ui_enter_view(st, VIEW_HOME);
            telemetry_emit(st);
            reply_ok(st);
            return;
        }
        reply_err_P(st, PSTR("INVALID-PARAMETER"));
        return;
    }

    if (!require_usb(st))
        return;

    if (strncmp_P(line, PSTR("AT+PROGRAM="), 11) == 0) {
        p = line + 11;
        if (process_is_active(st) || pid_atune_active(st)) {
            reply_err_P(st, PSTR("PROGRAM-BUSY"));
            return;
        }
        if (streq_P(p, PSTR("START_IN")))
            st->program = PROG_START_IN;
        else if (streq_P(p, PSTR("STOP_IN")))
            st->program = PROG_STOP_IN;
        else if (streq_P(p, PSTR("PREHEAT")))
            st->program = PROG_PREHEAT;
        else if (streq_P(p, PSTR("PID_TUNE")))
            st->program = PROG_PID_TUNE;
        else {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        cfg_load_program(st, st->program);
        st->row_dirty = ROW_ALL;
        st->telem_dirty = 1u;
        reply_ok(st);
        return;
    }

    if (strncmp_P(line, PSTR("AT+TEMP="), 8) == 0) {
        p = line + 8;
        if (parse_u16(&p, &u0) || *p
            || u0 < TEMP_MIN_SET_C || u0 > TEMP_MAX_SET_C) {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        st->t_set_c = u0;
        cfg_save_program(st, st->program);
        st->row_dirty = ROW_ALL;
        st->telem_dirty = 1u;
        reply_ok(st);
        return;
    }

    if (strncmp_P(line, PSTR("AT+DELAY="), 9) == 0) {
        p = line + 9;
        if (parse_u16(&p, &u0) || *p || u0 > 3600u) {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        st->delay_s = u0;
        st->run_s = u0;
        cfg_save_program(st, st->program);
        st->row_dirty = ROW_ALL;
        st->telem_dirty = 1u;
        reply_ok(st);
        return;
    }

    /* AT+RAMP=<i>,<temp>,<sec>  i=0..3 */
    if (strncmp_P(line, PSTR("AT+RAMP="), 8) == 0) {
        p = line + 8;
        if (parse_u16(&p, &u0) || *p != ',' || u0 >= RAMP_STEPS_MAX) {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        p++;
        if (parse_u16(&p, &u1) || *p != ','
            || u1 < TEMP_MIN_SET_C || u1 > TEMP_MAX_SET_C) {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        p++;
        if (parse_u16(&p, &u2) || *p || u2 < 1u || u2 > 3600u) {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
            return;
        }
        st->ramp_step[(uint8_t)u0].temp_c = u1;
        st->ramp_step[(uint8_t)u0].hold_s = u2;
        if (st->ramp_n < (uint8_t)(u0 + 1u))
            st->ramp_n = (uint8_t)(u0 + 1u);
        cfg_save_ramps(st);
        st->telem_dirty = 1u;
        reply_ok(st);
        return;
    }

    if (strncmp_P(line, PSTR("AT+PREHEAT="), 11) == 0) {
        if (parse_01(line + 11, &v) == 0) {
            st->preheat_en = v;
            cfg_save_global(st);
            st->row_dirty = ROW_ALL;
            st->telem_dirty = 1u;
            reply_ok(st);
        } else {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
        }
        return;
    }

    if (strncmp_P(line, PSTR("AT+RAMPS="), 9) == 0) {
        if (parse_01(line + 9, &v) == 0) {
            st->ramps_en = v;
            cfg_save_global(st);
            st->telem_dirty = 1u;
            reply_ok(st);
        } else {
            reply_err_P(st, PSTR("INVALID-PARAMETER"));
        }
        return;
    }

    if (streq_P(line, PSTR("AT+START"))) {
        reply_from_proc(st, process_start(st, CTRL_USB));
        st->row_dirty = ROW_ALL;
        return;
    }

    if (streq_P(line, PSTR("AT+STOP"))) {
        process_stop(st, CTRL_USB);
        st->row_dirty = ROW_ALL;
        telemetry_emit(st);
        reply_ok(st);
        return;
    }

    reply_err_P(st, PSTR("INVALID-COMMAND"));
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
            if (s_len > 0) {
                s_line[s_len] = '\0';
                handle_line(st, s_line);
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

uint8_t at_cmd_stream_on(void)
{
    return 0;
}

void at_cmd_set_stream(app_state_t *st, uint8_t on)
{
    (void)on;
    (void)st;
}
