#ifndef PROGRAM_H
#define PROGRAM_H

#include <stdint.h>
#include "../../app/app_state.h"

/* Result codes (compat with AT reply_from_proc) */
#define PROG_OK            0u
#define PROG_ERR_BUSY      1u
#define PROG_ERR_SENSOR    2u
#define PROG_ERR_OVERTEMP  3u
#define PROG_ERR_FAULT     4u
#define PROG_ERR_PARAM     5u

/* Legacy aliases */
#define PROC_OK            PROG_OK
#define PROC_ERR_BUSY      PROG_ERR_BUSY
#define PROC_ERR_SENSOR    PROG_ERR_SENSOR
#define PROC_ERR_OVERTEMP  PROG_ERR_OVERTEMP
#define PROC_ERR_FAULT     PROG_ERR_FAULT
#define PROC_ERR_PARAM     PROG_ERR_PARAM

/* Callback result for preheat pipeline (program_runner). */
#define PROG_CB_OK         0u
#define PROG_CB_FAULT      1u
#define PROG_CB_CANCEL     2u

typedef void (*prog_cb_t)(app_state_t *st, uint8_t result);

void program_init(app_state_t *st);
void program_tick(app_state_t *st);

/** Start currently selected `st->program` (params already in state). */
uint8_t program_start(app_state_t *st, ctrl_src_t src);

void program_stop(app_state_t *st, ctrl_src_t src);
void program_fault(app_state_t *st);

/**
 * PRESS durante PH_ALARM: cierra alarma.
 * PREHEAT → DONE; HEAT → sigue cooldown si hace falta.
 */
uint8_t program_user_ack(app_state_t *st);

uint8_t program_is_active(const app_state_t *st);

uint8_t program_set_output(app_state_t *st, uint8_t idx, uint8_t on,
                           ctrl_src_t src);
uint8_t program_set_bank(app_state_t *st, uint8_t on, ctrl_src_t src);

const char *program_phase_name(process_phase_t p);

/* Compat wrappers for existing call sites */
#define process_init        program_init
#define process_tick        program_tick
#define process_start       program_start
#define process_stop        program_stop
#define process_fault       program_fault
#define process_is_active   program_is_active
#define process_set_output  program_set_output
#define process_set_bank    program_set_bank
#define process_phase_name    program_phase_name

#endif
