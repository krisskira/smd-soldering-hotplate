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
**Shell:** Home (Heat \| Settings embebido), overlay USB en Heat (solo AT), LCD/i18n. El shell no cambia la secuencia.

## Programas

| Nombre | UI | USB | Entradas | Salidas |
|--------|----|-----|----------|---------|
| HEAT | Sí | Sí | `delay_s`, rampas, `preheat_en`, `preheat_pct`, PID, temp_min/max | Si ESTAB: PID al % de Ramp1 y banda ±2 °C; luego rampas a T plena. `ALARM:2`. Aire solo si está habilitado |
| PID_TUNE | No | Sí | `AT+RUN=2,temp,ciclos,hyst[,max_s]`; `AT+CFG=T` | `$HP` 1 Hz (`A=10` + `AP/AC/AK/AI/AD`); fan en medio OFF; `AT+CFG=A` → EEPROM |

Detalle de fases: [program_flows.md](program_flows.md).

## Home

Dos casillas: **Heat** | **Settings**. Sin vistas aparte.  
Heat: temp **FONT_8X12** (margen 3 px + gaps 4 px), fase, `Rx Tset mm:ss`; pie **Iniciar ↵** / **Para ↵**. Cancel UI → IDLE.  
USB: temp + icono USB ×3; pie **Salir ↵**. Lateral ×3: plancha / llave. Ajustes sin header.  
Settings: header **Ajustes** + R1…R4 + Retraso. PRESS entra al listado; **Salir ↵** → Heat. Aire solo AT.

## Ajustes (panel Home)

| Fila | Efecto |
|------|--------|
| R1…R4 | Temp/hold; T→bajo desactiva (R1 mínimo = `temp_min`); límites `temp_min`…`temp_max` |
| Retraso | `delay_s` de HEAT (±1 min, desde 0) |

Aire (`cooldown_air_en`), sonido / ESTAB / P% / PID / autotune: solo AT.  
Timeout autotune (`atune_max_s` / `$CF AMS=`): 120..3600 s, default 600.

## Alarmas

Detalle en [program_flows.md](program_flows.md). Contrato corto:

- `OT` es la línea UART de sobretemperatura (`temp ≥ temp_max_c`, lectura válida). PTC OFF, fase `PH_FAULT`, `$HP` `ACTION=FAULT`, sin beep.
- La columna Beep nombra una categoría (ancho del pulso + repeticiones), no una frecuencia en Hz.
- El token de fase va en `$HP` `ACTION`, no en una línea UART de alarma.

## EEPROM v6

Global: ganancias PID, `atune_cycles_target`, `atune_hyst_c_x10`, `atune_max_s`, `temp_min_c`, `temp_max_c`, `preheat_en`, `preheat_pct` (default 80), flags, alarmas. Un bloque con ver distinta (p.ej. v5) no se migra: vuelven los defaults.  
Programas: `ee_heat` (delay), `ee_tune`. Rampas: `ee_ramp`. No hay `ee_pre`.  
Picos de autotune y la fase viva no se guardan.

## Compilación

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
