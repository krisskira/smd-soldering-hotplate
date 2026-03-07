#define F_CPU 4000000UL

#include <avr/io.h>
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"
#include "lib/avr_delay/avr_delay.h"
#include "icons/animated/plot.c"
#include "icons/animated/temperature.c"


static const st7920_animation_t plot_anim = {
    .frame_0_pgm       = plot_frame_0,
    .diff_offsets_pgm  = plot_diff_offsets,
    .diff_values_pgm   = plot_diff_values,
    .diff_counts_pgm   = plot_diff_counts,
    .width             = PLOT_FRAME_WIDTH,
    .height            = PLOT_FRAME_HEIGHT,
    .bytes_per_row     = PLOT_BYTES_PER_ROW,
    .bytes_per_frame   = PLOT_BYTES_PER_FRAME,
    .frame_count       = PLOT_FRAME_COUNT,
};

static const st7920_animation_t temperature_anim = {
    .frame_0_pgm       = temperature_frame_0,
    .diff_offsets_pgm  = temperature_diff_offsets,
    .diff_values_pgm   = temperature_diff_values,
    .diff_counts_pgm   = temperature_diff_counts,
    .width             = TEMPERATURE_FRAME_WIDTH,
    .height            = TEMPERATURE_FRAME_HEIGHT,
    .bytes_per_row     = TEMPERATURE_BYTES_PER_ROW,
    .bytes_per_frame   = TEMPERATURE_BYTES_PER_FRAME,
    .frame_count       = TEMPERATURE_FRAME_COUNT,
};

int main(void)
{
    avr_spi_master_init(SPI_DIV_4);
    st7920_init();
    st7920_graphics_mode();
    delay_init();

    const uint8_t icono[] PROGMEM = {
        0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
    };

    static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];
    static uint8_t temperature_buffer[TEMPERATURE_BYTES_PER_FRAME];

    static st7920_animation_ctx_t plot_ctx;
    static st7920_animation_ctx_t temperature_ctx;

    st7920_clear_commands();
    st7920_draw_rect(0, 0, 12, 12);
    st7920_draw_bitmap(2, 2, 8, 8, icono);
    st7920_draw_rect(46, 14, 34, 34);
    st7920_draw_text(0, 57, "Hello");
    st7920_render();

    st7920_animation_start(&plot_ctx, 2, 16, &plot_anim, plot_buffer, 100);
    st7920_animation_start(&temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100);

    while (1) 
    {
        st7920_animation_tick(&plot_ctx);
        st7920_animation_tick(&temperature_ctx);
    }
}
