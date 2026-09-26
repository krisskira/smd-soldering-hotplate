#ifndef ENCODER_H
#define ENCODER_H

#include <stdint.h>

/*
 * Encoder rotatorio incremental + pulsador (KY-040 estilo).
 * Pines (config/board_pins.h):
 *   ENC_A  = PD2 (CLK)
 *   ENC_B  = PD3 (DT)
 *   ENC_SW = PD4 (pulsador, activo bajo)
 *
 * Lectura por polling. No usa interrupciones.
 *
 * Semántica de encoder_poll() (ENC_CW_IS_POSITIVE = 1):
 *   +1 = sentido horario   → cursor baja en el menú
 *   -1 = sentido antihorario → cursor sube
 *   0  = sin cambio
 *
 * encoder_button_pressed() devuelve 1 una sola vez por pulsación
 * (flanco descendente con debounce de ~30 ms). Requiere delay_init().
 */

void encoder_init(void);

/** Devuelve -1 (CCW), 0 (sin cambio) o +1 (CW). Llamar a menudo. */
int8_t encoder_poll(void);

/** Devuelve 1 una vez en el flanco de pulsación (debounced). Requiere
 * que avr_delay esté inicializado (delay_init()). */
uint8_t encoder_button_pressed(void);

#endif /* ENCODER_H */
