#include "ui_components.h"
#include "i18n/i18n_c.h"
#include "lib/st7920/st7920.h"
#include "lib/fonts/font.h"

void ui_comp_draw_footer(uint8_t x, uint8_t i18n_id, uint8_t inv)
{
    st7920_span_t s;

    s.f = &FONT_5X7;
    s.str = i18n_tr_hash(i18n_id);
    s.x = (uint8_t)(x + UI_FOOT_X);
    st7920_draw_band(x, (uint8_t)(128u - x), UI_FOOT_Y, UI_FOOT_H, &s, 1u, inv);
}
