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

/* Function prototypes for AVR UART */

/**
 * Initialize AVR UART hardware
 * @param baud_rate Desired baud rate (e.g., 9600, 115200)
 * @param data_bits Data bits (5-9, typically 8)
 * @param stop_bits Stop bits (1 or 2)
 * @param parity Parity mode ('N'=none, 'E'=even, 'O'=odd)
 */
void avr_uart_init(uint32_t baud_rate, uint8_t data_bits, uint8_t stop_bits, char parity);

/**
 * Transmit a single character
 * @param data Character to transmit
 */
void avr_uart_transmit_char(char data);

/**
 * Transmit a null-terminated string
 * @param str String to transmit
 */
void avr_uart_transmit_string(const char *str);

/**
 * Transmit a buffer of data
 * @param buffer Pointer to data buffer
 * @param length Number of bytes to transmit
 */
void avr_uart_transmit_buffer(const uint8_t *buffer, uint16_t length);

/**
 * Receive a single character
 * @param timeout_ms Timeout in milliseconds (0 = no timeout)
 * @return Received character, or -1 if timeout/error
 */
int16_t avr_uart_receive_char(uint16_t timeout_ms);

/**
 * Receive a line (until \n or \r)
 * @param buffer Buffer to store the line
 * @param max_length Maximum buffer length
 * @param timeout_ms Timeout per character in milliseconds
 * @return Number of characters received, or -1 if timeout
 */
int16_t avr_uart_receive_line(char *buffer, uint16_t max_length, uint16_t timeout_ms);

/**
 * Check if data is available to read
 * @return Number of bytes available in receive buffer
 */
uint8_t avr_uart_data_available(void);

/**
 * Flush the UART receive buffer
 */
void avr_uart_flush_rx(void);

/**
 * Flush the UART transmit buffer (wait for completion)
 */
void avr_uart_flush_tx(void);

/**
 * Set UART baud rate dynamically
 * @param baud_rate New baud rate
 */
void avr_uart_set_baud_rate(uint32_t baud_rate);

#endif /* AVR_UART_H */