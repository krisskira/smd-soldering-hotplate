#include "st7920.h"
#include "../avr_spi/avr_spi.h"

#define LCD_CS_LOW()  PORTB &= ~(1<<PB3)
#define LCD_CS_HIGH() PORTB |= (1<<PB3)

static void st7920_write(uint8_t data, uint8_t rs)
{
    LCD_CS_LOW();

    if(rs)
        avr_spi_transmit(0xFA);
    else
        avr_spi_transmit(0xF8);

    avr_spi_transmit(data & 0xF0);
    avr_spi_transmit((data<<4) & 0xF0);

    LCD_CS_HIGH();

    _delay_us(10);
}

void st7920_cmd(uint8_t cmd)
{
    st7920_write(cmd,0);
}

void st7920_data(uint8_t data)
{
    st7920_write(data,1);
}

/* Init display */
void st7920_init(void)
{
    DDRB |= (1 << PB2);
    PORTB |= (1 << PB2); // mantener reset en alto

    // st7920_gpio_init();

    _delay_ms(50);

    st7920_cmd(0x30);
    _delay_ms(10);

    st7920_cmd(0x30);
    _delay_us(100);

    st7920_cmd(0x0C);   // display on
    st7920_cmd(0x01);   // clear
    _delay_ms(10);

    st7920_cmd(0x06);   // entry mode
}

/* Clear text screen */
void st7920_clear(void)
{
    st7920_cmd(0x01);
    _delay_ms(10);
}

/* Set cursor */
void st7920_goto(uint8_t x, uint8_t y)
{
    uint8_t addr;

    if(y == 0) addr = 0x80 + x;
    else       addr = 0x90 + x;

    st7920_cmd(addr);
}

/* Print string */
void st7920_print(const char *str)
{
    while(*str)
    {
        st7920_data(*str++);
    }
}