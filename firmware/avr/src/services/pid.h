#ifndef PID_H
#define PID_H

#include <stdint.h>
#include "../app/app_state.h"

void pid_init(app_state_t *st);

/** Reset integrator / window (on start/stop). */
void pid_reset(app_state_t *st);

/**
 * Compute P/I/D from a new valid temperature sample.
 * Call once per TEMP_PERIOD_MS after sensor_tick when regulating.
 * Updates st->duty_pct only (does not drive outputs).
 */
void pid_compute_sample(app_state_t *st);

/**
 * Apply time-proportioning window to heater bank.
 * Call every super-loop iteration while PID_MAN or PID_AUTO is active.
 */
void pid_window_tick(app_state_t *st);

/**
 * Legacy combined tick: compute if sample-ready flag, always window.
 * Prefer calling compute + window separately from main/process.
 */
void pid_tick(app_state_t *st);

/** Mark that a fresh sensor sample is available for AUTO compute. */
void pid_notify_sample(void);

#endif
