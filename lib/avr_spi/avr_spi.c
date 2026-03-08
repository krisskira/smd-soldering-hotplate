#include "avr_spi.h"
#include <util/delay.h>

/* Con F_CPU 4 MHz: DIV_4 → 1 MHz (usado en esta placa; válido para ST7920 y MAX31865). */
void avr_spi_master_init(spi_clock_div_t div)
{
    /* configurar pines */
    DDRB |= (1 << PB4);      // SS como salida
    PORTB |= (1 << PB4);     // mantener en alto

    DDRB |= (1 << PB5) | (1 << PB7); // MOSI + SCK salida
    DDRB &= ~(1 << PB6);             // MISO entrada

    uint8_t spcr = (1 << SPE) | (1 << MSTR);
    uint8_t spsr = 0;

    switch (div)
    {
        case SPI_DIV_2:
            spsr |= (1 << SPI2X);
            break;

        case SPI_DIV_4:
            break;

        case SPI_DIV_8:
            spcr |= (1 << SPR0);
            spsr |= (1 << SPI2X);
            break;

        case SPI_DIV_16:
            spcr |= (1 << SPR0);
            break;

        case SPI_DIV_32:
            spcr |= (1 << SPR1);
            spsr |= (1 << SPI2X);
            break;

        case SPI_DIV_64:
            spcr |= (1 << SPR1);
            break;

        case SPI_DIV_128:
            spcr |= (1 << SPR1) | (1 << SPR0);
            break;
    }

    SPCR = spcr;
    SPSR = spsr;
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