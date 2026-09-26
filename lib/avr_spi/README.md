# AVR SPI – SPI hardware ATmega16

SPI hardware del ATmega16 usado **solo por el LCD ST7920**.
El MAX31865 usa SPI **software** independiente en PORTA.

## Hardware (según `config/board_pins.h`)

| Pin ATmega16 | Función | Descripción |
|--------------|---------|-------------|
| PB7 | SCK  | Reloj SPI |
| PB6 | MISO | Maestro entrada (LCD no lo usa) |
| PB5 | MOSI | Maestro salida |
| PB0 | LCD_CS | Chip Select ST7920 (activo alto en modo serie) |
| PB1 | MAX_CS | Chip Select MAX31865 (SPI software, no este bus) |

F_CPU oficial: **8 MHz**. Divisor típico en app: `SPI_DIV_8` → 1 MHz.

## Uso

```c
#include "lib/avr_spi/avr_spi.h"

avr_spi_master_init(SPI_DIV_8);
uint8_t r = avr_spi_transmit(0x55);
```

## API

- `avr_spi_master_init(spi_clock_div_t div)` – SPI maestro.
- `avr_spi_transmit(uint8_t data)` – Envía un byte y devuelve el recibido.
- `avr_spi_select_device` / `avr_spi_deselect_device` – CS genérico (el ST7920 gestiona el suyo).
- `avr_spi_set_clock(divider)` – Cambia el divisor.
