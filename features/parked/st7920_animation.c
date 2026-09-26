/*
 * Reproductor de frames por diff. Documentado en
 * doc/animaciones_no_bloqueantes.md. No forma parte del enlace.
 */
#include "st7920_animation.h"
#include "st7920/st7920.h"
#include "st7920/st7920_private.h"
#include "avr_delay/avr_delay.h"

#include <avr/pgmspace.h>
#include <util/delay.h>

void st7920_write_frame(uint8_t base_x, uint8_t base_y, const uint8_t *data,
                        uint8_t width, uint8_t height, uint8_t bytes_per_row)
{
    uint8_t num_blocks;
    uint8_t block_base;
    uint8_t row;
    uint8_t b;

    if (!data)
        return;
    num_blocks = (uint8_t)((bytes_per_row + 1u) / 2u);
    block_base = (uint8_t)(base_x / 16u);
    for (row = 0; row < height; row++) {
        uint16_t row_off = (uint16_t)row * bytes_per_row;
        for (b = 0; b < num_blocks; b++) {
            uint8_t left = data[row_off + (uint16_t)b * 2u];
            uint8_t right = (b * 2u + 1u < bytes_per_row)
                ? data[row_off + (uint16_t)b * 2u + 1u]
                : 0u;
            st7920_write_gdram(block_base + b, base_y + row, left, right);
        }
    }
}

void st7920_draw_region_pgm(uint8_t x, uint8_t y, const uint8_t *bitmap_pgm,
                            uint8_t w, uint8_t h)
{
    uint8_t bytes_per_row;
    uint8_t num_rows;

    if (!bitmap_pgm || w == 0u || h == 0u)
        return;
    bytes_per_row = (uint8_t)((w + 7u) / 8u);
    num_rows = (uint8_t)((h + 1u) / 2u);
    st7920_write_frame_pgm(x, y, bitmap_pgm, w, num_rows, bytes_per_row);
}

void st7920_apply_diff(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                       uint16_t bytes_per_row, const uint16_t *offsets,
                       const uint8_t *values, uint16_t count)
{
    uint16_t i;

    if (!buffer || !offsets || !values)
        return;
    for (i = 0; i < count; i++) {
        uint16_t off = offsets[i];
        uint8_t val = values[i];
        uint8_t row = (uint8_t)(off / bytes_per_row);
        uint8_t col_byte = (uint8_t)(off % bytes_per_row);
        uint8_t block_x = (uint8_t)((base_x + (uint16_t)col_byte * 8u) / 16u);
        uint8_t left, right;

        buffer[off] = val;
        if ((col_byte & 1u) == 0u) {
            left = val;
            right = (col_byte + 1u < bytes_per_row) ? buffer[off + 1] : 0u;
        } else {
            left = buffer[off - 1];
            right = val;
        }
        st7920_write_gdram(block_x, base_y + row, left, right);
    }
}

void st7920_apply_diff_pgm(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                           uint16_t bytes_per_row, const uint16_t *offsets_pgm,
                           const uint8_t *values_pgm, uint16_t count)
{
    uint16_t i;

    if (!buffer || !offsets_pgm || !values_pgm)
        return;
    for (i = 0; i < count; i++) {
        uint16_t off = pgm_read_word(offsets_pgm + i);
        uint8_t val = pgm_read_byte(values_pgm + i);
        uint8_t row = (uint8_t)(off / bytes_per_row);
        uint8_t col_byte = (uint8_t)(off % bytes_per_row);
        uint8_t block_x = (uint8_t)((base_x + (uint16_t)col_byte * 8u) / 16u);
        uint8_t left, right;

        buffer[off] = val;
        if ((col_byte & 1u) == 0u) {
            left = val;
            right = (col_byte + 1u < bytes_per_row) ? buffer[off + 1] : 0u;
        } else {
            left = buffer[off - 1];
            right = val;
        }
        st7920_write_gdram(block_x, base_y + row, left, right);
    }
}

void st7920_draw_animation(uint8_t x, uint8_t y,
                           const st7920_animation_t *anim, uint8_t *buffer,
                           uint16_t delay_ms)
{
    uint16_t i;
    uint16_t frame_idx;

    if (!anim || !buffer || anim->frame_count < 1u)
        return;

    st7920_write_frame_pgm(x, y, anim->frame_0_pgm, anim->width, anim->height,
                           anim->bytes_per_row);
    for (i = 0; i < anim->bytes_per_frame; i++)
        buffer[i] = pgm_read_byte(anim->frame_0_pgm + i);

    frame_idx = 1u;
    for (;;) {
        const uint16_t *offsets_pgm = (const uint16_t *)(uint16_t)pgm_read_word(
            (const uint16_t *)anim->diff_offsets_pgm + (frame_idx - 1u));
        const uint8_t *values_pgm = (const uint8_t *)(uint16_t)pgm_read_word(
            (const uint16_t *)anim->diff_values_pgm + (frame_idx - 1u));
        uint16_t count = pgm_read_word(anim->diff_counts_pgm + (frame_idx - 1u));

        st7920_apply_diff_pgm(x, y, buffer, anim->bytes_per_row,
                              offsets_pgm, values_pgm, count);
        frame_idx++;
        if (frame_idx >= anim->frame_count)
            frame_idx = 1u;
        _delay_ms(delay_ms);
    }
}

void st7920_animation_run(st7920_animation_ctx_t *ctx, uint8_t x, uint8_t y,
                          const st7920_animation_t *anim, uint8_t *buffer,
                          uint16_t interval_ms)
{
    uint16_t i;
    uint16_t now;

    if (!ctx)
        return;

    if (!ctx->active) {
        if (!anim || !buffer || anim->frame_count < 1u)
            return;
        st7920_write_frame_pgm(x, y, anim->frame_0_pgm, anim->width, anim->height,
                               anim->bytes_per_row);
        for (i = 0; i < anim->bytes_per_frame; i++)
            buffer[i] = pgm_read_byte(anim->frame_0_pgm + i);
        ctx->anim = anim;
        ctx->buffer = buffer;
        ctx->x = x;
        ctx->y = y;
        ctx->frame_idx = 1u;
        ctx->last_tick_ms = delay_ms();
        ctx->interval_ms = interval_ms;
        ctx->active = 1;
        return;
    }

    now = delay_ms();
    if ((uint16_t)(now - ctx->last_tick_ms) < ctx->interval_ms)
        return;

    anim = ctx->anim;
    {
        const uint16_t *offsets_pgm = (const uint16_t *)(uint16_t)pgm_read_word(
            (const uint16_t *)anim->diff_offsets_pgm + (ctx->frame_idx - 1u));
        const uint8_t *values_pgm = (const uint8_t *)(uint16_t)pgm_read_word(
            (const uint16_t *)anim->diff_values_pgm + (ctx->frame_idx - 1u));
        uint16_t count = pgm_read_word(anim->diff_counts_pgm + (ctx->frame_idx - 1u));

        st7920_apply_diff_pgm(ctx->x, ctx->y, ctx->buffer, anim->bytes_per_row,
                              offsets_pgm, values_pgm, count);
    }
    ctx->frame_idx++;
    if (ctx->frame_idx >= anim->frame_count)
        ctx->frame_idx = 1u;
    ctx->last_tick_ms = now;
}

void st7920_animation_run_all(const st7920_animation_slot_t *slots, uint8_t count)
{
    uint8_t i;

    if (!slots)
        return;
    for (i = 0; i < count; i++)
        st7920_animation_run(slots[i].ctx, slots[i].x, slots[i].y,
                             slots[i].anim, slots[i].buffer, slots[i].interval_ms);
}
