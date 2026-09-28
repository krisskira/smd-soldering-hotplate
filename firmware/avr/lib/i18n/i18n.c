#include "i18n_c.h"
#include <avr/pgmspace.h>

#define BUF_LEN 8u

static const char S_IDLE[] PROGMEM = "IDLE";
static const char S_WAIT[] PROGMEM = "WAIT";
static const char S_PRE[] PROGMEM = "PREHEAT";
static const char S_STAB[] PROGMEM = "STABLE";
static const char S_ALM[] PROGMEM = "ALM";
static const char S_RUN[] PROGMEM = "RUN";
static const char S_END[] PROGMEM = "END";
static const char S_FLT[] PROGMEM = "ERR";
static const char S_SALIR[] PROGMEM = "OUT";
static const char S_AIR[] PROGMEM = "AIR";
static const char S_DLY[] PROGMEM = "DLY";
static const char S_OFF[] PROGMEM = "OFF";
static const char S_PARA[] PROGMEM = "STOP";
static const char S_UMODE[] PROGMEM = "USB";
static const char S_NULL[] PROGMEM = "*"; /* sin glifo '?' */

static const char *const TABLE[] PROGMEM = {
    S_IDLE, S_WAIT, S_PRE, S_STAB, S_ALM, S_RUN, S_END, S_FLT,
    S_SALIR, S_AIR, S_DLY, S_RUN, S_OFF, S_PARA, S_UMODE,
};

static char s_buf[BUF_LEN];

const char *i18n_tr_hash(uint8_t id)
{
    PGM_P src = S_NULL;
    uint8_t i;
    char c;

    if (id < (uint8_t)(sizeof(TABLE) / sizeof(TABLE[0])))
        src = (PGM_P)pgm_read_word(&TABLE[id]);
    for (i = 0; i < (BUF_LEN - 1u); i++) {
        c = (char)pgm_read_byte(src + i);
        if (c == '\0')
            break;
        s_buf[i] = c;
    }
    s_buf[i] = '\0';
    return s_buf;
}
