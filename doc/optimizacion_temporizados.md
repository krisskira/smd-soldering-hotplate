# Guía oficial: temporización no bloqueante (estilo Arduino millis)

Esta guía es la referencia para temporizar tareas sin bloquear el programa, equivalente a `millis()` de Arduino. Usa el módulo `avr_delay` (Timer0 por interrupción) y el patrón **guardar instante + comparar**.

---

## 1. Por qué no usar `_delay_ms()`

`_delay_ms(100)` detiene todo el programa. Mientras tanto no se puede:
- Actualizar animaciones en pantalla
- Leer sensores (MAX31865) o teclas
- Ejecutar otras tareas

Para UI con varias tareas concurrentes hace falta **no bloquear**: el main loop sigue girando y decide "¿ya pasó el intervalo?" consultando un reloj que avanza en interrupción.

---

## 2. El reloj: `avr_delay`

El módulo `lib/avr_delay` usa **Timer0** con interrupción cada ~1 ms y expone tres contadores:

| Función        | Retorno   | Wrap      | Uso típico              |
|----------------|-----------|-----------|--------------------------|
| `delay_init()` | void      | —         | Una vez al arranque      |
| `delay_ms()`   | uint16_t  | ~65 s     | Intervalos en ms         |
| `delay_sec()`  | uint16_t  | ~18 h     | Intervalos en segundos   |
| `delay_min()`  | uint8_t   | 256 min   | Intervalos en minutos    |

Elegir el tipo según el intervalo para ahorrar RAM. Ver [lib/avr_delay/README.md](../lib/avr_delay/README.md).

---

## 3. Patrón básico (equivalente a millis)

1. **Inicializar** el reloj una vez: `delay_init()`
2. **Guardar** el instante al iniciar el intervalo: `t = delay_ms()`
3. **En el loop**: si `(delay_ms() - t) >= intervalo`, ejecutar la acción y hacer `t = delay_ms()`

Con tipos unsigned, el wrap del contador hace que la resta siga siendo correcta.

---

## 4. Ejemplo real: lectura de sensor cada 1 segundo

Fragmento de [src/main.c](../src/main.c) que lee el MAX31865 cada segundo sin bloquear:

```c
#include "lib/avr_delay/avr_delay.h"
#include "lib/max31865/max31865.h"

int main(void)
{
    /* ... init de hardware ... */
    delay_init();

    static float temperature = 0.0f;
    static const uint16_t temperature_sampling_time_ms = 1000u;
    static uint16_t temperature_time = 0;

    temperature_time = delay_ms();   /* Guardar instante inicial */

    while (1) {
        uint16_t now = delay_ms();   /* Leer reloj actual */

        if ((uint16_t)(now - temperature_time) >= temperature_sampling_time_ms) {
            /* Ha pasado 1 s: leer sensor */
            ptc_on();
            max31865_prepare_for_read();
            uint16_t rtd = max31865_read_rtd();
            temperature = max31865_temperature(rtd);
            ptc_off();
            temperature_time = now;  /* Reiniciar intervalo */
        }

        /* Otras tareas: animaciones, texto, etc. */
        st7920_animation_run_all(animation_slots1, ANIMATION_SLOT_COUNT1);
        st7920_animation_run_all(animation_slots2, ANIMATION_SLOT_COUNT2);
        st7920_draw_text_gdram(35, 57, texto);
    }
}
```

**Clave:** el cast `(uint16_t)(now - temperature_time)` hace que el wrap del contador siga dando el intervalo correcto.

---

## 5. Varios intervalos en el mismo loop

```c
uint16_t t_ms  = delay_ms();
uint16_t t_sec = delay_sec();

while (1) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* Cada 100 ms: animación */
        t_ms = delay_ms();
    }
    if ((uint16_t)(delay_sec() - t_sec) >= 2) {
        /* Cada 2 s: actualizar texto */
        t_sec = delay_sec();
    }
}
```

---

## 6. Consumir gráficos y datos en procesos asíncronos

### Animaciones (gráficos)

Las animaciones usan el mismo reloj internamente. Cada animación tiene un `last_tick_ms` y un `interval_ms`. En el loop solo se llama `st7920_animation_run_all(slots, count)`; cada slot comprueba si ha pasado su intervalo y avanza el frame.

```c
static const st7920_animation_slot_t animation_slots[] = {
    { &plot_ctx,        2, 16, &plot_anim,        plot_buffer,        100 },
    { &temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100 },
};

while (1) {
    st7920_animation_run_all(animation_slots, ANIMATION_SLOT_COUNT);
}
```

Cada slot tiene su propio intervalo (100 ms en el ejemplo). Ver [doc/animaciones_no_bloqueantes.md](animaciones_no_bloqueantes.md).

### Datos (lectura de sensor)

La lectura del sensor se temporiza con el patrón de la sección 4: variable `temperature_time`, comparar `(now - temperature_time) >= 1000`, ejecutar lectura y actualizar `temperature_time`.

### Combinar animaciones + datos

```c
while (1) {
    uint16_t now = delay_ms();

    /* Tarea 1: cada 1 s, leer sensor */
    if ((uint16_t)(now - temperature_time) >= 1000) {
        temperature = max31865_temperature(max31865_read_rtd());
        temperature_time = now;
    }

    /* Tarea 2: animaciones (cada 100 ms internamente) */
    st7920_animation_run_all(animation_slots, count);

    /* Tarea 3: texto en pantalla (usa temperature actualizado) */
    st7920_draw_text_gdram(35, 57, texto);
}
```

El main loop no bloquea; cada tarea se ejecuta cuando toca su intervalo.

---

## 7. Prueba rápida

```c
#include "lib/avr_delay/avr_delay.h"

int main(void)
{
    /* init hardware */
    delay_init();

    uint16_t t = delay_ms();

    for (;;) {
        if ((uint16_t)(delay_ms() - t) >= 500) {
            /* Cada 500 ms */ 
            t = delay_ms();
        }
    }
}
```

---

## 8. Documentación relacionada

- [lib/avr_delay/README.md](../lib/avr_delay/README.md) – API del módulo de delay
- [doc/delays_no_bloqueantes.md](delays_no_bloqueantes.md) – Cómo crear delays reutilizables
- [doc/animaciones_no_bloqueantes.md](animaciones_no_bloqueantes.md) – Animaciones y slots
- [doc/atmega16_pin_definition_hotplate.md](atmega16_pin_definition_hotplate.md) – Pines y SPI
