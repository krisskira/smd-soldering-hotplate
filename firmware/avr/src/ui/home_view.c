#include "home_view.h"
#include "ui_text.h"
#include "ui_router.h"
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
#define PANEL_W    96u
#define BOX_H      32u
#define TEMP_TOP   3u    /* aire bajo el borde superior */
#define TEMP_H     8u    /* FONT_5X7 (sin X2: flash) */
#define LINE_H     8u    /* 5×7 + 1 */
#define LINE_GAP   4u    /* entre temp / fase / info */
#define PCOLS      ((128u - PANEL_TX) / 6u) /* ~15 cols visibles */
/* Sidebar texto 5×7 (sin FONT_ICONS: presupuesto flash). */

/* 0=heat 1=set 2=usb — wipe del panel solo al cambiar de modo. */
static uint8_t s_panel_mode;

static void panel_wipe(void)
{
    st7920_draw_band(PANEL_X, PANEL_W, 0u, UI_FOOT_Y, 0, 0u, 0u);
}

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

static void sel_rot(uint8_t *sel, uint8_t count, int8_t dir)
{
    if (!sel || count == 0u)
        return;
    if (dir > 0)
        *sel = (uint8_t)((*sel + 1u) % count);
    else
        *sel = (*sel == 0u) ? (uint8_t)(count - 1u) : (uint8_t)(*sel - 1u);
}

static void side_box(uint8_t i, uint8_t inv)
{
    st7920_span_t sp;
    char lab[2];

    lab[0] = (i == HOME_IDX_HEAT) ? 'H' : 'S';
    lab[1] = '\0';
    sp.f = &FONT_5X7;
    sp.str = lab;
    sp.x = 12u;
    st7920_draw_band(0u, 32u, (uint8_t)(i * BOX_H), BOX_H, &sp, 1u, inv);
}

static void panel_band(uint8_t y, uint8_t h, const char *s, uint8_t inv)
{
    st7920_span_t sp;

    sp.f = &FONT_5X7;
    sp.str = s;
    sp.x = PANEL_TX;
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

/* "123.4°C"; sin sensor "ERR". */
static void draw_centered_temp(const app_state_t *st, uint8_t y)
{
    char val[10];
    uint8_t n;

    ui_temp_to_str(&st->sensor, val);
    if (st->sensor.valid) {
        n = ui_str_len(val);
        val[n++] = (char)FONT_DEG_CHAR;
        val[n++] = 'C';
        val[n] = '\0';
    }
    panel_center(y, TEMP_H, val, 0u);
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

static void draw_heat_panel(const app_state_t *st, uint8_t dirty)
{
    uint8_t y_phase, y_info, mode;

    y_phase = (uint8_t)(TEMP_TOP + TEMP_H + LINE_GAP);
    y_info = (uint8_t)(y_phase + LINE_H + LINE_GAP);
    mode = is_usb(st) ? 2u : 0u;
    if (s_panel_mode != mode) {
        panel_wipe();
        s_panel_mode = mode;
        dirty = (uint8_t)(HOME_DIRTY_TEMP | HOME_DIRTY_BODY);
    }

    /* Banda = fondo+texto atómico. Sin wipe en cada tick → sin parpadeo. */
    if (dirty & HOME_DIRTY_TEMP)
        draw_centered_temp(st, TEMP_TOP);

    if (!(dirty & HOME_DIRTY_BODY))
        return;

    if (mode == 2u) {
        panel_center(y_phase, LINE_H, i18n_tr_hash(I18N_TITLE_USB), 0u);
        return;
    }
    panel_center(y_phase, LINE_H, process_phase_name(st->phase), 0u);
    draw_heat_info(st, y_info);
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

    if (idx <= SET_IDX_RAMP3) {
        buf[0] = 'R';
        buf[1] = (char)('1' + idx);
        if (!ramp_on(st, idx) || st->ramp_step[idx].temp_c == 0u) {
            ui_line_put(buf, (uint8_t)(PCOLS - 3u), i18n_tr_hash(I18N_OFF));
            return;
        }
        /* Hueco del '*': temp cierra en col 8, tiempo en col 14. */
        if (ed == SET_EDIT_TEMP && st->settings_sel == idx)
            buf[5] = '*';
        ui_u16_to_str(st->ramp_step[idx].temp_c, v);
        ui_line_put(buf, (uint8_t)(9u - ui_str_len(v)), v);
        if (ed == SET_EDIT_TIME && st->settings_sel == idx)
            buf[10] = '*';
        ui_u16_to_str(st->ramp_step[idx].hold_s, v);
        ui_line_put(buf, (uint8_t)(PCOLS - ui_str_len(v)), v);
        return;
    }
    ui_line_put(buf, 0, i18n_tr_hash(I18N_SET_DELAY));
    if (ed == SET_EDIT_DELAY)
        buf[9] = '*';
    ui_mmss_to_str(st->delay_s, v);
    ui_line_put(buf, (uint8_t)(PCOLS - 5u), v);
}

static void draw_set_panel(const app_state_t *st)
{
    char buf[LINE_LEN + 1];
    uint8_t r, inv, armed;

    if (s_panel_mode != 1u) {
        panel_wipe();
        s_panel_mode = 1u;
    }
    panel_center(0u, SET_HDR_H, i18n_tr_hash(I18N_TITLE_SETTINGS), 1u);
    armed = in_set(st);
    for (r = 0; r < SETTINGS_COUNT; r++) {
        ui_line_clear(buf);
        build_set_item(st, r, buf);
        buf[PCOLS] = '\0';
        inv = (armed && r == st->settings_sel) ? 1u : 0u;
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
    sel_rot(&st->settings_sel, (uint8_t)(SETTINGS_COUNT + 1u), dir);
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
            /* Ajustes: solo BODY (el sensor no debe repintar la lista). */
            if (st->row_dirty & HOME_DIRTY_BODY)
                draw_set_panel(st);
        } else if (focus(st) == HOME_IDX_HEAT || is_run(st) || is_usb(st))
            draw_heat_panel(st, st->row_dirty);
        else
            st7920_draw_band(PANEL_X, 96u, 0u, UI_FOOT_Y, 0, 0u, 0u);
    }
    if (st->row_dirty & HOME_DIRTY_FOOT) {
        if (is_usb(st))
            ui_comp_draw_footer(PANEL_X, I18N_USB_EXIT, 1u);
        else if (in_set(st))
            ui_comp_draw_footer(PANEL_X, I18N_USB_EXIT,
                                (uint8_t)(st->settings_sel >= SETTINGS_COUNT));
        else if (st->phase == PH_DONE || st->phase == PH_FAULT)
            ui_comp_draw_footer(PANEL_X, I18N_USB_EXIT, 1u);
        else if (focus(st) == HOME_IDX_HEAT) {
            if (is_run(st))
                ui_comp_draw_footer(PANEL_X, I18N_BTN_CANCEL, 1u);
            else
                ui_comp_draw_footer(PANEL_X, I18N_BTN_START, 1u);
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
        sel_rot(&st->home_sel, HOME_COUNT, dir);
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
    if (!st || show_set(st))
        return;
    /* Solo temperatura; fase/reloj si hay proceso activo (1 Hz). Sin pie. */
    st->row_dirty |= HOME_DIRTY_TEMP;
    if (is_run(st))
        st->row_dirty |= HOME_DIRTY_BODY;
}
