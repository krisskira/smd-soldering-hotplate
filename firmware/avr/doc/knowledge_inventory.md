# Inventario de conocimiento — SMI Soldering Hot Plate

Índice de qué documento manda y qué código existe. Si este inventario contradice el código, manda el código y hay que corregir el inventario.

Última revisión: 2026-09-28.

## Qué leer

| Pregunta | Documento |
|----------|-----------|
| Qué hace el producto y cómo navega el usuario | [product_features.md](product_features.md) |
| Fases, alarmas, EEPROM (maestro térmico) | [program_flows.md](program_flows.md) |
| Dónde está cada módulo y el super-loop | [architecture.md](architecture.md) |
| Tipografía, foco, dirty rows | [ui_style_guide.md](ui_style_guide.md) |
| Comandos AT y tramas `$HP`/`$CF`/`$R` | [usb-automation.md](usb-automation.md) |
| Pines del MCU | [atmega16_pin_definition_hotplate.md](atmega16_pin_definition_hotplate.md) vs `config/board_pins.h` |
| Cómo compilar | [../README.md](../README.md) |

## Documentos

| Documento | Estado | Notas |
|-----------|--------|-------|
| `product_features.md` | Vigente | Shell / Home / labels LCD |
| `program_flows.md` | Vigente | **Maestro** de fases, beeps, EEPROM v7 |
| `architecture.md` | Vigente | Mapa de módulos y super-loop |
| `ui_style_guide.md` | Vigente | 5×7 + 8×12 + iconos **16×16**; Home vía `home_view` |
| `usb-automation.md` | Vigente | Contrato AT; fases detalladas en `program_flows.md` |
| `atmega16_pin_definition_hotplate.md` | Vigente | PTC1=PD7, PTC2=PD6 |
| `optimizacion_temporizados.md` / `delays_no_bloqueantes.md` / `animaciones_no_bloqueantes.md` | Referencia | Patrones; no son el menú de producto |
| `bitmap_icono_8x8_carita.md` | Histórico | Tutorial; el producto usa 16×16 |

## Código de aplicación

```
src/main.c                      super-loop
src/app/app_config.h            constantes, HOME_DIRTY_*, EEPROM v7
src/app/app_state.h             app_state_t, fases, PROG_HEAT / PROG_PID_TUNE
src/ui/ui_router.c              → home_view
src/ui/home_view.c              Heat + Settings embebido + overlay USB
src/ui/core/ui_components.c     footer 5×7
src/ui/core/ui_text.c           temp 8×12 helpers, mm:ss
src/services/program/           program_runner — fases HEAT/PREHEAT
src/services/pid.c / pid_atune.c
src/services/cfg_store.c        EEPROM global + heat + rampas
src/services/safety.c           corte → ERROR:7 (temp_max_c)
src/services/device_session.c   MANUAL / USB
src/services/at_cmd.c / telemetry.c
```

`ui_display.c` / `ui_window.c`: presentes, **no** enlazados en el Makefile.

## Drivers (`lib/`)

| Módulo | Rol |
|--------|-----|
| `avr_delay` | Timer0 → `delay_ms` |
| `avr_spi` / `avr_soft_spi` | ST7920 / MAX31865 |
| `st7920` | LCD 128×64, bandas GDRAM |
| `max31865` | PT100 |
| `encoder` | Polling |
| `ports` | PTC, fan, buzzer |
| `avr_uart` | 9600 |
| `fonts` | **5×7 + 8×12 + ICONS 16×16** enlazados |
| `i18n` | PROGMEM CAPS inglés abreviado |

## Hechos cerrados

| Tema | Dónde |
|------|-------|
| PTC1/PTC2 | `board_pins.h`: PD7 / PD6 |
| Encoder | CW = cursor baja |
| Reloj | `F_CPU` 8 MHz |
| Programas AT | Solo HEAT (`RUN=1`) y PID_TUNE (`RUN=2`); PREHEAT es fase |
| RAMPS | Bloque EEPROM; no lanzable |
| Flash | 16384 B; medir con `make size` |

## Huecos / límites

- Sin vista aparte de alarma (`PH_ALARM` en Home/USB).
- Settings UI: R1…R4 + DELAY. PID / aire / ESTAB / P% / autotune solo AT.
- Autotune: `$HP` 1 Hz; picos en `pid_atune` (no en `app_state`); sin `$HP,PLOT`.
- Sin guía eléctrica aparte del KiCad + datasheets en `hardware/`.

## Skills

Ver [AGENTS.md](../../../AGENTS.md) en la raíz del monorepo.
