#ifndef UI_COMPONENTS_H
#define UI_COMPONENTS_H

#include <stdint.h>
#include "ui_icons.h"
#include "../../app/app_state.h"

typedef enum {
    UI_COMP_NORMAL = 0,
    UI_COMP_SELECTED,
    UI_COMP_EDITING
} ui_comp_state_t;

/* Pie de vista: banda y 54–63. */
#define UI_FOOT_Y 54u
#define UI_FOOT_H 10u
#define UI_FOOT_X 4u

/** Pie "label ↵" desde x. inv = 1 cuando el pie tiene el foco. */
void ui_comp_draw_footer(uint8_t x, const char *label, uint8_t inv);

/** Temperatura 8×12 + "C" en banda [band_x..127], texto en text_x. */
void ui_comp_draw_temp(uint8_t band_x, uint8_t text_x, uint8_t y, uint8_t h,
                       const sensor_reading_t *r);

#endif
