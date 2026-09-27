# Características del producto — SMI Soldering Hot Plate

Maestro de fases, alarmas y EEPROM: [program_flows.md](program_flows.md). Si este archivo discrepa, manda ese. Código: [architecture.md](architecture.md). AT: [usb-automation.md](usb-automation.md).

Firmware `firmware/avr/`, ATmega16 @ 8 MHz. Actualizado: 2026-09-27.

## Decisiones

| Tema | Contrato |
|------|----------|
| Programa principal | **HEAT** (`delay_s==0` inmediato; `>0` espera) |
| PREHEAT | Fase de HEAT (`preheat_en`). No es programa AT |
| PID_TUNE | Solo AT (`AT+RUN=2`). Settings no lanza Auto |
| RAMPS | Dato EEPROM; no lanzable |
| Done / aire | PTC OFF. Fan solo si `cooldown_air_en`, hasta `temp_min_c` (default 40 °C) |
| Safety / consignas | `temp_min_c` 30..100; `temp_max_c` 40..250 (también `AT+CFG=S`) |
| Calor | SSR: MOC3021 + BT136 (no relé mecánico) |
| UART | `ERROR:n` / `ALARM:n` / `$HP` con `P`/`A` numéricos — [usb-automation.md](usb-automation.md) |

## Core vs shell

**Core:** HEAT, PREHEAT, PID/autotune, rampas EEPROM, estado, alarmas, AT.  
**Shell:** Home (Heat \| Settings), Ajustes (Sonido, ESTAB, P%, Aire), USB (solo AT), LCD/i18n. El shell no cambia la secuencia.

## Programas

| Nombre | UI | USB | Entradas | Salidas |
|--------|----|-----|----------|---------|
| HEAT | Sí | Sí | `delay_s`, rampas, `preheat_en`, `preheat_pct`, PID, temp_min/max | Si ESTAB: PID al % de Ramp1 y banda ±2 °C; luego rampas a T plena. `ALARM:2`. Aire solo si está habilitado |
| PID_TUNE | No | Sí | `AT+RUN=2,temp,ciclos,hyst` | `$HP` 1 Hz (`A=10` + `AP/AC/AK/AI/AD`); `AT+CFG=A` → EEPROM |

Detalle de fases: [program_flows.md](program_flows.md).

## Home

Dos casillas: **Heat** | **Settings**.  
Heat: 1º PRESS edita `delay_s` (±1 min, desde **0**); 2º PRESS arranca.  
USB: solo `AT+MODE=1` → vista propia.

## Ajustes

| Fila | Efecto |
|------|--------|
| Sonido | Silencia el beep `NAV` (`AT+CFG=H` campo snd) |
| ESTAB | `preheat_en` (`AT+CFG=H` campo en) |
| P% | `preheat_pct` 50..100 paso 5 (`AT+CFG=H` campo pct) |
| Aire | `cooldown_air_en` (`AT+CFG=H` campo air) |

PID Kp/Ki/Kd y autotune: solo AT (`AT+CFG=P`, `AT+RUN=2`, `AT+CFG=A`).

## Alarmas

Detalle en [program_flows.md](program_flows.md). Contrato corto:

- `OT` es la línea UART de sobretemperatura (`temp ≥ temp_max_c`, lectura válida). PTC OFF, fase `PH_FAULT`, `$HP` `ACTION=FAULT`, sin beep.
- La columna Beep nombra una categoría (ancho del pulso + repeticiones), no una frecuencia en Hz.
- El token de fase va en `$HP` `ACTION`, no en una línea UART de alarma.

## EEPROM v5

Global: ganancias PID, `atune_cycles_target`, `atune_hyst_c_x10`, `temp_min_c`, `temp_max_c`, `preheat_en`, `preheat_pct` (default 80), flags, alarmas. Un bloque v4 no se migra: vuelven los defaults.  
Programas: `ee_heat` (delay), `ee_tune`. Rampas: `ee_ramp`. No hay `ee_pre`.  
Picos de autotune y la fase viva no se guardan.

## Compilación

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
