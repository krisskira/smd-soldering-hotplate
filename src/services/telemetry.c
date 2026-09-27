#include "telemetry.h"
#include "process.h"
#include "pid_atune.h"
#include "proto_codes.h"
#include "proto_tokens.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

static void put_i16_x10(int16_t v)
{
    uint16_t a;

    if (v < 0) {
        avr_uart_transmit_char('-');
        a = (uint16_t)(-v);
    } else {
        a = (uint16_t)v;
    }
    proto_put_u16((uint16_t)(a / 10u));
    avr_uart_transmit_char('.');
    avr_uart_transmit_char((char)('0' + (a % 10u)));
}

static void kv_u(const char *key_P, uint16_t v)
{
    avr_uart_transmit_pstr(key_P);
    proto_put_u16(v);
}

static void kv_i(const char *key_P, int16_t v)
{
    avr_uart_transmit_pstr(key_P);
    if (v < 0) {
        avr_uart_transmit_char('-');
        proto_put_u16((uint16_t)(-v));
    } else {
        proto_put_u16((uint16_t)v);
    }
}

static void kv_b(const char *key_P, uint8_t on)
{
    avr_uart_transmit_pstr(key_P);
    avr_uart_transmit_char(on ? '1' : '0');
}

void telemetry_emit(const app_state_t *st)
{
    uint8_t act;

    if (!st)
        return;

    act = pid_atune_active(st) ? PROTO_ACTION_TUNING : (uint8_t)st->phase;

    avr_uart_transmit_pstr(PSTR("$HP,T="));
    if (st->sensor.valid)
        put_i16_x10(st->sensor.temp_c_x10);
    else
        avr_uart_transmit_pstr(PSTR("---"));

    kv_u(PSTR(",P="), (uint16_t)st->program);
    kv_u(PSTR(",A="), act);
    kv_u(PSTR(",SET="), st->t_set_c);
    kv_u(PSTR(",DLY="), st->delay_s);
    kv_u(PSTR(",RUN="), st->t_remain_s);
    kv_u(PSTR(",EL="), st->t_elapsed_s);
    kv_u(PSTR(",DU="), st->duty_pct);
    kv_b(PSTR(",F="), st->out_state[OUT_FAN]);
    kv_u(PSTR(",RI="), st->ramp_idx);
    kv_b(PSTR(",FL="),
         (uint8_t)(st->phase == PH_FAULT || st->sensor.fault));
    if (st->atune_stream) {
        int16_t kp, ki, kd;

        pid_atune_result(&kp, &ki, &kd);
        kv_u(PSTR(",AP="), (uint16_t)st->atune_phase);
        kv_u(PSTR(",AC="), st->atune_cycles);
        kv_i(PSTR(",AK="), kp);
        kv_i(PSTR(",AI="), ki);
        kv_i(PSTR(",AD="), kd);
    }
    avr_uart_transmit_pstr(PROTO_CRLF);
}

void telemetry_emit_cfg(const app_state_t *st)
{
    if (!st)
        return;

    avr_uart_transmit_pstr(PSTR("$CF"));
    kv_u(PSTR(",MN="), st->temp_min_c);
    kv_u(PSTR(",MX="), st->temp_max_c);
    kv_i(PSTR(",KP="), st->pid_kp_x10);
    kv_i(PSTR(",KI="), st->pid_ki_x10);
    kv_i(PSTR(",KD="), st->pid_kd_x10);
    kv_u(PSTR(",PH="), st->preheat_en);
    kv_u(PSTR(",PCT="), st->preheat_pct);
    kv_u(PSTR(",SB="), st->stabilize_s);
    kv_u(PSTR(",DLY="), st->delay_s);
    kv_u(PSTR(",AIR="), st->cooldown_air_en);
    kv_u(PSTR(",SND="), st->buzz_nav_en);
    kv_u(PSTR(",RN="), st->ramp_n);
    avr_uart_transmit_pstr(PROTO_CRLF);
}

/* $R,N=<n>,0=<°C>/<s>,1=...,2=...,3=... — siempre 4 huecos. */
void telemetry_emit_ramps(const app_state_t *st)
{
    uint8_t i;

    if (!st)
        return;

    avr_uart_transmit_pstr(PSTR("$R"));
    kv_u(PSTR(",N="), st->ramp_n);
    for (i = 0; i < RAMP_STEPS_MAX; i++) {
        avr_uart_transmit_char(',');
        avr_uart_transmit_char((char)('0' + i));
        avr_uart_transmit_char('=');
        proto_put_u16(st->ramp_step[i].temp_c);
        avr_uart_transmit_char('/');
        proto_put_u16(st->ramp_step[i].hold_s);
    }
    avr_uart_transmit_pstr(PROTO_CRLF);
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
