# AVR UART – Comunicación serial ATmega16

UART hardware del ATmega16 para comunicación serie (p. ej. con puente USB).

## Uso

```c
#include "lib/avr_uart/avr_uart.h"
#include <avr/interrupt.h>

avr_uart_init(9600, 8, 1, 'N');
sei();

avr_uart_transmit_string("Hola\n");

/* Super-loop no bloqueante */
int16_t c = avr_uart_rx_pop();
if (c >= 0) {
    /* procesar byte */
}
```

## API

- `avr_uart_init(baud, data_bits, stop_bits, parity)` – Init + RXCIE.
- `avr_uart_transmit_char` / `_string` / `_buffer` – TX polling.
- `avr_uart_rx_pop()` – Pop no bloqueante del ring RX (o -1).
- `avr_uart_data_available()` – Bytes en el ring.
- `avr_uart_flush_rx()` / `avr_uart_flush_tx()`.

Ring RX: 64 bytes. Overflow descarta el byte nuevo.
