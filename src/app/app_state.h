#ifndef APP_STATE_H
#define APP_STATE_H

#include <stdint.h>
#include "app_config.h"

typedef enum {
    VIEW_HOME = 0,
    VIEW_USB,
    VIEW_SETTINGS
} view_t;

typedef enum {
    EVT_NONE = 0,
    EVT_ENCODER_NEXT,
    EVT_ENCODER_PREV,
    EVT_PRESS,
    EVT_SENSOR_UPDATED,
    EVT_SAFETY_TRIP,
    EVT_PROCESS_CHANGED
} app_event_t;

typedef enum {
    PH_IDLE = 0,
    PH_DELAY,
    PH_PREHEAT,
    PH_STABILIZE,
    PH_HOLD,
    PH_RUN,
    PH_COOLDOWN,
    PH_ALARM,
    PH_DONE,
    PH_FAULT
} process_phase_t;

typedef enum {
    PID_OFF = 0,
    PID_MAN,
    PID_AUTO
} pid_loop_t;

typedef enum {
    CTRL_NONE = 0,
    CTRL_UI,
    CTRL_USB
} ctrl_src_t;

typedef enum {
    DEVICE_MANUAL = 0,
    DEVICE_USB
} device_mode_t;

/* Lanzables: HEAT, PREHEAT, PID_TUNE. RAMPS no es program_id_t. */
typedef enum {
    PROG_PREHEAT = 0,
    PROG_HEAT,
    PROG_PID_TUNE
} program_id_t;

typedef enum {
    ATUNE_IDLE = 0,
    ATUNE_RUN,
    ATUNE_DONE,
    ATUNE_FAIL
} atune_phase_t;

typedef struct {
    int16_t  temp_c_x10;
    uint16_t rtd_adc;
    uint8_t  fault;
    uint8_t  valid;
} sensor_reading_t;

typedef struct {
    uint16_t temp_c;
    uint16_t hold_s;
} ramp_step_t;

typedef struct {
    view_t   view;
    view_t   prev_view;
    uint8_t  out_state[OUTPUT_COUNT];
    uint8_t  frame_dirty;
    uint8_t  row_dirty;
    sensor_reading_t sensor;

    uint8_t  home_sel;
    uint8_t  home_page;
    uint8_t  settings_sel;
    uint8_t  settings_page;
    uint8_t  usb_sel;
    uint8_t  edit_armed;

    program_id_t    program;
    process_phase_t phase;
    uint16_t        t_set_c;
    uint16_t        t_remain_s;
    uint16_t        t_elapsed_s;
    uint16_t        delay_s;       /* HEAT: 0 = inmediato */
    uint8_t         duty_pct;
    uint8_t         preheat_en;    /* 0 = HEAT salta PREHEAT→STABILIZE */
    uint8_t         preheat_pct;   /* 50..100, tope = pct% de T(Ramp1) */
    uint8_t         ramps_en;
    uint16_t        stabilize_s;
    uint16_t        stabilize_left;

    uint8_t         ramp_n;
    uint8_t         ramp_idx;
    ramp_step_t     ramp_step[RAMP_STEPS_MAX];

    uint16_t        alarm_duration_s;
    uint16_t        alarm_period_s;
    uint16_t        alarm_left_s;
    uint16_t        alarm_beep_left_s;
    uint8_t         alarm_hold_heat;
    uint8_t         cooldown_air_en;
    uint16_t        temp_min_c;    /* piso consignas + OFF aire */
    uint16_t        temp_max_c;    /* techo + safety */

    device_mode_t   device_mode;
    uint8_t         telem_dirty;

    int16_t    pid_kp_x10;
    int16_t    pid_ki_x10;
    int16_t    pid_kd_x10;
    pid_loop_t pid_loop;

    atune_phase_t atune_phase;
    uint8_t       atune_cycles;
    uint8_t       atune_cycles_target;
    int16_t       atune_hyst_c_x10;
    uint8_t       atune_relay_on;
    uint16_t      atune_elapsed_s;
    int16_t       atune_kp_x10;
    int16_t       atune_ki_x10;
    int16_t       atune_kd_x10;
    int16_t       atune_peak_hi_x10;
    int16_t       atune_peak_lo_x10;
    uint8_t       atune_stream;    /* 1 = $HP a 1 Hz (solo lanzado por USB) */

    uint8_t    buzz_nav_en;
    uint8_t    buzz_nav_reps;
    uint8_t    usb_last_ok;
    ctrl_src_t ctrl_src;
} app_state_t;

typedef program_id_t usb_program_t;

#endif
