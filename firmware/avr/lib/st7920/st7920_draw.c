/*
 * ST7920 — helpers de pixel/fila. El path de lista de comandos (line/rect/
 * bitmap/render) se eliminó: la UI usa solo st7920_draw_band / GDRAM directo.
 */
#include "st7920.h"
#include "st7920_private.h"
#include <stdint.h>

#define LCD_WIDTH  128

void st7920_row_set_pixel(uint16_t *row_buf, uint8_t x)
{
    uint8_t block;
    uint8_t bit;

    if (x >= LCD_WIDTH)
        return;
    block = (uint8_t)(x / 16u);
    bit = (uint8_t)(15u - (x % 16u));
    row_buf[block] |= (uint16_t)(1u << bit);
}

void st7920_row_clear_pixel(uint16_t *row_buf, uint8_t x)
{
    uint8_t block;
    uint8_t bit;

    if (x >= LCD_WIDTH)
        return;
    block = (uint8_t)(x / 16u);
    bit = (uint8_t)(15u - (x % 16u));
    row_buf[block] &= (uint16_t)~(1u << bit);
}

void st7920_clear_gdram_buffer(void)
{
}

void st7920_clear_commands(void)
{
}
