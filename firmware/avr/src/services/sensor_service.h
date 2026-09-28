#ifndef SENSOR_SERVICE_H
#define SENSOR_SERVICE_H

#include "../app/app_state.h"

void sensor_init(void);
void sensor_tick(sensor_reading_t *out);

#endif
