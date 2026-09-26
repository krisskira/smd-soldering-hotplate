#include "safety.h"
#include "outputs.h"
#include "../app/app_config.h"
#include "lib/avr_uart/avr_uart.h"
#include <avr/pgmspace.h>

uint8_t safety_apply_limit(sensor_reading_t *reading, uint8_t *out_state)
{
    if (!reading || !out_state)
        return 0;

    if (!reading->valid)
        return 0;

    if (reading->temp_c_x10 < TEMP_LIMIT_X10)
        return 0;

    outputs_heaters_off(out_state);

    avr_uart_transmit_pstr(PSTR("ALARM:OVER-TEMP\r\n"));
    return 1;
}
