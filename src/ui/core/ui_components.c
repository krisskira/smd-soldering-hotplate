#include "ui_components.h"
#include "ui_text.h"
#include "ui_icons.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include "lib/fonts/font.h"
#include "i18n/i18n_c.h"

/* Impar: 7 px de glifo + 4 px arriba y 4 abajo. */
#define UI_TITLE_H 15u

static void span_set(st7920_span_t *s, const font_t *f, const char *str,
                     uint8_t x)
{
    s->f = f;
    s->str = str;
    s->x = x;
    s->scale = 1;
    s->bold = 0;
}

/* Banda invertida de todo el ancho: el fondo no depende de dónde caiga el
 * título ni de lo que se pinte debajo. */
void ui_comp_draw_header(const char *title, ui_icon_id_t ico)
{
    st7920_span_t s;

    st7920_clear_gdram();
    (void)ico;
    if (!title)
        return;
    s.f = &FONT_5X7;
    s.str = title;
    s.x = 4;
    s.scale = 1;
    s.bold = 0;
    st7920_draw_band(0, 128u, 0, UI_TITLE_H, &s, 1u, 1u);
}

void ui_comp_format_menu(char *buf, const char *label, ui_comp_state_t st)
{
    ui_line_clear(buf);
    (void)st;
    ui_line_put(buf, 2, label);
}

void ui_comp_draw_footer(uint8_t x, const char *label, uint8_t inv)
{
    static const char enter[2] = { (char)(ICO_ENTER + 1u), '\0' };
    st7920_span_t s[2];
    uint8_t n = ui_str_len(label);
    uint8_t tx = (uint8_t)(x + UI_FOOT_X);

    span_set(&s[0], &FONT_5X7, label, tx);
    span_set(&s[1], &FONT_ICONS, enter,
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
        /* avance FONT_8X12 = 9; evita font_text_width. */
        span_set(&s[1], &FONT_5X7, unit,
                 (uint8_t)(text_x + (uint8_t)(len * 9u) + 2u));
        n = 2;
    } else {
        val[0] = '-'; val[1] = '-'; val[2] = '-'; val[3] = '.'; val[4] = '-';
        val[5] = '\0';
    }
    span_set(&s[0], &FONT_8X12, val, text_x);
    st7920_draw_band(band_x, (uint8_t)(128u - band_x), y, h, s, n, 0u);
}

void ui_comp_format_toggle(char *buf, const char *label, uint8_t on,
                           ui_comp_state_t st)
{
    ui_line_clear(buf);
    (void)st;
    ui_line_put(buf, 2, label);
    ui_line_put_right(buf, i18n_tr_hash(on ? I18N_ON : I18N_OFF));
}
