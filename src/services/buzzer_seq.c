#include "buzzer_seq.h"
#include "../app/app_config.h"
#include "lib/ports/ports.h"
#include "lib/avr_delay/avr_delay.h"

static uint8_t  buzz_remaining;
static uint8_t  buzz_is_on;
static uint16_t buzz_next_ms;
static uint16_t buzz_on_ms;
static uint16_t buzz_off_ms;
static app_state_t *s_st;

void buzzer_seq_init(void)
{
    buzzer_init();
    buzz_remaining = 0;
    buzz_is_on = 0;
    buzz_on_ms = BEEP_ON_MS;
    buzz_off_ms = BEEP_OFF_MS;
    s_st = 0;
}

void buzzer_seq_bind(app_state_t *st)
{
    s_st = st;
}

void buzzer_seq_beep_cat(app_state_t *st, beep_cat_t cat, uint8_t count)
{
    if (count == 0)
        return;

    if (cat == BEEP_NAV) {
        if (st && !st->buzz_nav_en)
            return;
        if (st && st->buzz_nav_reps)
            count = st->buzz_nav_reps;
        buzz_on_ms = BEEP_ON_MS;
        buzz_off_ms = BEEP_OFF_MS;
    } else if (cat == BEEP_ALARM) {
        /* Never mute alarms */
        buzz_on_ms = BEEP_ALERT_ON_MS;
        buzz_off_ms = BEEP_ALERT_OFF_MS;
    } else if (cat == BEEP_READY) {
        buzz_on_ms = BEEP_ALERT_ON_MS;
        buzz_off_ms = BEEP_ALERT_OFF_MS;
        if (count < 3u)
            count = 3;
    } else {
        buzz_on_ms = BEEP_ON_MS;
        buzz_off_ms = BEEP_OFF_MS;
    }

    buzz_remaining = count;
    buzz_is_on = 1;
    buzzer_on();
    buzz_next_ms = (uint16_t)(delay_ms() + buzz_on_ms);
}

void buzzer_seq_beep(uint8_t count)
{
    /* Heuristic: 1 = nav, 2 = confirm, 4+ = alarm */
    if (count >= 4u)
        buzzer_seq_beep_cat(s_st, BEEP_ALARM, count);
    else if (count >= 2u)
        buzzer_seq_beep_cat(s_st, BEEP_CONFIRM, count);
    else
        buzzer_seq_beep_cat(s_st, BEEP_NAV, count);
}

void buzzer_seq_tick(void)
{
    if (buzz_remaining == 0 && !buzz_is_on)
        return;

    int16_t dt = (int16_t)((uint16_t)delay_ms() - buzz_next_ms);
    if (dt < 0)
        return;

    if (buzz_is_on) {
        buzzer_off();
        buzz_is_on = 0;
        buzz_remaining--;
        if (buzz_remaining > 0)
            buzz_next_ms = (uint16_t)(delay_ms() + buzz_off_ms);
    } else {
        buzzer_on();
        buzz_is_on = 1;
        buzz_next_ms = (uint16_t)(delay_ms() + buzz_on_ms);
    }
}
