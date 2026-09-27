#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <stdint.h>

/* Safety / consignas (también en EEPROM v5) */
#define TEMP_MIN_C_DEFAULT     40u   /* OFF aire + piso default */
#define TEMP_MAX_C_DEFAULT     200u  /* corte safety default */
#define TEMP_MIN_C_LO          30u
#define TEMP_MIN_C_HI          100u
#define TEMP_MAX_C_LO          40u
#define TEMP_MAX_C_HI          250u
#define TEMP_PERIOD_MS         1000u
#define RREF_OHM               430.0f

/* Compat: límites de consignas usan estado temp_min/max en runtime */
#define TEMP_MIN_SET_C         TEMP_MIN_C_LO
#define TEMP_MAX_SET_C         TEMP_MAX_C_HI
#define TEMP_LIMIT_C           TEMP_MAX_C_DEFAULT
#define TEMP_LIMIT_X10         ((int16_t)(TEMP_MAX_C_DEFAULT * 10))

#define LINE_LEN          21u
#define ROW_COUNT         4u
#define ROW_ALL           0x0Fu

#define BEEP_ON_MS        30u
#define BEEP_OFF_MS       60u
#define BEEP_ALERT_ON_MS  50u
#define BEEP_ALERT_OFF_MS 80u

#define OUT_PTC1          0u
#define OUT_PTC2          1u
#define OUT_FAN           2u
#define OUTPUT_COUNT      3u

/* HOME: Heat | Settings. USB solo AT. */
#define HOME_COUNT         2u
#define HOME_IDX_HEAT      0u
#define HOME_IDX_SETTINGS  1u
#define HOME_PAGE_MENU     0u

#define HOME_DIRTY_SIDE    0x01u
#define HOME_DIRTY_TEMP    0x02u
#define HOME_DIRTY_BODY    0x04u
#define HOME_DIRTY_FOOT    0x08u
#define HOME_DIRTY_ALL     0x0Fu

#define SET_PAGE_MAIN     0u
#define SET_PAGE_PID      1u
#define SETTINGS_COUNT    5u
#define SET_IDX_PID       0u
#define SET_IDX_SOUND     1u
#define SET_IDX_PREHEAT   2u
#define SET_IDX_PRE_PCT   3u
#define SET_IDX_AIR       4u

#define SET_RAMPS_COUNT   RAMP_STEPS_MAX
#define SET_EDIT_NONE     0u
#define SET_EDIT_TEMP     1u
#define SET_EDIT_TIME     2u
#define RAMP_TEMP_STEP_C  5u
#define START_DELAY_MIN_S 0u
#define START_DELAY_MAX_S TIMER_MAX_S
#define START_DELAY_STEP_S 60u

#define USB_SEL_COUNT     2u

#define PID_WINDOW_MS     2000u
#define PID_KP_DEFAULT    20
#define PID_KI_DEFAULT    5
#define PID_KD_DEFAULT    10

/* Autotune (SSR bang-bang); defaults EEPROM */
#define ATUNE_MIN_CYCLES  3u
#define ATUNE_MAX_CYCLES  10u
#define ATUNE_MAX_S       600u
#define ATUNE_HYST_C_X10  15

#define PREHEAT_STABLE_S_DEFAULT  30u
#define PREHEAT_BAND_C_X10        20
/* Tope del PREHEAT/STABILIZE de HEAT, en % de T(Ramp1). No es el setpoint del RUN. */
#define PREHEAT_PCT_DEFAULT       80u
#define PREHEAT_PCT_LO            50u
#define PREHEAT_PCT_HI            100u
#define PREHEAT_PCT_STEP          5u
#define ALARM_DURATION_S_DEFAULT  60u
#define ALARM_PERIOD_S_DEFAULT    5u
#define COOLDOWN_TARGET_C_DEFAULT TEMP_MIN_C_DEFAULT
#define RAMP_STEPS_MAX            4u

#define TIMER_MAX_S       (60u * 60u)
#define TIMER_STEP_S      30u
#define AT_LINE_MAX       32u

#define CFG_EEPROM_MAGIC  0xA5u
#define CFG_EEPROM_VER    5u

#endif
