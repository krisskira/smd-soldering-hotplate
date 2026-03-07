#ifndef AVR_DELAY_H
#define AVR_DELAY_H

#include <stdint.h>

/**
 * Sistema de delays basado en interrupciones por timer (estilo Arduino millis).
 * Tres contadores independientes para optimizar tamaño de variables:
 * - delay_ms(): milisegundos (uint16_t, wrap ~65 s)
 * - delay_sec(): segundos (uint16_t, wrap ~18 h)
 * - delay_min(): minutos (uint8_t, wrap 256 min)
 *
 * Ejemplos (no bloqueantes):
 *
 *   // Cada 100 ms (p. ej. refresco de animación)
 *   uint16_t t_ms = delay_ms();
 *   if ((uint16_t)(delay_ms() - t_ms) >= 100) { ...; t_ms = delay_ms(); }
 *
 *   // Cada 2 segundos (p. ej. actualizar texto en pantalla)
 *   uint16_t t_sec = delay_sec();
 *   if ((uint16_t)(delay_sec() - t_sec) >= 2) { ...; t_sec = delay_sec(); }
 *
 *   // Cada 1 minuto (p. ej. log o lectura de sensor)
 *   uint8_t t_min = delay_min();
 *   if ((uint8_t)(delay_min() - t_min) >= 1) { ...; t_min = delay_min(); }
 *
 * Requiere llamar delay_init() una vez tras configurar el sistema.
 */

/** Inicializa el timer (Timer0) y habilita el contador de ticks. Llamar una vez al inicio. */
void delay_init(void);

/**
 * Devuelve el contador de milisegundos desde delay_init().
 * Tipo uint16_t: hace wrap cada 65535 ms (~65 s). Para intervalos mayores usar delay_sec() o delay_min().
 */
uint16_t delay_ms(void);

/**
 * Devuelve el contador de segundos desde delay_init().
 * Tipo uint16_t: wrap cada 65535 s.
 */
uint16_t delay_sec(void);

/**
 * Devuelve el contador de minutos desde delay_init().
 * Tipo uint8_t: wrap cada 256 min. Óptimo para intervalos de minutos.
 */
uint8_t delay_min(void);

#endif /* AVR_DELAY_H */
