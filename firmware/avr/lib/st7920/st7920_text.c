/*
 * ST7920 texto: un solo blit para FONT_COLS (5×7, 1× o 2×) y FONT_ROWS
 * (iconos 16×16, 1:1). Buffer de fila = 16 bytes, MSB = izquierda.
 */
#include "st7920.h"
#include "st7920_private.h"
#include <avr/pgmspace.h>

#define LCD_W 128u
#define LCD_H 64u

static void row_px(uint8_t *row_buf, uint8_t x, uint8_t clear)
{
    uint8_t m;

    if (x >= LCD_W)
        return;
    m = (uint8_t)(0x80u >> (x & 7u));
    if (clear)
        row_buf[x >> 3] &= (uint8_t)~m;
    else
        row_buf[x >> 3] |= m;
}

/*
 * FONT_COLS con h > 8 es la misma tabla a 2×: cada píxel fuente → 2×2.
 * El ancho/alto fuente es w >> sh / h >> sh.
 */
void st7920_glyph_row(uint8_t *row_buf, uint8_t row_y, const font_t *f,
                      uint8_t glyph, uint8_t tx, uint8_t ty, uint8_t clear)
{
    const uint8_t *p;
    uint8_t gy, gx, w, sh, cols, bpr, on, px;

    if (glyph == FONT_NO_GLYPH || row_y < ty)
        return;
    gy = (uint8_t)(row_y - ty);
    if (gy >= f->h)
        return;
    cols = (uint8_t)(f->layout == FONT_COLS);
    sh = (uint8_t)(cols && f->h > 8u);
    gy >>= sh;
    w = (uint8_t)(f->w >> sh);
    if (cols) {
        p = f->data + (uint16_t)glyph * w;
    } else {
        bpr = (uint8_t)((w + 7u) >> 3);
        p = f->data + ((uint16_t)glyph * f->h + gy) * bpr;
    }
    for (gx = 0; gx < w; gx++) {
        if (cols)
            on = (uint8_t)((pgm_read_byte(p + gx) >> gy) & 1u);
        else
            on = (uint8_t)((uint8_t)(pgm_read_byte(p + (gx >> 3)) << (gx & 7u))
                           & 0x80u);
        if (!on)
            continue;
        px = (uint8_t)(tx + (gx << sh));
        row_px(row_buf, px, clear);
        if (sh)
            row_px(row_buf, (uint8_t)(px + 1u), clear);
    }
}

void st7920_draw_band(uint8_t x, uint8_t w, uint8_t y, uint8_t h,
                      const st7920_span_t *spans, uint8_t n, uint8_t inv)
{
    uint8_t row[16];
    uint8_t b0 = (uint8_t)(x >> 4);
    uint8_t b1 = (uint8_t)(((uint16_t)x + w + 15u) >> 4);
    uint8_t row_y, b, i, gh, ty, tx, c;
    const st7920_span_t *s;
    const char *str;

    if (b1 > 8u)
        b1 = 8u;
    for (row_y = y; row_y < (uint8_t)(y + h) && row_y < LCD_H; row_y++) {
        for (b = 0; b < 16u; b++)
            row[b] = inv ? 0xFFu : 0u;
        for (i = 0; i < n; i++) {
            s = &spans[i];
            gh = s->f->h;
            ty = (uint8_t)(y + (h > gh ? (uint8_t)((h - gh) / 2u) : 0u));
            tx = s->x;
            for (str = s->str; (c = (uint8_t)*str++) != 0u && tx < LCD_W;
                 tx = (uint8_t)(tx + s->f->advance))
                st7920_glyph_row(row, row_y, s->f, font_glyph(s->f, c),
                                 tx, ty, inv);
        }
        for (b = b0; b < b1; b++)
            st7920_write_gdram(b, row_y, row[2u * b], row[2u * b + 1u]);
    }
}
