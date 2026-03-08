#include <avr/io.h>
#include <stdint.h>

#define PTC1_PORT PORTD
#define PTC1_DDR  DDRD
#define PTC1_PIN  PD6

#define PTC2_PORT PORTD
#define PTC2_DDR  DDRD
#define PTC2_PIN  PD7


void ptc_init(void) {
    PTC1_DDR |= (1 << PTC1_PIN);
    PTC2_DDR |= (1 << PTC2_PIN);
    PTC1_PORT &= ~(1 << PTC1_PIN);
    PTC2_PORT &= ~(1 << PTC2_PIN);
}

void ptc_on(void) {
    PTC1_PORT |= (1 << PTC1_PIN);
    PTC2_PORT |= (1 << PTC2_PIN);
}

void ptc_off(void) {
    PTC1_PORT &= ~(1 << PTC1_PIN);
    PTC2_PORT &= ~(1 << PTC2_PIN);
}

void ptc1_on(void) {
    PTC1_PORT |= (1 << PTC1_PIN);
}

void ptc1_off(void) {   
    PTC1_PORT &= ~(1 << PTC1_PIN);
}

void ptc2_on(void) {
    PTC2_PORT |= (1 << PTC2_PIN);
}

void ptc2_off(void) {
    PTC2_PORT &= ~(1 << PTC2_PIN);
}
