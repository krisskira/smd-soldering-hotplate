# HotPlate Studio

Aplicación de escritorio que controla el HotPlate por USB. Mientras tiene el mando, el panel del equipo muestra **USB** y la perilla no actúa. Los dos modos no se usan a la vez.

## Arrancar

```bash
cd hotplate-studio
pip install -r requirements.txt
python app.py
```

La ventana se abre maximizada. Si se reduce, no baja de 1100×760.

En macOS también se puede compilar a un ejecutable:

```bash
./build.sh
./dist/HotPlateStudio
```

`./build.sh --help` lista las variantes (rápida, con consola, o como `.app`).

## Qué queda guardado en el disco

Estos tres archivos viven junto al programa. Si se usa el ejecutable, viven junto a él:

| Archivo | Qué guarda |
|---------|------------|
| `ramps.json` | El perfil de soldadura editado en HEAT |
| `tune_params.json` | Los parámetros del autoajuste |
| `ui_theme.json` | La apariencia. Solo afecta a este equipo; no se envía al HotPlate |

## Dónde seguir

- Cómo está armada la app: [ARCHITECTURE.md](ARCHITECTURE.md)
- Cómo se ven las pantallas: [design/README.md](design/README.md)
- Qué se dice por el cable: [usb-automation.md](../firmware/avr/doc/usb-automation.md)
- El orden del ciclo de soldadura: [program_flows.md](../firmware/avr/doc/program_flows.md)
