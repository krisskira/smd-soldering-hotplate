"""Gráfico T / objetivo / potencia embebido en Tk."""

from __future__ import annotations

import math
from collections import deque
from typing import Callable, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import ttk

from constants import CHART_X_SPAN_S
import theme as ui_theme


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


_PHASE_COLORS = (
    "#0e6655",
    "#1a5276",
    "#6c3483",
    "#b9770e",
    "#1b4f72",
    "#7b241c",
)
_EVENT_LIMIT = 300


def _phase_color(name: str) -> str:
    """Color estable por nombre, independiente del orden o del zoom."""
    idx = sum(name.encode("utf-8")) % len(_PHASE_COLORS)
    return _PHASE_COLORS[idx]


class LiveChart:
    def __init__(
        self,
        parent: ttk.Frame,
        *,
        title: str = "Curva en vivo",
        on_export: Optional[Callable[[], None]] = None,
        on_export_events: Optional[Callable[[], None]] = None,
        on_clear: Optional[Callable[[], None]] = None,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        figsize: tuple[float, float] = (7, 2.8),
        show_live_info: bool = False,
        start_label: str = "Iniciar",
        x_span_s: float = CHART_X_SPAN_S,
        x_locked: bool = True,
    ) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        from matplotlib.lines import Line2D

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
        self._frame = ttk.LabelFrame(parent, text=title)
        self._frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        hdr = ttk.Frame(self._frame)
        hdr.pack(fill=tk.X, padx=6, pady=(4, 0))

        self.var_phase = tk.StringVar(value="Fase: —")
        self.var_temp = tk.StringVar(value="T medida: —")
        if show_live_info:
            info = ttk.Frame(hdr)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info, textvariable=self.var_phase).pack(side=tk.LEFT, padx=(0, 16))
            ttk.Label(info, textvariable=self.var_temp).pack(side=tk.LEFT)
        else:
            ttk.Frame(hdr).pack(side=tk.LEFT, fill=tk.X, expand=True)

        if on_clear is not None:
            ttk.Button(hdr, text="Limpiar", command=on_clear).pack(side=tk.RIGHT, padx=(4, 0))
        ttk.Button(hdr, text="Restablecer zoom", command=self.reset_view).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        if on_export is not None:
            ttk.Button(hdr, text="Exportar muestras", command=on_export).pack(
                side=tk.RIGHT, padx=(4, 0)
            )
        if on_stop is not None:
            ttk.Button(hdr, text="Detener", command=on_stop).pack(side=tk.RIGHT, padx=(4, 0))
        if on_start is not None:
            ttk.Button(hdr, text=start_label, command=on_start).pack(
                side=tk.RIGHT, padx=(4, 0)
            )

        self._legend_host = ttk.LabelFrame(self._frame, text="Leyenda")
        self._legend_host.pack(fill=tk.X, padx=6, pady=(6, 0))
        self._legend_bits: list[tuple[tk.Canvas, str, str]] = []

        self._paned = ttk.Panedwindow(self._frame, orient=tk.HORIZONTAL)
        self._paned.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        plot_pane = ttk.Frame(self._paned)
        events = ttk.LabelFrame(self._paned, text="Registro de eventos")
        self._paned.add(plot_pane, weight=3)
        self._paned.add(events, weight=2)
        self._sash_set = False
        self._paned.bind("<Map>", lambda _e: self._frame.after(80, self._place_sash), add="+")
        self._paned.bind("<Configure>", self._place_sash, add="+")

        self.fig = Figure(figsize=figsize, dpi=100)
        self.fig.patch.set_facecolor(ui_theme.surface_bg())
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax2.set_ylabel("Potencia calentador (%)")
        self.ax2.set_ylim(0, 110)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self._x_span_s)
        self._apply_x_measures()
        self.ax.callbacks.connect("xlim_changed", self._on_xlim_changed)
        self.ax.callbacks.connect("ylim_changed", self._on_ylim_changed)
        self.ax.grid(True, which="major", linestyle="-", linewidth=0.6, alpha=0.35)
        self.ax.minorticks_on()
        self.ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.2)
        self.ax.set_axisbelow(True)

        cc = ui_theme.chart_colors()
        self.ax.set_facecolor(cc["face"])
        (self.line_t,) = self.ax.plot(
            [],
            [],
            label="Temperatura medida (°C)",
            color=cc["temp"],
            linewidth=1.8,
        )
        (self.line_set,) = self.ax.plot(
            [],
            [],
            label="Temperatura objetivo / SET (°C)",
            color=cc["set"],
            linestyle="--",
            linewidth=1.4,
        )
        (self.line_du,) = self.ax2.plot(
            [],
            [],
            label="Potencia calentador DU (%)",
            color=cc["duty"],
            alpha=0.65,
            linewidth=1.2,
        )
        # Placeholders para leyenda de marcadores
        self._mark_up = Line2D(
            [],
            [],
            linestyle="None",
            marker="^",
            color=cc["mark_up"],
            markersize=9,
            label="Cruce T sube el SET",
        )
        self._mark_down = Line2D(
            [],
            [],
            linestyle="None",
            marker="v",
            color=cc["mark_down"],
            markersize=9,
            label="Cruce T baja el SET",
        )
        self._mark_on = Line2D(
            [],
            [],
            linestyle="None",
            marker="|",
            color=cc["mark_on"],
            markersize=14,
            markeredgewidth=2.4,
            label="Calentador ON",
        )
        self._mark_off = Line2D(
            [],
            [],
            linestyle="None",
            marker="|",
            color=cc["mark_off"],
            markersize=14,
            markeredgewidth=2.4,
            label="Calentador OFF",
        )
        self._mark_peak = Line2D(
            [],
            [],
            linestyle="None",
            marker="D",
            color=cc["mark_peak"],
            markersize=8,
            label="Cresta (máximo)",
        )
        self._handles = [
            self.line_t,
            self.line_set,
            self.line_du,
            self._mark_up,
            self._mark_down,
            self._mark_peak,
            self._mark_on,
            self._mark_off,
        ]
        self._build_legend()
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.97, bottom=0.10)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_pane)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=(2, 0))
        try:
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

            self._toolbar = NavigationToolbar2Tk(self.canvas, plot_pane, pack_toolbar=False)
            self._toolbar.update()
            self._toolbar.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=(0, 2))
        except Exception:
            self._toolbar = None

        bar = ttk.Frame(events)
        bar.pack(fill=tk.X, padx=6, pady=(4, 0))
        if on_export_events is not None:
            ttk.Button(bar, text="Exportar registro", command=on_export_events).pack(
                side=tk.RIGHT
            )

        table = ttk.Frame(events)
        table.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.event_log = ttk.Treeview(
            table,
            columns=("time", "duration", "temp", "event"),
            show="headings",
            height=6,
            selectmode="browse",
        )
        self.event_log.heading("time", text="Tiempo")
        self.event_log.heading("duration", text="Dur.")
        self.event_log.heading("temp", text="T °C")
        self.event_log.heading("event", text="Evento")
        self.event_log.column("time", width=58, minwidth=50, anchor=tk.E, stretch=False)
        self.event_log.column(
            "duration", width=54, minwidth=46, anchor=tk.E, stretch=False
        )
        self.event_log.column("temp", width=58, minwidth=50, anchor=tk.E, stretch=False)
        self.event_log.column("event", width=130, minwidth=100, anchor=tk.W)
        scroll = ttk.Scrollbar(table, orient=tk.VERTICAL, command=self.event_log.yview)
        self.event_log.configure(yscrollcommand=scroll.set)
        self.event_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.event_log.tag_configure("phase", foreground=cc["phase"])
        self.event_log.tag_configure("up", foreground=cc["mark_up"])
        self.event_log.tag_configure("down", foreground=cc["mark_down"])
        self.event_log.tag_configure("on", foreground=cc["mark_on"])
        self.event_log.tag_configure("off", foreground=cc["mark_off"])
        self.event_log.tag_configure("peak", foreground=cc["mark_peak"])

    def set_live_info(self, phase: str, temp_c: str) -> None:
        self.var_phase.set(f"Fase: {phase}")
        self.var_temp.set(f"T medida: {temp_c}")

    def _build_legend(self) -> None:
        """Leyenda fuera de la curva, en dos filas, para dejarle todo el alto al eje."""
        items = (
            ("line", "temp", "Temperatura medida"),
            ("dashed", "set", "SET"),
            ("line", "duty", "Potencia"),
            ("peak", "mark_peak", "Cresta"),
            ("up", "mark_up", "Cruce ↑"),
            ("down", "mark_down", "Cruce ↓"),
            ("tick", "mark_on", "Calentador ON"),
            ("tick", "mark_off", "Calentador OFF"),
        )
        for index, (kind, key, text) in enumerate(items):
            cell = ttk.Frame(self._legend_host)
            cell.grid(row=index // 4, column=index % 4, sticky=tk.W, padx=8, pady=3)
            swatch = tk.Canvas(
                cell,
                width=28,
                height=14,
                highlightthickness=0,
                background=ui_theme.surface_bg(),
            )
            swatch.pack(side=tk.LEFT, padx=(0, 4))
            ttk.Label(cell, text=text).pack(side=tk.LEFT)
            self._legend_bits.append((swatch, kind, key))
        for col in range(4):
            self._legend_host.columnconfigure(col, weight=1)
        self._paint_legend()

    def _paint_legend(self) -> None:
        cc = ui_theme.chart_colors()
        bg = ui_theme.surface_bg()
        for swatch, kind, key in self._legend_bits:
            swatch.configure(background=bg)
            swatch.delete("all")
            color = cc[key]
            width, height = 28, 14
            mid = height / 2
            if kind == "line":
                swatch.create_line(2, mid, width - 2, mid, fill=color, width=2)
            elif kind == "dashed":
                swatch.create_line(
                    2, mid, width - 2, mid, fill=color, width=2, dash=(3, 2)
                )
            elif kind == "up":
                swatch.create_polygon(
                    width / 2, 2, width - 4, height - 2, 4, height - 2,
                    fill=color, outline=color,
                )
            elif kind == "down":
                swatch.create_polygon(
                    4, 2, width - 4, 2, width / 2, height - 2,
                    fill=color, outline=color,
                )
            elif kind == "peak":
                swatch.create_polygon(
                    width / 2, 2, width - 3, mid, width / 2, height - 2, 3, mid,
                    fill=color, outline=color,
                )
            else:
                swatch.create_line(width / 2, 1, width / 2, height - 1, fill=color, width=3)

    def _place_sash(self, _event=None) -> None:
        if self._sash_set:
            return
        width = self._paned.winfo_width()
        if width < 520:
            return
        self._sash_set = True
        # Tabla al ancho de sus columnas (+ scroll y márgenes); el resto para la curva.
        table_w = 58 + 54 + 58 + 150 + 30
        try:
            self._paned.sashpos(0, max(int(width * 0.55), width - table_w))
        except Exception:
            self._sash_set = False

    def event_rows(self) -> list[tuple[str, str, str, str]]:
        """Filas visibles del registro: tiempo, duración, temperatura, evento."""
        out: list[tuple[str, str, str, str]] = []
        for iid in self.event_log.get_children():
            vals = self.event_log.item(iid, "values")
            if len(vals) >= 4:
                out.append((str(vals[0]), str(vals[1]), str(vals[2]), str(vals[3])))
        return out

    def apply_theme(self) -> None:
        """Reaplica colores de series/marcadores y la fuente de los ejes."""
        cc = ui_theme.chart_colors()
        self.fig.patch.set_facecolor(ui_theme.surface_bg())
        self.ax.set_facecolor(cc["face"])
        self.line_t.set_color(cc["temp"])
        self.line_set.set_color(cc["set"])
        self.line_du.set_color(cc["duty"])
        self._mark_up.set_color(cc["mark_up"])
        self._mark_down.set_color(cc["mark_down"])
        self._mark_on.set_color(cc["mark_on"])
        self._mark_off.set_color(cc["mark_off"])
        self._mark_peak.set_color(cc["mark_peak"])
        self._paint_legend()
        self.event_log.tag_configure("phase", foreground=cc["phase"])
        self.event_log.tag_configure("up", foreground=cc["mark_up"])
        self.event_log.tag_configure("down", foreground=cc["mark_down"])
        self.event_log.tag_configure("on", foreground=cc["mark_on"])
        self.event_log.tag_configure("off", foreground=cc["mark_off"])
        self.event_log.tag_configure("peak", foreground=cc["mark_peak"])
        self._apply_mpl_fonts()
        self.canvas.draw_idle()

    def _apply_mpl_fonts(self) -> None:
        t = ui_theme.get()
        fam = ui_theme.ui_family()
        size = max(8, int(t["body_size"]) - 1)
        for axis in (self.ax, self.ax2):
            axis.tick_params(labelsize=size)
            axis.xaxis.label.set_size(size)
            axis.yaxis.label.set_size(size)
            for label in (axis.xaxis.label, axis.yaxis.label):
                try:
                    label.set_fontname(fam)
                except Exception:
                    pass
            for label in axis.get_xticklabels() + axis.get_yticklabels():
                label.set_fontsize(size)
                try:
                    label.set_fontname(fam)
                except Exception:
                    pass

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
            self.ax.set_ylim(y0, y1)
        finally:
            self._applying_ylim = False

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
        from matplotlib.ticker import FuncFormatter, MultipleLocator

        self.ax.xaxis.set_major_locator(MultipleLocator(_x_major_step(max(span_s, 1.0))))
        self.ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _pos: f"{int(round(v))}")
        )

    def set_y_max(self, y_max: float) -> None:
        self._y_max = max(float(y_max), 1.0)
        if self._user_ylim is None:
            self._auto_y_top = max(self._auto_y_top, self._y_max)
            self._set_ylim_safe(0, self._auto_y_top)
        self.canvas.draw_idle()

    def _clear_overlays(self) -> None:
        for coll in list(self.ax.collections):
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
            tag = f"phase:{name}"
            self.event_log.tag_configure(tag, foreground=_phase_color(name))
            rows.append(
                (t0, max(t1 - t0, 0.0), self._temp_at(xs, ys, t0), f"Fase: {name}", tag)
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
        for item in self.event_log.get_children():
            self.event_log.delete(item)
        for t, duration, temp, text, tag in rows:
            self.event_log.insert(
                "",
                tk.END,
                values=(
                    self._fmt_time(t),
                    self._fmt_time(duration) if duration > 0 else "—",
                    f"{temp:.1f}" if temp == temp else "—",
                    text,
                ),
                tags=(tag,),
            )
        children = self.event_log.get_children()
        if children:
            self.event_log.see(children[-1])

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
            sc = self.ax.scatter(
                [p[0] for p in up],
                [p[1] for p in up],
                marker="^",
                s=64,
                c=cc["mark_up"],
                zorder=5,
                label="_nolegend_",
            )
            self._overlay_artists.append(sc)
        if down:
            sc = self.ax.scatter(
                [p[0] for p in down],
                [p[1] for p in down],
                marker="v",
                s=64,
                c=cc["mark_down"],
                zorder=5,
                label="_nolegend_",
            )
            self._overlay_artists.append(sc)

        if crests:
            sc = self.ax.scatter(
                [p[0] for p in crests],
                [p[1] for p in crests],
                marker="D",
                s=42,
                c=cc["mark_peak"],
                edgecolors="white",
                linewidths=0.6,
                zorder=6,
                label="_nolegend_",
            )
            self._overlay_artists.append(sc)

        y_lo, y_hi = self.ax.get_ylim()
        for t, kind in edges:
            color = cc["mark_on"] if kind == "on" else cc["mark_off"]
            ln = self.ax.axvline(
                t, color=color, alpha=0.55, linewidth=1.15, zorder=2
            )
            self._overlay_artists.append(ln)
            mk = self.ax.plot(
                [t],
                [y_lo + 0.015 * (y_hi - y_lo)],
                marker="|",
                markersize=16,
                markeredgewidth=2.4,
                color=color,
                linestyle="None",
                zorder=5,
            )
            self._overlay_artists.extend(mk)

        for t0, _t1, name in spans:
            color = _phase_color(name)
            ln = self.ax.axvline(
                t0,
                color=color,
                linestyle="--",
                linewidth=1.6,
                alpha=0.9,
                zorder=3,
            )
            self._overlay_artists.append(ln)
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
        self.line_t.set_data(xs, ys)
        self.line_set.set_data(xs, sets)
        self.line_du.set_data(xs, dus)

        if y_max is not None:
            self._y_max = max(float(y_max), 1.0)
        if self._user_ylim is not None:
            self._set_ylim_safe(self._user_ylim[0], self._user_ylim[1])
        else:
            finite = [
                float(v)
                for v in list(ys) + list(sets)
                if float(v) == float(v)
            ]
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
            self._apply_x_locator(
                max(self._user_xlim[1] - self._user_xlim[0], 1.0)
            )
        elif self._x_locked:
            self._set_xlim_safe(0.0, self._x_span_s)
            self._apply_x_locator(self._x_span_s)
        else:
            t_end = self._auto_x_end(float(xs[-1]))
            self._set_xlim_safe(0.0, t_end)
            self._apply_x_locator(t_end)
        self.ax2.set_ylim(0, 110)

        self._clear_overlays()
        if band is not None:
            lo, hi = band
            self.ax.axhspan(lo, hi, color=ui_theme.chart_colors()["band"], alpha=0.15)
        self._draw_event_markers(xs, ys, sets, dus, phases)
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
        for item in self.event_log.get_children():
            self.event_log.delete(item)
        self._user_xlim = None
        self._user_ylim = None
        if self._y_max is not None:
            self._auto_y_top = self._y_max
            self._set_ylim_safe(0, self._auto_y_top)
        else:
            self._auto_y_top = 100.0
            self._set_ylim_safe(0, self._auto_y_top)
        self._apply_x_measures()
        self.ax2.set_ylim(0, 110)
        self.var_phase.set("Fase: —")
        self.var_temp.set("T medida: —")
        self.canvas.draw_idle()
