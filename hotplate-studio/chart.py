"""Gráfico T / objetivo / potencia embebido en Tk."""

from __future__ import annotations

import math
from collections import deque
from typing import Callable, List, Optional, Sequence, Tuple

import tkinter as tk

from constants import CHART_X_SPAN_S
import theme as ui_theme
from widgets import ui
from widgets.tooltip import ToolTip


def _x_major_step(span_s: float) -> float:
    """Paso de marcas que divide el tramo y cae en un número redondo."""
    span = max(int(round(span_s)), 1)
    best = float(span)
    best_score = -1
    for parts in range(4, 9):
        if span % parts != 0:
            continue
        step = span // parts
        score = parts
        if step % 1000 == 0:
            score += 40
        elif step % 100 == 0:
            score += 30
        elif step % 50 == 0:
            score += 20
        elif step % 10 == 0:
            score += 10
        elif step % 5 == 0:
            score += 5
        if score > best_score:
            best_score = score
            best = float(step)
    if best_score < 0:
        return span / 5.0
    return best


def _nice_step(span_s: float, max_parts: int = 9) -> float:
    """Paso redondo (1, 2, 4, 5 × 10ⁿ) con como mucho `max_parts` intervalos."""
    span = max(float(span_s), 1.0)
    base = 10.0 ** math.floor(math.log10(span / max_parts))
    for mult in (1, 2, 4, 5, 10, 20):
        if span / (base * mult) <= max_parts:
            return base * mult
    return span


def _mpl_families(preferred: Sequence[str], fallback: str) -> list[str]:
    """Familias que matplotlib conoce (evita avisos de findfont)."""
    from matplotlib import font_manager

    known = {f.name for f in font_manager.fontManager.ttflist}
    out = [f for f in preferred if f and f in known]
    return out + [fallback]


def _crossings_t_set(
    xs: Sequence[float], ys: Sequence[float], sets: Sequence[float]
) -> List[Tuple[float, float, str]]:
    """Cruces T vs SET: (t, T, 'up'|'down')."""
    out: List[Tuple[float, float, str]] = []
    for i in range(1, len(xs)):
        t0, t1 = float(xs[i - 1]), float(xs[i])
        y0, y1 = float(ys[i - 1]), float(ys[i])
        s0, s1 = float(sets[i - 1]), float(sets[i])
        if any(map(lambda v: v != v, (y0, y1, s0, s1))):  # NaN
            continue
        e0, e1 = y0 - s0, y1 - s1
        if e0 == 0.0:
            continue
        if e0 * e1 > 0:
            continue
        if e1 == 0.0:
            out.append((t1, y1, "up" if e0 < 0 else "down"))
            continue
        frac = abs(e0) / (abs(e0) + abs(e1))
        tc = t0 + frac * (t1 - t0)
        yc = y0 + frac * (y1 - y0)
        out.append((tc, yc, "up" if e1 > 0 else "down"))
    return out


def _duty_edges(
    xs: Sequence[float], dus: Sequence[float], thr: float = 0.0
) -> List[Tuple[float, str]]:
    """Bordes de calentador: (t, 'on'|'off'). ON si la potencia pasa de 0."""
    out: List[Tuple[float, str]] = []
    prev: Optional[bool] = None
    for t, du in zip(xs, dus):
        tf, df = float(t), float(du)
        if df != df:
            continue
        on = df > thr
        if prev is None:
            prev = on
            if on:
                out.append((tf, "on"))
            continue
        if on != prev:
            out.append((tf, "on" if on else "off"))
            prev = on
    return out


def _crests(
    xs: Sequence[float], ys: Sequence[float], min_drop: float = 5.0
) -> List[Tuple[float, float]]:
    """Punto más alto de cada cresta que sube y luego baja al menos min_drop °C."""
    pts: List[Tuple[float, float]] = []
    for x, y in zip(xs, ys):
        yf = float(y)
        if yf == yf:
            pts.append((float(x), yf))
    if len(pts) < 3:
        return []
    out: List[Tuple[float, float]] = []
    trough = pts[0][1]
    peak = pts[0]
    rising = False
    for t, y in pts:
        if not rising:
            if y <= trough:
                trough = y
                peak = (t, y)
            elif y >= trough + min_drop:
                rising = True
                peak = (t, y)
            continue
        if y >= peak[1]:
            peak = (t, y)
        elif peak[1] - y >= min_drop:
            out.append(peak)
            rising = False
            trough = y
            peak = (t, y)
    return out


def _phase_spans(
    xs: Sequence[float], phases: Sequence[str]
) -> List[Tuple[float, float, str]]:
    """Tramos continuos de la misma fase: (t0, t1, nombre)."""
    n = min(len(xs), len(phases))
    spans: List[Tuple[float, float, str]] = []
    i = 0
    while i < n and not phases[i]:
        i += 1
    if i >= n:
        return spans
    start = i
    name = str(phases[i])
    for j in range(i + 1, n):
        cur = str(phases[j]) if phases[j] else name
        if cur != name:
            spans.append((float(xs[start]), float(xs[j]), name))
            start = j
            name = cur
    spans.append((float(xs[start]), float(xs[n - 1]), name))
    return spans


_EVENT_LIMIT = 300


# Stitch: texto SVG de 9 / 8.5 unidades en un lienzo 1000 → ~770 px (≈ 6.9 / 6.5 px).
TICK_PT = 5.0
_ACTIVE_ROW_MARK = "#dbe2ea"
_PHASE_LABEL_MIN_PX = 40
PHASE_PT = 4.7
_PHASE_LINE = "#cbd5e1"
_PHASE_TEXT = "#64748b"

HEAT_LEGEND = (
    ("line", "temp", "Temperatura medida"),
    ("dashed", "set", "SET"),
    ("line", "duty", "Potencia (eje der. 0–100 %)"),
    ("glyph:◆:14", "mark_peak", "Cresta"),
    ("glyph:▲:12", "mark_up", "Cruce ↑"),
    ("glyph:▼:12", "mark_down", "Cruce ↓"),
    ("glyph:|:12", "text", "Calentador ON/OFF"),
    ("glyph:┊:12", "phase", "Inicio de fase"),
)
TUNE_LEGEND = (
    ("line", "temp", "Temperatura medida"),
    ("dashed", "set", "SET"),
    ("line", "duty", "Potencia (eje der. 0–100 %)"),
    ("band", "band", "Banda histéresis"),
    ("glyph:◆:14", "mark_peak", "Cresta"),
    ("glyph:▲:12", "mark_up", "Cruce ↑"),
    ("glyph:▼:12", "mark_down", "Cruce ↓"),
    ("glyph:|:12", "text", "Calentador ON / OFF"),
)


class EventTable(tk.Canvas):
    """Tabla del registro de eventos (`font-mono text-[11px]`, cabecera #edf4ff)."""

    ROW_H = 25
    HEAD_H = 25
    COLS = (0.215, 0.155, 0.17)

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, bg=ui.CARD, highlightthickness=0, bd=0)
        self._hp_own_wheel = True
        self.rows: list[tuple[str, str, str, str, str]] = []
        self._colors: dict[str, str] = {}
        self._top = 0
        self._follow = True
        self.bind("<Configure>", lambda _e: self.render(), add="+")
        self.bind("<MouseWheel>", self._on_wheel, add="+")

    def set_colors(self, colors: dict[str, str]) -> None:
        self._colors = colors
        self.render()

    def set_rows(self, rows: list[tuple[str, str, str, str, str]]) -> None:
        self.rows = rows
        if self._follow:
            self._top = max(0, len(rows) - self._visible_rows())
        self.render()

    def _visible_rows(self) -> int:
        h = max(self.winfo_height(), 1)
        return max(1, (h - self.HEAD_H) // self.ROW_H)

    def _on_wheel(self, e) -> None:
        if not self.rows:
            return
        step = -1 if e.delta > 0 else 1
        max_top = max(0, len(self.rows) - self._visible_rows())
        self._top = max(0, min(max_top, self._top + step))
        self._follow = self._top >= max_top
        self.render()

    def _event_color(self, tag: str) -> str:
        cc = self._colors
        if tag.startswith("phase"):
            return cc.get("phase", ui.ACCENT)
        return {
            "up": cc.get("mark_up", "#8e44ad"),
            "down": cc.get("mark_down", "#d35400"),
            "on": cc.get("mark_on", ui.GREEN),
            "off": cc.get("mark_off", "#7f8c8d"),
            "peak": cc.get("mark_peak", "#6c3483"),
        }.get(tag, ui.TEXT)

    def render(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 20:
            return
        f_head = ui.mono(11, "bold")
        f_row = ui.mono(11)
        f_bold = ui.mono(11, "bold")
        xs = [0.0]
        for frac in self.COLS:
            xs.append(xs[-1] + frac * w)
        pads = (8, 4, 6, 8)
        self.create_rectangle(0, 0, w, self.HEAD_H - 1, fill=ui.SOFT, outline="")
        self.create_line(0, self.HEAD_H - 1, w, self.HEAD_H - 1, fill=ui.SUBTLE)
        for x, pad, title in zip(xs, pads, ("Tiempo", "Dur.", "T °C", "Evento")):
            self.create_text(x + pad, self.HEAD_H / 2, text=title, anchor=tk.W,
                             fill=ui.MUTED, font=f_head)
        n_vis = self._visible_rows() + 1
        visible = self.rows[self._top:self._top + n_vis]
        last_index = len(self.rows) - 1
        y = self.HEAD_H
        for offset, (time_s, dur, temp, text, tag) in enumerate(visible):
            idx = self._top + offset
            is_last = idx == last_index
            color = self._event_color(tag)
            if is_last:
                self.create_rectangle(0, y, w, y + self.ROW_H - 1, fill=ui.SOFT, outline="")
                self.create_rectangle(0, y, 1, y + self.ROW_H - 1, fill=_ACTIVE_ROW_MARK,
                                      outline="")
            cy = y + (self.ROW_H - 1) / 2
            self.create_text(xs[0] + pads[0], cy, text=time_s, anchor=tk.W,
                             fill=(ui.ACCENT if is_last else ui.MUTED),
                             font=(f_bold if is_last else f_row))
            self.create_text(xs[1] + pads[1], cy, text=dur, anchor=tk.W, fill=ui.MUTED, font=f_row)
            self.create_text(xs[2] + pads[2], cy, text=temp, anchor=tk.W,
                             fill=(ui.RED if is_last else ui.TEXT),
                             font=(f_bold if is_last else f_row))
            ex = xs[3] + pads[3]
            if is_last:
                self.create_oval(ex, cy - 3, ex + 6, cy + 3, fill=color, outline="")
                ex += 10
            weight_font = f_bold if (is_last or not tag.startswith("phase")) else f_row
            self.create_text(ex, cy, text=text, anchor=tk.W, fill=color, font=weight_font)
            y += self.ROW_H
            if y < h:
                self.create_line(0, y - 1, w, y - 1, fill=ui.SUBTLE)
            if y > h:
                break


class LiveChart:
    def __init__(
        self,
        parent: tk.Misc,
        *,
        title: str = "Curva en vivo",
        on_export: Optional[Callable[[], None]] = None,
        on_export_events: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        figsize: tuple[float, float] = (7.7, 2.61),
        x_span_s: float = CHART_X_SPAN_S,
        x_locked: bool = True,
        legend: Sequence[tuple[str, str, str]] = HEAT_LEGEND,
        plot_height: int = 261,
        events_height: int = 321,
    ) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self._y_max: Optional[float] = None
        self._auto_y_top = 100.0
        self._user_ylim: Optional[tuple[float, float]] = None
        self._x_locked = bool(x_locked)
        self._x_span_s = max(float(x_span_s), 1.0)
        self._user_xlim: Optional[tuple[float, float]] = None
        self._applying_xlim = False
        self._applying_ylim = False
        self._overlay_artists: list = []
        self._event_signature: tuple = ()
        self._drag: Optional[tuple[float, tuple[float, float]]] = None

        self.frame = ui.card(parent)
        body = self.frame.body
        head = ui.CardHeader(body, title, icon="chart", height=26)
        head.pack(fill=tk.X)
        if on_clear is not None:
            ui.Button(head.right, "Limpiar", command=on_clear, variant="secondary",
                      height=26, radius=4).pack(side=tk.RIGHT)
        ui.Button(head.right, "Restablecer zoom", command=self.reset_view,
                  variant="secondary", height=26, radius=4).pack(side=tk.RIGHT, padx=(0, 8))
        if on_export is not None:
            ui.Button(head.right, "Exportar muestras", command=on_export, variant="soft",
                      height=26, radius=4).pack(side=tk.RIGHT, padx=(0, 8))

        self._legend_row = tk.Frame(body, bg=ui.CARD, height=24)
        self._legend_row.pack(fill=tk.X, pady=(12, 0))
        self._legend_row.pack_propagate(False)
        ui.hline(body).pack(fill=tk.X)
        self._legend_bits: list[tuple[tk.Canvas, str, str]] = []
        self._legend_labels: dict[str, ui.Line] = {}
        self._build_legend(legend)

        split = tk.Frame(body, bg=ui.CARD)
        split.pack(fill=tk.X, pady=(12, 0))
        split.columnconfigure(0, weight=8, uniform="chart")
        split.columnconfigure(1, weight=4, uniform="chart")
        plot_box = ui.Box(split, fill=ui.CARD, border=ui.BORDER, radius=4, padx=8, pady=8)
        plot_box.grid(row=0, column=0, sticky="new", padx=(0, 8))
        events = ui.Box(split, fill=ui.BG, border=ui.BORDER, radius=4, padx=12, pady=12)
        events.grid(row=0, column=1, sticky="new", padx=(8, 0))
        events.configure(height=events_height)
        events.pack_propagate(False)
        split.bind("<Configure>", lambda e: self._fit_split(e.width), add="+")
        self._split = split

        self.fig = Figure(figsize=figsize, dpi=100)
        self.fig.patch.set_facecolor(ui.CARD)
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.ax.twinx()
        # Potencia debajo de la temperatura: el eje principal va delante y transparente.
        self.ax.set_zorder(2)
        self.ax2.set_zorder(1)
        self._style_axes()
        self.ax.set_ylim(0, 100)
        self.ax2.set_ylim(0, 100)
        self.ax.set_xlim(0, self._x_span_s)
        self._apply_x_measures()
        self.ax.callbacks.connect("xlim_changed", self._on_xlim_changed)
        self.ax.callbacks.connect("ylim_changed", self._on_ylim_changed)

        cc = ui_theme.chart_colors()
        (self.line_t,) = self.ax.plot([], [], color=cc["temp"], linewidth=1.22,
                                      solid_capstyle="round", zorder=4)
        (self.line_set,) = self.ax.plot([], [], color=cc["set"], linestyle=(0, (2.8, 2.2)),
                                        linewidth=1.0, zorder=3)
        (self.line_du,) = self.ax2.plot([], [], color=cc["duty"], linewidth=0.83, zorder=2)
        self.fig.subplots_adjust(left=0.051, right=0.939, top=0.900, bottom=0.146)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_box.body)
        widget = self.canvas.get_tk_widget()
        # width=1: el ancho lo decide la rejilla 8/12, no el figsize.
        widget.configure(width=1, height=plot_height, highlightthickness=0, bd=0, bg=ui.CARD)
        widget.pack(fill=tk.X)
        self._plot_widget = widget
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        ToolTip(
            widget,
            "Arrastra para desplazar · ⌘/Ctrl + rueda para zoom · doble clic restablece",
        )

        ev = events.body
        bar = tk.Frame(ev, bg=ui.BG, height=22)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        ui.Line(bar, "REGISTRO DE EVENTOS", font=ui.sans(12, "bold"), fg=ui.TEXT,
                height=22, bg=ui.BG).pack(side=tk.LEFT)
        if on_export_events is not None:
            ui.Button(bar, "Exportar registro", command=on_export_events, variant="white",
                      font=ui.sans(11, "bold"), padx=8, height=22, radius=4,
                      icon="download", icon_size=13, gap=4).pack(side=tk.RIGHT)
        tk.Frame(ev, bg=ui.BG, height=8).pack(fill=tk.X)
        ui.hline(ev).pack(fill=tk.X)
        table_box = ui.Box(ev, fill=ui.CARD, border=ui.SUBTLE, radius=4)
        table_box.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
        self.event_table = EventTable(table_box.body)
        self.event_table.pack(fill=tk.BOTH, expand=True)
        self.event_table.set_colors(cc)
        self._apply_mpl_fonts()

    # ------------------------------------------------------------ layout
    def _fit_split(self, width: int) -> None:
        """Proporción 8/12 · 4/12 con 16 px de separación (grid-cols-12 gap-4)."""
        col = (width - 11 * 16) / 12.0
        left = int(round(8 * col + 7 * 16))
        if getattr(self, "_split_left", None) == left:
            return
        self._split_left = left
        self._split.columnconfigure(0, weight=0, minsize=left, uniform="")
        self._split.columnconfigure(1, weight=1, uniform="")

    def set_legend_text(self, key: str, text: str) -> None:
        lbl = self._legend_labels.get(key)
        if lbl is not None:
            lbl.configure(text=text)

    def _build_legend(self, items: Sequence[tuple[str, str, str]]) -> None:
        for index, (kind, key, text) in enumerate(items):
            cell = tk.Frame(self._legend_row, bg=ui.CARD)
            cell.pack(side=tk.LEFT, padx=(0 if index == 0 else 20, 0))
            if kind.startswith("glyph:"):
                _g, glyph, size = kind.split(":")
                swatch = tk.Canvas(cell, width=int(size) - 2, height=16, highlightthickness=0,
                                   bg=ui.CARD, bd=0)
            else:
                swatch = tk.Canvas(cell, width=14, height=16, highlightthickness=0,
                                   bg=ui.CARD, bd=0)
            swatch.pack(side=tk.LEFT, padx=(0, 6))
            lbl = ui.Line(cell, text, font=ui.sans(12), fg=ui.MUTED, height=16)
            lbl.pack(side=tk.LEFT)
            self._legend_labels[key] = lbl
            self._legend_bits.append((swatch, kind, key))
        self._paint_legend()

    def _paint_legend(self) -> None:
        cc = ui_theme.chart_colors()
        cc = dict(cc, text=ui.TEXT)
        for swatch, kind, key in self._legend_bits:
            swatch.delete("all")
            color = cc.get(key, ui.TEXT)
            if kind == "line":
                swatch.create_rectangle(0, 7, 14, 9, fill=color, outline="")
            elif kind == "dashed":
                for x in (0, 5, 10):
                    swatch.create_rectangle(x, 8, x + 3, 10, fill=color, outline="")
            elif kind == "band":
                swatch.create_rectangle(0, 4, 14, 12, fill=ui.blend(color, ui.CARD, 0.4),
                                        outline=color)
            else:
                _g, glyph, size = kind.split(":")
                swatch.create_text(
                    (int(size) - 2) / 2, 8, text=glyph, fill=color,
                    font=ui.sans(int(size), "bold"),
                )

    # --------------------------------------------------------- estilo mpl
    def _style_axes(self) -> None:
        for axis in (self.ax, self.ax2):
            for side in ("top", "left", "right"):
                axis.spines[side].set_visible(False)
            axis.spines["bottom"].set_visible(False)
            axis.tick_params(length=0, pad=3)
            axis.set_facecolor("none")
        self.ax.patch.set_visible(False)
        self.ax2.set_facecolor(ui_theme.chart_colors()["face"])
        self.ax.spines["bottom"].set_visible(True)
        self.ax.spines["bottom"].set_color(ui.BORDER)
        self.ax.spines["bottom"].set_linewidth(0.83)
        self.ax.grid(True, axis="y", color=ui.SOFT, linewidth=0.55)
        self.ax.grid(False, axis="x")
        self.ax2.grid(False)
        self.ax.set_axisbelow(True)

    def _apply_mpl_fonts(self) -> None:
        from widgets.ui import mono_family

        mono = _mpl_families([mono_family(), "JetBrains Mono", "SF Mono", "Menlo"],
                             "DejaVu Sans Mono")
        sans = _mpl_families([ui_theme.ui_family(), "Inter", "SF Pro Text", "Arial",
                              "Helvetica Neue"], "DejaVu Sans")
        self._sans_fonts = sans
        tick_pt = TICK_PT
        for axis in (self.ax, self.ax2):
            axis.tick_params(labelsize=tick_pt, colors=ui.FAINT)
            for label in axis.get_xticklabels() + axis.get_yticklabels():
                label.set_fontfamily(mono)
        self.ax.set_xlabel("Tiempo (s)", fontsize=tick_pt, fontweight="bold",
                           color=ui.MUTED, fontfamily=sans, labelpad=2)
        self.ax.set_ylabel("Temperatura (°C)", fontsize=tick_pt, fontweight="bold",
                           color=ui.MUTED, fontfamily=sans, labelpad=2)
        self.ax2.set_ylabel("Potencia (%)", fontsize=tick_pt, fontweight="bold",
                            color=ui_theme.chart_colors()["duty"], fontfamily=sans,
                            rotation=90, labelpad=2)
        self._tick_fonts = mono
        self._style_tick_labels()

    @staticmethod
    def _y_ticks(top: float) -> list[float]:
        ticks = [float(v) for v in range(0, int(top) + 1, 50)]
        if top - ticks[-1] > 5:
            ticks.append(float(top))
        return ticks

    def _apply_y_measures(self) -> None:
        from matplotlib.ticker import FixedLocator, FuncFormatter

        _y0, y1 = self.ax.get_ylim()
        self.ax.yaxis.set_major_locator(FixedLocator(self._y_ticks(y1)))
        self.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{int(round(v))} °C"))
        self.ax2.set_ylim(0, 100)
        self.ax2.yaxis.set_major_locator(FixedLocator([0, 25, 50, 75, 100]))
        self.ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{int(v)}%"))
        self._style_tick_labels()

    def _style_tick_labels(self) -> None:
        """Marca del SET actual en azul y 100 % de potencia en verde (negrita)."""
        cc = ui_theme.chart_colors()
        fonts = getattr(self, "_tick_fonts", ["Menlo"])
        set_c = getattr(self, "_current_set", None)
        for tick, value in zip(self.ax.yaxis.get_major_ticks(), self.ax.yaxis.get_majorticklocs()):
            hit = set_c is not None and abs(float(value) - set_c) < 0.5
            tick.label1.set_fontfamily(fonts)
            tick.label1.set_color(cc["set"] if hit else ui.FAINT)
            tick.label1.set_fontweight("bold" if hit else "normal")
        for tick, value in zip(self.ax2.yaxis.get_major_ticks(), self.ax2.yaxis.get_majorticklocs()):
            top = abs(float(value) - 100.0) < 0.5
            for label in (tick.label1, tick.label2):
                label.set_fontfamily(fonts)
                label.set_color(cc["duty"] if top else ui.FAINT)
                label.set_fontweight("bold" if top else "normal")

    # ------------------------------------------------------------- tema
    def event_rows(self) -> list[tuple[str, str, str, str]]:
        """Filas del registro: tiempo, duración, temperatura, evento."""
        return [(r[0], r[1], r[2], r[3]) for r in self.event_table.rows]

    def apply_theme(self) -> None:
        """Reaplica colores de series/marcadores y la fuente de los ejes."""
        cc = ui_theme.chart_colors()
        self.ax2.set_facecolor(cc["face"])
        self.line_t.set_color(cc["temp"])
        self.line_set.set_color(cc["set"])
        self.line_du.set_color(cc["duty"])
        self._paint_legend()
        self.event_table.set_colors(cc)
        self._apply_mpl_fonts()
        self.canvas.draw_idle()

    # ------------------------------------------------------ interacción
    def _on_press(self, event) -> None:
        if event.inaxes is None or event.xdata is None:
            return
        if getattr(event, "dblclick", False):
            self.reset_view()
            return
        self._drag = (float(event.x), tuple(self.ax.get_xlim()))

    def _on_motion(self, event) -> None:
        if self._drag is None or event.x is None:
            return
        x_px, (x0, x1) = self._drag
        width_px = max(self.ax.bbox.width, 1.0)
        shift = (float(event.x) - x_px) * (x1 - x0) / width_px
        lo = max(0.0, x0 - shift)
        self.ax.set_xlim(lo, lo + (x1 - x0))
        self._apply_x_locator(x1 - x0)
        self.canvas.draw_idle()

    def _on_release(self, _event) -> None:
        self._drag = None

    def _on_scroll(self, event) -> None:
        key = (event.key or "").lower()
        if not any(k in key for k in ("control", "ctrl", "cmd", "super", "meta")):
            return
        if event.xdata is None:
            return
        x0, x1 = self.ax.get_xlim()
        factor = 0.8 if event.button == "up" else 1.25
        center = float(event.xdata)
        lo = max(0.0, center - (center - x0) * factor)
        hi = max(lo + 5.0, center + (x1 - center) * factor)
        self.ax.set_xlim(lo, hi)
        self._apply_x_locator(hi - lo)
        self.canvas.draw_idle()

    # ------------------------------------------------------------ ejes
    def _on_xlim_changed(self, _ax) -> None:
        if self._applying_xlim:
            return
        x0, x1 = self.ax.get_xlim()
        self._user_xlim = (float(x0), float(x1))

    def _set_xlim_safe(self, x0: float, x1: float) -> None:
        self._applying_xlim = True
        try:
            self.ax.set_xlim(x0, x1)
        finally:
            self._applying_xlim = False

    def _on_ylim_changed(self, _ax) -> None:
        if self._applying_ylim:
            return
        y0, y1 = self.ax.get_ylim()
        self._user_ylim = (float(y0), float(y1))

    def _set_ylim_safe(self, y0: float, y1: float) -> None:
        self._applying_ylim = True
        try:
            self.ax.set_ylim(y0, math.ceil(y1 / 25.0) * 25.0)
        finally:
            self._applying_ylim = False
        self._apply_y_measures()

    def _apply_x_measures(self) -> None:
        # Origen fijo en t=0 del proceso; zoom del usuario se respeta en redraw.
        if self._user_xlim is None:
            self._set_xlim_safe(0.0, self._x_span_s)
            span = self._x_span_s
        else:
            span = max(self._user_xlim[1] - self._user_xlim[0], 1.0)
        self._apply_x_locator(span)

    def set_x_window(self, span_s: float, *, locked: bool) -> None:
        """Tramo base del eje X. `locked` mantiene el techo (autoajuste = timeout)."""
        span = max(float(span_s), 1.0)
        if abs(span - self._x_span_s) < 0.5 and locked == self._x_locked:
            return
        self._x_span_s = span
        self._x_locked = bool(locked)
        if self._user_xlim is None:
            self._apply_x_measures()
            self.canvas.draw_idle()

    def set_x_span(self, span_s: float) -> None:
        """Compat: fija el tramo, lo bloquea y sale de un zoom manual."""
        self._user_xlim = None
        self._x_span_s = max(float(span_s), 1.0)
        self._x_locked = True
        self._apply_x_measures()
        self.canvas.draw_idle()

    def _auto_x_end(self, t_last: float) -> float:
        """Techo ≥ span base; si t supera el tramo, crece en pasos redondos (origen 0)."""
        base = self._x_span_s
        t = max(float(t_last), 0.0)
        if t <= base:
            return base
        step = max(_x_major_step(base), 50.0)
        return max(base, math.ceil(t / step) * step)

    def _apply_x_locator(self, span_s: float) -> None:
        from matplotlib.ticker import FuncFormatter

        from matplotlib.ticker import FixedLocator

        x0, x1 = self.ax.get_xlim()
        step = _nice_step(max(span_s, 1.0))
        ticks = [v * step for v in range(math.ceil(x0 / step), int(x1 // step) + 1)]
        if ticks and x1 - ticks[-1] > 0.3 * step:
            ticks.append(x1)
        elif ticks:
            ticks[-1] = x1 if abs(x1 - ticks[-1]) < 0.3 * step else ticks[-1]
        self.ax.xaxis.set_major_locator(FixedLocator(ticks))
        every = self._x_locked

        def fmt(v: float, _pos) -> str:
            text = f"{int(round(v))}"
            if every:
                return f"{text}s"
            return f"{text} s" if abs(v - self.ax.get_xlim()[1]) < 0.5 else text

        self.ax.xaxis.set_major_formatter(FuncFormatter(fmt))

    def set_y_max(self, y_max: float) -> None:
        self._y_max = max(float(y_max), 1.0)
        if self._user_ylim is None:
            self._auto_y_top = max(self._auto_y_top, self._y_max)
            self._set_ylim_safe(0, self._auto_y_top)
        self.canvas.draw_idle()

    def _clear_overlays(self) -> None:
        for coll in list(self.ax.collections) + list(self.ax2.collections):
            coll.remove()
        for art in self._overlay_artists:
            try:
                art.remove()
            except Exception:
                pass
        self._overlay_artists.clear()

    @staticmethod
    def _fmt_time(value: float) -> str:
        sec = max(int(round(value)), 0)
        return f"{sec // 60:02d}:{sec % 60:02d}"

    @staticmethod
    def _temp_at(xs: Sequence[float], ys: Sequence[float], t: float) -> float:
        """Temperatura interpolada en t (NaN si no hay muestras válidas alrededor)."""
        import bisect

        n = min(len(xs), len(ys))
        if n == 0:
            return float("nan")
        i = bisect.bisect_left(xs, t, 0, n)
        if i < n and float(xs[i]) == t:
            return float(ys[i])
        if i <= 0:
            return float(ys[0])
        if i >= n:
            return float(ys[n - 1])
        x0, x1 = float(xs[i - 1]), float(xs[i])
        y0, y1 = float(ys[i - 1]), float(ys[i])
        if y0 != y0:
            return y1
        if y1 != y1 or x1 <= x0:
            return y0
        return y0 + (y1 - y0) * (t - x0) / (x1 - x0)

    def _update_event_console(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        crosses: Sequence[Tuple[float, float, str]],
        edges: Sequence[Tuple[float, str]],
        crests: Sequence[Tuple[float, float]],
        spans: Sequence[Tuple[float, float, str]],
    ) -> None:
        rows: list[tuple[float, float, float, str, str]] = []
        for t0, t1, name in spans:
            rows.append(
                (t0, max(t1 - t0, 0.0), self._temp_at(xs, ys, t0), f"Fase: {name}", "phase")
            )
        for t, y, kind in crosses:
            arrow = "↑" if kind == "up" else "↓"
            rows.append((t, 0.0, y, f"Cruce {arrow} SET", kind))
        for t, kind in edges:
            rows.append(
                (t, 0.0, self._temp_at(xs, ys, t), f"Calentador {kind.upper()}", kind)
            )
        for t, temp in crests:
            rows.append((t, 0.0, temp, "Cresta", "peak"))
        rows.sort(key=lambda row: (row[0], row[3]))
        rows = rows[-_EVENT_LIMIT:]
        signature = tuple(
            (round(t, 1), round(duration, 1), text, tag)
            for t, duration, _temp, text, tag in rows
        )
        if signature == self._event_signature:
            return
        self._event_signature = signature
        self.event_table.set_rows(
            [
                (
                    self._fmt_time(t),
                    self._fmt_time(duration) if duration > 0 else "—",
                    f"{temp:.1f}" if temp == temp else "—",
                    text,
                    tag,
                )
                for t, duration, temp, text, tag in rows
            ]
        )

    def _draw_event_markers(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        sets: Sequence[float],
        dus: Sequence[float],
        phases: Sequence[str],
    ) -> None:
        crosses = _crossings_t_set(xs, ys, sets)
        edges = _duty_edges(xs, dus)
        crests = _crests(xs, ys)
        spans = _phase_spans(xs, phases)

        up = [(t, y) for t, y, k in crosses if k == "up"]
        down = [(t, y) for t, y, k in crosses if k == "down"]
        cc = ui_theme.chart_colors()
        if up:
            sc = self.ax.scatter([p[0] for p in up], [p[1] for p in up], marker="^",
                                 s=30, c=cc["mark_up"], zorder=5)
            self._overlay_artists.append(sc)
        if down:
            sc = self.ax.scatter([p[0] for p in down], [p[1] for p in down], marker="v",
                                 s=30, c=cc["mark_down"], zorder=5)
            self._overlay_artists.append(sc)
        if crests:
            sc = self.ax.scatter([p[0] for p in crests], [p[1] for p in crests], marker="D",
                                 s=22, c=cc["mark_peak"], zorder=6)
            self._overlay_artists.append(sc)
            t_last, y_last = crests[-1]
            txt = self.ax.annotate(
                f"{y_last:.1f}°C", (t_last, y_last), xytext=(0, 7),
                textcoords="offset points", ha="center", va="bottom", fontsize=TICK_PT,
                fontweight="bold", color=cc["mark_peak"], fontfamily=self._tick_fonts,
                zorder=7,
            )
            self._overlay_artists.append(txt)

        y_lo, y_hi = self.ax.get_ylim()
        for t, kind in edges:
            color = cc["mark_on"] if kind == "on" else cc["mark_off"]
            mk = self.ax.plot([t], [y_lo], marker="|", markersize=8, markeredgewidth=1.6,
                              color=color, linestyle="None", zorder=5, clip_on=False)
            self._overlay_artists.extend(mk)

        last = len(spans) - 1
        x0, x1 = self.ax.get_xlim()
        px_per_s = self.ax.bbox.width / max(x1 - x0, 1e-6)
        for index, (t0, _t1, name) in enumerate(spans):
            current = index == last
            color = cc["phase"] if current else _PHASE_LINE
            ln = self.ax.axvline(t0, color=color, linestyle=(0, (3, 3)),
                                 linewidth=(0.67 if current else 0.55), zorder=3)
            self._overlay_artists.append(ln)
            next_t0 = spans[index + 1][0] if not current else None
            if next_t0 is not None and (next_t0 - t0) * px_per_s < _PHASE_LABEL_MIN_PX:
                continue
            label = self.ax.annotate(
                name, (t0, y_hi), xytext=(3, -4), textcoords="offset points",
                ha="left", va="top", fontsize=PHASE_PT,
                fontweight=("bold" if current else "normal"),
                color=(cc["phase"] if current else _PHASE_TEXT), zorder=7,
                fontfamily=getattr(self, "_sans_fonts", None),
                annotation_clip=True,
            )
            self._overlay_artists.append(label)
        self._update_event_console(xs, ys, crosses, edges, crests, spans)

    def redraw(
        self,
        samples: Sequence | deque,
        band: Optional[tuple[float, float]] = None,
        *,
        y_max: Optional[float] = None,
    ) -> None:
        if not samples:
            return
        xs = [s[0] for s in samples]
        ys = [s[1] for s in samples]
        sets = [s[2] for s in samples]
        dus = [s[3] for s in samples]
        phases = [s[4] if len(s) > 4 else "" for s in samples]
        self._current_set = next(
            (float(v) for v in reversed(sets) if float(v) == float(v)), None
        )
        self.line_t.set_data(xs, ys)
        self.line_set.set_data(xs, sets)
        self.line_du.set_data(xs, dus)

        if y_max is not None:
            self._y_max = max(float(y_max), 1.0)
        if self._user_ylim is not None:
            self._set_ylim_safe(self._user_ylim[0], self._user_ylim[1])
        else:
            finite = [float(v) for v in list(ys) + list(sets) if float(v) == float(v)]
            observed = max(finite, default=1.0)
            base = self._y_max if self._y_max is not None else 100.0
            # El eje automático solo aumenta, en saltos redondos, y conserva y=0.
            target = max(base, math.ceil((observed + 10.0) / 25.0) * 25.0)
            self._auto_y_top = max(self._auto_y_top, target)
            self._set_ylim_safe(0.0, self._auto_y_top)

        # Series en tiempo absoluto desde t=0. Zoom/pan del usuario se respeta;
        # si no hay zoom: techo fijo (locked) o crece desde 0 sin mover el origen.
        if self._user_xlim is not None:
            self._set_xlim_safe(self._user_xlim[0], self._user_xlim[1])
            self._apply_x_locator(max(self._user_xlim[1] - self._user_xlim[0], 1.0))
        elif self._x_locked:
            self._set_xlim_safe(0.0, self._x_span_s)
            self._apply_x_locator(self._x_span_s)
        else:
            t_end = self._auto_x_end(float(xs[-1]))
            self._set_xlim_safe(0.0, t_end)
            self._apply_x_locator(t_end)

        self._clear_overlays()
        cc = ui_theme.chart_colors()
        if band is not None:
            lo, hi = band
            self.ax.axhspan(lo, hi, color=cc["band"], alpha=0.15, zorder=1)
        fill_t = self.ax.fill_between(xs, ys, 0, color=cc["temp"], alpha=0.07,
                                      linewidth=0, zorder=2)
        fill_d = self.ax2.fill_between(xs, dus, 0, color=cc["duty"], alpha=0.09,
                                       linewidth=0, zorder=1)
        self._overlay_artists.extend([fill_t, fill_d])
        head = None
        for x, y in zip(reversed(xs), reversed(ys)):
            if float(y) == float(y):
                head = (x, y)
                break
        if head is not None:
            dot = self.ax.plot([head[0]], [head[1]], marker="o", markersize=5.0,
                               markerfacecolor=cc["temp"], markeredgecolor="#ffffff",
                               markeredgewidth=0.83, linestyle="None", zorder=8)
            self._overlay_artists.extend(dot)
        self._draw_event_markers(xs, ys, sets, dus, phases)
        self._apply_mpl_fonts()
        self.canvas.draw_idle()

    def reset_view(self) -> None:
        """Sale del zoom manual y vuelve a ejes automáticos anclados en cero."""
        self._user_xlim = None
        self._user_ylim = None
        self._apply_x_measures()
        self._set_ylim_safe(0.0, self._auto_y_top)
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.line_t.set_data([], [])
        self.line_set.set_data([], [])
        self.line_du.set_data([], [])
        self._clear_overlays()
        self._event_signature = ()
        self.event_table.set_rows([])
        self._user_xlim = None
        self._user_ylim = None
        if self._y_max is not None:
            self._auto_y_top = self._y_max
        else:
            self._auto_y_top = 100.0
        self._set_ylim_safe(0, self._auto_y_top)
        self._apply_x_measures()
        self.canvas.draw_idle()
