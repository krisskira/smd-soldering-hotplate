# HotPlate Studio — estructura

Arranque: `python host-ui/app.py`

| Módulo | Responsabilidad |
|--------|-----------------|
| `app.py` | Entry point |
| `window.py` | `MainWindow`: notebook + cableado |
| `controller.py` | Serie, comandos AT, poll RX, sondeo STAT |
| `state.py` | Sesión / telemetría (sin widgets) |
| `protocol.py` | Constructores AT + parse de tramas. El retraso de HEAT viaja en segundos (0…43200) y la UI lo muestra como reloj `hh:mm` |
| `serial_link.py` | Hilo lector + una orden en vuelo hasta `OK`/`ERROR`. `$HP` no cierra el comando. Baud 9600 hoy; el stream de sesión (19200, un `$HP` a 1 Hz) está en `firmware/avr/doc/usb-automation.md` y aún no está en este enlace |
| `heat_logic.py` | Objetivo HEAT (plan vs vivo) |
| `ramps_store.py` | Caché `ramps.json` |
| `tune_store.py` | Caché `tune_params.json` (autotune / CFG=T) |
| `chart.py` | Matplotlib embebido + consola cronológica de fases/eventos. Los marcadores quedan en la curva sin textos superpuestos; el autoescalado conserva el origen 0 y el zoom manual se respeta hasta “Restablecer zoom” |
| `constants.py` | Intervalos, LED, paths |
| `views/` | Construcción de cada pestaña |

Flujo: **vista** dispara acción → **controller** habla con el device → RX actualiza **state** + métodos `apply_*` de las vistas.
