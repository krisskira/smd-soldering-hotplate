#!/usr/bin/env python3
"""Captura HotPlate Studio real junto a las pantallas de Stitch para compararlas.

Arranca la app con cachés temporales (no toca ramps.json, tune_params.json ni
ui_theme.json del usuario), inyecta tramas del protocolo como si llegaran por
el puerto serie y guarda, por pantalla:

    <out>/ours_<nombre>.png   captura de la página completa (1280 px)
    <out>/cmp_<nombre>.png    captura | referencia de Stitch (reescalada a 1×)

    python hotplate-studio/design/tools/compare_stitch.py [--out /tmp/hpcmp] [nombre ...]
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path

from PIL import Image, ImageGrab

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent
APP = DESIGN.parent
STITCH = DESIGN / "stitch"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(HERE))

TMP = Path(tempfile.mkdtemp(prefix="hp-compare-"))

import constants  # noqa: E402

constants.RAMPS_CACHE = TMP / "ramps.json"
constants.TUNE_CACHE = TMP / "tune_params.json"
import ramps_store  # noqa: E402
import theme  # noqa: E402
import tune_store  # noqa: E402

ramps_store.RAMPS_CACHE = constants.RAMPS_CACHE
tune_store.TUNE_CACHE = constants.TUNE_CACHE
theme.THEME_CACHE = TMP / "ui_theme.json"

import demo_data as sim  # noqa: E402
import protocol as proto  # noqa: E402
import serial_link  # noqa: E402
from serial_link import RxEvent  # noqa: E402
from widgets import ui  # noqa: E402
from window import MainWindow  # noqa: E402

PORT = "/dev/cu.usbserial-A10K"
WIDTH = 1280
PAGE = {"conexion": 0, "heat": 1, "autotune": 2, "ajustes": 3,
        "apariencia-fuentes": 4, "apariencia-graficas": 4, "apariencia-consola": 4}

serial_link.SerialLink.connected = property(lambda _self: True)  # type: ignore[assignment]


def rx(win: MainWindow, line: str) -> None:
    win.ctrl._handle_ev(RxEvent(kind="line", parsed=proto.parse_line(line), raw=line))


def hp_line(hp: dict) -> str:
    keys = ("T", "P", "A", "SET", "DLY", "RUN", "EL", "DU", "F", "RI", "FL", "TL")
    vals = dict(hp, DLY=hp.get("DLY", 0))
    if vals["T"] is None:
        vals["T"] = "---"
    extra = [f"{k}={hp[k]}" for k in ("AP", "AC", "AK", "AI") if k in hp]
    return "$HP," + ",".join([f"{k}={vals[k]}" for k in keys] + extra)


def go_online(win: MainWindow) -> None:
    st = win.state
    st.device_online, st.usb_mode, st.conn_port = True, True, PORT
    conn = win.ctrl.conn
    conn.port_cb.set_values([PORT])
    conn.port_var.set(PORT)
    conn.log_line("--", "puerto abierto — el saludo HP solo sale al encender; preguntando con AT…")
    conn.log_line("TX", "AT")
    rx(win, "OK")
    conn.log_line("--", "equipo en marcha (AT → OK)")
    conn.log_line("TX", "AT+MODE=1")
    rx(win, "OK")
    conn.log_line("TX", "AT+CFG?")
    rx(win, "$CF,MN=50,MX=210,KP=246,KI=10,BN=4,BX=6,DLY=0,AIR=1,AMS=2000")
    rx(win, "OK")
    conn.log_line("TX", "AT+CFG=R?")
    rx(win, "$R,N=4,0=150/120,1=165/1,2=170/1,3=190/90")
    rx(win, "OK")
    win.ctrl.refresh_chrome()


def _load_heat(win: MainWindow, rows, hp: dict, *, running: bool) -> None:
    st = win.state
    st.clear_samples()
    for row in rows:
        st.append_sample(*row)
    heat = win.ctrl.heat
    heat.set_banner("")
    heat.set_heat_running(running)
    rx(win, hp_line(hp))
    heat.chart.redraw(st.trace, None, y_max=heat.ramp_ymax())


def demo_heat(win: MainWindow) -> None:
    rows, hps = sim.sim_heat(sim.PROFILE)
    cut = next(i for i, h in enumerate(hps) if h["A"] == 4 and h["RI"] == 3) + 40
    _load_heat(win, rows[:cut], hps[cut - 1], running=True)


def demo_heat_done(win: MainWindow) -> None:
    rows, hps = sim.sim_heat(sim.PROFILE)
    _load_heat(win, rows, dict(hps[-1], F=0), running=False)
    rx(win, "ALARM:2")


def demo_heat_fault(win: MainWindow) -> None:
    rows, hps = sim.sim_heat(sim.PROFILE)
    cut = next(i for i, h in enumerate(hps) if h["A"] == 5 and h["RI"] == 1) + 25
    fault = dict(hps[cut - 1], A=9, T=None, DU=0, FL=1, RUN=0)
    _load_heat(win, rows[:cut], fault, running=False)


def demo_tune(win: MainWindow) -> None:
    rows, cycles = sim.sim_tune()
    tune = win.ctrl.tune
    tune.history.clear()
    tune.history.extend(rows)
    last = rows[-1]
    rx(win, hp_line({
        "T": last[1], "P": 2, "A": 10, "SET": 150, "RUN": 0, "EL": int(last[0]), "DU": 0,
        "F": 0, "RI": 0, "FL": 0, "TL": 0, "AP": 2, "AC": cycles, "AK": 246, "AI": 10,
    }))
    tune.chart.redraw(tune.history, tune.hyst_band(150.0), y_max=tune.target_ymax())


def find_scroll(widget):
    if isinstance(widget, ui.ScrollPage) and widget.winfo_ismapped():
        return widget
    for child in widget.winfo_children():
        hit = find_scroll(child)
        if hit is not None:
            return hit
    return None


def settle(win: MainWindow, delay: float = 0.25) -> None:
    end = time.time() + delay
    while time.time() < end:
        win.update()
        time.sleep(0.02)


def _client(win: MainWindow) -> Image.Image:
    """Área cliente de la ventana (sin barra de título), también fuera de pantalla."""
    if sys.platform == "darwin":
        import macwin

        shots = [im for im in map(macwin.grab_window, macwin.own_window_ids()) if im]
        if shots:
            im = max(shots, key=lambda i: i.width * i.height)
            w, h = win.winfo_width(), win.winfo_height()
            return im.crop((0, im.height - h, w, im.height))
    x, y = win.winfo_rootx(), win.winfo_rooty()
    return ImageGrab.grab(bbox=(x, y, x + win.winfo_width(), y + win.winfo_height()))


def grab(widget) -> Image.Image:
    win = widget.winfo_toplevel()
    full = _client(win)
    if widget is win:
        return full
    x = widget.winfo_rootx() - win.winfo_rootx()
    y = widget.winfo_rooty() - win.winfo_rooty()
    return full.crop((x, y, x + widget.winfo_width(), y + widget.winfo_height()))


def capture(win: MainWindow) -> Image.Image:
    """Cabecera + página completa (uniendo tramos de scroll) + barra de estado."""
    settle(win)
    page = win.pages[win._current]
    scroll = find_scroll(page)
    if scroll is None:
        return grab(win)
    canvas = scroll._canvas
    total = max(scroll.inner.winfo_reqheight(), canvas.winfo_height())
    view_h = canvas.winfo_height()
    content = Image.new("RGB", (canvas.winfo_width(), total), ui.BG)
    offset = 0
    while True:
        canvas.yview_moveto(offset / total)
        settle(win, 0.15)
        top = int(canvas.canvasy(0))
        content.paste(grab(canvas), (0, top))
        if top + view_h >= total:
            break
        offset = top + view_h
    canvas.yview_moveto(0)
    # La barra flotante cae en el margen derecho (solo fondo) y no es parte de la página.
    x0 = content.width - 12
    for y in range(total):
        content.paste(content.getpixel((x0 - 1, y)), (x0, y, content.width, y + 1))
    full = grab(win)
    head_h = canvas.winfo_rooty() - win.winfo_rooty()
    foot_h = full.height - head_h - view_h
    out = Image.new("RGB", (full.width, head_h + total + foot_h), ui.BG)
    out.paste(full.crop((0, 0, full.width, head_h)), (0, 0))
    out.paste(content, (0, head_h))
    out.paste(full.crop((0, full.height - foot_h, full.width, full.height)), (0, head_h + total))
    return out


def side_by_side(ours: Image.Image, ref: Image.Image) -> Image.Image:
    h = max(ours.height, ref.height)
    out = Image.new("RGB", (ours.width + ref.width + 12, h), "#ff00ff")
    out.paste(ours, (0, 0))
    out.paste(ref, (ours.width + 12, 0))
    return out


def reference(name: str) -> Image.Image:
    im = Image.open(STITCH / f"{name}.png").convert("RGB")
    return im.resize((im.width // 2, im.height // 2), Image.LANCZOS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/hpcmp")
    ap.add_argument("--height", type=int, default=980)
    ap.add_argument("--width", type=int, default=WIDTH)
    ap.add_argument("--tag", default="", help="sufijo para no pisar capturas anteriores")
    ap.add_argument("names", nargs="*", default=list(PAGE))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    win = MainWindow(maximized=False)
    win.geometry(f"{args.width}x{args.height}+40+40")
    win.attributes("-topmost", True)
    win.lift()
    settle(win, 0.6)
    win.focus_force()
    settle(win, 1.0)
    go_online(win)
    for name in args.names:
        (demo_tune if name == "autotune" else demo_heat)(win)
        win.select_page(PAGE[name])
        if name.startswith("apariencia-"):
            tab = {"fuentes": "Fuentes", "graficas": "Gráficas", "consola": "Consola serie"}
            win.ctrl.appearance.select_tab(tab[name.split("-", 1)[1]])
        ours = capture(win)
        tag = f"_{args.tag}" if args.tag else ""
        ours.save(out / f"ours_{name}{tag}.png")
        side_by_side(ours, reference(name)).save(out / f"cmp_{name}{tag}.png")
        print(out / f"cmp_{name}{tag}.png", ours.size)
    win.destroy()


if __name__ == "__main__":
    main()
