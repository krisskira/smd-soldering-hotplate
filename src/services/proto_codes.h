#ifndef PROTO_CODES_H
#define PROTO_CODES_H

#include <stdint.h>

/*
 * Códigos UART numéricos. Nombres largos solo en doc/usb-automation.md.
 * ACTION 0..9 = process_phase_t; 10 = TUNING (ATUNE_RUN).
 * PROGRAM = program_id_t.
 */

typedef enum {
    PROTO_ERR_INVALID_COMMAND = 1,
    PROTO_ERR_INVALID_PARAMETER = 2,
    PROTO_ERR_USB_MODE_REQUIRED = 3,
    PROTO_ERR_DEVICE_BUSY = 4,
    PROTO_ERR_PROGRAM_BUSY = 5,
    PROTO_ERR_SENSOR_INVALID = 6,
    PROTO_ERR_OVER_TEMPERATURE = 7,
    PROTO_ERR_ABORTED_BY_DEVICE = 8
} proto_err_t;

typedef enum {
    PROTO_ALARM_PH_OK = 1,
    PROTO_ALARM_DONE = 2
} proto_alarm_t;

#define PROTO_ACTION_TUNING  10u

void proto_put_u16(uint16_t v);
void proto_emit_error(uint8_t code);
void proto_emit_alarm(uint8_t code);

#endif
