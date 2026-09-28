#include "i18n_c.h"
#include <avr/pgmspace.h>
#include <string.h>

#define BUF_LEN 24u

static const char S_PANEL_RAMP[] PROGMEM = "RAMPA:";
static const char S_T_USB[] PROGMEM = "USB MODE"; /* 8 chars */
static const char S_PH_IDLE[] PROGMEM = "IDLE";
static const char S_PH_WAIT[] PROGMEM = "ESPERA";
static const char S_PH_PRE[] PROGMEM = "PRECAL";
static const char S_PH_STAB[] PROGMEM = "ESTAB";
static const char S_PH_RDY[] PROGMEM = "LISTO";
static const char S_PH_RUN[] PROGMEM = "RUN";
static const char S_PH_DONE[] PROGMEM = "DONE";
static const char S_PH_FLT[] PROGMEM = "FAULT";
static const char S_USB_EXIT[] PROGMEM = "Salir";
static const char S_HEAT[] PROGMEM = "HEAT";
static const char S_NAV_SET[] PROGMEM = "Ajustes";
static const char S_SET_DELAY[] PROGMEM = "Retraso";
static const char S_BTN_START[] PROGMEM = "Iniciar";
static const char S_ON[] PROGMEM = "ON";
static const char S_OFF[] PROGMEM = "OFF";
static const char S_BTN_CANCEL[] PROGMEM = "Cancel";
static const char S_NULL[] PROGMEM = "?";

/* Slots legacy reutilizan OFF / Ajustes para ahorrar flash. */
static const char *const TABLE[] PROGMEM = {
    S_PANEL_RAMP, S_T_USB, S_PH_IDLE, S_PH_WAIT, S_PH_PRE, S_PH_STAB,
    S_PH_RDY, S_PH_RUN, S_PH_DONE, S_PH_FLT, S_USB_EXIT, S_HEAT,
    S_NAV_SET, S_NAV_SET, S_SET_DELAY, S_BTN_START, S_OFF, S_OFF,
    S_ON, S_OFF, S_OFF, S_BTN_CANCEL,
};

static char s_buf[BUF_LEN];

const char *i18n_tr_hash(uint8_t id)
{
    PGM_P src = S_NULL;

    if (id < (uint8_t)(sizeof(TABLE) / sizeof(TABLE[0])))
        src = (PGM_P)pgm_read_word(&TABLE[id]);
    strcpy_P(s_buf, src);
    s_buf[BUF_LEN - 1u] = '\0';
    return s_buf;
}
