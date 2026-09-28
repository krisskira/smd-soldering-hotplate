#ifndef UI_ROUTER_H
#define UI_ROUTER_H

#include "../app/app_state.h"

void ui_router_init(app_state_t *st);
void ui_router_refresh(app_state_t *st);
void ui_router_on_event(app_state_t *st, app_event_t evt);
void ui_router_on_sensor_update(app_state_t *st);

/** Cambia de vista (frame_dirty + row_dirty). */
void ui_enter_view(app_state_t *st, view_t v);

#endif
