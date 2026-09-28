# Guía de estilo UI — ST7920 128×64

Fuente de verdad para tipografía, espaciado, foco e iconos en el **binario actual**.
Complementa [architecture.md](architecture.md) y [product_features.md](product_features.md).

Actualizado: 2026-09-28.

## Hardware

| Recurso | Límite |
|---------|--------|
| Resolución | 128 × 64 px |
| Color | **1 bit** (ON/OFF). Sin gradientes, anti-alias ni sombras suaves |
| Énfasis | Solo **inversión** (fondo ON, glifo OFF) |
| Entrada | Encoder: horario = cursor **baja** (`+1`) |

## Fuentes enlazadas (`lib/fonts/`)

| Papel | Fuente | Uso |
|-------|--------|-----|
| BODY / footer / fases | `FONT_5X7` | Menús, pies, labels i18n (~15 cols útiles en panel) |
| Temperatura | `FONT_8X12` | Valor centrado en panel Heat/USB |
| Iconos | `FONT_ICONS` | **16×16** nativos: Heat, Settings, USB (`ui_icons.h`) |

No hay `FONT_6X8` ni iconos 8×8 en el Makefile actual. Flash ≈ **16384 B (100%)**.

## Layout HOME (`home_view.c`)

| Zona | x | Notas |
|------|---|-------|
| Sidebar | 0..31 | Dos casillas 32 px (Heat / Settings), icono 16×16 centrado, separador x=31 |
| Panel | 32..127 | Temp / fase / info o lista Settings / overlay USB |
| Footer | y=54, h=10 | Labels: **`RUN`** / **`STOP`** / **`OUT`** (sin glifo ↵) |

Heat: temp (y≈3) → fase → `Rx Tset mm:ss`.  
USB: temp → **`USB`** → icono 16×16.  
Settings: **sin header**; filas R1…R4 + **`DLY`** desde y=0.

Pintado: bandas `st7920_draw_band` + dirty flags (`HOME_DIRTY_*`). `ui_display.c` / `ui_window.c` existen pero **no** se enlazan.

## Textos (i18n)

- Catálogo: `lib/i18n/i18n.c` + IDs en `i18n_keys.h`.
- Call sites: `i18n_tr_hash(I18N_*)`.
- Labels LCD: CAPS **inglés** abreviado (`PREHEAT`, `STABLE`, `ALM`, `ERR`, `DLY`, `OUT`, `USB`, …).

## Checklist al tocar UI

- [ ] Dirty rows; no wipe completo del panel cada tick
- [ ] Textos vía `I18N_*` (o literal justificado en flash)
- [ ] Encoder CW = cursor baja
- [ ] `make size` ≤ 16384
