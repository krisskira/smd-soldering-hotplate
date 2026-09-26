/*
 * font_icons — símbolos 8×8: ENTER, START, TIMER, CFG.
 * Glifo i = ICO_* ; en un texto el carácter es i+1 (el 0 termina la cadena).
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

    /* START: triángulo play apuntando a la derecha */
    0x00, /* ........ */
    0xC0, /* ##...... */
    0xF0, /* ####.... */
    0xFC, /* ######.. */
    0xFF, /* ######## */
    0xFC, /* ######.. */
    0xF0, /* ####.... */
    0xC0, /* ##...... */

    /* TIMER: reloj analógico */
    0x3C, /* ..####.. */
    0x42, /* .#....#. */
    0x99, /* #..##..# */
    0xA5, /* #.#..#.# */
    0x81, /* #......# */
    0x81, /* #......# */
    0x42, /* .#....#. */
    0x3C, /* ..####.. */

    /* CFG: engranaje */
    0x18, /* ...##... */
    0x7E, /* .######. */
    0x7E, /* .######. */
    0xDB, /* ##.##.## */
    0xDB, /* ##.##.## */
    0x7E, /* .######. */
    0x7E, /* .######. */
    0x18, /* ...##... */
};

const font_t FONT_ICONS = {
    font_icons_data, 0, 8u, 8u, 9u, 1u, 4u, FONT_NO_GLYPH, FONT_ROWS
};
