#ifndef UI_FONT_H
#define UI_FONT_H

/*
 * Fuentes en uso:
 *   UI_FONT_* → FONT_5X7. home_view usa FONT_5X7_X2 / FONT_ICONS directo.
 * FONT_8X12 no se enlaza.
 */

#include <stdint.h>
#include "lib/st7920/st7920.h"
#include "fonts/font.h"

typedef enum {
    UI_FONT_SMALL = 0,
    UI_FONT_NORMAL,
    UI_FONT_LARGE,
    UI_FONT_ICONS
} ui_font_t;

typedef enum {
    UI_X1 = 1,
    UI_X2 = 2
} ui_scale_t;

static inline const font_t *ui_font_get(ui_font_t font)
{
    switch (font) {
    default:             return &FONT_5X7;
    }
}

/** Alto del glifo a esa escala (sin banda). */
static inline uint8_t ui_font_height(ui_font_t font, ui_scale_t scale)
{
    return (uint8_t)(ui_font_get(font)->h * (uint8_t)scale);
}

static inline uint8_t ui_text_width(const char *s, ui_font_t font,
                                    ui_scale_t scale)
{
    return (uint8_t)font_text_width(ui_font_get(font), s, (uint8_t)scale);
}

/** h = alto de la banda (0 = alto del glifo); el texto va centrado en ella. */
static inline void ui_text_draw(uint8_t x, uint8_t y, uint8_t h,
                                const char *s, ui_font_t font,
                                ui_scale_t scale, uint8_t inv)
{
    st7920_draw_font_gdram(ui_font_get(font), x, y, h, s, (uint8_t)scale, inv);
}

static inline void ui_text_center(uint8_t y, uint8_t h, const char *s,
                                  ui_font_t font, ui_scale_t scale, uint8_t inv)
{
    uint8_t w = ui_text_width(s, font, scale);
    ui_text_draw((uint8_t)((128u - (w > 128u ? 128u : w)) / 2u), y, h, s,
                 font, scale, inv);
}

#endif
