# Presupuesto de features (flash / core / minify)

Documento vivo: **actualizar la columna de coste tras cada `make size`** (o al menos tras cada PR que toque firmware).  
**Guardián de agentes:** skill [`.cursor/skills/hotplate-feature-budget/SKILL.md`](../../.cursor/skills/hotplate-feature-budget/SKILL.md) — todos los skills de feature deben invocarlo tras tocar flash/UI.  
Complementa: [product_features.md](product_features.md) · [program_flows.md](program_flows.md) · [architecture.md](architecture.md) · [usb-automation.md](usb-automation.md) · [ui_style_guide.md](ui_style_guide.md) · [pid_control.md](pid_control.md) (C6/C7).

**MCU:** ATmega16 · Flash **16384 B** · Medición: `cd firmware/avr && make size`  
**Última medición de referencia:** Program **16374 B** (99,9 %) · Data **271 B** · EEPROM **62 B** (2026-09-29).

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
| 2026-09-29 | 16374 | ~10 | Sin `FONT_ICONS` ni `FONT_5X7_X2` enlazados (regresión UI). `SND`/`RN`/`KD` fuera de `$CF`. |

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
| C7 | **Autotune** (`PID_TUNE`, solo AT) | CORE (USB) | Solo `AT+RUN=2`; apply `CFG=A`; no lanzar desde Settings LCD | Compactar Z–N; no quitar apply | Stream `$HP` AP/AC/AK/AI | `pid_atune.c` · **medir** |
| C8 | **Safety / overtemp / sensor fault** | CORE | PTC OFF; `ERROR:7` / FAULT | Sin minify funcional | Mantener | `safety` + hooks · **medir** |
| C9 | **Alarmas de proceso** (`ALARM:2`, beeps READY/FAULT) | CORE | Fin HEAT → alarma; cancel UI ≠ ALARM USB | Fijar reps; no quitar ALARM:2 | Mantener beeps de **proceso** | `buzzer_seq` · **medir** |
| S1 | **Home Heat \| Settings** (2 casillas, overlays) | SHELL | Nunca vistas USB/Settings aparte; dirty rows; i18n | Compactar `home_view` sin cambiar layout | Layout [ui_style_guide](ui_style_guide.md) | `home_view` · **medir** |
| S2 | **Iconos sidebar 16×16** (`FONT_ICONS`) | SHELL / **APROBADO** | Contrato visual; no sustituir por letra si hay margen | Comprimir glifos; 2 iconos | **Enlazado** Heat/CFG (+ USB si cabe) | Δ restaurar ~**130–200 B** (hist.) · **hoy NO enlazado (regresión)** |
| S3 | **Temperatura FONT_5X7_X2** | SHELL / **APROBADO** | Temp legible centrada con `°C` | Mantener X2; no bajar a 1× salvo emergencia documentada | **X2 en Heat/USB** | Δ restaurar ~**150–180 B** · **hoy 1× (regresión)** |
| S4 | **i18n CAPS** (fases / footer) | SHELL | Textos vía `i18n_tr_hash` | Strings más cortos | Labels actuales | Pequeño · **medir** |
| U1 | **Sesión USB** (`AT+MODE`, mutex manual) | CORE-IF | USB y MANUAL no activos a la vez | — | Mantener | `device_session` + AT · **medir** |
| U2 | **Telemetría `$HP`** (T, fase A, SET, DU, RI, …) | CORE-IF | Suficiente para la gráfica de HotPlate Studio (fases HEAT/autotune) | Quitar campos raros; no quitar A/SET/DU/RI | Chart fases + potencia | `telemetry` · **medir** |
| U3 | **`$CF` / `$R`** | CFG | Lectura bajo demanda | Omitir campos redundantes (`KD`/`SND`/`RN` ya omitidos) | BN/BX/PH/PCT/SB/S/P/AMS + `$R` | Ya minificado parcial |
| U4 | **`AT+CFG=S`** límites | CFG | min≤max, rangos producto | — | Mantener | Bajo |
| U5 | **`AT+CFG=H`** flujo HEAT | CFG | en/pct/stab/delay/air/(snd) | **Quitar `snd`** del comando (feature descartada) | H sin sonido nav | Ahorro esperado **~20–40 B** + HotPlate Studio · **medir** |
| U6 | **`AT+CFG=B`** bandas | CFG | bn≤bx | Valorar fusionar en H si cabe línea AT | Mantener BN/BX | Bajo–medio |
| U7 | **`AT+CFG=P`** PID | CFG | Kp/Ki (Kd=0) | Emitir solo Kp/Ki; no exigir Kd | Mantener P | Bajo |
| U8 | **`AT+CFG=T` / `A` / `RUN=2`** | CFG | Solo USB | Compactar parse | Mantener | Medio |
| U9 | **`AT+CFG=R` / `R?`** | CFG | Perfil no decreciente | — | Mantener | Medio |
| F1 | **Flag `cooldown_air_en`** | CFG | Fan solo cooldown final | — | Mantener | Bajo |
| F2 | **Flag `buzz_nav_en` / reps / `SND`** | OPT / **DESCARTAR de producto** | Beeps de proceso se quedan; nav no es feature | Quitar de `$CF`, CFG=H, ajustes de HotPlate Studio, EEPROM en próximo bump | **Fuera de lista de producto** | Ahorro **~30–80 B** + simplifica HotPlate Studio · **medir** |
| D1 | **Driver ST7920** (draw/text/config) | SHELL-DRV | Home usa `draw_band` / GDRAM / clear | Eliminar API no usada: `draw_line/rect/progressbar`, lista diferida si no se usa | Solo API usada por Home | **Alto potencial** · **medir por símbolo** |
| D2 | **MAX31865 + soft SPI** | CORE-DRV | Lectura válida para PID/safety | — | Mantener | Necesario |
| D3 | **Fonts** `font5x7` (+ icons/X2 cuando restaurados) | SHELL | Guía UI | No reintroducir `font8x12` | 5×7 + icons + X2 | icons/X2 ver S2/S3 |

---

## Matriz rápida: ¿de dónde sacar flash?

| Prioridad | Acción | ¿Rompe core/UI aprobada? | Notas |
|-----------|--------|---------------------------|-------|
| P0 | Restaurar **S2 + S3** cuando haya margen | No — **recupera** UI aprobada | Objetivo de producto |
| P1 | Recortar **ST7920** no usado (D1) | No | Mejor ROI vs quitar iconos |
| P2 | Eliminar **F2** (sonido nav) de AT/EEPROM/HotPlate Studio | No (feature descartada) | Alinea producto |
| P3 | Acortar **U5** (`snd` fuera de CFG=H) | No | Encaja con P2 |
| P4 | Compactar parse AT / `$CF` redundante | No si se mantiene chart | Cuidado con HotPlate Studio |
| P5 | Micro-opts PID/autotune (mismo comportamiento) | No si tests verdes | No “elegancia” cara |
| **Prohibido** | Quitar iconos / temp X2 / HEAT / PI / safety para meter otra feature | Sí | Ya ocurrió; no repetir |

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
| Quitar enlace `FONT_ICONS` | −130…200 B |
| Quitar uso `FONT_5X7_X2` | −150…180 B |
| Quitar un `kv_u` de `$CF` | −15…25 B |

---

## Relación con otros docs

- Qué debe hacer el producto: [product_features.md](product_features.md)  
- Cómo fluye: [program_flows.md](program_flows.md)  
- Capas: [architecture.md](architecture.md)  
- AT: [usb-automation.md](usb-automation.md)  
- UI: [ui_style_guide.md](ui_style_guide.md)  
- Plan de trabajo para recuperar margen **sin** romper lo de arriba: [optimization_plan.md](optimization_plan.md)
