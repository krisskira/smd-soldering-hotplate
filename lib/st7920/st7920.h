#ifndef ST7920_H
#define ST7920_H

#include <avr/io.h>
#include <stdint.h>
#include "fonts/font.h"

/* --- Configuración (st7920_config.c) --- */
void st7920_init(void);
void st7920_cmd(uint8_t cmd);
void st7920_data(uint8_t data);
void st7920_clear(void);
void st7920_graphics_mode(void);
void st7920_goto(uint8_t x, uint8_t y);
void st7920_print(const char *str);

/* --- Dibujo (st7920_draw.c). Acumulan comandos; llamar st7920_render() al final. --- */
void st7920_draw_pixel(uint8_t x, uint8_t y);
void st7920_draw_line(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1);
void st7920_draw_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h);
void st7920_draw_progressbar(uint8_t x, uint8_t y, uint8_t w, uint8_t h,
                             uint8_t percent);
void st7920_draw_text(uint8_t x, uint8_t y, const char *str);

/*
 * Texto directo en GDRAM (5×7). Reescribe desde el bloque de 16 px que
 * contiene x hasta el borde derecho: lo que está a la izquierda (p. ej. un
 * icono) no se toca. El LCD no se puede leer, así que un bitmap y un texto
 * no deben compartir bloque. Para fondos a todo el ancho con texto centrado
 * usar st7920_draw_band.
 */

/** Escribe texto directamente en GDRAM (sin lista de comandos). Para actualizar texto en el loop
 * sin llamar a st7920_render() (que borra toda la pantalla). */
void st7920_draw_text_gdram(uint8_t x, uint8_t y, const char *str);

/** Texto invertido en GDRAM (fondo ON). y = borde superior de la barra,
 * h = alto de la barra (p.ej. 9–15); texto 5x7 centrado en vertical. */
void st7920_draw_text_gdram_inv(uint8_t x, uint8_t y, uint8_t h, const char *str);

/**
 * Texto GDRAM con escala 1..3 y flags:
 * bit0 = invertido, bit1 = negrita (doble trazo horizontal).
 * h = alto de banda a reescribir (recomendado: 8 * scale).
 */
#define ST7920_TEXT_INV   0x01u
#define ST7920_TEXT_BOLD  0x02u
void st7920_draw_text_gdram_styled(uint8_t x, uint8_t y, uint8_t h,
                                   const char *str, uint8_t scale,
                                   uint8_t flags);

/**
 * Texto con cualquier fuente de lib/fonts (FONT_5X7, FONT_6X8_BOLD,
 * FONT_8X12, FONT_ICONS). Escala 1..3.
 * y = borde superior de la banda; h = alto de banda (0 = alto del glifo).
 * El glifo va centrado en vertical dentro de la banda. inv = fondo ON.
 */
void st7920_draw_font_gdram(const font_t *f, uint8_t x, uint8_t y, uint8_t h,
                            const char *str, uint8_t scale, uint8_t inv);

/** Una pieza dentro de una banda. Se centra en vertical según su fuente. */
typedef struct {
    const font_t *f;
    const char *str;
    uint8_t x;
    uint8_t scale;
    uint8_t bold; /* reservado; la negrita sintética se quitó por flash */
} st7920_span_t;

/**
 * Reescribe el rectángulo [x, x+w) × [y, y+h) con el fondo (inv = ON) y las
 * piezas encima. x y w se redondean a bloques de 16 px; lo que queda fuera
 * del rectángulo no se toca. Cada elemento de pantalla debe tener su banda.
 */
void st7920_draw_band(uint8_t x, uint8_t w, uint8_t y, uint8_t h,
                      const st7920_span_t *spans, uint8_t n, uint8_t inv);

/* Carga y dibuja un mapa de bits en (x,y), tamaño w×h. data: por filas, 1 bit/píxel, (w+7)/8 bytes por fila, MSB = izquierda. */
void st7920_draw_bitmap(uint8_t x, uint8_t y, uint8_t w, uint8_t h, const uint8_t *data);

/* Vacía la lista de comandos de dibujo (para redibujar solo el contenido deseado, p. ej. animación frame a frame). */
void st7920_clear_commands(void);

void st7920_render(void);

/* Bitmap en PROGMEM. Lo usa el icono USB. El reproductor de animaciones
 * (diffs, run/run_all) está en features/parked/ y no se enlaza. */
void st7920_write_frame_pgm(uint8_t base_x, uint8_t base_y, const uint8_t *data_pgm,
                                 uint8_t width, uint8_t height, uint8_t bytes_per_row);

/* Borra una región rectangular en GDRAM (escribe 0). Coordenadas en píxeles (0..127 x, 0..63 y).
 * Se redondea a bloques completos del ST7920 (16 px ancho × 2 px alto). */
void st7920_clear_region(uint8_t x, uint8_t y, uint8_t w, uint8_t h);

void st7920_disable(void);
void st7920_enable(void);

#endif
