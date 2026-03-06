# Librería ST7920 - Display LCD 128x64

Control completo del display gráfico ST7920 128x64 mediante interfaz serial por software.

## 📋 Características

- ✅ **Display gráfico 128x64** píxeles
- ✅ **Interfaz serial por software** - Compatible con protocolo ST7920
- ✅ **Buffer gráfico completo** en RAM (1024 bytes)
- ✅ **Funciones de dibujo** optimizadas
- ✅ **Font ASCII 5x7** integrado
- ✅ **SPI compartido** con otros dispositivos

## 🔧 Hardware

### Pines de Control (Software SPI)
El display ST7920 utiliza una interfaz serial personalizada implementada por software, no compatible con SPI estándar.

| Pin ST7920 | Pin ATmega16 | Función |
|-----------|-------------|---------|
| RS        | PB0         | Register Select |
| RW        | PB1         | Read/Write (datos) |
| E         | PB2         | Enable/Clock |
| BLA       | +5V         | Backlight |
| GND       | GND         | Tierra |
| VDD       | +5V         | Alimentación |

**Nota:** Esta implementación por software permite control preciso del protocolo serial del ST7920, que no es completamente compatible con SPI estándar.

**Referencia:** Ver `doc/atmega16_pin_definition_hotplate.md` para detalles completos de asignación de pines.

## 🚀 Uso Rápido

```c
#include "lib/st7920/st7920.h"

int main(void) {
    st7920_init();
    st7920_clear();

    // Dibujar texto
    st7920_draw_string(10, 10, "Hello World!");

    // Dibujar formas
    st7920_draw_circle(64, 32, 15);
    st7920_draw_line(0, 0, 127, 63);
    st7920_draw_rectangle(20, 20, 50, 30);

    // Mostrar en pantalla
    st7920_update_display();

    while(1);
    return 0;
}
```

## 📚 API Reference

### Inicialización
- `st7920_init()` - Inicializar display
- `st7920_clear()` - Limpiar pantalla
- `st7920_display_on()` / `st7920_display_off()` - Control display

### Dibujo
- `st7920_draw_pixel(x, y)` - Dibujar píxel
- `st7920_clear_pixel(x, y)` - Borrar píxel
- `st7920_draw_line(x0, y0, x1, y1)` - Línea (Bresenham)
- `st7920_draw_circle(cx, cy, r)` - Círculo
- `st7920_draw_filled_circle(cx, cy, r)` - Círculo relleno
- `st7920_draw_rectangle(x, y, w, h)` - Rectángulo

### Texto
- `st7920_draw_char(x, y, c)` - Carácter individual
- `st7920_draw_string(x, y, str)` - Cadena de texto

### Pantalla
- `st7920_update_display()` - Actualizar pantalla física

## 🔧 SPI Compartido

```c
// Inicializar SPI (una sola vez)
avr_spi_master_init(1);

// Inicializar ST7920
st7920_init();

// Usar otras funciones...
st7920_draw_string(0, 0, "SPI Multi-Device!");
st7920_update_display();
```

## 📊 Especificaciones

- **Resolución:** 128x64 píxeles
- **Memoria:** 1024 bytes buffer RAM
- **Velocidad SPI:** 1 MHz
- **Tamaño código:** ~3KB
- **Modo:** Gráfico (no texto)

## 🎯 Algoritmos

- **Líneas:** Algoritmo de Bresenham
- **Círculos:** Midpoint circle algorithm
- **Texto:** Font bitmap 5x7 ASCII

## 🐛 Troubleshooting

### Pantalla negra
- Verificar alimentación (+5V, GND)
- Revisar backlight conectado
- Verificar conexiones SPI

### Texto no aparece
- Llamar `st7920_update_display()` después de dibujar
- Verificar coordenadas (0-127 x, 0-63 y)
- Revisar inicialización correcta

### Formas distorsionadas
- Verificar límites de pantalla
- Revisar coordenadas válidas
- Verificar buffer no corrupto

## 📈 Optimizaciones

- **Buffer único:** Todas las operaciones en RAM
- **Actualización por bloques:** Escritura eficiente SPI
- **Algoritmos optimizados:** Sin flotantes, enteros únicamente
- **Font comprimido:** 96 caracteres en ~500 bytes

## 🔍 Configuración Avanzada

### Modificar pines
```c
// En st7920.h
#define ST7920_CS_PIN    PB4  // Cambiar pin CS
#define ST7920_SPI_CLK   PB7  // Cambiar pin SCK
#define ST7920_SPI_MOSI  PB5  // Cambiar pin MOSI
```

### Buffer personalizado
```c
// Acceso directo al buffer
extern uint8_t display_buffer[128 * 8];

// Manipulación directa
display_buffer[y * 128 + x] |= (1 << (y % 8));
```

## 📝 Notas Técnicas

- **Coordenadas:** (0,0) = esquina superior izquierda
- **Actualización:** Solo `st7920_update_display()` escribe a LCD
- **SPI Mode:** 0 (CPOL=0, CPHA=0)
- **Endianness:** MSB first
- **Comandos:** 3 bytes por comando SPI

## 🎨 Ejemplos

### Barra de progreso
```c
void draw_progress_bar(uint8_t percent) {
    uint8_t width = (percent * 100) / 100;
    st7920_draw_rectangle(14, 30, width, 4);
    st7920_draw_string(14, 20, "Progress:");
    st7920_update_display();
}
```

### Gráfico simple
```c
void draw_graph(uint8_t data[], uint8_t count) {
    for (uint8_t i = 1; i < count; i++) {
        uint8_t x1 = (i-1) * 2;
        uint8_t y1 = 60 - (data[i-1] / 4);
        uint8_t x2 = i * 2;
        uint8_t y2 = 60 - (data[i] / 4);
        st7920_draw_line(x1, y1, x2, y2);
    }
    st7920_update_display();
}
```

## 📚 Referencias

- [ST7920 Datasheet](https://www.crystalfontz.com/controllers/ST7920/)
- [SPI Communication](https://en.wikipedia.org/wiki/Serial_Peripheral_Interface)
- [Bresenham Algorithm](https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm)

---

**Parte del proyecto SMI Soldering Hot Plate** 🔧⚡