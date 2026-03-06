# MAX31865 – Sensor de temperatura RTD

Lectura del MAX31865 (RTD PT100/PT1000) por **SPI hardware** compartido con el LCD.

## Hardware (según código)

| Señal MAX31865 | Pin ATmega16 | Notas |
|----------------|--------------|--------|
| CS   | PB4 | Chip Select |
| SCK  | PB7 | SPI compartido |
| MOSI | PB5 | SPI compartido |
| MISO | PB6 | SPI compartido |
| DRDY | No conectado | Modo polling |

Referencia: `config/board_pins.h`, `doc/atmega16_pin_definition_hotplate.md`.

## Uso

```c
#include "lib/max31865/max31865.h"

avr_spi_master_init();
max31865_init();

uint16_t rtd = max31865_read_rtd();
float temp_c = max31865_temperature(rtd);
```

## API

- `max31865_init()` – Configura el sensor (p. ej. 2-wire, conversión automática).
- `max31865_read_rtd()` – Devuelve valor ADC del RTD.
- `max31865_temperature(rtd)` – Convierte a temperatura en °C.

Pines CS y SPI deben coincidir con `config/board_pins.h` y la librería `avr_spi`.
