/*
 * ST7920 - Texto con cualquier fuente de lib/fonts (escala 1..3).
 * Compone fila a fila en un buffer de 128 px y escribe solo los bloques
 * de la banda pedida.
 */
#include "st7920.h"
#include "st7920_private.h"
#include <avr/pgmspace.h>

#define LCD_W 128u
#define LCD_H 64u

void st7920_glyph_row(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                      uint8_t glyph, uint8_t tx, uint8_t ty, uint8_t scale,
                      uint8_t clear)
{
    const uint8_t *p;
    uint8_t gy, gx, sx, bits = 0, on;
    uint16_t px;

    if (!f || glyph == FONT_NO_GLYPH || row_y < ty)
        return;
    gy = (uint8_t)((row_y - ty) / scale);
    if (gy >= f->h)
        return;

    p = f->data + (uint16_t)glyph * font_glyph_bytes(f);
    if (f->layout == FONT_ROWS)
        p += (uint16_t)gy * (uint8_t)((f->w + 7u) >> 3);

    for (gx = 0; gx < f->w; gx++) {
        if (f->layout == FONT_ROWS) {
            if ((gx & 7u) == 0u)
                bits = pgm_read_byte(p + (gx >> 3));
            on = (uint8_t)(bits & (0x80u >> (gx & 7u)));
        } else {
            on = (uint8_t)(pgm_read_byte(p + gx) & (1u << gy));
        }
        if (!on)
            continue;
        for (sx = 0; sx < scale; sx++) {
            px = (uint16_t)tx + (uint16_t)gx * scale + sx;
            if (px >= LCD_W)
                break;
            if (clear)
                st7920_row_clear_pixel(row_buf, (uint8_t)px);
            else
                st7920_row_set_pixel(row_buf, (uint8_t)px);
        }
    }
}

static void font_row_adv(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                         uint8_t tx, uint8_t ty, const char *str,
                         uint8_t scale, uint8_t clear)
{
    uint16_t x = tx;
    uint8_t c;

    if (!f || !str)
        return;
    while ((c = (uint8_t)*str++) != 0u && x < LCD_W) {
        if (c == FONT_UTF8_C2)
            continue;
        st7920_glyph_row(row_buf, row_y, f, font_glyph(f, c), (uint8_t)x, ty,
                         scale, clear);
        x += (uint16_t)f->advance * scale;
    }
}

void st7920_font_row(uint16_t *row_buf, uint8_t row_y, const font_t *f,
                     uint8_t tx, uint8_t ty, const char *str, uint8_t scale,
                     uint8_t clear)
{
    font_row_adv(row_buf, row_y, f, tx, ty, str, scale, clear);
}

void st7920_draw_band(uint8_t x, uint8_t w, uint8_t y, uint8_t h,
                      const st7920_span_t *spans, uint8_t n, uint8_t inv)
{
    uint16_t row[8];
    uint16_t fill = inv ? 0xFFFFu : 0u;
    uint8_t b0 = (uint8_t)(x >> 4);
    uint8_t b1 = (uint8_t)(((uint16_t)x + w + 15u) >> 4);
    uint8_t row_y, b, i, scale, gh, ty;
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
            scale = s->scale ? s->scale : 1u;
            if (scale > 3u)
                scale = 3u;
            gh = (uint8_t)(s->f->h * scale);
            ty = (uint8_t)(y + (h > gh ? (uint8_t)((h - gh) / 2u) : 0u));
            if (row_y < ty || row_y >= (uint8_t)(ty + gh))
                continue;
            font_row_adv(row, row_y, s->f, s->x, ty, s->str, scale, inv);
        }
        for (b = b0; b < b1; b++)
            st7920_write_gdram(b, row_y,
                               (uint8_t)(row[b] >> 8),
                               (uint8_t)(row[b] & 0xFFu));
    }
}

void st7920_draw_font_gdram(const font_t *f, uint8_t x, uint8_t y, uint8_t h,
                            const char *str, uint8_t scale, uint8_t inv)
{
    st7920_span_t s;
    uint8_t bx = (uint8_t)(x & 0xF0u);

    s.f = f;
    s.str = str;
    s.x = x;
    s.scale = scale;
    s.bold = 0;
    st7920_draw_band(bx, (uint8_t)(LCD_W - bx), y, h, &s, 1u, inv);
}
