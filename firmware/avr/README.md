# SMI Soldering Hot Plate – Firmware AVR

Firmware ATmega16 @ **8 MHz**: HOME (Heat|Settings), HEAT (+ fase PREHEAT), PID_TUNE,
rampas EEPROM, PID (SSR MOC3021+BT136), MODO USB / AT, EEPROM **v8**.

**Docs:** [product_features.md](doc/product_features.md) (producto + mapa código) · [program_flows.md](doc/program_flows.md) · [architecture.md](doc/architecture.md) · [usb-automation.md](doc/usb-automation.md)

## Build

```bash
cd firmware/avr
make clean && make && make size
make usb-host-test
make flash
```

Presupuesto flash: **16384 B (100% típico)**. Tras cualquier cambio: `make size`.

## Características

- Home: Heat (temp 8×12, fase, info) | Settings embebido (R1…R4 + DLY)
- Overlay USB: temp + `USB` + icono 16×16; solo entra con `AT+MODE=1`
- Programas AT: `AT+RUN=1` (HEAT), `AT+RUN=2` (PID_TUNE). PREHEAT **no** es programa
- Pipeline HEAT: delay? → PREHEAT/STABILIZE (si `preheat_en`) → RUN rampas → aire @ `temp_min`
- Safety: `temp_min` 50..100, `temp_max` 40..250 (EEPROM)
- Pies LCD: `RUN` / `STOP` / `EXIT`
