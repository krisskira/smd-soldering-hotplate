<!-- SMI Soldering Hot Plate — keep under ~150 lines -->
<!-- Last updated: 2026-09-28 -->

# SMI Soldering Hot Plate

## Stack

- Firmware: C bare-metal, avr-gcc, ATmega16 @ **8 MHz**
- Display: ST7920 128×64 (SPI HW)
- Sensor: MAX31865 + PT100 (SPI SW)
- Heat: MOC3021 + BT136 (SSR)
- PCB: KiCad (`hardware/pcb/`)
- Datasheets: `hardware/datasheets/`
- Mecánica 3D: `mechanical/`
- Host UI: `host-ui/`

## Docs

- Producto: [firmware/avr/doc/product_features.md](firmware/avr/doc/product_features.md)
- Flujos: [program_flows.md](firmware/avr/doc/program_flows.md)
- Arquitectura: [architecture.md](firmware/avr/doc/architecture.md)
- USB: [usb-automation.md](firmware/avr/doc/usb-automation.md)

**Core** manda sobre **shell**. Flash: medir con `make size`.

## Programs

| ID | UI | USB | Notas |
|----|----|-----|-------|
| HEAT | Home | `AT+RUN=1` | `delay_s` 0 = inmediato. PREHEAT es fase si `preheat_en` |
| PID_TUNE | No | `AT+RUN=2` | Autotune → `AT+CFG=A` → EEPROM |
| RAMPS | — | `AT+CFG=R` | No lanzable |

## Skills / agents

| Skill | Uso |
|-------|-----|
| hotplate-heating | HEAT + Home delay |
| hotplate-preheat | Fase PREHEAT de HEAT |
| hotplate-pid | PID / autotune |
| hotplate-usb-mode | AT / `$HP` |
| hotplate-app-state | Menús / EEPROM v6 |
| hotplate-feature-development | Features generales |

## Critical Rules

- ALWAYS leer product_features + program_flows + architecture antes de feature.
- ALWAYS salidas OFF al boot / fault / overtemp (`temp_max_c`).
- ALWAYS dirty rows; textos `i18n_tr_hash`.
- NEVER reintroducir START_IN/STOP_IN, PROG_TIMED, RAMPS como programa, PANEL.
- NEVER PREHEAT en menú Home.
- NEVER vista USB ni Settings aparte: overlays en Home (`AT+MODE=1` / casilla Ajustes).
- NEVER mezclar USB y MANUAL activos.
- F_CPU 8 MHz. Encoder CW = cursor baja.

## Development

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test
```
