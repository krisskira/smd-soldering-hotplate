# Pantallas

Diseño vigente de HotPlate Studio, exportado del proyecto Stitch
[HotPlate Studio Desktop UI](https://stitch.withgoogle.com/projects/9967566109376928826).

El PNG es la referencia de cómo se ve, a 2560 px de ancho: en pantalla se mira a la mitad. El HTML trae la jerarquía, los textos y los colores. El contexto de uso está en [el README de esta carpeta](../README.md).

| Archivos | Pantalla | Código |
|----------|----------|--------|
| `conexion.png` / `.html` | Puerto, sesión, sondeo y consola | `hotplate-studio/views/connection_view.py` |
| `heat.png` / `.html` | HEAT en curso, meseta de la rampa 4 | `hotplate-studio/views/heat_view.py`, `status_panel.py`, `chart.py` |
| `autotune.png` / `.html` | Autoajuste terminado, 5 de 5 ciclos | `hotplate-studio/views/tune_view.py` |
| `ajustes.png` / `.html` | Límites, bandas, arranque y ganancias | `hotplate-studio/views/settings_view.py` |
| `apariencia-fuentes.png` / `.html` | Apariencia · Fuentes | `hotplate-studio/views/appearance_view.py` |
| `apariencia-graficas.png` / `.html` | Apariencia · Gráficas | el mismo |
| `apariencia-consola.png` / `.html` | Apariencia · Consola serie | el mismo |

`previews/`, en la carpeta de arriba, son capturas de la app real ya construida con estas pantallas. Si una captura y un PNG de aquí no coinciden, manda el PNG.
