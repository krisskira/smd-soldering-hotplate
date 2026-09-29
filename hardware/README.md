# Hardware

## PCB (`pcb/`)

Proyecto KiCad de **HotPlate**:

- `controller.*` — placa de control (ATmega16, LCD, encoder, MAX31865, …)
- `power-stage.*` — etapa de potencia / SSR
- `smd-soldering-hotplate-pcb.csv` — BOM
- `pcb-cnc/` — exports CNC si aplica

Abrir los `.kicad_pro` con KiCad 8+.

## Datasheets (`datasheets/`)

PDFs de referencia: ATmega16, MAX31865, MOC3021, BT136, ST7920, CH340, HLK-PM01, etc.

Pines de firmware: `firmware/avr/doc/atmega16_pin_definition_hotplate.md` ↔ `firmware/avr/config/board_pins.h`.
