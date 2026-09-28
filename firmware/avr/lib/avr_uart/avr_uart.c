#include "avr_uart.h"
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>

static volatile uint8_t s_rx_ring[AVR_UART_RX_RING_SIZE];
static volatile uint8_t s_rx_head;
static volatile uint8_t s_rx_tail;

ISR(USART_RXC_vect)
{
    uint8_t status = AVR_UART_UCSRA;
    uint8_t data = AVR_UART_UDR;

    if (status & ((1 << AVR_UART_FE) | (1 << AVR_UART_DOR) | (1 << AVR_UART_PE)))
        return;

    uint8_t next = (uint8_t)((s_rx_head + 1u) % AVR_UART_RX_RING_SIZE);
    if (next == s_rx_tail)
        return; /* overrun: drop */

    s_rx_ring[s_rx_head] = data;
    s_rx_head = next;
}

void avr_uart_init(uint32_t baud_rate, uint8_t data_bits, uint8_t stop_bits, char parity)
{
    uint16_t ubrr = (uint16_t)((F_CPU / (16UL * baud_rate)) - 1UL);

    s_rx_head = 0;
    s_rx_tail = 0;

    AVR_UART_UBRRH = (uint8_t)(ubrr >> 8);
    AVR_UART_UBRRL = (uint8_t)ubrr;

    uint8_t ucsrc = (1 << AVR_UART_URSEL);

    switch (data_bits) {
    case 5:
        break;
    case 6:
        ucsrc |= (1 << AVR_UART_UCSZ0);
        break;
    case 7:
        ucsrc |= (1 << AVR_UART_UCSZ1);
        break;
    case 9:
        ucsrc |= (1 << AVR_UART_UCSZ1) | (1 << AVR_UART_UCSZ0);
        AVR_UART_UCSRB |= (1 << UCSZ2);
        break;
    case 8:
    default:
        ucsrc |= (1 << AVR_UART_UCSZ1) | (1 << AVR_UART_UCSZ0);
        break;
    }

    switch (parity) {
    case 'E':
        ucsrc |= (1 << UPM1);
        break;
    case 'O':
        ucsrc |= (1 << UPM1) | (1 << UPM0);
        break;
    case 'N':
    default:
        break;
    }

    if (stop_bits == 2)
        ucsrc |= (1 << USBS);

    AVR_UART_UCSRC = ucsrc;
    AVR_UART_UCSRB = (1 << AVR_UART_RXEN) | (1 << AVR_UART_TXEN) | (1 << RXCIE);
}

void avr_uart_transmit_char(char data)
{
    while (!(AVR_UART_UCSRA & (1 << AVR_UART_UDRE)))
        ;
    AVR_UART_UDR = data;
}

void avr_uart_transmit_string(const char *str)
{
    if (!str)
        return;
    while (*str)
        avr_uart_transmit_char(*str++);
}

void avr_uart_transmit_pstr(const char *pstr)
{
    char c;
    if (!pstr)
        return;
    while ((c = (char)pgm_read_byte(pstr++)) != '\0')
        avr_uart_transmit_char(c);
}

void avr_uart_transmit_buffer(const uint8_t *buffer, uint16_t length)
{
    if (!buffer)
        return;
    for (uint16_t i = 0; i < length; i++)
        avr_uart_transmit_char((char)buffer[i]);
}

int16_t avr_uart_rx_pop(void)
{
    uint8_t head;
    uint8_t tail;
    uint8_t data;

    cli();
    head = s_rx_head;
    tail = s_rx_tail;
    if (head == tail) {
        sei();
        return -1;
    }
    data = s_rx_ring[tail];
    s_rx_tail = (uint8_t)((tail + 1u) % AVR_UART_RX_RING_SIZE);
    sei();
    return (int16_t)data;
}

uint8_t avr_uart_data_available(void)
{
    uint8_t head;
    uint8_t tail;

    cli();
    head = s_rx_head;
    tail = s_rx_tail;
    sei();

    if (head >= tail)
        return (uint8_t)(head - tail);
    return (uint8_t)(AVR_UART_RX_RING_SIZE - (tail - head));
}

void avr_uart_flush_rx(void)
{
    cli();
    s_rx_head = 0;
    s_rx_tail = 0;
    while (AVR_UART_UCSRA & (1 << AVR_UART_RXC)) {
        volatile uint8_t dummy = AVR_UART_UDR;
        (void)dummy;
    }
    sei();
}

void avr_uart_flush_tx(void)
{
    while (!(AVR_UART_UCSRA & (1 << AVR_UART_TXC)))
        ;
}

void avr_uart_set_baud_rate(uint32_t baud_rate)
{
    uint16_t ubrr = (uint16_t)((F_CPU / (16UL * baud_rate)) - 1UL);
    AVR_UART_UBRRH = (uint8_t)(ubrr >> 8);
    AVR_UART_UBRRL = (uint8_t)ubrr;
}
