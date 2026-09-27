#include "settings_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/cfg_store.h"

/*
 * Ajustes planos: Sonido | ESTAB | P% | Aire.
 * PID y autotune: solo AT (`CFG=P`, `RUN=2`). Escalones: `AT+CFG=R`.
 */
#define SET_ROW_Y0    16u
#define SET_ROW_H     9u
#define SET_ROWS      4u
#define SET_FOOT_BIT  (1u << SET_ROWS)
#define SET_DIRTY_ALL (ROW_ALL | SET_FOOT_BIT)

static uint8_t window_top(const app_state_t *st)
{
    uint8_t sel = (st->settings_sel < SETTINGS_COUNT)
                      ? st->settings_sel
                      : (uint8_t)(SETTINGS_COUNT - 1u);
    return ui_window_top(sel, SET_ROWS);
}

static uint8_t sel_bit(const app_state_t *st, uint8_t sel, uint8_t top)
{
    if (sel >= SETTINGS_COUNT)
        return SET_FOOT_BIT;
    return (uint8_t)(1u << (sel - top));
}

static void put_pct(char *buf, const char *lab, uint8_t pct)
{
    char v[6];

    ui_line_put(buf, 2, lab);
    ui_u16_to_str(pct, v);
    ui_line_put_right(buf, v);
}

static void build_item(const app_state_t *st, uint8_t idx, char *buf)
{
    switch (idx) {
    case SET_IDX_SOUND:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_SOUND),
                              st->buzz_nav_en, UI_COMP_NORMAL);
        break;
    case SET_IDX_PREHEAT:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_PREHEAT),
                              st->preheat_en, UI_COMP_NORMAL);
        break;
    case SET_IDX_PRE_PCT:
        put_pct(buf, i18n_tr_hash(I18N_SET_PRE_PCT), st->preheat_pct);
        break;
    case SET_IDX_AIR:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_AIR),
                              st->cooldown_air_en, UI_COMP_NORMAL);
        break;
    default:
        break;
    }
}

static void draw_row(const app_state_t *st, uint8_t r, uint8_t top)
{
    char buf[LINE_LEN + 1];
    uint8_t idx = (uint8_t)(top + r);

    ui_line_clear(buf);
    if (idx < SETTINGS_COUNT)
        build_item(st, idx, buf);
    ui_comp_draw_5x7_row((uint8_t)(SET_ROW_Y0 + r * SET_ROW_H), SET_ROW_H, buf,
                         (uint8_t)(idx == st->settings_sel));
}

static void toggle(app_state_t *st, uint8_t *flag)
{
    *flag = (uint8_t)!*flag;
    cfg_save_global(st);
    st->telem_dirty = 1u;
    buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
}

static void on_press(app_state_t *st)
{
    if (st->settings_sel >= SETTINGS_COUNT) {
        ui_enter_view(st, VIEW_HOME);
        st->home_sel = HOME_IDX_SETTINGS;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    switch (st->settings_sel) {
    case SET_IDX_SOUND:
        toggle(st, &st->buzz_nav_en);
        break;
    case SET_IDX_PREHEAT:
        toggle(st, &st->preheat_en);
        break;
    case SET_IDX_PRE_PCT: {
        uint8_t p = (uint8_t)(st->preheat_pct + PREHEAT_PCT_STEP);
        if (p > PREHEAT_PCT_HI || p < PREHEAT_PCT_LO)
            p = PREHEAT_PCT_LO;
        st->preheat_pct = p;
        cfg_save_global(st);
        st->telem_dirty = 1u;
        buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
        break;
    }
    case SET_IDX_AIR:
        toggle(st, &st->cooldown_air_en);
        break;
    default:
        break;
    }
}

void settings_view_enter(app_state_t *st)
{
    if (!st)
        return;
    st->settings_page = SET_PAGE_MAIN;
    st->settings_sel = 0;
    st->edit_armed = SET_EDIT_NONE;
    st->frame_dirty = 1;
    st->row_dirty = SET_DIRTY_ALL;
}

void settings_view_refresh(app_state_t *st)
{
    uint8_t top, r;

    if (!st)
        return;
    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(I18N_TITLE_SETTINGS), ICO_COUNT);
        st->frame_dirty = 0;
        st->row_dirty = SET_DIRTY_ALL;
    }
    if (!st->row_dirty)
        return;
    top = window_top(st);
    for (r = 0; r < SET_ROWS; r++) {
        if (st->row_dirty & (1u << r))
            draw_row(st, r, top);
    }
    if (st->row_dirty & SET_FOOT_BIT)
        ui_comp_draw_footer(0u, i18n_tr_hash(I18N_USB_EXIT),
                            (uint8_t)(st->settings_sel >= SETTINGS_COUNT));
    st->row_dirty = 0;
}

void settings_view_on_event(app_state_t *st, app_event_t evt)
{
    uint8_t old_sel, old_top;
    int8_t dir;

    if (!st)
        return;
    if (evt == EVT_PRESS) {
        on_press(st);
        st->row_dirty |= sel_bit(st, st->settings_sel, window_top(st));
        return;
    }
    if (evt != EVT_ENCODER_NEXT && evt != EVT_ENCODER_PREV)
        return;

    dir = (evt == EVT_ENCODER_NEXT) ? 1 : -1;
    old_sel = st->settings_sel;
    old_top = window_top(st);
    ui_window_rotate(&st->settings_sel, (uint8_t)(SETTINGS_COUNT + 1u), dir);
    if (window_top(st) != old_top)
        st->row_dirty |= SET_DIRTY_ALL;
    else
        st->row_dirty |= (uint8_t)(sel_bit(st, old_sel, old_top)
                                   | sel_bit(st, st->settings_sel, old_top));
    buzzer_seq_beep_cat(st, BEEP_NAV, 1);
}
