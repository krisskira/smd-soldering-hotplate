#ifndef AVR_SOFT_SPI_H
#define AVR_SOFT_SPI_H

#include <stdint.h>
#include <avr/io.h>

/* SPI software - pines configurables en config/board_pins.h */
#include "../../config/board_pins.h"

/**
 * Inicializa SPI por software (bit-banging).
 * Configura MOSI, SCK como salida; MISO como entrada.
 * Modo SPI 1 (CPOL=0, CPHA=1) - compatible con MAX31865.
 */
void avr_soft_spi_init(void);

/**
 * Transmite un byte por SPI y devuelve el recibido.
 * @param data Byte a transmitir
 * @return Byte recibido
 */
uint8_t avr_soft_spi_transmit(uint8_t data);

/**
 * Selecciona dispositivo SPI (pone CS en bajo).
 * @param cs_pin Número de pin Chip Select
 * @param cs_port Puntero al registro PORT del CS
 */
void avr_soft_spi_select_device(uint8_t cs_pin, volatile uint8_t *cs_port);

/**
 * Deselecciona dispositivo SPI (pone CS en alto).
 * @param cs_pin Número de pin Chip Select
 * @param cs_port Puntero al registro PORT del CS
 */
void avr_soft_spi_deselect_device(uint8_t cs_pin, volatile uint8_t *cs_port);

#endif /* AVR_SOFT_SPI_H */
