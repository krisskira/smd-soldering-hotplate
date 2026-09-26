# SMI Soldering Hot Plate – Firmware AVR

Firmware ATmega16 @ **8 MHz**: HOME + programas PREHEAT/START_IN/STOP_IN,
fase RAMPS, PID por ventana, **MODO USB** / AT, Ajustes EEPROM.

**Docs:** [product_features.md](doc/product_features.md) · [architecture.md](doc/architecture.md) · [usb-automation.md](doc/usb-automation.md) · [ui_style_guide.md](doc/ui_style_guide.md)

## Build

```bash
cd firmware/avr
make clean && make && make size
make usb-host-test
make flash
```

Un solo firmware (sin perfiles PANEL/USB). Gates de flash en Makefile:
`NO_PID_ATUNE`, `UI_NO_ICONS`, sin font6x8/8x12/icons.

## Características

- HOME → Ajustes (Modo USB, Rampas, sonido, precalentar, aire)
- MODO USB: sesión exclusiva `AT+DEVICEMODE=USB|MANUAL`
- Programas: PREHEAT, START_IN, STOP_IN (+ PID_TUNE cuando haya flash/UI)
- Pipeline: preheat? → rampas → FIN (alarma + aire)
- Corte ≥ 200 °C; salidas OFF al boot; banco PTC unificado
