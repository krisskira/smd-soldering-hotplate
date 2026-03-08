#ifndef BOARD_PINS_H
#define BOARD_PINS_H

#include <avr/io.h>

/* SPI hardware (LCD ST7920) - PORTB */
#define SPI_PORT PORTB
#define SPI_DDR  DDRB

#define SPI_MOSI PB5
#define SPI_MISO PB6
#define SPI_SCK  PB7

/* SPI software (MAX31865) - PORTA */
#define SOFT_SPI_MOSI  PA0
#define SOFT_SPI_MISO  PA1
#define SOFT_SPI_SCK   PA2
#define SOFT_SPI_DDR   DDRA
#define SOFT_SPI_PORT  PORTA
#define SOFT_SPI_PIN   PINA

/* Chip Selects */

/* LCD ST7920: CS en PB0 (SPI hardware) */
#define LCD_CS_PORT PORTB
#define LCD_CS_DDR  DDRB
#define LCD_CS_PIN  PB0

#define MAX31865_CS_PORT PORTB
#define MAX31865_CS_DDR  DDRB
#define MAX31865_CS_PIN  PB1

#endif