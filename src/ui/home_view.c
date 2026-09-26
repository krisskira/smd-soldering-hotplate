#include "home_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_window.h"
#include "ui_components.h"
#include "ui_icons.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/cfg_store.h"
#include "../services/process.h"
#include "../services/device_session.h"
#include "lib/st7920/st7920.h"
#include "lib/st7920/st7920_private.h"
#include "lib/fonts/font.h"

/* x0..30 barra | x31 | x32..127 panel. Tres casillas de ~21 px. */
#define PANEL_X    32u
#define PANEL_TX   36u
#define BOX_H      21u
#define TEMP_H     18u
#define LINE_H     10u
#define PCOLS      ((128u - PANEL_TX) / 6u)

static const ui_icon_id_t s_ico[3] = { ICO_START, ICO_TIMER, ICO_CFG };

static uint8_t is_run(const app_state_t *st)
{
    return process_is_active(st);
}

static uint8_t focus(const app_state_t *st)
{
    if (!is_run(st))
        return st->home_sel;
    return (st->program == PROG_START_IN) ? HOME_IDX_START_IN
                                          : HOME_IDX_STOP_IN;
}

static void side_box(uint8_t i, uint8_t inv)
{
    char ico[2];
    uint8_t y0 = (uint8_t)(i * BOX_H);
    uint8_t h = (i == 2u) ? 22u : BOX_H;
    uint8_t iy = (uint8_t)(y0 + (h - 16u) / 2u);
    uint8_t ix = 7u;
    uint8_t py;
    uint16_t row[2], fill = inv ? 0xFFFFu : 0u;

    ico[0] = ui_icon_char(s_ico[i]);
    ico[1] = '\0';
    for (py = y0; py < (uint8_t)(y0 + h); py++) {
        row[0] = fill;
        row[1] = (uint16_t)(fill | 0x0001u); /* x=31 */
        st7920_font_row(row, py, &FONT_ICONS, ix, iy, ico, 2u, inv);
        st7920_write_gdram(0, py, (uint8_t)(row[0] >> 8), (uint8_t)row[0]);
        st7920_write_gdram(1, py, (uint8_t)(row[1] >> 8), (uint8_t)row[1]);
    }
}

static void line_at(uint8_t y, const char *s)
{
    st7920_span_t sp = { &FONT_5X7, s, PANEL_TX, 1u, 0u };
    st7920_draw_band(PANEL_X, (uint8_t)(128u - PANEL_X), y, LINE_H, &sp, 1u, 0u);
}

static void clear_line(uint8_t y)
{
    st7920_draw_band(PANEL_X, (uint8_t)(128u - PANEL_X), y, LINE_H, 0, 0u, 0u);
}

/* buf ya limpio. "RAMPA: Paso i/n" o "RAMPA: OFF". */
static void fmt_ramp(const app_state_t *st, char *buf)
{
    ui_line_put(buf, 0, i18n_tr_hash(I18N_PANEL_RAMP));
    if (!st->ramps_en || st->ramp_n == 0u) {
        ui_line_put(buf, 7, i18n_tr_hash(I18N_OFF));
        return;
    }
    ui_line_put(buf, 7, i18n_tr_hash(I18N_RAMP_STEP));
    buf[12] = (is_run(st) && st->program == PROG_STOP_IN && st->phase == PH_RUN)
        ? (char)('0' + st->ramp_idx + 1u) : '-';
    buf[13] = '-';
    buf[14] = (char)('0' + st->ramp_n);
}

static void fmt_elapsed(const app_state_t *st, char *buf)
{
    char t[6];
    ui_line_put(buf, 0, i18n_tr_hash(I18N_PANEL_ELAPSED));
    ui_mmss_to_str(is_run(st) ? st->t_elapsed_s : 0u, t);
    ui_line_put(buf, 8, t);
}

static void draw_body(const app_state_t *st)
{
    char line[LINE_LEN + 1];
    char t[6];
    uint8_t f = focus(st);

    if (is_run(st)) {
        ui_line_clear(line);
        ui_line_put(line, 0, i18n_tr_hash(st->program == PROG_START_IN
            ? I18N_PROG_START_IN : I18N_PROG_STOP_IN));
        line[PCOLS] = '\0';
        line_at(20, line);

        ui_line_clear(line);
        ui_line_put(line, 0, process_phase_name(st->phase));
        if (st->t_remain_s) {
            ui_mmss_to_str(st->t_remain_s, t);
            ui_line_put(line, (uint8_t)(PCOLS - 5u), t);
        }
        line[PCOLS] = '\0';
        line_at(30, line);

        ui_line_clear(line);
        if (st->program == PROG_STOP_IN)
            fmt_ramp(st, line);
        else
            fmt_elapsed(st, line);
        line[PCOLS] = '\0';
        line_at(40, line);
        return;
    }

    ui_line_clear(line);
    if (f == HOME_IDX_STOP_IN) {
        fmt_ramp(st, line);
        line[PCOLS] = '\0';
        line_at(20, line);
        ui_line_clear(line);
        fmt_elapsed(st, line);
        line[PCOLS] = '\0';
        line_at(30, line);
        clear_line(40);
    } else if (f == HOME_IDX_START_IN) {
        ui_line_put(line, 0, i18n_tr_hash(I18N_PANEL_SET));
        if (st->edit_armed)
            line[4] = '*';
        line[5] = '[';
        ui_mmss_to_str(st->delay_s, t);
        ui_line_put(line, 6, t);
        line[11] = ']';
        line[PCOLS] = '\0';
        line_at(20, line);
        clear_line(30);
        clear_line(40);
    } else {
        ui_line_put(line, 0, i18n_tr_hash(I18N_NAV_SETTINGS));
        line[PCOLS] = '\0';
        line_at(20, line);
        clear_line(30);
        clear_line(40);
    }
}

static void dirty_all(app_state_t *st)
{
    st->row_dirty = HOME_DIRTY_ALL;
}

static uint8_t do_start(app_state_t *st, program_id_t prog)
{
    st->program = prog;
    if (prog == PROG_START_IN) {
        if (st->delay_s < 60u)
            st->delay_s = 60u;
        if (st->delay_s > TIMER_MAX_S)
            st->delay_s = TIMER_MAX_S;
        st->delay_s = (uint16_t)((st->delay_s / 60u) * 60u);
        if (st->delay_s == 0u)
            st->delay_s = 60u;
        cfg_save_program(st, PROG_START_IN);
    } else if (!st->ramps_en || st->ramp_n < 1u) {
        return 1u;
    }
    if (process_start(st, CTRL_UI) != PROG_OK)
        return 1u;
    st->edit_armed = 0;
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
    cfg_load_ramps(st);
    cfg_load_program(st, PROG_START_IN);
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
    if (st->row_dirty & HOME_DIRTY_TEMP)
        ui_comp_draw_temp(PANEL_X, PANEL_TX, 0u, TEMP_H, &st->sensor);
    if (st->row_dirty & HOME_DIRTY_BODY)
        draw_body(st);
    if (st->row_dirty & HOME_DIRTY_FOOT) {
        if (is_run(st))
            ui_comp_draw_footer(PANEL_X, i18n_tr_hash(I18N_USB_EXIT), 1u);
        else
            st7920_draw_band(PANEL_X, (uint8_t)(128u - PANEL_X),
                             UI_FOOT_Y, UI_FOOT_H, 0, 0u, 0u);
    }
    st->row_dirty = 0;
}

void home_view_on_event(app_state_t *st, app_event_t evt)
{
    int8_t dir;
    uint8_t old;

    if (!st)
        return;

    if (is_run(st)) {
        if (evt == EVT_PRESS) {
            device_session_safe_stop(st, CTRL_UI);
            st->edit_armed = 0;
            dirty_all(st);
            buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
        }
        return;
    }

    if (evt == EVT_ENCODER_NEXT || evt == EVT_ENCODER_PREV) {
        dir = (evt == EVT_ENCODER_NEXT) ? 1 : -1;
        if (st->edit_armed && st->home_sel == HOME_IDX_START_IN) {
            int16_t v = (int16_t)st->delay_s + dir * 60;
            if (v < 60)
                v = 60;
            if (v > (int16_t)TIMER_MAX_S)
                v = (int16_t)TIMER_MAX_S;
            st->delay_s = (uint16_t)v;
            st->row_dirty |= HOME_DIRTY_BODY;
            return;
        }
        old = st->home_sel;
        ui_window_rotate(&st->home_sel, HOME_COUNT, dir);
        if (st->home_sel != old) {
            st->edit_armed = 0;
            st->row_dirty |= (uint8_t)(HOME_DIRTY_SIDE | HOME_DIRTY_BODY);
            buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        }
        return;
    }

    if (evt != EVT_PRESS)
        return;

    if (st->home_sel == HOME_IDX_SETTINGS) {
        ui_enter_view(st, VIEW_SETTINGS);
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    if (st->home_sel == HOME_IDX_STOP_IN) {
        buzzer_seq_beep_cat(st, do_start(st, PROG_STOP_IN) ? BEEP_ALARM
                                                           : BEEP_CONFIRM, 2);
        return;
    }
    if (!st->edit_armed) {
        st->edit_armed = 1;
        st->row_dirty |= HOME_DIRTY_BODY;
        buzzer_seq_beep_cat(st, BEEP_NAV, 1);
        return;
    }
    buzzer_seq_beep_cat(st, do_start(st, PROG_START_IN) ? BEEP_ALARM
                                                        : BEEP_CONFIRM, 2);
}

void home_view_on_sensor(app_state_t *st)
{
    if (!st)
        return;
    st->row_dirty |= (uint8_t)(HOME_DIRTY_TEMP | HOME_DIRTY_BODY);
    if (is_run(st))
        st->row_dirty |= HOME_DIRTY_FOOT;
}
