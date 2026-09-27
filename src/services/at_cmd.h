#ifndef AT_CMD_H
#define AT_CMD_H

#include "../app/app_state.h"

void at_cmd_init(void);
void at_cmd_set_stream(app_state_t *st, uint8_t on);
void at_cmd_tick(app_state_t *st);

#endif
