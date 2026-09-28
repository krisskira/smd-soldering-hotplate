/*
 * ST7920 texto: FONT_ROWS (8×12 + iconos 16×16) y blit dedicado FONT_5X7.
 * Tinta 1:1 (sin escala por píxel).
 */
#include "st7920.h"
#include "st7920_private.h"
#include <avr/pgmspace.h>

#define LCD_W 128u
#define LCD_H 64u

void st7920_glyph_row(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                      uint8_t glyph, uint8_t tx, uint8_t ty, uint8_t clear)
{
    const uint8_t *p;
    uint8_t gy, gx, bpr, bits = 0, px;
    uint16_t gsz;

    if (!f || glyph == FONT_NO_GLYPH || row_y < ty)
        return;
    gy = (uint8_t)(row_y - ty);
    if (gy >= f->h)
        return;
    bpr = (uint8_t)((f->w + 7u) >> 3);
    gsz = (uint16_t)f->h * bpr;
    p = f->data + (uint16_t)glyph * gsz + (uint16_t)gy * bpr;
    for (gx = 0; gx < f->w; gx++) {
        if ((gx & 7u) == 0u)
            bits = pgm_read_byte(p + (gx >> 3));
        if (!(bits & (uint8_t)(0x80u >> (gx & 7u))))
            continue;
        px = (uint8_t)(tx + gx);
        if (px >= LCD_W)
            break;
        if (clear)
            st7920_row_clear_pixel(row_buf, px);
        else
            st7920_row_set_pixel(row_buf, px);
    }
}

static void glyph5x7_row(uint16_t *row_buf, uint8_t row_y, uint8_t glyph,
                         uint8_t tx, uint8_t ty, uint8_t clear)
{
    const uint8_t *p;
    uint8_t gy, gx, col;

    if (glyph == FONT_NO_GLYPH || row_y < ty)
        return;
    gy = (uint8_t)(row_y - ty);
    if (gy >= 7u)
        return;
    p = font5x7_data + (uint16_t)glyph * 5u;
    for (gx = 0; gx < 5u; gx++) {
        col = pgm_read_byte(p + gx);
        if (!(col & (uint8_t)(1u << gy)))
            continue;
        if (clear)
            st7920_row_clear_pixel(row_buf, (uint8_t)(tx + gx));
        else
            st7920_row_set_pixel(row_buf, (uint8_t)(tx + gx));
    }
}

static void font_row_adv(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                         uint8_t tx, uint8_t ty, const char *str,
                         uint8_t clear)
{
    uint16_t x = tx;
    uint8_t c, gid;

    if (!f || !str)
        return;
    while ((c = (uint8_t)*str++) != 0u && x < LCD_W) {
        gid = font_glyph(f, c);
        if (f == &FONT_5X7)
            glyph5x7_row(row_buf, row_y, gid, (uint8_t)x, ty, clear);
        else
            st7920_glyph_row(row_buf, row_y, f, gid, (uint8_t)x, ty, clear);
        x = (uint16_t)(x + f->advance);
    }
}

void st7920_draw_band(uint8_t x, uint8_t w, uint8_t y, uint8_t h,
                      const st7920_span_t *spans, uint8_t n, uint8_t inv)
{
    uint16_t row[8];
    uint16_t fill = inv ? 0xFFFFu : 0u;
    uint8_t b0 = (uint8_t)(x >> 4);
    uint8_t b1 = (uint8_t)(((uint16_t)x + w + 15u) >> 4);
    uint8_t row_y, b, i, gh, ty;
    const st7920_span_t *s;

    if (b1 > 8u)
        b1 = 8u;
    for (row_y = y; row_y < (uint8_t)(y + h) && row_y < LCD_H; row_y++) {
        for (b = 0; b < 8u; b++)
            row[b] = fill;
        for (i = 0; i < n; i++) {
            s = &spans[i];
            if (!s->f || !s->str)
                continue;
            gh = s->f->h;
            ty = (uint8_t)(y + (h > gh ? (uint8_t)((h - gh) / 2u) : 0u));
            if (row_y < ty || row_y >= (uint8_t)(ty + gh))
                continue;
            font_row_adv(row, row_y, s->f, s->x, ty, s->str, inv);
        }
        for (b = b0; b < b1; b++)
            st7920_write_gdram(b, row_y,
                               (uint8_t)(row[b] >> 8),
                               (uint8_t)(row[b] & 0xFFu));
    }
}
