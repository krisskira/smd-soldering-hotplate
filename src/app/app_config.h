#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <stdint.h>

/* Constantes de aplicación. Drivers viven en lib/; esto es capa app. */

#define TEMP_LIMIT_C      200
#define TEMP_LIMIT_X10    2000
#define TEMP_MIN_SET_C    30u
#define TEMP_MAX_SET_C    200u
#define TEMP_PERIOD_MS    1000u
#define RREF_OHM          430.0f

#define LINE_LEN          21u     /* 21 chars × 6 px = 126 px */
#define ROW_COUNT         4u
#define ROW_ALL           0x0Fu

#define BEEP_ON_MS        30u
#define BEEP_OFF_MS       60u
#define BEEP_ALERT_ON_MS  50u
#define BEEP_ALERT_OFF_MS 80u

/* Índices de salidas (coherentes con outputs.c) */
#define OUT_PTC1          0u
#define OUT_PTC2          1u
#define OUT_FAN           2u
#define OUTPUT_COUNT      3u

/*
 * HOME, iteración actual: solo Modo USB.
 * Marcha, ajustes y el resto de ítems vuelven como vistas nuevas.
 */
#define HOME_COUNT        1u
#define HOME_IDX_USB      0u

/* Subpágina visible hoy. RUN y SETTINGS se reintroducen con sus vistas. */
#define HOME_PAGE_MENU     0u

/* Ajustes: beep | preheat | ramps | cooldown | VOLVER */
#define SETTINGS_COUNT    5u

/* USB view: DETENER | VOLVER */
#define USB_SEL_COUNT     2u

/* PID time-proportioning window */
#define PID_WINDOW_MS     2000u
#define PID_KP_DEFAULT    20     /* ×10 → 2.0 */
#define PID_KI_DEFAULT    5      /* ×10 → 0.5 */
#define PID_KD_DEFAULT    10     /* ×10 → 1.0 */

/* Autotune relay */
#define ATUNE_MIN_CYCLES  3u
#define ATUNE_MAX_S       600u
#define ATUNE_HYST_C_X10  15     /* 1.5 °C */

/* Preheat / alarm / cooldown defaults */
#define PREHEAT_STABLE_S_DEFAULT  30u
#define PREHEAT_BAND_C_X10        20  /* ±2.0 °C */
#define ALARM_DURATION_S_DEFAULT  60u /* 1 min final / PREHEAT */
#define ALARM_PERIOD_S_DEFAULT    5u
#define COOLDOWN_TARGET_C_DEFAULT 40u
#define RAMP_STEPS_MAX            4u

#define TIMER_MAX_S       (60u * 60u)
#define TIMER_STEP_S      30u

#define AT_LINE_MAX       32u

/* EEPROM config v3 (ramps_en) */
#define CFG_EEPROM_MAGIC  0xA5u
#define CFG_EEPROM_VER    3u

#endif
