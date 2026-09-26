#ifndef CFG_STORE_H
#define CFG_STORE_H

#include <stdint.h>
#include "../app/app_state.h"

/** Load global settings at boot. Returns 1 if EEPROM valid. */
uint8_t cfg_load_global(app_state_t *st);

/** Load per-program parameters into state (lazy). */
void cfg_load_program(app_state_t *st, program_id_t prog);

/** Persist global block from state. */
void cfg_save_global(const app_state_t *st);

/** Persist active program parameters. */
void cfg_save_program(const app_state_t *st, program_id_t prog);

/** Load / save perfil de rampas (no es program_id lanzable). */
void cfg_load_ramps(app_state_t *st);
void cfg_save_ramps(const app_state_t *st);

/** Apply factory defaults (no EEPROM write). */
void cfg_store_defaults(app_state_t *st);

/* Compat */
#define cfg_store_load(st)   cfg_load_global(st)
#define cfg_store_save(st)   cfg_save_global(st)

#endif
