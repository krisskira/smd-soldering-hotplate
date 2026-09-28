#ifndef BOARD_PINS_H
#define BOARD_PINS_H

#include <avr/io.h>

/*
 * Mapa de pines del ATmega16 — SMI Soldering Hot Plate.
 * Fuente de verdad para SPI, CS y actuadores. F_CPU oficial: 8 MHz
 * (lo define el Makefile; cristal de la placa según BOM puede diferir,
 * pero el firmware se compila y temporiza a 8 MHz).
 */

/* ---------- SPI hardware (LCD ST7920) — PORTB ------------------------ */

#define SPI_PORT PORTB
#define SPI_DDR  DDRB

#define SPI_MOSI PB5
#define SPI_MISO PB6
#define SPI_SCK  PB7

/* ---------- SPI software (MAX31865) — PORTA -------------------------- */

#define SOFT_SPI_MOSI  PA0
#define SOFT_SPI_MISO  PA1
#define SOFT_SPI_SCK   PA2
#define SOFT_SPI_DDR   DDRA
#define SOFT_SPI_PORT  PORTA
#define SOFT_SPI_PIN   PINA

/* ---------- Chip Selects --------------------------------------------- */

#define LCD_CS_PORT PORTB
#define LCD_CS_DDR  DDRB
#define LCD_CS_PIN  PB0

#define MAX31865_CS_PORT PORTB
#define MAX31865_CS_DDR  DDRB
#define MAX31865_CS_PIN  PB1

/* ---------- Encoder (PORTD) ------------------------------------------ */

#define ENC_PORT  PORTD
#define ENC_DDR   DDRD
#define ENC_PINR  PIND
#define ENC_A     PD2       /* CLK */
#define ENC_B     PD3       /* DT  */
#define ENC_SW    PD4       /* pulsador, activo bajo */

/*
 * Semántica de encoder_poll():
 *   +1 = un click en sentido HORARIO  → cursor baja en el menú
 *   -1 = un click en sentido ANTIHORARIO → cursor sube
 *
 * Si el cableado A/B está invertido respecto a la mecánica, pon 0.
 */
#define ENC_CW_IS_POSITIVE  1

/* ---------- Actuadores ----------------------------------------------- */

/* Calefactores (esquemático: PTC1=PD7 pin21, PTC2=PD6 pin20) */
#define PTC1_PORT PORTD
#define PTC1_DDR  DDRD
#define PTC1_PIN  PD7

#define PTC2_PORT PORTD
#define PTC2_DDR  DDRD
#define PTC2_PIN  PD6

/* Bomba de aire / ventilador (esquemático: FAN=PC0 pin22) */
#define FAN_PORT  PORTC
#define FAN_DDR   DDRC
#define FAN_PIN   PC0

/* Buzzer */
#define BUZZER_PORT PORTD
#define BUZZER_DDR  DDRD
#define BUZZER_PIN  PD5

#endif
