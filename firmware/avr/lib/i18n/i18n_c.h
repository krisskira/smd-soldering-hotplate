#ifndef I18N_C_H
#define I18N_C_H

#include <stdint.h>
#include "i18n_keys.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Traduce por id I18N_*. El puntero vale hasta la siguiente llamada.
 */
const char *i18n_tr_hash(uint8_t id);

#ifdef __cplusplus
}
#endif

#endif
