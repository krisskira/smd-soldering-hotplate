#ifndef TELEMETRY_H
#define TELEMETRY_H

#include "../app/app_state.h"

/** Trama de proceso $HP. Si atune_stream, añade AP/AC/AK/AI. */
void telemetry_emit(const app_state_t *st);

/** Trama de settings $CF. Solo bajo demanda (AT+CFG?). */
void telemetry_emit_cfg(const app_state_t *st);

/** Trama de escalones $R. Solo bajo demanda (AT+CFG=R?). */
void telemetry_emit_ramps(const app_state_t *st);

/** Si telem_dirty, emite y limpia el flag. Sin rate periódico. */
void telemetry_tick(const app_state_t *st);

#endif
