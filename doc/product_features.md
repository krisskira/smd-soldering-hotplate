# Características del producto — SMI Soldering Hot Plate

Dominio: [program_flows.md](program_flows.md). Código: [architecture.md](architecture.md). AT: [usb-automation.md](usb-automation.md).

Firmware `firmware/avr/`, ATmega16 @ 8 MHz. Actualizado: 2026-09-27.

## Decisiones

| Tema | Contrato |
|------|----------|
| Programa principal | **HEAT** (`delay_s==0` inmediato; `>0` espera) |
| PREHEAT | Solo USB/AT |
| PID_TUNE | UI Ajustes + AT |
| RAMPS | Dato EEPROM; no lanzable |
| Done / aire | Hasta `temp_min_c` (default 40 °C) |
| Safety / consignas | `temp_min_c` 30..100; `temp_max_c` 40..250 |
| Calor | SSR: MOC3021 + BT136 (no relé mecánico) |

## Core vs shell

**Core:** HEAT, PREHEAT, PID/autotune, rampas EEPROM, estado, alarmas, AT.  
**Shell:** Home (Heat \| Settings), Settings→PID, USB (solo AT), LCD/i18n.

## Programas

| Nombre | UI | USB | Entradas | Salidas |
|--------|----|-----|----------|---------|
| HEAT | Sí | Sí | `delay_s`, rampas, PID, temp_min/max | PTC vía PID; `ALARM:DONE`; aire → temp_min |
| PREHEAT | No | Sí | `t_set_c`, stabilize | `ALARM:PH-OK`; sin rampas/aire |
| PID_TUNE | Ajustes | Sí | t_set, cycles, hyst | Kp/Ki/Kd → EEPROM |

Detalle de fases: [program_flows.md](program_flows.md).

## Home

Dos casillas: **Heat** | **Settings**.  
Heat: 1º PRESS edita `delay_s` (±1 min, desde **0**); 2º PRESS arranca.  
USB: solo `AT+DEVICEMODE=USB` → vista propia.

## EEPROM v4

Global v5: ganancias PID, `atune_cycles_target`, `atune_hyst_c_x10`, `temp_min_c`, `temp_max_c`, `preheat_en`, `preheat_pct` (default 80), flags, alarmas. Un bloque v4 no se migra: vuelven los defaults.  
Programas: `ee_heat` (delay), `ee_pre`, `ee_tune`. Rampas: `ee_ramp`.

## Compilación

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
