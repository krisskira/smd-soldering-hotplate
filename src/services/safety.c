#include "safety.h"
#include "outputs.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

uint8_t safety_apply_limit(app_state_t *st)
{
    int16_t lim;

    if (!st || !st->sensor.valid)
        return 0;

    lim = (int16_t)(st->temp_max_c * 10);
    if (st->sensor.temp_c_x10 < lim)
        return 0;

    outputs_heaters_off(st->out_state);
    avr_uart_transmit_pstr(PSTR("OT\r\n"));
    return 1;
}
