# Inventario de conocimiento — SMI Soldering Hot Plate

Índice de qué documento manda y qué código existe. Si este inventario contradice el código, manda el código y hay que corregir el inventario.

Última revisión: 2026-09-26.

## Qué leer

| Pregunta | Documento |
|----------|-----------|
| Qué hace el producto y cómo navega el usuario | [product_features.md](product_features.md) |
| Dónde está cada módulo y cómo corre el bucle | [architecture.md](architecture.md) |
| Tipografía, foco, dirty rows | [ui_style_guide.md](ui_style_guide.md) |
| Comandos AT y trama `$HP` | [usb-automation.md](usb-automation.md) |
| Pines del MCU | [atmega16_pin_definition_hotplate.md](atmega16_pin_definition_hotplate.md) frente a `config/board_pins.h` |
| Cómo compilar | [../README.md](../README.md) |

## Documentos

| Documento | Estado | Notas |
|-----------|--------|-------|
| `product_features.md` | Vigente | Fuente de producto. Flujos de programa y de menú. |
| `architecture.md` | Vigente | Fuente de arquitectura. Mapa de archivos y super-loop. |
| `ui_style_guide.md` | Vigente con matices | El sistema visual incluye 6×8, 8×12 e iconos 8×8. El Makefile actual los deja fuera (`NO_FONT_6X8`, `UI_NO_ICONS`; 8×12 e icono ENTER sí entran por la vista USB). La cabecera linkeada es 5×7 en negrita sintetizada. |
| `usb-automation.md` | Vigente | Contrato AT. El detalle de fases está en `product_features.md`. |
| `atmega16_pin_definition_hotplate.md` | Vigente | PTC1 = PD7, PTC2 = PD6. Confirmar contra `board_pins.h` si se toca el esquemático. |
| `optimizacion_temporizados.md` | Referencia | Patrón `delay_ms()` no bloqueante. Los ejemplos de animación no son el menú actual. |
| `delays_no_bloqueantes.md` | Referencia | Mismo patrón. Menciona una API de animación que el HOME no usa. |
| `animaciones_no_bloqueantes.md` | Referencia | Pipeline GIF → ST7920. No está en el menú de producto. |
| `mapeo_offset_bits_pantalla.md` | Referencia | Diffs de bitmap. |
| `bitmap_icono_8x8_carita.md` | Histórico | Tutorial de un icono que no está en el firmware linkeado. |
| `prompt_stitch_ui.md` | Ausente | El inventario anterior lo citaba. No está en `firmware/avr/doc/`. |

`lib/*/README.md` describen drivers. Si discrepan del `.c` (chip-select, modos SPI), manda el fuente.

## Código de aplicación

```
src/main.c                      super-loop
src/app/app_config.h            constantes, índices HOME, EEPROM v3
src/app/app_state.h             app_state_t, vistas, fases, programas
src/ui/ui_router.c              VIEW_HOME | VIEW_USB
src/ui/home_view.c              MENU, RUN, SETTINGS
src/ui/usb_view.c               sesión USB
src/ui/core/ui_window.c         ventana de 3 filas sobre N ítems
src/ui/core/ui_display.c        refresh por fila sucia
src/ui/core/ui_components.c     cabecera, bandas 5×7, formato de fila
src/ui/core/ui_text.c           temperatura, mm:ss, líneas
src/services/program/           program_runner — fases
src/services/pid.c              ventana temporal; lo llama program_tick
src/services/pid_atune.c        autoajuste por relé (enlazado)
src/services/cfg_store.c        EEPROM global + programa + rampas
src/services/sensor_service.c   PT100
src/services/safety.c           límite 200 °C
src/services/outputs.c          banco PTC y fan
src/services/device_session.c   MANUAL / USB
src/services/at_cmd.c           parser AT
src/services/telemetry.c        $HP
src/services/buzzer_seq.c       secuencias de beep
```

No existen `ui_menu`, `core_demo_view` ni un `process.c` suelto. `process.h` es un alias de `program/program.h`.

## Drivers (`lib/`)

| Módulo | Rol |
|--------|-----|
| `avr_delay` | Timer0 → `delay_ms` no bloqueante |
| `avr_spi` | SPI hardware del ST7920 |
| `avr_soft_spi` | SPI software del MAX31865 |
| `st7920` | LCD 128×64, GDRAM parcial, texto |
| `max31865` | PT100 |
| `encoder` | Polling y antirrebote |
| `ports` | PTC, fan, buzzer |
| `avr_uart` | UART 9600, RX por interrupción |
| `fonts` | En el binario solo entra 5×7. 6×8, 8×12 e iconos están excluidos en el Makefile |
| `i18n` | `i18n.c` + `i18n_keys.h`. Tabla PROGMEM en español. La UI llama `i18n_tr_hash(I18N_*)` |

u8g2 y el driver Adafruit del MAX31865 no están en el árbol.

## Hechos que no hay que reabrir

| Tema | Dónde quedó |
|------|-------------|
| PTC1 / PTC2 | Esquemático y `board_pins.h`: PTC1 = PD7, PTC2 = PD6 |
| Encoder | `ENC_CW_IS_POSITIVE`: horario = +1 = el cursor baja |
| Reloj | `F_CPU` 8 MHz en el Makefile. No subirlo porque el BOM liste 16 MHz sin medir el cristal |
| Un firmware | Sin perfiles PANEL/USB. HOME y USB conviven en el mismo binario |
| RAMPS | Fase y bloque EEPROM. No es `program_id_t` ni ítem que arranque un ciclo |

## Huecos reales

- No hay vista aparte de alarma. `PH_ALARM` se refleja en HOME en marcha / USB.
- Sin editor UI de setpoint, delay ni escalones de rampa (`AT+TEMP` / `AT+DELAY` / `AT+RAMP`). Ganancias PID sí: Ajustes → PID.
- Autotune: USB reemite `$HP` a 1 Hz. No hay `$HP,PLOT` ni página de curva (flash). Picos y ganancias quedan en `app_state`; la fila Auto muestra RUN/OK/FAIL.
- No hay guía eléctrica del PCB más allá del KiCad y del CSV de BOM.
- `ui_style_guide.md` puede describir paths de iconos/fuentes grandes no presentes en el binario.

## Skills

| Skill | Cuándo |
|-------|--------|
| `hotplate-feature-development` | Pantallas, térmico, programas, EEPROM |
| `hotplate-app-state` | Menús y campos de `app_state_t` |
| `hotplate-usb-mode` | Sesión USB, AT, `$HP` |
| `st7920-animated-icons` | GIF → animación ST7920 |
