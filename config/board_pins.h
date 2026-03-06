#ifndef BOARD_PINS_H
#define BOARD_PINS_H

#include <avr/io.h>

/* SPI hardware */

#define SPI_PORT PORTB
#define SPI_DDR  DDRB

#define SPI_MOSI PB5
#define SPI_MISO PB6
#define SPI_SCK  PB7

/* Chip Selects */

#define LCD_CS_PORT PORTB
#define LCD_CS_DDR  DDRB
#define LCD_CS_PIN  PB3

#define MAX31865_CS_PORT PORTB
#define MAX31865_CS_DDR  DDRB
#define MAX31865_CS_PIN  PB4

#endif