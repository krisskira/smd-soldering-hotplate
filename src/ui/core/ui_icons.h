#ifndef UI_ICONS_H
#define UI_ICONS_H

#include <stdint.h>

typedef enum {
    ICO_ENTER = 0,
    ICO_START,
    ICO_TIMER,
    ICO_CFG,
    ICO_COUNT
} ui_icon_id_t;

/** Carácter del icono dentro de un texto con FONT_ICONS (0 termina la cadena). */
static inline char ui_icon_char(ui_icon_id_t id)
{
    return (char)((uint8_t)id + 1u);
}

#ifdef UI_NO_ICONS
static inline void ui_icon_copy(ui_icon_id_t id, uint8_t *dst)
{ (void)id; (void)dst; }
static inline void ui_icon_draw(uint8_t x, uint8_t y, ui_icon_id_t id)
{ (void)x; (void)y; (void)id; }
static inline void ui_icon_draw_gdram(uint8_t x, uint8_t y, ui_icon_id_t id)
{ (void)x; (void)y; (void)id; }
static inline void ui_icon_stamp_row(uint16_t *row, uint8_t row_y,
                                     uint8_t x, uint8_t y, ui_icon_id_t id,
                                     uint8_t clear)
{ (void)row; (void)row_y; (void)x; (void)y; (void)id; (void)clear; }
#else
void ui_icon_copy(ui_icon_id_t id, uint8_t *dst);
void ui_icon_draw(uint8_t x, uint8_t y, ui_icon_id_t id);
void ui_icon_draw_gdram(uint8_t x, uint8_t y, ui_icon_id_t id);
/** Pinta el icono sobre una fila ya rellena. clear=1 lo recorta (fondo ON). */
void ui_icon_stamp_row(uint16_t *row, uint8_t row_y, uint8_t x, uint8_t y,
                       ui_icon_id_t id, uint8_t clear);
#endif

#endif
