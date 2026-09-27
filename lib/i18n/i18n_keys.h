/* IDs densos. Orden = TABLE[] en i18n.c. */
#ifndef I18N_KEYS_H
#define I18N_KEYS_H

#include <stdint.h>

#define I18N_PANEL_RAMP ((uint8_t)0u)
#define I18N_TITLE_USB ((uint8_t)1u)
#define I18N_PHASE_IDLE ((uint8_t)2u)
#define I18N_PHASE_WAIT ((uint8_t)3u)
#define I18N_PHASE_PREHEAT ((uint8_t)4u)
#define I18N_PHASE_STABLE ((uint8_t)5u)
#define I18N_PHASE_READY ((uint8_t)6u)
#define I18N_PHASE_RUN ((uint8_t)7u)
#define I18N_PHASE_DONE ((uint8_t)8u)
#define I18N_PHASE_FAULT ((uint8_t)9u)
#define I18N_USB_EXIT ((uint8_t)10u)
#define I18N_PROG_HEAT ((uint8_t)11u)
#define I18N_PROG_STOP_IN ((uint8_t)12u) /* reserved / unused */
#define I18N_PROG_PREHEAT ((uint8_t)13u)
#define I18N_PROG_PID_TUNE ((uint8_t)14u)
#define I18N_NAV_SETTINGS ((uint8_t)15u)
#define I18N_TITLE_SETTINGS ((uint8_t)16u)
#define I18N_SET_SOUND ((uint8_t)17u)
#define I18N_SET_PREHEAT ((uint8_t)18u)
#define I18N_SET_AIR ((uint8_t)19u)
#define I18N_RAMP_STEP ((uint8_t)20u)
#define I18N_ON ((uint8_t)21u)
#define I18N_OFF ((uint8_t)22u)
#define I18N_PANEL_ELAPSED ((uint8_t)23u)
#define I18N_PANEL_SET ((uint8_t)24u)
#define I18N_SET_PID ((uint8_t)25u)
#define I18N_SET_PID_AUTO ((uint8_t)26u)
#define I18N_SET_PRE_PCT ((uint8_t)27u)

#define I18N_PRODUCT_COUNT ((uint8_t)28u)

#endif
