#ifndef BUZZER_SEQ_H
#define BUZZER_SEQ_H

#include <stdint.h>
#include "../app/app_state.h"

typedef enum {
    BEEP_NAV = 0,
    BEEP_CONFIRM,
    BEEP_READY,
    BEEP_ALARM
} beep_cat_t;

void buzzer_seq_init(void);

/** Beep with category; NAV respects buzz_nav_en / reps from state. */
void buzzer_seq_beep_cat(app_state_t *st, beep_cat_t cat, uint8_t count);

/** Legacy: treated as NAV if st known via last pointer, else always plays. */
void buzzer_seq_beep(uint8_t count);

void buzzer_seq_tick(void);

/** Bind state pointer for legacy beep() nav gating (call after init). */
void buzzer_seq_bind(app_state_t *st);

#endif
