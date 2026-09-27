#ifndef OUTPUTS_H
#define OUTPUTS_H

#include <stdint.h>
#include "../app/app_config.h"

typedef struct {
    const char *label; /* reservado; no usado */
    void (*on)(void);
    void (*off)(void);
    uint8_t is_heater;
} output_desc_t;

void outputs_init(void);
void output_set(uint8_t *state, uint8_t idx, uint8_t on);
void outputs_bank_set(uint8_t *state, uint8_t on);
uint8_t outputs_heaters_off(uint8_t *state);

#endif
