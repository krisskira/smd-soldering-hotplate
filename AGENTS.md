<!-- SMI Soldering Hot Plate — keep under ~150 lines -->
<!-- Last updated: 2026-10-04 -->

# SMI Soldering Hot Plate

## Stack

- Firmware: C bare-metal, avr-gcc, ATmega16 @ **8 MHz**
- Display: ST7920 128×64 (SPI HW)
- Sensor: MAX31865 + PT100 (SPI SW)
- Heat: MOC3021 + BT136 (SSR)
- PCB: KiCad (`hardware/pcb/`)
- Datasheets: `hardware/datasheets/`
- Mecánica 3D: `mechanical/`
- HotPlate Studio: `hotplate-studio/`
- Diseño de esa app: `hotplate-studio/design/`

## Docs

- Producto (+ mapa código): [firmware/avr/doc/product_features.md](firmware/avr/doc/product_features.md)
- Flujos: [program_flows.md](firmware/avr/doc/program_flows.md)
- Arquitectura: [architecture.md](firmware/avr/doc/architecture.md)
- USB: [usb-automation.md](firmware/avr/doc/usb-automation.md)
- Presupuesto features/flash: [feature_budget.md](firmware/avr/doc/feature_budget.md) (skill **hotplate-feature-budget**)
- PI / Autotune portable: [pid_control.md](firmware/avr/doc/pid_control.md) (skill **hotplate-pid**)
- Plan optimización: [optimization_plan.md](firmware/avr/doc/optimization_plan.md)
- Erratas / mejoras futuras: [mejoras_futuras.md](firmware/avr/doc/mejoras_futuras.md)

**Core** y **UI aprobada** (iconos, temperatura 8×12) mandan sobre AT opcional. Flash: `make size` + actualizar `feature_budget.md`.

## Programs

| ID | UI | USB | Notas |
|----|----|-----|-------|
| HEAT | Home | `AT+RUN=1` | Retraso `hh:mm`, 00:00 = inmediato, tope 12:00. PREHEAT fase. Rampas no decrecientes. PI predictivo |
| PID_TUNE | No | `AT+RUN=2` | Autotune PI → EEPROM al terminar |
| RAMPS | — | `AT+CFG=R` | No lanzable; perfil ascendente/igual |

## Skills / agents

| Skill / agente | Uso |
|----------------|-----|
| hotplate-feature-budget | Guardián `feature_budget.md` · `make size` · UI aprobada |
| hotplate-pid | PI / autotune · doc `pid_control.md` |
| hotplate-heating | HEAT + Home (`°C` de rampa, transcurrido) |
| hotplate-preheat | Fase PREHEAT de HEAT |
| hotplate-usb-mode | AT / `$HP`. Stream de sesión: un `$HP` a 1 Hz en USB, UART 19200 (`usb-automation.md`) |
| hotplate-app-state | Menús / EEPROM v8 |
| hotplate-feature-development | Features generales (siempre consulta budget) |
| st7920-animated-icons | Iconos animados LCD (parked; medir flash antes de enlazar) |

Agentes en `.cursor/agents/` delegan al skill homónimo; el de budget es obligatorio tras tocar flash.

## Critical Rules

- ALWAYS leer product_features + program_flows + architecture; si toca flash/UI → skill **hotplate-feature-budget**.
- ALWAYS salidas OFF al boot / fault / overtemp (`temp_max_c`).
- ALWAYS dirty rows; textos `i18n_tr_hash`.
- ALWAYS actualizar `feature_budget.md` (medición) tras cambios de tamaño — nunca dejar el doc desactualizado.
- ALWAYS en trabajo PID/autotune: leer `pid_control.md` completo.
- NEVER financiar features quitando UI aprobada (iconos 16×16, temperatura FONT_8X12) ni core térmico.
- NEVER reintroducir START_IN/STOP_IN, PROG_TIMED, RAMPS como programa, PANEL.
- NEVER PREHEAT en menú Home.
- NEVER vista USB ni Settings aparte: overlays en Home (`AT+MODE=1` / casilla Ajustes).
- NEVER mezclar USB y MANUAL activos.
- F_CPU 8 MHz. Encoder CW = cursor baja.

## Development

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
