#include <avr/io.h>
#include <stdint.h>

#define BUZZER_PORT PORTD
#define BUZZER_DDR  DDRD
#define BUZZER_PIN  PD5

void buzzer_init(void) {
    BUZZER_DDR |= (1 << BUZZER_PIN);
    BUZZER_PORT &= ~(1 << BUZZER_PIN);
}

void buzzer_on(void) {
    BUZZER_PORT |= (1 << BUZZER_PIN);
}

void buzzer_off(void) {
    BUZZER_PORT &= ~(1 << BUZZER_PIN);
}

void buzzer_toggle(void) {
    BUZZER_PORT ^= (1 << BUZZER_PIN);
}