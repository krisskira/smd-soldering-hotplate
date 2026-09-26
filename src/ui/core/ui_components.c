#include "ui_components.h"
#include "ui_text.h"
#include "ui_icons.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include "lib/fonts/font.h"
#include "i18n/i18n_c.h"

/* Impar: 7 px de glifo + 4 px arriba y 4 abajo. */
#define UI_TITLE_H 15u

/* Banda invertida de todo el ancho: el fondo no depende de dónde caiga el
 * título ni de lo que se pinte debajo. */
void ui_comp_draw_header(const char *title, ui_icon_id_t ico)
{
    st7920_span_t s[2];
    uint8_t n = 1;
    uint16_t w;

    st7920_clear_gdram();
    if (!title)
        return;

#ifdef NO_FONT_6X8
    s[0].f = &FONT_5X7;
    s[0].bold = 1;
#else
    s[0].f = &FONT_6X8_BOLD;
    s[0].bold = 0;
#endif
    s[0].str = title;
    s[0].scale = 1;
    w = st7920_span_width(&s[0]);
    s[0].x = (uint8_t)((128u - (w > 128u ? 128u : w)) / 2u);

#ifndef UI_NO_ICONS
    if (ico < ICO_COUNT) {
        static char ico_str[2];
        ico_str[0] = ui_icon_char(ico);
        s[1].f = &FONT_ICONS;
        s[1].str = ico_str;
        s[1].x = 2;
        s[1].scale = 1;
        s[1].bold = 0;
        n = 2;
    }
#else
    (void)ico;
#endif
    st7920_draw_band(0, 128u, 0, UI_TITLE_H, s, n, 1u);
}

void ui_comp_format_menu(char *buf, const char *label, ui_comp_state_t st)
{
    ui_line_clear(buf);
    (void)st;
    ui_line_put(buf, 2, label);
}

void ui_comp_draw_footer(const char *label, uint8_t inv)
{
    static const char enter[2] = { (char)(ICO_ENTER + 1u), '\0' };
    st7920_span_t s[2];
    uint8_t n = ui_str_len(label);

    s[0].f = &FONT_5X7;
    s[0].str = label;
    s[0].x = UI_FOOT_X;
    s[0].scale = 1;
    s[0].bold = 0;
    s[1].f = &FONT_ICONS;
    s[1].str = enter;
    s[1].x = (uint8_t)(UI_FOOT_X + (n + 1u) * FONT_5X7.advance);
    s[1].scale = 1;
    s[1].bold = 0;
    st7920_draw_band(0, 128u, UI_FOOT_Y, UI_FOOT_H, s, 2u, inv);
}

/* label ya está copiado en buf antes de pedir ON/OFF al catálogo. */
void ui_comp_format_toggle(char *buf, const char *label, uint8_t on,
                           ui_comp_state_t st)
{
    ui_line_clear(buf);
    (void)st;
    ui_line_put(buf, 2, label);
    ui_line_put_right(buf, i18n_tr_hash(on ? I18N_ON : I18N_OFF));
}

void ui_comp_format_number(char *buf, const char *label, const char *value,
                           ui_comp_state_t st)
{
    uint8_t col;

    ui_line_clear(buf);
    ui_line_put(buf, 2, label);
    col = (uint8_t)(2u + ui_str_len(label));
    if (value)
        ui_line_put(buf, col, value);
    if (st == UI_COMP_EDITING)
        ui_line_put_right(buf, "*");
}

void ui_comp_format_action(char *buf, const char *label, ui_comp_state_t st)
{
    ui_line_clear(buf);
    (void)st;
    ui_line_put(buf, 2, "[");
    ui_line_put(buf, 3, label);
    ui_line_put(buf, (uint8_t)(3u + ui_str_len(label)), "]");
}
