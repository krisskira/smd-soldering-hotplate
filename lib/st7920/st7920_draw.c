/*
 * ST7920 - Dibujo sin framebuffer completo.
 * Lista de comandos (dibujo diferido) + buffer de una fila (16 bytes).
 * st7920_render() interpreta los comandos y envía fila a fila al LCD.
 * RAM: ~16 (fila) + 24*6 = 144 (comandos) = 160 bytes vs 1024 del framebuffer.
 */
#include "st7920.h"
#include "st7920_private.h"
#include "avr_delay/avr_delay.h"
#include <avr/pgmspace.h>
#include <util/delay.h>
#include <stdint.h>

#define LCD_WIDTH  128
#define LCD_HEIGHT 64

#define CMD_LINE        0
#define CMD_RECT        1
#define CMD_TEXT        2
#define CMD_PROGRESSBAR 3
#define CMD_PIXEL       4
#define CMD_BITMAP      5

#define CMD_SIZE        7   /* tipo (1) + 6 params (bitmap necesita x,y,w,h,ptr_lo,ptr_hi) */
#define CMD_MAX         24

/* Lista de comandos */
static uint8_t cmd_buf[CMD_MAX * CMD_SIZE];
static uint8_t cmd_count;

/* Buffer de una fila: 8 bloques × 16 bits */
static uint16_t row_buf[8];

void st7920_row_set_pixel(uint16_t *row_buf, uint8_t x)
{
    if (x >= LCD_WIDTH)
        return;
    uint8_t block = x / 16;
    uint8_t bit  = 15 - (x % 16);
    row_buf[block] |= (uint16_t)(1 << bit);
}

void st7920_clear_gdram_buffer(void)
{
    cmd_count = 0;
}

void st7920_clear_commands(void)
{
    cmd_count = 0;
}

static uint8_t push_cmd(uint8_t type, const uint8_t *params)
{
    if (cmd_count >= CMD_MAX)
        return 0;
    uint8_t *p = &cmd_buf[cmd_count * CMD_SIZE];
    *p++ = type;
    for (uint8_t i = 0; i < 6; i++)
        *p++ = params[i];
    cmd_count++;
    return 1;
}

void st7920_draw_pixel(uint8_t x, uint8_t y)
{
    uint8_t params[6] = { x, y, 0, 0, 0, 0 };
    push_cmd(CMD_PIXEL, params);
}

static void add_line_to_row(uint16_t *row, uint8_t row_y,
                            int16_t x0, int16_t y0, int16_t x1, int16_t y1)
{
    int16_t dx = (x1 >= x0) ? (x1 - x0) : (x0 - x1);
    int16_t sx = (x0 < x1) ? 1 : -1;
    int16_t dy = (y1 >= y0) ? (y1 - y0) : (y0 - y1);
    int16_t sy = (y0 < y1) ? 1 : -1;
    int16_t err = dx - dy;
    int16_t px = x0, py = y0;

    for (;;)
    {
        if (py == (int16_t)row_y)
            st7920_row_set_pixel(row, (uint8_t)px);
        if (px == x1 && py == y1)
            break;
        int16_t e2 = (int16_t)(2 * err);
        if (e2 > -dy)
        {
            err -= dy;
            px += sx;
        }
        if (e2 < dx)
        {
            err += dx;
            py += sy;
        }
    }
}

static void add_rect_to_row(uint16_t *row, uint8_t row_y,
                            uint8_t x, uint8_t y, uint8_t w, uint8_t h,
                            uint8_t fill_percent)
{
    uint8_t y0 = y, y1 = y + h;
    if (row_y < y0 || row_y > y1)
        return;

    if (fill_percent == 0)
    {
        /* Solo borde */
        if (row_y == y0 || row_y == y1)
        {
            for (uint8_t i = 0; i <= w; i++)
                st7920_row_set_pixel(row, x + i);
        }
        else
        {
            st7920_row_set_pixel(row, x);
            st7920_row_set_pixel(row, x + w);
        }
        return;
    }

    /* Rectángulo relleno (progressbar): borde + relleno hasta fill */
    uint8_t fill = (w * fill_percent) / 100;
    if (fill > w)
        fill = w;

    if (row_y == y0 || row_y == y1)
    {
        for (uint8_t i = 0; i <= w; i++)
            st7920_row_set_pixel(row, x + i);
    }
    else
    {
        st7920_row_set_pixel(row, x);
        st7920_row_set_pixel(row, x + w);
        for (uint8_t i = 1; i < fill; i++)
            st7920_row_set_pixel(row, x + i);
    }
}

void st7920_draw_line(uint8_t x0, uint8_t y0, uint8_t x1, uint8_t y1)
{
    uint8_t params[6] = { x0, y0, x1, y1, 0, 0 };
    push_cmd(CMD_LINE, params);
}

void st7920_draw_rect(uint8_t x, uint8_t y, uint8_t w, uint8_t h)
{
    uint8_t params[6] = { x, y, w, h, 0, 0 };
    push_cmd(CMD_RECT, params);
}

void st7920_draw_progressbar(uint8_t x, uint8_t y, uint8_t w, uint8_t h,
                             uint8_t percent)
{
    if (percent > 100)
        percent = 100;
    uint8_t params[6] = { x, y, w, h, (uint8_t)percent, 0 };
    push_cmd(CMD_PROGRESSBAR, params);
}

void st7920_draw_text(uint8_t x, uint8_t y, const char *str)
{
    uint8_t params[6];
    params[0] = x;
    params[1] = y;
    *(uint16_t *)(params + 2) = (uint16_t)(uintptr_t)str;
    params[4] = 0;
    params[5] = 0;
    push_cmd(CMD_TEXT, params);
}

void st7920_draw_text_gdram(uint8_t x, uint8_t y, const char *str)
{
    if (!str)
        return;
    /* Fuente 5x7: 7 filas de píxel. Escribir solo esas filas en GDRAM. */
    for (uint8_t row_y = y; row_y < y + 7u && row_y < LCD_HEIGHT; row_y++)
    {
        for (uint8_t b = 0; b < 8u; b++)
            row_buf[b] = 0u;
        st7920_text_fill_row(row_buf, row_y, x, y, str);
        for (uint8_t block = 0; block < 8u; block++)
            st7920_write_gdram(block, row_y,
                              (uint8_t)(row_buf[block] >> 8),
                              (uint8_t)(row_buf[block] & 0xFFu));
    }
}

static void add_bitmap_to_row(uint16_t *row, uint8_t row_y,
                              uint8_t bx, uint8_t by, uint8_t bw, uint8_t bh,
                              const uint8_t *data)
{
    if (row_y < by || row_y >= by + bh || !data)
        return;
    uint8_t local_y = row_y - by;
    uint8_t row_bytes = (bw + 7) / 8;
    const uint8_t *row_data = data + (uint16_t)local_y * row_bytes;
    for (uint8_t cx = 0; cx < bw; cx++)
    {
        uint8_t byte_idx = cx / 8;
        uint8_t bit_idx = 7 - (cx % 8);
        if (row_data[byte_idx] & (1u << bit_idx))
            st7920_row_set_pixel(row, bx + cx);
    }
}

void st7920_draw_bitmap(uint8_t x, uint8_t y, uint8_t w, uint8_t h, const uint8_t *data)
{
    if (!data)
        return;
    uint8_t params[6];
    params[0] = x;
    params[1] = y;
    params[2] = w;
    params[3] = h;
    *(uint16_t *)(params + 4) = (uint16_t)(uintptr_t)data;
    push_cmd(CMD_BITMAP, params);
}

void st7920_render(void)
{
    st7920_clear_gdram();

    for (uint8_t y = 0; y < LCD_HEIGHT; y++)
    {
        for (uint8_t b = 0; b < 8; b++)
            row_buf[b] = 0;

        for (uint8_t n = 0; n < cmd_count; n++)
        {
            uint8_t *c = &cmd_buf[n * CMD_SIZE];
            uint8_t type = c[0];

            if (type == CMD_LINE)
                add_line_to_row(row_buf, y,
                                (int16_t)c[1], (int16_t)c[2],
                                (int16_t)c[3], (int16_t)c[4]);
            else if (type == CMD_RECT)
                add_rect_to_row(row_buf, y, c[1], c[2], c[3], c[4], 0);
            else if (type == CMD_PROGRESSBAR)
                add_rect_to_row(row_buf, y, c[1], c[2], c[3], c[4], c[5]);
            else if (type == CMD_TEXT)
                st7920_text_fill_row(row_buf, y, c[1], c[2],
                                    (const char *)(uintptr_t)(c[3] | (c[4] << 8)));
            else if (type == CMD_PIXEL && c[2] == y)
                st7920_row_set_pixel(row_buf, c[1]);
            else if (type == CMD_BITMAP)
                add_bitmap_to_row(row_buf, y, c[1], c[2], c[3], c[4],
                                  (const uint8_t *)(uintptr_t)(c[5] | (c[6] << 8)));
        }

        for (uint8_t block = 0; block < 8; block++)
            st7920_write_gdram(block, y,
                              (uint8_t)(row_buf[block] >> 8),
                              (uint8_t)(row_buf[block] & 0xFF));
    }
}

/* Escribe frame completo en GDRAM por bloques (2 bytes = 16 píxeles por bloque). */
void st7920_write_frame(uint8_t base_x, uint8_t base_y, const uint8_t *data,
                             uint8_t width, uint8_t height, uint8_t bytes_per_row)
{
    if (!data)
        return;
    uint8_t num_blocks = (bytes_per_row + 1u) / 2u;
    uint8_t block_base = (uint8_t)(base_x / 16u);
    for (uint8_t row = 0; row < height; row++)
    {
        uint16_t row_off = (uint16_t)row * bytes_per_row;
        for (uint8_t b = 0; b < num_blocks; b++)
        {
            uint8_t left  = data[row_off + (uint16_t)b * 2u];
            uint8_t right = (b * 2u + 1u < bytes_per_row)
                ? data[row_off + (uint16_t)b * 2u + 1u]
                : 0u;
            st7920_write_gdram(block_base + b, base_y + row, left, right);
        }
    }
}

void st7920_write_frame_pgm(uint8_t base_x, uint8_t base_y, const uint8_t *data_pgm,
                                 uint8_t width, uint8_t height, uint8_t bytes_per_row)
{
    if (!data_pgm)
        return;
    uint8_t num_blocks = (bytes_per_row + 1u) / 2u;
    uint8_t block_base = (uint8_t)(base_x / 16u);
    for (uint8_t row = 0; row < height; row++)
    {
        uint16_t row_off = (uint16_t)row * bytes_per_row;
        for (uint8_t b = 0; b < num_blocks; b++)
        {
            uint8_t left  = pgm_read_byte(data_pgm + row_off + (uint16_t)b * 2u);
            uint8_t right = (b * 2u + 1u < bytes_per_row)
                ? pgm_read_byte(data_pgm + row_off + (uint16_t)b * 2u + 1u)
                : 0u;
            st7920_write_gdram(block_base + b, base_y + row, left, right);
        }
    }
}

/* ST7920 GDRAM: 16 columnas (bloques de 16 px), 32 filas (2 px por fila). */
void st7920_clear_region(uint8_t x, uint8_t y, uint8_t w, uint8_t h)
{
    if (w == 0u || h == 0u)
        return;

    uint8_t block_lo = (uint8_t)(x / 16u);
    uint8_t block_hi = (uint8_t)((uint16_t)(x + w - 1u) / 16u);
    uint8_t row_lo   = (uint8_t)(y / 2u);
    uint8_t row_hi   = (uint8_t)((uint16_t)(y + h - 1u) / 2u);

    if (block_hi > 15u)
        block_hi = 15u;
    if (row_hi > 31u)
        row_hi = 31u;

    for (uint8_t row = row_lo; row <= row_hi; row++)
    {
        for (uint8_t block = block_lo; block <= block_hi; block++)
            st7920_write_gdram(block, row, 0u, 0u);
    }
}

void st7920_draw_region_pgm(uint8_t x, uint8_t y, const uint8_t *bitmap_pgm,
                                uint8_t w, uint8_t h)
{
    if (!bitmap_pgm || w == 0u || h == 0u)
        return;
    uint8_t bytes_per_row = (uint8_t)((w + 7u) / 8u);
    uint8_t num_rows = (uint8_t)((h + 1u) / 2u);
    st7920_write_frame_pgm(x, y, bitmap_pgm, w, num_rows, bytes_per_row);
}

void st7920_apply_diff(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
    uint16_t bytes_per_row, const uint16_t *offsets,
    const uint8_t *values, uint16_t count)
{
    if (!buffer || !offsets || !values)
        return;
    for (uint16_t i = 0; i < count; i++)
    {
        uint16_t off = offsets[i];
        uint8_t val = values[i];
        buffer[off] = val;
        uint8_t row      = (uint8_t)(off / bytes_per_row);
        uint8_t col_byte = (uint8_t)(off % bytes_per_row);
        uint8_t block_x  = (uint8_t)((base_x + (uint16_t)col_byte * 8u) / 16u);
        uint8_t left, right;
        if ((col_byte & 1u) == 0u)
        {
            left  = val;
            right = (col_byte + 1u < bytes_per_row) ? buffer[off + 1] : 0u;
        }
        else
        {
            left  = buffer[off - 1];
            right = val;
        }
        st7920_write_gdram(block_x, base_y + row, left, right);
    }
}

void st7920_apply_diff_pgm(uint8_t base_x, uint8_t base_y, uint8_t *buffer,
                                uint16_t bytes_per_row, const uint16_t *offsets_pgm,
                                const uint8_t *values_pgm, uint16_t count)
{
    if (!buffer || !offsets_pgm || !values_pgm)
        return;
    for (uint16_t i = 0; i < count; i++)
    {
        uint16_t off = pgm_read_word(offsets_pgm + i);
        uint8_t val  = pgm_read_byte(values_pgm + i);
        buffer[off] = val;
        uint8_t row      = (uint8_t)(off / bytes_per_row);
        uint8_t col_byte = (uint8_t)(off % bytes_per_row);
        uint8_t block_x  = (uint8_t)((base_x + (uint16_t)col_byte * 8u) / 16u);
        uint8_t left, right;
        if ((col_byte & 1u) == 0u)
        {
            left  = val;
            right = (col_byte + 1u < bytes_per_row) ? buffer[off + 1] : 0u;
        }
        else
        {
            left  = buffer[off - 1];
            right = val;
        }
        st7920_write_gdram(block_x, base_y + row, left, right);
    }
}

void st7920_draw_animation(uint8_t x, uint8_t y,
    const st7920_animation_t *anim, uint8_t *buffer, uint16_t delay_ms)
{
    if (!anim || !buffer || anim->frame_count < 1u)
        return;

    st7920_write_frame_pgm(x, y, anim->frame_0_pgm, anim->width, anim->height,
                            anim->bytes_per_row);

    for (uint16_t i = 0; i < anim->bytes_per_frame; i++)
        buffer[i] = pgm_read_byte(anim->frame_0_pgm + i);

    uint16_t frame_idx = 1u;
    for (;;)
    {
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

/* Máquina de estados: una sola función run hace start la primera vez (ctx inactivo)
 * y tick en adelante. Así el main solo llama run (o run_all) en el loop. */

void st7920_animation_run(st7920_animation_ctx_t *ctx, uint8_t x, uint8_t y,
    const st7920_animation_t *anim, uint8_t *buffer, uint16_t interval_ms)
{
    if (!ctx)
        return;

    if (!ctx->active)
    {
        /* Estado: parado → si tenemos anim y buffer, iniciar (start). */
        if (!anim || !buffer || anim->frame_count < 1u)
            return;

        st7920_write_frame_pgm(x, y, anim->frame_0_pgm, anim->width, anim->height,
                                anim->bytes_per_row);

        for (uint16_t i = 0; i < anim->bytes_per_frame; i++)
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

    /* Estado: activo → tick (aplicar siguiente diff si ha pasado interval_ms). */
    uint16_t now = delay_ms();
    if ((uint16_t)(now - ctx->last_tick_ms) < ctx->interval_ms)
        return;

    anim = ctx->anim;
    const uint16_t *offsets_pgm = (const uint16_t *)(uint16_t)pgm_read_word(
        (const uint16_t *)anim->diff_offsets_pgm + (ctx->frame_idx - 1u));
    const uint8_t *values_pgm = (const uint8_t *)(uint16_t)pgm_read_word(
        (const uint16_t *)anim->diff_values_pgm + (ctx->frame_idx - 1u));
    uint16_t count = pgm_read_word(anim->diff_counts_pgm + (ctx->frame_idx - 1u));

    st7920_apply_diff_pgm(ctx->x, ctx->y, ctx->buffer, anim->bytes_per_row,
                          offsets_pgm, values_pgm, count);

    ctx->frame_idx++;
    if (ctx->frame_idx >= anim->frame_count)
        ctx->frame_idx = 1u;
    ctx->last_tick_ms = now;
}

void st7920_animation_run_all(const st7920_animation_slot_t *slots, uint8_t count)
{
    if (!slots)
        return;
    for (uint8_t i = 0; i < count; i++)
        st7920_animation_run(slots[i].ctx, slots[i].x, slots[i].y,
                             slots[i].anim, slots[i].buffer, slots[i].interval_ms);
}
