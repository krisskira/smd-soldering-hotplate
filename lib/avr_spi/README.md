# Librería AVR SPI - Controlador SPI Hardware ATmega16

Librería para controlar el módulo SPI hardware del microcontrolador ATmega16.

## 📋 Características

- ✅ **SPI hardware nativo** del ATmega16
- ✅ **Modo maestro** con configuración flexible
- ✅ **Control de reloj** programable (f_cpu/2 hasta f_cpu/128)
- ✅ **Funciones seguras** para selección/deselección de dispositivos
- ✅ **Compatible** con múltiples dispositivos SPI

## 🔧 Hardware

### Pines SPI (ATmega16)
| Pin ATmega16 | Función SPI | Descripción |
|-------------|-------------|-------------|
| PB7 (19)    | SCK         | Reloj serial |
| PB5 (17)    | MOSI        | Maestro salida/esclavo entrada |
| PB6 (18)    | MISO        | Maestro entrada/esclavo salida |
| PB4 (16)    | SS          | Selección esclavo (no usado en maestro) |

**Referencia:** Ver `doc/atmega16_pin_definition_hotplate.md` para detalles completos.

## 🚀 Uso Básico

### Inicialización
```c
#include "lib/avr_spi/avr_spi.h"

// Inicializar SPI a 1MHz (f_cpu/16 para 12MHz)
avr_spi_master_init(1);  // 1 = f_cpu/16
```

### Comunicación con dispositivo
```c
// Seleccionar dispositivo (CS en PB4)
avr_spi_select_device(PB4, &PORTB);

// Enviar y recibir datos
uint8_t response = avr_spi_transmit(0x55);

// Deseleccionar dispositivo
avr_spi_deselect_device(PB4, &PORTB);
```

## 📖 API de Funciones

### `avr_spi_master_init(uint8_t clock_divider)`
Inicializa el SPI en modo maestro.

**Parámetros:**
- `clock_divider`: Divisor de reloj (0-7)
  - 0: f_cpu/4 (3MHz @ 12MHz)
  - 1: f_cpu/16 (750kHz @ 12MHz) - **Recomendado**
  - 2: f_cpu/64 (187.5kHz @ 12MHz)
  - 3: f_cpu/128 (93.75kHz @ 12MHz)

### `avr_spi_transmit(uint8_t data)`
Transmite un byte y retorna el recibido.

### `avr_spi_select_device(uint8_t cs_pin, volatile uint8_t *cs_port)`
Selecciona un dispositivo SPI (pone CS en bajo).

### `avr_spi_deselect_device(uint8_t cs_pin, volatile uint8_t *cs_port)`
Deselecciona un dispositivo SPI (pone CS en alto).

### `avr_spi_set_clock(uint8_t divider)`
Cambia dinámicamente la velocidad del reloj SPI.

## 🔄 Modos SPI Soportados

- **Mode 0**: CPOL=0, CPHA=0 (por defecto)
- **Mode 1**: CPOL=0, CPHA=1
- **Mode 2**: CPOL=1, CPHA=0
- **Mode 3**: CPOL=1, CPHA=1

*Nota: Para cambiar modo, modificar directamente SPCR después de inicializar.*

## ⚠️ Consideraciones

- **Llamar una vez**: `avr_spi_master_init()` solo al inicio del programa
- **CS manual**: Gestionar manualmente los pines CS de cada dispositivo
- **Velocidad**: Ajustar según las especificaciones del dispositivo esclavo
- **Interrupciones**: SPI no usa interrupciones (modo polling)

## 📚 Dispositivos Compatibles

Esta librería se usa para:
- **MAX31865**: Sensor de temperatura RTD
- **Otros dispositivos SPI**: Que requieran SPI hardware estándar

*Para displays como ST7920 que usan protocolos propietarios, usar software SPI.*