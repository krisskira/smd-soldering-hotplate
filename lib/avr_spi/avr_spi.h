#ifndef AVR_SPI_H
#define AVR_SPI_H

#include <stdint.h>
#include <avr/io.h>

/* AVR SPI Hardware Configuration */
/* Based on atmega16_pin_definition_hotplate.md */
#define AVR_SPI_DDR   DDRB
#define AVR_SPI_PORT  PORTB
#define AVR_SPI_CLK   PB7  /* SCK   - Hardware SPI Clock */
#define AVR_SPI_MOSI  PB5  /* MOSI  - Master Out/Slave In */
#define AVR_SPI_MISO  PB6  /* MISO  - Master In/Slave Out */

/* Function prototypes for AVR hardware SPI */

/**
 * Initialize AVR SPI hardware in master mode
 * Call this once at system startup for all SPI devices
 * @param clock_divider SPI clock divider (SPR0, SPR1 bits)
 */
void avr_spi_master_init();

/**
 * Transmit one byte via SPI and return received byte
 * @param data Byte to transmit
 * @return Received byte
 */
uint8_t avr_spi_transmit(uint8_t data);

/**
 * Select SPI device (pull CS low)
 * @param cs_pin Chip select pin number
 * @param cs_port Pointer to chip select port register
 */
void avr_spi_select_device(uint8_t cs_pin, volatile uint8_t *cs_port);

/**
 * Deselect SPI device (pull CS high)
 * @param cs_pin Chip select pin number
 * @param cs_port Pointer to chip select port register
 */
void avr_spi_deselect_device(uint8_t cs_pin, volatile uint8_t *cs_port);

/**
 * Set SPI clock divider
 * @param divider Clock divider value (0-3 for SPR0/SPR1)
 */
void avr_spi_set_clock(uint8_t divider);

#endif /* AVR_SPI_H */