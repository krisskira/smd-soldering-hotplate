#ifndef FONT_H
#define FONT_H

/*
 * Sistema de fuentes (solo datos en flash + búsqueda de glifos).
 * El dibujo en pantalla está en lib/st7920 (st7920_draw_font_gdram).
 *
 *   FONT_5X7       SMALL   menús
 *   FONT_6X8_BOLD  NORMAL  títulos
 *   FONT_8X12      LARGE   temperatura (solo dígitos y unidades)
 *   FONT_ICONS     símbolos 8×8 (glifo = ui_icon_id_t)
 *
 * font6x8_bold.c y font8x12.c los genera tools/gen_fonts.py.
 */

#include <stdint.h>

#define FONT_COLS 0u     /* 1 byte por columna, bit 0 = fila superior (h <= 8) */
#define FONT_ROWS 1u     /* (w + 7) / 8 bytes por fila, MSB = izquierda */

#define FONT_NO_GLYPH 0xFFu

/* '°' en Latin-1. Escribir "25" FONT_DEG "C": "\xB0C" sería un solo escape. */
#define FONT_DEG_CHAR 0xB0u
#define FONT_DEG      "\xB0"
/* "°" en UTF-8 es C2 B0: el C2 se ignora y B0 pinta el grado. */
#define FONT_UTF8_C2  0xC2u

typedef struct {
    const uint8_t *data;   /* PROGMEM */
    const char *map;       /* PROGMEM; orden de glifos. NULL = rango first..first+count */
    uint8_t w;             /* ancho del glifo en px */
    uint8_t h;             /* alto del glifo en px (el centrado usa este valor) */
    uint8_t advance;       /* avance horizontal: w + separación */
    uint8_t first;         /* primer código (map == NULL) */
    uint8_t count;         /* glifos del rango (map == NULL) */
    uint8_t deg;           /* índice del '°' si map == NULL, o FONT_NO_GLYPH */
    uint8_t layout;        /* FONT_COLS | FONT_ROWS */
} font_t;

extern const font_t FONT_5X7;
extern const font_t FONT_6X8_BOLD;
extern const font_t FONT_8X12;
extern const font_t FONT_ICONS;

/** Tabla 5×7 cruda: la usa también el texto 5×7 original de st7920. */
extern const uint8_t font5x7_data[];

/** Índice del glifo para el byte c, o FONT_NO_GLYPH. */
uint8_t font_glyph(const font_t *f, uint8_t c);

/** Bytes por glifo en data. */
uint8_t font_glyph_bytes(const font_t *f);

/** Ancho de tinta en px (sin la separación final). */
uint16_t font_text_width(const font_t *f, const char *s, uint8_t scale);

#endif
