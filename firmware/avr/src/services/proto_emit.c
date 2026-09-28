#include "proto_codes.h"
#include "proto_tokens.h"
#include "ui/core/ui_digits.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

void proto_put_u16(uint16_t v)
{
    char tmp[5];
    uint8_t n, i;

    if (v == 0u) {
        avr_uart_transmit_char('0');
        return;
    }
    n = ui_u16_digits(v, tmp);
    for (i = 0; i < n; i++)
        avr_uart_transmit_char(tmp[i]);
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
