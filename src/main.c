/*
 * Firmware único: HOME (solo Modo USB) + sesión AT + sensor + PID.
 * Entrada USB: menú HOME o AT+DEVICEMODE=USB. Ver doc/usb-automation.md.
 */

#include <avr/io.h>
#include <stdint.h>

#include "app/app_config.h"
#include "app/app_state.h"
#include "services/outputs.h"
#include "services/buzzer_seq.h"
#include "services/process.h"
#include "services/cfg_store.h"
#include "services/pid.h"
#include "services/pid_atune.h"
#include "services/sensor_service.h"
#include "services/safety.h"
#include "services/at_cmd.h"
#include "services/telemetry.h"
#include "services/device_session.h"
#include "ui/ui_router.h"

#include "lib/avr_spi/avr_spi.h"
#include "lib/avr_delay/avr_delay.h"
#include "lib/avr_uart/avr_uart.h"
#include "lib/st7920/st7920.h"
#include "lib/encoder/encoder.h"
#include "lib/ports/ports.h"

static app_state_t g_state;
static process_phase_t s_prev_phase;
static atune_phase_t s_prev_atune;
static uint8_t s_plot_due;

int main(void)
{
    avr_spi_master_init(SPI_DIV_8);
    st7920_init();
    st7920_graphics_mode();
    avr_uart_init(9600, 8, 1, 'N');
    delay_init();
    encoder_init();

    outputs_init();
    buzzer_seq_init();
    sensor_init();
    process_init(&g_state);
    cfg_load_global(&g_state);
    buzzer_seq_bind(&g_state);
    at_cmd_init();
    s_prev_phase = PH_IDLE;
    s_prev_atune = ATUNE_IDLE;

    ptc_off();
    fan_off();
    outputs_set_quiet(1u);

    avr_uart_transmit_string("\r\nSMI HP\r\n");

    sensor_tick(&g_state.sensor);
    ui_router_init(&g_state);

    {
        uint16_t t_sensor = delay_ms();

        for (;;) {
            ui_router_refresh(&g_state);

            {
                int8_t enc = encoder_poll();
                if (enc > 0)
                    ui_router_on_event(&g_state, EVT_ENCODER_NEXT);
                else if (enc < 0)
                    ui_router_on_event(&g_state, EVT_ENCODER_PREV);
            }

            if (encoder_button_pressed())
                ui_router_on_event(&g_state, EVT_PRESS);

            at_cmd_tick(&g_state);

            {
                uint16_t now = delay_ms();
                if ((uint16_t)(now - t_sensor) >= TEMP_PERIOD_MS) {
                    t_sensor = now;

                    sensor_tick(&g_state.sensor);
                    pid_notify_sample();

                    if (pid_atune_active(&g_state))
                        pid_atune_on_sample(&g_state);

                    if (safety_apply_limit(&g_state.sensor, g_state.out_state)) {
                        process_fault(&g_state);
                        g_state.telem_dirty = 1u;
                    }

                    telemetry_tick(&g_state);
                    if (device_session_is_usb(&g_state)
                        && pid_atune_active(&g_state))
                        s_plot_due = 1u;
                    ui_router_on_sensor_update(&g_state);

                    if (g_state.phase == PH_HOLD && s_prev_phase != PH_HOLD)
                        buzzer_seq_beep_cat(&g_state, BEEP_READY, 3);
                    if (g_state.phase == PH_ALARM && s_prev_phase != PH_ALARM)
                        buzzer_seq_beep_cat(&g_state, BEEP_READY, 3);
                    if (g_state.phase == PH_DONE && s_prev_phase != PH_DONE)
                        buzzer_seq_beep_cat(&g_state, BEEP_READY, 2);
                    if (g_state.atune_phase != s_prev_atune)
                        g_state.telem_dirty = 1u;

                    s_prev_phase = g_state.phase;
                    s_prev_atune = g_state.atune_phase;
                }
            }

            process_tick(&g_state);
            if (s_plot_due) {
                s_plot_due = 0;
                telemetry_plot(&g_state);
            }
            if (g_state.telem_dirty)
                telemetry_tick(&g_state);
            buzzer_seq_tick();
        }
    }
}
