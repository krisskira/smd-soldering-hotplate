#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <stdint.h>

/* Safety / consignas (también en EEPROM v8) */
#define TEMP_MIN_C_DEFAULT     50u   /* OFF aire + piso default */
#define TEMP_MAX_C_DEFAULT     250u  /* corte safety default */
#define TEMP_MIN_C_LO          50u
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
#define HOME_PAGE_SETTINGS 1u  /* lista Ajustes embebida (foco en filas) */

#define HOME_DIRTY_SIDE    0x01u
#define HOME_DIRTY_TEMP    0x02u
#define HOME_DIRTY_BODY    0x04u
#define HOME_DIRTY_FOOT    0x08u
#define HOME_DIRTY_ALL     0x0Fu

#define SET_PAGE_MAIN     0u
/* Ajustes embebidos: R1..R4 + retraso (+ pie Salir). Aire solo AT. */
#define SETTINGS_COUNT    5u
#define SET_IDX_RAMP0     0u
#define SET_IDX_RAMP1     1u
#define SET_IDX_RAMP2     2u
#define SET_IDX_RAMP3     3u
#define SET_IDX_DELAY     4u
#define SET_VIS_ROWS      5u
#define SET_HDR_H         11u  /* 2 px + glifo 7 + 2 px; "SETUP" invertido */
#define SET_HDR_GAP       2u   /* aire bajo el header, fuera de la banda invertida */
#define SET_ROW_Y0        (SET_HDR_H + SET_HDR_GAP) /* 13 */
#define SET_ROW_H         7u   /* glifo 5×7; el hueco no entra en el inverso */
#define SET_ROW_PAD       1u   /* separación entre opciones */
#define SET_ROW_STEP      (SET_ROW_H + SET_ROW_PAD) /* 8; 13+4×8+7 = 52 < pie 54 */

#define SET_RAMPS_COUNT   RAMP_STEPS_MAX
#define SET_EDIT_NONE     0u
#define SET_EDIT_TEMP     1u
#define SET_EDIT_TIME     2u
#define SET_EDIT_DELAY_H  3u  /* reloj DLY: horas */
#define SET_EDIT_DELAY_M  4u  /* reloj DLY: minutos */
#define RAMP_TEMP_STEP_C  5u
/* Retraso de HEAT: 00:00 … 12:00. En RAM/EEPROM son hora + minuto, no un contador de segundos. */
#define DELAY_H_MAX       12u
#define DELAY_M_MAX       59u
#define DELAY_MAX_S       (DELAY_H_MAX * 3600u) /* 43200; solo en la trama AT */
/* cfg_p2_t.flags bit0: b = (hora<<8)|minuto. Sin el bit, b es el retraso antiguo en segundos. */
#define CFG_HEAT_DLY_HM   0x01u

#define USB_SEL_COUNT     2u

#define PID_WINDOW_MS     1500u
#define PID_KP_DEFAULT    246  /* ×10 — AT+CFG=P,246,10 */
#define PID_KI_DEFAULT    10
/* Pendiente máx. de t_ref (°C/s ×10) y horizonte de cola (s); compile-time */
#define RISE_C_X10_DEFAULT    12u   /* 1.2 °C/s (muestra 1 s) */
#define LOOKAHEAD_S_DEFAULT   15  /* ~18 °C cola @ 1.2 °C/s */

/* Autotune (SSR bang-bang); defaults EEPROM v8 */
#define ATUNE_MIN_CYCLES     3u
#define ATUNE_MAX_CYCLES     10u
#define ATUNE_CYCLES_DEFAULT 5u
#define ATUNE_MAX_S_DEFAULT  2000u  /* timeout global del RUN (s) */
#define ATUNE_MAX_S_LO       120u
#define ATUNE_MAX_S_HI       3600u
#define ATUNE_HYST_C_X10  15
/* Compat: código legacy que use ATUNE_MAX_S → default */
#define ATUNE_MAX_S       ATUNE_MAX_S_DEFAULT

#define PREHEAT_STABLE_S_DEFAULT  30u
/* Banda ±°C (EEPROM / AT+CFG=H / $CF BN,BX). Entrada vs salida = histéresis. */
#define PREHEAT_BAND_C_DEFAULT       4u
#define PREHEAT_BAND_EXIT_C_DEFAULT  6u
#define PREHEAT_BAND_C_LO            1u
#define PREHEAT_BAND_C_HI            15u
#define PREHEAT_BAND_EXIT_C_HI       20u
/* Cola por encima del tope: si no vuelve bajo el preheat, seguir a Ramp1. */
#define PREHEAT_OVERHEAT_S        60u
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
/* v8: + preheat_band_c / preheat_band_exit_c. Ver distinta → defaults. */
#define CFG_EEPROM_VER    8u

#endif
