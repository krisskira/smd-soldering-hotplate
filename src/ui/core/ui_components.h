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

/** Cabecera invertida (negrita) + icono opcional. ICO_COUNT = sin icono. */
void ui_comp_draw_header(const char *title, ui_icon_id_t ico);

/* Pie de vista: banda y 54–63. */
#define UI_FOOT_Y 54u
#define UI_FOOT_H 10u
#define UI_FOOT_X 4u

/** Pie "label ↵" desde x. inv = 1 cuando el pie tiene el foco. */
void ui_comp_draw_footer(uint8_t x, const char *label, uint8_t inv);

/** Temperatura 8×12 + "C" en banda [band_x..127], texto en text_x. */
void ui_comp_draw_temp(uint8_t band_x, uint8_t text_x, uint8_t y, uint8_t h,
                       const sensor_reading_t *r);

/** Línea 5×7 en banda [band_x .. band_x+band_w). str=NULL o "" limpia. */
#define UI_COMP_LINE_H 10u
void ui_comp_draw_5x7_band(uint8_t band_x, uint8_t band_w, uint8_t text_x,
                           uint8_t y, const char *str);

/** Fila de lista 5×7 a todo el ancho, invierte si inv!=0. */
void ui_comp_draw_5x7_row(uint8_t y, uint8_t h, const char *str, uint8_t inv);

/** Formatea fila LINE_LEN: botón de menú / volver. */
void ui_comp_format_menu(char *buf, const char *label, ui_comp_state_t st);

/** Formatea fila: label + ON/OFF a la derecha. */
void ui_comp_format_toggle(char *buf, const char *label, uint8_t on,
                           ui_comp_state_t st);

#endif
