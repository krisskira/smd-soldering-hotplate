#include "ui_router.h"
#include "home_view.h"

void ui_enter_view(app_state_t *st, view_t v)
{
    if (!st)
        return;

    (void)v;
    st->view = VIEW_HOME;
    st->frame_dirty = 1;
    st->row_dirty = ROW_ALL;
    st->edit_armed = 0;
    home_view_enter(st);
}

void ui_router_init(app_state_t *st)
{
    if (!st)
        return;
    st->prev_view = VIEW_HOME;
    st->home_sel = 0;
    st->home_page = HOME_PAGE_MENU;
    st->settings_sel = 0;
    st->settings_page = SET_PAGE_MAIN;
    ui_enter_view(st, VIEW_HOME);
}

void ui_router_refresh(app_state_t *st)
{
    if (!st)
        return;
    home_view_refresh(st);
}

void ui_router_on_event(app_state_t *st, app_event_t evt)
{
    if (!st)
        return;
    home_view_on_event(st, evt);
}

void ui_router_on_sensor_update(app_state_t *st)
{
    if (!st)
        return;
    home_view_on_sensor(st);
}
