# Temporización no bloqueante — HotPlate

Cómo hace HotPlate varias cosas a la vez (sensor, HotPanel, control, USB) **sin congelarse**.  
Equivalente práctico a `millis()` de Arduino: un reloj por interrupción + el patrón **guardar instante y comparar**.

| También ver | Para |
|-------------|------|
| [lib/avr_delay/README.md](../lib/avr_delay/README.md) | API del módulo |
| [st7920_pantalla.md](st7920_pantalla.md) | Bitmaps, diffs y animaciones LCD |
| [architecture.md](architecture.md) | Super-loop del firmware |

---

## 1. Por qué no usar `_delay_ms()`

`_delay_ms(100)` detiene **todo** el programa durante 100 ms. Mientras tanto no se puede:

- refrescar HotPanel
- leer el sensor (MAX31865)
- atender USB o el encoder
- avanzar el lazo PI / el Soldering Profile

HotPlate necesita que el `main` **siga girando** y solo pregunte: “¿ya pasó el intervalo?”.

---

## 2. El reloj: `avr_delay`

El módulo `lib/avr_delay` usa **Timer0** con interrupción cada ~1 ms y ofrece tres contadores (elige el más pequeño que te baste → menos RAM):

| Función | Retorno | Wrap aproximado | Uso típico |
|---------|---------|-----------------|------------|
| `delay_init()` | — | — | Una vez al arranque |
| `delay_ms()` | `uint16_t` | ~65 s | Intervalos en milisegundos |
| `delay_sec()` | `uint16_t` | ~18 h | Intervalos en segundos |
| `delay_min()` | `uint8_t` | 256 min | Intervalos en minutos |

---

## 3. El patrón (siempre el mismo)

1. **Init:** `delay_init()` una vez.
2. **Al empezar el intervalo:** guarda el reloj → `t = delay_ms()` (o `_sec` / `_min`).
3. **En cada vuelta del loop:** si `(reloj_actual - t) >= intervalo`, haz la tarea y actualiza `t`.

Con tipos **unsigned**, el wrap del contador sigue dando bien la resta (si el intervalo cabe en el tipo). El cast `(uint16_t)(now - t)` es importante.

```c
#include "lib/avr_delay/avr_delay.h"

delay_init();
uint16_t t_ms = delay_ms();

for (;;) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* Han pasado 100 ms */
        t_ms = delay_ms();
    }
    /* Aquí caben más tareas sin bloquear */
}
```

### Varios intervalos en el mismo loop

```c
uint16_t t_ms  = delay_ms();
uint16_t t_sec = delay_sec();

for (;;) {
    if ((uint16_t)(delay_ms() - t_ms) >= 100) {
        /* cada 100 ms */
        t_ms = delay_ms();
    }
    if ((uint16_t)(delay_sec() - t_sec) >= 2) {
        /* cada 2 s */
        t_sec = delay_sec();
    }
}
```

---

## 4. Crear un delay reutilizable

Para cualquier tarea “cada N ms” (o s / min):

1. Declara `uint16_t last_ms` (o el tipo que toque).
2. En el init de la tarea: `last_ms = delay_ms();`
3. En el tick (función que llama el loop):

```c
if ((uint16_t)(delay_ms() - last_ms) >= INTERVALO_MS) {
    /* hacer la tarea */
    last_ms = delay_ms();
}
```

Así trabaja por dentro `st7920_animation_tick`: el contexto guarda `last_tick_ms` e `interval_ms` y solo avanza frame cuando toca.

### Principio: configuración → init → ciclo

| Paso | Qué hacer |
|------|-----------|
| **Configuración** | Estructuras con intervalo, último tick, punteros a contexto/callback. Varias tareas → array de “slots”. |
| **Primera ejecución (init)** | Guardar `last_tick`, marcar activo, acción inicial si hace falta. **No** repetir esto en el loop. |
| **Ciclo (tick)** | Solo comprobar `(reloj - last_tick) >= intervalo`; si toca, ejecutar y actualizar `last_tick`. |

Añadir una tarea = añadir un slot (y el `count` de `tick_all` si aplica). El `main` se mantiene simple.

---

## 5. Ejemplo: sensor cada 1 s + otras tareas

Patrón usado en el firmware (lectura MAX31865 sin congelar HotPanel):

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

    temperature_time = delay_ms();

    while (1) {
        uint16_t now = delay_ms();

        if ((uint16_t)(now - temperature_time) >= temperature_sampling_time_ms) {
            ptc_on();
            max31865_prepare_for_read();
            uint16_t rtd = max31865_read_rtd();
            temperature = max31865_temperature(rtd);
            ptc_off();
            temperature_time = now;
        }

        /* Otras tareas: animaciones, texto, AT, PI… */
        st7920_animation_run_all(animation_slots, ANIMATION_SLOT_COUNT);
    }
}
```

### Animaciones (mismo reloj)

Cada slot tiene su `interval_ms`. El loop solo llama `st7920_animation_run_all(...)`; dentro, cada animación decide si avanza.

```c
static const st7920_animation_slot_t animation_slots[] = {
    { &plot_ctx,        2, 16, &plot_anim,        plot_buffer,        100 },
    { &temperature_ctx, 48, 16, &temperature_anim, temperature_buffer, 100 },
};

while (1) {
    st7920_animation_run_all(animation_slots, ANIMATION_SLOT_COUNT);
}
```

Detalle: [st7920_pantalla.md](st7920_pantalla.md).

### Combinar sensor + animaciones + UI

```c
while (1) {
    uint16_t now = delay_ms();

    if ((uint16_t)(now - temperature_time) >= 1000) {
        temperature = max31865_temperature(max31865_read_rtd());
        temperature_time = now;
    }

    st7920_animation_run_all(animation_slots, count);
    st7920_draw_text_gdram(35, 57, texto);
}
```

Nadie espera a nadie: cada quien corre cuando le toca su intervalo.

---

## 6. Prueba mínima

```c
#include "lib/avr_delay/avr_delay.h"

int main(void)
{
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

## 7. Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | `delay_init()` una vez al arranque |
| 2 | Guardar el reloj al iniciar el intervalo |
| 3 | En el loop: si pasó el intervalo → acción + actualizar guardado |
| 4 | Usar `ms` / `sec` / `min` según el tamaño del intervalo |
| 5 | **Nunca** `_delay_ms()` en caminos calientes (UI, sensor, AT, PI) |

Así se construyen todos los delays no bloqueantes de HotPlate.
