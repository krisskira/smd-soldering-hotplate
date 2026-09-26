#ifndef APP_STATE_H
#define APP_STATE_H

#include <stdint.h>
#include "app_config.h"

/* View: HOME, MODO USB y Ajustes. */
typedef enum {
    VIEW_HOME = 0,
    VIEW_USB,
    VIEW_SETTINGS
} view_t;

/* App event */
typedef enum {
    EVT_NONE = 0,
    EVT_ENCODER_NEXT,
    EVT_ENCODER_PREV,
    EVT_PRESS,
    EVT_SENSOR_UPDATED,
    EVT_SAFETY_TRIP,
    EVT_PROCESS_CHANGED
} app_event_t;

/* Program phase (shared across runners) */
typedef enum {
    PH_IDLE = 0,
    PH_DELAY,
    PH_PREHEAT,
    PH_STABILIZE,
    PH_HOLD,             /* PID hold / run hasta STOP */
    PH_RUN,              /* timed hold (STOP_IN / rampa escalón) */
    PH_COOLDOWN,         /* aire hasta cooldown_target_c */
    PH_ALARM,            /* beep post-preheat standalone */
    PH_DONE,
    PH_FAULT
} process_phase_t;

/* PID loop */
typedef enum {
    PID_OFF = 0,
    PID_MAN,
    PID_AUTO
} pid_loop_t;

/* Control source */
typedef enum {
    CTRL_NONE = 0,
    CTRL_UI,
    CTRL_USB
} ctrl_src_t;

/* Device operating mode (mutually exclusive session) */
typedef enum {
    DEVICE_MANUAL = 0,   /* local UI / encoder */
    DEVICE_USB           /* remote AT session */
} device_mode_t;

/* Launchable programs (RAMPS no es lanzable: solo perfil EEPROM) */
typedef enum {
    PROG_PREHEAT = 0,
    PROG_START_IN,
    PROG_STOP_IN,
    PROG_PID_TUNE
} program_id_t;

/* Autotune phase */
typedef enum {
    ATUNE_IDLE = 0,
    ATUNE_RUN,
    ATUNE_DONE,
    ATUNE_FAIL
} atune_phase_t;

/* Sensor reading */
typedef struct {
    int16_t  temp_c_x10;     /* °C × 10 */
    uint16_t rtd_adc;
    uint8_t  fault;          /* MAX31865 fault status */
    uint8_t  valid;          /* 1 = lectura usable */
} sensor_reading_t;

/* One RAMPS step */
typedef struct {
    uint16_t temp_c;
    uint16_t hold_s;
} ramp_step_t;

/* App state */
typedef struct {
    view_t   view;
    view_t   prev_view;
    uint8_t  out_state[OUTPUT_COUNT];
    uint8_t  frame_dirty;
    uint8_t  row_dirty;
    sensor_reading_t sensor;

    /* UI selection */
    uint8_t  home_sel;
    uint8_t  home_page;      /* HOME_PAGE_* */
    uint8_t  settings_sel;   /* == número de ítems: foco en el pie */
    uint8_t  settings_page;  /* SET_PAGE_* */
    uint8_t  usb_sel;
    uint8_t  edit_armed;     /* Ajustes: SET_EDIT_* del escalón en edición */

    /* Active program */
    program_id_t    program;
    process_phase_t phase;
    uint16_t        t_set_c;       /* 30..200 active setpoint */
    uint16_t        t_remain_s;    /* live countdown */
    uint16_t        t_elapsed_s;   /* segundos desde process_start */
    uint16_t        delay_s;       /* START_IN delay / STOP_IN run_s */
    uint16_t        run_s;         /* STOP_IN hold duration */
    uint8_t         duty_pct;      /* 0..100 from PID or MAN */
    uint8_t         preheat_en;    /* START_IN / STOP_IN: fase preheat */
    uint8_t         ramps_en;      /* siempre 1: START_IN / STOP_IN entran en rampas */
    uint16_t        stabilize_s;   /* hold time at setpoint for preheat OK */
    uint16_t        stabilize_left;

    /* RAMPS profile (EEPROM; no es programa lanzable) */
    uint8_t         ramp_n;
    uint8_t         ramp_idx;
    ramp_step_t     ramp_step[RAMP_STEPS_MAX];

    /* Alarm / cooldown (global settings) */
    uint16_t        alarm_duration_s;
    uint16_t        alarm_period_s;
    uint16_t        alarm_left_s;
    uint16_t        alarm_beep_left_s;
    uint8_t         alarm_hold_heat; /* 1 = PREHEAT: PID on durante alarma */
    uint8_t         cooldown_air_en;
    uint16_t        cooldown_target_c;
    uint16_t        temp_limit_c;

    /* USB session */
    device_mode_t   device_mode;
    uint8_t         telem_dirty;

    /* PID gains ×10 (integer) */
    int16_t    pid_kp_x10;
    int16_t    pid_ki_x10;
    int16_t    pid_kd_x10;
    pid_loop_t pid_loop;

    /* Autotune. Picos y umbrales en °C×10 para vistas y trama de gráfico. */
    atune_phase_t atune_phase;
    uint8_t       atune_cycles;
    uint8_t       atune_relay_on;
    uint16_t      atune_elapsed_s;
    int16_t       atune_peak_hi_x10;
    int16_t       atune_peak_lo_x10;
    int16_t       atune_hyst_hi_x10;
    int16_t       atune_hyst_lo_x10;
    int16_t       atune_kp_x10;
    int16_t       atune_ki_x10;
    int16_t       atune_kd_x10;

    /* Sound */
    uint8_t    buzz_nav_en;
    uint8_t    buzz_nav_reps;

    /* USB / AT */
    uint8_t    usb_last_ok;

    ctrl_src_t ctrl_src;
} app_state_t;

/* Compat alias used by telemetría / AT */
typedef program_id_t usb_program_t;

#endif
