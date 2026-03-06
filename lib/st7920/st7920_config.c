/*
 * ST7920 - Configuración, comandos y modo texto.
 */
#include "st7920.h"
#include "st7920_private.h"
#include "../avr_spi/avr_spi.h"
#include <util/delay.h>

#define LCD_CS_LOW()  PORTB &= ~(1 << PB3)
#define LCD_CS_HIGH() PORTB |= (1 << PB3)

static void st7920_write(uint8_t data, uint8_t rs)
{
    LCD_CS_LOW();

    if (rs)
        avr_spi_transmit(0xFA);
    else
        avr_spi_transmit(0xF8);

    avr_spi_transmit(data & 0xF0);
    avr_spi_transmit((data << 4) & 0xF0);

    LCD_CS_HIGH();
    _delay_us(10);
}

void st7920_cmd(uint8_t cmd)
{
    st7920_write(cmd, 0);
}

void st7920_data(uint8_t data)
{
    st7920_write(data, 1);
}

void st7920_set_gdram(uint8_t x, uint8_t y)
{
    if (y < 32)
    {
        st7920_cmd(0x80 | y);
        st7920_cmd(0x80 | x);
    }
    else
    {
        st7920_cmd(0x80 | (y - 32));
        st7920_cmd(0x88 | x);
    }
}

void st7920_write_gdram(uint8_t x, uint8_t y, uint8_t left, uint8_t right)
{
    st7920_set_gdram(x, y);
    st7920_data(left);
    st7920_data(right);
}

void st7920_clear_gdram(void)
{
    for (uint8_t y = 0; y < 32; y++)
    {
        st7920_cmd(0x80 | y);
        st7920_cmd(0x80);

        for (uint8_t x = 0; x < 16; x++)
        {
            st7920_data(0x00);
            st7920_data(0x00);
        }
    }

    for (uint8_t y = 0; y < 32; y++)
    {
        st7920_cmd(0x80 | y);
        st7920_cmd(0x88);

        for (uint8_t x = 0; x < 16; x++)
        {
            st7920_data(0x00);
            st7920_data(0x00);
        }
    }
}

void st7920_init(void)
{
    DDRB |= (1 << PB2);
    PORTB |= (1 << PB2);
    _delay_ms(50);

    st7920_cmd(0x30);
    _delay_ms(10);
    st7920_cmd(0x30);
    _delay_us(110);
    st7920_cmd(0x0C);
    _delay_us(110);
    st7920_cmd(0x01);
    _delay_ms(12);
    st7920_cmd(0x06);
    _delay_us(110);
}

void st7920_clear(void)
{
    st7920_cmd(0x01);
    _delay_ms(10);
}

void st7920_graphics_mode(void)
{
    st7920_cmd(0x34);
    st7920_cmd(0x36);
    st7920_clear_gdram();
    st7920_clear_gdram_buffer();
}

void st7920_goto(uint8_t x, uint8_t y)
{
    uint8_t addr = (y == 0) ? (0x80 + x) : (0x90 + x);
    st7920_cmd(addr);
}

void st7920_print(const char *str)
{
    while (*str)
        st7920_data((uint8_t)*str++);
}
