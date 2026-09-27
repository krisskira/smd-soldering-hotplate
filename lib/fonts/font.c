#include "font.h"
#include <avr/pgmspace.h>

uint8_t font_glyph(const font_t *f, uint8_t c)
{
    uint8_t i, m;

    if (!f)
        return FONT_NO_GLYPH;
    if (f->map) {
        for (i = 0; (m = pgm_read_byte(f->map + i)) != 0u; i++) {
            if (m == c)
                return i;
        }
        return FONT_NO_GLYPH;
    }
    if (c == FONT_DEG_CHAR)
        return f->deg;
    if (c >= f->first && (uint8_t)(c - f->first) < f->count)
        return (uint8_t)(c - f->first);
    return FONT_NO_GLYPH;
}

uint8_t font_glyph_bytes(const font_t *f)
{
    if (f->layout == FONT_ROWS)
        return (uint8_t)(f->h * (uint8_t)((f->w + 7u) >> 3));
    return f->w;
}
