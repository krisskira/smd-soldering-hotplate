# Vistas Stitch (diseño nuevo)

Capturas y HTML de las pantallas corregidas en el proyecto Stitch
[HotPlate Studio Desktop UI](https://stitch.withgoogle.com/projects/9967566109376928826).
Los `previews/*.png` de la carpeta padre son la app tal como está hoy: no se tocan, sirven para comparar.

| Archivo | Qué es | Para implementar | Comparar con |
|---------|--------|------------------|--------------|
| `heat.png` / `.html` | HEAT en curso, meseta de la rampa 4 | `host-ui/views/heat_view.py`, `status_panel.py`, `chart.py` | `previews/02_heat_en_curso.png` |
| `conexion.png` / `.html` | Puerto, sesión, sondeo y consola | `host-ui/views/connection_view.py` | `previews/01_conexion.png` |
| `ajustes.png` / `.html` | Límites, bandas, arranque y ganancias PI | `host-ui/views/settings_view.py` | `previews/06_ajustes.png` |
| `autotune.png` / `.html` | Autoajuste listo, 5/5 ciclos | `host-ui/views/tune_view.py` | `previews/05_autotune_listo.png` |
| `apariencia-fuentes.png` / `.html` | Subpestaña Fuentes | `host-ui/views/appearance_view.py` | `previews/07_apariencia.png` |
| `apariencia-graficas.png` / `.html` | Subpestaña Gráficas | ídem | ídem |
| `apariencia-consola.png` / `.html` | Subpestaña Consola serie | ídem | ídem |

El PNG es la referencia visual a 2560 px de ancho. El HTML es el layout de Stitch (clases e inline): de ahí salen jerarquía, textos y colores al pasarlo a Tk.
