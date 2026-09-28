# SMI Soldering Hot Plate

Plancha de soldadura SMD controlada: ATmega16 + PT100 + SSR + LCD ST7920, automatizable por UART/AT y app de escritorio.

## Mapa del repositorio

| Ruta | Contenido |
|------|-----------|
| [`firmware/avr/`](firmware/avr/) | Firmware bare-metal (avr-gcc, 8 MHz) |
| [`host-ui/`](host-ui/) | App de escritorio (Python) — modo USB / AT |
| [`hardware/pcb/`](hardware/pcb/) | PCB KiCad (controlador + etapa de potencia) |
| [`hardware/datasheets/`](hardware/datasheets/) | Datasheets (ATmega16, MAX31865, MOC3021, BT136, ST7920, …) |
| [`mechanical/`](mechanical/) | Carcasa / tapas / perilla (3MF, Fusion `.f3d`) |
| [`icons/`](icons/) | Fuentes de iconos (GIF/BMP → firmware) |
| [`docs/`](docs/) | Índice de documentación del proyecto |
| [`AGENTS.md`](AGENTS.md) | Reglas cortas para agentes / desarrollo |

## Documentación (firmware)

- Producto: [`firmware/avr/doc/product_features.md`](firmware/avr/doc/product_features.md)
- Flujos / EEPROM / alarmas: [`program_flows.md`](firmware/avr/doc/program_flows.md)
- Arquitectura: [`architecture.md`](firmware/avr/doc/architecture.md)
- USB / AT: [`usb-automation.md`](firmware/avr/doc/usb-automation.md)

## Build rápido

```bash
# Firmware
cd firmware/avr && make clean && make && make size && make usb-host-test

# Host UI
cd host-ui && pip install -r requirements.txt && python app.py
```

Flash ATmega16: **16384 B** — medir siempre con `make size`.

## Licencia / autoría

Proyecto SMI — soldadura SMD en banco.
