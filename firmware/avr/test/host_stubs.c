/* Stubs para compilar pid_atune.c en host (make pid-atune-host-test). */
#include "app/app_state.h"
#include <stdint.h>

static uint16_t s_ms;

void host_set_ms(uint16_t ms)
{
    s_ms = ms;
}

void host_advance_ms(uint16_t dt)
{
    s_ms = (uint16_t)(s_ms + dt);
}

uint16_t delay_ms(void)
{
    return s_ms;
}

uint16_t delay_sec(void)
{
    return (uint16_t)(s_ms / 1000u);
}

void outputs_bank_set(uint8_t *state, uint8_t on)
{
    if (!state)
        return;
    state[OUT_PTC1] = on ? 1u : 0u;
    state[OUT_PTC2] = on ? 1u : 0u;
}

void fan_on(void)
{
}

void fan_off(void)
{
}

#ifndef PID_HOST_TEST
void pid_reset(app_state_t *st)
{
    (void)st;
}

void pid_on_set_step(app_state_t *st)
{
    (void)st;
}
#endif

void at_cmd_set_stream(app_state_t *st, uint8_t on)
{
    if (st)
        st->atune_stream = on ? 1u : 0u;
}
