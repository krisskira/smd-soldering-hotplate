#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <stdint.h>

/* Safety / consignas (también en EEPROM v8)
 * temp_min_c: piso de toda consigna y T a la que para el aire (50–100 °C).
 * temp_max_c: corte de seguridad; si T lo alcanza → PTC OFF, FAULT, ERROR:7
 * (40–260 °C, AT+CFG=S). Un escalón nunca pide más que temp_cmd_hi_c(). */
#define TEMP_MIN_C_DEFAULT     50u   /* piso de consigna y OFF del aire */
#define TEMP_MAX_C_DEFAULT     210u  /* corte de seguridad; por encima del techo de consigna */
#define TEMP_MIN_C_LO          50u   /* mínimo que admite temp_min_c */
#define TEMP_MIN_C_HI          100u  /* máximo que admite temp_min_c */
#define TEMP_MAX_C_LO          40u   /* mínimo que admite el corte */
#define TEMP_MAX_C_HI          260u  /* máximo que admite el corte */
/* Techo de consigna (proceso). El corte temp_max_c queda por encima. */
#define TEMP_SET_CEILING_C     250u

/* Máximo °C que puede pedir un escalón: el menor entre el corte y el techo. */
static inline uint16_t temp_cmd_hi_c(uint16_t temp_max_c)
{
    return (temp_max_c < TEMP_SET_CEILING_C) ? temp_max_c : TEMP_SET_CEILING_C;
}
/* PH_RUN: duty alto, T bajo la banda y pendiente ~0 durante este tiempo → stall.
 * Solo cuenta con sensor válido, duty ≥ RUN_STALL_DUTY_PCT y T fuera de ±BN;
 * al cumplirse RUN_STALL_S compara la subida total con SLOPE × S. */
#define RUN_STALL_S            180u  /* ventana (s) antes de declarar estancado */
#define RUN_STALL_DUTY_PCT     95u   /* duty mínimo (%) para contar ese tiempo */
#define RUN_STALL_SLOPE_X10    2     /* |dT| ≤ 0,2 °C/s cuenta como plano */
#define TEMP_PERIOD_MS         1000u /* periodo de lectura PT100 y del PI (ms) */
#define RREF_OHM               430.0f /* Rref del MAX31865 para el PT100 (Ω) */

/* Compat: límites de consignas usan estado temp_min/max en runtime */
#define TEMP_MIN_SET_C         TEMP_MIN_C_LO /* alias del piso de consigna */
#define TEMP_MAX_SET_C         TEMP_MAX_C_HI /* alias del techo absoluto */
#define TEMP_LIMIT_C           TEMP_MAX_C_DEFAULT /* alias del corte default (°C) */
#define TEMP_LIMIT_X10         ((int16_t)(TEMP_MAX_C_DEFAULT * 10)) /* corte ×10 */

/* Texto LCD: buffers de línea (LINE_LEN + '\0') y filas marcadas en row_dirty. */
#define LINE_LEN          21u  /* caracteres útiles de una línea de texto */
#define ROW_COUNT         4u   /* filas del layout de texto */
#define ROW_ALL           0x0Fu /* máscara: las 4 filas sucias */

/* Buzzer: CONFIRM usa el pulso corto; READY (≥ 3 pulsos) y ALARM el largo. */
#define BEEP_ON_MS        30u  /* pulso corto ON (confirmación) */
#define BEEP_OFF_MS       60u  /* silencio entre pulsos cortos */
#define BEEP_ALERT_ON_MS  50u  /* pulso largo ON (listo / alarma) */
#define BEEP_ALERT_OFF_MS 80u  /* silencio entre pulsos largos */

/* Salidas físicas: PTC1/PTC2 por MOC3021 + BT136; ventilador de enfriamiento. */
#define OUT_PTC1          0u   /* índice de la resistencia 1 en out_state[] */
#define OUT_PTC2          1u   /* índice de la resistencia 2 */
#define OUT_FAN           2u   /* índice del ventilador */
#define OUTPUT_COUNT      3u   /* tamaño de out_state[] */

/* HOME: Heat | Settings. USB solo AT. */
#define HOME_COUNT         2u  /* casillas laterales */
#define HOME_IDX_HEAT      0u  /* casilla Heat */
#define HOME_IDX_SETTINGS  1u  /* casilla Settings */
#define HOME_PAGE_MENU     0u  /* el encoder cambia de casilla */
#define HOME_PAGE_SETTINGS 1u  /* lista Ajustes embebida (foco en filas) */

/* Zonas de Home en row_dirty: solo se redibuja lo marcado. */
#define HOME_DIRTY_SIDE    0x01u /* redibujar las casillas laterales */
#define HOME_DIRTY_TEMP    0x02u /* redibujar la temperatura */
#define HOME_DIRTY_BODY    0x04u /* redibujar fase, rampa y reloj */
#define HOME_DIRTY_FOOT    0x08u /* redibujar el pie RUN/STOP/EXIT */
#define HOME_DIRTY_ALL     0x0Fu /* las cuatro zonas de Home */

#define SET_PAGE_MAIN     0u   /* única página de Ajustes */
/* Ajustes embebidos: R1..R4 + retraso (+ pie Salir). Aire solo AT. */
#define SETTINGS_COUNT    5u   /* filas: R1..R4 + DLY */
#define SET_IDX_RAMP0     0u   /* fila R1 */
#define SET_IDX_RAMP1     1u   /* fila R2 */
#define SET_IDX_RAMP2     2u   /* fila R3 */
#define SET_IDX_RAMP3     3u   /* fila R4 */
#define SET_IDX_DELAY     4u   /* fila del retraso DLY */
#define SET_VIS_ROWS      4u   /* 5 opciones: la lista se desplaza en DLY/EXIT */
#define SET_HDR_H         11u  /* 2 px + glifo 7 + 2 px; "SETUP" invertido */
#define SET_HDR_GAP       2u   /* aire bajo el header, fuera de la banda invertida */
#define SET_ROW_Y0        (SET_HDR_H + SET_HDR_GAP) /* 13: Y de la primera fila */
#define SET_ROW_H         9u   /* 1 px + glifo 7 + 1 px, todo en el inverso */
#define SET_ROW_PAD       1u   /* separación entre opciones, fuera del inverso */
#define SET_ROW_STEP      (SET_ROW_H + SET_ROW_PAD) /* 10; 13+3×10+9 = 52 < pie 54 */

/* Edición en Ajustes (edit_armed): PRESS en Rn arma °C → hold → suelta;
 * PRESS en DLY arma horas → minutos → suelta. */
#define SET_RAMPS_COUNT   RAMP_STEPS_MAX /* escalones editables en Ajustes */
#define SET_EDIT_NONE     0u   /* navegando: el encoder no cambia el valor */
#define SET_EDIT_TEMP     1u   /* editando los °C del escalón */
#define SET_EDIT_TIME     2u   /* editando el hold del escalón */
#define SET_EDIT_DELAY_H  3u   /* reloj DLY: horas */
#define SET_EDIT_DELAY_M  4u   /* reloj DLY: minutos */
#define RAMP_TEMP_STEP_C  5u   /* paso del encoder al editar °C */
/* Retraso de HEAT: 00:00 … 12:00. En RAM/EEPROM son hora + minuto, no un contador de segundos. */
#define DELAY_H_MAX       12u  /* tope de horas */
#define DELAY_M_MAX       59u  /* tope de minutos; en 12 h queda en 0 */
#define DELAY_MAX_S       (DELAY_H_MAX * 3600u) /* 43200; solo en la trama AT */
/* cfg_p2_t.flags bit0: b = (hora<<8)|minuto. Sin el bit, b es el retraso antiguo en segundos. */
#define CFG_HEAT_DLY_HM   0x01u

#define USB_SEL_COUNT     2u   /* compat: el selector USB ya no se dibuja */

/* PI predictivo (sin D). Kp y Ki van en EEPROM / AT+CFG=P,kp,ki / autotune.
 * duty = (Kp_x10·e + Ki_x100·I) / 10, con e = t_ref − (T + rate·LOOKAHEAD).
 * Kp_x10 = 76 → Kp 7,6. Ki_x100 = 6 → Ki 0,06/s. */
#define PID_WINDOW_MS     1500u /* ventana SSR: el duty es el % ON de este periodo */
#define PID_KP_DEFAULT    76    /* Kp ×10 (7,6); AT+CFG=P */
#define PID_KI_DEFAULT    6     /* Ki ×100 (0,06/s) */
/* Pendiente máx. de t_ref (°C/s ×10) y horizonte de cola (s); compile-time */
#define RISE_C_X10_DEFAULT    12u  /* 1,2 °C/s por muestra de 1 s */
#define LOOKAHEAD_S_DEFAULT   15   /* ~18 °C de cola a 1,2 °C/s */

/* Autotune (SSR bang-bang); defaults EEPROM v8
 * AT+RUN=2,temp,ciclos,hyst[,max_s] o AT+CFG=T. Oscila ±hyst alrededor de temp,
 * mide amplitud y periodo y calcula Kp/Ki por Z–N PI; al terminar los guarda. */
#define ATUNE_MIN_CYCLES     3u    /* mínimo de ciclos que acepta el RUN */
#define ATUNE_MAX_CYCLES     10u   /* máximo de ciclos */
#define ATUNE_CYCLES_DEFAULT 5u    /* ciclos si no se indica otro */
#define ATUNE_MAX_S_DEFAULT  2000u /* timeout global del RUN (s) */
#define ATUNE_MAX_S_LO       120u  /* timeout mínimo configurable */
#define ATUNE_MAX_S_HI       3600u /* timeout máximo configurable */
#define ATUNE_HYST_C_X10     15    /* histéresis del bang-bang: ±1,5 °C */
/* Zona con autoridad. Fuera de aquí el relé no describe la planta. */
#define ATUNE_SET_LO_C       120u  /* consigna mínima válida */
#define ATUNE_SET_HI_C       150u  /* consigna máxima válida */
/* ON medio ≥ 3× OFF medio, o 3 min plano sin llegar al umbral alto → FAIL. */
#define ATUNE_ON_OFF_RATIO   3u    /* ON medio / OFF medio que invalida la planta */
#define ATUNE_FLAT_S         180u  /* segundos planos antes del FAIL */
#define ATUNE_FLAT_SLOPE_X10 2     /* |dT| ≤ 0,2 °C/s cuenta como plano */
/* Compat: código legacy que use ATUNE_MAX_S → default */
#define ATUNE_MAX_S       ATUNE_MAX_S_DEFAULT

/* Queda en el layout EEPROM v8; el lazo ya no tiene fase PREHEAT. */
#define PREHEAT_STABLE_S_DEFAULT  30u /* segundos de “estable” que ya no se usan */
/* Banda ±°C (EEPROM / AT+CFG=H / $CF BN,BX). Entrada vs salida = histéresis. */
#define PREHEAT_BAND_C_DEFAULT       4u  /* BN: |T−SET| para entrar en meseta */
#define PREHEAT_BAND_EXIT_C_DEFAULT  6u  /* BX: guardada; la meseta no se aborta */
#define PREHEAT_BAND_C_LO            1u  /* BN mínimo */
#define PREHEAT_BAND_C_HI            15u /* BN máximo */
#define PREHEAT_BAND_EXIT_C_HI       20u /* BX máximo; debe ser ≥ BN */
/* Cola por encima del tope: si no vuelve bajo el preheat, seguir a Ramp1. */
#define PREHEAT_OVERHEAT_S        60u /* sin uso: ya no hay fase previa a R1 */
/* Tope del PREHEAT/STABILIZE de HEAT, en % de T(Ramp1). No es el setpoint del RUN. */
#define PREHEAT_PCT_DEFAULT       80u /* % de R1; el campo EEPROM se escribe a 0 */
#define PREHEAT_PCT_LO            50u /* mínimo de ese % (legacy) */
#define PREHEAT_PCT_HI            100u /* máximo de ese % (legacy) */
#define PREHEAT_PCT_STEP          5u  /* paso al editar ese % (legacy) */
/* Fin de HEAT (PH_ALARM): PTC OFF, pitidos y ALARM:2; luego aire o END. */
#define ALARM_DURATION_S_DEFAULT  60u /* duración de la fase de fin (s) */
#define ALARM_PERIOD_S_DEFAULT    5u  /* cada cuántos segundos pita la alarma */
#define COOLDOWN_TARGET_C_DEFAULT TEMP_MIN_C_DEFAULT /* alias: el aire para en temp_min_c */
#define RAMP_STEPS_MAX            4u  /* escalones del Soldering Profile */

/* Hold (meseta) de cada escalón: 30 s … 60 min en pasos de 30 s. */
#define TIMER_MAX_S       (60u * 60u) /* hold máximo de un escalón: 3600 s */
#define TIMER_STEP_S      30u         /* paso del encoder y hold por defecto */
#define AT_LINE_MAX       32u         /* bytes del buffer de una línea AT */

/* Cabecera del bloque EEPROM: magic + versión + checksum; si falla, defaults. */
#define CFG_EEPROM_MAGIC  0xA5u /* marca de bloque escrito por este firmware */
/* v8: + preheat_band_c / preheat_band_exit_c. Ver distinta → defaults. */
#define CFG_EEPROM_VER    8u    /* versión del layout; otra versión recarga defaults */

#endif
