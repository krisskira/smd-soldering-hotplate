# HotPlate Studio

Studio es la aplicación de escritorio, en Python, con la que el computador maneja el HotPlate. Se abre con `python app.py` dentro de `hotplate-studio/`. En macOS, `./build.sh` deja un ejecutable. Mientras Studio tiene el mando, HotPanel muestra USB y el encoder no cambia nada.

## Cómo está escrita

La ventana solo dibuja. Un botón no habla con el puerto: pide una acción al controlador, y el controlador manda una orden AT por la UART a 19200 8N1. Hay una sola orden en vuelo. Hasta que llega `OK` o `ERROR`, no sale la siguiente. Una trama `$HP` que aparezca en medio no cuenta como esa respuesta.

Al conectar, la app envía `AT` y toma `OK` como «en línea». El saludo `HP` del equipo solo sale al encender, así que abrir el puerto no lo vuelve a ver. Pasar a modo USB es `AT+MODE=1`. Volver a manual es `AT+MODE=0`, el botón EXIT del panel o un reinicio del equipo.

En manual, Studio puede preguntar el estado cada cierto tiempo. En USB no hace falta: el equipo manda solo una trama `$HP` cada segundo, con temperatura, consigna, fase, escalón, potencia y salidas. Al entrar en USB lee el perfil (`$R`) y los ajustes (`$CF`).

Cinco páginas comparten esa sesión: Conexión, HEAT, Autotune, Ajustes y Apariencia. HEAT y Autotune usan el mismo panel de estado y la misma curva. La apariencia (fuentes y colores) se queda en el computador; no se envía al equipo. Las cinco páginas siguen montadas aunque solo se vea una, para que la curva no se congele al cambiar de pestaña.

## Qué guarda y dónde

El perfil que el equipo ejecuta vive en su EEPROM. Studio, además, guarda tres archivos junto al programa: `ramps.json` (el perfil editado en HEAT), `tune_params.json` (los parámetros del autoajuste) y `ui_theme.json` (solo la apariencia local). Guardar rampas envía el perfil al equipo. Leer rampas lo trae de vuelta.

En HEAT se arman hasta cuatro escalones, se lanza o se detiene el ciclo, y se ve la curva: temperatura medida, consigna, potencia y los cambios de fase. El registro se exporta a CSV. Esa curva es la misma historia que HotPanel resume en una línea.

## Material de esta pieza

- Vídeo: `videos/04-hotplate-studio.mp4` y `videos/04-hotplate-studio.srt`
- Capturas: `referencias/04-studio/`
- Arquitectura de la app: `hotplate-studio/ARCHITECTURE.md`
- Protocolo: `firmware/avr/doc/usb-automation.md`
