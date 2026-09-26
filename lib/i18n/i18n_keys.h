/* IDs densos. Orden = TABLE[] en i18n.c. Solo textos que el binario pinta. */
#ifndef I18N_KEYS_H
#define I18N_KEYS_H

#include <stdint.h>

#define I18N_TITLE_HOME ((uint8_t)0u)
#define I18N_NAV_USB ((uint8_t)1u)
#define I18N_TITLE_USB ((uint8_t)2u)

#define I18N_PHASE_IDLE ((uint8_t)3u)
#define I18N_PHASE_WAIT ((uint8_t)4u)
#define I18N_PHASE_PREHEAT ((uint8_t)5u)
#define I18N_PHASE_STABLE ((uint8_t)6u)
#define I18N_PHASE_READY ((uint8_t)7u)
#define I18N_PHASE_RUN ((uint8_t)8u)
#define I18N_PHASE_DONE ((uint8_t)9u)
#define I18N_PHASE_FAULT ((uint8_t)10u)

#define I18N_OUT_PTC1 ((uint8_t)11u)
#define I18N_OUT_PTC2 ((uint8_t)12u)
#define I18N_OUT_FAN ((uint8_t)13u)

#define I18N_USB_EXIT ((uint8_t)14u)

#define I18N_PROG_START_IN ((uint8_t)15u)
#define I18N_PROG_STOP_IN ((uint8_t)16u)
#define I18N_PROG_PREHEAT ((uint8_t)17u)
#define I18N_PROG_PID_TUNE ((uint8_t)18u)

#define I18N_PRODUCT_COUNT ((uint8_t)19u)

#endif
