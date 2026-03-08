# Plan: Quitar animación y gestionar la zona (borrar o reemplazar)

## Objetivo

Tras dejar de mostrar una animación en una zona (por tiempo, por evento o por cambio de estado), poder:
- **Borrar** esa zona en pantalla (GDRAM a 0 en ese rectángulo), o
- **Reemplazar** esa zona por otro bitmap (mismo tamaño/región, contenido distinto).

El “cuándo” quitar la animación lo decide el flujo principal (timer, máquina de estados, etc.); este plan se centra en **cómo** borrar o reemplazar la región en el ST7920.

---

## Alcance: solo helpers de pantalla

- No se define aquí la lógica de “duración en el contexto de animación” ni cuándo llamar a estos helpers; eso queda en el plan de máquina de estados / temporizador.
- Sí se define: **requerimientos y estrategias** para una API de “borrar región” y “escribir bitmap en región” (reemplazo), reutilizable para animaciones y para cualquier contenido en GDRAM.

---

## Requerimientos

### R1 – Borrar una región en GDRAM

- **Entrada:** posición y tamaño de la región (p. ej. `x`, `y`, `ancho`, `alto` en píxeles, o en bloques de 8×8 según el modelo del ST7920).
- **Comportamiento:** escribir 0 en todos los bytes de GDRAM que cubren ese rectángulo, de forma que en pantalla esa zona quede negra (o “vacía”).
- **Restricciones:** coordenadas alineadas al modelo de direccionamiento del ST7920 (p. ej. `y` en unidades de 8 líneas si el hardware direcciona por filas de 8 px). No depender de la lista de comandos de dibujo; operar directamente sobre GDRAM.

### R2 – Reemplazar una región por un bitmap

- **Entrada:** posición (`x`, `y`), dimensiones de la región (o del bitmap), y el bitmap (puntero a PROGMEM o RAM).
- **Comportamiento:** escribir en GDRAM los bytes del bitmap en el rectángulo indicado, reemplazando lo que hubiera (animación, texto, etc.).
- **Restricciones:** mismo alineamiento que R1; formato del bitmap coherente con el usado en el proyecto (ej. 1 bpp, por filas de 8 px). Reutilizar si existe algo como `st7920_write_frame_pgm` pero garantizando que cubre “esta región” de forma explícita.

### R3 – Reutilización

- Ambas operaciones deben servir para:
  - “Quitar” una animación (borrar o poner un bitmap estático).
  - Cualquier otra pantalla que necesite limpiar o rellenar un rectángulo en GDRAM (iconos, zonas de texto redibujado, etc.).

---

## Estrategias

### E1 – Helper “borrar región”

- **Nombre propuesto:** `st7920_clear_region(x, y, w, h)` (o equivalentes en bloques, p. ej. `x, y` en caracteres/bloques, `w, h` en ancho/alto de bloque).
- **Implementación:**
  - Calcular qué bytes (direcciones) de GDRAM cubren el rectángulo `(x,y,w,h)` según el mapeo del ST7920 (mitad izquierda/derecha, filas de 8 px). Ver doc de mapeo si existe (p. ej. `mapeo_offset_bits_pantalla.md`).
  - Recorrer solo esos bytes/bloques y escribir 0 (o llamar a la primitiva de escritura en GDRAM que ya use la librería).
- **Alternativa:** si ya existe un “frame vacío” en PROGMEM del tamaño típico de la animación, se podría tener `st7920_write_region_pgm(x, y, empty_frame, w, h)` y usarlo con ese frame para “borrar”; entonces el helper genérico sería “escribir región desde bitmap” y “borrar” sería un caso particular (bitmap de ceros). La estrategia recomendada es **implementar primero “borrar región”** explícito (más simple y sin depender de tamaños predefinidos), y opcionalmente un “escribir región desde bitmap” que también permita borrar pasando un buffer de 0.

### E2 – Helper “reemplazar por bitmap en región”

- **Nombre propuesto:** `st7920_draw_region_pgm(x, y, bitmap, w, h)` (o similar: `st7920_write_region_*` si se alinea con la nomenclatura existente).
- **Implementación:**
  - Misma lógica de mapeo que E1: a partir de `(x,y,w,h)` obtener los bytes/bloques de GDRAM afectados.
  - Escribir en esos bloques los datos del `bitmap` (leyendo de PROGMEM por filas/columnas según el formato usado en el proyecto). Si la librería ya tiene “escribir un frame en (x,y)”, generalizarlo a “escribir este bitmap de w×h en (x,y)”.
- **Relación con animación:** al “quitar” la animación, el main puede llamar primero a “clear region” o directamente a “draw region” con el bitmap que debe verse después (icono estático, logo, etc.), sin necesidad de redibujar toda la pantalla.

### E3 – Unidad de coordenadas

- Decidir y documentar si la API usa:
  - **Píxeles** (x, y, w, h en px) y la función traduce internamente a bloques/bytes del ST7920, o
  - **Bloques** (p. ej. x en columnas de 8 px, y en filas de 8 px) para que quien llama conozca el modelo del LCD.
- **Recomendación:** usar píxeles y hacer la traducción dentro de la librería, para que el resto del firmware no dependa del direccionamiento interno; si el ST7920 impone alineación (p. ej. múltiplos de 8 en `y`), documentarlo y redondear/truncar internamente.

### E4 – Orden de implementación

1. **Fase 1:** Implementar `st7920_clear_region(...)` según R1 y E1/E3. Probar borrando la zona de una animación desde el main.
2. **Fase 2:** Implementar `st7920_draw_region_*` (o el nombre elegido) según R2 y E2. Probar reemplazando la zona de la animación por un bitmap estático.
3. Opcional: si se dispone de “frame vacío” fijo, usarlo vía `draw_region` para borrar en lugar de `clear_region`; en cualquier caso, mantener `clear_region` como API estable para “solo borrar” sin pasar bitmap.

---

## Resumen de cambios propuestos (implementado)

| Qué | Descripción | Estado |
|-----|-------------|--------|
| **`st7920_clear_region(x, y, w, h)`** | Escribe 0 en los bytes de GDRAM que cubren el rectángulo. Coordenadas en píxeles; se traduce a bloques (16 px × 2 px). | Hecho en `st7920_draw.c` |
| **`st7920_draw_region_pgm(x, y, bitmap_pgm, w, h)`** | Escribe el bitmap en la región (x,y) de tamaño w×h. Formato: `(w+7)/8` bytes por fila, `(h+1)/2` filas (2 px por fila, igual que frames de animación). | Hecho en `st7920_draw.c` |
| **Unidad de coordenadas** | API en píxeles; traducción interna a bloques GDRAM (E3). | Documentado en `st7920.h` |
| **Uso al “quitar” animación** | El main (o callback) marca la animación inactiva (`ctx->active = 0`) y llama a `st7920_clear_region(x, y, width, height)` o a `st7920_draw_region_pgm(x, y, bitmap, w, h)` para esa zona. | A criterio del flujo (timer/estado). |

### Ejemplo de uso al quitar una animación

```c
/* Tras decidir quitar la animación (p. ej. por tiempo): */
plot_ctx.active = 0;
st7920_clear_region(2, 16, PLOT_FRAME_WIDTH, PLOT_FRAME_HEIGHT);  /* borrar zona */

/* O reemplazar por un icono estático en PROGMEM (mismo formato 2 px/fila): */
/* st7920_draw_region_pgm(2, 16, icono_estatico_pgm, 32, 32); */
```

Con esto el plan queda **implementado** y la API es reutilizable para animaciones y para el resto de la UI.
