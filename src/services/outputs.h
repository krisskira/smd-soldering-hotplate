#ifndef OUTPUTS_H
#define OUTPUTS_H

#include <stdint.h>
#include "../app/app_config.h"

typedef struct {
    const char *label; /* opcional; preferir outputs_label() */
    void (*on)(void);
    void (*off)(void);
    uint8_t is_heater;
} output_desc_t;

void outputs_init(void);

const output_desc_t *outputs_table(void);
/** Etiqueta localizada de la salida (i18n). */
const char *outputs_label(uint8_t idx);

void output_set(uint8_t *state, uint8_t idx, uint8_t on);

/** Banco PTC1+PTC2 juntos (procesos automáticos). */
void outputs_bank_set(uint8_t *state, uint8_t on);

/** Apaga todas las salidas marcadas como calefactor. Devuelve cuántas cortó. */
uint8_t outputs_heaters_off(uint8_t *state);

/** Si 1, no emitir logs de cambio de salida (STREAM activo). */
void outputs_set_quiet(uint8_t quiet);

#endif
