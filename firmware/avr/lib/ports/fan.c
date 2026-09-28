/*
 * Bomba de aire / ventilador.
 * Señal FAN del esquemático → PC0 (pin 22), va a la etapa de potencia (P_FAN).
 */
#include "../../config/board_pins.h"
#include <avr/io.h>
#include <stdint.h>

void fan_init(void)
{
    FAN_DDR |= (1 << FAN_PIN);
    FAN_PORT &= ~(1 << FAN_PIN);
}

void fan_on(void)
{
    FAN_PORT |= (1 << FAN_PIN);
}

void fan_off(void)
{
    FAN_PORT &= ~(1 << FAN_PIN);
}

void fan_toggle(void)
{
    FAN_PORT ^= (1 << FAN_PIN);
}
