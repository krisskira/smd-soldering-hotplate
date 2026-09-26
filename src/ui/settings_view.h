#ifndef SETTINGS_VIEW_H
#define SETTINGS_VIEW_H

#include "../app/app_state.h"

void settings_view_enter(app_state_t *st);
void settings_view_refresh(app_state_t *st);
void settings_view_on_event(app_state_t *st, app_event_t evt);

#endif
