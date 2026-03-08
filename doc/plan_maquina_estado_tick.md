# Plan: Temporizador genérico con callback y máquina de estados

Objetivo: definir un **mecanismo reutilizable** de temporización (no solo para animaciones) que permita registrar “cada XX tiempo ejecutar esta función”, y usarlo como base para **máquinas de estado** y otros procesos (animaciones, parpadeos, lecturas periódicas, fases de UI, etc.). Solo plan; sin implementar.

---

## 0. Principio: configuración → primera ejecución (init) → ciclo temporizado

Patrón reutilizable para flujos temporizados y máquinas de estado:

1. **Definir la configuración del flujo**  
   Estructuras de datos que describen *qué* se ejecuta y *cada cuánto*: parámetros de temporizado, punteros a contexto/buffer/callback, lista de “slots” o tabla de estados. Todo por **punteros** cuando sea posible, para no redefinir código al añadir más tareas.

2. **Llamadas de configuración / init en la primera ejecución**  
   La primera vez que se entra en el flujo (o al arranque), se hace la **inicialización**: escribir estado inicial, guardar `last_tick = reloj_actual`, activar el proceso. No se repite en el loop.

3. **Ejecutar en ciclos temporizados**  
   En el loop solo se llama una función de **tick** (o `run_all` sobre un array de configuraciones). Esa función compara `reloj_actual - last_tick` con el intervalo; si toca, ejecuta la acción (callback o paso de animación) y actualiza `last_tick`. El loop no hace “init” cada vez; solo avanza el tiempo y dispara acciones.

**Casos de uso donde aplicar este principio:**

| Caso | Configuración | Primera ejecución | Ciclo temporizado |
|------|----------------|--------------------|--------------------|
| **Una animación** | `ctx` + parámetros (x, y, anim, buffer, interval_ms) | Primera llamada a `run(ctx, ...)`: escribe frame 0, rellena ctx, `active = 1`. | Mismas llamadas `run(ctx, ...)`: si `active`, hace tick (siguiente frame). |
| **Varias animaciones** | Array de **slots** (cada slot: ctx, x, y, anim, buffer, interval_ms). | Primera llamada a `run_all(slots, n)`: cada ctx inactivo recibe su “start”. | Loop solo llama `run_all(slots, n)`; cada slot hace start una vez y luego tick. |
| **Temporizador genérico** | Estructura: interval, last_tick, active, callback, user_data. | `timer_init(t, interval, callback, user_data)`: last_tick = reloj, active = 1. | Loop: `timer_tick(t)`; si (ahora - last_tick) >= interval → callback, last_tick = ahora. |
| **Máquina de estados** | Enum de estados, tabla o switch por estado (intervalo, acción, transición). | Init: estado = inicial, last_tick = reloj, (opcional) timer_init con intervalo del estado. | Loop: timer_tick o “tick máquina”; callback hace acción del estado y/o transición; si transición, reprogramar intervalo. |

Así se evita mezclar “configuración” con “ejecución” en el loop: la configuración se define una vez (una o N tareas); la primera ejecución hace el init; el ciclo solo hace comprobación de tiempo y ejecución.

---

## 1. Modelo de tiempo: reloj principal y comparación hasta “desborde”

- **Variable principal de tiempo:** un único reloj que avanza en una interrupción (Timer0), ya disponible como `delay_ms()`, `delay_sec()`, `delay_min()`. Es la referencia de “ahora”.
- **Por cada proceso o tarea temporizada:** una variable que guarda el **último instante** en que se disparó (o se inicializó). En el ciclo principal (o en un método de “tick” común) se compara constantemente:
  - `ahora = delay_ms()` (o `delay_sec()` / `delay_min()` según la unidad);
  - si `(ahora - ultimo_tick) >= intervalo` → se produce el “desborde”: toca ejecutar la acción, y entonces se **reinicia** `ultimo_tick = ahora` (o se incrementa otro contador si se quiere una cadena de fases).
- El control de “qué hacer cuando toca” y “reiniciar o pasar a la siguiente fase” se lleva **dentro de los métodos principales** (callbacks o lógica de estado), de forma que el mismo mecanismo sirva para animaciones, LEDs, lecturas, cambios de estado, etc.

Así, la reutilización viene de: **un solo reloj global** + **por tarea/proceso: último_tick + intervalo + “qué hacer cuando toca”** (callback).

---

## 2. API deseada: parámetros de temporizado + callback

Se quiere un **método (o abstracción)** al que se le pase:

1. **Parámetros de temporizado:** intervalo y unidad (cada N ms, cada N seg, cada N min), o un único intervalo en ms si se simplifica.
2. **Función callback:** la que se invoca cada vez que pasa ese intervalo (o al desborde).

La idea es no repetir en cada módulo la lógica “guardar último tick, comparar, si toca llamar a X y actualizar”. Ese código queda en un solo sitio; el usuario solo registra “cada XX tiempo, llamar a esta función”.

Propuesta de uso (a nivel de API):

- **Inicializar** un temporizador: intervalo (y unidad si se soporta) + puntero a callback. Opcional: un `void *user_data` para pasar contexto al callback (ej. puntero al contexto de animación, o al estado actual de la máquina).
- **En el ciclo principal:** una única función tipo **`timer_tick(temporizador)`** (o `timer_tick_all()` si hay varios) que:
  - Lee el reloj (`delay_ms()` o el que corresponda).
  - Comprueba si `(ahora - ultimo_tick) >= intervalo`.
  - Si sí: llama al **callback** y actualiza `ultimo_tick = ahora` (reinicio). Si no, no hace nada.

Con eso, cualquier proceso que necesite “hacer algo cada N tiempo” solo tiene que implementar el callback y registrar el temporizador con el intervalo deseado.

---

## 3. Estructura de datos del temporizador genérico (plan)

Cada “temporizador” podría ser una estructura que agrupe:

| Campo        | Rol |
|-------------|-----|
| `interval_ms` (o `interval_sec` / unidad) | Cada cuánto se dispara. |
| `last_tick`  | Valor del reloj en el último disparo (o en la init). Comparado con el reloj actual para saber si ya pasó el intervalo. |
| `active`     | Si está activo (1) o pausado (0). Permite “parar” sin borrar el registro. |
| `callback`   | Función a llamar cuando `(ahora - last_tick) >= interval`. Firmas posibles: `void (*cb)(void)` o `void (*cb)(void *user_data)`. |
| `user_data`  | Opcional: puntero que se pasa al callback (contexto de animación, número de estado, etc.). |

La **unidad** de tiempo puede fijarse por convención (siempre ms) o guardarse en la estructura (enum: MS, SEC, MIN) y en el tick usar `delay_ms()`, `delay_sec()` o `delay_min()` según corresponda. El “desborde” es siempre: “ya pasó el intervalo” → llamar callback y hacer `last_tick = ahora`.

Si se quiere **varios contadores en cascada** (ej. “cada 100 ms incrementar X; cuando X llega a 10, pasar al siguiente estado”), eso ya no lo lleva el temporizador genérico sino la **lógica dentro del callback**: el callback puede incrementar un contador y, al llegar a N, cambiar de estado o registrar otro temporizador. El temporizador base solo resuelve “cada XX tiempo, llamar a esta función”.

---

## 4. Reutilización en distintos procesos

El mismo mecanismo sirve para:

- **Animación:** temporizador con intervalo 100 ms y callback que llama a “aplicar siguiente frame” (o que llama a `st7920_animation_tick(ctx)` si se mantiene el contexto de animación por compatibilidad).
- **Parpadeo LED:** intervalo 500 ms, callback que hace toggle del pin.
- **Lectura de sensor:** intervalo 2000 ms, callback que lee MAX31865 y actualiza variable o pantalla.
- **Timeout de tecla:** intervalo 300 ms, callback que considera “tecla soltada” o “fin de pulsación larga”.
- **Máquina de estados:** un temporizador por “fase con tiempo” (ej. “estado mostrando animación 10 s”); callback = “al cumplirse 10 s, pasar a estado siguiente y ejecutar entrada al nuevo estado”. O un único temporizador y en el callback un `switch(state)` que decide transición.

Así se evita duplicar la lógica de “comparar tiempo y reiniciar” en cada módulo; solo se implementa el callback específico.

---

## 5. Máquina de estados y temporizador

La máquina de estados puede apoyarse en el temporizador genérico de dos maneras (combinables):

**A) Callback = transición de estado**  
- Un temporizador con intervalo “duración del estado actual”.  
- Al dispararse el callback: se ejecuta la salida del estado actual (si hace falta), se cambia el estado (variable o enum), se ejecuta la entrada del nuevo estado y se **reprograma** el temporizador con el intervalo del nuevo estado (o se desactiva si el nuevo estado no tiene tiempo).  
- El “control de todo esto” queda en los métodos principales: init de la máquina (estado inicial + registro del temporizador con su intervalo) y callback (transición + posible reprogramación).

**B) Callback = acción periódica dentro del estado**  
- Mientras se está en “mostrando animación”, el callback se llama cada 100 ms y ejecuta “siguiente frame”.  
- Cuando se quiera “solo 10 s de animación”, puede haber un **segundo** temporizador (o un contador en el callback) que a los 10 s dispare “salir de este estado y pasar a otro”.  
- O un único temporizador con intervalo 100 ms y en el callback: incrementar un contador; si contador >= 100 (10 s), transición de estado; si no, siguiente frame.

En ambos casos, la **variable principal** sigue siendo el reloj (`delay_ms`/`delay_sec`/`delay_min`); la **variable por proceso** es `last_tick` (y opcionalmente contadores o estado). Los **métodos principales** (init, callback, y la función que llama a `timer_tick` en el loop) llevan el control de cuándo reiniciar, cuándo cambiar de estado y qué hacer en cada disparo.

---

## 6. Plan de implementación sugerido

1. **Definir el tipo “temporizador genérico”**  
   - Estructura con: intervalo, último tick, active, callback, [user_data], [unidad ms/sec/min].  
   - Función **init**: recibe temporizador, intervalo, callback, [user_data]; pone `last_tick = delay_xx()`, `active = 1`.  
   - Función **tick**: recibe temporizador; si no activo return; si `(delay_xx() - last_tick) >= interval`, llamar callback y `last_tick = delay_xx()`.

2. **Reloj**  
   - Seguir usando `delay_ms()` / `delay_sec()` / `delay_min()` como única fuente de tiempo. El temporizador genérico solo lee uno de ellos según su unidad.

3. **Integrar con código existente**  
   - Las animaciones ya siguen el principio anterior: **una función** `st7920_animation_run(ctx, x, y, anim, buffer, interval_ms)` con máquina de estados interna (primera vez: start; luego: tick). Para **varias animaciones**, array de `st7920_animation_slot_t` y `st7920_animation_run_all(slots, count)` en el loop. Un temporizador genérico podría llamar en su callback a `st7920_animation_run(...)` si se quiere un único punto de entrada en el loop.

4. **Máquina de estados**  
   - Definir enum de estados y, por estado, intervalo opcional y callback (acción periódica o “al timeout”). En el init se pone estado inicial y se arranca el temporizador con el intervalo del primer estado. En el callback del temporizador: o bien se hace la acción del estado (ej. siguiente frame), o bien se comprueba timeout y se cambia de estado y se actualiza el intervalo del temporizador al del nuevo estado.

5. **Documentar**  
   - En la doc de delays y de animaciones: “temporizador genérico con callback” como capa reutilizable por encima del reloj, y “máquina de estados” como uso típico (transiciones por tiempo + callbacks).

Con esto el planteamiento queda **genérico** (aplicable a animaciones y a otros procesos), con **un método al que se le pasan parámetros de temporizado y la función callback** que se llama cada XX tiempo, y con el **control del desborde y del reinicio** centralizado en el tick del temporizador, mientras los métodos principales (callbacks e init) llevan la lógica de negocio y de estados.
