#include "device_session.h"
#include "process.h"
#include "outputs.h"
#include "pid_atune.h"
#include "telemetry.h"
#include "proto_codes.h"

uint8_t device_session_is_busy(const app_state_t *st)
{
    uint8_t i;

    if (!st)
        return 1u;
    if (process_is_active(st))
        return 1u;
    if (pid_atune_active(st))
        return 1u;
    for (i = 0; i < OUTPUT_COUNT; i++) {
        if (st->out_state[i])
            return 1u;
    }
    return 0u;
}

void device_session_safe_stop(app_state_t *st, ctrl_src_t src)
{
    if (!st)
        return;
    if (pid_atune_active(st))
        pid_atune_cancel(st);
    process_stop(st, src);
    /* Apagar también la bomba: aborto de sesión = todo OFF. */
    output_set(st->out_state, OUT_FAN, 0);
    st->telem_dirty = 1u;
}

uint8_t device_session_enter_usb(app_state_t *st)
{
    if (!st)
        return 1u;
    if (st->device_mode == DEVICE_USB)
        return 0u;
    if (device_session_is_busy(st))
        return 1u;

    st->device_mode = DEVICE_USB;
    st->ctrl_src = CTRL_USB;
    st->telem_dirty = 1u;
    return 0u;
}

void device_session_leave_manual(app_state_t *st, uint8_t notify_abort)
{
    if (!st)
        return;

    device_session_safe_stop(st, notify_abort ? CTRL_UI : CTRL_USB);
    st->device_mode = DEVICE_MANUAL;
    st->ctrl_src = CTRL_NONE;
    st->telem_dirty = 1u;

    if (notify_abort)
        proto_emit_error((uint8_t)PROTO_ERR_ABORTED_BY_DEVICE);
}

uint8_t device_session_is_usb(const app_state_t *st)
{
    return (st && st->device_mode == DEVICE_USB) ? 1u : 0u;
}
