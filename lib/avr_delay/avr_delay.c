/*
 * AVR Delay - Temporización no bloqueante basada en Timer0 (interrupción).
 * Contadores: ms (uint16_t), sec (uint16_t), min (uint8_t).
 * F_CPU debe estar definido (ej. 4000000UL). Timer0 en modo CTC, tick 1 ms.
 */
#include "avr_delay.h"
#include <avr/io.h>
#include <avr/interrupt.h>

/* Contadores actualizados en ISR. Tamaños elegidos para reducir RAM. */
static volatile uint16_t ticks_ms;
static volatile uint16_t ticks_sec;
static volatile uint8_t ticks_min;
/* Contadores descendentes para evitar módulo en ISR */
static volatile uint16_t ms_until_sec;
static volatile uint8_t sec_until_min;

/* F_CPU 4 MHz, prescaler 64 -> tick = 16 us. 1 ms = 62.5 ticks. Usamos 62 -> 992 us. */
#define TICK_MS_COUNT  62

ISR(TIMER0_COMP_vect)
{
    ticks_ms++;
    if (--ms_until_sec == 0)
    {
        ms_until_sec = 1000;
        ticks_sec++;
        if (--sec_until_min == 0)
        {
            sec_until_min = 60;
            ticks_min++;
        }
    }
}

void delay_init(void)
{
    ticks_ms = 0;
    ticks_sec = 0;
    ticks_min = 0;
    ms_until_sec = 1000;
    sec_until_min = 60;

    TCCR0 = 0;
    TCNT0 = 0;
    OCR0 = (uint8_t)(TICK_MS_COUNT - 1);   /* CTC: cuenta 0..OCR0, luego resetea */
    TCCR0 = (1 << WGM01) | (1 << CS01) | (1 << CS00);  /* CTC, prescaler 64 */
    TIMSK |= (1 << OCIE0);
    sei();
}

uint16_t delay_ms(void)
{
    return ticks_ms;
}

uint16_t delay_sec(void)
{
    return ticks_sec;
}

uint8_t delay_min(void)
{
    return ticks_min;
}
