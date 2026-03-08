# AVR Delay – Temporización por timer (no bloqueante)

Sistema de delays basado en **interrupciones del Timer0**, similar a `millis()` de Arduino. Expone tres contadores (ms, sec, min) para poder usar el tipo más pequeño según el intervalo a medir.

## API

| Función        | Retorno   | Uso recomendado                          |
|----------------|-----------|------------------------------------------|
| `delay_init()` | void      | Llamar una vez al arranque.              |
| `delay_ms()`   | uint16_t  | Intervalos en milisegundos (wrap ~65 s).|
| `delay_sec()`  | uint16_t  | Intervalos en segundos.                  |
| `delay_min()`  | uint8_t   | Intervalos en minutos (wrap 256 min).   |

## Ejemplos (basados en main con ST7920 y animación)

Inicialización (una vez al arranque):

```c
#include "lib/avr_delay/avr_delay.h"
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"

int main(void)
{
    avr_spi_master_init(SPI_DIV_4);
    st7920_init();
    st7920_graphics_mode();
    delay_init();   /* después de init del sistema */

    /* ... dibujos, st7920_render(), etc. */
}
```

Cada 100 ms (p. ej. paso de animación o parpadeo):

```c
uint16_t t_ms = delay_ms();
for (;;) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* hacer algo cada 100 ms */
        t_ms = delay_ms();
    }
}
```

Cada 2 segundos (p. ej. actualizar texto en pantalla):

```c
uint16_t t_sec = delay_sec();
for (;;) {
    if ((uint16_t)(delay_sec() - t_sec) >= 2) {
        st7920_clear_commands();
        st7920_draw_text(0, 57, "Hello");
        st7920_render();
        t_sec = delay_sec();
    }
}
```

Cada 1 minuto (p. ej. lectura de sensor o log):

```c
uint8_t t_min = delay_min();
for (;;) {
    if ((uint8_t)(delay_min() - t_min) >= 1) {
        /* cada minuto */
        t_min = delay_min();
    }
}
```

Varios intervalos en el mismo loop (ms + segundos):

```c
uint16_t t_ms = delay_ms();
uint16_t t_sec = delay_sec();
for (;;) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* cada 100 ms */
        t_ms = delay_ms();
    }
    if ((uint16_t)(delay_sec() - t_sec) >= 5) {
        /* cada 5 segundos */
        t_sec = delay_sec();
    }
}
```

El cast a `(uint16_t)` o `(uint8_t)` en la resta hace que el wrap del contador siga dando el intervalo correcto.

## Patrón: configuración → primera ejecución (init) → ciclo temporizado

Para flujos con una o varias tareas temporizadas (animaciones, máquinas de estado, etc.):

1. **Configuración:** definir estructuras con intervalo, último tick y punteros a contexto/callback (o array de “slots”).
2. **Primera ejecución:** al arranque o primera vez que se entra en el flujo, hacer init (guardar `last_tick = delay_ms()`, activar, acción inicial). No repetir en el loop.
3. **Ciclo:** en el loop solo llamar una función de tick (o `tick_all`); comprobar `(reloj - last_tick) >= intervalo` y, si toca, ejecutar acción y actualizar `last_tick`.

Guía detallada: [doc/delays_no_bloqueantes.md](../../doc/delays_no_bloqueantes.md). Casos de uso y máquinas de estado: [doc/plan_maquina_estado_tick.md](../../doc/plan_maquina_estado_tick.md).

## Hardware

- **Timer0** en modo CTC (Compare Match), prescaler 64.
- Interrupción cada ~1 ms (F_CPU 4 MHz: 62 cuentas × 16 µs ≈ 992 µs).
- No usa pines externos.

## Dependencias

- `F_CPU` definido (p. ej. en Makefile o en el .c que incluye el header).
- Ninguna otra librería.
