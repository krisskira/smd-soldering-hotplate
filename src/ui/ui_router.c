#include "ui_router.h"
#include "home_view.h"
#include "usb_view.h"
#include "settings_view.h"

void ui_enter_view(app_state_t *st, view_t v)
{
    if (!st)
        return;

    st->view = v;
    st->frame_dirty = 1;
    st->row_dirty = ROW_ALL;
    st->edit_armed = 0;

    switch (v) {
    case VIEW_USB:
        usb_view_enter(st);
        break;
    case VIEW_SETTINGS:
        settings_view_enter(st);
        break;
    case VIEW_HOME:
    default:
        home_view_enter(st);
        st->view = VIEW_HOME;
        break;
    }
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

    switch (st->view) {
    case VIEW_USB:
        usb_view_refresh(st);
        break;
    case VIEW_SETTINGS:
        settings_view_refresh(st);
        break;
    case VIEW_HOME:
    default:
        home_view_refresh(st);
        break;
    }
}

void ui_router_on_event(app_state_t *st, app_event_t evt)
{
    if (!st)
        return;

    switch (st->view) {
    case VIEW_USB:
        usb_view_on_event(st, evt);
        break;
    case VIEW_SETTINGS:
        settings_view_on_event(st, evt);
        break;
    case VIEW_HOME:
    default:
        home_view_on_event(st, evt);
        break;
    }
}

void ui_router_on_sensor_update(app_state_t *st)
{
    if (!st)
        return;

    if (st->view == VIEW_USB)
        st->row_dirty = ROW_ALL;
    else if (st->view == VIEW_HOME)
        home_view_on_sensor(st);
}
