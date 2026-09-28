#ifndef ST7920_PRIVATE_H
#define ST7920_PRIVATE_H

#include <stdint.h>
#include "fonts/font.h"

/* Solo para uso interno entre módulos ST7920 */

void st7920_set_gdram(uint8_t x, uint8_t y);
void st7920_write_gdram(uint8_t x, uint8_t y, uint8_t left, uint8_t right);
void st7920_clear_gdram(void);
void st7920_clear_gdram_buffer(void);

/* Render por filas: añade un píxel al buffer de fila (solo x; y implícita) */
void st7920_row_set_pixel(uint16_t *row_buf, uint8_t x);
void st7920_row_clear_pixel(uint16_t *row_buf, uint8_t x);

/* Fuentes de lib/fonts (st7920_text.c). ty = fila superior del glifo;
 * clear=1 borra píxeles (texto invertido sobre fondo ON). */
void st7920_glyph_row(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                      uint8_t glyph, uint8_t tx, uint8_t ty, uint8_t clear);

#endif
