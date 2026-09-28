#include "home_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/cfg_store.h"
#include "../services/process.h"
#include "../services/device_session.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include "lib/fonts/font.h"

/* x0..30 barra | x31 | x32..127 panel. Dos casillas ~32 px. */
#define PANEL_X    32u
#define PANEL_TX   36u
#define BOX_H      32u
#define TEMP_H     16u
#define LINE_H     10u
#define PCOLS      ((128u - PANEL_TX) / 6u) /* ~15 cols visibles */

static const char s_mark[2] = { 'H', 'A' };

static uint8_t is_run(const app_state_t *st)
{
    return process_is_active(st);
}

static uint8_t is_usb(const app_state_t *st)
{
    return device_session_is_usb(st);
}

static uint8_t in_set(const app_state_t *st)
{
    return (st->home_page == HOME_PAGE_SETTINGS) ? 1u : 0u;
}

static uint8_t show_set(const app_state_t *st)
{
    if (is_usb(st) || is_run(st))
        return 0u;
    return (in_set(st) || st->home_sel == HOME_IDX_SETTINGS) ? 1u : 0u;
}

static uint8_t focus(const app_state_t *st)
{
    if (is_usb(st) || is_run(st))
        return HOME_IDX_HEAT;
    if (in_set(st))
        return HOME_IDX_SETTINGS;
    return st->home_sel;
}

static void dirty_all(app_state_t *st)
{
    st->row_dirty = HOME_DIRTY_ALL;
}

static void side_box(uint8_t i, uint8_t inv)
{
    char ico[2];
    uint8_t y0 = (uint8_t)(i * BOX_H);
    uint8_t iy = (uint8_t)(y0 + (BOX_H - 7u) / 2u);
    uint8_t py;
    uint16_t row[2], fill = inv ? 0xFFFFu : 0u;

    ico[0] = s_mark[i];
    ico[1] = '\0';
    for (py = y0; py < (uint8_t)(y0 + BOX_H); py++) {
        row[0] = fill;
        row[1] = (uint16_t)(fill | 0x0001u);
        st7920_font_row(row, py, &FONT_5X7, 12u, iy, ico, 1u, inv);
        st7920_write_gdram(0, py, (uint8_t)(row[0] >> 8), (uint8_t)row[0]);
        st7920_write_gdram(1, py, (uint8_t)(row[1] >> 8), (uint8_t)row[1]);
    }
}

static void panel_band(uint8_t y, uint8_t h, const char *s, uint8_t inv)
{
    st7920_span_t sp = { &FONT_5X7, s, PANEL_TX, 1u, 0u };
    st7920_draw_band(PANEL_X, (uint8_t)(128u - PANEL_X), y, h, &sp, 1u, inv);
}

/* Texto centrado en el panel (cols PCOLS). */
static void panel_center(uint8_t y, uint8_t h, const char *str, uint8_t inv)
{
    char line[LINE_LEN + 1];
    uint8_t n = ui_str_len(str);
    uint8_t col = (n < PCOLS) ? (uint8_t)((PCOLS - n) / 2u) : 0u;

    ui_line_clear(line);
    ui_line_put(line, col, str);
    line[PCOLS] = '\0';
    panel_band(y, h, line, inv);
}

static void draw_centered_temp(const app_state_t *st, uint8_t y)
{
    char val[8];
    st7920_span_t s;
    uint8_t n;

    if (st->sensor.valid)
        ui_temp_to_str(&st->sensor, val);
    else {
        val[0] = '-'; val[1] = '-'; val[2] = '-'; val[3] = '\0';
    }
    n = ui_str_len(val);
    s.f = &FONT_8X12;
    s.str = val;
    s.x = (uint8_t)(PANEL_X + ((96u - (uint8_t)(n * 6u)) / 2u));
    s.scale = 1u;
    s.bold = 0u;
    st7920_draw_band(PANEL_X, 96u, y, TEMP_H, &s, 1u, 0u);
}

/* "R1 150 01:30" — rampa | T objetivo | remain/delay. */
static void draw_heat_info(const app_state_t *st, uint8_t y)
{
    char body[16];
    char num[6];
    uint8_t n = 0;
    uint16_t tset, trem;

    if (st->ramp_n == 0u) {
        panel_center(y, LINE_H, i18n_tr_hash(I18N_OFF), 0u);
        return;
    }
    body[n++] = 'R';
    if (is_run(st) && st->phase >= PH_PREHEAT && st->phase <= PH_RUN) {
        body[n++] = (char)('0' + st->ramp_idx + 1u);
        tset = st->t_set_c;
        trem = st->t_remain_s;
    } else {
        body[n++] = '1';
        tset = st->ramp_step[0].temp_c;
        trem = is_run(st) ? st->t_remain_s : st->delay_s;
    }
    body[n++] = ' ';
    ui_u16_to_str(tset, num);
    ui_line_put(body, n, num);
    n = (uint8_t)(n + ui_str_len(num));
    body[n++] = ' ';
    ui_mmss_to_str(trem, num);
    ui_line_put(body, n, num);
    n = (uint8_t)(n + 5u);
    body[n] = '\0';
    panel_center(y, LINE_H, body, 0u);
}

static void draw_heat_panel(const app_state_t *st)
{
    panel_center(0u, SET_HDR_H,
                 is_usb(st) ? i18n_tr_hash(I18N_TITLE_USB)
                            : i18n_tr_hash(I18N_PROG_HEAT),
                 1u);
    draw_centered_temp(st, SET_HDR_H);
    if (is_usb(st))
        return;
    panel_center((uint8_t)(SET_HDR_H + TEMP_H), LINE_H,
                 process_phase_name(st->phase), 0u);
    draw_heat_info(st, (uint8_t)(SET_HDR_H + TEMP_H + LINE_H));
}

static uint8_t ramp_on(const app_state_t *st, uint8_t idx)
{
    return (idx < st->ramp_n) ? 1u : 0u;
}

static void save_ramps(app_state_t *st)
{
    cfg_save_ramps(st);
    st->telem_dirty = 1u;
}

static void ensure_ramp(app_state_t *st, uint8_t idx)
{
    uint8_t i;
    if (idx >= RAMP_STEPS_MAX)
        return;
    for (i = st->ramp_n; i <= idx; i++) {
        if (st->ramp_step[i].temp_c < st->temp_min_c
            || st->ramp_step[i].temp_c > st->temp_max_c
            || st->ramp_step[i].temp_c == 0u)
            st->ramp_step[i].temp_c = st->temp_min_c;
        if (st->ramp_step[i].hold_s == 0u)
            st->ramp_step[i].hold_s = TIMER_STEP_S;
    }
    st->ramp_n = (uint8_t)(idx + 1u);
    save_ramps(st);
}

static void build_set_item(const app_state_t *st, uint8_t idx, char *buf)
{
    char v[6];
    uint8_t ed = st->edit_armed;
    uint8_t n;

    if (idx <= SET_IDX_RAMP3) {
        buf[0] = 'R';
        buf[1] = (char)('1' + idx);
        buf[2] = ':';
        if (!ramp_on(st, idx) || st->ramp_step[idx].temp_c == 0u) {
            ui_line_put(buf, 4, i18n_tr_hash(I18N_OFF));
            return;
        }
        if (ed == SET_EDIT_TEMP && st->settings_sel == idx)
            buf[3] = '*';
        ui_u16_to_str(st->ramp_step[idx].temp_c, v);
        ui_line_put(buf, 4, v);
        buf[7] = '/';
        if (ed == SET_EDIT_TIME && st->settings_sel == idx)
            buf[8] = '*';
        ui_u16_to_str(st->ramp_step[idx].hold_s, v);
        ui_line_put(buf, 9, v);
        return;
    }
    ui_line_put(buf, 0, i18n_tr_hash(I18N_SET_DELAY));
    if (ed == SET_EDIT_DELAY)
        buf[7] = '*';
    ui_mmss_to_str(st->delay_s, v);
    n = ui_str_len(v); /* 5 = mm:ss */
    if (n < PCOLS)
        ui_line_put(buf, (uint8_t)(PCOLS - n), v);
}

static void draw_set_rows(const app_state_t *st)
{
    char buf[LINE_LEN + 1];
    uint8_t top, r, idx, inv, armed;

    armed = in_set(st);
    top = armed ? ui_window_top(st->settings_sel < SETTINGS_COUNT
                                    ? st->settings_sel
                                    : (uint8_t)(SETTINGS_COUNT - 1u),
                                SET_VIS_ROWS)
                : 0u;
    for (r = 0; r < SET_VIS_ROWS; r++) {
        idx = (uint8_t)(top + r);
        ui_line_clear(buf);
        if (idx < SETTINGS_COUNT)
            build_set_item(st, idx, buf);
        buf[PCOLS] = '\0';
        inv = (armed && idx == st->settings_sel
               && st->settings_sel < SETTINGS_COUNT)
                  ? 1u
                  : 0u;
        panel_band((uint8_t)(SET_ROW_Y0 + r * SET_ROW_H), SET_ROW_H, buf, inv);
    }
}

static void leave_set(app_state_t *st)
{
    st->home_page = HOME_PAGE_MENU;
    st->home_sel = HOME_IDX_HEAT;
    st->edit_armed = SET_EDIT_NONE;
    dirty_all(st);
}

static void enter_set(app_state_t *st)
{
    st->home_page = HOME_PAGE_SETTINGS;
    st->settings_sel = 0;
    st->edit_armed = SET_EDIT_NONE;
    cfg_load_ramps(st);
    cfg_load_program(st, PROG_HEAT);
    dirty_all(st);
}

static void enc_edit(app_state_t *st, int8_t dir)
{
    uint8_t sel = st->settings_sel;
    int16_t v;

    if (st->edit_armed == SET_EDIT_DELAY) {
        v = (int16_t)st->delay_s + dir * (int16_t)START_DELAY_STEP_S;
        if (v < 0)
            v = 0;
        if (v > (int16_t)TIMER_MAX_S)
            v = (int16_t)TIMER_MAX_S;
        st->delay_s = (uint16_t)v;
        cfg_save_program(st, PROG_HEAT);
        st->telem_dirty = 1u;
        return;
    }
    if (sel > SET_IDX_RAMP3)
        return;
    if (!ramp_on(st, sel)) {
        if (dir > 0)
            ensure_ramp(st, sel);
        return;
    }
    /* Pendiente OFF (temp_c==0): CW vuelve a temp_min. */
    if (st->ramp_step[sel].temp_c == 0u) {
        if (dir > 0 && st->edit_armed == SET_EDIT_TEMP) {
            st->ramp_step[sel].temp_c = st->temp_min_c;
            save_ramps(st);
        }
        return;
    }
    if (st->edit_armed == SET_EDIT_TEMP) {
        v = (int16_t)st->ramp_step[sel].temp_c
            + dir * (int16_t)RAMP_TEMP_STEP_C;
        if (v > (int16_t)st->temp_max_c)
            v = (int16_t)st->temp_max_c;
        if (v < (int16_t)st->temp_min_c) {
            /* R1: clamp. R2+: pending OFF (confirmar con PRESS). */
            if (sel == 0u)
                v = (int16_t)st->temp_min_c;
            else {
                st->ramp_step[sel].temp_c = 0u;
                return;
            }
        }
        st->ramp_step[sel].temp_c = (uint16_t)v;
        save_ramps(st);
        return;
    }
    if (st->edit_armed == SET_EDIT_TIME) {
        v = (int16_t)st->ramp_step[sel].hold_s
            + dir * (int16_t)TIMER_STEP_S;
        if (v < (int16_t)TIMER_STEP_S)
            v = (int16_t)TIMER_STEP_S;
        if (v > (int16_t)TIMER_MAX_S)
            v = (int16_t)TIMER_MAX_S;
        st->ramp_step[sel].hold_s = (uint16_t)v;
        save_ramps(st);
    }
}

static void set_press(app_state_t *st)
{
    uint8_t sel = st->settings_sel;

    if (sel >= SETTINGS_COUNT) {
        leave_set(st);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (sel <= SET_IDX_RAMP3) {
        if (!ramp_on(st, sel)) {
            ensure_ramp(st, sel);
            st->edit_armed = SET_EDIT_TEMP;
        } else if (st->edit_armed == SET_EDIT_NONE)
            st->edit_armed = SET_EDIT_TEMP;
        else if (st->edit_armed == SET_EDIT_TEMP) {
            /* Confirmar OFF pendiente. */
            if (sel > 0u && st->ramp_step[sel].temp_c == 0u) {
                st->ramp_n = sel;
                st->edit_armed = SET_EDIT_NONE;
                save_ramps(st);
            } else
                st->edit_armed = SET_EDIT_TIME;
        } else
            st->edit_armed = SET_EDIT_NONE;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    st->edit_armed = (st->edit_armed == SET_EDIT_DELAY)
                         ? SET_EDIT_NONE
                         : SET_EDIT_DELAY;
    buzzer_seq_beep_cat(st, BEEP_NAV, 1);
}

static void on_set_event(app_state_t *st, app_event_t evt)
{
    int8_t dir;

    if (evt == EVT_PRESS) {
        set_press(st);
        dirty_all(st);
        return;
    }
    if (evt != EVT_ENCODER_NEXT && evt != EVT_ENCODER_PREV)
        return;
    dir = (evt == EVT_ENCODER_NEXT) ? 1 : -1;
    if (st->edit_armed != SET_EDIT_NONE) {
        enc_edit(st, dir);
        dirty_all(st);
        return;
    }
    ui_window_rotate(&st->settings_sel, (uint8_t)(SETTINGS_COUNT + 1u), dir);
    dirty_all(st);
    buzzer_seq_beep_cat(st, BEEP_NAV, 1);
}

static uint8_t do_start(app_state_t *st)
{
    st->program = PROG_HEAT;
    if (st->delay_s > TIMER_MAX_S)
        st->delay_s = TIMER_MAX_S;
    st->delay_s = (uint16_t)((st->delay_s / 60u) * 60u);
    cfg_save_program(st, PROG_HEAT);
    cfg_load_ramps(st);
    if (st->ramp_n < 1u)
        return 1u;
    if (process_start(st, CTRL_UI) != PROG_OK)
        return 1u;
    dirty_all(st);
    return 0u;
}

void home_view_enter(app_state_t *st)
{
    if (!st)
        return;
    st->home_page = HOME_PAGE_MENU;
    if (st->home_sel >= HOME_COUNT)
        st->home_sel = 0;
    st->edit_armed = 0;
    if (st->phase == PH_DONE || st->phase == PH_FAULT)
        st->phase = PH_IDLE;
    cfg_load_ramps(st);
    cfg_load_program(st, PROG_HEAT);
    st->frame_dirty = 1;
    dirty_all(st);
}

void home_view_refresh(app_state_t *st)
{
    uint8_t i, f;

    if (!st)
        return;
    if (st->frame_dirty) {
        st7920_clear_gdram();
        st->frame_dirty = 0;
        dirty_all(st);
    }
    if (st->row_dirty & HOME_DIRTY_SIDE) {
        f = focus(st);
        for (i = 0; i < HOME_COUNT; i++)
            side_box(i, (uint8_t)(i == f));
    }
    if (st->row_dirty & (HOME_DIRTY_TEMP | HOME_DIRTY_BODY)) {
        if (show_set(st)) {
            panel_center(0u, SET_HDR_H, i18n_tr_hash(I18N_NAV_SETTINGS), 1u);
            draw_set_rows(st);
        } else if (focus(st) == HOME_IDX_HEAT || is_run(st) || is_usb(st))
            draw_heat_panel(st);
        else
            st7920_draw_band(PANEL_X, 96u, 0u, UI_FOOT_Y, 0, 0u, 0u);
    }
    if (st->row_dirty & HOME_DIRTY_FOOT) {
        if (is_usb(st))
            ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_USB_EXIT), 1u);
        else if (in_set(st))
            ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_USB_EXIT),
                                (uint8_t)(st->settings_sel >= SETTINGS_COUNT));
        else if (st->phase == PH_DONE || st->phase == PH_FAULT)
            ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_USB_EXIT), 1u);
        else if (focus(st) == HOME_IDX_HEAT) {
            if (is_run(st))
                ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_BTN_CANCEL), 1u);
            else
                ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_BTN_START), 1u);
        } else
            st7920_draw_band(PANEL_X, 96u, UI_FOOT_Y, UI_FOOT_H, 0, 0u, 0u);
    }
    st->row_dirty = 0;
}

void home_view_on_event(app_state_t *st, app_event_t evt)
{
    int8_t dir;
    uint8_t old;

    if (!st)
        return;

    if (is_usb(st)) {
        if (evt == EVT_PRESS) {
            device_session_leave_manual(st, 1u);
            st->home_sel = HOME_IDX_HEAT;
            st->home_page = HOME_PAGE_MENU;
            dirty_all(st);
            buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
        }
        return;
    }

    if (in_set(st)) {
        on_set_event(st, evt);
        return;
    }

    /* DONE/FAULT: Salir → IDLE */
    if (st->phase == PH_DONE || st->phase == PH_FAULT) {
        if (evt == EVT_PRESS) {
            st->phase = PH_IDLE;
            dirty_all(st);
            buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        }
        return;
    }

    if (is_run(st)) {
        if (evt == EVT_PRESS) {
            device_session_safe_stop(st, CTRL_UI);
            dirty_all(st);
            buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
        }
        return;
    }

    if (evt == EVT_ENCODER_NEXT || evt == EVT_ENCODER_PREV) {
        dir = (evt == EVT_ENCODER_NEXT) ? 1 : -1;
        old = st->home_sel;
        ui_window_rotate(&st->home_sel, HOME_COUNT, dir);
        if (st->home_sel != old) {
            if (st->home_sel == HOME_IDX_SETTINGS) {
                cfg_load_ramps(st);
                cfg_load_program(st, PROG_HEAT);
            }
            dirty_all(st);
            buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        }
        return;
    }

    if (evt != EVT_PRESS)
        return;

    if (st->home_sel == HOME_IDX_SETTINGS) {
        enter_set(st);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    buzzer_seq_beep_cat(st, do_start(st) ? BEEP_ALARM : BEEP_CONFIRM, 2);
}

void home_view_on_sensor(app_state_t *st)
{
    if (!st)
        return;
    st->row_dirty |= (uint8_t)(HOME_DIRTY_TEMP | HOME_DIRTY_BODY
                               | HOME_DIRTY_FOOT);
}
