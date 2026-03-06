#include "avr_spi.h"
#include <util/delay.h>

void avr_spi_master_init()
{
    /* safe master mode */
    DDRB |= (1 << PB4);
    PORTB |= (1 << PB4);

    DDRB |= (1 << PB5) | (1 << PB7); // MOSI + SCK
    DDRB &= ~(1 << PB6);             // MISO

    SPCR =
        (1 << SPE) |  // enable SPI
        (1 << MSTR) | // master
        (1 << SPR0);  // clk /16

    SPSR = (1 << SPI2X); // clk /8
}

/**
 * Transmit one byte via SPI and return received byte
 * @param data Byte to transmit
 * @return Received byte
 */
uint8_t avr_spi_transmit(uint8_t data)
{
    SPDR = data;
    while (!(SPSR & (1 << SPIF)))
        ;
    return SPDR;
}

/**
 * Select SPI device (pull CS low)
 * @param cs_pin Chip select pin number
 * @param cs_port Pointer to chip select port register
 */
void avr_spi_select_device(uint8_t cs_pin, volatile uint8_t *cs_port)
{
    *cs_port &= ~(1 << cs_pin);
    _delay_us(1); /* Small delay for CS setup */
}

/**
 * Deselect SPI device (pull CS high)
 * @param cs_pin Chip select pin number
 * @param cs_port Pointer to chip select port register
 */
void avr_spi_deselect_device(uint8_t cs_pin, volatile uint8_t *cs_port)
{
    _delay_us(1); /* Small delay for data hold */
    *cs_port |= (1 << cs_pin);
}

/**
 * Set SPI clock divider dynamically
 * @param divider Clock divider value (0-7):
 *               0: f_cpu/4, 1: f_cpu/16, 2: f_cpu/64, 3: f_cpu/128
 *               4: f_cpu/2, 5: f_cpu/8, 6: f_cpu/32, 7: f_cpu/64 (with SPI2X)
 */
void avr_spi_set_clock(uint8_t divider)
{
    /* Clear current clock bits */
    SPCR &= ~((1 << SPR1) | (1 << SPR0));
    SPSR &= ~(1 << SPI2X);

    /* Set new clock divider */
    if (divider & 0x04)
    {
        SPSR |= (1 << SPI2X);
    }
    SPCR |= (divider & 0x03);
}