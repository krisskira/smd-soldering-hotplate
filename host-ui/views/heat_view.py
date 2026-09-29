"""Pestaña HEAT: perfil y estado en una fila · curva y registro debajo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

import theme as ui_theme
from chart import LiveChart
from views.layout import add_panel, content_row
from views.status_panel import StatusPanel

# Margen del eje Y de temperatura por encima del escalón más alto activo.
CHART_HEAT_Y_MARGIN_C = 50.0

if TYPE_CHECKING:
    from controller import AppController


class HeatView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self._heat_running = False
        self._hi = (0, 0, 0)

        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=(8, 2))
        self.btn_heat = ttk.Button(
            top, text="Iniciar HEAT", command=ctrl.toggle_heat, style="Accent.TButton"
        )
        self.btn_heat.pack(side=tk.LEFT, padx=(0, 8))
        self.banner = tk.Label(top, text="", anchor=tk.W)
        self.banner.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row = content_row(parent)
        self._build_ramps_panel(row)
        self.status = StatusPanel(row)
        add_panel(row, self._ramps_frame)
        add_panel(row, self.status.frame)

        chart_host = ttk.Frame(parent)
        chart_host.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 6))
        self.chart = LiveChart(
            chart_host,
            title="Curva en vivo",
            on_export=ctrl.export_csv,
            on_export_events=ctrl.export_heat_events,
            on_clear=ctrl.clear_plot,
            figsize=(8.6, 3.4),
            x_span_s=self.planned_x_span(),
            x_locked=False,
        )
        self._sync_chart_ylim()
        self.apply_theme()

    def _build_ramps_panel(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="Soldering Profile")
        self._ramps_frame = box
        ttk.Label(
            box,
            text="Escalones contiguos desde la rampa 1. Guardar envía el perfil; Leer pide $R.",
            style="Muted.TLabel",
            wraplength=420,
        ).pack(anchor=tk.W, padx=8, pady=(6, 2))

        hdr = ttk.Frame(box)
        hdr.pack(fill=tk.X, padx=8)
        for col, title in enumerate(("Usar", "Escalón", "°C", "s", "")):
            ttk.Label(hdr, text=title, style="Muted.TLabel").grid(
                row=0, column=col, sticky=tk.W, padx=2
            )

        self.ramp_active: list[tk.BooleanVar] = []
        self.ramp_temp: list[tk.StringVar] = []
        self.ramp_hold: list[tk.StringVar] = []
        self.ramp_row_labels: list[ttk.Label] = []
        self._ramp_checks: list[ttk.Checkbutton] = []

        body = ttk.Frame(box)
        body.pack(padx=8, pady=4)
        for i in range(4):
            av = tk.BooleanVar(value=(i < 2))
            tv = tk.StringVar(value=str(100 + 25 * i))
            hv = tk.StringVar(value="60")
            self.ramp_active.append(av)
            self.ramp_temp.append(tv)
            self.ramp_hold.append(hv)
            cb = ttk.Checkbutton(body, variable=av)
            if i == 0:
                av.set(True)
                cb.state(["disabled"])
            else:
                cb.config(command=self._on_ramp_active_toggle)
            cb.grid(row=i, column=0, padx=2, pady=2)
            self._ramp_checks.append(cb)
            rl = ttk.Label(body, text=f"Rampa {i + 1}", width=10)
            rl.grid(row=i, column=1, sticky=tk.W)
            self.ramp_row_labels.append(rl)
            ttk.Entry(body, textvariable=tv, width=8, justify=tk.RIGHT).grid(
                row=i, column=2, padx=4, pady=2
            )
            ttk.Entry(body, textvariable=hv, width=8, justify=tk.RIGHT).grid(
                row=i, column=3, padx=4, pady=2
            )
            ttk.Button(
                body, text="Guardar", command=lambda idx=i: self._ctrl.write_ramp(idx)
            ).grid(row=i, column=4, padx=2)

        foot = ttk.Frame(box)
        foot.pack(fill=tk.X, padx=8, pady=(2, 8))
        ttk.Button(foot, text="Leer rampas", command=self._ctrl.read_ramps).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(
            foot, text="Guardar rampas activas", command=self._ctrl.write_all_ramps
        ).pack(side=tk.LEFT)

        for v in self.ramp_temp + self.ramp_hold + self.ramp_active:
            v.trace_add("write", lambda *_: self._on_ramp_edit())

    def _on_ramp_active_toggle(self) -> None:
        """Fuerza prefijo contiguo: rampa 1 siempre ON; sin huecos."""
        self.ramp_active[0].set(True)
        saw_off = False
        for i in range(1, 4):
            if saw_off:
                self.ramp_active[i].set(False)
            elif not self.ramp_active[i].get():
                saw_off = True
        self._on_ramp_edit()

    def set_heat_running(self, running: bool) -> None:
        self._heat_running = bool(running)
        self.btn_heat.config(
            text=("Detener HEAT" if self._heat_running else "Iniciar HEAT")
        )

    def is_heat_running(self) -> bool:
        return self._heat_running

    def _on_ramp_edit(self) -> None:
        self.sync_chart_x()
        self._sync_chart_ylim()
        self.refresh_objetivo()

    def ramp_snapshot(self) -> tuple[list[bool], list[str], list[str]]:
        return (
            [v.get() for v in self.ramp_active],
            [v.get() for v in self.ramp_temp],
            [v.get() for v in self.ramp_hold],
        )

    def planned_x_span(self) -> float:
        """Ventana del eje X según el perfil: mesetas, subida y un margen de enfriamiento."""
        active, _temps, holds = self.ramp_snapshot()
        hold = 0.0
        steps = 0
        for on, raw in zip(active, holds):
            if not on:
                continue
            steps += 1
            try:
                hold += max(float(raw), 0.0)
            except ValueError:
                hold += 60.0
        span = hold + 90.0 * max(steps, 1) + 180.0
        return max(300.0, min(span, 7200.0))

    def sync_chart_x(self) -> None:
        if hasattr(self, "chart"):
            self.chart.set_x_window(self.planned_x_span(), locked=False)

    def ramp_ymax(self) -> float:
        """Tope del eje Y: max(°C de rampas activas) + 50 °C."""
        active, temps, _ = self.ramp_snapshot()
        vals: list[float] = []
        for on, raw in zip(active, temps):
            if not on:
                continue
            try:
                vals.append(float(raw))
            except ValueError:
                pass
        if not vals:
            for raw in temps:
                try:
                    vals.append(float(raw))
                except ValueError:
                    pass
        base = max(vals) if vals else 100.0
        return base + CHART_HEAT_Y_MARGIN_C

    def sync_chart_ylim(self) -> None:
        if hasattr(self, "chart"):
            self.chart.set_y_max(self.ramp_ymax())

    def _sync_chart_ylim(self) -> None:
        self.sync_chart_ylim()

    def apply_ramps_frame(self, n: int, steps: list[tuple[int, int]]) -> None:
        """Aplica `$R`: N define activos; °C/hold de cada hueco."""
        n = max(0, min(int(n), 4))
        for i in range(4):
            if i < len(steps):
                temp, hold = steps[i]
                if temp > 0:
                    self.ramp_temp[i].set(str(temp))
                if hold > 0:
                    self.ramp_hold[i].set(str(hold))
            self.ramp_active[i].set(i < n)
        self.ramp_active[0].set(True)
        self.sync_chart_x()
        self._sync_chart_ylim()
        self.refresh_objetivo()

    def apply_hp(self, fields: dict[str, Any], delay_cfg: str | None) -> None:
        self.status.apply_hp(fields, delay_cfg)
        self._update_fault_banner(fields.get("FL", 0))
        self.refresh_objetivo()
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        self.highlight_ramp(int(fields.get("P", 0)), int(fields.get("A", 0)), ri)

    def _update_fault_banner(self, fl: Any) -> None:
        try:
            fault = int(fl) != 0
        except (TypeError, ValueError):
            fault = bool(fl)
        if fault:
            self.set_banner("Corte por falla — salidas desactivadas", "#c0392b")
        else:
            cur = self.banner.cget("text")
            if str(cur).startswith("Corte por falla"):
                self.set_banner("")

    def refresh_objetivo(self, *_args, **_kwargs) -> None:
        """La consigna vive en el panel de estado y en la curva."""
        self._sync_chart_ylim()

    def highlight_ramp(self, prog: int, phase: int, ri: int) -> None:
        self._hi = (prog, phase, ri)
        for i, lab in enumerate(self.ramp_row_labels):
            on = prog == 1 and phase in (4, 5) and i == ri
            lab.config(
                text=("► Rampa " if on else "Rampa ") + str(i + 1),
                font=self._ramp_font(on),
            )

    def _ramp_font(self, active: bool) -> tuple:
        t = ui_theme.get()
        fam = ui_theme.ui_family()
        size = int(t["body_size"])
        return (fam, size, "bold" if active else "normal")

    def set_banner(self, text: str, color: str = "#a00") -> None:
        self.banner.config(text=text, fg=color)

    def apply_theme(self) -> None:
        t = ui_theme.get()
        self.banner.configure(
            font=ui_theme.font_tuple("body_size"),
            bg=ui_theme.surface_bg(),
        )
        if not self.banner.cget("text"):
            self.banner.configure(fg=t["body_color"])
        self.status.apply_theme()
        prog, phase, ri = self._hi
        self.highlight_ramp(prog, phase, ri)
        if hasattr(self, "chart"):
            self.chart.apply_theme()

    def has_active_ramps(self) -> bool:
        self.ramp_active[0].set(True)
        return True
