"""Gráfico T / objetivo / potencia embebido en Tk."""

from __future__ import annotations

from collections import deque
from typing import Callable, Optional, Sequence

import tkinter as tk
from tkinter import ttk

from constants import CHART_X_SPAN_S


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
    ) -> None:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure

        self._y_max: Optional[float] = None
        self._x_span_s = max(float(x_span_s), 1.0)
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

        # pack RIGHT: primero el que queda más a la derecha
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
        self._handles = [self.line_t, self.line_set, self.line_du]
        self.fig.legend(
            self._handles,
            [h.get_label() for h in self._handles],
            loc="lower center",
            ncol=3,
            fontsize=8,
            frameon=True,
            fancybox=False,
            bbox_to_anchor=(0.5, 0.0),
        )
        self.fig.subplots_adjust(left=0.08, right=0.92, top=0.95, bottom=0.22)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self._frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def set_live_info(self, phase: str, temp_c: str) -> None:
        self.var_phase.set(f"Fase: {phase}")
        self.var_temp.set(f"T medida: {temp_c}")

    def set_y_max(self, y_max: float) -> None:
        self._y_max = max(float(y_max), 1.0)
        self.ax.set_ylim(0, self._y_max)
        self.canvas.draw_idle()

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
        self.line_t.set_data(xs, [s[1] for s in samples])
        self.line_set.set_data(xs, [s[2] for s in samples])
        self.line_du.set_data(xs, [s[3] for s in samples])

        if y_max is not None:
            self._y_max = max(float(y_max), 1.0)
        if self._y_max is not None:
            self.ax.set_ylim(0, self._y_max)
        else:
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=True)

        # Mantener al menos CHART_X_SPAN_S; crecer si la curva supera ese tramo.
        t_end = max(float(xs[-1]), self._x_span_s)
        self.ax.set_xlim(0, t_end)
        self.ax2.set_ylim(0, 110)

        for coll in list(self.ax.collections):
            coll.remove()
        if band is not None:
            lo, hi = band
            self.ax.axhspan(lo, hi, color="#f1c40f", alpha=0.15)
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.line_t.set_data([], [])
        self.line_set.set_data([], [])
        self.line_du.set_data([], [])
        for coll in list(self.ax.collections):
            coll.remove()
        if self._y_max is not None:
            self.ax.set_ylim(0, self._y_max)
        self.ax.set_xlim(0, self._x_span_s)
        self.ax2.set_ylim(0, 110)
        self.var_phase.set("Fase: —")
        self.var_temp.set("T medida: —")
        self.canvas.draw_idle()
