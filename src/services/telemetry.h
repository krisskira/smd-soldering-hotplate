#ifndef TELEMETRY_H
#define TELEMETRY_H

#include "../app/app_state.h"

/** Emite una trama $HP completa (request o evento). */
void telemetry_emit(const app_state_t *st);

/** Si telem_dirty, emite y limpia el flag. Sin rate periódico. */
void telemetry_tick(const app_state_t *st);

/**
 * Muestra de gráfico a 1 Hz, solo con autotune en curso (`ATUNE_RUN`)
 * y sesión USB. Emite `$HP,PLOT,T,SET,DUTY,HHI,HLO,PKH,PKL`.
 * Entrar a USB, u otro programa, no emite esta trama.
 */
void telemetry_plot(const app_state_t *st);

#endif
