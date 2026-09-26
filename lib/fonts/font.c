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

uint16_t font_text_width(const font_t *f, const char *s, uint8_t scale)
{
    uint16_t n = 0;

    if (!f || !s)
        return 0;
    for (; *s; s++) {
        if ((uint8_t)*s != FONT_UTF8_C2)
            n++;
    }
    if (n == 0u)
        return 0;
    return (uint16_t)((n * f->advance - (uint8_t)(f->advance - f->w)) * scale);
}
