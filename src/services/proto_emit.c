#include "proto_codes.h"
#include "proto_tokens.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

void proto_put_u16(uint16_t v)
{
    char tmp[5];
    uint8_t i = 0;

    if (v >= 10000u) {
        avr_uart_transmit_pstr(PSTR("9999"));
        return;
    }
    if (v == 0) {
        avr_uart_transmit_char('0');
        return;
    }
    while (v > 0) {
        tmp[i++] = (char)('0' + (v % 10u));
        v /= 10u;
    }
    while (i > 0)
        avr_uart_transmit_char(tmp[--i]);
}

void proto_emit_error(uint8_t code)
{
    avr_uart_transmit_pstr(PSTR("ERROR:"));
    proto_put_u16(code);
    avr_uart_transmit_pstr(PROTO_CRLF);
}

void proto_emit_alarm(uint8_t code)
{
    avr_uart_transmit_pstr(PSTR("ALARM:"));
    proto_put_u16(code);
    avr_uart_transmit_pstr(PROTO_CRLF);
}
