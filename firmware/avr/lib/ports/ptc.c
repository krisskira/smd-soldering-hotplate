#include "../../config/board_pins.h"
#include <avr/io.h>
#include <stdint.h>

void ptc_init(void)
{
    PTC1_DDR |= (1 << PTC1_PIN);
    PTC2_DDR |= (1 << PTC2_PIN);
    PTC1_PORT &= ~(1 << PTC1_PIN);
    PTC2_PORT &= ~(1 << PTC2_PIN);
}

void ptc_on(void)
{
    PTC1_PORT |= (1 << PTC1_PIN);
    PTC2_PORT |= (1 << PTC2_PIN);
}

void ptc_off(void)
{
    PTC1_PORT &= ~(1 << PTC1_PIN);
    PTC2_PORT &= ~(1 << PTC2_PIN);
}

void ptc1_on(void)
{
    PTC1_PORT |= (1 << PTC1_PIN);
}

void ptc1_off(void)
{
    PTC1_PORT &= ~(1 << PTC1_PIN);
}

void ptc2_on(void)
{
    PTC2_PORT |= (1 << PTC2_PIN);
}

void ptc2_off(void)
{
    PTC2_PORT &= ~(1 << PTC2_PIN);
}
