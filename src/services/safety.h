#ifndef SAFETY_H
#define SAFETY_H

#include <stdint.h>
#include "../app/app_state.h"

/**
 * Si la lectura es válida y T >= st->temp_max_c, apaga calefactores.
 * Devuelve 1 si cortó.
 */
uint8_t safety_apply_limit(app_state_t *st);

#endif
