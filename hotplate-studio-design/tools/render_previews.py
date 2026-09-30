#!/usr/bin/env python3
"""Vistas simuladas de HotPlate Studio (maquetas PNG) a partir de host-ui.

Reutiliza de host-ui: textos de fases (protocol), filas del estado
(views.status_panel), colores (theme) y la detección de eventos de la
curva (chart). Los datos de proceso salen de un modelo térmico sencillo,
no de un equipo real.

    python hotplate-studio-design/tools/render_previews.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent
ROOT = DESIGN.parent
sys.path.insert(0, str(ROOT / "host-ui"))

import chart as hp_chart  # noqa: E402
import protocol as proto  # noqa: E402
from theme import DEFAULT_THEME, SURFACE  # noqa: E402
from views.status_panel import STATUS_COLUMNS  # noqa: E402

OUT = DESIGN / "previews"
W, H = 1280, 900
DPI = 100

BODY = DEFAULT_THEME["body_color"]
MUTED = DEFAULT_THEME["frame_title_color"]
KEY = DEFAULT_THEME["status_key_color"]
VAL = DEFAULT_THEME["status_value_color"]
BORDER = "#c5d0dc"
BTN = "#e7eef4"
ACCENT = "#1a5276"
TAB = "#e4eaef"
WINDOW = "#e9ebee"
CC = {k[6:]: v for k, v in DEFAULT_THEME.items() if k.startswith("chart_")}

PORT = "/dev/cu.usbserial-A10K"
TABS = ("Conexión", "HEAT", "Autotune", "Ajustes", "Apariencia")

plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]


# --------------------------------------------------------------------------
# Lienzo de maqueta en píxeles (origen arriba a la izquierda)
# --------------------------------------------------------------------------


class Mock:
    def __init__(self, tab: str, *, online: bool = True, usb: bool = True) -> None:
        self.fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.axis("off")
        self._chrome(tab, online, usb)

    @staticmethod
    def tw(s: str, size: float = 9) -> float:
        return len(s) * size * 0.72

    def rect(self, x, y, w, h, fc, ec=None, lw=1.0, z=1) -> None:
        self.ax.add_patch(
            Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec or fc, linewidth=lw, zorder=z)
        )

    def text(self, x, y, s, size=9, color=BODY, weight="normal", ha="left",
             va="center", family=None, z=6) -> None:
        kw = {"fontfamily": family} if family else {}
        self.ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                     ha=ha, va=va, zorder=z, **kw)

    def button(self, x, y, label, *, w=None, accent=False, h=26, disabled=False) -> float:
        w = w or self.tw(label) + 26
        if accent:
            fc = "#b7c3ce" if disabled else ACCENT
            self.rect(x, y, w, h, fc, z=3)
            self.text(x + w / 2, y + h / 2, label, color="#ffffff", ha="center")
        else:
            self.rect(x, y, w, h, BTN, "#b8c4cf", z=3)
            self.text(x + w / 2, y + h / 2, label, ha="center",
                      color=("#a0aab4" if disabled else BODY))
        return w

    def entry(self, x, y, w, value, *, h=22, align="right") -> None:
        self.rect(x, y, w, h, "#ffffff", "#9aa8b5", z=3)
        if align == "right":
            self.text(x + w - 5, y + h / 2, value, ha="right")
        else:
            self.text(x + 5, y + h / 2, value)

    def combo(self, x, y, w, value, *, h=22, disabled=False) -> None:
        self.rect(x, y, w, h, "#eef1f4" if disabled else "#ffffff", "#9aa8b5", z=3)
        self.text(x + 5, y + h / 2, value, color=("#8795a1" if disabled else BODY))
        self.text(x + w - 10, y + h / 2, "▾", ha="center", color=MUTED)

    def spin(self, x, y, w, value, *, h=22) -> None:
        self.rect(x, y, w, h, "#ffffff", "#9aa8b5", z=3)
        self.text(x + w - 18, y + h / 2, value, ha="right")
        self.text(x + w - 8, y + h / 2 - 4, "▴", ha="center", size=6, color=MUTED)
        self.text(x + w - 8, y + h / 2 + 4, "▾", ha="center", size=6, color=MUTED)

    def check(self, x, y, on, *, disabled=False) -> None:
        self.rect(x, y, 14, 14, "#eef1f4" if disabled else "#ffffff", "#8795a1", z=3)
        if on:
            self.text(x + 7, y + 7, "✓", ha="center", size=9,
                      color=("#8795a1" if disabled else ACCENT), weight="bold")

    def frame(self, x, y, w, h, title) -> None:
        self.rect(x, y + 8, w, h - 8, SURFACE, BORDER, z=2)
        tw = self.tw(title, 9.5) + 8
        self.rect(x + 8, y + 2, tw, 12, SURFACE, z=2.5)
        self.text(x + 12, y + 8, title, size=9.5, weight="bold", color=MUTED)

    def sep(self, x, y, w) -> None:
        self.ax.plot([x, x + w], [y, y], color="#d5dde5", linewidth=1, zorder=3)

    def swatch(self, x, y, color) -> None:
        self.rect(x, y, 22, 16, color, "#8795a1", z=3)

    def _chrome(self, tab, online, usb) -> None:
        self.rect(0, 0, W, H, WINDOW, z=0)
        self.rect(0, 0, W, 28, "#dfe2e6", z=1)
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
            self.ax.add_patch(Circle((16 + 20 * i, 14), 6, color=c, zorder=2))
        self.text(W / 2, 14, "HotPlate Studio", weight="bold", ha="center", size=9.5)

        self.rect(6, 64, W - 12, H - 64 - 34, SURFACE, BORDER, z=1)
        x = 12
        for name in TABS:
            w = self.tw(name) + 34
            sel = name == tab
            self.rect(x, 34 if sel else 38, w, 30 if sel else 26,
                      "#ffffff" if sel else TAB, BORDER, z=2)
            self.text(x + w / 2, 50, name, ha="center",
                      color=(ACCENT if sel else BODY), weight=("bold" if sel else "normal"))
            x += w + 2

        y = H - 22
        if online:
            led, label = hp_led_green(), f"{PORT} @ 19200  ·  En línea  ·  Modo {'USB' if usb else 'Manual'}"
        else:
            led, label = "#c0392b", ""
        self.ax.add_patch(Circle((20, y), 5, color=led, zorder=3))
        self.text(34, y, label)

    def save(self, name: str) -> Path:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / name
        self.fig.savefig(path, dpi=150)
        plt.close(self.fig)
        return path


def hp_led_green() -> str:
    from constants import LED_GREEN

    return LED_GREEN


# --------------------------------------------------------------------------
# Modelo térmico (placa PTC + PT100 con retardo) para curvas creíbles
# --------------------------------------------------------------------------

T_AMB = 28.0
GAIN = 3.2  # °C por % de potencia en régimen
TAU = 700.0
DEAD_S = 32


class Plate:
    def __init__(self, t0: float = T_AMB) -> None:
        self.t = t0
        self.hist = [0.0] * DEAD_S

    def step(self, duty: float, fan: bool) -> float:
        self.hist.append(duty)
        u = self.hist.pop(0)
        loss = (self.t - T_AMB) * (2.2 if fan else 1.0)
        self.t += (GAIN * u - loss) / TAU
        return round(self.t, 1)


def sim_heat(ramps: list[tuple[int, int]], *, band: int = 4, t_min: int = 50,
             alarm_s: int = 60, stop_at: float | None = None):
    """Filas (t, T, SET_plot, DU, fase) + snapshots $HP por segundo."""
    plate = Plate()
    rows, hp = [], []
    ri, phase, hold_left = 0, 5, 0
    t = 0
    alarm_left = alarm_s
    tl = 0
    while True:
        set_c = ramps[ri][0] if phase in (4, 5) else 0
        temp = plate.t
        if phase in (4, 5):
            slope = (plate.t - (rows[-5][1] if len(rows) >= 5 else plate.t)) / 5.0
            pred = temp + slope * 30.0
            ff = (set_c - T_AMB) / GAIN
            duty = max(0.0, min(100.0, ff + 5.0 * (set_c - pred)))
        else:
            duty = 0.0
        fan = phase in (6, 7)
        duty = float(int(duty))
        temp = plate.step(duty, fan)
        if temp >= 183:
            tl += 1

        if phase == 5 and abs(temp - set_c) <= band:
            phase, hold_left = 4, ramps[ri][1]
        elif phase == 4:
            hold_left -= 1
            if hold_left <= 0:
                if ri + 1 < len(ramps):
                    ri, phase = ri + 1, 5
                else:
                    phase = 7
        elif phase == 7:
            alarm_left -= 1
            if alarm_left <= 0:
                phase = 6
        elif phase == 6 and temp <= t_min:
            phase = 8

        plot_set = float(set_c) if phase in (4, 5) else float("nan")
        rows.append((float(t), temp, plot_set, duty, proto.chart_phase_label(phase, ri)))
        hp.append({
            "T": temp, "P": 1, "A": phase, "SET": ramps[ri][0],
            "RUN": hold_left if phase == 4 else (alarm_left if phase == 7 else 0),
            "EL": t, "DU": int(duty), "F": int(fan), "RI": ri, "FL": 0, "TL": tl,
        })
        t += 1
        if phase == 8 or (stop_at is not None and t >= stop_at):
            break
    return rows, hp


def sim_tune(set_c: int = 150, hyst_x10: int = 15, cycles: int = 5):
    plate = Plate()
    h = hyst_x10 / 10.0
    rows = []
    heating, done_cycles, seen_high = True, 0, False
    t = 0
    while t < 2000:
        if heating and plate.t >= set_c + h:
            heating, seen_high = False, True
        elif not heating and plate.t <= set_c - h:
            heating = True
            if seen_high:
                done_cycles += 1
        duty = 100.0 if heating else 0.0
        temp = plate.step(duty, fan=not heating and seen_high)
        finished = done_cycles >= cycles
        rows.append((float(t), temp, float(set_c), 0.0 if finished else duty,
                     proto.chart_atune_label(2 if finished else 1)))
        t += 1
        if finished:
            break
    return rows, done_cycles


# --------------------------------------------------------------------------
# Bloques de vista
# --------------------------------------------------------------------------


def status_panel(m: Mock, x: float, y: float, w: float, h: float, vals: dict) -> None:
    m.frame(x, y, w, h, "Estado del proceso")
    col_x = (x + 14, x + 14 + 262)
    for ci, sections in enumerate(STATUS_COLUMNS):
        cy = y + 30
        cx = col_x[ci]
        for title, fields in sections:
            m.text(cx, cy, title, color=DEFAULT_THEME["section_title_color"])
            m.sep(cx, cy + 11, 230)
            cy += 22
            for key, label, _tip in fields:
                m.text(cx + 6, cy, label, color=KEY, size=8.8)
                m.text(cx + 140, cy, vals.get(key, "—"), color=VAL, size=8.8)
                cy += 19
            cy += 6


def hp_values(hp: dict | None, *, delay="00:00") -> dict:
    if not hp:
        return {"DLY": delay}
    a, p = hp["A"], hp["P"]
    t = hp.get("T")
    return {
        "PROG": proto.prog_name(p),
        "PHASE": proto.phase_name(a),
        "T": "—" if t is None else f"{t:.1f} °C",
        "SET": f"{hp['SET']} °C",
        "DLY": delay,
        "RUN": str(hp["RUN"]),
        "EL": str(hp["EL"]),
        "DU": str(hp["DU"]),
        "F": "Encendido" if hp["F"] else "Apagado",
        "RI": f"Rampa {hp['RI'] + 1}" if p == 1 and a in (4, 5) else "—",
        "FL": "Sí" if hp["FL"] else "No",
        "TL": f"{hp['TL']} s",
    }


def ramps_panel(m: Mock, x, y, w, h, ramps, active_idx: int | None) -> None:
    m.frame(x, y, w, h, "Soldering Profile")
    m.text(x + 12, y + 30, "Escalones contiguos desde la rampa 1. Guardar envía el perfil;",
           color=MUTED)
    m.text(x + 12, y + 46, "Leer pide $R.", color=MUTED)
    cols = (x + 16, x + 52, x + 150, x + 232, x + 316)
    for cx, title in zip(cols, ("Usar", "Escalón", "°C", "s", "")):
        m.text(cx, y + 70, title, color=MUTED)
    ry = y + 84
    for i, (on, temp, hold) in enumerate(ramps):
        m.check(cols[0] + 4, ry + 4, on, disabled=(i == 0))
        hi = active_idx == i
        m.text(cols[1], ry + 11, ("► Rampa " if hi else "Rampa ") + str(i + 1),
               weight=("bold" if hi else "normal"))
        m.entry(cols[2], ry, 70, str(temp))
        m.entry(cols[3], ry, 70, str(hold))
        m.button(cols[4], ry - 1, "Guardar", h=24)
        ry += 32
    bx = x + 12
    bx += m.button(bx, ry + 8, "Leer rampas") + 6
    m.button(bx, ry + 8, "Guardar rampas activas")


def chart_block(m: Mock, x, y, w, h, title, rows, *, y_max, x_span, locked,
                band=None, event_rows_max=17) -> None:
    m.frame(x, y, w, h, title)
    bx = x + w - 10
    for label in ("Limpiar", "Restablecer zoom", "Exportar muestras"):
        bw = m.tw(label) + 26
        bx -= bw
        m.button(bx, y + 18, label, w=bw)
        bx -= 6

    lx, ly, lw = x + 8, y + 50, w - 16
    m.frame(lx, ly, lw, 58, "Leyenda")
    items = (
        ("line", "temp", "Temperatura medida"), ("dashed", "set", "SET"),
        ("line", "duty", "Potencia"), ("peak", "mark_peak", "Cresta"),
        ("up", "mark_up", "Cruce ↑"), ("down", "mark_down", "Cruce ↓"),
        ("tick", "mark_on", "Calentador ON"), ("tick", "mark_off", "Calentador OFF"),
    )
    cw = lw / 4
    for i, (kind, key, label) in enumerate(items):
        cx = lx + 12 + (i % 4) * cw
        cy = ly + 28 + (i // 4) * 18
        col = CC[key]
        if kind in ("line", "dashed"):
            m.ax.plot([cx, cx + 24], [cy, cy], color=col, linewidth=2,
                      linestyle=("--" if kind == "dashed" else "-"), zorder=4)
        elif kind == "tick":
            m.ax.plot([cx + 12, cx + 12], [cy - 6, cy + 6], color=col, linewidth=3, zorder=4)
        else:
            mk = {"up": "^", "down": "v", "peak": "D"}[kind]
            m.ax.plot([cx + 12], [cy], marker=mk, color=col, markersize=7, zorder=4)
        m.text(cx + 30, cy, label)

    py = ly + 66
    ph = y + h - py - 8
    pw = (w - 16) * 0.62
    px = x + 8
    m.rect(px, py, pw, ph, "#ffffff", BORDER, z=2)
    _plot(m, (px + 56, py + 10, pw - 56 - 58, ph - 10 - 36 - 30), rows,
          y_max=y_max, x_span=x_span, locked=locked, band=band)
    m.rect(px + 1, py + ph - 28, pw - 2, 27, "#eef1f4", z=3)
    tx = px + 12
    for glyph in ("⌂", "←", "→", "✥", "◎", "⚙", "▣"):
        m.text(tx, py + ph - 14, glyph, size=11, color=MUTED)
        tx += 30
    m.text(px + pw - 12, py + ph - 14, "x=412  y=151.6", ha="right", size=8, color=MUTED)

    ex = px + pw + 8
    ew = x + w - 8 - ex
    m.frame(ex, py - 6, ew, ph + 6, "Registro de eventos")
    m.button(ex + ew - 130, py + 12, "Exportar registro", w=120, h=24)
    events = _events(rows)[-event_rows_max:]
    hy = py + 44
    m.rect(ex + 6, hy, ew - 12, 22, "#e8eef3", z=3)
    heads = ((ex + 58, "Tiempo", "right"), (ex + 112, "Dur.", "right"),
             (ex + 170, "T °C", "right"), (ex + 182, "Evento", "left"))
    for hx, label, ha in heads:
        m.text(hx, hy + 11, label, weight="bold", color=ACCENT, ha=ha)
    ry = hy + 22
    m.rect(ex + 6, ry, ew - 12, ph - (ry - py) - 6, "#ffffff", z=3)
    for tt, dur, temp, label, color in events:
        ry += 19
        if ry > py + ph - 12:
            break
        m.text(ex + 58, ry - 8, tt, ha="right", color=color, size=8.6)
        m.text(ex + 112, ry - 8, dur, ha="right", color=color, size=8.6)
        m.text(ex + 170, ry - 8, temp, ha="right", color=color, size=8.6)
        m.text(ex + 182, ry - 8, label, color=color, size=8.6)


def _events(rows):
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    sets = [r[2] for r in rows]
    dus = [r[3] for r in rows]
    phases = [r[4] for r in rows]
    fmt = hp_chart.LiveChart._fmt_time
    at = hp_chart.LiveChart._temp_at
    out = []
    for t0, t1, name in hp_chart._phase_spans(xs, phases):
        out.append((t0, t1 - t0, at(xs, ys, t0), f"Fase: {name}", hp_chart._phase_color(name)))
    for t, y, kind in hp_chart._crossings_t_set(xs, ys, sets):
        out.append((t, 0.0, y, f"Cruce {'↑' if kind == 'up' else '↓'} SET",
                    CC["mark_up" if kind == "up" else "mark_down"]))
    for t, kind in hp_chart._duty_edges(xs, dus):
        out.append((t, 0.0, at(xs, ys, t), f"Calentador {kind.upper()}",
                    CC["mark_on" if kind == "on" else "mark_off"]))
    for t, temp in hp_chart._crests(xs, ys):
        out.append((t, 0.0, temp, "Cresta", CC["mark_peak"]))
    out.sort(key=lambda r: (r[0], r[3]))
    return [
        (fmt(t), fmt(d) if d > 0 else "—", f"{temp:.1f}" if temp == temp else "—", label, col)
        for t, d, temp, label, col in out
    ]


def _plot(m: Mock, rect, rows, *, y_max, x_span, locked, band) -> None:
    x, y, w, h = rect
    ax = m.fig.add_axes([x / W, 1 - (y + h) / H, w / W, h / H])
    ax2 = ax.twinx()
    ax.set_facecolor(CC["face"])
    xs = [r[0] for r in rows]
    ys = [r[1] for r in rows]
    sets = [r[2] for r in rows]
    dus = [r[3] for r in rows]
    phases = [r[4] for r in rows]

    if locked:
        x_end = x_span
    else:
        x_end = x_span
        if xs and xs[-1] > x_span:
            step = max(hp_chart._x_major_step(x_span), 50.0)
            x_end = math.ceil(xs[-1] / step) * step
    finite = [v for v in ys + sets if v == v]
    top = max(y_max, math.ceil((max(finite, default=1.0) + 10.0) / 25.0) * 25.0)

    ax.set_xlim(0, x_end)
    ax.set_ylim(0, top)
    ax2.set_ylim(0, 110)
    ax.xaxis.set_major_locator(MultipleLocator(hp_chart._x_major_step(x_end)))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{int(round(v))}"))
    ax.grid(True, which="major", linestyle="-", linewidth=0.6, alpha=0.35)
    ax.minorticks_on()
    ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.2)
    ax.set_axisbelow(True)
    for a in (ax, ax2):
        a.tick_params(labelsize=7.5)
    ax.set_xlabel("Tiempo (s)", fontsize=8)
    ax.set_ylabel("Temperatura (°C)", fontsize=8)
    ax2.set_ylabel("Potencia calentador (%)", fontsize=8)

    if band:
        ax.axhspan(band[0], band[1], color=CC["band"], alpha=0.15)
    ax.plot(xs, ys, color=CC["temp"], linewidth=1.6, zorder=4)
    ax.plot(xs, sets, color=CC["set"], linestyle="--", linewidth=1.3, zorder=4)
    ax2.plot(xs, dus, color=CC["duty"], alpha=0.65, linewidth=1.0)

    for t, kind in hp_chart._duty_edges(xs, dus):
        col = CC["mark_on"] if kind == "on" else CC["mark_off"]
        ax.axvline(t, color=col, alpha=0.55, linewidth=1.0, zorder=2)
        ax.plot([t], [0.015 * top], marker="|", markersize=12, markeredgewidth=2,
                color=col, zorder=5)
    for t0, _t1, name in hp_chart._phase_spans(xs, phases):
        ax.axvline(t0, color=hp_chart._phase_color(name), linestyle="--",
                   linewidth=1.3, alpha=0.9, zorder=3)
    cr = hp_chart._crossings_t_set(xs, ys, sets)
    up = [(t, v) for t, v, k in cr if k == "up"]
    dn = [(t, v) for t, v, k in cr if k == "down"]
    if up:
        ax.scatter(*zip(*up), marker="^", s=42, c=CC["mark_up"], zorder=6)
    if dn:
        ax.scatter(*zip(*dn), marker="v", s=42, c=CC["mark_down"], zorder=6)
    crests = hp_chart._crests(xs, ys)
    if crests:
        ax.scatter(*zip(*crests), marker="D", s=30, c=CC["mark_peak"],
                   edgecolors="white", linewidths=0.6, zorder=7)


def top_bar(m: Mock, label: str, banner: str = "", color: str = BODY) -> None:
    w = m.button(14, 76, label, accent=True, h=30)
    if banner:
        m.text(14 + w + 12, 91, banner, color=color, weight="bold")


# --------------------------------------------------------------------------
# Vistas
# --------------------------------------------------------------------------

PROFILE = [(150, 120), (165, 1), (170, 1), (190, 90)]


def heat_x_span(ramps) -> float:
    hold = sum(h for _t, h in ramps)
    return max(300.0, min(hold + 90.0 * max(len(ramps), 1) + 180.0, 7200.0))


def view_heat(name, rows, hp, *, running, banner="", banner_color=BODY, hp_override=None):
    m = Mock("HEAT")
    top_bar(m, "Detener HEAT" if running else "Iniciar HEAT", banner, banner_color)
    last = hp_override or (hp[-1] if hp else None)
    act = last["RI"] if last and last["P"] == 1 and last["A"] in (4, 5) else None
    ramps = [(True, t, h) for t, h in PROFILE]
    ramps_panel(m, 14, 114, 440, 300, ramps, act)
    status_panel(m, 462, 114, 520, 300, hp_values(last))
    chart_block(m, 10, 422, W - 20, H - 422 - 44, "Curva en vivo", rows,
                y_max=max(t for t, _h in PROFILE) + 50.0,
                x_span=heat_x_span(PROFILE), locked=False, event_rows_max=15)
    return m.save(name)


def view_connection():
    m = Mock("Conexión")
    y = 76
    m.frame(14, y, 612, 56, "Puerto serie")
    m.text(26, y + 34, "Puerto")
    m.combo(72, y + 23, 214, PORT, disabled=True)
    bx = 294
    bx += m.button(bx, y + 21, "Refrescar") + 8
    m.text(bx, y + 34, "19200 8N1")
    bx += 76
    bx += m.button(bx, y + 21, "Desconectar", accent=True) + 6
    m.button(bx, y + 21, "Ping")

    m.frame(634, y, 330, 56, "Sesión")
    bx = 646
    bx += m.button(bx, y + 21, "Cambiar a modo Manual") + 6
    m.button(bx, y + 21, "Consultar estado")

    m.frame(972, y, 294, 74, "Sondeo de estado")
    m.check(984, y + 27, True, disabled=True)
    m.text(1004, y + 34, "Activar", color="#8795a1")
    m.text(1070, y + 34, "cada")
    m.combo(1104, y + 23, 70, "1 s", disabled=True)
    m.text(984, y + 58, "Pausado: en USB el equipo envía $HP cada 1 s", color=MUTED, size=8.5)

    cy = 160
    m.frame(14, cy, W - 28, H - cy - 44, "Consola serie")
    m.text(26, cy + 30, "Tráfico AT: órdenes, respuestas y tramas $HP.", color=MUTED)
    bx = W - 28
    for label in ("Exportar", "Limpiar"):
        bw = m.tw(label) + 26
        bx -= bw
        m.button(bx, cy + 18, label, w=bw)
        bx -= 6
    con = DEFAULT_THEME
    lx, ly, lw, lh = 24, cy + 48, W - 48, H - cy - 44 - 58
    m.rect(lx, ly, lw, lh, con["console_bg"], con["console_border"], z=3)
    hp_idle = "$HP,T=31.6,P=1,A=0,SET=0,DLY=0,RUN=0,EL=0,DU=0,F=0,RI=0,FL=0,TL=0"
    lines = [
        ("--", "puerto abierto — el saludo HP solo sale al encender; preguntando con AT…"),
        ("TX", "AT"), ("RX", "OK"),
        ("--", "equipo en marcha (AT → OK)"), ("--", "equipo en línea"),
        ("TX", "AT+STAT?"), ("RX", hp_idle), ("RX", "OK"),
        ("TX", "AT+MODE=1"), ("RX", hp_idle), ("RX", "OK"),
        ("TX", "AT+CFG=R?"), ("RX", "$R,N=4,0=150/120,1=165/1,2=170/1,3=190/90"), ("RX", "OK"),
        ("TX", "AT+CFG?"),
        ("RX", "$CF,MN=50,MX=210,KP=246,KI=10,BN=4,BX=6,DLY=0,AIR=1,AMS=2000"), ("RX", "OK"),
        ("RX", "$HP,T=31.7,P=1,A=0,SET=0,DLY=0,RUN=0,EL=0,DU=0,F=0,RI=0,FL=0,TL=0"),
        ("TX", "AT+RUN=1"), ("RX", "OK"),
        ("RX", "$HP,T=31.9,P=1,A=5,SET=150,DLY=0,RUN=0,EL=1,DU=100,F=0,RI=0,FL=0,TL=0"),
        ("RX", "$HP,T=32.4,P=1,A=5,SET=150,DLY=0,RUN=0,EL=2,DU=100,F=0,RI=0,FL=0,TL=0"),
        ("RX", "$HP,T=33.1,P=1,A=5,SET=150,DLY=0,RUN=0,EL=3,DU=100,F=0,RI=0,FL=0,TL=0"),
    ]
    ms = 402
    for i, (d, text) in enumerate(lines):
        ms += 37 if d != "--" else 1
        ts = f"18:02:{11 + ms // 1000:02d}.{ms % 1000:03d}"
        yy = ly + 14 + i * 19
        if yy > ly + lh - 10:
            break
        m.text(lx + 10, yy, f"{ts} {d} {text}", family="monospace", size=8.4,
               color=con["console_fg"], z=4)
    return m.save("01_conexion.png")


def view_tune(rows, cycles):
    m = Mock("Autotune")
    top_bar(m, "Iniciar autoajuste")
    x, y, w, h = 14, 114, 440, 300
    m.frame(x, y, w, h, "Autoajuste")
    fields = [
        ("Temperatura (°C)", "150", "Ciclos", str(cycles)),
        ("Histéresis (×10)", "15", "Timeout (s)", "2000"),
    ]
    fy = y + 28
    for l1, v1, l2, v2 in fields:
        m.text(x + 14, fy + 11, l1)
        m.entry(x + 130, fy, 70, v1)
        m.text(x + 230, fy + 11, l2)
        m.entry(x + 330, fy, 70, v2)
        fy += 30
    m.button(x + 14, fy + 4, "Guardar parámetros")
    m.sep(x + 14, fy + 44, w - 28)
    fy += 58
    m.text(x + 14, fy, "Fase")
    m.text(x + 130, fy, "Listo", color=VAL)
    m.text(x + 230, fy, "Ciclos")
    m.text(x + 330, fy, f"{cycles} / {cycles}", color=VAL)
    fy += 26
    m.text(x + 14, fy, "Progreso")
    m.text(x + 130, fy, "100 %", color=VAL)
    m.rect(x + 230, fy - 4, 170, 8, ACCENT, z=3)
    fy += 34
    m.text(x + 14, fy, "Kp ×10")
    m.text(x + 130, fy, "246", color=VAL, weight="bold")
    m.text(x + 230, fy, "Ki ×10")
    m.text(x + 330, fy, "10", color=VAL, weight="bold")
    m.button(x + 14, fy + 20, "Releer ganancias del equipo")

    last = rows[-1]
    hp = {"T": last[1], "P": 2, "A": 10, "SET": 150, "RUN": 0, "EL": int(last[0]),
          "DU": 0, "F": 0, "RI": 0, "FL": 0, "TL": 0}
    vals = hp_values(hp)
    vals["PROG"] = proto.prog_name(2)
    status_panel(m, 462, 114, 520, 300, vals)
    chart_block(m, 10, 422, W - 20, H - 422 - 44, "Curva de autoajuste", rows,
                y_max=150 * 1.5, x_span=2000.0, locked=True, band=(148.5, 151.5),
                event_rows_max=15)
    return m.save("05_autotune_listo.png")


def view_settings():
    m = Mock("Ajustes")
    m.text(16, 88, "HotPlate", size=10, weight="bold", color=MUTED)
    m.button(W - 30 - 190, 76, "Leer ajustes del equipo", w=190)
    m.text(16, 116, "Límites, bandas de meseta, arranque de HEAT y ganancias PI del equipo.",
           color=MUTED)

    def block(x, y, w, h, title, rows, save):
        m.frame(x, y, w, h, title)
        ry = y + 30
        for label, kind, value in rows:
            m.text(x + 14, ry + 11, label)
            if kind == "entry":
                m.entry(x + w - 14 - 110, ry, 110, value)
            elif kind == "clock":
                hh, mm = value.split(":")
                m.spin(x + w - 14 - 110, ry, 48, hh)
                m.text(x + w - 14 - 56, ry + 11, ":")
                m.spin(x + w - 14 - 48, ry, 48, mm)
            elif kind == "check":
                m.check(x + w - 14 - 14, ry + 4, value == "1")
            ry += 32
        m.button(x + 10, y + h - 36, save)

    bw, bh = 400, 150
    block(14, 134, bw, bh, "Límites de temperatura",
          [("Temperatura mínima (°C)", "entry", "50"),
           ("Temperatura máxima (°C)", "entry", "210")], "Guardar límites")
    block(14 + bw + 8, 134, bw, bh, "Meseta de las rampas",
          [("Banda entrada (±°C)", "entry", "4"),
           ("Banda salida (±°C)", "entry", "6")], "Guardar bandas")
    block(14, 134 + bh + 8, bw, bh, "Arranque y finalización de HEAT",
          [("Retraso de arranque", "clock", "00:00"),
           ("Aire al enfriar", "check", "1")], "Guardar arranque / fin")
    block(14 + bw + 8, 134 + bh + 8, bw, bh, "Ganancias PI (valores ×10)",
          [("Proporcional Kp", "entry", "246"),
           ("Integral Ki", "entry", "10")], "Sobrescribir valores PID")
    m.text(16, 134 + 2 * bh + 30,
           "Guardar bandas envía AT+CFG=B. Guardar arranque / fin envía AT+CFG=H,<delay>,<air>.",
           color=MUTED)

    tip_x, tip_y = 40, 500
    m.text(tip_x, tip_y - 14, "Ejemplo de tooltip (cursor sobre «Retraso de arranque»):",
           color=MUTED, size=8.5)
    m.rect(tip_x, tip_y, 380, 58, "#ffffe0", "#8795a1", z=8)
    for i, line in enumerate((
        "Retraso de arranque",
        "Rango / escala: 00:00 … 12:00 (horas:minutos). 00:00 = inmediato.",
        "Trama / comando: $CF DLY=<s>  ·  AT+CFG=H,<s>,<air>",
    )):
        m.text(tip_x + 8, tip_y + 12 + i * 17, line, size=8.2, z=9)
    return m.save("06_ajustes.png")


def view_appearance():
    m = Mock("Apariencia")
    m.text(16, 88, "HotPlate Studio", size=10, weight="bold", color=MUTED)
    m.text(16, 110, "Familia, texto, campos y botones cubren toda la interfaz. El estado del "
           "proceso usa sus propias filas de sección, clave y valor.", color=MUTED)
    x, y, w, h = 14, 124, W - 28, H - 124 - 44
    m.frame(x, y, w, h, "Apariencia")
    tx = x + 14
    for i, name in enumerate(("Fuentes", "Gráficas", "Consola serie")):
        tw = m.tw(name) + 30
        sel = i == 0
        m.rect(tx, y + 24 if sel else y + 28, tw, 28 if sel else 24,
               "#ffffff" if sel else TAB, BORDER, z=3)
        m.text(tx + tw / 2, y + 39, name, ha="center",
               color=(ACCENT if sel else BODY), weight=("bold" if sel else "normal"))
        tx += tw + 2
    m.rect(x + 14, y + 52, w - 28, h - 110, "#ffffff", BORDER, z=2)
    t = DEFAULT_THEME
    rows = [
        ("Familia general", "combo", "Helvetica"),
        ("Texto general (pt)", "spin", str(t["body_size"])),
        ("Color del texto general", "color", t["body_color"]),
        ("Campos (pt)", "spin", str(t["input_size"])),
        ("Botones (pt)", "spin", str(t["button_size"])),
        ("Títulos de paneles", "swc", ("frame_title_size", "frame_title_weight", "frame_title_color")),
        ("Estado · títulos de sección", "swc", ("section_title_size", "section_title_weight", "section_title_color")),
        ("Estado · etiquetas", "swc", ("status_key_size", "status_key_weight", "status_key_color")),
        ("Estado · valores", "swc", ("status_value_size", "status_value_weight", "status_value_color")),
    ]
    ry = y + 68
    cx = x + 240
    for label, kind, val in rows:
        m.text(x + 30, ry + 11, label)
        if kind == "combo":
            m.combo(cx, ry, 150, val)
        elif kind == "spin":
            m.spin(cx, ry, 70, val)
        elif kind == "color":
            m.entry(cx, ry, 90, val, align="left")
            m.swatch(cx + 96, ry + 3, val)
            m.button(cx + 124, ry - 1, "…", w=28, h=24)
        else:
            sk, wk, ck = val
            m.spin(cx, ry, 56, str(t[sk]))
            m.combo(cx + 62, ry, 80, t[wk])
            m.entry(cx + 148, ry, 80, t[ck], align="left")
            m.swatch(cx + 234, ry + 3, t[ck])
            m.button(cx + 262, ry - 1, "…", w=28, h=24)
        ry += 34

    px, py = 760, y + 68
    m.frame(px, py, 470, 300, "Muestra de colores de gráfica (pestaña Gráficas)")
    chart_rows = [
        ("Temperatura medida", "temp"), ("SET / objetivo", "set"), ("Potencia DU", "duty"),
        ("Marcador cruce ↑", "mark_up"), ("Marcador cruce ↓", "mark_down"),
        ("Calentador ON", "mark_on"), ("Calentador OFF", "mark_off"), ("Cresta", "mark_peak"),
        ("Inicio de fase", "phase"), ("Banda histéresis", "band"), ("Fondo de ejes", "face"),
    ]
    for i, (label, key) in enumerate(chart_rows):
        yy = py + 30 + i * 24
        m.text(px + 16, yy + 8, label, size=8.6)
        m.entry(px + 200, yy, 84, CC[key], align="left", h=20)
        m.swatch(px + 292, yy + 2, CC[key])

    bx = x + 14
    bx += m.button(bx, y + h - 42, "Aplicar y guardar tema") + 6
    m.button(bx, y + h - 42, "Restaurar defaults")
    return m.save("07_apariencia.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [view_connection()]

    full_rows, full_hp = sim_heat(PROFILE)
    cut = next(i for i, h in enumerate(full_hp) if h["A"] == 4 and h["RI"] == 3) + 40
    paths.append(view_heat("02_heat_en_curso.png", full_rows[:cut], full_hp[:cut], running=True))
    paths.append(view_heat(
        "03_heat_terminado.png", full_rows, full_hp, running=False,
        banner="Alarma: HEAT terminado (código 2)", banner_color="#cc9900",
    ))
    fcut = next(i for i, h in enumerate(full_hp) if h["A"] == 5 and h["RI"] == 1) + 25
    fault_rows = full_rows[:fcut]
    fault_hp = dict(full_hp[fcut - 1], A=9, T=None, DU=0, FL=1, RUN=0)
    paths.append(view_heat(
        "04_heat_falla.png", fault_rows, full_hp[:fcut], running=False,
        banner="Corte por falla — salidas desactivadas", banner_color="#c0392b",
        hp_override=fault_hp,
    ))

    tune_rows, cycles = sim_tune()
    paths.append(view_tune(tune_rows, cycles))
    paths.append(view_settings())
    paths.append(view_appearance())
    for p in paths:
        print(p.relative_to(ROOT))


if __name__ == "__main__":
    main()
