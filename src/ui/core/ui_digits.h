#ifndef UI_DIGITS_H
#define UI_DIGITS_H

#include <stdint.h>

/**
 * Escribe dígitos decimales de v en dst (sin NUL). Devuelve longitud 1..5.
 * v se satura a 9999 para el path UART; UI puede pasar valores menores.
 */
static inline uint8_t ui_u16_digits(uint16_t v, char *dst)
{
    char tmp[5];
    uint8_t n = 0, i = 0;

    if (v >= 10000u)
        v = 9999u;
    do {
        tmp[n++] = (char)('0' + (v % 10u));
        v /= 10u;
    } while (v && n < 5u);
    while (n)
        dst[i++] = tmp[--n];
    return i;
}

#endif
