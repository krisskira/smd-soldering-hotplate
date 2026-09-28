# Cómo crear y usar delays no bloqueantes

**Guía oficial:** [doc/optimizacion_temporizados.md](optimizacion_temporizados.md) – Ejemplo real de main.c (lectura sensor cada 1 s), consumir gráficos y datos en procesos asíncronos.

Esta guía explica cómo temporizar acciones **sin bloquear** el programa, usando el módulo `avr_delay` (timer por interrupción) y el patrón “guardar instante inicial + comparar con el contador”.

## Por qué no usar `_delay_ms()`

`_delay_ms(100)` detiene todo el programa 100 ms. Mientras tanto no se puede:
- Actualizar otra animación.
- Leer teclas o sensores.
- Hacer ninguna otra tarea.

Para una UI con varias animaciones o tareas concurrentes hace falta **no bloquear**: el main loop debe seguir girando y decidir “¿ya pasaron 100 ms?” consultando un **reloj** que avanza en una interrupción.

## El reloj: `avr_delay`

El módulo `lib/avr_delay` usa el **Timer0** con una interrupción cada ~1 ms y mantiene tres contadores:

| Función        | Retorno   | Uso típico                    |
|----------------|-----------|--------------------------------|
| `delay_init()` | void      | Llamar **una vez** al arranque. |
| `delay_ms()`   | uint16_t  | Intervalos en ms (wrap ~65 s). |
| `delay_sec()`  | uint16_t  | Intervalos en segundos.       |
| `delay_min()`  | uint8_t   | Intervalos en minutos.       |

Tres funciones permiten elegir el tipo más pequeño según el intervalo (ms/sec/min) y ahorrar RAM. Ver [lib/avr_delay/README.md](../lib/avr_delay/README.md).

## Patrón: “¿Ha pasado el intervalo?”

1. **Al empezar** la tarea o al **reiniciar** el intervalo: guardar el valor actual del reloj.
2. **En cada iteración** del main loop: leer el reloj y restar el valor guardado; si la diferencia es mayor o igual al intervalo, “ha pasado el tiempo” → ejecutar la acción y **actualizar** el valor guardado al reloj actual.

En C, con tipos unsigned, el wrap del contador hace que la resta siga siendo correcta (si el intervalo cabe en el rango del tipo).

### Ejemplo: hacer algo cada 100 ms

```c
#include "lib/avr_delay/avr_delay.h"

int main(void)
{
    /* ... init de hardware, delay_init(); ... */
    delay_init();

    uint16_t t_ms = delay_ms();

    for (;;)
    {
        if ((uint16_t)(delay_ms() - t_ms) >= 100)
        {
            /* Han pasado 100 ms: hacer la tarea */
            t_ms = delay_ms();
        }
        /* Aquí se puede hacer más cosas sin bloquear */
    }
}
```

### Ejemplo: cada 2 segundos

```c
uint16_t t_sec = delay_sec();

for (;;)
{
    if ((uint16_t)(delay_sec() - t_sec) >= 2)
    {
        /* Cada 2 segundos */
        t_sec = delay_sec();
    }
}
```

### Ejemplo: varios intervalos en el mismo loop

```c
uint16_t t_ms  = delay_ms();
uint16_t t_sec = delay_sec();

for (;;)
{
    if ((uint16_t)(delay_ms() - t_ms) >= 100)
    {
        /* cada 100 ms */
        t_ms = delay_ms();
    }
    if ((uint16_t)(delay_sec() - t_sec) >= 5)
    {
        /* cada 5 segundos */
        t_sec = delay_sec();
    }
}
```

## Crear un “delay” reutilizable en tu código

Si quieres una tarea que “se ejecute cada N ms” sin bloquear:

1. **Declara** una variable para guardar el último tick (p. ej. `uint16_t last_ms`).
2. **En el init** de la tarea (o la primera vez que la activas): `last_ms = delay_ms();`
3. **En el tick** (función que llamas en el main loop):  
   `if ((uint16_t)(delay_ms() - last_ms) >= INTERVALO_MS) { ... hacer la tarea ...; last_ms = delay_ms(); }`

Eso es exactamente lo que hace por dentro `st7920_animation_tick`: el contexto guarda `last_tick_ms` y `interval_ms`, y solo aplica el siguiente frame cuando `(delay_ms() - last_tick_ms) >= interval_ms`.

## Principio: configuración → primera ejecución (init) → ciclo temporizado

Para reutilizar el mismo patrón en **flujos temporizados** (una o varias tareas, máquinas de estado):

1. **Definir la configuración del flujo**  
   Estructuras con intervalo, último tick, punteros a contexto/callback. Si hay varias tareas, un array de “slots” o configuraciones (todo por punteros para no redefinir al añadir tareas).

2. **Primera ejecución = init**  
   Al arranque o la primera vez que se entra en el flujo: guardar `last_tick = delay_ms()` (o sec/min), marcar activo, y opcionalmente ejecutar la acción inicial. No repetir esta lógica en el loop.

3. **Ciclo = solo temporizado**  
   En el loop se llama una función de **tick** (o `tick_all` sobre el array). Esa función solo comprueba `(reloj_actual - last_tick) >= intervalo`; si toca, ejecuta la acción y actualiza `last_tick`. El loop no hace init cada vez.

Así el main loop queda simple y escalable: añadir una tarea es añadir una entrada a la configuración (p. ej. un slot más) y, si aplica, incrementar el count en `tick_all`. Ver [doc/optimizacion_temporizados.md](optimizacion_temporizados.md) para ejemplos completos.

## Resumen

| Paso | Acción |
|-----|--------|
| 1 | Llamar `delay_init()` una vez al arranque. |
| 2 | Guardar el valor del reloj al iniciar el intervalo (`t = delay_ms()` o `delay_sec()` / `delay_min()`). |
| 3 | En el loop, si `(reloj_actual - t) >= intervalo`, ejecutar la acción y hacer `t = reloj_actual`. |
| 4 | Usar el tipo que corresponda (uint16_t para ms/sec, uint8_t para min) para que el wrap siga siendo correcto. |

Así se crean delays no bloqueantes para cualquier tarea que deba repetirse cada N ms, segundos o minutos.
