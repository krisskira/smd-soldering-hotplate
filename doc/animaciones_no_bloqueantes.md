# Estrategia: animaciones no bloqueantes con temporizador

## Problema

`st7920_draw_animation(x, y, &anim, buffer, delay_ms)` ejecuta un bucle infinito con `_delay_ms(delay_ms)` entre frames. No retorna, por lo que:

- No se pueden ejecutar **varias animaciones** a la vez (p. ej. dos iconos animados en distintas zonas).
- No se puede mezclar animación con **otras tareas** (lectura de sensores, teclas, otra lógica en el main loop).

## Objetivo

Sustituir el “delay bloqueante” por una **temporización basada en un timer** (interrupción periódica) y una API que permita:

1. **Iniciar** una animación (escribir frame 0, preparar estado).
2. **Avanzar** la animación cuando haya pasado el intervalo, sin bloquear (polling desde el main loop o desde un único manejador de tick).

Así el main loop puede llamar en cada iteración a “paso” de varias animaciones y a otras tareas; el “cuándo toca el siguiente frame” lo decide el temporizador.

## Enfoque propuesto

### 1. Contador de ticks (timer)

- Usar **un timer del AVR** (p. ej. Timer0 o Timer1) con interrupción por overflow o compare.
- Configurar el prescaler para que la ISR se ejecute cada **1 ms** (o una base fija: 1 ms es cómoda para intervalos en ms).
- En la ISR, incrementar un **contador global** de milisegundos (por ejemplo `volatile uint32_t systick_ms` o `volatile uint16_t systick_ms` si 65 s de margen bastan).

Requisitos: una sola ISR que solo incremente el contador (y opcionalmente llame a otras tareas ligeras). No hacer dibujo ni SPI dentro de la ISR.

### 2. Estado por animación (contexto)

Cada instancia de animación que quiera correr “en paralelo” necesita su propio **contexto** en RAM, por ejemplo:

```c
typedef struct {
    const st7920_animation_t *anim;  /* descriptor, no copiado */
    uint8_t *buffer;                   /* buffer de al menos bytes_per_frame */
    uint8_t x, y;
    uint16_t frame_idx;                /* siguiente frame a aplicar (1..frame_count-1) */
    uint32_t last_tick_ms;              /* valor de systick_ms cuando se aplicó el último frame */
    uint16_t interval_ms;              /* intervalo entre frames (ej. 100) */
    uint8_t active;                    /* 1 = animación en curso, 0 = parada/inactiva */
} st7920_animation_ctx_t;
```

- **anim**, **buffer**, **x**, **y**, **interval_ms**: fijados al **iniciar** la animación.
- **frame_idx**, **last_tick_ms**: se actualizan cada vez que se aplica un diff.
- **active**: permite “parar” o “no dibujar” sin borrar el contexto.

### 3. API en dos partes

**Inicio (una vez por animación):**

- `void st7920_animation_start(st7920_animation_ctx_t *ctx, uint8_t x, uint8_t y, const st7920_animation_t *anim, uint8_t *buffer, uint16_t interval_ms)`  
  - Valida `anim`, `buffer`, `frame_count >= 1`.  
  - Escribe el frame 0 en GDRAM (`st7920_write_frame_pgm`).  
  - Copia frame 0 al buffer desde PROGMEM.  
  - Inicializa `ctx`: anim, buffer, x, y, frame_idx = 1, last_tick_ms = systick_ms, interval_ms, active = 1.

**Paso (llamada desde el main loop o desde un único “tick handler”):**

- `void st7920_animation_tick(st7920_animation_ctx_t *ctx)` (o `st7920_animation_poll`)  
  - Si `!ctx || !ctx->active` return.  
  - Si `(systick_ms - ctx->last_tick_ms) < ctx->interval_ms` return (aún no toca).  
  - Aplicar el diff del frame actual: leer desde PROGMEM offsets/values/count del frame `ctx->frame_idx`, llamar `st7920_apply_diff_pgm(ctx->x, ctx->y, ctx->buffer, ...)`.  
  - Avanzar: `ctx->frame_idx++`; si `ctx->frame_idx >= ctx->anim->frame_count`, poner `ctx->frame_idx = 1`.  
  - Actualizar `ctx->last_tick_ms = systick_ms`.

No se usa `_delay_ms`; la decisión “¿avanzar ya?” se basa solo en el contador de ticks.

### 4. Uso típico en main

```c
/* Una vez: iniciar timer que actualice systick_ms cada 1 ms (ISR). */

st7920_animation_ctx_t plot_ctx;
st7920_animation_ctx_t other_ctx;

/* Tras st7920_render() o cuando se quiera mostrar la animación: */
st7920_animation_start(&plot_ctx, PLOT_BASE_X, PLOT_BASE_Y, &plot_anim, plot_buffer, 100);
st7920_animation_start(&other_ctx, 80, 20, &other_anim, other_buffer, 150);

for (;;) {
    st7920_animation_tick(&plot_ctx);
    st7920_animation_tick(&other_ctx);
    /* Otras tareas: teclas, sensores, etc. */
}
```

### 5. Detalles a tener en cuenta

- **Desbordamiento de `systick_ms`**: si se usa `uint32_t`, el cálculo `(systick_ms - ctx->last_tick_ms) >= interval_ms` sigue siendo correcto al dar la vuelta. Con `uint16_t` (máx. 65 535 ms) hay que decidir si es suficiente o usar `uint32_t`.
- **Frames con count 0**: `st7920_apply_diff_pgm` con `count == 0` no escribe; no hace falta tratarlo aparte.
- **Misma animación en dos sitios**: dos contextos con el mismo `anim` pero distinto `buffer`, `x`, `y` (y opcionalmente `interval_ms`). Cada uno mantiene su propio `frame_idx` y `last_tick_ms`.
- **Compatibilidad**: mantener `st7920_draw_animation()` existente para código que prefiera el comportamiento bloqueante; la nueva API es opt-in.

## Resumen

| Concepto | Rol |
|----------|-----|
| Timer ISR | Incrementa `systick_ms` cada 1 ms (u otra base). |
| `st7920_animation_ctx_t` | Estado por animación (descriptor, buffer, posición, frame actual, último tick, intervalo, activo). |
| `st7920_animation_start` | Escribe frame 0, rellena buffer, inicializa contexto. |
| `st7920_animation_tick` | Si ha pasado el intervalo, aplica diff del frame actual y avanza; no bloquea. |
| Main loop | Llama a `st7920_animation_tick` para cada contexto y al resto de la lógica. |

Con esto se pueden tener varias animaciones y otras tareas en paralelo sin bloquear en delays.
