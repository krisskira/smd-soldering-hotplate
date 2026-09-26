#include "home_view.h"
#include "ui_display.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/device_session.h"

/* Filas: Modo USB, Ajustes. El resto de pantallas vuelve en iteraciones siguientes. */
static const uint8_t row_y[ROW_COUNT] = { 16, 28, 40, 52 };

static void build_menu_row(const app_state_t *st, uint8_t idx, char *buf)
{
    (void)st;
    ui_line_clear(buf);
    if (idx == HOME_IDX_USB)
        ui_comp_format_menu(buf, i18n_tr_hash(I18N_NAV_USB), UI_COMP_NORMAL);
    else if (idx == HOME_IDX_SETTINGS)
        ui_comp_format_menu(buf, i18n_tr_hash(I18N_NAV_SETTINGS),
                            UI_COMP_NORMAL);
}

void home_view_enter(app_state_t *st)
{
    if (!st)
        return;
    st->home_page = HOME_PAGE_MENU;
    st->home_sel = HOME_IDX_USB;
    st->edit_armed = 0;
    st->frame_dirty = 1;
    st->row_dirty = ROW_ALL;
}

void home_view_refresh(app_state_t *st)
{
    if (!st)
        return;
    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(I18N_TITLE_HOME), ICO_COUNT);
        st->frame_dirty = 0;
        st->row_dirty = ROW_ALL;
    }
    ui_display_refresh_focus(st, row_y, build_menu_row, (int8_t)st->home_sel);
}

void home_view_on_event(app_state_t *st, app_event_t evt)
{
    uint8_t old;

    if (!st)
        return;
    if (evt == EVT_ENCODER_NEXT || evt == EVT_ENCODER_PREV) {
        old = st->home_sel;
        ui_window_rotate(&st->home_sel, HOME_COUNT,
                         (evt == EVT_ENCODER_NEXT) ? 1 : -1);
        st->row_dirty |= (uint8_t)((1u << old) | (1u << st->home_sel));
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (evt != EVT_PRESS)
        return;
    if (st->home_sel == HOME_IDX_SETTINGS) {
        ui_enter_view(st, VIEW_SETTINGS);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (device_session_enter_usb(st) == 0) {
        ui_enter_view(st, VIEW_USB);
        buzzer_seq_beep_cat(st, BEEP_NAV, 2);
    } else {
        buzzer_seq_beep_cat(st, BEEP_ALARM, 2);
    }
}

void home_view_on_sensor(app_state_t *st)
{
    (void)st;
}
