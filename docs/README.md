# Documentación — SMI Soldering Hot Plate

Índice del monorepo. El detalle de producto vive sobre todo bajo `firmware/avr/doc/`.

## General

| Doc | Descripción |
|-----|-------------|
| [../README.md](../README.md) | Producto, features y mapa del repo |
| [../AGENTS.md](../AGENTS.md) | Reglas de desarrollo / agentes |

## Firmware

| Doc | Descripción |
|-----|-------------|
| [../firmware/avr/README.md](../firmware/avr/README.md) | Build y visión firmware |
| [product_features.md](../firmware/avr/doc/product_features.md) | Producto / HotPanel / EEPROM · mapa doc↔código |
| [feature_budget.md](../firmware/avr/doc/feature_budget.md) | **Presupuesto flash** · core vs minify · UI aprobada (skill `hotplate-feature-budget`) |
| [pid_control.md](../firmware/avr/doc/pid_control.md) | **PI predictivo + Autotune** portable (variables, fórmulas, tuning) |
| [optimization_plan.md](../firmware/avr/doc/optimization_plan.md) | Plan de optimización sin romper cores/UI |
| [mejoras_futuras.md](../firmware/avr/doc/mejoras_futuras.md) | Resultados térmicos, límites medidos y mejoras de algoritmo |
| [program_flows.md](../firmware/avr/doc/program_flows.md) | **Maestro** fases, alarmas, EEPROM |
| [architecture.md](../firmware/avr/doc/architecture.md) | Capas y super-loop |
| [temporizacion_no_bloqueante.md](../firmware/avr/doc/temporizacion_no_bloqueante.md) | Reloj `avr_delay` · delays sin bloquear HotPanel |
| [st7920_pantalla.md](../firmware/avr/doc/st7920_pantalla.md) | Bitmaps, diffs y animaciones LCD (HotPanel) |
| [usb-automation.md](../firmware/avr/doc/usb-automation.md) | Contrato AT / `$HP` |
| [ui_style_guide.md](../firmware/avr/doc/ui_style_guide.md) | LCD 128×64 · layout aprobado |
| [atmega16_pin_definition_hotplate.md](../firmware/avr/doc/atmega16_pin_definition_hotplate.md) | Pines MCU |

## HotPlate Studio

| Doc | Descripción |
|-----|-------------|
| [../host-ui/ARCHITECTURE.md](../host-ui/ARCHITECTURE.md) | Módulos de HotPlate Studio (`host-ui/`) |

## Hardware / mecánica

| Ruta | Descripción |
|------|-------------|
| [../hardware/README.md](../hardware/README.md) | PCB + datasheets |
| [../mechanical/README.md](../mechanical/README.md) | Modelos 3D |
