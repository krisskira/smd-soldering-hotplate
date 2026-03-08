#define F_CPU 4000000UL

#include <avr/io.h>
#include <avr/pgmspace.h>
#include <stdint.h>
#include "../config/board_pins.h"
#include "lib/ports/ports.h"
#include "lib/avr_spi/avr_spi.h"
#include "lib/avr_delay/avr_delay.h"
#include "lib/st7920/st7920.h"
#include "lib/max31865/max31865.h"
#include "icons/animated/plot.c"
#include "icons/animated/temperature.c"
#include <util/delay.h>
#include <stdio.h>
#include <stdlib.h>

/** Convierte temperatura °C a cadena "XXX" o "ERR". buf al menos 5 bytes. */
static void format_temp_c(float temp_c, char *buf, uint8_t buf_size)
{
    if (buf_size < 4u)
        return;
    if (temp_c < -99.0f || temp_c > 999.0f) {
        buf[0] = 'E'; buf[1] = 'R'; buf[2] = 'R'; buf[3] = '\0';
        return;
    }
    int16_t n = (int16_t)(temp_c >= 0.0f ? temp_c + 0.5f : temp_c - 0.5f);
    uint8_t i = 0;
    if (n < 0) {
        buf[i++] = '-';
        n = (int16_t)(-(int32_t)n);
    }
    if (n >= 100)
        buf[i++] = (char)('0' + (n / 100));
    if (n >= 10)
        buf[i++] = (char)('0' + ((n / 10) % 10));
    buf[i++] = (char)('0' + (n % 10));
    buf[i] = '\0';
}

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
    avr_spi_master_init(SPI_DIV_4);  /* SPI hardware para LCD */
    st7920_init();
    st7920_graphics_mode();
    st7920_disable();
    ptc_init();
    buzzer_init();
    max31865_init();  /* SPI software en PA0/PA1/PA2 */
    delay_init();


    const uint8_t icono[] PROGMEM = {
        0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
    };

    static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];
    static uint8_t temperature_buffer[TEMPERATURE_BYTES_PER_FRAME];

    static st7920_animation_ctx_t plot_ctx;
    static st7920_animation_ctx_t temperature_ctx;

    static const st7920_animation_slot_t animation_slots1[] = {
        { &plot_ctx,        2, 16, &plot_anim,        plot_buffer,        100 },
    };

    static const st7920_animation_slot_t animation_slots2[] = {
        { &temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100 },
    };
    #define ANIMATION_SLOT_COUNT1  (sizeof(animation_slots1) / sizeof(animation_slots1[0]))
    #define ANIMATION_SLOT_COUNT2  (sizeof(animation_slots2) / sizeof(animation_slots2[0]))

    st7920_clear_commands();
    st7920_draw_rect(0, 0, 12, 12);
    st7920_draw_bitmap(2, 2, 8, 8, icono);
    st7920_draw_rect(46, 14, 34, 34);
    st7920_render();

    static float temperature = 0.0f;
    static const uint16_t temperature_sampling_time_ms = 1000u;
    static uint16_t temperature_time = 0;

    temperature_time = delay_ms();

    /* LCD y MAX31865 en buses distintos (SPI software vs hardware), sin conflicto. */
    while (1) {
        uint16_t now = delay_ms();

        if ((uint16_t)(now - temperature_time) >= temperature_sampling_time_ms) {
            ptc_on();
            max31865_prepare_for_read();
            uint16_t rtd = max31865_read_rtd();
            temperature = max31865_temperature(rtd);
            ptc_off();
            temperature_time = now;
        }

        /* Actualizar animaciones y texto en pantalla */
        char buffer[20];
        char texto[40] = "Valor: ";
        dtostrf(temperature, 6, 2, buffer); 
        strcat(texto, buffer); // concatenar el buffer al texto
        st7920_animation_run_all(animation_slots1, (uint8_t)ANIMATION_SLOT_COUNT1);
        st7920_animation_run_all(animation_slots2, (uint8_t)ANIMATION_SLOT_COUNT2);
        st7920_draw_text_gdram(35, 57, texto);
    }
}
