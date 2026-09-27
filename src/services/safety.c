#include "safety.h"
#include "outputs.h"
#include "proto_codes.h"

uint8_t safety_apply_limit(app_state_t *st)
{
    int16_t lim;

    if (!st || !st->sensor.valid)
        return 0;

    lim = (int16_t)(st->temp_max_c * 10);
    if (st->sensor.temp_c_x10 < lim)
        return 0;

    outputs_heaters_off(st->out_state);
    proto_emit_error((uint8_t)PROTO_ERR_OVER_TEMPERATURE);
    return 1;
}
