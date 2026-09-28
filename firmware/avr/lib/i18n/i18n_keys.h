/* IDs densos. Orden = TABLE[] en i18n.c. */
#ifndef I18N_KEYS_H
#define I18N_KEYS_H

#include <stdint.h>

#define I18N_PHASE_IDLE ((uint8_t)0u)
#define I18N_PHASE_WAIT ((uint8_t)1u)
#define I18N_PHASE_PREHEAT ((uint8_t)2u)
#define I18N_PHASE_STABLE ((uint8_t)3u)
#define I18N_PHASE_READY ((uint8_t)4u)   /* ALM — PH_ALARM */
#define I18N_PHASE_RUN ((uint8_t)5u)
#define I18N_PHASE_DONE ((uint8_t)6u)    /* FIN */
#define I18N_PHASE_FAULT ((uint8_t)7u)   /* ERR */
#define I18N_USB_EXIT ((uint8_t)8u)      /* OUT — pie */
#define I18N_PHASE_COOL ((uint8_t)9u)    /* AIR */
#define I18N_SET_DELAY ((uint8_t)10u)    /* DLY */
#define I18N_BTN_START ((uint8_t)11u)    /* RUN (comparte S_RUN) */
#define I18N_OFF ((uint8_t)12u)
#define I18N_BTN_CANCEL ((uint8_t)13u)   /* PARA */
#define I18N_TITLE_USB ((uint8_t)14u)    /* USB */

/* Alias legacy (mismo slot OFF / cool). */
#define I18N_PANEL_RAMP I18N_OFF
#define I18N_PROG_HEAT I18N_PHASE_COOL
#define I18N_NAV_SETTINGS I18N_OFF
#define I18N_TITLE_SETTINGS I18N_OFF
#define I18N_SET_AIR I18N_OFF
#define I18N_RAMP_STEP I18N_OFF
#define I18N_ON I18N_OFF
#define I18N_PANEL_SET I18N_OFF

#define I18N_PRODUCT_COUNT ((uint8_t)15u)

#endif
