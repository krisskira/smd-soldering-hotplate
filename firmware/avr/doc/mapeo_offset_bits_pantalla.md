# Mapeo de offset a bit exacto en la pantalla (modo diff)

Este documento explica cómo interpretar los **offsets** y los **valores** generados en modo diff para saber **qué byte** reemplazar, **cómo está formado** ese byte (qué bit es qué píxel) y **qué posición exacta en pantalla** corresponde a cada bit.

---

## 1. Qué es el offset

El **offset** es el **índice lineal** del byte en el buffer de la imagen, en orden **fila-major**:

- Los bytes se almacenan **fila por fila**, de arriba abajo.
- Dentro de cada fila, los bytes van de **izquierda a derecha**.
- Cada byte representa **8 píxeles horizontales** (8 bits = 1 byte).

Por tanto:

| Rango de offset | Significado |
|-----------------|-------------|
| `0 .. (BYTES_PER_ROW - 1)` | Primera fila (fila 0) |
| `BYTES_PER_ROW .. (2×BYTES_PER_ROW - 1)` | Segunda fila (fila 1) |
| `2×BYTES_PER_ROW .. (3×BYTES_PER_ROW - 1)` | Tercera fila (fila 2) |
| … | … |

Con:

```text
BYTES_PER_ROW = (ANCHO_IMAGEN + 7) / 8
```

Ejemplo: imagen 50×50 → `BYTES_PER_ROW = 7`.  
Offset 0..6 = fila 0, offset 7..13 = fila 1, etc.

---

## 2. De offset a posición del byte (fila y columna de byte)

A partir del **offset** se obtiene en qué **fila** y en qué **columna de byte** está ese byte:

```c
uint16_t offset = plot_diff_N_offsets[i];   // índice lineal del byte

uint8_t row      = offset / BYTES_PER_ROW;  // fila (0 = arriba)
uint8_t col_byte = offset % BYTES_PER_ROW;  // índice del byte dentro de la fila (0 = izquierda)
```

- **`row`**: fila de la imagen (0 = primera fila desde arriba).
- **`col_byte`**: “número de byte” en esa fila; el byte 0 cubre los píxeles 0–7, el byte 1 los píxeles 8–15, etc.

Así ya sabes **qué byte** del buffer (y de la pantalla) debes actualizar: el que está en la fila `row` y en la columna de byte `col_byte`.

---

## 3. Cómo está formado el valor del array (un byte = 8 píxeles)

El **valor** en `plot_diff_N_values[i]` es un **byte de 8 bits**. Cada bit controla **un píxel** de ese grupo de 8 horizontales:

| Bit del byte | Posición del píxel dentro del byte | Significado |
|--------------|-------------------------------------|-------------|
| **Bit 7** (MSB) | Primer píxel (más a la **izquierda**) | 1 = encendido, 0 = apagado |
| **Bit 6** | Segundo píxel | 1 = encendido, 0 = apagado |
| **Bit 5** | Tercer píxel | … |
| **Bit 4** | Cuarto píxel | … |
| **Bit 3** | Quinto píxel | … |
| **Bit 2** | Sexto píxel | … |
| **Bit 1** | Séptimo píxel | … |
| **Bit 0** (LSB) | Octavo píxel (más a la **derecha**) | 1 = encendido, 0 = apagado |

Resumen:

- **MSB (bit 7)** = píxel **izquierdo** del grupo de 8.
- **LSB (bit 0)** = píxel **derecho** del grupo de 8.
- **1** = píxel encendido (negro), **0** = píxel apagado (fondo).

Ejemplo: el byte `0xA5` = `1010 0101` en binario:

```text
Bit:    7  6  5  4  3  2  1  0
Bin:    1  0  1  0  0  1  0  1
Píxel:  ■  ·  ■  ·  ·  ■  ·  ■   (■ = on, · = off)
```

Ese byte, en pantalla, dibuja esos 8 píxeles en una misma fila, de izquierda a derecha.

---

## 4. De byte + bit al píxel exacto en pantalla

Para pasar de **“este byte en (row, col_byte)”** a la **posición (x, y) del píxel en pantalla**:

- El byte en `(row, col_byte)` cubre **8 píxeles** en la misma fila.
- El **primer píxel** del byte (bit 7) está en la columna de píxel `col_byte * 8`.
- Un **bit** dentro del byte (7…0) es el **desplazamiento** dentro de esos 8 píxeles.

Fórmula para la **coordenada X** del píxel correspondiente al bit `bit_index` (0 = LSB, 7 = MSB):

```text
pixel_x = base_x + (col_byte * 8) + (7 - bit_index)
pixel_y = base_y + row
```

O, si cuentas el bit de izquierda a derecha (0 = izquierda, 7 = derecha):

```text
pixel_x = base_x + (col_byte * 8) + bit_index   // bit_index 0..7 de izquierda a derecha
pixel_y = base_y + row
```

Donde:

- **base_x, base_y**: esquina superior izquierda donde dibujas la imagen en la ST7920.

Tabla para un byte en `(row, col_byte)` con `base_x = 10`, `base_y = 0`:

| Bit (7→0) | pixel_x (ej. base_x=10, col_byte=0) | pixel_y |
|-----------|--------------------------------------|--------|
| 7 (MSB)   | base_x + col_byte×8 + 0 = 10         | base_y + row |
| 6         | base_x + col_byte×8 + 1 = 11        | base_y + row |
| 5         | 12                                   | base_y + row |
| 4         | 13                                   | base_y + row |
| 3         | 14                                   | base_y + row |
| 2         | 15                                   | base_y + row |
| 1         | 16                                   | base_y + row |
| 0 (LSB)   | base_x + col_byte×8 + 7 = 17        | base_y + row |

Así puedes saber **qué bit exacto** (y por tanto qué píxel en pantalla) representa cada parte del valor del array.

---

## 5. Cómo determinar qué bit actualizar en la pantalla

En modo diff normalmente **no** actualizas bit a bit en la pantalla, sino **byte a byte**:

- **Offset** → indica **qué byte** del buffer (y de la imagen) reemplazar.
- **Valor** → es el **nuevo contenido completo** de ese byte (los 8 bits = 8 píxeles).

Por tanto, al aplicar un diff:

1. Usas el **offset** para saber **qué byte** actualizar (y su `row` y `col_byte`).
2. Escribes en pantalla **todo el byte** `valor` en la posición que corresponde a ese `(row, col_byte)`.

Eso actualiza de una vez los **8 píxeles** (los 8 bits) de ese byte. No hace falta calcular bit a bit a menos que tu driver solo permita escribir un píxel.

### Si tu API es “escribir un byte en (x, y)”

```c
// Escribir el byte completo en la posición correcta (8 píxeles horizontales)
uint16_t off = plot_diff_N_offsets[i];
uint8_t  val = plot_diff_N_values[i];
uint8_t row     = off / PLOT_BYTES_PER_ROW;
uint8_t col_byte = off % PLOT_BYTES_PER_ROW;

// Posición del primer píxel de ese byte en pantalla
uint8_t pixel_x = base_x + (col_byte * 8);
uint8_t pixel_y = base_y + row;

st7920_write_byte_at(pixel_x, pixel_y, val);  // actualiza los 8 bits (8 píxeles)
```

Con eso ya estás actualizando **todos los bits** de ese byte en la pantalla.

### Si solo puedes escribir un píxel (1 bit)

Entonces sí necesitas “reventar” el byte en bits y actualizar cada píxel:

```c
uint8_t val = plot_diff_N_values[i];
uint8_t pixel_x_base = base_x + (col_byte * 8);
uint8_t pixel_y = base_y + row;

for (int b = 7; b >= 0; b--) {  // bit 7 (MSB) = izquierda, bit 0 (LSB) = derecha
    uint8_t bit_val = (val >> b) & 1;
    uint8_t px = pixel_x_base + (7 - b);
    st7920_draw_pixel(px, pixel_y, bit_val);
}
```

O con índice de bit 0..7 de izquierda a derecha:

```c
for (int b = 0; b < 8; b++) {
    uint8_t bit_val = (val >> (7 - b)) & 1;
    uint8_t px = pixel_x_base + b;
    st7920_draw_pixel(px, pixel_y, bit_val);
}
```

Así puedes **mapear cada bit del valor del array al píxel exacto** en la pantalla cuando tu hardware solo permite escribir por píxel.

---

## 6. Resumen visual (un byte en la fila)

```text
Offset:     índice lineal del byte en el buffer (fila-major).
            → row = offset / BYTES_PER_ROW
            → col_byte = offset % BYTES_PER_ROW

Valor:      Un byte = 8 bits = 8 píxeles en una fila.
            Bit 7 (MSB) = píxel izquierdo, bit 0 (LSB) = píxel derecho.
            1 = encendido, 0 = apagado.

Pantalla:   Ese byte dibuja en:
            x = base_x + col_byte*8  ..  base_x + col_byte*8 + 7
            y = base_y + row

            Bit 7 → (base_x + col_byte*8,     base_y + row)
            Bit 0 → (base_x + col_byte*8 + 7, base_y + row)
```

Con esto puedes identificar a partir de un **offset** y un **valor** del array exactamente **qué byte** reemplazar, **cómo está formado** (qué bit es qué píxel) y **qué bits/píxeles** actualizar en la pantalla.
