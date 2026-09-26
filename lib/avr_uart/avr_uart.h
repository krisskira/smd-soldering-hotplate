#ifndef AVR_UART_H
#define AVR_UART_H

#include <stdint.h>
#include <avr/io.h>

/* AVR UART Hardware Configuration */
/* Based on atmega16_pin_definition_hotplate.md */
#define AVR_UART_UBRRH   UBRRH
#define AVR_UART_UBRRL   UBRRL
#define AVR_UART_UCSRA   UCSRA
#define AVR_UART_UCSRB   UCSRB
#define AVR_UART_UCSRC   UCSRC
#define AVR_UART_UDR     UDR

/* UART Status bits */
#define AVR_UART_RXC     RXC
#define AVR_UART_TXC     TXC
#define AVR_UART_UDRE    UDRE
#define AVR_UART_FE      FE
#define AVR_UART_DOR     DOR
#define AVR_UART_PE      PE

/* UART Control bits */
#define AVR_UART_RXEN    RXEN
#define AVR_UART_TXEN    TXEN
#define AVR_UART_URSEL   URSEL
#define AVR_UART_UCSZ1   UCSZ1
#define AVR_UART_UCSZ0   UCSZ0

#define AVR_UART_RX_RING_SIZE  32u

/**
 * Initialize AVR UART hardware and enable RX interrupt (RXCIE).
 * Caller should enable global interrupts with sei() after init.
 */
void avr_uart_init(uint32_t baud_rate, uint8_t data_bits, uint8_t stop_bits, char parity);

void avr_uart_transmit_char(char data);
void avr_uart_transmit_string(const char *str);
/** Transmit null-terminated string from PROGMEM (flash). */
void avr_uart_transmit_pstr(const char *pstr);
void avr_uart_transmit_buffer(const uint8_t *buffer, uint16_t length);

/**
 * Non-blocking: pop one byte from RX ring.
 * @return byte 0..255, or -1 if empty
 */
int16_t avr_uart_rx_pop(void);

/**
 * @return number of bytes waiting in RX ring
 */
uint8_t avr_uart_data_available(void);

void avr_uart_flush_rx(void);
void avr_uart_flush_tx(void);
void avr_uart_set_baud_rate(uint32_t baud_rate);

#endif /* AVR_UART_H */
