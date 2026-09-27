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
    kv_b(PSTR(",P1="), st->out_state[OUT_PTC1]);
    kv_b(PSTR(",P2="), st->out_state[OUT_PTC2]);
    kv_b(PSTR(",F="), st->out_state[OUT_FAN]);
    kv_u(PSTR(",DU="), st->duty_pct);
    kv_b(PSTR(",FL="),
         (uint8_t)(st->phase == PH_FAULT || st->sensor.fault));
    kv_u(PSTR(",MN="), st->temp_min_c);
    kv_u(PSTR(",MX="), st->temp_max_c);
    kv_i(PSTR(",KP="), st->pid_kp_x10);
    kv_i(PSTR(",KI="), st->pid_ki_x10);
    kv_i(PSTR(",KD="), st->pid_kd_x10);
    /* Flags + atune (host reconstruye UI / gráfico). */
    kv_u(PSTR(",CF="),
         (uint16_t)((st->preheat_en ? 1u : 0u)
                    | (st->cooldown_air_en ? 2u : 0u)
                    | (st->buzz_nav_en ? 4u : 0u)
                    | (st->ramps_en ? 8u : 0u)
                    | ((uint16_t)st->preheat_pct << 8)));
    kv_u(PSTR(",SB="), st->stabilize_s);
    kv_u(PSTR(",RN="), st->ramp_n);
    kv_u(PSTR(",RI="), st->ramp_idx);
    kv_u(PSTR(",AP="), (uint16_t)st->atune_phase);
    kv_u(PSTR(",AC="), st->atune_cycles);
    kv_u(PSTR(",AG="), st->atune_cycles_target);
    kv_i(PSTR(",AH="), st->atune_hyst_c_x10);
    kv_i(PSTR(",AK="), st->atune_kp_x10);
    kv_i(PSTR(",AI="), st->atune_ki_x10);
    kv_i(PSTR(",AD="), st->atune_kd_x10);
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
