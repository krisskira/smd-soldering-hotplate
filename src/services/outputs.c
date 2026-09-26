#include "outputs.h"
#include "i18n/i18n_c.h"
#include "lib/ports/ports.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

static uint8_t s_quiet;

static const output_desc_t s_outputs[OUTPUT_COUNT] = {
    { 0, ptc1_on, ptc1_off, 1 },
    { 0, ptc2_on, ptc2_off, 1 },
    { 0, fan_on,  fan_off,  0 },
};

static const uint8_t s_out_keys[OUTPUT_COUNT] = {
    I18N_OUT_PTC1, I18N_OUT_PTC2, I18N_OUT_FAN
};

static const char *out_label(uint8_t idx)
{
    if (idx >= OUTPUT_COUNT)
        return "";
    return i18n_tr_hash(s_out_keys[idx]);
}

void outputs_init(void)
{
    ptc_init();
    fan_init();
    s_quiet = 0;
}

void outputs_set_quiet(uint8_t quiet)
{
    s_quiet = quiet ? 1u : 0u;
}

const output_desc_t *outputs_table(void)
{
    return s_outputs;
}

const char *outputs_label(uint8_t idx)
{
    return out_label(idx);
}

void output_set(uint8_t *state, uint8_t idx, uint8_t on)
{
    if (!state || idx >= OUTPUT_COUNT)
        return;

    state[idx] = on ? 1u : 0u;
    if (on)
        s_outputs[idx].on();
    else
        s_outputs[idx].off();

    if (!s_quiet) {
        avr_uart_transmit_string(out_label(idx));
        avr_uart_transmit_pstr(on ? PSTR(" = ON\r\n") : PSTR(" = OFF\r\n"));
    }
}

void outputs_bank_set(uint8_t *state, uint8_t on)
{
    if (!state)
        return;
    output_set(state, OUT_PTC1, on);
    output_set(state, OUT_PTC2, on);
}

uint8_t outputs_heaters_off(uint8_t *state)
{
    uint8_t cut = 0;

    if (!state)
        return 0;

    for (uint8_t i = 0; i < OUTPUT_COUNT; i++) {
        if (s_outputs[i].is_heater && state[i]) {
            output_set(state, i, 0);
            cut++;
        }
    }
    return cut;
}
