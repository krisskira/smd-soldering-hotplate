
# Hot Plate Controller – ATmega16 Pin Definition Document

## Overview

This document defines the pin usage, architecture decisions, and configuration strategy for the main microcontroller used in the SMD Hot Plate controller.

Microcontroller: **ATmega16**

The goal of this document is to provide a clear reference for firmware agents or developers so they understand:

- Which pins are used
- What each pin does
- Why that pin was selected
- How the pins should be configured in firmware

The design philosophy is to **group pins by function** to simplify firmware and reduce configuration conflicts.

---

# Port Architecture Strategy

| Port | Purpose |
|-----|--------|
PORTB | Communication buses (SPI + LCD serial control) |
PORTD | User interface + UART + Power control |
PORTA | Reserved for expansion |
PORTC | Reserved for expansion / system control |

This separation avoids configuration conflicts and keeps firmware simple.

---

# PORTB – Communication and Display

PORTB is dedicated to communication protocols and display control.

## LCD ST7920 (Software SPI / Bitbang)

The LCD uses a serial protocol similar to SPI but **not fully SPI compliant**, therefore it is driven using a **software SPI implementation**.

| Pin | Signal | Direction | Description |
|----|----|----|----|
PB0 | LCD_RS | Output | LCD Register Select |
PB1 | LCD_RW | Output | LCD Serial Data |
PB2 | LCD_E  | Output | LCD Clock |

### Reason for Selection

- LCD serial interface is not true SPI
- Prevents conflicts with hardware SPI
- Allows precise timing control
- Keeps SPI bus free for other peripherals

---

## Hardware SPI Bus

Hardware SPI is used for high‑speed peripherals.

| Pin | Signal | Direction | Description |
|----|----|----|----|
PB4 | CS_MAX31865 | Output | Chip select for MAX31865 |
PB5 | MOSI | Output | SPI Master Out |
PB6 | MISO | Input | SPI Master In |
PB7 | SCK | Output | SPI Clock |

### Hardware Notes

- 330Ω series resistors are placed between MCU and MAX31865
- SPI pins are also connected to the **ICSP programming header**
- This allows in‑system programming without disconnecting peripherals

### Reason for Selection

- Matches ATmega16 hardware SPI pins
- Allows reliable ISP programming
- Keeps communication high speed and stable

---

# PORTD – User Interface and Power Control

PORTD is dedicated to UI input, communication with the PC, and power control.

## UART Communication

Used for communication with the USB interface chip.

| Pin | Signal | Direction | Description |
|----|----|----|----|
PD0 | RX | Input | UART receive |
| PD1 | TX | Output | UART transmit |

Connected to a USB‑UART bridge (CH340/CH430).

---

## Encoder (Menu Navigation)

The rotary encoder is used to control the interface.

| Pin | Signal | Direction | Description |
|----|----|----|----|
PD2 | MENU_CLK | Input | Encoder A |
PD3 | MENU_DT | Input | Encoder B |
PD4 | MENU_SW | Input | Encoder push button |

### Encoder Handling Strategy

Interrupts are **not used**.

Instead the firmware uses **polling**.

### Reason

- Simpler firmware
- Avoids interrupt noise from encoder bounce
- Polling at ~1kHz is sufficient for UI navigation

---

## Output Devices

| Pin | Signal | Direction | Description |
|----|----|----|----|
PD5 | BUZZER | Output | Buzzer control (PWM capable) |
PD6 | PTC2 | Output | Heater control channel 2 |
PD7 | PTC1 | Output | Heater control channel 1 |

### Purpose

- BUZZER provides user feedback
- PTC1 and PTC2 control heating elements

---

# PORTA – Reserved Expansion

PORTA is currently unused.

Future possibilities:

- Analog sensors
- Voltage monitoring
- Fan control
- Additional buttons

No configuration required yet.

---

# PORTC – Reserved Expansion

PORTC is also reserved.

Possible future uses:

- I²C sensors
- External EEPROM
- LCD reset line
- System status LEDs

---

# Firmware Initialization Example

Example initialization code for ports.

```c
// PORTB
DDRB =
    (1<<PB0) |   // LCD_RS
    (1<<PB1) |   // LCD_RW
    (1<<PB2) |   // LCD_E
    (1<<PB4) |   // CS_MAX31865
    (1<<PB5) |   // MOSI
    (1<<PB7);    // SCK

PORTB = (1<<PB4); // MAX31865 CS idle

// PORTD
DDRD =
    (1<<PD1) |   // TX
    (1<<PD5) |   // BUZZER
    (1<<PD6) |   // PTC2
    (1<<PD7);    // PTC1

PORTD =
    (1<<PD2) |   // encoder pull‑ups
    (1<<PD3) |
    (1<<PD4);
```

---

# Encoder Polling Strategy

Recommended polling frequency:

```
1 kHz timer interrupt
```

Example loop:

```
main loop
    read_encoder()
    update_menu()
    read_temperature()
    run_pid()
    update_display()
    handle_usb()
```

---

# Summary

Key design goals achieved:

- Clear port separation
- Dedicated hardware SPI bus
- Software SPI for LCD
- Reliable ISP programming
- Clean UI input handling
- Expansion capability

This architecture keeps firmware simple and scalable while maximizing reliability.
