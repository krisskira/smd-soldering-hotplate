#include "usb_view.h"
#include "ui_text.h"
#include "ui_router.h"
#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "../services/buzzer_seq.h"
#include "../services/process.h"
#include "../services/device_session.h"
#include "lib/st7920/st7920.h"

/* USB shell mínimo (flash): cabecera + temp + Salir. Fase en $HP. */

void usb_view_enter(app_state_t *st)
{
    if (!st) return;
    st->frame_dirty = 1;
    st->row_dirty = ROW_ALL;
}

void usb_view_refresh(app_state_t *st)
{
    if (!st) return;
    if (st->frame_dirty) {
        ui_comp_draw_header(i18n_tr_hash(I18N_TITLE_USB), ICO_COUNT);
        ui_comp_draw_footer(0u, i18n_tr_hash(I18N_USB_EXIT), 1u);
        st->frame_dirty = 0;
        st->row_dirty = ROW_ALL;
    }
    if (st->row_dirty) {
        ui_comp_draw_temp(0u, 4u, 24u, 18u, &st->sensor);
        st->row_dirty = 0;
    }
}

void usb_view_on_event(app_state_t *st, app_event_t evt)
{
    if (!st) return;
    if (evt == EVT_PRESS) {
        device_session_leave_manual(st, 1u);
        process_stop(st, CTRL_UI);
        ui_enter_view(st, VIEW_HOME);
        buzzer_seq_beep_cat(st, BEEP_CONFIRM, 2);
    }
}
