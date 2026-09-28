# Características del producto — SMI Soldering Hot Plate

Maestro de fases, alarmas y EEPROM: [program_flows.md](program_flows.md). Si este archivo discrepa, manda ese. Código: [architecture.md](architecture.md). AT: [usb-automation.md](usb-automation.md).

Firmware `firmware/avr/`, ATmega16 @ 8 MHz. Actualizado: 2026-09-28.

## Decisiones

| Tema | Contrato |
|------|----------|
| Programa principal | **HEAT** (`delay_s==0` inmediato; `>0` espera) |
| PREHEAT | Fase de HEAT (`preheat_en`). No es programa AT |
| PID_TUNE | Solo AT (`AT+RUN=2`). Settings no lanza Auto |
| RAMPS | Dato EEPROM; no lanzable. Escalones **no decrecientes** |
| Done / aire | PTC OFF. Fan solo si `cooldown_air_en`, hasta `temp_min_c` (default **50 °C**). Sin fan entre rampas |
| Safety / consignas | `temp_min_c` **50..100**; `temp_max_c` 40..250 (también `AT+CFG=S`) |
| Calor | SSR: MOC3021 + BT136 (no relé mecánico) |
| UART | `ERROR:n` / `ALARM:n` / `$HP` con `P`/`A` numéricos — [usb-automation.md](usb-automation.md) |

## Core vs shell

**Core:** HEAT, PREHEAT, PID/autotune, rampas EEPROM, estado, alarmas, AT.  
**Shell:** Home (Heat \| Settings embebido), overlay USB en Heat (solo AT), LCD/i18n. El shell no cambia la secuencia.

## Programas

| Nombre | UI | USB | Entradas | Salidas |
|--------|----|-----|----------|---------|
| HEAT | Sí | Sí | `delay_s`, rampas no decrecientes, `preheat_en`, `preheat_pct`, PID, temp_min/max | PI predictivo (t_ref + lookahead). ESTAB: % de Ramp1; overshoot → timeout 60 s. `hold_s` = reloj de etapa. `ALARM:2`. Aire solo al final |
| PID_TUNE | No | Sí | `AT+RUN=2,temp,ciclos,hyst[,max_s]`; `AT+CFG=T` | `$HP` 1 Hz (`A=10` + `AP/AC/AK/AI`); fan en medio OFF; `AT+CFG=A` → EEPROM (PI, Kd=0) |

Detalle de fases: [program_flows.md](program_flows.md).

## Home

Dos casillas laterales: **Heat** | **Settings**. Sin vistas aparte.  
Heat: temp **FONT_5X7_X2** (5×7 a 2×, `123.4°C`), fase, `Rx Tset mm:ss`; pie **`RUN`** / **`STOP`**. Cancel UI → IDLE.  
USB: temp + etiqueta **`USB`**; pie **`EXIT`**. Lateral 16×16: plancha / llave.  
Settings: header invertido **`SETTINGS`** (11 px, 2 px de aire) + lista R1…R4 + **`DELAY`** desde y=11 (nombre a la izquierda, valores a la derecha); PRESS entra al listado; pie **`EXIT`** → Heat. Aire / PID / autotune solo AT.

Labels LCD (i18n, CAPS inglés): `IDLE` `WAIT` `PREHEAT` `STABLE` `ALM` `RUN` `END` `ERR` `EXIT` `AIR` `DELAY` `OFF` `STOP` `USB` `SETTINGS`.

## Ajustes (panel Home)

| Fila | Efecto |
|------|--------|
| R1…R4 | Temp/hold; T→bajo desactiva (R1 mínimo = `temp_min`); límites `temp_min`…`temp_max` |
| DELAY | `delay_s` de HEAT (±1 min, desde 0). No se edita desde la casilla Heat |

Aire (`cooldown_air_en`), sonido / ESTAB / P% / PID / autotune: solo AT.  
Timeout autotune (`atune_max_s` / `$CF AMS=`): 120..3600 s, default **2000**.

## Alarmas

Detalle en [program_flows.md](program_flows.md). Contrato corto:

- Sobretemperatura (`temp ≥ temp_max_c`, lectura válida): UART **`ERROR:7`**, PTC OFF, fase `PH_FAULT`, `$HP` `A=FAULT`, sin beep.
- La columna Beep nombra una categoría (ancho del pulso + repeticiones), no una frecuencia en Hz.
- El token de fase va en `$HP` `A=`, no en una línea UART de alarma aparte (salvo `ALARM:n` de proceso).

## EEPROM v7

Global: ganancias PID (default Kp **246** / Ki **10** / Kd **0**, ×10), `atune_cycles_target` (default **5**), `atune_hyst_c_x10` (default **15**), `atune_max_s` (default **2000**), `temp_min_c` (default **50**), `temp_max_c` (default **250**), `preheat_en`, `preheat_pct` (default 80), flags, alarmas. Un bloque con ver distinta no se migra: vuelven los defaults.  
`RISE_C_X10_DEFAULT` (7) y `LOOKAHEAD_S_DEFAULT` (30) son compile-time en `app_config.h` (no EEPROM).  
Programas: `ee_heat` (delay), `ee_tune`. Rampas: `ee_ramp` (solo no decrecientes en HEAT). No hay `ee_pre`.

## Compilación / flash

Flash ATmega16 = **16384 B**. Medir siempre:

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
