# Librería MAX31865 - Sensor de Temperatura RTD

Librería para controlar el sensor de temperatura MAX31865 con RTD PT100/PT1000 mediante SPI compartido.

## 📋 Características

- ✅ **Sensor RTD de alta precisión** (PT100/PT1000)
- ✅ **Conversión automática** de resistencia a temperatura
- ✅ **SPI compartido** - Compatible con múltiples dispositivos
- ✅ **Configuración flexible** (2-wire, 3-wire, 4-wire)
- ✅ **Detección de fallos** integrada
- ✅ **Compensación de temperatura** automática

## 🔧 Configuración de Hardware

### Pines de conexión (ATmega16)
| Pin MAX31865 | Pin ATmega16 | Función |
|-------------|-------------|---------|
| CS          | PB4         | Chip Select |
| SCK         | PB7         | Serial Clock (compartido) |
| SDI (MOSI)  | PB5         | Master Out/Slave In (compartido) |
| SDO (MISO)  | PB6         | Master In/Slave Out (compartido) |
| DRDY        | No conectar | Data Ready (modo polling) |
| VIN         | +3.3V/+5V  | Alimentación |
| GND         | GND         | Tierra |

**Referencia:** Ver `doc/atmega16_pin_definition_hotplate.md` para detalles completos de asignación de pines y arquitectura SPI compartida.

### Configuración RTD
- **PT100:** Resistencia nominal 100Ω a 0°C
- **PT1000:** Resistencia nominal 1000Ω a 0°C
- **Cableado:** 2-wire (recomendado), 3-wire, 4-wire

## 🚀 Instalación

1. Copiar carpeta `lib/max31865/` al proyecto
2. Incluir header: `#include "lib/max31865/max31865.h"`
3. Usar funciones SPI compartidas

## 📖 Uso Básico

### Inicialización
```c
#include "lib/max31865/max31865.h"

// Inicializar SPI hardware (una sola vez)
avr_spi_master_init(1);

// Inicializar sensor
max31865_init();
```

### Lectura de temperatura
```c
// Leer valor RTD (ADC)
uint16_t rtd_value = max31865_read_rtd();

// Convertir a temperatura (°C)
float temperature = max31865_temperature(rtd_value);

// Verificar errores
if (temperature < -100.0f) {
    // Error de sensor
    printf("Error de sensor\n");
} else {
    printf("Temperatura: %.2f C\n", temperature);
}
```

### Ejemplo completo
```c
#define F_CPU 4000000UL
#include <avr/io.h>
#include <util/delay.h>
#include <stdio.h>
#include "lib/max31865/max31865.h"

int main(void) {
    // Inicializar SPI y sensor
    avr_spi_master_init(1);
    max31865_init();

    while(1) {
        // Leer temperatura
        uint16_t rtd = max31865_read_rtd();
        float temp = max31865_temperature(rtd);

        // Procesar temperatura...
        _delay_ms(1000);
    }

    return 0;
}
```

## 🔧 Configuración Avanzada

### Modificar pines CS
```c
// En max31865.h
#define MAX31865_CS_PIN    PB3  // Cambiar pin CS
```

### Configuración del sensor
```c
// Configuración por defecto (2-wire, auto-convert)
uint8_t config = MAX31865_CONFIG_VBIAS | MAX31865_CONFIG_CONVERSION;
max31865_write_register(MAX31865_REG_CONFIG, config);

// Para 3-wire RTD
uint8_t config_3wire = MAX31865_CONFIG_VBIAS |
                      MAX31865_CONFIG_CONVERSION |
                      MAX31865_CONFIG_3WIRE;
max31865_write_register(MAX31865_REG_CONFIG, config_3wire);
```

### Acceso directo a registros
```c
// Leer registro
uint8_t config = max31865_read_register(MAX31865_REG_CONFIG);

// Escribir registro
max31865_write_register(MAX31865_REG_CONFIG, new_config);
```

## 📊 Especificaciones Técnicas

### Precisión
- **Resolución:** 15 bits (0.03125°C con PT100)
- **Precisión:** ±0.5°C (típico)
- **Rango:** -200°C a +850°C
- **Tiempo conversión:** ~100ms

### Registros del MAX31865
| Registro | Dirección | Descripción |
|----------|-----------|-------------|
| CONFIG   | 0x00      | Configuración |
| RTD_MSB  | 0x01      | Valor RTD (MSB) |
| RTD_LSB  | 0x02      | Valor RTD (LSB) |
| FAULT_MSB| 0x03      | Límite alto falla |
| FAULT_LSB| 0x04      | Límite bajo falla |
| FAULT_STATUS | 0x07   | Estado de fallas |

### Bits de configuración
```c
#define MAX31865_CONFIG_VBIAS       0x80  // Bias voltage
#define MAX31865_CONFIG_CONVERSION  0x40  // Auto conversion
#define MAX31865_CONFIG_1SHOT       0x20  // Single shot
#define MAX31865_CONFIG_3WIRE       0x10  // 3-wire RTD
#define MAX31865_CONFIG_FAULT_CLEAR 0x02  // Clear faults
#define MAX31865_CONFIG_50HZ        0x01  // 50Hz filter
```

## 🔍 Funciones de la API

### Inicialización
- `max31865_init()` - Inicializar sensor con configuración por defecto

### Lectura
- `max31865_read_rtd()` - Leer valor ADC del RTD
- `max31865_temperature(rtd_value)` - Convertir ADC a temperatura °C

### Registros
- `max31865_read_register(reg)` - Leer registro
- `max31865_write_register(reg, value)` - Escribir registro

## 🐛 Troubleshooting

### Temperatura incorrecta
- Verificar tipo de RTD (PT100 vs PT1000)
- Revisar configuración de cableado (2/3/4 wire)
- Verificar conexiones del sensor

### Lectura falla
- Verificar conexiones SPI (SCK, MOSI, MISO)
- Revisar pin CS (debe estar en alto cuando no se usa)
- Verificar alimentación del sensor (3.3V)

### Error de conversión
- Esperar tiempo de conversión (~100ms)
- Verificar configuración VBIAS habilitada
- Revisar estado de fallas con registro FAULT_STATUS

### Valores inconsistentes
- Agregar filtrado software
- Verificar estabilidad de alimentación
- Considerar ruido electromagnético

## 📈 Algoritmo de Conversión

La librería implementa la **ecuación Callendar-Van Dusen** para conversión RTD:

```
Rt = R0 * (1 + A*T + B*T²)  [para T ≥ 0°C]
Rt = R0 * (1 + A*T + B*T² + C*T³*(T-100))  [para T < 0°C]
```

Donde:
- **Rt:** Resistencia medida
- **R0:** Resistencia nominal (100Ω o 1000Ω)
- **A, B, C:** Coeficientes del sensor
- **T:** Temperatura en °C

## 🔄 SPI Compartido

Esta librería usa el **módulo SPI hardware** del ATmega16:

```c
// Inicializar SPI hardware (una sola vez)
avr_spi_master_init(1);

// Seleccionar MAX31865
avr_spi_select_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
// ... comunicación SPI ...
avr_spi_deselect_device(MAX31865_CS_PIN, &MAX31865_CS_PORT);
```

## 📝 Notas de Implementación

- **Modo polling:** No usa interrupciones DRDY
- **Configuración fija:** 2-wire RTD por defecto
- **Sin filtrado:** Implementar filtrado en aplicación si es necesario
- **Unidad de temperatura:** Celsius (°C)

## 🎯 Ejemplos Avanzados

### Con filtrado de temperatura
```c
#define FILTER_SIZE 10
float temp_filter[FILTER_SIZE];
uint8_t filter_index = 0;

float read_filtered_temperature() {
    uint16_t rtd = max31865_read_rtd();
    float temp = max31865_temperature(rtd);

    if (temp > -100.0f) {
        temp_filter[filter_index] = temp;
        filter_index = (filter_index + 1) % FILTER_SIZE;

        // Calcular promedio
        float sum = 0;
        for (uint8_t i = 0; i < FILTER_SIZE; i++) {
            sum += temp_filter[i];
        }
        return sum / FILTER_SIZE;
    }

    return temp; // Error
}
```

### Detección de fallas
```c
uint8_t check_sensor_faults() {
    uint8_t fault_status = max31865_read_register(MAX31865_REG_FAULT_STATUS);

    if (fault_status & 0x01) {
        // RTD High Threshold
    }
    if (fault_status & 0x02) {
        // RTD Low Threshold
    }
    if (fault_status & 0x04) {
        // REFIN- > 0.85 x VBIAS
    }
    if (fault_status & 0x08) {
        // REFIN- < 0.85 x VBIAS (FORCE- open)
    }
    if (fault_status & 0x10) {
        // RTDIN- < 0.85 x VBIAS (FORCE- open)
    }
    if (fault_status & 0x20) {
        // Overvoltage/Undervoltage fault
    }

    // Limpiar fallas
    max31865_write_register(MAX31865_REG_CONFIG,
        MAX31865_CONFIG_FAULT_CLEAR);

    return fault_status;
}
```

## 📚 Referencias

- [MAX31865 Datasheet](https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)
- [PT100 Temperature Tables](https://www.omega.com/temperature/z/pdf/z252-254.pdf)
- [Callendar-Van Dusen Equation](https://en.wikipedia.org/wiki/Callendar%E2%80%93Van_Dusen_equation)

---

**Parte del proyecto SMI Soldering Hot Plate** 🔧⚡