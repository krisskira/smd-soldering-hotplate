#ifndef UI_DISPLAY_H
#define UI_DISPLAY_H

#include <stdint.h>
#include "../../app/app_state.h"
#include "ui_icons.h"

/* Icono de fila en las 2 primeras columnas; el texto debe empezar en col 2. */
#define UI_ROW_ICON_X 3u

typedef enum {
    UI_ROLE_TITLE = 0,
    UI_ROLE_BODY,
    UI_ROLE_ACTION,
    UI_ROLE_META
} ui_role_t;

typedef void (*ui_build_row_fn)(const app_state_t *st, uint8_t idx, char *buf);

void ui_display_draw_frame(const char *title);
/** Refresh with inverted ACTION when row index == focus_row (−1 = none). */
void ui_display_refresh_focus(app_state_t *st, const uint8_t *row_ys,
                              ui_build_row_fn build, int8_t focus_row);

/** Icono por fila (ICO_COUNT = sin icono). Solo si no UI_NO_ICONS. */
#ifndef UI_NO_ICONS
typedef ui_icon_id_t (*ui_row_icon_fn)(const app_state_t *st, uint8_t idx);

/** Como refresh_focus. El icono 8×8 se pinta solo si el callback lo devuelve. */
void ui_display_refresh_icons(app_state_t *st, const uint8_t *row_ys,
                              ui_build_row_fn build, ui_row_icon_fn icon,
                              int8_t focus_row);
#endif

#endif
