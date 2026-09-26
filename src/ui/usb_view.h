#ifndef USB_VIEW_H
#define USB_VIEW_H

#include "../app/app_state.h"

void usb_view_enter(app_state_t *st);
void usb_view_refresh(app_state_t *st);
void usb_view_on_event(app_state_t *st, app_event_t evt);

#endif
