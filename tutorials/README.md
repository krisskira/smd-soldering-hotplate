# Tutoriales de HotPlate

Paquete para la sección de tutoriales de kriver-device. Cubre el hardware, el firmware y HotPlate Studio con el material real del proyecto: fotos del equipo, el fresado de la PCB, el modelo 3D, las pantallas de la LCD y las capturas de Studio.

Cada video es MP4, 1920×1080, sin voz. La narración va en subtítulos quemados y, además, en un `.srt` al lado del archivo para poder ofrecerlos como pista aparte.

| Pieza | Vídeo | De qué habla |
|---|---|---|
| Promo | `videos/promo.mp4` | El producto de punta a punta, en un minuto |
| 01 | `videos/01-pcb.mp4` | Fresado de la PCB en cobre |
| 02 | `videos/02-modelado-3d.mp4` | Carcasa en Fusion 360 e impresión |
| 03 | `videos/03-firmware.mp4` | Firmware y estados de HotPanel |
| 04 | `videos/04-hotplate-studio.mp4` | Cómo está hecha la aplicación |
| 05 | `videos/05-calibracion.mp4` | Límites, bandas, autoajuste y un ciclo de prueba |

El texto largo de cada pieza está en su carpeta (`01-pcb/tutorial.md`, etc.). Las imágenes de apoyo están en `referencias/`. El índice para montar la sección está en `manifest.json`.

La música es CC0 y está copiada en `audio/`. Créditos en `CREDITOS.md`.

Para regenerar los vídeos (hace falta el material de `~/Downloads/fotos-hotplate` y ffmpeg):

```bash
python3 tutorials/build_videos.py
```
