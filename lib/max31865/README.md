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

- `max31865_init()` – Configura el sensor: **2-wire** RTD (no 3-wire), conversión automática, **filtro 50 Hz**.
- `max31865_read_rtd()` – Devuelve valor ADC del RTD (0xFFFF si hay fault).
- `max31865_temperature(rtd)` – Convierte a temperatura en °C.
- `max31865_read_fault_status()` – Lee el registro de fault (0x07); 0 = sin fallo.
- `max31865_clear_fault()` – Escribe config con FAULT_CLEAR para limpiar fallos.
- `max31865_prepare_for_read()` – Limpia fallos y espera ~30 ms; llamar antes de leer con el bus libre.

## SPI compartido con la pantalla

Cuando el bus SPI se comparte con el LCD (u otro dispositivo), hay que **deseleccionar el otro dispositivo** antes de hablar con el MAX31865, para evitar datos basura y fault por tráfico ajeno:

1. Poner **LCD CS en alto** (deseleccionar pantalla).
2. Pequeña espera (p. ej. 2 ms).
3. `max31865_prepare_for_read()` (clear fault + espera).
4. `max31865_read_rtd()`.
5. Usar el valor y volver a usar el LCD; el LCD se selecciona de nuevo en la siguiente llamada a la librería de pantalla.

Conviene leer el sensor cada 500 ms (o similar) con un temporizador no bloqueante para no saturar el bus ni bloquear animaciones.

Pines CS y SPI deben coincidir con `config/board_pins.h` y la librería `avr_spi`.
