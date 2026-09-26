#include "ui_window.h"

uint8_t ui_window_top(uint8_t sel, uint8_t visible)
{
    if (visible == 0u || sel < visible)
        return 0;
    return (uint8_t)(sel - (visible - 1u));
}

void ui_window_rotate(uint8_t *sel, uint8_t count, int8_t dir)
{
    if (!sel || count == 0u)
        return;
    if (dir > 0)
        *sel = (uint8_t)((*sel + 1u) % count);
    else
        *sel = (*sel == 0u) ? (uint8_t)(count - 1u) : (uint8_t)(*sel - 1u);
}

int8_t ui_window_focus_row(uint8_t sel, uint8_t visible, uint8_t first_row)
{
    uint8_t top = ui_window_top(sel, visible);
    return (int8_t)((int8_t)first_row + (int8_t)sel - (int8_t)top);
}
