# AVR UART – Comunicación serial ATmega16

UART hardware del ATmega16 para comunicación serie (p. ej. con puente USB).

## Uso

```c
#include "lib/avr_uart/avr_uart.h"
#include <avr/interrupt.h>

avr_uart_init(19200, 8, 1, 'N'); /* HotPlate: ver doc/usb-automation.md */
sei();

avr_uart_transmit_string("Hola\n");

/* RX en el super-loop; el TX bloquea hasta vaciar el byte */
int16_t c = avr_uart_rx_pop();
if (c >= 0) {
    /* procesar byte */
}
```

## API

- `avr_uart_init(baud, data_bits, stop_bits, parity)` – Init + RXCIE.
- `avr_uart_transmit_char` / `_string` / `_buffer` – TX por polling: espera `UDRE` y bloquea el llamador.
- `avr_uart_rx_pop()` – Pop no bloqueante del ring RX (o -1). La ISR sigue llenando el anillo durante ese TX.
- `avr_uart_data_available()` – Bytes en el ring.
- `avr_uart_flush_rx()` / `avr_uart_flush_tx()`.

Ring RX: 32 bytes (31 útiles). Si se llena, el byte nuevo se descarta.
