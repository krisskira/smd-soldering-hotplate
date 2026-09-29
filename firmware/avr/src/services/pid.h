#ifndef PID_H
#define PID_H

#include <stdint.h>
#include "../app/app_state.h"

#ifdef __cplusplus
extern "C" {
#endif

void pid_init(app_state_t *st);

/** Reset integrator / rate / window (start, stop, fault). */
void pid_reset(app_state_t *st);

/**
 * Nueva consigna de rampa: anula tasa fantasma y alinea t_ref a T.
 * Conserva el integral (bumpless entre etapas).
 */
void pid_on_set_step(app_state_t *st);

/**
 * Compute PI + lookahead from a new valid temperature sample.
 * Call once per TEMP_PERIOD_MS after sensor_tick when regulating.
 * Updates st->duty_pct and st->t_ref_x10.
 */
void pid_compute_sample(app_state_t *st);

/**
 * Apply time-proportioning window to heater bank.
 * Call every super-loop iteration while PID_AUTO is active.
 */
void pid_window_tick(app_state_t *st);

/** Combined tick: compute if sample-ready, always window. */
void pid_tick(app_state_t *st);

/** Mark that a fresh sensor sample is available for AUTO compute. */
void pid_notify_sample(void);

#ifdef __cplusplus
}
#endif

#endif
