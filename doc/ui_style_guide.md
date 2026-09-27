# Guía de estilo UI — ST7920 128×64

Fuente de verdad para tipografía, espaciado, foco e iconos.
Complementa [architecture.md](architecture.md) (capas y binario actual) y
[product_features.md](product_features.md) (navegación).

El sistema visual de abajo incluye 6×8, 8×12 e iconos 8×8. El Makefile
actual los excluye (`NO_FONT_6X8`, `UI_NO_ICONS`; 8×12 e icono ENTER sí entran por la vista USB): la
cabecera linkeada es 5×7 con negrita sintetizada y las listas van por
`ui_display_refresh_focus`.

## Hardware

| Recurso | Límite |
|---------|--------|
| Resolución | 128 × 64 px |
| Color | **1 bit** (ON/OFF). Sin gradientes, anti-alias ni sombras suaves |
| “Sombra” / énfasis | Solo **inversión** (fondo ON, glifo OFF) o trazo negrita |
| Entrada | Encoder: horario = cursor **baja** (`+1`) |

## Fuentes (`lib/fonts/` + `ui_font.h`)

| Papel | Constante | Glifo | Uso |
|-------|-----------|-------|-----|
| SMALL | `UI_FONT_SMALL` / `FONT_5X7` | 5×7 | Filas BODY, menús (~21 cols) |
| NORMAL | `UI_FONT_NORMAL` / `FONT_6X8_BOLD` | 6×8 negrita | Títulos en cabecera |
| LARGE | `UI_FONT_LARGE` / `FONT_8X12` | 8×12 | Temperatura / valores grandes |
| ICONS | `UI_FONT_ICONS` / `FONT_ICONS` | 8×8 | Solo `ICO_ENTER` (confirmar). Fuera del binario con `UI_NO_ICONS` |

- Escalas: `UI_X1` / `UI_X2` / `UI_X3` vía `ui_text_draw(..., scale, inv)`.
- Grado: `"150" FONT_DEG "C"` (no `"\xB0C"`).
- API: `ui_text_draw(x, y, h, str, font, scale, inv)` — `h` = alto de **banda**; el glifo se centra en ella.
- Generación: `tools/gen_fonts.py` → `font6x8_bold.c`, `font8x12.c`.

### Roles de producto (mapa a fuentes)

| Rol | Render en firmware |
|-----|--------------------|
| TITLE / HEADER | Banda invertida `UI_TITLE_H` + `FONT_6X8_BOLD` (`ui_comp_draw_header`) |
| BODY | `FONT_5X7` 1x en filas de lista |
| VALUE_LG | `FONT_8X12` ± escala 2x/3x |
| ACTION | Fila invertida (foco) o `[ LABEL ]` (`ui_comp_format_action`) |
| META | BODY alineado a la derecha (`ui_line_put_right`) |
| BOLD | NORMAL 6×8 (avance 7: no pegar glifos) |

## Layout y espaciado

Constantes en `ui_components.c` / `ui_display.c`:

| Token | Valor | Notas |
|-------|-------|-------|
| `UI_TITLE_H` | 15 px | Impar: 7 px glifo + ~4 px arriba/abajo |
| `UI_ROW_H` | 10 px | Banda de fila BODY |
| `UI_ROW_ICON_DY` | 1 px | Icono 8×8 un poco más abajo que el texto 5×7 |
| Primer BODY `y` | 16 | Justo bajo la cabecera |
| Paso típico filas | 12 px | p.ej. `{16,28,40,52}` |
| Indent label | col 2 | `ui_comp_format_*` deja 2 espacios |
| `LINE_LEN` | 21 | `app_config.h` — no exceder |

HOME usa `{16,28,40,52}`. Al añadir vistas, **no** solapar bandas: `y[i+1] >= y[i] + UI_ROW_H`.

## Foco, inversión e iconos

1. Cabecera: siempre invertida; limpia GDRAM (`st7920_clear_gdram`) solo al entrar / `frame_dirty`.
2. Fila con foco: `st7920_draw_text_gdram_inv` (o `ui_display_refresh_icons` con `inv=1`).
3. Iconos 8×8: en cabecera (siempre que quepa) y **en la fila con foco** en listas con `ui_display_refresh_icons`. Resto de filas: solo texto.
4. El binario actual define `UI_NO_ICONS`: cabecera centrada sin icono 8×8; filas vía `ui_display_refresh_focus` (texto 5×7). `ui_display_refresh_icons` no se compila.
5. MODO USB: solo `AT+MODE=1`. HOME: barra Heat | Settings.
   Cabecera negrita solo en Ajustes/USB; Home no usa cabecera de título.
   Temperatura 8×12 en el panel; pie `Salir ↵` en marcha (x≥32) y en USB.
   Divisoria Home en x=31. Cada zona es una banda; no compartir bloques de 16 px.

No inventar sombras, bordes dobles ni chips redondeados: el LCD no los soporta.

## Dirty / pintado

- `frame_dirty` → redibujar header (clear + título).
- `row_dirty` bitmask → solo esas bandas.
- `st7920_render()` **prohibido** en refresh parcial.
- No pasar buffers de stack a APIs que guarden el puntero hasta un render diferido.

## Textos (i18n)

- Catálogo: `lib/i18n/i18n.c` (PROGMEM, solo español, id denso).
- Call sites: `i18n_tr_hash(I18N_*)` — IDs en `i18n_keys.h`. Copiar el puntero antes de la siguiente consulta.
- Labels en **mayúsculas** español en UI de producto.

## Checklist al crear una pantalla

- [ ] Header con `ui_comp_draw_header(title, ICO_*)`
- [ ] `row_y[]` sin solapes; 4 filas máx visibles (`ROW_COUNT`)
- [ ] Foco = fila invertida; encoder CW = `+1`
- [ ] Textos vía `I18N_*`
- [ ] `make size` reportado
