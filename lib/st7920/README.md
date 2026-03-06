# ST7920 – Display LCD 128x64

Control del display gráfico ST7920 128x64 mediante **SPI hardware** y dibujo diferido (lista de comandos + `st7920_render()`). Sin framebuffer completo para ahorrar RAM.

## Hardware (según código)

| Señal LCD | Pin ATmega16 | Notas        |
|-----------|--------------|--------------|
| CS        | PB3          | Chip Select  |
| MOSI/SCK  | PB5, PB7     | SPI hardware |
| RST       | No conectado | No usado     |

Referencia: `config/board_pins.h`, `lib/st7920/st7920_config.c`.

## Uso básico

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"

int main(void) {
    avr_spi_master_init();
    st7920_init();
    st7920_graphics_mode();

    st7920_draw_rect(10, 10, 100, 30);
    st7920_draw_line(0, 0, 127, 0);
    st7920_draw_text(5, 20, "Hola");
    st7920_draw_progressbar(10, 45, 100, 10, 65);
    st7920_render();  /* obligatorio: envía todos los comandos al LCD */

    for (;;) {}
}
```

## API

### Configuración
- `st7920_init()` – Inicializa el display.
- `st7920_clear()` – Limpia RAM de texto (modo texto).
- `st7920_graphics_mode()` – Modo gráfico y borrado de GDRAM.

### Dibujo (acumulan comandos; se envían con `st7920_render()`)
- `st7920_draw_pixel(x, y)`
- `st7920_draw_line(x0, y0, x1, y1)`
- `st7920_draw_rect(x, y, w, h)`
- `st7920_draw_progressbar(x, y, w, h, percent)`
- `st7920_draw_text(x, y, str)`
- `st7920_draw_bitmap(x, y, w, h, data)` – Carga y dibuja un mapa de bits (véase más abajo).

### Pantalla
- `st7920_render()` – Interpreta la lista de comandos y envía todo al LCD. Borra la pantalla al inicio.

## Carga de mapas de bit

`st7920_draw_bitmap(x, y, w, h, data)` añade un bitmap a la lista de comandos. En `st7920_render()` se dibuja en la posición `(x, y)` con tamaño `w`×`h` píxeles.

- **Formato de `data`:** por filas, 1 bit por píxel. Cada fila tiene `(w + 7) / 8` bytes. Bit más significativo = píxel izquierdo. Orden: fila 0, fila 1, …
- **Origen:** puntero a RAM. Para datos en flash (PROGMEM) hace falta copiarlos a un buffer en RAM antes de dibujar, o se puede añadir más adelante una variante `st7920_draw_bitmap_pgm`.

Ejemplo (icono 8×8 en RAM):

```c
const uint8_t icono[] = {
    0x3C, 0x42, 0xA5, 0x81, 0xA5, 0x99, 0x42, 0x3C
};
st7920_draw_bitmap(10, 20, 8, 8, icono);
st7920_render();
```


## Memoria

- Lista de comandos: 24 entradas × 7 bytes.
- Buffer de una fila: 16 B.

## Estructura del código

- `st7920_config.c` – Init, comandos, GDRAM bajo nivel.
- `st7920_draw.c` – Lista de comandos, render por filas, bitmap.
- `st7920_font.c` – Fuente 5x7 en PROGMEM y texto para el render.

## Coordenadas

- (0,0) = esquina superior izquierda.
- x: 0–127, y: 0–63.
