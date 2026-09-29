/*
 * Reproductor de animaciones ST7920. No entra al firmware de producto.
 * Para enlazarlo (p. ej. la vista de gráfico de pid_atune), añadir este
 * .c al Makefile. Guía: doc/st7920_pantalla.md.
 * El icono USB sigue usando st7920_write_frame_pgm.
 */
#ifndef ST7920_ANIMATION_H
#define ST7920_ANIMATION_H

#include <stdint.h>

void st7920_apply_diff(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                       uint16_t bytes_per_row, const uint16_t *offsets,
                       const uint8_t *values, uint16_t count);

void st7920_write_frame(uint8_t base_x, uint8_t base_y, const uint8_t *data,
                        uint8_t width, uint8_t height, uint8_t bytes_per_row);

void st7920_draw_region_pgm(uint8_t x, uint8_t y, const uint8_t *bitmap_pgm,
                            uint8_t w, uint8_t h);

void st7920_apply_diff_pgm(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                           uint16_t bytes_per_row, const uint16_t *offsets_pgm,
                           const uint8_t *values_pgm, uint16_t count);

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

void st7920_draw_animation(uint8_t x, uint8_t y,
                           const st7920_animation_t *anim, uint8_t *buffer,
                           uint16_t delay_ms);

typedef struct {
    const st7920_animation_t *anim;
    uint8_t *buffer;
    uint8_t x, y;
    uint16_t frame_idx;
    uint16_t last_tick_ms;
    uint16_t interval_ms;
    uint8_t active;
} st7920_animation_ctx_t;

typedef struct {
    st7920_animation_ctx_t *ctx;
    uint8_t x, y;
    const st7920_animation_t *anim;
    uint8_t *buffer;
    uint16_t interval_ms;
} st7920_animation_slot_t;

void st7920_animation_run(st7920_animation_ctx_t *ctx, uint8_t x, uint8_t y,
                          const st7920_animation_t *anim, uint8_t *buffer,
                          uint16_t interval_ms);

void st7920_animation_run_all(const st7920_animation_slot_t *slots, uint8_t count);

#endif
