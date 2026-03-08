# SMI Soldering Hot Plate – Firmware AVR

Firmware para la placa de soldadura SMI basado en ATmega16. Incluye display LCD ST7920 (128x64). **La referencia es el código** (`config/board_pins.h`, `doc/atmega16_pin_definition_hotplate.md`).

## Características

- **Display LCD ST7920 128x64** – Modo gráfico, dibujo diferido (comandos + `st7920_render()`), animaciones por frame 0 + diffs. Una o varias animaciones con `st7920_animation_run_all(slots, n)`. Ver [lib/st7920/README.md](lib/st7920/README.md).
- **SPI hardware** (LCD) – PB5 MOSI, PB6 MISO, PB7 SCK, PB0 CS
- **SPI software** (MAX31865) – PA0 MOSI, PA1 MISO, PA2 SCK, PB1 CS. Ver [lib/avr_soft_spi/README.md](lib/avr_soft_spi/README.md).
- **Temporización no bloqueante** – Estilo Arduino millis con `avr_delay`. Ver [doc/optimizacion_temporizados.md](doc/optimizacion_temporizados.md).
- **Sin framebuffer completo** – Lista de comandos + buffer de una fila (~160 B RAM en draw)

## Build

```bash
cd smi-soldering-hot-plate/firmware/avr
make clean && make
make flash
make size
```

## Pines (resumen)

| Función      | Pin  | Notas                    |
|-------------|------|--------------------------|
| LCD CS      | PB0  | ST7920 (SPI hardware)    |
| MAX31865 CS | PB1  | SPI software en PORTA   |
| SPI hardware | PB5 (MOSI), PB6 (MISO), PB7 (SCK) | LCD |
| SPI software | PA0 (MOSI), PA1 (MISO), PA2 (SCK) | MAX31865 |
| UART        | PD0 (RX), PD1 (TX) |        |

LCD RST no conectado. Ver [doc/atmega16_pin_definition_hotplate.md](doc/atmega16_pin_definition_hotplate.md).

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
├── doc/optimizacion_temporizados.md    # Guía oficial de temporización
├── src/main.c
├── lib/
│   ├── avr_delay/     # Temporización no bloqueante (timer, estilo millis)
│   ├── avr_spi/       # SPI hardware (LCD)
│   ├── avr_soft_spi/  # SPI software (MAX31865)
│   ├── avr_uart/
│   ├── st7920/        # LCD: config, draw, font
│   └── max31865/
└── build/
```

## Documentación por librería

- [lib/avr_delay/README.md](lib/avr_delay/README.md) – Temporización no bloqueante (delay_ms, delay_sec, delay_min)
- [lib/avr_spi/README.md](lib/avr_spi/README.md) – SPI hardware (LCD)
- [lib/avr_soft_spi/README.md](lib/avr_soft_spi/README.md) – SPI software (MAX31865)
- [lib/avr_uart/README.md](lib/avr_uart/README.md)
- [lib/st7920/README.md](lib/st7920/README.md)
- [lib/max31865/README.md](lib/max31865/README.md)

## Documentación adicional

- [doc/optimizacion_temporizados.md](doc/optimizacion_temporizados.md) – **Guía oficial:** temporización no bloqueante (estilo millis), ejemplo de main.c, consumir gráficos y datos en procesos asíncronos.
- [doc/atmega16_pin_definition_hotplate.md](doc/atmega16_pin_definition_hotplate.md) – Pines, SPI hardware/software, referencias.
- [doc/animaciones_no_bloqueantes.md](doc/animaciones_no_bloqueantes.md) – Animaciones con `run_all` y slots.
- [doc/delays_no_bloqueantes.md](doc/delays_no_bloqueantes.md) – Patrón de delays reutilizables.

## Comandos Make

- `make` – Compilar
- `make clean` – Limpiar
- `make flash` – Programar
- `make size` – Uso de memoria

---

**SMI Soldering Hot Plate**
