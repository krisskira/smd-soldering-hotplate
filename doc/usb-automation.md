# UART / AT / MODO USB — SMI Soldering Hot Plate

UART 9600 8N1. Sesión exclusiva MANUAL/USB (`AT+DEVICEMODE`).

Entrada a sesión: solo `AT+DEVICEMODE=USB` (si el equipo está libre). El PRESS de la vista USB vuelve a HOME.

## Comandos (requieren USB salvo DEVICEMODE/STATUS)

| Comando | Efecto | Persistencia |
|---------|--------|--------------|
| `AT+PROGRAM=PREHEAT\|START_IN\|STOP_IN\|PID_TUNE` | Selecciona programa (**sin RAMPS**) | load perfil |
| `AT+TEMP=<30..200>` | Setpoint | `cfg_save_program` |
| `AT+DELAY=<0..3600>` | Delay (START) / run_s (STOP) | `cfg_save_program` |
| `AT+PREHEAT=0\|1` | Fase preheat en START/STOP | `cfg_save_global` |
| `AT+RAMPS=1` | Confirma rampas siempre activas. `=0` → `ERROR:INVALID-PARAMETER` | `cfg_save_global` |
| `AT+RAMP=<i>,<temp>,<sec>` | Escalón i=0..3 | `cfg_save_ramps` |
| `AT+START` / `AT+STOP` | Arranca / pide FIN o abort | — |

## Secuencia START/STOP

```
[DELAY si START_IN] → [PREHEAT si preheat_en] → RAMPS (paso 1 siempre; 2–4 opcionales)
  → FIN: ALARM:CYCLE-DONE (timeout o PRESS) + bomba ~cooldown_target_c
```

PREHEAT standalone: `ALARM:PREHEAT-SUCCESS` con PID hold hasta PRESS/timeout → DONE.

## Trama `$HP`

Campos incluyen `PROGRAM=PREHEAT|START_IN|STOP_IN|PID_TUNE`, `ACTION=…`, `RUN=` (tiempo restante / run).

## Trama `$HP,PLOT`

Una línea por muestra de sensor (1 Hz) **solo mientras el autotune está en curso** (`ATUNE_RUN`) y la sesión es `DEVICE_USB`. Entrar a USB, elegir `PID_TUNE` sin `AT+START`, o correr PREHEAT/START/STOP no emite esta trama. En MANUAL tampoco.

```
$HP,PLOT,148.0,150,40,151.5,148.5,152.0,147.0
```

CSV de orden fijo (compatible con un plotter). Fase y ciclo del autotune no van en la línea: se leen de `atune_phase` y `atune_cycles` en el estado, y la trama de evento `$HP` sigue llevando `ACTION`.

| # | Campo | Unidad | Origen |
|---|-------|--------|--------|
| 1 | `T` | °C, un decimal | `sensor.temp_c_x10` (`---` si no es válida) |
| 2 | `SET` | °C | `t_set_c` |
| 3 | `DUTY` | 0..100 | `duty_pct` (relé de autotune) |
| 4 | `HHI` | °C, un decimal | umbral alto de conmutación |
| 5 | `HLO` | °C, un decimal | umbral bajo de conmutación |
| 6 | `PKH` | °C, un decimal | pico alto de la oscilación |
| 7 | `PKL` | °C, un decimal | pico bajo de la oscilación |

Al terminar el autotune (`DONE`, `FAIL` o cancelación) la trama de gráfico se corta. El evento `$HP` de cambio de fase sigue saliendo.

Ver skill `hotplate-usb-mode` y `product_features.md`.
