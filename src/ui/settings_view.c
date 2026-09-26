#include "settings_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/cfg_store.h"
#include "lib/st7920/st7920.h"
#include "lib/fonts/font.h"

/*
 * Mapa de la vista (128×64), mismo esqueleto que MODO USB:
 *
 *   y  0–14   cabecera invertida (AJUSTES / RAMPAS)
 *   y 16–51   4 filas 5×7 de 9 px; la fila con foco va invertida
 *   y 54–63   pie "Salir ↵"; invertido solo cuando tiene el foco
 *
 * El pie es la última posición del cursor (settings_sel == número de
 * ítems). Rampas muestra Paso 1..4; el paso 1 siempre está activo.
 *
 * Fila de escalón: "  Paso 1  150°C 01:30"; '*' marca el campo en edición.
 */
#define SET_ROW_Y0    16u
#define SET_ROW_H     9u
#define SET_ROWS      4u
#define SET_FOOT_BIT  (1u << SET_ROWS)
#define SET_DIRTY_ALL (ROW_ALL | SET_FOOT_BIT)

#define STEP_COL_NUM   7u
#define STEP_COL_TEMP  10u   /* 3 cifras alineadas a la derecha: 10–12 */
#define STEP_COL_TIME  16u

static uint8_t item_count(const app_state_t *st)
{
    return (st->settings_page == SET_PAGE_RAMPS) ? SET_RAMPS_COUNT
                                                 : SETTINGS_COUNT;
}

static uint8_t window_top(const app_state_t *st)
{
    uint8_t n = item_count(st);
    uint8_t sel = (st->settings_sel < n) ? st->settings_sel : (uint8_t)(n - 1u);
    return ui_window_top(sel, SET_ROWS);
}

static uint8_t sel_bit(const app_state_t *st, uint8_t sel, uint8_t top)
{
    if (sel >= item_count(st))
        return SET_FOOT_BIT;
    return (uint8_t)(1u << (sel - top));
}

static void build_step(const app_state_t *st, uint8_t i, char *buf)
{
    const ramp_step_t *r = &st->ramp_step[i];
    uint8_t editing = (uint8_t)(st->edit_armed != SET_EDIT_NONE
                                && st->settings_sel == i);
    char v[6];

    ui_line_put(buf, 2, i18n_tr_hash(I18N_RAMP_STEP));
    buf[STEP_COL_NUM] = (char)('1' + i);
    if (i >= st->ramp_n && !editing) {
        ui_line_put_right(buf, i18n_tr_hash(I18N_OFF));
        return;
    }
    ui_u16_to_str(r->temp_c, v);
    ui_line_put(buf, (uint8_t)(STEP_COL_TEMP + 3u - ui_str_len(v)), v);
    buf[STEP_COL_TEMP + 3u] = (char)FONT_DEG_CHAR;
    buf[STEP_COL_TEMP + 4u] = 'C';
    ui_mmss_to_str(r->hold_s, v);
    ui_line_put(buf, STEP_COL_TIME, v);
    if (editing)
        buf[(st->edit_armed == SET_EDIT_TEMP) ? (STEP_COL_TEMP - 1u)
                                              : (STEP_COL_TIME - 1u)] = '*';
}

static void build_item(const app_state_t *st, uint8_t idx, char *buf)
{
    if (st->settings_page == SET_PAGE_RAMPS) {
        build_step(st, idx, buf);
        return;
    }
    switch (idx) {
    case SET_IDX_RAMPS:
        ui_comp_format_menu(buf, i18n_tr_hash(I18N_SET_RAMPS), UI_COMP_NORMAL);
        break;
    case SET_IDX_SOUND:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_SOUND),
                              st->buzz_nav_en, UI_COMP_NORMAL);
        break;
    case SET_IDX_PREHEAT:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_PREHEAT),
                              st->preheat_en, UI_COMP_NORMAL);
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
    if (idx < item_count(st))
        build_item(st, idx, buf);
    st7920_draw_text_gdram_styled(1, (uint8_t)(SET_ROW_Y0 + r * SET_ROW_H),
                                  SET_ROW_H, buf, 1u,
                                  (idx == st->settings_sel) ? ST7920_TEXT_INV
                                                            : 0u);
}

static void open_page(app_state_t *st, uint8_t page, uint8_t sel)
{
    st->settings_page = page;
    st->settings_sel = sel;
    st->edit_armed = SET_EDIT_NONE;
    st->frame_dirty = 1;
}

static void toggle(app_state_t *st, uint8_t *flag)
{
    *flag = (uint8_t)!*flag;
    cfg_save_global(st);
    st->telem_dirty = 1u;
    buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
}

static void edit_value(app_state_t *st, int8_t dir)
{
    ramp_step_t *r = &st->ramp_step[st->settings_sel];
    int16_t v;

    if (st->edit_armed == SET_EDIT_TEMP) {
        v = (int16_t)r->temp_c + dir * (int16_t)RAMP_TEMP_STEP_C;
        if (v < (int16_t)TEMP_MIN_SET_C)
            v = TEMP_MIN_SET_C;
        if (v > (int16_t)TEMP_MAX_SET_C)
            v = TEMP_MAX_SET_C;
        r->temp_c = (uint16_t)v;
    } else {
        v = (int16_t)r->hold_s + dir * (int16_t)TIMER_STEP_S;
        if (v < 0)
            v = 0;
        if (v > (int16_t)TIMER_MAX_S)
            v = TIMER_MAX_S;
        r->hold_s = (uint16_t)v;
    }
}

/* PRESS en un escalón: temperatura → tiempo → guardar.
 * Tiempo 0 corta la lista en ese escalón (mínimo uno activo). */
static void press_step(app_state_t *st)
{
    uint8_t i = st->settings_sel;
    ramp_step_t *r = &st->ramp_step[i];

    if (st->edit_armed == SET_EDIT_NONE) {
        if (r->temp_c < TEMP_MIN_SET_C || r->temp_c > TEMP_MAX_SET_C)
            r->temp_c = TEMP_MIN_SET_C;
        if (r->hold_s > TIMER_MAX_S)
            r->hold_s = TIMER_MAX_S;
        st->edit_armed = SET_EDIT_TEMP;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (st->edit_armed == SET_EDIT_TEMP) {
        st->edit_armed = SET_EDIT_TIME;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (r->hold_s == 0u) {
        if (i == 0u)
            r->hold_s = TIMER_STEP_S;
        else if (st->ramp_n > i)
            st->ramp_n = i;
    } else if (st->ramp_n < (uint8_t)(i + 1u)) {
        st->ramp_n = (uint8_t)(i + 1u);
    }
    st->edit_armed = SET_EDIT_NONE;
    cfg_save_ramps(st);
    st->telem_dirty = 1u;
    st->row_dirty |= SET_DIRTY_ALL;
    buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
}

static void on_press(app_state_t *st)
{
    if (st->settings_sel >= item_count(st)) {
        if (st->settings_page == SET_PAGE_RAMPS) {
            open_page(st, SET_PAGE_MAIN, SET_IDX_RAMPS);
        } else {
            ui_enter_view(st, VIEW_HOME);
            st->home_sel = HOME_IDX_SETTINGS;
        }
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (st->settings_page == SET_PAGE_RAMPS) {
        press_step(st);
        return;
    }
    switch (st->settings_sel) {
    case SET_IDX_RAMPS:
        cfg_load_ramps(st);
        open_page(st, SET_PAGE_RAMPS, 0u);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        break;
    case SET_IDX_SOUND:
        toggle(st, &st->buzz_nav_en);
        break;
    case SET_IDX_PREHEAT:
        toggle(st, &st->preheat_en);
        break;
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
    open_page(st, SET_PAGE_MAIN, SET_IDX_RAMPS);
    st->row_dirty = SET_DIRTY_ALL;
}

void settings_view_refresh(app_state_t *st)
{
    uint8_t top, r;

    if (!st)
        return;
    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(st->settings_page == SET_PAGE_RAMPS
                                             ? I18N_TITLE_RAMPS
                                             : I18N_TITLE_SETTINGS),
                            ICO_COUNT);
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
                            (uint8_t)(st->settings_sel >= item_count(st)));
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
    if (st->edit_armed != SET_EDIT_NONE) {
        edit_value(st, dir);
        st->row_dirty |= sel_bit(st, st->settings_sel, window_top(st));
        return;
    }
    old_sel = st->settings_sel;
    old_top = window_top(st);
    ui_window_rotate(&st->settings_sel, (uint8_t)(item_count(st) + 1u), dir);
    if (window_top(st) != old_top)
        st->row_dirty |= SET_DIRTY_ALL;
    else
        st->row_dirty |= (uint8_t)(sel_bit(st, old_sel, old_top)
                                   | sel_bit(st, st->settings_sel, old_top));
    buzzer_seq_beep_cat(st, BEEP_NAV, 1);
}
