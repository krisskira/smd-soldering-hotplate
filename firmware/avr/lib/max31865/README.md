# MAX31865 – Sensor de temperatura RTD

Lectura del MAX31865 (RTD PT100/PT1000) por **SPI software** (bit-banging) en pines dedicados.

## Hardware (según código)

| Señal MAX31865 | Pin ATmega16 | Notas |
|----------------|--------------|--------|
| CS   | PB1 | Chip Select |
| SCK  | PA2 | SPI software |
| MOSI | PA0 | SPI software |
| MISO | PA1 | SPI software |
| DRDY | No conectado | Modo polling |

Referencia: `config/board_pins.h`, `lib/avr_soft_spi/`.

## Uso

```c
#include "lib/max31865/max31865.h"

max31865_init();  /* Inicializa SPI software y sensor */

uint16_t rtd = max31865_read_rtd();
float temp_c = max31865_temperature(rtd);
```

## API

- `max31865_init()` – Inicializa SPI software (PA0/PA1/PA2) y configura el sensor: **2-wire** RTD, **filtro 50 Hz**.
- `max31865_read_rtd()` – Devuelve valor ADC del RTD (0xFFFF si hay fault).
- `max31865_temperature(rtd)` – Convierte a temperatura en °C.
- `max31865_read_fault_status()` – Lee el registro de fault (0x07); 0 = sin fallo.
- `max31865_clear_fault()` – Escribe config con FAULT_CLEAR para limpiar fallos.
- `max31865_prepare_for_read()` – Limpia fallos y espera ~10 ms; llamar antes de leer.

## Bus independiente del LCD

El MAX31865 usa SPI software en PORTA; el LCD usa SPI hardware en PORTB. No comparten bus.
