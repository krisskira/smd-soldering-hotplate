#ifndef PID_ATUNE_H
#define PID_ATUNE_H

#include <stdint.h>
#include "../app/app_state.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifdef NO_PID_ATUNE

static inline void pid_atune_init(app_state_t *st)
{
    if (st)
        st->atune_phase = ATUNE_IDLE;
}
static inline uint8_t pid_atune_start(app_state_t *st)
{
    (void)st;
    return 1u;
}
static inline void pid_atune_cancel(app_state_t *st)
{
    if (st)
        st->atune_phase = ATUNE_IDLE;
}
static inline uint8_t pid_atune_active(const app_state_t *st)
{
    (void)st;
    return 0;
}
static inline void pid_atune_on_sample(app_state_t *st) { (void)st; }
static inline void pid_atune_apply(app_state_t *st) { (void)st; }

#else

void pid_atune_init(app_state_t *st);
/* 0 = entró en ATUNE_RUN; 1 = rechazado (sensor/rango). */
uint8_t pid_atune_start(app_state_t *st);
void pid_atune_cancel(app_state_t *st);
uint8_t pid_atune_active(const app_state_t *st);
void pid_atune_on_sample(app_state_t *st);
void pid_atune_apply(app_state_t *st);

#endif

#ifdef __cplusplus
}
#endif

#endif
