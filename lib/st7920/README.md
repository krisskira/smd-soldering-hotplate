# ST7920 – Display LCD 128x64

Control del display gráfico ST7920 128x64 mediante **SPI hardware** y dibujo diferido (lista de comandos + `st7920_render()`). Sin framebuffer completo para ahorrar RAM.

## Hardware (según código)

| Señal LCD | Pin ATmega16 | Notas        |
|-----------|--------------|--------------|
| CS        | PB3          | Chip Select  |
| MOSI/SCK  | PB5, PB7     | SPI hardware |
| RST       | No conectado | No usado     |

Referencia: `config/board_pins.h`, `lib/st7920/st7920_config.c`.

## Uso básico

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"

int main(void) {
    avr_spi_master_init();
    st7920_init();
    st7920_graphics_mode();

    st7920_draw_rect(10, 10, 100, 30);
    st7920_draw_line(0, 0, 127, 0);
    st7920_draw_text(5, 20, "Hola");
    st7920_draw_progressbar(10, 45, 100, 10, 65);
    st7920_render();  /* obligatorio: envía todos los comandos al LCD */

    for (;;) {}
}
```

## API

### Configuración
- `st7920_init()` – Inicializa el display.
- `st7920_clear()` – Limpia RAM de texto (modo texto).
- `st7920_graphics_mode()` – Modo gráfico y borrado de GDRAM.

### Dibujo (acumulan comandos; se envían con `st7920_render()`)
- `st7920_draw_pixel(x, y)`
- `st7920_draw_line(x0, y0, x1, y1)`
- `st7920_draw_rect(x, y, w, h)`
- `st7920_draw_progressbar(x, y, w, h, percent)`
- `st7920_draw_text(x, y, str)` – Añade texto a la lista de comandos (se envía con `st7920_render()`).
- **`st7920_draw_text_gdram(x, y, str)`** – Escribe texto **directo en GDRAM** (sin lista de comandos). Usar en el loop cuando combines texto variable y animaciones; así no hace falta llamar a `st7920_render()` de nuevo. Sobrescribe las 7 filas de píxel que ocupa el texto (fuente 5x7).
- `st7920_draw_bitmap(x, y, w, h, data)` – Carga y dibuja un mapa de bits (véase más abajo).

### Pantalla
- `st7920_render()` – Interpreta la lista de comandos y envía todo al LCD. Borra la pantalla al inicio.

### Animaciones (frame 0 + diffs)
- `st7920_write_frame_pgm(base_x, base_y, data_pgm, width, height, bytes_per_row)` – Escribe un frame completo en GDRAM desde PROGMEM. No borra la pantalla.
- `st7920_apply_diff_pgm(base_x, base_y, buffer, bytes_per_row, offsets_pgm, values_pgm, count)` – Actualiza el buffer con los bytes indicados y escribe solo los bloques modificados en GDRAM. Datos en PROGMEM.
- **`st7920_clear_region(x, y, w, h)`** – Borra una región rectangular en GDRAM (escribe 0). Coordenadas en píxeles; útil para “quitar” una animación o limpiar una zona.
- **`st7920_draw_region_pgm(x, y, bitmap_pgm, w, h)`** – Escribe un bitmap en la región (x,y) de tamaño w×h en GDRAM. Formato del bitmap: `(w+7)/8` bytes por fila, `(h+1)/2` filas (2 px por fila, igual que los frames de animación). Útil para reemplazar una animación por un icono estático.
- `st7920_draw_animation(x, y, anim, buffer, delay_ms)` – Ejecuta una animación en bucle: escribe el frame 0, luego aplica los diffs de los frames 1..N-1 con un retardo de `delay_ms` ms entre frames. **Bloqueante** (usa `_delay_ms`). Para varias animaciones o lógica concurrente, ver *Estrategia de animaciones no bloqueantes* más abajo.

## Animaciones con descriptor

Las animaciones se describen con la estructura `st7920_animation_t`:

- **frame_0_pgm** – Puntero al frame completo en PROGMEM.
- **diff_offsets_pgm** – Puntero al array en PROGMEM de punteros (cada uno apunta a los offsets del diff de ese frame). Índice 0 = frame 1.
- **diff_values_pgm** – Puntero al array en PROGMEM de punteros a los valores del diff.
- **diff_counts_pgm** – Puntero al array en PROGMEM de `uint16_t` (número de bytes por diff).
- **width, height, bytes_per_row, bytes_per_frame, frame_count** – Dimensiones y número de frames.

El llamador debe proporcionar un buffer en RAM de al menos `bytes_per_frame` bytes. Ejemplo de uso (bloqueante):

```c
static const st7920_animation_t plot_anim = {
    .frame_0_pgm       = plot_frame_0,
    .diff_offsets_pgm   = plot_diff_offsets,
    .diff_values_pgm    = plot_diff_values,
    .diff_counts_pgm    = plot_diff_counts,
    .width              = PLOT_FRAME_WIDTH,
    .height             = PLOT_FRAME_HEIGHT,
    .bytes_per_row      = PLOT_BYTES_PER_ROW,
    .bytes_per_frame    = PLOT_BYTES_PER_FRAME,
    .frame_count       = PLOT_FRAME_COUNT,
};
static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];

st7920_render();
st7920_draw_animation(0, 0, &plot_anim, plot_buffer, 100);  /* no retorna; bloquea */
```

## Carga de mapas de bit

`st7920_draw_bitmap(x, y, w, h, data)` añade un bitmap a la lista de comandos. En `st7920_render()` se dibuja en la posición `(x, y)` con tamaño `w`×`h` píxeles.

- **Formato de `data`:** por filas, 1 bit por píxel. Cada fila tiene `(w + 7) / 8` bytes. Bit más significativo = píxel izquierdo. Orden: fila 0, fila 1, …
- **Origen:** puntero a RAM. Para datos en flash (PROGMEM) hace falta copiarlos a un buffer en RAM antes de dibujar, o se puede añadir más adelante una variante `st7920_draw_bitmap_pgm`.

Ejemplo (icono 8×8 en RAM):

```c
const uint8_t icono[] = {
    0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
};
st7920_draw_bitmap(10, 20, 8, 8, icono);
st7920_render();
```


## Memoria

- Lista de comandos: 24 entradas × 7 bytes.
- Buffer de una fila: 16 B.

## Estructura del código

- `st7920_config.c` – Init, comandos, GDRAM bajo nivel.
- `st7920_draw.c` – Lista de comandos, render por filas, bitmap.
- `st7920_font.c` – Fuente 5x7 en PROGMEM y texto para el render.

## Coordenadas

- (0,0) = esquina superior izquierda.
- x: 0–127, y: 0–63.

## Animaciones no bloqueantes

`st7920_draw_animation()` es bloqueante. Para **una o varias** animaciones sin bloquear se sigue el principio **configuración → primera ejecución (init) → ciclo temporizado** (ver [doc/plan_maquina_estado_tick.md](../../doc/plan_maquina_estado_tick.md)):

- **Una animación:** `st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)` – Una función con máquina de estados: la primera llamada hace start (frame 0 + init ctx); las siguientes hacen tick. Llamar siempre en el loop con los mismos parámetros.
- **Varias animaciones:** definir un array de **slots** (`st7920_animation_slot_t`), cada uno con punteros a ctx, anim, buffer y (x, y, interval_ms). En el loop solo **`st7920_animation_run_all(slots, count)`**. Añadir una animación = añadir un slot al array; no hace falta reescribir el loop.

Documentación completa (una vs varias animaciones, ejemplos, delays): [doc/animaciones_no_bloqueantes.md](../../doc/animaciones_no_bloqueantes.md).

## Texto + animaciones (sin volver a llamar render)

`st7920_render()` **borra toda la GDRAM** y luego dibuja la lista de comandos. Si en el loop llamas otra vez a `render()` para actualizar texto, se pierden las animaciones (que se dibujan directo en GDRAM).

**Uso recomendado cuando hay texto variable y animaciones:**

1. **Al inicio:** `st7920_clear_commands()`, añadir rectángulos, bitmap estático, etc., luego **`st7920_render()`** una sola vez.
2. **En el loop:** animaciones con `st7920_animation_run_all(...)` y **`st7920_draw_text_gdram(x, y, str)`** para el texto que cambia (p. ej. año, temperatura). No llames a `st7920_render()` en el loop.

Así el texto se escribe directo en GDRAM y las animaciones siguen visibles. La zona del texto (7 filas de píxel con fuente 5x7) se sobrescribe por completo en cada llamada; no pongas ahí otras cosas que quieras conservar.
