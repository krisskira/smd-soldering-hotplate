#include "usb_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_icons.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "assets/usb_icon_32.h"
#include "../services/buzzer_seq.h"
#include "../services/process.h"
#include "../services/pid_atune.h"
#include "../services/device_session.h"
#include "lib/st7920/st7920.h"
#include "lib/fonts/font.h"

/*
 * Mapa de la vista (128×64). Cada zona es un rectángulo propio: se pinta
 * entero y no invade a las demás. La GDRAM va en bloques de 16 px, así que
 * el borde entre icono y texto cae en x = 32.
 *
 *   y  0–14   cabecera invertida, todo el ancho
 *   y 16–47   icono USB 32×32, x 0–31 (se pinta una vez al entrar)
 *   y 16–33   temperatura 8×12, x 32–127
 *   y 34–43   programa 5×7,     x 32–127
 *   y 44–53   fase + tiempo,    x 32–127
 *   y 54–63   pie invertido "Salir ↵", todo el ancho
 */
#define USB_ICON_X    0u
#define USB_ICON_Y    16u
#define USB_BODY_X    32u
#define USB_BODY_W    (128u - USB_BODY_X)
#define USB_TEXT_X    40u
#define USB_TEMP_Y    16u
#define USB_TEMP_H    18u
#define USB_PROG_Y    34u
#define USB_ACTION_Y  44u
#define USB_LINE_H    10u
#define USB_FOOT_Y    54u
#define USB_FOOT_H    10u
#define USB_FOOT_X    4u

/* Columnas de 6 px que caben desde USB_TEXT_X hasta el borde. */
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

static void span_set(st7920_span_t *s, const font_t *f, const char *str,
                     uint8_t x)
{
    s->f = f;
    s->str = str;
    s->x = x;
    s->scale = 1;
    s->bold = 0;
}

static void draw_line(uint8_t y, const char *str)
{
    st7920_span_t s;

    span_set(&s, &FONT_5X7, str, USB_TEXT_X);
    st7920_draw_band(USB_BODY_X, USB_BODY_W, y, USB_LINE_H, &s, 1u, 0u);
}

static void draw_footer(void)
{
    static const char enter[2] = { (char)(ICO_ENTER + 1u), '\0' };
    char label[LINE_LEN + 1];
    st7920_span_t s[2];
    uint8_t n;

    ui_line_clear(label);
    ui_line_put(label, 0, i18n_tr_hash(I18N_USB_EXIT));
    n = ui_str_len(i18n_tr_hash(I18N_USB_EXIT));
    label[n] = '\0';
    span_set(&s[0], &FONT_5X7, label, USB_FOOT_X);
    span_set(&s[1], &FONT_ICONS, enter,
             (uint8_t)(USB_FOOT_X + (n + 1u) * FONT_5X7.advance));
    st7920_draw_band(0, 128u, USB_FOOT_Y, USB_FOOT_H, s, 2u, 1u);
}

static void draw_temp(const sensor_reading_t *r)
{
    static const char unit[2] = { 'C', '\0' };
    char val[10];
    st7920_span_t s[2];
    uint8_t n = 1;
    uint8_t len;

    if (r && r->valid) {
        ui_temp_to_str(r, val);
        len = ui_str_len(val);
        val[len++] = (char)FONT_DEG_CHAR;
        val[len] = '\0';
        span_set(&s[1], &FONT_5X7, unit,
                 (uint8_t)(USB_TEXT_X + font_text_width(&FONT_8X12, val, 1u)
                           + 2u));
        n = 2;
    } else {
        val[0] = '-'; val[1] = '-'; val[2] = '-'; val[3] = '.'; val[4] = '-';
        val[5] = '\0';
    }
    span_set(&s[0], &FONT_8X12, val, USB_TEXT_X);
    st7920_draw_band(USB_BODY_X, USB_BODY_W, USB_TEMP_Y, USB_TEMP_H, s, n, 0u);
}

static void draw_body(const app_state_t *st)
{
    char line[LINE_LEN + 1];

    draw_temp(&st->sensor);

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
        st7920_write_frame_pgm(USB_ICON_X, USB_ICON_Y, usb_icon_32,
                               USB_ICON_W, USB_ICON_H, USB_ICON_BPR);
        draw_footer();
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
