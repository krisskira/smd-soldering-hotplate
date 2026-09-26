#ifndef UI_TEXT_H
#define UI_TEXT_H

#include <stdint.h>
#include "../../app/app_config.h"
#include "../../app/app_state.h"

uint8_t ui_str_len(const char *s);
void ui_line_clear(char *buf);
void ui_line_put(char *buf, uint8_t col, const char *s);
void ui_line_put_right(char *buf, const char *s);
void ui_u16_to_str(uint16_t v, char *dst);
void ui_hex8_to_str(uint8_t v, char *dst);
void ui_temp_to_str(const sensor_reading_t *r, char *dst);

/** mm:ss from total seconds (max 99:59 display). */
void ui_mmss_to_str(uint16_t sec, char *dst);

/** Gain ×10 → "12.3" style (1 decimal). */
void ui_gain_to_str(int16_t x10, char *dst);

#endif
