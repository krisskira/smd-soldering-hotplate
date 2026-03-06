#define F_CPU 4000000UL

#include <avr/io.h>
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"
#include "icons/plot/plot_diff.c"

/* Base (0,0) para que los bloques GDRAM coincidan con la imagen (múltiplo de 16 en X). */
#define PLOT_BASE_X  48
#define PLOT_BASE_Y  16

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

int main(void)
{
    avr_spi_master_init(SPI_DIV_4);
    st7920_init();
    st7920_graphics_mode();

    const uint8_t icono[] PROGMEM = {
        0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
    };

    static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];

    st7920_clear_commands();
    st7920_draw_rect(0, 0, 12, 12);
    st7920_draw_bitmap(2, 2, 8, 8, icono);
    st7920_draw_rect(46, 14, 34, 34);
    st7920_draw_text(0, 57, "Hello");
    st7920_render();

    st7920_draw_animation(PLOT_BASE_X, PLOT_BASE_Y, &plot_anim, plot_buffer, 100);
}
