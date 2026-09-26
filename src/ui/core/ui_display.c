#include "ui_display.h"
#include "ui_text.h"
#include "ui_components.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"

/* Fuente 5×7 e icono 8×8 no caben centrados en la misma banda.
 * Banda 10: texto con 1 px arriba y 2 abajo.
 * Icono una fila más abajo: 1 px arriba y 1 abajo. */
#define UI_ROW_H      10u
#define UI_ROW_ICON_DY 1u

void ui_display_draw_frame(const char *title)
{
    ui_comp_draw_header(title, ICO_COUNT);
}

void ui_display_refresh_focus(app_state_t *st, const uint8_t *row_ys,
                              ui_build_row_fn build, int8_t focus_row)
{
    char buf[LINE_LEN + 1];
    uint8_t i;

    if (!st || !row_ys || !build)
        return;

    for (i = 0; i < ROW_COUNT; i++) {
        if (st->row_dirty & (1u << i)) {
            build(st, i, buf);
            if (focus_row >= 0 && (int8_t)i == focus_row)
                st7920_draw_text_gdram_inv(1, row_ys[i], UI_ROW_H, buf);
            else
                st7920_draw_text_gdram_styled(1, row_ys[i], UI_ROW_H, buf,
                                              1u, 0u);
            st->row_dirty &= (uint8_t)~(1u << i);
        }
    }
}

#ifndef UI_NO_ICONS
void ui_display_refresh_icons(app_state_t *st, const uint8_t *row_ys,
                              ui_build_row_fn build, ui_row_icon_fn icon,
                              int8_t focus_row)
{
    char buf[LINE_LEN + 1];
    uint16_t row[8];
    uint8_t i, y, py, b, inv, ty, iy;
    ui_icon_id_t ico;

    if (!st || !row_ys || !build)
        return;

    for (i = 0; i < ROW_COUNT; i++) {
        if (!(st->row_dirty & (1u << i)))
            continue;
        build(st, i, buf);
        ico = icon ? icon(st, i) : ICO_COUNT;
        inv = (uint8_t)(focus_row >= 0 && (int8_t)i == focus_row);
        y = row_ys[i];
        ty = (uint8_t)(y + (UI_ROW_H - FONT_5X7.h) / 2u);
        iy = (uint8_t)(y + UI_ROW_ICON_DY);
        for (py = y; py < (uint8_t)(y + UI_ROW_H) && py < 64u; py++) {
            for (b = 0; b < 8u; b++)
                row[b] = inv ? 0xFFFFu : 0u;
            st7920_font_row(row, py, &FONT_5X7, 1, ty, buf, 1u, inv);
            if (ico < ICO_COUNT)
                ui_icon_stamp_row(row, py, UI_ROW_ICON_X, iy, ico, inv);
            for (b = 0; b < 8u; b++)
                st7920_write_gdram(b, py,
                                   (uint8_t)(row[b] >> 8),
                                   (uint8_t)(row[b] & 0xFFu));
        }
        st->row_dirty &= (uint8_t)~(1u << i);
    }
}
#endif
