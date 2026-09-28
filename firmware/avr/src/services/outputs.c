#include "outputs.h"
#include "lib/ports/ports.h"

static const output_desc_t s_outputs[OUTPUT_COUNT] = {
    { 0, ptc1_on, ptc1_off, 1 },
    { 0, ptc2_on, ptc2_off, 1 },
    { 0, fan_on,  fan_off,  0 },
};

void outputs_init(void)
{
    ptc_init();
    fan_init();
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
    uint8_t i;

    if (!state)
        return 0;

    for (i = 0; i < OUTPUT_COUNT; i++) {
        if (s_outputs[i].is_heater && state[i]) {
            output_set(state, i, 0);
            cut++;
        }
    }
    return cut;
}
