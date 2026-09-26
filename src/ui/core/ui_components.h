#ifndef UI_COMPONENTS_H
#define UI_COMPONENTS_H

#include <stdint.h>
#include "ui_icons.h"

typedef enum {
    UI_COMP_NORMAL = 0,
    UI_COMP_SELECTED,
    UI_COMP_EDITING
} ui_comp_state_t;

/** Cabecera invertida (negrita) + icono opcional. ICO_COUNT = sin icono. */
void ui_comp_draw_header(const char *title, ui_icon_id_t ico);

/* Pie de vista: banda de todo el ancho, y 54–63. */
#define UI_FOOT_Y 54u
#define UI_FOOT_H 10u
#define UI_FOOT_X 4u

/** Pie "label ↵". inv = 1 cuando el pie tiene el foco (en USB, siempre). */
void ui_comp_draw_footer(const char *label, uint8_t inv);

/** Formatea fila LINE_LEN: botón de menú / volver. */
void ui_comp_format_menu(char *buf, const char *label, ui_comp_state_t st);

/** Formatea fila: label + ON/OFF a la derecha. */
void ui_comp_format_toggle(char *buf, const char *label, uint8_t on,
                           ui_comp_state_t st);

/** Formatea fila: label + valor (+ '*' si EDITING). */
void ui_comp_format_number(char *buf, const char *label, const char *value,
                           ui_comp_state_t st);

/** Formatea CTA: "[ LABEL ]". */
void ui_comp_format_action(char *buf, const char *label, ui_comp_state_t st);

#endif
