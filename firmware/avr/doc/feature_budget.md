# Presupuesto de features (flash / core / minify)

Documento vivo: **actualizar la columna de coste tras cada `make size`** (o al menos tras cada PR que toque firmware).  
**Guardián de agentes:** skill [`.cursor/skills/hotplate-feature-budget/SKILL.md`](../../.cursor/skills/hotplate-feature-budget/SKILL.md) — todos los skills de feature deben invocarlo tras tocar flash/UI.  
Complementa: [product_features.md](product_features.md) · [program_flows.md](program_flows.md) · [architecture.md](architecture.md) · [usb-automation.md](usb-automation.md) · [ui_style_guide.md](ui_style_guide.md) · [pid_control.md](pid_control.md) (C6/C7).

**MCU:** ATmega16 · Flash **16384 B** · Medición: `cd firmware/avr && make size`  
**Última medición de referencia:** Program **15924 B** (97,2 %) · Data **293 B** · EEPROM **62 B** (2026-09-29).

---

## Cómo usar esta tabla

| Columna | Significado |
|---------|-------------|
| **Clase** | `CORE` = no se sacrifica por margen; `SHELL` = UI/adaptador; `CFG` = ajuste AT/EEPROM; `OPT` = opcional / candidato a recorte |
| **Reglas core** | Contrato que no se puede romper |
| **Minify seguro** | Hasta dónde se puede achicar **sin** quitar la feature base |
| **Full deseado** | Estado “aprobado” de producto (hacia dónde volver si hubo regresión) |
| **Coste** | Flash estimado o medido. `Δ` = ahorro/coste al quitar o restaurar. Si no hay Δ, poner “medir” |

### Política de decisión (obligatoria)

1. **Antes** de meter o sacar código: mirar esta tabla + `make size`.
2. **Nunca** financiar una feature nueva quitando **UI aprobada** (iconos 16×16, temp a 2×, glifos/layout de [ui_style_guide.md](ui_style_guide.md)) ni **core térmico** (HEAT/PREHEAT/rampas/PI/safety).
3. Preferir: drivers no usados, AT redundante, flags de producto descartados, algoritmos elegantes pero caros.
4. Tras el cambio: actualizar **Coste** y la fila **Medición global**.

---

## Medición global

| Fecha | Program (B) | Libre | Notas |
|-------|-------------|-------|-------|
| 2026-09-29 | 16374 | 10 | Sin `FONT_ICONS` ni `FONT_5X7_X2` enlazados (regresión UI). `SND`/`RN`/`KD` fuera de `$CF`. |
| 2026-09-29 | 16588 | −204 | Paso intermedio: S2+S3 re-enlazados sin optimizar (**+214 B**). No cabe |
| 2026-09-29 | 16326 | 58 | + Fase A: F2/U5/U7 fuera (`buzz_nav_*`, `snd`, `kd` de estado/AT/cfg; API buzzer sin `st`) **−262 B** |
| 2026-09-29 | 16128 | 256 | + Fase B: D1 blit de glifos con buffer de bytes y un solo camino COLS/ROWS **−198 B** |
| 2026-09-29 | 16096 | 288 | Icono USB fuera de `FONT_ICONS` (−32 B) y `pid_atune_result` sin kd. Data 289 B. UI aprobada enlazada |
| 2026-09-29 | 16044 | 340 | Pitido de navegación, de arranque, de parada y de salida USB eliminados **−52 B** |
| 2026-09-29 | 15024 | 1360 | Fuera la fase al % de la rampa 1 y `AT+CFG=A` (el autotune escribe Kp/Ki al terminar). Data 286 B **−1020 B** |
| 2026-09-29 | 15536 | 848 | Reloj DLY `hh:mm` (tope 12:00). Base de este cambio de HotPanel. Data 283 B |
| 2026-09-29 | 15696 | 688 | Setup: 2 px bajo el header y 1 px entre filas. Heat: `°C` en la consigna de rampa y `mm:ss` transcurrido. **+160 B**. Data 283 B |
| 2026-09-29 | 15676 | 708 | Stream de sesión: `$HP` a 1 Hz en todo USB (mismo formateador) y UART a 19200. **−20 B**. Data 283 B, EEPROM 62 B |
| 2026-09-29 | 15698 | 686 | Setup: banda invertida de 9 px (1 px sobre y bajo la letra) + 1 px de separación; 4 filas visibles con desplazamiento. **+22 B**. Data 283 B |
| 2026-09-29 | **15924** | **460** | Temperatura en `FONT_8X12` nativa (trazo 2 px) con `°C` y `ERR`; `USB` sigue en 5×7 a 2×. **+226 B**. Data 293 B (+10: descriptor de fuente), EEPROM 62 B |

---

## Tabla de features / programas / subprocesos / CFG

| ID | Feature / pieza | Clase | Reglas core | Minify seguro | Full deseado | Coste (flash) |
|----|-----------------|-------|-------------|---------------|--------------|---------------|
| C1 | **Scheduler cooperativo** (super-loop, ticks, delays no bloqueantes) | CORE | Sin `_delay_ms()` en caminos calientes; ver [temporizacion_no_bloqueante.md](temporizacion_no_bloqueante.md) | Compactar helpers; no fusionar en un solo hilo bloqueante | Mantener | Incluido en `main` + `avr_delay` · **medir Δ** si se toca |
| C2 | **AppState + ConfigStore** (EEPROM v8, única fuente de verdad) | CORE | Ver distinta → defaults; salidas OFF en fault; dirty telem | Compactar validación; no fragmentar estado | EEPROM v8 + bandas BN/BX | `cfg_store.c` grande en fuente · **medir** |
| C3 | **Programa HEAT** (DELAY→PREHEAT→RUN/HOLD→ALARM→COOL→DONE) | CORE | Rampas no decrecientes; no mezclar USB+MANUAL; aire solo al final | Acortar strings de fase; no quitar fases | Perfil SMD usable en banco | `program_runner` · **medir** |
| C4 | **PREHEAT** (fase, no programa AT) | CORE | % de Ramp1; meseta + histéresis; overheat timeout | Ajustar defaults; no eliminar fase | `preheat_en`/`pct`/`stabilize`/`BN`/`BX` | Parte de C3 |
| C5 | **Rampas** (dato EEPROM, approach + meseta `hold_s`) | CORE | Approach PI controlado; `hold_s` solo en HOLD; no decrecientes | Menos escalones en UI no reduce flash de lógica | 4 huecos + `$R` | Parte de C3 + `CFG=R` |
| C6 | **PI predictivo** (`t_ref` + lookahead, anti-windup) | CORE | Duty → SSR; Kd lazo = 0; `pid_on_set_step` entre SET | Tunear RISE/LOOKAHEAD compile-time; no quitar gobernador | Precisión sin overshoot grave | `pid.c` ~3 KB fuente · **medir .text** |
| C7 | **Autotune** (`PID_TUNE`, solo AT) | CORE (USB) | Solo `AT+RUN=2`; al terminar copia Kp/Ki; no lanzar desde Settings LCD | Compactar Z–N; no quitar el copiado a EEPROM | Mismos campos `AP/AC/AK/AI` en el `$HP` de sesión, sin segunda trama | `pid_atune.c` · **medir** |
| C8 | **Safety / overtemp / sensor fault** | CORE | PTC OFF; `ERROR:7` / FAULT | Sin minify funcional | Mantener | `safety` + hooks · **medir** |
| C9 | **Alarmas de proceso** (`ALARM:2`, beeps READY/FAULT) | CORE | Fin HEAT → alarma; cancel UI ≠ ALARM USB | Fijar reps; no quitar ALARM:2 | Mantener beeps de **proceso** | `buzzer_seq` · **medir** |
| S1 | **Home Heat \| Settings** (2 casillas, overlays) | SHELL | Nunca vistas USB/Settings aparte; dirty rows; i18n | Compactar `home_view` sin cambiar layout | Layout [ui_style_guide](ui_style_guide.md) | Aire de Setup + `°C` de rampa + transcurrido **+160 B** (15536 → 15696). Filas de Setup de 9+1 px con desplazamiento **+22 B** (15676 → 15698) |
| S2 | **Iconos sidebar 16×16** (`FONT_ICONS`) | SHELL / **APROBADO** | Contrato visual; no sustituir por letra si hay margen | Comprimir glifos; 2 iconos | **Enlazado** Heat/CFG (+ USB si cabe) | S2+S3 juntos **+214 B** medido · **enlazado** Heat/CFG + separador x=31; USB solo con `-DFONT_ICONS_USB` (+32 B) |
| S3 | **Temperatura `FONT_8X12`** (+ título USB en `FONT_5X7_X2`) | SHELL / **APROBADO** | Temp legible centrada con `°C` | Tabla solo `-.0-9°CER`; no bajar a 5×7 1× salvo emergencia documentada | **8×12 nativa en Heat/USB**, `USB` a 2× | `font8x12` **+226 B** (15698 → 15924) · **enlazado** |
| S4 | **i18n CAPS** (fases / footer) | SHELL | Textos vía `i18n_tr_hash` | Strings más cortos | Labels actuales | Pequeño · **medir** |
| U1 | **Sesión USB** (`AT+MODE`, mutex manual) | CORE-IF | USB y MANUAL no activos a la vez | — | Mantener | `device_session` + AT · **medir** |
| U2 | **Telemetría `$HP`** (T, fase A, SET, DU, RI, …) | CORE-IF | Una trama a 1 Hz en toda la sesión USB, UART 19200, enriquecida en autotune. No tres formateadores | Quitar campos raros; no quitar A/SET/DU/RI | Chart fases + potencia | `telemetry` · stream de sesión **−20 B** (15696 → 15676) · TX 34–54 ms/s |
| U3 | **`$CF` / `$R`** | CFG | Lectura bajo demanda | `KD`/`SND` ya no existen; `RN` omitido | BN/BX/PH/PCT/SB/S/P/AMS + `$R` | Ya minificado parcial |
| U4 | **`AT+CFG=S`** límites | CFG | min≤max, rangos producto | — | Mantener | Bajo |
| U5 | **`AT+CFG=H`** flujo HEAT | CFG | delay 0…43200 s (se guarda h+m), air | **Hecho:** `snd` fuera (6.º argumento → `ERROR:2`) | H sin sonido nav. Reloj hasta 12:00 | Incluido en la medición 15536 |
| U6 | **`AT+CFG=B`** bandas | CFG | bn≤bx | Valorar fusionar en H si cabe línea AT | Mantener BN/BX | Bajo–medio |
| U7 | **`AT+CFG=P`** PID | CFG | Kp/Ki | **Hecho:** `P,kp,ki`; `pid_kd_x10` eliminado del estado (EEPROM: bytes reservados) | Mantener P | Parte de los −262 B de la Fase A |
| U8 | **`AT+CFG=T` / `RUN=2`** | CFG | Solo USB. No existe `CFG=A` | Compactar parse | Mantener | Medio |
| U9 | **`AT+CFG=R` / `R?`** | CFG | Perfil no decreciente | — | Mantener | Medio |
| F1 | **Flag `cooldown_air_en`** | CFG | Fan solo cooldown final | — | Mantener | Bajo |
| F2 | **Sonido de navegación** | OPT / **DESCARTADO** | Beeps de proceso y el pulso al guardar se quedan | **Hecho:** fuera de estado, `CFG=H`, HotPlate Studio y de HotPanel (cursor, RUN, STOP, EXIT). EEPROM v8 conserva los bytes como `rsv` | **Fuera** | Fase A −262 B; quitar las llamadas del panel **−52 B** |
| D1 | **Driver ST7920** (draw/text/config) | SHELL-DRV | Home usa `draw_band` / GDRAM / clear | La API geométrica ya no se enlazaba (gc-sections). **Hecho:** blit con `uint8_t row[16]` y un solo `st7920_glyph_row` para COLS (1×/2×) y ROWS | Solo API usada por Home | **−198 B** medido. `draw_band` 342 B + `glyph_row` 268 B |
| D2 | **MAX31865 + soft SPI** | CORE-DRV | Lectura válida para PID/safety | — | Mantener | Necesario |
| D3 | **Fonts** `font5x7` + `font8x12` + icons | SHELL | Guía UI | `font8x12` solo con los glifos de temperatura (`tools/gen_fonts.py`) | 5×7 + 8×12 + icons + X2 (USB) | icons ver S2; 8×12 ver S3 |

---

## Matriz rápida: ¿de dónde sacar flash?

| Prioridad | Acción | ¿Rompe core/UI aprobada? | Notas |
|-----------|--------|---------------------------|-------|
| ~~P0~~ | ~~Restaurar **S2 + S3**~~ | — | **Hecho** 2026-09-29 |
| ~~P1~~ | ~~Recortar **ST7920** (D1)~~ | — | **Hecho** (−198 B) |
| ~~P2~~ | ~~Eliminar **F2**~~ | — | **Hecho** |
| ~~P3~~ | ~~Acortar **U5**~~ | — | **Hecho** |
| P4 | Compactar parse AT / `$CF` redundante | No si se mantiene chart | Cuidado con HotPlate Studio |
| P5 | Micro-opts PID/autotune (mismo comportamiento) | No si tests verdes | No “elegancia” cara |
| **Prohibido** | Quitar iconos / temperatura 8×12 / HEAT / PI / safety para meter otra feature | Sí | Ya ocurrió; no repetir |

---

## Procedimiento de actualización

```bash
cd firmware/avr && make clean && make && make size
# Anotar Program/Data/EEPROM en “Medición global”
# Si el PR toca una fila: actualizar Coste (Δ medido) y Full vs actual
make usb-host-test flow-host-test
```

Historial breve de Δ conocidos (aprox., LTO):

| Cambio | Δ Program (aprox.) |
|--------|-------------------|
| Quitar enlace `FONT_ICONS` + uso `FONT_5X7_X2` (medido juntos, driver antiguo) | −214 B |
| Quitar un `kv_u` de `$CF` | −15…25 B |
| F2 + U5 + U7 (sonido nav, `snd`, `kd`) | −262 B |
| D1 blit de glifos en bytes | −198 B |
| Icono USB fuera de `FONT_ICONS` | −32 B |
| Aire de Setup (2 px / 1 px) + `°C` en la fila de rampa + `mm:ss` transcurrido | +160 B |
| Temperatura en `FONT_8X12` nativa, con `°C` y `ERR` | +226 B |

---

## Relación con otros docs

- Qué debe hacer el producto: [product_features.md](product_features.md)  
- Cómo fluye: [program_flows.md](program_flows.md)  
- Capas: [architecture.md](architecture.md)  
- AT: [usb-automation.md](usb-automation.md)  
- UI: [ui_style_guide.md](ui_style_guide.md)  
- Plan de trabajo para recuperar margen **sin** romper lo de arriba: [optimization_plan.md](optimization_plan.md)
