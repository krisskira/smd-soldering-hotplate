# AVR UART – Comunicación serial ATmega16

UART hardware del ATmega16 para comunicación serie (p. ej. con puente USB).

## Hardware (según código)

| Pin ATmega16 | Función | Descripción |
|--------------|---------|-------------|
| PD0 | RXD | Recepción |
| PD1 | TXD | Transmisión |

Referencia: `doc/atmega16_pin_definition_hotplate.md`.

## Uso

```c
#include "lib/avr_uart/avr_uart.h"

// 9600 baud, 8 datos, 1 stop, sin paridad
avr_uart_init(9600, 8, 1, 'N');

avr_uart_transmit_string("Hola\n");

char buf[64];
int16_t n = avr_uart_receive_line(buf, sizeof(buf), 1000);
```

## API principal

- `avr_uart_init(baud_rate, data_bits, stop_bits, parity)` – Inicialización.
- `avr_uart_transmit_char(c)` / `avr_uart_transmit_string(str)` / `avr_uart_transmit_buffer(buf, len)`.
- `avr_uart_receive_char(timeout_ms)` – Devuelve carácter o -1.
- `avr_uart_receive_line(buf, max_len, timeout_ms)` – Lee hasta \n/\r.
- `avr_uart_data_available()` / `avr_uart_flush_rx()` / `avr_uart_flush_tx()`.

Paridad: `'N'` ninguna, `'E'` par, `'O'` impar.
