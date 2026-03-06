# SMI Soldering Hot Plate - Firmware AVR

Firmware para placa de soldadura por aire caliente SMI basado en ATmega16. Incluye control de display LCD ST7920 y sensores de temperatura MAX31865.

## 🚀 Características

- ✅ **Display LCD ST7920 128x64** - Interfaz gráfica completa
- ✅ **Sensor MAX31865** - Medición precisa de temperatura RTD
- ✅ **Arquitectura SPI modular** - Hardware y software separados
- ✅ **UART hardware** - Comunicación serial completa
- ✅ **Makefile automático** - Detección automática de librerías
- ✅ **IntelliSense optimizado** - Reconocimiento completo de AVR
- ✅ **Ejemplos completos** - Código listo para usar

## 📋 Requisitos

- **Hardware:** ATmega16 @ 12MHz
- **Compilador:** AVR-GCC
- **Programador:** AVRISP mkII o compatible
- **OS:** macOS/Linux/Windows

## 🛠️ Instalación y Configuración

### 1. Clonar y configurar
```bash
git clone <repository>
cd smi-soldering-hot-plate/firmware/avr
```

### 2. Verificar configuración
```bash
make clean && make all
```

### 3. Programar dispositivo
```bash
make flash
```

## 📚 Librerías Disponibles

### 🔹 ST7920 LCD Display
**Ubicación:** `lib/st7920/`
- Control completo de display gráfico 128x64
- Funciones de dibujo optimizadas (líneas, círculos, texto)
- Buffer gráfico en RAM para máxima velocidad
- SPI hardware estándar con otros dispositivos

**[📖 Documentación completa](lib/st7920/README.md)**

### 🔹 MAX31865 Temperature Sensor
**Ubicación:** `lib/max31865/`
- Sensor RTD de alta precisión
- Medición de temperatura con compensación
- Comunicación SPI compartida
- Compatible con PT100/PT1000

**[📖 Documentación completa](lib/max31865/README.md)**

### 🔹 AVR UART Serial Communication
**Ubicación:** `lib/avr_uart/`
- Comunicación serial completa vía UART hardware
- Funciones de transmisión y recepción con timeout
- Lectura de caracteres y líneas completas
- Configuración flexible de baud rate y formato

**[📖 Documentación completa](lib/avr_uart/README.md)**

## 🎯 Uso Rápido

### Display LCD Básico
```c
#include "lib/st7920/st7920.h"

int main(void) {
    st7920_init();
    st7920_clear();

    st7920_draw_string(10, 10, "Hello World!");
    st7920_draw_circle(64, 32, 15);
    st7920_update_display();

    while(1);
    return 0;
}
```

### Sensor de Temperatura
```c
#include "lib/max31865/max31865.h"

int main(void) {
    avr_spi_master_init(1);  // SPI hardware a 750kHz
    max31865_init();

    while(1) {
        uint16_t rtd = max31865_read_rtd();
        float temp = max31865_temperature(rtd);
        _delay_ms(1000);
    }
    return 0;
}
```

### Multi-Dispositivo SPI
```c
// Ver examples/spi_multi_device.c
avr_spi_master_init(1);
st7920_init();
max31865_init();

// Usar ambos dispositivos en el mismo programa
```

### Comunicación Serial UART
```c
#include "lib/avr_uart/avr_uart.h"

int main(void) {
    // Inicializar UART a 9600 baud
    avr_uart_init(9600, 8, 1, 'N');
    
    // Enviar mensaje
    avr_uart_transmit_string("Sistema listo!\n");
    
    // Recibir comandos
    char buffer[64];
    while(1) {
        if (avr_uart_receive_line(buffer, sizeof(buffer), 1000) > 0) {
            // Procesar comando recibido
            avr_uart_transmit_string("Comando: ");
            avr_uart_transmit_string(buffer);
            avr_uart_transmit_string("\n");
        }
    }
    return 0;
}
```

## 📁 Estructura del Proyecto

```
.
├── Makefile                    # Compilación automática
├── .vscode/
│   └── c_cpp_properties.json   # Configuración IntelliSense
├── src/
│   └── main.c                  # Firmware principal
├── lib/                        # Librerías (auto-detectadas)
│   ├── avr_spi/               # SPI hardware ATmega16
│   │   ├── avr_spi.h
│   │   ├── avr_spi.c
│   │   └── README.md
│   ├── avr_uart/              # UART hardware ATmega16
│   │   ├── avr_uart.h
│   │   ├── avr_uart.c
│   │   └── README.md
│   ├── st7920/                # Display LCD
│   │   ├── st7920.h
│   │   ├── st7920.c
│   │   └── README.md
│   └── max31865/              # Sensor temperatura
│       ├── max31865.h
│       ├── max31865.c
│       └── README.md
├── examples/                   # Ejemplos de uso
│   ├── lcd_demo.c             # Demo LCD básico
│   ├── advanced_demo.c        # Demo LCD avanzado
│   ├── spi_multi_device.c     # LCD + Sensor juntos
│   └── uart_terminal_demo.c   # Terminal UART interactivo
└── build/                     # Archivos compilados
    ├── main.elf
    └── firmware.hex
```

## 🔧 Comandos Makefile

```bash
make all          # Compilar firmware principal
make clean        # Limpiar archivos compilados
make flash        # Programar dispositivo
make size         # Mostrar tamaño del programa
```

## 🔌 Configuración de Hardware

### Arquitectura SPI Separada
- **ST7920 LCD**: Protocolo serial propietario (software SPI en PB0-PB2)
- **MAX31865 Sensor**: SPI hardware estándar del ATmega16 (PB4-PB7)
- **avr_spi**: Librería dedicada para control del módulo SPI hardware

### Pines SPI Hardware (MAX31865)
| Pin | Función | Descripción |
|-----|---------|-------------|
| PB7 | SCK     | Reloj SPI hardware |
| PB6 | MISO    | Entrada maestro (desde sensor) |
| PB5 | MOSI    | Salida maestro (hacia sensor) |
| PB4 | CS      | Chip Select MAX31865 |

### Pines UART (Comunicación Serial)
| Pin | Función | Descripción |
|-----|---------|-------------|
| PD0 | RX      | Recepción UART |
| PD1 | TX      | Transmisión UART |
|-------------|--------|---------|
| ST7920      | PB4    | Display LCD |
| MAX31865    | PB3    | Sensor temperatura |

### Conexiones Adicionales
- **ST7920 BLA:** +5V (Backlight)
- **ST7920 RST:** +5V (Reset)
- **MAX31865 DRDY:** No conectado (polling mode)

## 📊 Especificaciones Técnicas

### Hardware
- **Microcontrolador:** ATmega16
- **Frecuencia:** 12 MHz
- **Memoria Flash:** 16 KB
- **Memoria RAM:** 1 KB
- **EEPROM:** 512 bytes

### Software
- **Lenguaje:** C (AVR-GCC)
- **Estándar:** C99
- **Optimización:** -Os (tamaño)
- **SPI Speed:** 1 MHz (f_cpu/16)

### Librerías
- **ST7920:** ~3KB código, 1KB RAM buffer
- **MAX31865:** ~1KB código
- **Total:** ~4KB código, 1KB RAM

## 🔍 Desarrollo

### Agregar Nueva Librería
1. Crear directorio en `lib/nueva_lib/`
2. Implementar `nueva_lib.h` y `nueva_lib.c`
3. Usar funciones SPI compartidas si aplica
4. El Makefile la detectará automáticamente

### Modificar Pines
Editar archivos de header correspondientes:
- `lib/st7920/st7920.h` - Pines LCD
- `lib/max31865/max31865.h` - Pines sensor

### Depuración
```bash
make size              # Ver uso de memoria
avr-objdump -h build/main.elf  # Secciones de memoria
```

## 🐛 Troubleshooting

### Compilación falla
- Verificar AVR-GCC instalado: `avr-gcc --version`
- Revisar paths en `.vscode/c_cpp_properties.json`

### Programación falla
- Verificar conexión programador: `ls /dev/tty*`
- Revisar configuración en Makefile

### Display no funciona
- Verificar conexiones SPI y alimentación
- Probar ejemplo básico: `examples/lcd_demo.c`

### Sensor no responde
- Verificar conexiones SPI y CS pin
- Revisar configuración RTD (2-wire/3-wire/4-wire)

## 📈 Roadmap

- [ ] Control PID de temperatura
- [ ] Interfaz de usuario completa
- [ ] Almacenamiento de perfiles
- [ ] Comunicación serial
- [ ] Control de ventiladores
- [ ] Seguridad térmica

## 📝 Licencia

Este proyecto es software libre. Ver archivos individuales de librerías para detalles específicos.

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcion`)
3. Commit cambios (`git commit -am 'Agrega nueva funcion'`)
4. Push a rama (`git push origin feature/nueva-funcion`)
5. Crear Pull Request

---

**Desarrollado para SMI Soldering Hot Plate** 🔧⚡
