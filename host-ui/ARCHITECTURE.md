# HotPlate Studio — estructura

Arranque: `python host-ui/app.py`

| Módulo | Responsabilidad |
|--------|-----------------|
| `app.py` | Entry point |
| `window.py` | `MainWindow`: notebook + cableado |
| `controller.py` | Serie, comandos AT, poll RX. Al conectar manda `AT` (el saludo `HP` solo sale al encender). Sondeo `STAT?` solo en Manual: en USB el equipo empuja `$HP` a 1 Hz. `ERROR:8` o el saludo `HP` devuelven a Manual |
| `state.py` | Sesión / telemetría (sin widgets) |
| `protocol.py` | Constructores AT + parse de tramas. El retraso de HEAT viaja en segundos (0…43200) y la UI lo muestra como reloj `hh:mm` |
| `serial_link.py` | 19200 8N1. Hilo lector + una orden en vuelo hasta `OK`/`ERROR`. `$HP` no cierra el comando |
| `heat_logic.py` | Objetivo HEAT (plan vs vivo) |
| `ramps_store.py` | Caché `ramps.json` |
| `tune_store.py` | Caché `tune_params.json` (autotune / CFG=T) |
| `chart.py` | Misma curva en HEAT y Autotune: origen en 0, marcadores sin texto encima, registro de eventos exportable. HEAT abre el eje X según el perfil y lo deja crecer; Autotune lo fija al timeout. El zoom manual se respeta hasta “Restablecer zoom” |
| `views/status_panel.py` | Estado `$HP` compartido por HEAT y Autotune |
| `views/layout.py` | Filas de paneles: ancho al contenido, misma altura |
| `constants.py` | Intervalos, LED, paths |
| `views/` | Construcción de cada pestaña |

Flujo: **vista** dispara acción → **controller** habla con el device → RX actualiza **state** + métodos `apply_*` de las vistas.
