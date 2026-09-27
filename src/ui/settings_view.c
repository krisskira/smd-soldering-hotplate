#include "settings_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/cfg_store.h"
#include "../services/process.h"
#include "../services/pid_atune.h"

/*
 * Ajustes: lista principal + página PID (auto + Kp/Ki/Kd).
 * Escalones de rampa: solo AT+RAMP (sin editor en pantalla; flash).
 */
#define SET_ROW_Y0    16u
#define SET_ROW_H     9u
#define SET_ROWS      4u
#define SET_FOOT_BIT  (1u << SET_ROWS)
#define SET_DIRTY_ALL (ROW_ALL | SET_FOOT_BIT)


#define PID_IDX_RUN  0u
#define PID_IDX_KP   1u
#define PID_IDX_KI   2u
#define PID_IDX_KD   3u
#define PID_COUNT    4u

static uint8_t item_count(const app_state_t *st)
{
    if (st->settings_page == SET_PAGE_PID)
        return PID_COUNT;
    return SETTINGS_COUNT;
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

static void put_gain(char *buf, const char *lab, int16_t x10, uint8_t edit)
{
    char v[6];

    ui_line_put(buf, 2, lab);
    if (edit)
        buf[5] = '*';
    ui_u16_to_str((uint16_t)(x10 < 0 ? 0 : x10), v);
    ui_line_put_right(buf, v);
}

static void build_item(const app_state_t *st, uint8_t idx, char *buf)
{
    uint8_t edit = (uint8_t)(st->edit_armed != SET_EDIT_NONE
                             && st->settings_sel == idx);

    if (st->settings_page == SET_PAGE_PID) {
        switch (idx) {
        case PID_IDX_RUN:
            if (pid_atune_active(st))
                ui_comp_format_menu(buf, "RUN", UI_COMP_NORMAL);
            else if (st->atune_phase == ATUNE_DONE)
                ui_comp_format_menu(buf, "OK", UI_COMP_NORMAL);
            else if (st->atune_phase == ATUNE_FAIL)
                ui_comp_format_menu(buf, "FAIL", UI_COMP_NORMAL);
            else
                ui_comp_format_menu(buf, i18n_tr_hash(I18N_SET_PID_AUTO),
                                    UI_COMP_NORMAL);
            break;
        case PID_IDX_KP:
            put_gain(buf, "Kp", st->pid_kp_x10, edit);
            break;
        case PID_IDX_KI:
            put_gain(buf, "Ki", st->pid_ki_x10, edit);
            break;
        case PID_IDX_KD:
            put_gain(buf, "Kd", st->pid_kd_x10, edit);
            break;
        default:
            break;
        }
        return;
    }
    switch (idx) {
    case SET_IDX_PID:
        ui_comp_format_menu(buf, i18n_tr_hash(I18N_SET_PID), UI_COMP_NORMAL);
        break;
    case SET_IDX_SOUND:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_SOUND),
                              st->buzz_nav_en, UI_COMP_NORMAL);
        break;
    case SET_IDX_PREHEAT:
        ui_comp_format_toggle(buf, i18n_tr_hash(I18N_SET_PREHEAT),
                              st->preheat_en, UI_COMP_NORMAL);
        break;
    case SET_IDX_PRE_PCT:
        put_gain(buf, i18n_tr_hash(I18N_SET_PRE_PCT),
                 (int16_t)st->preheat_pct, 0);
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
    ui_comp_draw_5x7_row((uint8_t)(SET_ROW_Y0 + r * SET_ROW_H), SET_ROW_H, buf,
                         (uint8_t)(idx == st->settings_sel));
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

static int16_t *gain_ptr(app_state_t *st)
{
    switch (st->settings_sel) {
    case PID_IDX_KP: return &st->pid_kp_x10;
    case PID_IDX_KI: return &st->pid_ki_x10;
    case PID_IDX_KD: return &st->pid_kd_x10;
    default: return 0;
    }
}

static void edit_gain(app_state_t *st, int8_t dir)
{
    int16_t *g = gain_ptr(st);
    int16_t v;

    if (!g)
        return;
    v = (int16_t)(*g + dir);
    if (v < 0)
        v = 0;
    if (v > 999)
        v = 999;
    *g = v;
}

static void pid_apply_if_done(app_state_t *st)
{
    if (st->atune_phase != ATUNE_DONE)
        return;
    pid_atune_apply(st);
    cfg_save_global(st);
    st->telem_dirty = 1u;
    st->row_dirty |= SET_DIRTY_ALL;
}

static void press_pid(app_state_t *st)
{
    uint8_t rc;

    if (st->settings_sel == PID_IDX_RUN) {
        if (pid_atune_active(st)) {
            process_stop(st, CTRL_UI);
            buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
            st->row_dirty |= SET_DIRTY_ALL;
            return;
        }
        pid_apply_if_done(st);
        st->program = PROG_PID_TUNE;
        rc = process_start(st, CTRL_UI);
        buzzer_seq_beep_cat(st, rc == PROG_OK ? BEEP_CONFIRM : BEEP_ALARM, 2);
        st->row_dirty |= SET_DIRTY_ALL;
        return;
    }
    if (st->edit_armed == SET_EDIT_NONE) {
        st->edit_armed = SET_EDIT_TEMP;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    st->edit_armed = SET_EDIT_NONE;
    cfg_save_global(st);
    st->telem_dirty = 1u;
    buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
}

static void on_press(app_state_t *st)
{
    if (st->settings_sel >= item_count(st)) {
        if (st->settings_page != SET_PAGE_MAIN) {
            open_page(st, SET_PAGE_MAIN, SET_IDX_PID);
        } else {
            ui_enter_view(st, VIEW_HOME);
            st->home_sel = HOME_IDX_SETTINGS;
        }
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (st->settings_page == SET_PAGE_PID) {
        press_pid(st);
        return;
    }
    switch (st->settings_sel) {
    case SET_IDX_PID:
        open_page(st, SET_PAGE_PID, 0u);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        break;
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

static uint8_t title_key(const app_state_t *st)
{
    return (st->settings_page == SET_PAGE_PID) ? I18N_SET_PID
                                               : I18N_TITLE_SETTINGS;
}

void settings_view_enter(app_state_t *st)
{
    if (!st)
        return;
    open_page(st, SET_PAGE_MAIN, SET_IDX_PID);
    st->row_dirty = SET_DIRTY_ALL;
}

void settings_view_refresh(app_state_t *st)
{
    uint8_t top, r;

    if (!st)
        return;
    if (st->settings_page == SET_PAGE_PID)
        pid_apply_if_done(st);
    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(title_key(st)), ICO_COUNT);
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
    if (st->edit_armed != SET_EDIT_NONE
        && st->settings_page == SET_PAGE_PID) {
        edit_gain(st, dir);
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

