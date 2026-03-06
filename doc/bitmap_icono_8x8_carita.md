# Bitmap 8×8: icono de carita (smiley)

Este documento explica **por qué** y **cómo** se construye el array del icono de la carita usado en `main.c`, qué convención de bits y bytes se usa, y qué hace cada byte y cada bit para que se dibuje la cara.

## Dónde se usa

En `src/main.c` se define un bitmap de 8×8 píxeles y se dibuja con la librería ST7920:

```c
const uint8_t icono[] = {
    0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
};
st7920_draw_bitmap(10, 20, 8, 8, icono);
```

La función `st7920_draw_bitmap(x, y, w, h, data)` espera los datos en este formato:

- **Orden:** por **filas** (fila 0, fila 1, …, fila 7).
- **Ancho:** 8 píxeles → 1 byte por fila (8 bits = 8 píxeles).
- **Bit más significativo (MSB)** del byte = píxel **izquierdo**; **LSB** = píxel **derecho**.
- **1** = píxel encendido (negro/dibujado), **0** = apagado (fondo).

Por tanto:

- El array tiene **8 bytes** → **8 filas**.
- Cada byte es una fila horizontal de 8 píxeles: bit 7 = columna 0, bit 0 = columna 7.

## Qué se tiene en cuenta para “llegar” a este array

1. **Tamaño:** 8×8 para un icono pequeño y legible.
2. **Formato:** 1 bit por píxel, una fila por byte, MSB = izquierda (igual que la librería).
3. **Diseño:** se eligen qué píxeles encender para formar:
   - Contorno circular de la cabeza (arriba, abajo y lados).
   - Dos ojos (dos puntos separados).
   - Una sonrisa (curva en la parte inferior).

A partir de eso se escribe cada fila en binario y se convierte a hexadecimal para cada byte.

## Significado de cada byte y cada bit

Se considera:

- **Fila 0** = parte superior del dibujo (y más pequeño).
- **Columna 0** = izquierda (bit 7 del byte).
- **Columna 7** = derecha (bit 0 del byte).
- **1** = píxel dibujado, **0** = fondo.

A continuación, fila por fila (de arriba a abajo), con el byte en hex, en binario y la interpretación de cada bit.

---

### Fila 0 — `0x3C` — Parte superior de la cabeza

| Binario | `0  0  1  1  1  1  0  0` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ·  ·  ■  ■  ■  ■  ·  ·   |

- **0x3C** = 0011 1100 en binario.
- Bits 2, 3, 4, 5 en 1 → se dibuja una franja horizontal en el centro: **borde superior** de la cabeza (arco superior del círculo).

---

### Fila 1 — `0x42` — Lados superiores

| Binario | `0  1  0  0  0  0  1  0` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ·  ■  ·  ·  ·  ·  ■  ·   |

- **0x42** = 0100 0010.
- Bits 1 y 6 en 1 → dos píxeles a los **lados**, continuando el contorno circular (izquierda y derecha de la cabeza).

---

### Fila 2 — `0xA5` — Ojos (línea superior de los ojos)

| Binario | `1  0  1  0  0  1  0  1` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ■  ·  ■  ·  ·  ■  ·  ■   |

- **0xA5** = 1010 0101.
- Bits 0, 2, 5, 7 en 1 → **contorno** de la cara a izquierda y derecha (0 y 7) y **dos puntos** hacia dentro (2 y 5): **ojos**. En 8×8 a veces se usa una sola fila por ojo; aquí esa fila ya sugiere los dos ojos.

---

### Fila 3 — `0x81` — Contorno de la cara

| Binario | `1  0  0  0  0  0  0  1` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ■  ·  ·  ·  ·  ·  ·  ■   |

- **0x81** = 1000 0001.
- Solo bits 0 y 7 en 1 → **bordes izquierdo y derecho** de la cara (sin rellenar el centro), lo que mantiene el contorno circular.

---

### Fila 4 — `0xA5` — Ojos (misma forma que fila 2)

| Binario | `1  0  1  0  0  1  0  1` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ■  ·  ■  ·  ·  ■  ·  ■   |

- Mismo valor que la fila 2: **0xA5**.
- Vuelve a marcar **contorno** (0, 7) y **ojos** (2, 5). En conjunto con la fila 2 se forman los dos “cuadrados” de 1×2 píxeles que se leen como ojos.

---

### Fila 5 — `0x99` — Sonrisa

| Binario | `1  0  0  1  1  0  0  1` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ■  ·  ·  ■  ■  ·  ·  ■   |

- **0x99** = 1001 1001.
- Bits 0, 3, 4, 7 en 1 → contorno en los lados (0, 7) y **dos píxeles en el centro** (3, 4): forman la **curva de la boca** (sonrisa) en la parte baja del rostro.

---

### Fila 6 — `0x42` — Lados inferiores

| Binario | `0  1  0  0  0  0  1  0` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ·  ■  ·  ·  ·  ·  ■  ·   |

- **0x42** = 0100 0010 (igual que fila 1).
- Bits 1 y 6 en 1 → **lados** del círculo en la parte inferior, cerrando el contorno de la cabeza.

---

### Fila 7 — `0x3C` — Parte inferior de la cabeza

| Binario | `0  0  1  1  1  1  0  0` |
|--------|---------------------------|
| Bit    | 7  6  5  4  3  2  1  0   |
| Columna| 0  1  2  3  4  5  6  7   |
| Píxel  | ·  ·  ■  ■  ■  ■  ·  ·   |

- **0x3C** = 0011 1100 (igual que fila 0).
- Bits 2, 3, 4, 5 en 1 → **arco inferior** del círculo; cierra la cabeza por abajo.

---

## Vista global del bitmap (1 = ■, 0 = ·)

```
       col: 0 1 2 3 4 5 6 7
            L     R
fila 0:     · · ■ ■ ■ ■ · ·   0x3C  (arco superior)
fila 1:     · ■ · · · · ■ ·   0x42  (lados)
fila 2:     ■ · ■ · · ■ · ■   0xA5  (ojos + contorno)
fila 3:     ■ · · · · · · ■   0x81  (contorno)
fila 4:     ■ · ■ · · ■ · ■   0xA5  (ojos + contorno)
fila 5:     ■ · · ■ ■ · · ■   0x99  (sonrisa)
fila 6:     · ■ · · · · ■ ·   0x42  (lados)
fila 7:     · · ■ ■ ■ ■ · ·   0x3C  (arco inferior)
```

## Resumen

| Byte  | Hex  | Rol en el dibujo                          |
|-------|------|-------------------------------------------|
| [0]   | 0x3C | Arco superior de la cabeza                |
| [1]   | 0x42 | Lados del círculo (arriba)                |
| [2]   | 0xA5 | Ojos (y contorno izquierdo/derecho)      |
| [3]   | 0x81 | Solo contorno izquierdo/derecho           |
| [4]   | 0xA5 | Ojos (y contorno)                          |
| [5]   | 0x99 | Sonrisa (curva central) + contorno        |
| [6]   | 0x42 | Lados del círculo (abajo)                  |
| [7]   | 0x3C | Arco inferior de la cabeza                |

El array se “llega” eligiendo este formato (1 byte por fila, MSB = izquierda), el tamaño 8×8 y qué bits poner en 1 para contorno, ojos y boca. Cada byte controla una fila; cada bit de ese byte controla un píxel de izquierda (bit 7) a derecha (bit 0), y así se dibuja la carita.
