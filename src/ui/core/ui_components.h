#ifndef UI_COMPONENTS_H
#define UI_COMPONENTS_H

#include <stdint.h>
#include "../../app/app_state.h"

/* Pie de vista: banda y 54–63. */
#define UI_FOOT_Y 54u
#define UI_FOOT_H 10u
#define UI_FOOT_X 4u

/** Pie con texto i18n (PROGMEM). inv = 1 cuando el pie tiene el foco. */
void ui_comp_draw_footer(uint8_t x, uint8_t i18n_id, uint8_t inv);

#endif
