# Animaciones en el display ST7920 (no bloqueantes)

Documentación sobre las animaciones en el LCD, el sistema de delays por timer y cómo combinar ambos para tener **una o varias animaciones** (o animación + otras tareas) **sin bloquear** la UI. Se sigue el principio **configuración → primera ejecución (init) → ciclo temporizado**.

**Documentación relacionada:**
- [doc/optimizacion_temporizados.md](optimizacion_temporizados.md) – Guía oficial de temporización (estilo millis)
- [doc/atmega16_pin_definition_hotplate.md](atmega16_pin_definition_hotplate.md) – Pines, SPI hardware (LCD)

---

## 1. Descriptor de animación y API de bajo nivel

Las animaciones se describen con **frame 0 completo** (en PROGMEM) más **diffs** por frame (solo los bytes que cambian). La estructura es `st7920_animation_t`:

- **frame_0_pgm** – Puntero al frame completo en PROGMEM.
- **diff_offsets_pgm** – Array en PROGMEM de punteros a los offsets de cada diff (índice 0 = frame 1).
- **diff_values_pgm** – Array en PROGMEM de punteros a los valores de cada diff.
- **diff_counts_pgm** – Array en PROGMEM con el número de bytes por diff.
- **width, height, bytes_per_row, bytes_per_frame, frame_count** – Dimensiones.

El llamador proporciona un **buffer en RAM** de al menos `bytes_per_frame` bytes.

### API de bajo nivel (frame y diff)

- `st7920_write_frame_pgm(x, y, data_pgm, width, height, bytes_per_row)` – Escribe un frame completo en GDRAM desde PROGMEM.
- `st7920_apply_diff_pgm(x, y, buffer, bytes_per_row, offsets_pgm, values_pgm, count)` – Actualiza buffer y escribe solo los bloques modificados en GDRAM.

### Animación bloqueante (una sola, no recomendada para UI con varias tareas)

- `st7920_draw_animation(x, y, anim, buffer, delay_ms)` – Escribe frame 0 y entra en un bucle infinito aplicando diffs con `_delay_ms(delay_ms)`. **No retorna**; no permite otras animaciones ni otras tareas. Útil solo para demos o pantallas con una única animación.

---

## 2. Delays no bloqueantes: `avr_delay`

Para no bloquear hace falta un **reloj** que avance en una interrupción. El módulo `lib/avr_delay` usa el **Timer0** y expone tres contadores (ms, sec, min) para poder usar tipos pequeños y ahorrar RAM.

### API

| Función        | Retorno   | Uso                          |
|----------------|-----------|------------------------------|
| `delay_init()` | void      | Una vez al arranque.         |
| `delay_ms()`   | uint16_t  | Contador de ms (wrap ~65 s). |
| `delay_sec()`  | uint16_t  | Contador de segundos.        |
| `delay_min()`  | uint8_t   | Contador de minutos.        |

### Patrón de uso

Guardar el valor del reloj al iniciar el intervalo; en el loop, si `(delay_xx() - guardado) >= intervalo`, ejecutar la acción y actualizar el guardado. Ver [doc/optimizacion_temporizados.md](optimizacion_temporizados.md).

```c
delay_init();
uint16_t t_ms = delay_ms();
for (;;) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* cada 100 ms */
        t_ms = delay_ms();
    }
}
```

---

## 3. Animación no bloqueante: una función + máquina de estados (run)

Cada animación tiene un **contexto** en RAM (`st7920_animation_ctx_t`) que guarda descriptor, buffer, posición, frame actual, último tick, intervalo y estado (`active`). Se usa **una sola función** que hace **start la primera vez** (ctx inactivo) y **tick en adelante** (ctx activo), siguiendo el principio: **configuración → primera ejecución = init → ciclo = solo temporizado**.

### API

- **`st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)`** – Una función con máquina de estados interna:
  - Si `ctx->active == 0` y se pasan `anim` y `buffer` no NULL: hace **start** (escribe frame 0 en GDRAM, rellena buffer, inicializa ctx, `active = 1`).
  - Si `ctx->active == 1`: hace **tick** (si ha pasado `interval_ms`, aplica el siguiente diff, avanza frame, actualiza `last_tick_ms`).
- No hace falta llamar a “start” por separado: la primera llamada a `run()` en el loop hace el start; las siguientes hacen tick.

El “cuándo toca el siguiente frame” lo decide el reloj (`delay_ms()`), no un `_delay_ms()`.

### Una sola animación

Defines un **contexto** y un **buffer**; en el loop llamas siempre a `st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)` con los mismos parámetros. La primera vez se inicializa; luego solo tick.

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"
#include "lib/avr_delay/avr_delay.h"

static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];
static st7920_animation_ctx_t plot_ctx;

int main(void)
{
    avr_spi_master_init(SPI_DIV_4);
    st7920_init();
    st7920_graphics_mode();
    delay_init();

    st7920_clear_commands();
    st7920_draw_rect(0, 0, 12, 12);
    st7920_draw_text(0, 57, "Hello");
    st7920_render();

    for (;;)
        st7920_animation_run(&plot_ctx, 48, 16, &plot_anim, plot_buffer, 100);
}
```

### Varias animaciones: slots + run_all

Para **varias animaciones** se define un **array de slots** (`st7920_animation_slot_t`): cada slot tiene punteros a `ctx`, `anim`, `buffer` y los parámetros `x`, `y`, `interval_ms`. En el loop solo se llama **`st7920_animation_run_all(slots, count)`**. Así no se reescribe el loop al añadir o quitar animaciones: solo se añade o quita una entrada en el array.

| Qué | Cómo |
|-----|------|
| **Una animación** | Un `ctx` + un `buffer`; en el loop: `st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)`. |
| **Varias animaciones** | Array `st7920_animation_slot_t slots[]` con un slot por animación (ctx, x, y, anim, buffer, interval_ms). En el loop: `st7920_animation_run_all(slots, count)`. |

### Ejemplo: dos o más animaciones en paralelo

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"
#include "lib/avr_delay/avr_delay.h"
#include "icons/animated/plot.c"
#include "icons/animated/temperature.c"

static const st7920_animation_t plot_anim = { ... };
static const st7920_animation_t temperature_anim = { ... };

int main(void)
{
    avr_spi_master_init(SPI_DIV_4);
    st7920_init();
    st7920_graphics_mode();
    delay_init();

    static uint8_t plot_buffer[PLOT_BYTES_PER_FRAME];
    static uint8_t temperature_buffer[TEMPERATURE_BYTES_PER_FRAME];
    static st7920_animation_ctx_t plot_ctx;
    static st7920_animation_ctx_t temperature_ctx;

    /* Configuración del flujo: array de slots (punteros). */
    static const st7920_animation_slot_t animation_slots[] = {
        { &plot_ctx,        2, 16, &plot_anim,        plot_buffer,        100 },
        { &temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100 },
    };
    #define ANIMATION_SLOT_COUNT  (sizeof(animation_slots) / sizeof(animation_slots[0]))

    st7920_clear_commands();
    st7920_draw_rect(0, 0, 12, 12);
    st7920_draw_bitmap(2, 2, 8, 8, icono);
    st7920_draw_rect(46, 14, 34, 34);
    st7920_draw_text(0, 57, "Hello");
    st7920_render();

    /* Ciclo: solo run_all; la primera vez cada slot hace start, luego tick. */
    for (;;)
        st7920_animation_run_all(animation_slots, (uint8_t)ANIMATION_SLOT_COUNT);
}
```

Cada animación tiene su propio **contexto** y **buffer**; el mismo reloj (`delay_ms()`) sirve para todas. Añadir una animación = añadir un elemento a `animation_slots` y usar `ANIMATION_SLOT_COUNT` (o actualizar el count).

### Ejemplo: animaciones + otra tarea cada 2 segundos

```c
uint16_t t_sec = delay_sec();

for (;;)
{
    st7920_animation_run_all(animation_slots, (uint8_t)ANIMATION_SLOT_COUNT);

    if ((uint16_t)(delay_sec() - t_sec) >= 2)
    {
        st7920_clear_commands();
        st7920_draw_rect(0, 0, 12, 12);
        st7920_draw_bitmap(2, 2, 8, 8, icono);
        st7920_draw_rect(46, 14, 34, 34);
        st7920_draw_text(0, 57, "Hello");
        st7920_render();
        /* Reiniciar animaciones: poner ctx->active = 0 en cada ctx, o usar run_all
           que en la siguiente iteración hará start de nuevo si active quedó en 0. */
        t_sec = delay_sec();
    }
}
```

Cada 2 segundos se redibuja el contenido estático; si se reinician las animaciones (poniendo `active = 0` en cada contexto), en la siguiente vuelta `run_all` hará start de nuevo. El resto del tiempo solo se ejecuta `run_all` y la comprobación de los 2 s.

---

## 5. Resumen

| Concepto | Rol |
|----------|-----|
| **avr_delay** | Timer (Timer0) que actualiza `delay_ms()` / `delay_sec()` / `delay_min()`. Base para todos los intervalos no bloqueantes. |
| **st7920_animation_ctx_t** | Estado por animación (descriptor, buffer, x, y, frame_idx, last_tick_ms, interval_ms, active). |
| **st7920_animation_slot_t** | Configuración de una animación por punteros (ctx, x, y, anim, buffer, interval_ms); para array y run_all. |
| **st7920_animation_run** | Una función + máquina de estados: primera llamada con ctx inactivo = start; siguientes = tick. |
| **st7920_animation_run_all** | Ejecuta run() para cada slot; evita reescribir el loop al tener varias animaciones. |
| **Main loop** | Llama a `st7920_animation_run(...)` (una animación) o `st7920_animation_run_all(slots, n)` (varias) y a otras tareas; el “delay” lo da el reloj. |

Con esto se pueden tener una o varias animaciones y otras tareas en paralelo sin bloquear, siguiendo el principio configuración → primera ejecución = init → ciclo temporizado.

---

## 6. Documentación relacionada

- [doc/optimizacion_temporizados.md](optimizacion_temporizados.md) – Guía oficial de temporización (estilo millis), ejemplo main.c, consumir gráficos y datos.
- [doc/delays_no_bloqueantes.md](delays_no_bloqueantes.md) – Patrón de delays reutilizables.
- [lib/avr_delay/README.md](../lib/avr_delay/README.md) – API del módulo de delay.
- [lib/st7920/README.md](../lib/st7920/README.md) – API del display ST7920.
