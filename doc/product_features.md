# Características del producto — SMI Soldering Hot Plate

Maestro de fases, alarmas y EEPROM: [program_flows.md](program_flows.md). Si este archivo discrepa, manda ese. Código: [architecture.md](architecture.md). AT: [usb-automation.md](usb-automation.md).

Firmware `firmware/avr/`, ATmega16 @ 8 MHz. Actualizado: 2026-09-28.

## Decisiones

| Tema | Contrato |
|------|----------|
| Programa principal | **HEAT** (`delay_s==0` inmediato; `>0` espera) |
| PREHEAT | Fase de HEAT (`preheat_en`). No es programa AT |
| PID_TUNE | Solo AT (`AT+RUN=2`). Settings no lanza Auto |
| RAMPS | Dato EEPROM; no lanzable |
| Done / aire | PTC OFF. Fan solo si `cooldown_air_en`, hasta `temp_min_c` (default **50 °C**) |
| Safety / consignas | `temp_min_c` **50..100**; `temp_max_c` 40..250 (también `AT+CFG=S`) |
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

Dos casillas laterales: **Heat** | **Settings**. Sin vistas aparte.  
Heat: temp **FONT_8X12** (margen 3 px + gaps 4 px), fase, `Rx Tset mm:ss`; pie **`RUN`** / **`STOP`**. Cancel UI → IDLE.  
USB: temp + etiqueta **`USB`** + icono 16×16; pie **`OUT`**. Lateral 16×16: plancha / llave.  
Settings: **sin header** — lista R1…R4 + **`DLY`** desde y=0; PRESS entra al listado; pie **`OUT`** → Heat. Aire / PID / autotune solo AT.

Labels LCD (i18n, CAPS inglés): `IDLE` `WAIT` `PREHEAT` `STABLE` `ALM` `RUN` `END` `ERR` `OUT` `AIR` `DLY` `OFF` `STOP` `USB`.

## Ajustes (panel Home)

| Fila | Efecto |
|------|--------|
| R1…R4 | Temp/hold; T→bajo desactiva (R1 mínimo = `temp_min`); límites `temp_min`…`temp_max` |
| DLY | `delay_s` de HEAT (±1 min, desde 0). No se edita desde la casilla Heat |

Aire (`cooldown_air_en`), sonido / ESTAB / P% / PID / autotune: solo AT.  
Timeout autotune (`atune_max_s` / `$CF AMS=`): 120..3600 s, default **720**.

## Alarmas

Detalle en [program_flows.md](program_flows.md). Contrato corto:

- Sobretemperatura (`temp ≥ temp_max_c`, lectura válida): UART **`ERROR:7`**, PTC OFF, fase `PH_FAULT`, `$HP` `A=FAULT`, sin beep.
- La columna Beep nombra una categoría (ancho del pulso + repeticiones), no una frecuencia en Hz.
- El token de fase va en `$HP` `A=`, no en una línea UART de alarma aparte (salvo `ALARM:n` de proceso).

## EEPROM v6

Global: ganancias PID, `atune_cycles_target`, `atune_hyst_c_x10`, `atune_max_s`, `temp_min_c`, `temp_max_c`, `preheat_en`, `preheat_pct` (default 80), flags, alarmas. Un bloque con ver distinta (p.ej. v5) no se migra: vuelven los defaults.  
Programas: `ee_heat` (delay), `ee_tune`. Rampas: `ee_ramp`. No hay `ee_pre`.  
Picos de autotune y la fase viva no se guardan.

## Compilación / flash

Flash ATmega16 = **16384 B**. Medir siempre:

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
