# AVR Soft SPI – SPI por software (bit-banging)

Implementación de SPI por software para el ATmega16. Usado por el MAX31865 en pines dedicados (PORTA), independiente del SPI hardware del LCD.

## Hardware (según código)

| Pin ATmega16 | Función | Descripción        |
|--------------|---------|--------------------|
| PA0          | MOSI    | Master Out         |
| PA1          | MISO    | Master In          |
| PA2          | SCK     | Reloj SPI          |

Referencia: `config/board_pins.h`.

## Modo SPI

- **Modo 1** (CPOL=0, CPHA=1): compatible con MAX31865
- Reloj en reposo en bajo
- MSB first

## Uso

```c
#include "lib/avr_soft_spi/avr_soft_spi.h"

avr_soft_spi_init();

avr_soft_spi_select_device(CS_PIN, &CS_PORT);
uint8_t r = avr_soft_spi_transmit(0x55);
avr_soft_spi_deselect_device(CS_PIN, &CS_PORT);
```

## API

- `avr_soft_spi_init()` – Configura pines PA0/PA1/PA2.
- `avr_soft_spi_transmit(uint8_t data)` – Envía un byte y devuelve el recibido.
- `avr_soft_spi_select_device(cs_pin, cs_port)` – Pone CS en bajo.
- `avr_soft_spi_deselect_device(cs_pin, cs_port)` – Pone CS en alto.
