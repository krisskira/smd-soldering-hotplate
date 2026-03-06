# SMI Soldering Hot Plate – Firmware AVR

Firmware para la placa de soldadura SMI basado en ATmega16. Incluye display LCD ST7920 (128x64). **La referencia es el código** (`config/board_pins.h`, `doc/atmega16_pin_definition_hotplate.md`).

## Características

- **Display LCD ST7920 128x64** – Modo gráfico, dibujo diferido (comandos + `st7920_render()`)
- **SPI hardware** – Bus compartido: LCD (CS=PB3), MAX31865 (CS=PB4)
- **Sin framebuffer completo** – Lista de comandos + buffer de una fila (~160 B RAM en draw)

## Build

```bash
cd smi-soldering-hot-plate/firmware/avr
make clean && make
make flash
make size
```

## Pines (resumen)

| Función      | Pin  | Notas        |
|-------------|------|--------------|
| LCD CS      | PB3  | ST7920       |
| MAX31865 CS | PB4  | Mismo SPI    |
| SPI         | PB5 (MOSI), PB6 (MISO), PB7 (SCK) | |
| UART        | PD0 (RX), PD1 (TX) |        |

LCD RST no conectado. Ver `doc/atmega16_pin_definition_hotplate.md`.

## Uso rápido (display)

```c
#include "lib/st7920/st7920.h"
#include "lib/avr_spi/avr_spi.h"

avr_spi_master_init();
st7920_init();
st7920_graphics_mode();

st7920_draw_rect(10, 10, 100, 30);
st7920_draw_line(0, 0, 127, 0);
st7920_draw_text(15, 20, "AB C");
st7920_draw_progressbar(10, 45, 100, 10, 65);
st7920_render();   /* obligatorio al final */
```

## Estructura

```
├── config/board_pins.h
├── doc/atmega16_pin_definition_hotplate.md
├── src/main.c
├── lib/
│   ├── avr_spi/
│   ├── avr_uart/
│   ├── st7920/        # LCD: config, draw, font
│   └── max31865/
└── build/
```

## Documentación por librería

- [lib/avr_spi/README.md](lib/avr_spi/README.md)
- [lib/avr_uart/README.md](lib/avr_uart/README.md)
- [lib/st7920/README.md](lib/st7920/README.md)
- [lib/max31865/README.md](lib/max31865/README.md)

## Comandos Make

- `make` – Compilar
- `make clean` – Limpiar
- `make flash` – Programar
- `make size` – Uso de memoria

---

**SMI Soldering Hot Plate**
