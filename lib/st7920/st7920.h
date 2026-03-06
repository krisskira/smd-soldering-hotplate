#ifndef ST7920_H
#define ST7920_H

#include <avr/io.h>
#include <util/delay.h>
#include <stdint.h>

/* Pin configuration */
#define ST7920_PORT PORTB
#define ST7920_DDR  DDRB

#define ST7920_E    PB0
#define ST7920_RW   PB1
#define ST7920_RS   PB2

/* Public API */

void st7920_init(void);

void st7920_cmd(uint8_t cmd);
void st7920_data(uint8_t data);

void st7920_clear(void);
void st7920_goto(uint8_t x, uint8_t y);

void st7920_print(const char *str);

#endif