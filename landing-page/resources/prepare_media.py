#!/usr/bin/env python3
"""Copia y optimiza en public/media/ las imágenes del repo que usa la landing.

    ../.venv/bin/python resources/prepare_media.py

Las fuentes siguen en su sitio (docs/, firmware/, hotplate-studio-design/):
si se regeneran allí, basta con volver a correr este script.
"""

from pathlib import Path
import shutil

from PIL import Image

LANDING = Path(__file__).resolve().parents[1]
REPO = LANDING.parent
OUT = LANDING / "public/media"

HOTPANEL = REPO / "firmware/avr/doc/img/hotpanel"
STUDIO = REPO / "hotplate-studio-design/previews"

# Capturas de HotPanel: pixel art, se copian en PNG sin tocar.
COPY = {
    "hotpanel-idle.png": HOTPANEL / "01_heat_idle.png",
    "hotpanel-wait.png": HOTPANEL / "03_heat_wait.png",
    "hotpanel-ramp.png": HOTPANEL / "04_heat_ramp.png",
    "hotpanel-hold.png": HOTPANEL / "05_heat_hold.png",
    "hotpanel-alarm.png": HOTPANEL / "07_heat_alarm.png",
    "hotpanel-usb.png": HOTPANEL / "10_usb.png",
    "hotpanel-settings.png": HOTPANEL / "13_settings_edit_temp.png",
    "hotpanel-delay.png": HOTPANEL / "17_settings_edit_dly_hours.png",
}

# Capturas de escritorio y gráficas: WebP.
WEBP = {
    "studio-heat.webp": STUDIO / "02_heat_en_curso.png",
    "studio-autotune.webp": STUDIO / "05_autotune_listo.png",
    "studio-settings.webp": STUDIO / "06_ajustes.png",
    "studio-connection.webp": STUDIO / "01_conexion.png",
    "trace-heat-4.webp": REPO / "docs/heat-results/hotplate-chart-heat-trace-4.png",
    "trace-latest.webp": REPO / "firmware/avr/doc/ultimo-heat/char-1.png",
}


def og_cover() -> None:
    poster = OUT / "hotplate-demo-poster.jpg"
    if not poster.exists():
        print("falta hotplate-demo-poster.jpg: corre resources/demo-video/build.sh")
        return
    img = Image.open(poster).convert("RGB")
    w, h = img.size
    crop_h = round(w * 630 / 1200)
    top = (h - crop_h) // 2
    img.crop((0, top, w, top + crop_h)).resize((1200, 630), Image.LANCZOS).save(OUT / "og-cover.jpg", quality=86)
    print(OUT / "og-cover.jpg")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, src in COPY.items():
        shutil.copyfile(src, OUT / name)
        print(OUT / name)
    for name, src in WEBP.items():
        Image.open(src).convert("RGB").save(OUT / name, "WEBP", quality=86, method=6)
        print(OUT / name)
    og_cover()


if __name__ == "__main__":
    main()
