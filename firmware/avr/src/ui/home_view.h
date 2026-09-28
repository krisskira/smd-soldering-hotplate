#ifndef HOME_VIEW_H
#define HOME_VIEW_H

#include "../app/app_state.h"

void home_view_enter(app_state_t *st);
void home_view_refresh(app_state_t *st);
void home_view_on_event(app_state_t *st, app_event_t evt);
void home_view_on_sensor(app_state_t *st);

#endif
