#ifndef SAFETY_H
#define SAFETY_H

#include <stdint.h>
#include "../app/app_state.h"

/**
 * Si la lectura es válida y T >= TEMP_LIMIT_C, apaga calefactores.
 * Devuelve 1 si cortó; el llamador marca EVT_SAFETY_TRIP / refresca UI.
 */
uint8_t safety_apply_limit(sensor_reading_t *reading, uint8_t *out_state);

#endif
