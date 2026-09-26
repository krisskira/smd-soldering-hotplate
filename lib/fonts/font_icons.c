/*
 * font_icons — un solo símbolo 8×8: confirmar / entrar.
 * Glifo 0 = ICO_ENTER. En un texto el carácter es 1 (el 0 termina la cadena).
 * No entra al binario mientras UI_NO_ICONS.
 * Formato FONT_ROWS: 1 byte por fila, MSB = izquierda.
 */
#include "font.h"
#include <avr/pgmspace.h>

static const uint8_t font_icons_data[] PROGMEM = {
    /* ENTER: retorno, asta a la derecha y punta hacia la izquierda */
    0x01, /* .......# */
    0x01, /* .......# */
    0x11, /* ...#...# */
    0x31, /* ..##...# */
    0xFF, /* ######## */
    0x30, /* ..##.... */
    0x10, /* ...#.... */
    0x00, /* ........ */
};

const font_t FONT_ICONS = {
    font_icons_data, 0, 8u, 8u, 9u, 1u, 1u, FONT_NO_GLYPH, FONT_ROWS
};
