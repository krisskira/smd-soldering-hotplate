#include "usb_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/process.h"
#include "../services/pid_atune.h"
#include "../services/device_session.h"
#include "lib/st7920/st7920.h"
#include "lib/fonts/font.h"

/*
 *   y  0–14   cabecera invertida
 *   y 16–47   etiqueta "USB" a escala 2, x 0–31
 *   y 16–33   temperatura 8×12, x 32–127
 *   y 34–43   programa 5×7
 *   y 44–53   fase + tiempo
 *   y 54–63   pie "Salir ↵"
 */
#define USB_BODY_X    32u
#define USB_BODY_W    (128u - USB_BODY_X)
#define USB_TEXT_X    40u
#define USB_TEMP_Y    16u
#define USB_TEMP_H    18u
#define USB_PROG_Y    34u
#define USB_ACTION_Y  44u
#define USB_LINE_H    10u
#define USB_BODY_COLS ((128u - USB_TEXT_X) / 6u)

static uint8_t prog_key(program_id_t p)
{
    switch (p) {
    case PROG_START_IN: return I18N_PROG_START_IN;
    case PROG_STOP_IN:  return I18N_PROG_STOP_IN;
    case PROG_PREHEAT:  return I18N_PROG_PREHEAT;
    case PROG_PID_TUNE: return I18N_PROG_PID_TUNE;
    default:            return I18N_PROG_PREHEAT;
    }
}

static void draw_line(uint8_t y, const char *str)
{
    st7920_span_t s = { &FONT_5X7, str, USB_TEXT_X, 1u, 0u };
    st7920_draw_band(USB_BODY_X, USB_BODY_W, y, USB_LINE_H, &s, 1u, 0u);
}

static void draw_usb_mark(void)
{
    static const char mark[] = "USB";
    st7920_span_t s = { &FONT_5X7, mark, 8u, 1u, 0u };
    st7920_draw_band(0, USB_BODY_X, 28u, 10u, &s, 1u, 0u);
}

static void draw_body(const app_state_t *st)
{
    char line[LINE_LEN + 1];

    ui_comp_draw_temp(USB_BODY_X, USB_TEXT_X, USB_TEMP_Y, USB_TEMP_H,
                      &st->sensor);

    ui_line_clear(line);
    ui_line_put(line, 0, i18n_tr_hash(prog_key(st->program)));
    line[USB_BODY_COLS] = '\0';
    draw_line(USB_PROG_Y, line);

    ui_line_clear(line);
    if (pid_atune_active(st))
        ui_line_put(line, 0, i18n_tr_hash(I18N_PROG_PID_TUNE));
    else
        ui_line_put(line, 0, process_phase_name(st->phase));
    if (st->t_remain_s > 0) {
        char tbuf[8];
        ui_mmss_to_str(st->t_remain_s, tbuf);
        ui_line_put(line, (uint8_t)(USB_BODY_COLS - 5u), tbuf);
    }
    line[USB_BODY_COLS] = '\0';
    draw_line(USB_ACTION_Y, line);
}

void usb_view_enter(app_state_t *st)
{
    if (!st)
        return;
    st->usb_sel = 0;
    st->frame_dirty = 1;
    st->row_dirty = ROW_ALL;
}

void usb_view_refresh(app_state_t *st)
{
    if (!st)
        return;

    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(I18N_TITLE_USB), ICO_COUNT);
        draw_usb_mark();
        ui_comp_draw_footer(0u, i18n_tr_hash(I18N_USB_EXIT), 1u);
        st->frame_dirty = 0;
        st->row_dirty = ROW_ALL;
    }

    if (st->row_dirty) {
        draw_body(st);
        st->row_dirty = 0;
    }
}

void usb_view_on_event(app_state_t *st, app_event_t evt)
{
    if (!st)
        return;
    if (evt == EVT_PRESS) {
        device_session_leave_manual(st, 1u);
        process_stop(st, CTRL_UI);
        ui_enter_view(st, VIEW_HOME);
        buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
    }
}
