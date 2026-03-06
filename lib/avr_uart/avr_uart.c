#include "avr_uart.h"
#include <util/delay.h>
#include <avr/interrupt.h>

/**
 * Initialize AVR UART hardware
 * @param baud_rate Desired baud rate (e.g., 9600, 115200)
 * @param data_bits Data bits (5-9, typically 8)
 * @param stop_bits Stop bits (1 or 2)
 * @param parity Parity mode ('N'=none, 'E'=even, 'O'=odd)
 */
void avr_uart_init(uint32_t baud_rate, uint8_t data_bits, uint8_t stop_bits, char parity) {
    /* Calculate UBRR value for given baud rate */
    /* UBRR = (F_CPU / (16 * baud_rate)) - 1 */
    uint16_t ubrr = (F_CPU / (16UL * baud_rate)) - 1;

    /* Set baud rate */
    AVR_UART_UBRRH = (uint8_t)(ubrr >> 8);
    AVR_UART_UBRRL = (uint8_t)ubrr;

    /* Configure data bits, parity, and stop bits */
    uint8_t ucsrc = (1 << AVR_UART_URSEL);  /* Select UCSRC register */

    /* Data bits */
    switch (data_bits) {
        case 5: /* UCSZ = 000 */
            break;
        case 6: /* UCSZ = 001 */
            ucsrc |= (1 << AVR_UART_UCSZ0);
            break;
        case 7: /* UCSZ = 010 */
            ucsrc |= (1 << AVR_UART_UCSZ1);
            break;
        case 8: /* UCSZ = 011 */
        default:
            ucsrc |= (1 << AVR_UART_UCSZ1) | (1 << AVR_UART_UCSZ0);
            break;
        case 9: /* UCSZ = 111 - requires special handling */
            ucsrc |= (1 << AVR_UART_UCSZ1) | (1 << AVR_UART_UCSZ0);
            AVR_UART_UCSRB |= (1 << UCSZ2);
            break;
    }

    /* Parity */
    switch (parity) {
        case 'E': /* Even parity */
            ucsrc |= (1 << UPM1);
            break;
        case 'O': /* Odd parity */
            ucsrc |= (1 << UPM1) | (1 << UPM0);
            break;
        case 'N': /* No parity */
        default:
            break;
    }

    /* Stop bits */
    if (stop_bits == 2) {
        ucsrc |= (1 << USBS);
    }

    /* Set UCSRC */
    AVR_UART_UCSRC = ucsrc;

    /* Enable receiver and transmitter */
    AVR_UART_UCSRB = (1 << AVR_UART_RXEN) | (1 << AVR_UART_TXEN);
}

/**
 * Transmit a single character
 * @param data Character to transmit
 */
void avr_uart_transmit_char(char data) {
    /* Wait for empty transmit buffer */
    while (!(AVR_UART_UCSRA & (1 << AVR_UART_UDRE)));

    /* Put data into buffer, sends the data */
    AVR_UART_UDR = data;
}

/**
 * Transmit a null-terminated string
 * @param str String to transmit
 */
void avr_uart_transmit_string(const char *str) {
    while (*str) {
        avr_uart_transmit_char(*str++);
    }
}

/**
 * Transmit a buffer of data
 * @param buffer Pointer to data buffer
 * @param length Number of bytes to transmit
 */
void avr_uart_transmit_buffer(const uint8_t *buffer, uint16_t length) {
    for (uint16_t i = 0; i < length; i++) {
        avr_uart_transmit_char(buffer[i]);
    }
}

/**
 * Receive a single character
 * @param timeout_ms Timeout in milliseconds (0 = no timeout)
 * @return Received character, or -1 if timeout/error
 */
int16_t avr_uart_receive_char(uint16_t timeout_ms) {
    uint16_t timeout_counter = 0;

    /* Wait for data to be received */
    while (!(AVR_UART_UCSRA & (1 << AVR_UART_RXC))) {
        if (timeout_ms > 0) {
            _delay_ms(1);
            timeout_counter++;
            if (timeout_counter >= timeout_ms) {
                return -1;  /* Timeout */
            }
        }
    }

    /* Check for errors */
    if (AVR_UART_UCSRA & ((1 << AVR_UART_FE) | (1 << AVR_UART_DOR) | (1 << AVR_UART_PE))) {
        /* Clear error by reading UDR */
        volatile uint8_t dummy = AVR_UART_UDR;
        (void)dummy;
        return -1;  /* Error */
    }

    /* Get and return received data from buffer */
    return AVR_UART_UDR;
}

/**
 * Receive a line (until \n or \r)
 * @param buffer Buffer to store the line
 * @param max_length Maximum buffer length
 * @param timeout_ms Timeout per character in milliseconds
 * @return Number of characters received, or -1 if timeout
 */
int16_t avr_uart_receive_line(char *buffer, uint16_t max_length, uint16_t timeout_ms) {
    uint16_t index = 0;

    while (index < max_length - 1) {
        int16_t received = avr_uart_receive_char(timeout_ms);

        if (received == -1) {
            /* Timeout */
            if (index == 0) {
                return -1;  /* No data received */
            } else {
                break;  /* Return what we have */
            }
        }

        char c = (char)received;

        if (c == '\n' || c == '\r') {
            break;  /* End of line */
        }

        buffer[index++] = c;
    }

    buffer[index] = '\0';  /* Null terminate */
    return index;
}

/**
 * Check if data is available to read
 * @return 1 if data available, 0 otherwise
 */
uint8_t avr_uart_data_available(void) {
    return (AVR_UART_UCSRA & (1 << AVR_UART_RXC)) ? 1 : 0;
}

/**
 * Flush the UART receive buffer
 */
void avr_uart_flush_rx(void) {
    /* Read any available data to clear the buffer */
    while (AVR_UART_UCSRA & (1 << AVR_UART_RXC)) {
        volatile uint8_t dummy = AVR_UART_UDR;
        (void)dummy;
    }
}

/**
 * Flush the UART transmit buffer (wait for completion)
 */
void avr_uart_flush_tx(void) {
    /* Wait for transmit buffer to be empty */
    while (!(AVR_UART_UCSRA & (1 << AVR_UART_TXC)));
}

/**
 * Set UART baud rate dynamically
 * @param baud_rate New baud rate
 */
void avr_uart_set_baud_rate(uint32_t baud_rate) {
    /* Calculate UBRR value for given baud rate */
    uint16_t ubrr = (F_CPU / (16UL * baud_rate)) - 1;

    /* Set baud rate */
    AVR_UART_UBRRH = (uint8_t)(ubrr >> 8);
    AVR_UART_UBRRL = (uint8_t)ubrr;
}