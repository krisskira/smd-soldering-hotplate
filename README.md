# SMI Soldering Hot Plate – Firmware AVR

Firmware ATmega16 @ **8 MHz**: HOME (Heat|Settings), HEAT/PREHEAT/PID_TUNE,
rampas EEPROM, PID (SSR MOC3021+BT136), MODO USB / AT, EEPROM v4.

**Docs:** [product_features.md](doc/product_features.md) · [program_flows.md](doc/program_flows.md) · [architecture.md](doc/architecture.md) · [usb-automation.md](doc/usb-automation.md)

## Build

```bash
cd firmware/avr
make clean && make && make size
make usb-host-test
make flash
```

Gates: `UI_NO_ICONS`, `NO_FONT_6X8`. `pid_atune.c` enlazado.

## Características

- Home: Heat (delay 0.. + start) | Settings → PID
- USB: solo `AT+DEVICEMODE=USB`
- Programas: HEAT, PREHEAT (AT), PID_TUNE
- Pipeline HEAT: delay? → preheat Ramp1 → RUN rampas → aire @ temp_min
- Safety: temp_min 30..100, temp_max 40..250 (EEPROM)
