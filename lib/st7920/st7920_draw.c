/*
 * ST7920 - Dibujo sin framebuffer completo.
 * Lista de comandos (dibujo diferido) + buffer de una fila (16 bytes).
 * st7920_render() interpreta los comandos y envía fila a fila al LCD.
 * RAM: ~16 (fila) + 24*6 = 144 (comandos) = 160 bytes vs 1024 del framebuffer.
 */
#include "st7920.h"
#include "st7920_private.h"
#include <avr/pgmspace.h>
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
#define CMD_MAX         8   /* frame: clear+rect+title; filas van por GDRAM directo */

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

void st7920_row_clear_pixel(uint16_t *row_buf, uint8_t x)
{
    if (x >= LCD_WIDTH)
        return;
    uint8_t block = x / 16;
    uint8_t bit  = 15 - (x % 16);
    row_buf[block] &= (uint16_t)~(1u << bit);
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

void st7920_draw_text_gdram_styled(uint8_t x, uint8_t y, uint8_t h,
                                   const char *str, uint8_t scale,
                                   uint8_t flags)
{
    st7920_span_t s;
    uint8_t bx = (uint8_t)(x & 0xF0u);

    s.f = &FONT_5X7;
    s.str = str;
    s.x = x;
    s.scale = scale;
    s.bold = (uint8_t)((flags & ST7920_TEXT_BOLD) ? 1u : 0u);
    st7920_draw_band(bx, (uint8_t)(LCD_WIDTH - bx), y, h, &s, 1u,
                     (uint8_t)((flags & ST7920_TEXT_INV) ? 1u : 0u));
}

void st7920_draw_text_gdram(uint8_t x, uint8_t y, const char *str)
{
    st7920_draw_text_gdram_styled(x, y, 8u, str, 1u, 0u);
}

void st7920_draw_text_gdram_inv(uint8_t x, uint8_t y, uint8_t h, const char *str)
{
    st7920_draw_text_gdram_styled(x, y, h, str, 1u, ST7920_TEXT_INV);
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
                st7920_font_row(row_buf, y, &FONT_5X7, c[1], c[2],
                                (const char *)(uintptr_t)(c[3] | (c[4] << 8)),
                                1u, 0u);
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

void st7920_clear_region(uint8_t x, uint8_t y, uint8_t w, uint8_t h)
{
    uint8_t block_lo;
    uint8_t block_hi;
    uint8_t py;
    uint8_t b;
    uint8_t y_end;

    if (w == 0u || h == 0u)
        return;

    block_lo = (uint8_t)(x / 16u);
    block_hi = (uint8_t)((uint16_t)(x + w - 1u) / 16u);
    if (block_hi > 7u)
        block_hi = 7u;

    y_end = (uint8_t)(y + h);
    if (y_end > 64u)
        y_end = 64u;

    for (py = y; py < y_end; py++) {
        for (b = block_lo; b <= block_hi; b++)
            st7920_write_gdram(b, py, 0u, 0u);
    }
}
