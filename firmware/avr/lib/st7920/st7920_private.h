#ifndef ST7920_PRIVATE_H
#define ST7920_PRIVATE_H

#include <stdint.h>
#include "fonts/font.h"

/* Solo para uso interno entre módulos ST7920 */

void st7920_set_gdram(uint8_t x, uint8_t y);
void st7920_write_gdram(uint8_t x, uint8_t y, uint8_t left, uint8_t right);
void st7920_clear_gdram(void);

/* Fuentes de lib/fonts (st7920_text.c). row_buf = 16 bytes (x 0..127,
 * MSB = izquierda). ty = fila superior del glifo; clear=1 borra píxeles
 * (texto invertido sobre fondo ON). */
void st7920_glyph_row(uint8_t *row_buf, uint8_t row_y, const font_t *f,
                      uint8_t glyph, uint8_t tx, uint8_t ty, uint8_t clear);

#endif
