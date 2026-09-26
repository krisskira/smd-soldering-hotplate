#include "telemetry.h"
#include "process.h"
#include "device_session.h"
#include "pid_atune.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

/* Emisión compacta: un solo put_u16; campos fijos cortos (contrato $HP). */

static void put_u16(uint16_t v)
{
    char tmp[5];
    uint8_t i = 0;

    if (v >= 10000u) {
        avr_uart_transmit_char('9');
        avr_uart_transmit_char('9');
        avr_uart_transmit_char('9');
        avr_uart_transmit_char('9');
        return;
    }
    if (v == 0) {
        avr_uart_transmit_char('0');
        return;
    }
    while (v > 0) {
        tmp[i++] = (char)('0' + (v % 10u));
        v /= 10u;
    }
    while (i > 0)
        avr_uart_transmit_char(tmp[--i]);
}

static void put_kv_u16(const char *key_P, uint16_t v)
{
    avr_uart_transmit_pstr(key_P);
    put_u16(v);
}

/* °C×10 → texto con un decimal. Solo se usa al emitir por UART. */
static void put_i16_x10(int16_t v)
{
    uint16_t a;

    if (v < 0) {
        avr_uart_transmit_char('-');
        a = (uint16_t)(-v);
    } else {
        a = (uint16_t)v;
    }
    put_u16((uint16_t)(a / 10u));
    avr_uart_transmit_char('.');
    avr_uart_transmit_char((char)('0' + (a % 10u)));
}

void telemetry_emit(const app_state_t *st)
{
    if (!st)
        return;

    avr_uart_transmit_pstr(PSTR("$HP,T="));
    if (st->sensor.valid)
        put_i16_x10(st->sensor.temp_c_x10);
    else
        avr_uart_transmit_pstr(PSTR("---"));

    avr_uart_transmit_pstr(PSTR(",DEVICE="));
    avr_uart_transmit_pstr(device_session_is_usb(st) ? PSTR("USB") : PSTR("MANUAL"));
    avr_uart_transmit_pstr(PSTR(",PROGRAM="));
    avr_uart_transmit_pstr(process_program_token(st->program));
    avr_uart_transmit_pstr(PSTR(",ACTION="));
    avr_uart_transmit_pstr(process_action_token(st));
    put_kv_u16(PSTR(",SET="), st->t_set_c);
    put_kv_u16(PSTR(",DELAY="), st->delay_s);
    put_kv_u16(PSTR(",RUN="), st->run_s);
    put_kv_u16(PSTR(",REMAIN="), st->t_remain_s);
    avr_uart_transmit_pstr(PSTR(",P1="));
    avr_uart_transmit_char(st->out_state[OUT_PTC1] ? '1' : '0');
    avr_uart_transmit_pstr(PSTR(",P2="));
    avr_uart_transmit_char(st->out_state[OUT_PTC2] ? '1' : '0');
    avr_uart_transmit_pstr(PSTR(",FAN="));
    avr_uart_transmit_char(st->out_state[OUT_FAN] ? '1' : '0');
    put_kv_u16(PSTR(",DUTY="), st->duty_pct);
    avr_uart_transmit_pstr(PSTR(",FLT="));
    avr_uart_transmit_char((st->phase == PH_FAULT || st->sensor.fault) ? '1' : '0');
    avr_uart_transmit_pstr(PSTR("\r\n"));
}

void telemetry_tick(const app_state_t *st)
{
    app_state_t *mut;

    if (!st || !st->telem_dirty)
        return;
    mut = (app_state_t *)st;
    mut->telem_dirty = 0;
    telemetry_emit(st);
}

#ifdef NO_PID_ATUNE
void telemetry_plot(const app_state_t *st)
{
    (void)st;
}
#else
void telemetry_plot(const app_state_t *st)
{
    /* Solo el autotune en sesión USB. Entrar a USB o correr otro programa
     * no publica muestras de gráfico. */
    if (!st || !device_session_is_usb(st) || !pid_atune_active(st))
        return;

    /* Orden: T, SET, DUTY, HHI, HLO, PKH, PKL. Fase y ciclo se leen en st. */
    avr_uart_transmit_pstr(PSTR("$HP,PLOT,"));
    if (st->sensor.valid)
        put_i16_x10(st->sensor.temp_c_x10);
    else
        avr_uart_transmit_pstr(PSTR("---"));
    avr_uart_transmit_char(',');
    put_u16(st->t_set_c);
    avr_uart_transmit_char(',');
    put_u16(st->duty_pct);
    avr_uart_transmit_char(',');
    put_i16_x10(st->atune_hyst_hi_x10);
    avr_uart_transmit_char(',');
    put_i16_x10(st->atune_hyst_lo_x10);
    avr_uart_transmit_char(',');
    put_i16_x10(st->atune_peak_hi_x10);
    avr_uart_transmit_char(',');
    put_i16_x10(st->atune_peak_lo_x10);
    avr_uart_transmit_pstr(PSTR("\r\n"));
}
#endif
