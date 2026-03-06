# Librería AVR UART - Comunicación Serial ATmega16

Librería para controlar el módulo UART (USART) hardware del microcontrolador ATmega16.

## 📋 Características

- ✅ **UART hardware nativo** del ATmega16
- ✅ **Configuración flexible** de baud rate, bits de datos, paridad
- ✅ **Funciones de transmisión** síncronas y asíncronas
- ✅ **Recepción con timeout** para operaciones robustas
- ✅ **Lectura de líneas completas** con manejo de \n/\r
- ✅ **Buffer management** integrado

## 🔧 Hardware

### Pines UART (ATmega16)
| Pin ATmega16 | Función UART | Descripción |
|-------------|--------------|-------------|
| PD0 (14)    | RXD          | Recepción de datos |
| PD1 (15)    | TXD          | Transmisión de datos |

**Referencia:** Ver `doc/atmega16_pin_definition_hotplate.md` para detalles completos.

## 🚀 Uso Básico

### Inicialización
```c
#include "lib/avr_uart/avr_uart.h"

// Inicializar UART a 9600 baud, 8N1 (8 bits, sin paridad, 1 stop bit)
avr_uart_init(9600, 8, 1, 'N');
```

### Comunicación Básica
```c
// Enviar carácter
avr_uart_transmit_char('H');
avr_uart_transmit_char('i');

// Enviar string
avr_uart_transmit_string("Hello World!\n");

// Enviar buffer
uint8_t data[] = {0x01, 0x02, 0x03};
avr_uart_transmit_buffer(data, sizeof(data));

// Recibir carácter con timeout de 1 segundo
int16_t received = avr_uart_receive_char(1000);
if (received != -1) {
    // Procesar carácter recibido
    char c = (char)received;
}

// Recibir línea completa
char buffer[64];
int16_t length = avr_uart_receive_line(buffer, sizeof(buffer), 5000);
if (length > 0) {
    // Procesar línea recibida
}
```

## 📖 API de Funciones

### `avr_uart_init(uint32_t baud_rate, uint8_t data_bits, uint8_t stop_bits, char parity)`
Inicializa el UART con configuración completa.

**Parámetros:**
- `baud_rate`: Velocidad en baudios (9600, 19200, 115200, etc.)
- `data_bits`: Bits de datos (5-9, típicamente 8)
- `stop_bits`: Bits de stop (1 o 2)
- `parity`: Paridad ('N'=ninguna, 'E'=par, 'O'=impar)

### `avr_uart_transmit_char(char data)`
Transmite un carácter.

### `avr_uart_transmit_string(const char *str)`
Transmite una cadena terminada en null.

### `avr_uart_transmit_buffer(const uint8_t *buffer, uint16_t length)`
Transmite un buffer de datos.

### `avr_uart_receive_char(uint16_t timeout_ms)`
Recibe un carácter con timeout.

**Retorna:** Carácter recibido, o -1 si timeout/error.

### `avr_uart_receive_line(char *buffer, uint16_t max_length, uint16_t timeout_ms)`
Recibe una línea completa hasta \n o \r.

**Retorna:** Número de caracteres recibidos, o -1 si timeout.

### `avr_uart_data_available()`
Verifica si hay datos disponibles para leer.

**Retorna:** 1 si hay datos, 0 si no.

### `avr_uart_flush_rx()`
Limpia el buffer de recepción.

### `avr_uart_flush_tx()`
Espera a que se complete la transmisión.

### `avr_uart_set_baud_rate(uint32_t baud_rate)`
Cambia dinámicamente la velocidad de baudios.

## 🔄 Configuraciones Soportadas

### Bits de Datos
- 5, 6, 7, 8, 9 bits

### Bits de Stop
- 1 bit
- 2 bits

### Paridad
- 'N': Sin paridad
- 'E': Paridad par
- 'O': Paridad impar

### Velocidades de Baudios
- 2400, 4800, 9600, 19200, 38400, 57600, 115200
- O cualquier velocidad calculable: baud = F_CPU / (16 * (UBRR + 1))

## ⚠️ Consideraciones

- **Inicialización única**: Llamar `avr_uart_init()` solo una vez al inicio
- **Timeout**: Usar timeout > 0 para evitar bloqueos infinitos
- **Buffer limitado**: El UART no tiene buffer de hardware grande
- **Interrupciones**: Esta implementación usa polling, no interrupciones
- **Errores**: La función `receive_char` detecta y reporta errores de framing/paridad

## 📚 Aplicaciones Típicas

Esta librería es ideal para:
- **Comunicación con PC** vía USB-UART
- **Debugging** con printf-style output
- **Protocolos seriales** (Modbus, etc.)
- **Interfaz de usuario** vía terminal serie

## 🔧 Configuración Recomendada

Para la mayoría de aplicaciones:

```c
// 9600 baud, 8 bits de datos, 1 stop bit, sin paridad
avr_uart_init(9600, 8, 1, 'N');
```

Para alta velocidad:

```c
// 115200 baud, 8 bits de datos, 1 stop bit, sin paridad
avr_uart_init(115200, 8, 1, 'N');
```