# Hot Plate Controller – ATmega16 Pin Definition

## Resumen

Documento de referencia de pines del ATmega16 para la placa SMD Hot Plate. **La fuente de verdad es el código** (`config/board_pins.h` y las librerías en `lib/`).

- **MCU:** ATmega16
- **Objetivo:** Pines por función, sin conflictos

---

## Estrategia por puerto

| Puerto  | Uso principal                          |
|--------|----------------------------------------|
| PORTB  | SPI hardware + Chip Selects (LCD, MAX31865) |
| PORTD  | UART, encoder, buzzer, calefacción    |
| PORTA  | Reservado expansión                    |
| PORTC  | Reservado expansión                    |

---

## PORTB – Comunicación y display

### Bus SPI hardware

El **mismo bus SPI** (MOSI, MISO, SCK) se comparte entre LCD y MAX31865. Cada periférico tiene su propio **Chip Select (CS)**.

| Pin  | Señal | Dirección | Descripción                    |
|------|--------|-----------|--------------------------------|
| PB2  | LCD_CS | Salida    | Chip Select display ST7920 (ver `config/board_pins.h`) |
| PB3  | —      | —         | Libre si LCD está en PB2 |
| PB4  | CS_MAX31865 | Salida | Chip Select MAX31865        |
| PB5  | MOSI   | Salida    | SPI Master Out                 |
| PB6  | MISO   | Entrada   | SPI Master In                  |
| PB7  | SCK    | Salida    | Reloj SPI                      |

### ST7920 (LCD 128x64)

- **Interfaz:** Protocolo serie compatible con SPI (modo 8 bits), usando el **SPI hardware** del AVR.
- **Conexiones:** LCD_CS=PB3, MOSI=PB5, SCK=PB7. MISO no usado para el LCD.
- **RST:** No conectado; la inicialización por software es suficiente.

### MAX31865 (sensor temperatura RTD)

- **Conexiones:** CS=PB4, MOSI=PB5, MISO=PB6, SCK=PB7.
- **DRDY:** No conectado; se usa modo polling.

### Notas

- Resistencias en serie (p. ej. 330 Ω) entre MCU y MAX31865 según diseño.
- Pines SPI (PB4–PB7) suelen ir al conector ICSP para programación in-system.

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

## PORTA y PORTC

Reservados para expansión (sensores, I²C, LEDs, etc.). Sin asignación en el código actual.

---

## Ejemplo de inicialización (referencia)

```c
// PORTB: SPI + CS
DDRB |= (1 << PB3) | (1 << PB4) | (1 << PB5) | (1 << PB7);
DDRB &= ~(1 << PB6);
PORTB |= (1 << PB3) | (1 << PB4);  // CS en reposo alto

// PORTD: UART, encoder, salidas
DDRD |= (1 << PD1) | (1 << PD5) | (1 << PD6) | (1 << PD7);
PORTD |= (1 << PD2) | (1 << PD3) | (1 << PD4);  // pull-ups encoder
```

---

## Resumen

- LCD ST7920: **SPI hardware**, CS en **PB3**, RST no conectado.
- MAX31865: **SPI hardware**, CS en **PB4**.
- Pines y nombres deben coincidir con `config/board_pins.h` y con las librerías en `lib/`.
