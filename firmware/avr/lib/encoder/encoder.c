/*
 * Encoder rotatorio + pulsador. Lectura por polling, sin interrupciones.
 * Algoritmo de transiciones AB con tabla de delta y acumulador para
 * emitir un click por cada 4 transiciones (encoder mecánico estándar).
 *
 * Semántica de retorno (configurable con ENC_CW_IS_POSITIVE):
 *   +1 = sentido horario → cursor baja en el menú
 *   -1 = sentido antihorario → cursor sube
 */

#include "encoder.h"
#include "../../config/board_pins.h"
#include "../avr_delay/avr_delay.h"
#include <avr/io.h>
#include <avr/pgmspace.h>

#define ENC_DEBOUNCE_MS  30

/* Tabla [prev<<2 | cur] -> delta. Solo +1 / -1 / 0. */
static const int8_t enc_delta_table[16] PROGMEM = {
     0, -1,  1,  0,
     1,  0,  0, -1,
    -1,  0,  0,  1,
     0,  1, -1,  0
};

void encoder_init(void)
{
    ENC_DDR  &= ~((1 << ENC_A) | (1 << ENC_B) | (1 << ENC_SW));
    ENC_PORT |=  (1 << ENC_A) | (1 << ENC_B) | (1 << ENC_SW);
}

int8_t encoder_poll(void)
{
    static uint8_t prev_state = 0x03;
    static int8_t  accum = 0;

    uint8_t cur = ((ENC_PINR >> ENC_A) & 0x01) |
                  (((ENC_PINR >> ENC_B) & 0x01) << 1);

    int8_t d = (int8_t)pgm_read_byte(&enc_delta_table[(prev_state << 2) | cur]);
    prev_state = cur;

#if ENC_CW_IS_POSITIVE
    /* Invertir el signo de la tabla: la mecánica actual hace que CW
     * produzca deltas negativos en la tabla estándar. */
    d = (int8_t)(-d);
#endif

    accum += d;

    if (accum >= 4)  { accum = 0; return  1; }
    if (accum <= -4) { accum = 0; return -1; }
    return 0;
}

uint8_t encoder_button_pressed(void)
{
    static uint8_t  last_stable = 1;
    static uint8_t  pending = 1;
    static uint16_t pending_since_ms = 0;

    uint8_t raw = (ENC_PINR >> ENC_SW) & 0x01;
    uint16_t now = delay_ms();

    if (raw != pending) {
        pending = raw;
        pending_since_ms = now;
        return 0;
    }

    if ((uint16_t)(now - pending_since_ms) >= ENC_DEBOUNCE_MS &&
        pending != last_stable)
    {
        last_stable = pending;
        if (last_stable == 0)
            return 1;
    }
    return 0;
}
