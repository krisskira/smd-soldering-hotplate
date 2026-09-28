#include "ui_components.h"
#include "ui_text.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include "lib/fonts/font.h"

static void span_set(st7920_span_t *s, const font_t *f, const char *str,
                     uint8_t x)
{
    s->f = f;
    s->str = str;
    s->x = x;
    s->scale = 1;
    s->bold = 0;
}

void ui_comp_draw_footer(uint8_t x, const char *label, uint8_t inv)
{
    static const char enter[] = "<";
    st7920_span_t s[2];
    uint8_t n = ui_str_len(label);
    uint8_t tx = (uint8_t)(x + UI_FOOT_X);

    span_set(&s[0], &FONT_5X7, label, tx);
    span_set(&s[1], &FONT_5X7, enter,
             (uint8_t)(tx + (n + 1u) * FONT_5X7.advance));
    st7920_draw_band(x, (uint8_t)(128u - x), UI_FOOT_Y, UI_FOOT_H, s, 2u, inv);
}

void ui_comp_draw_temp(uint8_t band_x, uint8_t text_x, uint8_t y, uint8_t h,
                       const sensor_reading_t *r)
{
    static const char unit[2] = { 'C', '\0' };
    char val[10];
    st7920_span_t s[2];
    uint8_t n = 1;
    uint8_t len;

    if (r && r->valid) {
        ui_temp_to_str(r, val);
        len = ui_str_len(val);
        val[len++] = (char)FONT_DEG_CHAR;
        val[len] = '\0';
        span_set(&s[1], &FONT_5X7, unit,
                 (uint8_t)(text_x + (uint8_t)(len * 6u) + 2u));
        n = 2;
    } else {
        val[0] = '-'; val[1] = '-'; val[2] = '-'; val[3] = '.'; val[4] = '-';
        val[5] = '\0';
    }
    span_set(&s[0], &FONT_8X12, val, text_x);
    st7920_draw_band(band_x, (uint8_t)(128u - band_x), y, h, s, n, 0u);
}
