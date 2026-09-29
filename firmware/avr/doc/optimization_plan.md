# Plan de optimización de firmware (sin romper cores ni UI aprobada)

Contexto: flash **~16374 / 16384 B**. La UI visual aprobada (iconos 16×16, temperatura 2×) está **regresionada** por recortes previos. Este plan busca **margen real** en drivers/AT/CFG descartable y **devolver** esa UI, no seguir financiando features a costa del shell.

Maestro de reglas: [feature_budget.md](feature_budget.md).  
Agente/skill guardián: `.cursor/skills/hotplate-feature-budget/SKILL.md` (actualizar el doc tras cada `make size`).
Producto: [product_features.md](product_features.md) · Flujos: [program_flows.md](program_flows.md) · AT: [usb-automation.md](usb-automation.md) · UI: [ui_style_guide.md](ui_style_guide.md).

---

## Objetivos

1. Liberar **≥ 350–450 B** de flash (margen cómodo + restaurar icons + X2).
2. **No** alterar comportamiento térmico aprobado (HEAT / PREHEAT / HOLD / PI / autotune / safety).
3. **Restaurar** contrato UI de [ui_style_guide.md](ui_style_guide.md).
4. Alinear producto: **sacar sonido de navegación** de features, AT y HotPlate Studio (beeps de proceso se quedan).

Cada paso: `make size` + `usb-host-test` (y `flow-host-test` / `pid-host-test` si aplica); anotar Δ en [feature_budget.md](feature_budget.md).

---

## Fase A — Inventario AT / CFG (qué exponer)

### Mantener (útiles para operación y chart)

| Comando | Por qué |
|---------|---------|
| `AT+MODE` | Mutex USB/manual |
| `AT+RUN=1` / `AT+RUN=2…` / `AT+STOP` | Arranque HEAT y autotune |
| `AT+CFG?` → `$CF` | Ajustes de HotPlate Studio |
| `AT+CFG=R` / `R?` → `$R` | Soldering Profile |
| `AT+CFG=S` | Límites seguros |
| `AT+CFG=H` | Flujo HEAT (en, pct, stab, delay, air) |
| `AT+CFG=B` | Bandas BN/BX (o fusionar luego en H si cabe `AT_LINE_MAX`) |
| `AT+CFG=P` | Kp/Ki (Kd fijo 0) |
| `AT+CFG=T` / `A` | Autotune |
| `$HP` | Chart: fase, SET, DU, RI, autotune AP… |

### Recortar o dejar de documentar como feature

| Ítem | Acción propuesta | Riesgo |
|------|------------------|--------|
| **`snd` en `AT+CFG=H`** | Quitar parámetro; dejar beeps de proceso siempre según alarmas | Bajo — alinear con “sin sonido nav” |
| **`buzz_nav_en` / `buzz_nav_reps` en EEPROM** | Fijar compile-time o eliminar en bump EEPROM v9 | Medio (bump ver) |
| **Ajustes de HotPlate Studio “Sonido de navegación”** | Quitar control de producto | Bajo |
| **`KD` en `AT+CFG=P`** | Aceptar solo `P,kp,ki` o forzar kd=0 sin parse | Bajo |
| **Campos `$CF` ya omitidos** (`SND`, `RN`, `KD`) | No reintroducir | — |
| **Fusionar `CFG=B` → `CFG=H`** | Solo si la línea AT ≤ 31 chars en peores casos | Medio (compatibilidad con HotPlate Studio) |

**No sacar:** BN/BX, PH/PCT/SB, AIR, AMS, rampas, PID Kp/Ki, límites S.

---

## Fase B — Driver ST7920 (alto ROI)

El Home enlazado usa sobre todo: `st7920_init`, `graphics_mode`, `draw_band`, escritura GDRAM / clear, tipografía vía `st7920_text` / fonts.

API pública con **poca o nula** evidencia de uso en `src/` (candidatos a no enlazar o `#if 0` / split .c):

- `st7920_draw_line`, `st7920_draw_rect`, `st7920_draw_progressbar`
- `st7920_draw_text` (modo texto clásico) si solo se usa GDRAM
- `st7920_print` / `st7920_goto` si no hay callers
- Cola diferida `st7920_render` / `clear_commands` si el camino actual es GDRAM directo
- `st7920_write_frame_pgm` / animaciones si no están en el binario activo

**Plan de trabajo**

1. `avr-nm` / referencias: listar símbolos ST7920 vivos en `firmware.elf`.
2. Partir `st7920_draw.c` en “core GDRAM” vs “primitivos geométricos”; no compilar geométricos.
3. Acortar `st7920_text.c` a glifos 5×7 (+ escala 2× solo si se restaura X2).
4. Medir Δ; **no** tocar layout Home en esta fase.

Expectativa: **100–300 B+** según cuánto esté vivo hoy (confirmar con nm).

---

## Fase C — PID y Autotune (comprimir implementación, no el comportamiento)

Ambos se consideran **funcionando bien**. Objetivo: mismo contrato, menos bytes.

### PID (`pid.c`)

- Mantener: `t_ref`, lookahead, anti-windup, ventana SSR, `pid_on_set_step`.
- Candidatos: unificar clamps; evitar ramas muertas; no reintroducir filtro de tasa caro si el actual basta.
- **No** mover RISE/LOOKAHEAD a EEPROM en este plan (cuesta flash de AT/cfg).
- Validar con `pid-host-test` + traza de banco.

### Autotune (`pid_atune.c`)

- Mantener: bang-bang, Z–N PI, `CFG=A`, stream `$HP`.
- Candidatos: compactar aritmética Ku/Ti; eliminar almacenamiento `Kd` ya siempre 0; reducir locals.
- Validar con flujo AT documentado + `usb-host-test`.

Expectativa realista: **30–100 B** entre ambos si se mide con cuidado (LTO ya aplasta mucho).

---

## Fase D — UI: restaurar lo aprobado (después de A–C)

Orden cuando el libre ≥ ~400 B:

1. Re-enlazar **`FONT_ICONS`** y sidebar 16×16 (Heat / CFG) según [ui_style_guide.md](ui_style_guide.md).
2. Restaurar **temperatura `FONT_5X7_X2`** (y título USB si aplica).
3. Actualizar [feature_budget.md](feature_budget.md): S2/S3 → “enlazado”.
4. Prohibir nuevos PR que vuelvan a bajar S2/S3 sin entrada explícita en el presupuesto.

---

## Fase E — Otros archivos (revisión sistemática)

| Área | Qué mirar | Acción típica |
|------|-----------|---------------|
| `at_cmd.c` | Parser / tablas PROGMEM | Acortar nombres; menos copias |
| `telemetry.c` | Campos `$HP` | No tocar A/SET/DU/RI/AP |
| `cfg_store.c` | Validaciones duplicadas | Compactar clamps |
| `home_view.c` | Lógica Settings R1–R4 | No quitar filas; sí deduplicar edit |
| `buzzer_seq.c` | Tras quitar nav flag | Simplificar API NAV |
| `font8x12.c` | Ya fuera del link | Mantener fuera |
| `features/parked/` | No enlazar | Mantener parked |
| HotPlate Studio `settings_view` | Quitar control SND | Alinear con F2 |

---

## Orden de ejecución recomendado

```mermaid
flowchart LR
  A[A: quitar snd/nav de AT y Studio] --> B[B: podar ST7920 no usado]
  B --> C[C: micro-opts PID/atune]
  C --> M[make size + tests]
  M --> D[D: restaurar icons + temp X2]
  D --> U[Actualizar feature_budget]
```

### Criterio de éxito

| Métrica | Meta |
|---------|------|
| `make size` Program | ≤ **16000 B** tras A–C (margen ≥ 384 B) ideal; mínimo dejar margen para D |
| Tras D | Icons + X2 enlazados y Program ≤ **16384** |
| Tests | `usb-host-test` `flow-host-test` `pid-host-test` OK |
| Banco | HEAT con 2 rampas sin overshoot grave vs baseline actual |
| Producto | Sin feature “sonido navegación”; UI visual restaurada |

---

## Fuera de alcance (ahora)

- Cambiar algoritmo PI (RISE/LOOKAHEAD) salvo experimento de banco documentado.
- Migraciones EEPROM complejas más allá de v9 para quitar `buzz_nav_*`.
- Reintroducir `FONT_8X12`, animaciones parked, o AT de programas eliminados (START_IN, etc.).

---

## Siguiente paso operativo

1. Implementar **Fase A** (snd/nav fuera) — Δ rápido y limpia producto.  
2. **Fase B** con `avr-nm` sobre `build/firmware.elf` para no adivinar símbolos ST7920.  
3. Solo entonces **Fase D** (UI).

Si se pide ejecución en Agent mode: empezar por A + medición en [feature_budget.md](feature_budget.md).
