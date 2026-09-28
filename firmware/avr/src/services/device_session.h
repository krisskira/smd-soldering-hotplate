#ifndef DEVICE_SESSION_H
#define DEVICE_SESSION_H

#include <stdint.h>
#include "../app/app_state.h"

/** 1 si hay proceso, autoajuste o alguna salida ON. */
uint8_t device_session_is_busy(const app_state_t *st);

/** Cancela proceso/autotune y apaga PTC + bomba. */
void device_session_safe_stop(app_state_t *st, ctrl_src_t src);

/**
 * Entra en DEVICE_USB. Requiere equipo libre.
 * Devuelve 0 OK, 1 DEVICE-BUSY.
 */
uint8_t device_session_enter_usb(app_state_t *st);

/**
 * Sale a DEVICE_MANUAL con parada segura.
 * notify_abort=1 → emite ERROR:ABORTED-BY-DEVICE (aborto local).
 */
void device_session_leave_manual(app_state_t *st, uint8_t notify_abort);

uint8_t device_session_is_usb(const app_state_t *st);

#endif
