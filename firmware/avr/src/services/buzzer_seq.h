#ifndef BUZZER_SEQ_H
#define BUZZER_SEQ_H

#include <stdint.h>

typedef enum {
    BEEP_CONFIRM = 0, /* 1 pulso corto: un valor quedó en EEPROM */
    BEEP_READY,
    BEEP_ALARM
} beep_cat_t;

void buzzer_seq_init(void);

/** CONFIRM: pulso corto. READY/ALARM: pulso largo (READY ≥ 3). */
void buzzer_seq_beep_cat(beep_cat_t cat, uint8_t count);

void buzzer_seq_tick(void);

#endif
