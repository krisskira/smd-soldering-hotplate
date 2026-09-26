/*
 * Iconos 8×8: los bitmaps viven en lib/fonts/font_icons.c (FONT_ICONS).
 * Aquí solo el acceso por ui_icon_id_t.
 */
#include "ui_icons.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include <avr/pgmspace.h>

#define ICO_BYTES 8u

void ui_icon_copy(ui_icon_id_t id, uint8_t *dst)
{
    const uint8_t *src;
    uint8_t i;

    if (!dst || id >= ICO_COUNT)
        return;
    src = FONT_ICONS.data + (uint16_t)id * ICO_BYTES;
    for (i = 0; i < ICO_BYTES; i++)
        dst[i] = pgm_read_byte(src + i);
}

void ui_icon_draw(uint8_t x, uint8_t y, ui_icon_id_t id)
{
    uint8_t buf[ICO_BYTES];
    ui_icon_copy(id, buf);
    st7920_draw_bitmap(x, y, 8, 8, buf);
}

void ui_icon_stamp_row(uint16_t *row, uint8_t row_y, uint8_t x, uint8_t y,
                       ui_icon_id_t id, uint8_t clear)
{
    if (!row || id >= ICO_COUNT)
        return;
    st7920_glyph_row(row, row_y, &FONT_ICONS, (uint8_t)id, x, y, 1u, clear);
}

void ui_icon_draw_gdram(uint8_t x, uint8_t y, ui_icon_id_t id)
{
    char s[2];

    if (id >= ICO_COUNT)
        return;
    s[0] = ui_icon_char(id);
    s[1] = '\0';
    st7920_draw_font_gdram(&FONT_ICONS, x, y, 0u, s, 1u, 0u);
}
