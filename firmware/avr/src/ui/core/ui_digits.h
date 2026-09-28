#ifndef UI_DIGITS_H
#define UI_DIGITS_H

#include <stdint.h>

/**
 * Escribe dígitos decimales de v en dst (sin NUL). Devuelve longitud 1..5.
 * v se satura a 9999 para el path UART; UI puede pasar valores menores.
 */
uint8_t ui_u16_digits(uint16_t v, char *dst);

#endif
