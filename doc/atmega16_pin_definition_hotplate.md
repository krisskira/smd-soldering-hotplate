# Hot Plate Controller – ATmega16 Pin Definition

## Resumen

Documento de referencia de pines del ATmega16 para la placa SMD Hot Plate. **La fuente de verdad es el código** (`config/board_pins.h` y las librerías en `lib/`).

- **MCU:** ATmega16
- **Objetivo:** Pines por función, sin conflictos

**Documentación relacionada:**
- [doc/optimizacion_temporizados.md](optimizacion_temporizados.md) – Guía oficial de temporización no bloqueante (estilo millis)
- [lib/avr_soft_spi/README.md](../lib/avr_soft_spi/README.md) – SPI por software (MAX31865)
- [lib/avr_spi/README.md](../lib/avr_spi/README.md) – SPI hardware (LCD)

---

## Estrategia por puerto

| Puerto  | Uso principal                          |
|--------|----------------------------------------|
| PORTB  | SPI hardware (LCD) + Chip Selects (LCD, MAX31865) |
| PORTA  | SPI software (MAX31865)                |
| PORTD  | UART, encoder, buzzer, calefacción    |
| PORTC  | Reservado expansión                    |

---

## PORTB – LCD y Chip Selects

### Bus SPI hardware (solo LCD)

| Pin  | Señal | Dirección | Descripción                    |
|------|--------|-----------|--------------------------------|
| PB0  | LCD_CS | Salida    | Chip Select display ST7920    |
| PB1  | MAX_CS | Salida    | Chip Select MAX31865          |
| PB5  | MOSI   | Salida    | SPI Master Out (LCD)          |
| PB6  | MISO   | Entrada   | SPI Master In (LCD)            |
| PB7  | SCK    | Salida    | Reloj SPI (LCD)                |

### ST7920 (LCD 128x64)

- **Interfaz:** Protocolo serie compatible con SPI (modo 8 bits), usando el **SPI hardware** del AVR.
- **Conexiones:** LCD_CS=PB0, MOSI=PB5, SCK=PB7. MISO no usado para el LCD.
- **RST:** No conectado; la inicialización por software es suficiente.

---

## PORTA – SPI software (MAX31865)

| Pin  | Señal | Dirección | Descripción                    |
|------|--------|-----------|--------------------------------|
| PA0  | MOSI   | Salida    | SPI software Master Out       |
| PA1  | MISO   | Entrada   | SPI software Master In        |
| PA2  | SCK    | Salida    | Reloj SPI software            |

### MAX31865 (sensor temperatura RTD)

- **Interfaz:** SPI por software (bit-banging), modo 1. Ver [lib/avr_soft_spi/README.md](../lib/avr_soft_spi/README.md).
- **Conexiones:** CS=PB1, MOSI=PA0, MISO=PA1, SCK=PA2.
- **DRDY:** No conectado; se usa modo polling.
- Resistencias en serie (p. ej. 330 Ω) entre MCU y MAX31865 según diseño.
- **Lectura periódica:** temporizada con `delay_ms()` (ver [doc/optimizacion_temporizados.md](optimizacion_temporizados.md)).

---

## PORTD – Interfaz de usuario y potencia

| Pin  | Señal    | Dirección | Descripción           |
|------|----------|-----------|------------------------|
| PD0  | RX       | Entrada   | UART recepción         |
| PD1  | TX       | Salida    | UART transmisión       |
| PD2  | MENU_CLK | Entrada   | Encoder A              |
| PD3  | MENU_DT  | Entrada   | Encoder B              |
| PD4  | MENU_SW  | Entrada   | Pulsador del encoder   |
| PD5  | BUZZER   | Salida    | Buzzer (PWM posible)   |
| PD6  | PTC2     | Salida    | Calefactor 2           |
| PD7  | PTC1     | Salida    | Calefactor 1           |

- UART: puente USB (p. ej. CH340).
- Encoder: sin interrupciones; polling a ~1 kHz.

---

## PORTC

Reservado para expansión (sensores, I²C, LEDs, etc.).

---

## Ejemplo de inicialización (referencia)

```c
// PORTB: SPI hardware (LCD) + CS
DDRB |= (1 << PB0) | (1 << PB1) | (1 << PB5) | (1 << PB7);
DDRB &= ~(1 << PB6);
PORTB |= (1 << PB0) | (1 << PB1);  // CS en reposo alto

// PORTA: SPI software (MAX31865)
DDRA |= (1 << PA0) | (1 << PA2);
DDRA &= ~(1 << PA1);

// PORTD: UART, encoder, salidas
DDRD |= (1 << PD1) | (1 << PD5) | (1 << PD6) | (1 << PD7);
PORTD |= (1 << PD2) | (1 << PD3) | (1 << PD4);  // pull-ups encoder
```

---

## Resumen

- LCD ST7920: **SPI hardware** (PB5/PB6/PB7), CS en **PB0**, RST no conectado.
- MAX31865: **SPI software** (PA0/PA1/PA2), CS en **PB1**.
- Pines y nombres deben coincidir con `config/board_pins.h` y con las librerías en `lib/`.

## Referencias rápidas

| Dispositivo | SPI | Pines MOSI/MISO/SCK | CS |
|-------------|-----|---------------------|-----|
| LCD ST7920  | Hardware | PB5 / PB6 / PB7 | PB0 |
| MAX31865    | Software | PA0 / PA1 / PA2 | PB1 |
