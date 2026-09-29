# Pantalla ST7920 — bitmaps, diffs y animaciones

Guía del **flujo de dibujo** en HotPanel: cómo se representan los píxeles, cómo se aplican los diffs de animación y cómo reproducir una o varias animaciones **sin bloquear** el firmware.

El reproductor de animaciones **no está en el binario de producto**. Vive en `features/parked/st7920_animation.c`. Esta guía sirve cuando una vista (p. ej. gráfico de autoajuste) lo vuelva a enlazar.

| También ver | Para |
|-------------|------|
| [temporizacion_no_bloqueante.md](temporizacion_no_bloqueante.md) | Reloj `avr_delay` (no usar `_delay_ms` en el loop) |
| [ui_style_guide.md](ui_style_guide.md) | Layout aprobado de HotPanel (iconos 16×16, tipografía) |
| [lib/st7920/README.md](../lib/st7920/README.md) | API del driver |
| Skill / agente | `.cursor/skills/st7920-animated-icons/` · `.cursor/agents/st7920-animated-icons.md` |
| Generador GIF→C | `tools/gif_to_st7920_anim.py` |

---

## 1. Convención de bitmaps (base de todo)

`st7920_draw_bitmap` y los frames de animación usan el mismo formato:

| Regla | Detalle |
|-------|---------|
| Orden | Por **filas** (arriba → abajo) |
| Dentro de la fila | Bytes de **izquierda → derecha** |
| Un byte | **8 píxeles** horizontales |
| Bit 7 (MSB) | Píxel **izquierdo** |
| Bit 0 (LSB) | Píxel **derecho** |
| `1` | Píxel encendido · `0` = apagado |

Bytes por fila:

```text
BYTES_PER_ROW = (ANCHO + 7) / 8
```

### Ejemplo didáctico: icono 8×8 (carita)

Sirve para entender MSB = izquierda. El producto usa iconos **16×16** ([ui_style_guide.md](ui_style_guide.md)); este 8×8 es solo tutorial.

```c
const uint8_t icono[] = {
    0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
};
st7920_draw_bitmap(10, 20, 8, 8, icono);
```

Vista (■ = on):

```
       col: 0 1 2 3 4 5 6 7
fila 0:     · · ■ ■ ■ ■ · ·   0x3C  arco superior
fila 1:     · ■ · · · · ■ ·   0x42  lados
fila 2:     ■ · ■ · · ■ · ■   0xA5  ojos + contorno
fila 3:     ■ · · · · · · ■   0x81  contorno
fila 4:     ■ · ■ · · ■ · ■   0xA5  ojos + contorno
fila 5:     ■ · · ■ ■ · · ■   0x99  sonrisa
fila 6:     · ■ · · · · ■ ·   0x42  lados
fila 7:     · · ■ ■ ■ ■ · ·   0x3C  arco inferior
```

Ejemplo de un byte: `0xA5` = `1010 0101` → `■ · ■ · · ■ · ■` (bit 7 → izquierda).

---

## 2. Diffs: de offset a píxel en pantalla

Las animaciones no guardan cada frame completo: guardan el **frame 0** y, para cada frame siguiente, solo los bytes que cambian (**diff**: lista de `offset` + `valor`).

### Qué es el offset

Índice lineal del byte en el buffer, orden **fila-major**:

| Rango de offset | Fila |
|-----------------|------|
| `0 .. BYTES_PER_ROW−1` | fila 0 |
| `BYTES_PER_ROW .. 2×BYTES_PER_ROW−1` | fila 1 |
| … | … |

```c
uint8_t row      = offset / BYTES_PER_ROW;  /* 0 = arriba */
uint8_t col_byte = offset % BYTES_PER_ROW;  /* 0 = izquierda */
```

El byte en `(row, col_byte)` cubre los píxeles `col_byte*8` … `col_byte*8+7` de esa fila.

### Cómo está el valor

El valor del diff es el **byte completo** nuevo (8 bits = 8 píxeles), misma convención MSB = izquierda.

### Coordenadas en pantalla

Con la imagen dibujada en `(base_x, base_y)`:

```text
pixel_x = base_x + col_byte*8 + bit_from_left   /* 0 = izq … 7 = der */
pixel_y = base_y + row
```

Bit 7 del valor → `pixel_x = base_x + col_byte*8`.  
Bit 0 del valor → `pixel_x = base_x + col_byte*8 + 7`.

### Cómo se aplica (lo habitual)

El firmware **no** escribe bit a bit: reemplaza el byte entero en GDRAM.

```c
uint16_t off = diff_offsets[i];
uint8_t  val = diff_values[i];
uint8_t row      = off / BYTES_PER_ROW;
uint8_t col_byte = off % BYTES_PER_ROW;
uint8_t pixel_x  = base_x + (col_byte * 8);
uint8_t pixel_y  = base_y + row;
/* st7920_apply_diff_pgm hace esto en bloque vía el driver */
```

API de bajo nivel:

- `st7920_write_frame_pgm(...)` — frame completo desde PROGMEM  
- `st7920_apply_diff_pgm(...)` — solo los bytes del diff  

---

## 3. Importar un icono animado (GIF → C)

Origen: `icons/source/` (raíz del repo). Los `.c` generados **no** se versionan en el firmware de producto; regenerar cuando hagan falta:

```bash
cd firmware/avr
pip install Pillow
python3 tools/gif_to_st7920_anim.py \
  ../../icons/source/icons8-temperature.gif \
  -o icons/animated/temperature.c \
  --name temperature --size 32
```

Salida PROGMEM: `NAME_frame_0` + diffs + tablas `NAME_diff_offsets/values/counts`, listas para `st7920_animation_t`. Detalle del descriptor: skill `st7920-animated-icons`.

---

## 4. Descriptor y API de animación

Estructura `st7920_animation_t`:

| Campo | Rol |
|-------|-----|
| `frame_0_pgm` | Frame completo en PROGMEM |
| `diff_offsets_pgm` / `diff_values_pgm` / `diff_counts_pgm` | Diffs por frame (índice 0 = frame 1) |
| `width`, `height`, `bytes_per_row`, `bytes_per_frame`, `frame_count` | Dimensiones |

El llamador aporta un **buffer RAM** ≥ `bytes_per_frame`.

### Bloqueante (solo demos)

`st7920_draw_animation(...)` escribe frame 0 y entra en un bucle con `_delay_ms`. **No retorna**; no sirve para HotPanel con varias tareas.

### No bloqueante: `run` / `run_all`

Principio: **configuración → primera llamada = init → ciclo = tick** (mismo reloj que [temporizacion_no_bloqueante.md](temporizacion_no_bloqueante.md)).

- **`st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)`**  
  - `ctx->active == 0` → start (frame 0, init)  
  - `ctx->active == 1` → tick si pasó `interval_ms`  
- **`st7920_animation_run_all(slots, count)`** — varias animaciones sin reescribir el loop

| Caso | Cómo |
|------|------|
| Una animación | Un `ctx` + un `buffer` → `st7920_animation_run(...)` |
| Varias | Array `st7920_animation_slot_t` → `st7920_animation_run_all(...)` |

### Ejemplo: una animación

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_delay/avr_delay.h"

static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];
static st7920_animation_ctx_t plot_ctx;

int main(void)
{
    /* init SPI, st7920, delay_init() … */
    for (;;)
        st7920_animation_run(&plot_ctx, 48, 16, &plot_anim, plot_buffer, 100);
}
```

### Ejemplo: varias en paralelo

```c
static const st7920_animation_slot_t animation_slots[] = {
    { &plot_ctx,        2, 16, &plot_anim,        plot_buffer,        100 },
    { &temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100 },
};
#define ANIMATION_SLOT_COUNT  (sizeof(animation_slots) / sizeof(animation_slots[0]))

for (;;)
    st7920_animation_run_all(animation_slots, (uint8_t)ANIMATION_SLOT_COUNT);
```

Añadir una animación = añadir un slot. Cada una tiene su `ctx` y su buffer; todas comparten `delay_ms()`.

### Animaciones + otra tarea

```c
uint16_t t_sec = delay_sec();

for (;;) {
    st7920_animation_run_all(animation_slots, (uint8_t)ANIMATION_SLOT_COUNT);

    if ((uint16_t)(delay_sec() - t_sec) >= 2) {
        /* redibujar estáticos, etc. */
        t_sec = delay_sec();
    }
}
```

Para reiniciar una animación: `ctx->active = 0`; la siguiente `run` vuelve a hacer start.

---

## 5. Resumen

| Pieza | Rol |
|-------|-----|
| Convención MSB-izquierda | Bitmaps estáticos e iconos animados |
| Offset + valor | Diff: qué byte cambiar y a qué |
| `avr_delay` | Intervalos sin congelar HotPanel |
| `st7920_animation_ctx_t` | Estado por animación |
| `st7920_animation_slot_t` | Configuración para `run_all` |
| `st7920_animation_run` / `run_all` | Start/tick no bloqueante |

Antes de re-enlazar animaciones al producto: skill **hotplate-feature-budget** (`make size` + [feature_budget.md](feature_budget.md)). La UI aprobada (iconos 16×16) no se sacrifica por AT opcional.
