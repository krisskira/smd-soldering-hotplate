"""Gráfico T / objetivo / potencia embebido en Tk."""

from __future__ import annotations

from collections import deque
from typing import Callable, List, Optional, Sequence, Tuple

import tkinter as tk
from tkinter import ttk

from constants import CHART_X_SPAN_S


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
    xs: Sequence[float], dus: Sequence[float], thr: float = 50.0
) -> List[Tuple[float, str]]:
    """Bordes de calentador: (t, 'on'|'off')."""
    out: List[Tuple[float, str]] = []
    prev: Optional[bool] = None
    for t, du in zip(xs, dus):
        tf, df = float(t), float(du)
        if df != df:
            continue
        on = df > thr
        if prev is None:
            prev = on
            continue
        if on != prev:
            out.append((tf, "on" if on else "off"))
            prev = on
    return out


class LiveChart:
    def __init__(
        self,
        parent: ttk.Frame,
        *,
        title: str = "Curva en vivo",
        on_export: Optional[Callable[[], None]] = None,
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
        self._x_locked = bool(x_locked)
        self._x_span_s = max(float(x_span_s), 1.0)
        self._overlay_artists: list = []
        self._frame = ttk.LabelFrame(parent, text=title)
        self._frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        hdr = ttk.Frame(self._frame)
        hdr.pack(fill=tk.X, padx=4, pady=(2, 0))

        self.var_phase = tk.StringVar(value="Fase: —")
        self.var_temp = tk.StringVar(value="T medida: —")
        if show_live_info:
            info = ttk.Frame(hdr)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(
                info, textvariable=self.var_phase, font=("", 11, "bold")
            ).pack(side=tk.LEFT, padx=(0, 16))
            ttk.Label(
                info, textvariable=self.var_temp, font=("", 11, "bold")
            ).pack(side=tk.LEFT)
        else:
            ttk.Frame(hdr).pack(side=tk.LEFT, fill=tk.X, expand=True)

        if on_clear is not None:
            ttk.Button(hdr, text="Limpiar gráfico", command=on_clear).pack(
                side=tk.RIGHT, padx=(4, 0)
            )
        if on_export is not None:
            ttk.Button(hdr, text="Exportar CSV", command=on_export).pack(
                side=tk.RIGHT, padx=(4, 0)
            )
        if on_stop is not None:
            ttk.Button(hdr, text="Detener", command=on_stop).pack(
                side=tk.RIGHT, padx=(4, 0)
            )
        if on_start is not None:
            ttk.Button(hdr, text=start_label, command=on_start).pack(
                side=tk.RIGHT, padx=(4, 0)
            )

        self.fig = Figure(figsize=figsize, dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.ax.set_xlabel("Tiempo (s)")
        self.ax.set_ylabel("Temperatura (°C)")
        self.ax2.set_ylabel("Potencia calentador (%)")
        self.ax2.set_ylim(0, 110)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, self._x_span_s)
        self._apply_x_measures()
        self.ax.grid(True, which="major", linestyle="-", linewidth=0.6, alpha=0.35)
        self.ax.minorticks_on()
        self.ax.grid(True, which="minor", linestyle=":", linewidth=0.4, alpha=0.2)
        self.ax.set_axisbelow(True)

        (self.line_t,) = self.ax.plot(
            [],
            [],
            label="Temperatura medida (°C)",
            color="#c0392b",
            linewidth=1.8,
        )
        (self.line_set,) = self.ax.plot(
            [],
            [],
            label="Temperatura objetivo / SET (°C)",
            color="#2980b9",
            linestyle="--",
            linewidth=1.4,
        )
        (self.line_du,) = self.ax2.plot(
            [],
            [],
            label="Potencia calentador DU (%)",
            color="#27ae60",
            alpha=0.65,
            linewidth=1.2,
        )
        # Placeholders para leyenda de marcadores
        self._mark_up = Line2D(
            [],
            [],
            linestyle="None",
            marker="^",
            color="#8e44ad",
            markersize=7,
            label="Cruce T↑SET",
        )
        self._mark_down = Line2D(
            [],
            [],
            linestyle="None",
            marker="v",
            color="#d35400",
            markersize=7,
            label="Cruce T↓SET",
        )
        self._mark_on = Line2D(
            [],
            [],
            linestyle="None",
            marker="|",
            color="#27ae60",
            markersize=10,
            markeredgewidth=2,
            label="PTC ON",
        )
        self._mark_off = Line2D(
            [],
            [],
            linestyle="None",
            marker="|",
            color="#7f8c8d",
            markersize=10,
            markeredgewidth=2,
            label="PTC OFF",
        )
        self._handles = [
            self.line_t,
            self.line_set,
            self.line_du,
            self._mark_up,
            self._mark_down,
            self._mark_on,
            self._mark_off,
        ]
        self.fig.legend(
            self._handles,
            [h.get_label() for h in self._handles],
            loc="lower center",
            ncol=4,
            fontsize=7,
            frameon=True,
            fancybox=False,
            bbox_to_anchor=(0.5, 0.0),
        )
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.95, bottom=0.28)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self._frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def set_live_info(self, phase: str, temp_c: str) -> None:
        self.var_phase.set(f"Fase: {phase}")
        self.var_temp.set(f"T medida: {temp_c}")

    def _apply_x_measures(self) -> None:
        from matplotlib.ticker import FuncFormatter, MultipleLocator

        # Siempre anclado en t=0; no desplazar el origen.
        self.ax.set_xlim(0, self._x_span_s)
        self.ax.xaxis.set_major_locator(MultipleLocator(_x_major_step(self._x_span_s)))
        self.ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _pos: f"{int(round(v))}")
        )

    def set_x_span(self, span_s: float) -> None:
        """Fija el largo del eje X y sus marcas a `span_s` segundos."""
        self._x_span_s = max(float(span_s), 1.0)
        self._x_locked = True
        self._apply_x_measures()
        self.canvas.draw_idle()

    def set_y_max(self, y_max: float) -> None:
        self._y_max = max(float(y_max), 1.0)
        self.ax.set_ylim(0, self._y_max)
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

    def _draw_event_markers(
        self,
        xs: Sequence[float],
        ys: Sequence[float],
        sets: Sequence[float],
        dus: Sequence[float],
    ) -> None:
        crosses = _crossings_t_set(xs, ys, sets)
        edges = _duty_edges(xs, dus)

        up = [(t, y) for t, y, k in crosses if k == "up"]
        down = [(t, y) for t, y, k in crosses if k == "down"]
        if up:
            sc = self.ax.scatter(
                [p[0] for p in up],
                [p[1] for p in up],
                marker="^",
                s=36,
                c="#8e44ad",
                zorder=5,
                label="_nolegend_",
            )
            self._overlay_artists.append(sc)
        if down:
            sc = self.ax.scatter(
                [p[0] for p in down],
                [p[1] for p in down],
                marker="v",
                s=36,
                c="#d35400",
                zorder=5,
                label="_nolegend_",
            )
            self._overlay_artists.append(sc)

        # Etiquetas de tiempo en cruces (limitar densidad)
        annotate = len(crosses) <= 28
        if annotate:
            for t, y, _k in crosses:
                txt = self.ax.annotate(
                    f"{t:.0f}s",
                    xy=(t, y),
                    xytext=(0, 8),
                    textcoords="offset points",
                    fontsize=6,
                    color="#2c3e50",
                    ha="center",
                    zorder=6,
                )
                self._overlay_artists.append(txt)

        y_lo, y_hi = self.ax.get_ylim()
        for t, kind in edges:
            color = "#27ae60" if kind == "on" else "#7f8c8d"
            ln = self.ax.axvline(
                t, color=color, alpha=0.35, linewidth=1.0, zorder=2
            )
            self._overlay_artists.append(ln)
            # marca en el borde inferior del eje T
            mk = self.ax.plot(
                [t],
                [y_lo + 0.02 * (y_hi - y_lo)],
                marker="|",
                markersize=12,
                markeredgewidth=2.0,
                color=color,
                linestyle="None",
                zorder=5,
            )
            self._overlay_artists.extend(mk)

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
        self.line_t.set_data(xs, ys)
        self.line_set.set_data(xs, sets)
        self.line_du.set_data(xs, dus)

        if y_max is not None:
            self._y_max = max(float(y_max), 1.0)
        if self._y_max is not None:
            self.ax.set_ylim(0, self._y_max)
        else:
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=True)

        # Origen fijo en 0. Si x_locked, no crecer; si no, crecer el techo sin mover el 0.
        if self._x_locked:
            self.ax.set_xlim(0, self._x_span_s)
        else:
            t_end = max(float(xs[-1]), self._x_span_s)
            self.ax.set_xlim(0, t_end)
        self.ax2.set_ylim(0, 110)

        self._clear_overlays()
        if band is not None:
            lo, hi = band
            self.ax.axhspan(lo, hi, color="#f1c40f", alpha=0.15)
        self._draw_event_markers(xs, ys, sets, dus)
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.line_t.set_data([], [])
        self.line_set.set_data([], [])
        self.line_du.set_data([], [])
        self._clear_overlays()
        if self._y_max is not None:
            self.ax.set_ylim(0, self._y_max)
        self._apply_x_measures()
        self.ax2.set_ylim(0, 110)
        self.var_phase.set("Fase: —")
        self.var_temp.set("T medida: —")
        self.canvas.draw_idle()
