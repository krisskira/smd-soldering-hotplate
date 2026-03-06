#ifndef ST7920_H
#define ST7920_H

#include <avr/io.h>
#include <stdint.h>

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

/* Carga y dibuja un mapa de bits en (x,y), tamaño w×h. data: por filas, 1 bit/píxel, (w+7)/8 bytes por fila, MSB = izquierda. */
void st7920_draw_bitmap(uint8_t x, uint8_t y, uint8_t w, uint8_t h, const uint8_t *data);

/* Vacía la lista de comandos de dibujo (para redibujar solo el contenido deseado, p. ej. animación frame a frame). */
void st7920_clear_commands(void);

void st7920_render(void);

/* Animación por diff: actualiza buffer con (offsets[], values[]) y escribe solo los bloques modificados en GDRAM.
 * buffer: buffer fila-major, bytes_per_row (ej. 7 para 50px). No borra la pantalla. */
void st7920_apply_diff(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                            uint16_t bytes_per_row, const uint16_t *offsets,
                            const uint8_t *values, uint16_t count);

/* Escribe un frame completo en GDRAM (por filas/bloques). No borra la pantalla. */
void st7920_write_frame(uint8_t base_x, uint8_t base_y, const uint8_t *data,
                             uint8_t width, uint8_t height, uint8_t bytes_per_row);

/* Igual que plot_write_frame pero data está en PROGMEM. */
void st7920_write_frame_pgm(uint8_t base_x, uint8_t base_y, const uint8_t *data_pgm,
                                 uint8_t width, uint8_t height, uint8_t bytes_per_row);

/* Igual que plot_apply_diff pero offsets y values están en PROGMEM. */
void st7920_apply_diff_pgm(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                                uint16_t bytes_per_row, const uint16_t *offsets_pgm,
                                const uint8_t *values_pgm, uint16_t count);

/* Descriptor de animación: frame 0 en PROGMEM + tablas de diffs por frame.
 * diff_offsets_pgm / diff_values_pgm: dirección del primer elemento del array
 * de punteros en PROGMEM (índice 0 = frame 1). diff_counts_pgm: array de
 * uint16_t en PROGMEM. */
typedef struct {
    const uint8_t *frame_0_pgm;
    const void *diff_offsets_pgm;
    const void *diff_values_pgm;
    const uint16_t *diff_counts_pgm;
    uint8_t width;
    uint8_t height;
    uint8_t bytes_per_row;
    uint16_t bytes_per_frame;
    uint16_t frame_count;
} st7920_animation_t;

/* Ejecuta la animación en (x,y): escribe frame 0, luego aplica diffs 1..N-1
 * en bucle. buffer debe tener al menos anim->bytes_per_frame bytes. */
void st7920_draw_animation(uint8_t x, uint8_t y,
    const st7920_animation_t *anim, uint8_t *buffer, uint16_t delay_ms);

#endif
