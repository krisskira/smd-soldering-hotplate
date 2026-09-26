#ifndef UI_WINDOW_H
#define UI_WINDOW_H

#include <stdint.h>
#include "../../app/app_state.h"
#include "../../app/app_config.h"

uint8_t ui_window_top(uint8_t sel, uint8_t visible);
void ui_window_rotate(uint8_t *sel, uint8_t count, int8_t dir);
int8_t ui_window_focus_row(uint8_t sel, uint8_t visible, uint8_t first_row);

static inline void ui_window_dirty_all(app_state_t *st)
{
    if (st)
        st->row_dirty = ROW_ALL;
}

#endif
