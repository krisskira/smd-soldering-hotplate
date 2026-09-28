#include "avr_soft_spi.h"
#include <util/delay.h>

/* SPI Mode 1 (CPOL=0, CPHA=1): reloj idle bajo, muestreo en bajada, cambio en subida.
 * Bit-banging MSB first: poner MOSI -> SCK alto (capturar) -> SCK bajo (slave cambia). */

void avr_soft_spi_init(void)
{
    SOFT_SPI_DDR |= (1 << SOFT_SPI_MOSI) | (1 << SOFT_SPI_SCK);
    SOFT_SPI_DDR &= ~(1 << SOFT_SPI_MISO);
    SOFT_SPI_PORT &= ~(1 << SOFT_SPI_SCK); /* SCK idle bajo */
}

uint8_t avr_soft_spi_transmit(uint8_t data)
{
    uint8_t result = 0;

    for (int8_t i = 7; i >= 0; i--) {
        /* 1. Poner MOSI con el bit a enviar */
        if (data & (1 << i))
            SOFT_SPI_PORT |= (1 << SOFT_SPI_MOSI);
        else
            SOFT_SPI_PORT &= ~(1 << SOFT_SPI_MOSI);

        /* 2. SCK alto -> flanco subida (slave captura MOSI, nosotros capturamos MISO) */
        SOFT_SPI_PORT |= (1 << SOFT_SPI_SCK);
        _delay_us(1);
        result = (result << 1) | ((SOFT_SPI_PIN & (1 << SOFT_SPI_MISO)) ? 1 : 0);

        /* 3. SCK bajo -> flanco bajada (slave prepara siguiente bit) */
        SOFT_SPI_PORT &= ~(1 << SOFT_SPI_SCK);
        _delay_us(1);
    }

    return result;
}

void avr_soft_spi_select_device(uint8_t cs_pin, volatile uint8_t *cs_port)
{
    *cs_port &= ~(1 << cs_pin);
    _delay_us(1);
}

void avr_soft_spi_deselect_device(uint8_t cs_pin, volatile uint8_t *cs_port)
{
    _delay_us(1);
    *cs_port |= (1 << cs_pin);
}
