#include "i18n_c.h"
#include <avr/pgmspace.h>
#include <string.h>

#define BUF_LEN 24u

static const char S_PANEL_RAMP[] PROGMEM = "RAMPA:";
static const char S_T_USB[] PROGMEM = "USB";
static const char S_PH_IDLE[] PROGMEM = "IDLE";
static const char S_PH_WAIT[] PROGMEM = "ESPERA";
static const char S_PH_PRE[] PROGMEM = "PRECAL";
static const char S_PH_STAB[] PROGMEM = "ESTAB";
static const char S_PH_RDY[] PROGMEM = "LISTO";
static const char S_PH_RUN[] PROGMEM = "RUN";
static const char S_PH_DONE[] PROGMEM = "DONE";
static const char S_PH_FLT[] PROGMEM = "FAULT";
static const char S_USB_EXIT[] PROGMEM = "Salir";
static const char S_P_HEAT[] PROGMEM = "Heat";
static const char S_P_STOP[] PROGMEM = "Parar";
static const char S_P_PRE[] PROGMEM = "Prec";
static const char S_P_PID[] PROGMEM = "PID";
static const char S_NAV_SET[] PROGMEM = "Ajustes";
static const char S_T_SET[] PROGMEM = "AJUSTE";
static const char S_SET_SOUND[] PROGMEM = "Sonido";
static const char S_SET_PRE[] PROGMEM = "ESTAB";
static const char S_SET_AIR[] PROGMEM = "Aire";
static const char S_RAMP_STEP[] PROGMEM = "Paso";
static const char S_ON[] PROGMEM = "ON";
static const char S_OFF[] PROGMEM = "OFF";
static const char S_PANEL_ELAP[] PROGMEM = "T.TRAN:";
static const char S_PANEL_SET[] PROGMEM = "SET:";
static const char S_SET_PID[] PROGMEM = "PID";
static const char S_PID_AUTO[] PROGMEM = "Auto";
static const char S_SET_PCT[] PROGMEM = "P%";
static const char S_NULL[] PROGMEM = "?";

static const char *const TABLE[] PROGMEM = {
    S_PANEL_RAMP, S_T_USB, S_PH_IDLE, S_PH_WAIT, S_PH_PRE, S_PH_STAB,
    S_PH_RDY, S_PH_RUN, S_PH_DONE, S_PH_FLT, S_USB_EXIT, S_P_HEAT,
    S_P_STOP, S_P_PRE, S_P_PID, S_NAV_SET, S_T_SET, S_SET_SOUND,
    S_SET_PRE, S_SET_AIR, S_RAMP_STEP, S_ON, S_OFF, S_PANEL_ELAP,
    S_PANEL_SET, S_SET_PID, S_PID_AUTO, S_SET_PCT,
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
