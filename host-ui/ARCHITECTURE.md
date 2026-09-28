# Host UI — scaffolding

Arranque: `python host-ui/app.py`

| Módulo | Responsabilidad |
|--------|-----------------|
| `app.py` | Entry point |
| `window.py` | `MainWindow`: notebook + cableado |
| `controller.py` | Serie, comandos AT, poll RX, sondeo STAT |
| `state.py` | Sesión / telemetría (sin widgets) |
| `protocol.py` | Constructores AT + parse de tramas |
| `serial_link.py` | Hilo lector + cola OK/ERROR |
| `heat_logic.py` | Objetivo HEAT (plan vs vivo) |
| `ramps_store.py` | Caché `ramps.json` |
| `tune_store.py` | Caché `tune_params.json` (autotune / CFG=T) |
| `chart.py` | Matplotlib embebido |
| `constants.py` | Intervalos, LED, paths |
| `views/` | Construcción de cada pestaña |

Flujo: **vista** dispara acción → **controller** habla con el device → RX actualiza **state** + métodos `apply_*` de las vistas.
