#ifndef HOST_STUBS_H
#define HOST_STUBS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

void host_set_ms(uint16_t ms);
void host_advance_ms(uint16_t dt);

#ifdef __cplusplus
}
#endif

#endif
