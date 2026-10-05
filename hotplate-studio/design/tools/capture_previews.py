#!/usr/bin/env python3
"""Regenera design/previews/ con capturas de HotPlate Studio real.

Usa la misma preparación que compare_stitch.py: cachés temporales, equipo
en línea en modo USB y tramas de demostración. Cada PNG es la página
completa a 1280 px de ancho (cabecera + contenido + barra de estado).

    python hotplate-studio/design/tools/capture_previews.py [nombre ...]
"""

from __future__ import annotations

import argparse

import compare_stitch as cs

SHOTS = {
    "01_conexion": ("conexion", cs.demo_heat),
    "02_heat_en_curso": ("heat", cs.demo_heat),
    "03_heat_terminado": ("heat", cs.demo_heat_done),
    "04_heat_falla": ("heat", cs.demo_heat_fault),
    "05_autotune_listo": ("autotune", cs.demo_tune),
    "06_ajustes": ("ajustes", cs.demo_heat),
    "07_apariencia": ("apariencia-fuentes", cs.demo_heat),
}
OUT = cs.DESIGN / "previews"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--height", type=int, default=980)
    ap.add_argument("names", nargs="*", default=list(SHOTS))
    args = ap.parse_args()

    win = cs.MainWindow(maximized=False)
    win.geometry(f"{cs.WIDTH}x{args.height}+40+40")
    win.attributes("-topmost", True)
    win.lift()
    cs.settle(win, 0.6)
    win.focus_force()
    cs.settle(win, 1.0)
    cs.go_online(win)
    for name in args.names:
        page, demo = SHOTS[name]
        demo(win)
        win.select_page(cs.PAGE[page])
        if page.startswith("apariencia-"):
            win.ctrl.appearance.select_tab("Fuentes")
        shot = cs.capture(win)
        shot.save(OUT / f"{name}.png", optimize=True)
        print(OUT / f"{name}.png", shot.size)
    win.destroy()


if __name__ == "__main__":
    main()
