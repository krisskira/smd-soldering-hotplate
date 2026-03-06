# AVR SPI – SPI hardware ATmega16

Control del módulo SPI hardware del ATmega16. Usado por el LCD ST7920 y el MAX31865 en el mismo bus, con CS independientes.

## Hardware (según código)

| Pin ATmega16 | Función | Descripción |
|--------------|---------|-------------|
| PB7 | SCK  | Reloj SPI |
| PB6 | MISO | Maestro entrada |
| PB5 | MOSI | Maestro salida |
| PB3 | LCD_CS | Chip Select ST7920 (en `st7920_config.c`) |
| PB4 | CS    | Otro CS (p. ej. MAX31865); alto en reposo |

Referencia: `config/board_pins.h` y `doc/atmega16_pin_definition_hotplate.md`.

## Uso

```c
#include "lib/avr_spi/avr_spi.h"

// Una vez al inicio (sin argumentos en la API actual)
avr_spi_master_init();

// Envío de un byte (los dispositivos bajan su CS antes de transmitir)
uint8_t r = avr_spi_transmit(0x55);
```

## API

- `avr_spi_master_init()` – Inicializa SPI maestro (reloj f_cpu/16 con SPI2X).
- `avr_spi_transmit(uint8_t data)` – Envía un byte y devuelve el recibido.
- `avr_spi_select_device(cs_pin, cs_port)` – Pone CS en bajo.
- `avr_spi_deselect_device(cs_pin, cs_port)` – Pone CS en alto.
- `avr_spi_set_clock(divider)` – Cambia el divisor de reloj.

El LCD ST7920 y el MAX31865 gestionan su propio CS internamente; no hace falta llamar select/deselect desde la aplicación para el flujo normal.
