"""Pestaña Proceso HEAT: fila rampas|estado (al contenido) · gráfica abajo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

import protocol as proto
from chart import LiveChart
from constants import CHART_HEAT_X_SPAN_S

if TYPE_CHECKING:
    from controller import AppController

# Dos columnas (sin precalentado/consigna)
STATUS_COLUMNS: list[list[tuple[str, list[tuple[str, str]]]]] = [
    [
        (
            "Programa",
            [
                ("PROG", "Programa en curso"),
                ("PHASE", "Fase actual"),
            ],
        ),
        (
            "Temperatura de la placa",
            [
                ("T", "Temperatura medida (°C)"),
            ],
        ),
        (
            "Tiempos",
            [
                ("DLY", "Espera antes de calentar (s)"),
                ("RUN", "Tiempo que queda en este paso (s)"),
                ("EL", "Tiempo desde el arranque (s)"),
            ],
        ),
    ],
    [
        (
            "Salidas",
            [
                ("DU", "Potencia del calentador (%)"),
                ("F", "Ventilador de enfriado"),
            ],
        ),
        (
            "Perfil de rampas",
            [
                ("RI", "Rampa activa ahora"),
            ],
        ),
        (
            "Seguridad",
            [
                ("FL", "Corte por falla"),
            ],
        ),
    ],
]


class HeatView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl

        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(top, text="Iniciar HEAT", command=ctrl.start_heat).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(top, text="Detener", command=ctrl.stop).pack(side=tk.LEFT, padx=2)

        self.banner = tk.Label(
            top, text="", font=("", 11, "bold"), fg="#a00", anchor=tk.W
        )
        self.banner.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(16, 0))

        # Fila 1: paneles al contenido, misma altura
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, padx=8, pady=4, anchor=tk.NW)
        row1.rowconfigure(0, weight=1)

        self._build_ramps_panel(row1)
        self._build_status_table(row1)

        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.chart = LiveChart(
            row2,
            title="Curva en vivo",
            on_export=ctrl.export_csv,
            on_clear=ctrl.clear_plot,
            figsize=(9, 4.2),
            show_live_info=True,
            x_span_s=CHART_HEAT_X_SPAN_S,
            x_locked=True,
        )
        self._sync_chart_ylim()

    def _build_status_table(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Estado del proceso")
        frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(4, 0), pady=0)
        self._status_frame = frame

        keys = [
            k
            for cols in STATUS_COLUMNS
            for _, rows in cols
            for k, _ in rows
        ]
        self.proc_vars = {k: tk.StringVar(value="—") for k in keys}

        body = ttk.Frame(frame)
        body.pack(anchor=tk.NW, padx=4, pady=4)
        for col_i, sections in enumerate(STATUS_COLUMNS):
            col = ttk.Frame(body)
            col.grid(row=0, column=col_i, sticky=tk.NW, padx=4, pady=2)
            row = 0
            for section_title, fields in sections:
                ttk.Label(
                    col, text=section_title, font=("", 10, "bold"), anchor=tk.W
                ).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=4, pady=(6, 0))
                row += 1
                ttk.Separator(col, orient=tk.HORIZONTAL).grid(
                    row=row, column=0, columnspan=2, sticky=tk.EW, padx=4, pady=(0, 4)
                )
                row += 1
                for key, label in fields:
                    ttk.Label(col, text=label, anchor=tk.W).grid(
                        row=row, column=0, sticky=tk.W, padx=(8, 8), pady=1
                    )
                    ttk.Label(
                        col,
                        textvariable=self.proc_vars[key],
                        anchor=tk.W,
                        font=("", 11),
                    ).grid(row=row, column=1, sticky=tk.W, padx=4, pady=1)
                    row += 1

    def _build_ramps_panel(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="Perfil de rampas (HEAT)")
        box.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 4), pady=0)
        self._ramps_frame = box
        ttk.Label(
            box,
            text=(
                "HEAT sigue estos escalones. El número en el equipo solo crece "
                "al guardar un índice más alto."
            ),
            wraplength=380,
        ).pack(anchor=tk.W, padx=6, pady=(4, 2))

        hdr = ttk.Frame(box)
        hdr.pack(fill=tk.X, padx=6)
        for col, t in enumerate(
            ("Usar", "Escalón", "Temperatura (°C)", "Tiempo (s)", "")
        ):
            ttk.Label(hdr, text=t).grid(row=0, column=col, sticky=tk.W, padx=2)

        self.ramp_active: list[tk.BooleanVar] = []
        self.ramp_temp: list[tk.StringVar] = []
        self.ramp_hold: list[tk.StringVar] = []
        self.ramp_row_labels: list[ttk.Label] = []

        body = ttk.Frame(box)
        body.pack(padx=6, pady=4)
        for i in range(4):
            av = tk.BooleanVar(value=(i < 2))
            tv = tk.StringVar(value=str(100 + 25 * i))
            hv = tk.StringVar(value="60")
            self.ramp_active.append(av)
            self.ramp_temp.append(tv)
            self.ramp_hold.append(hv)
            ttk.Checkbutton(body, variable=av).grid(row=i, column=0, padx=2)
            rl = ttk.Label(body, text=f"Rampa {i + 1}", width=10)
            rl.grid(row=i, column=1, sticky=tk.W)
            self.ramp_row_labels.append(rl)
            ttk.Entry(body, textvariable=tv, width=10, justify=tk.RIGHT).grid(
                row=i, column=2, padx=4
            )
            ttk.Entry(body, textvariable=hv, width=10, justify=tk.RIGHT).grid(
                row=i, column=3, padx=4
            )
            ttk.Button(
                body, text="Guardar", command=lambda idx=i: self._ctrl.write_ramp(idx)
            ).grid(row=i, column=4, padx=2)

        foot = ttk.Frame(box)
        foot.pack(fill=tk.X, padx=6, pady=(4, 8))
        ttk.Button(foot, text="Leer rampas", command=self._ctrl.read_ramps).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(
            foot, text="Guardar rampas activas", command=self._ctrl.write_all_ramps
        ).pack(side=tk.LEFT)

        for v in self.ramp_temp + self.ramp_active:
            v.trace_add("write", lambda *_: self._on_ramp_edit())

    def _on_ramp_edit(self) -> None:
        self._sync_chart_ylim()
        self.refresh_objetivo()

    def ramp_snapshot(self) -> tuple[list[bool], list[str], list[str]]:
        return (
            [v.get() for v in self.ramp_active],
            [v.get() for v in self.ramp_temp],
            [v.get() for v in self.ramp_hold],
        )

    def ramp_ymax(self) -> float:
        active, temps, _ = self.ramp_snapshot()
        vals: list[float] = []
        for on, t in zip(active, temps):
            if not on:
                continue
            try:
                vals.append(float(t))
            except ValueError:
                pass
        if not vals:
            for t in temps:
                try:
                    vals.append(float(t))
                except ValueError:
                    pass
        return max(vals) if vals else 100.0

    def sync_chart_ylim(self) -> None:
        if hasattr(self, "chart"):
            self.chart.set_y_max(self.ramp_ymax())

    def _sync_chart_ylim(self) -> None:
        self.sync_chart_ylim()

    def apply_ramps_frame(self, n: int, steps: list[tuple[int, int]]) -> None:
        for i in range(4):
            if i < len(steps):
                t, h = steps[i]
                self.ramp_temp[i].set(str(t))
                self.ramp_hold[i].set(str(h))
            self.ramp_active[i].set(i < n)
        self._sync_chart_ylim()
        self.refresh_objetivo()

    def apply_hp(
        self,
        fields: dict[str, Any],
        delay_cfg: str | None,
        preheat_en: str,
        preheat_pct: str,
    ) -> None:
        t = fields.get("T")
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        phase = proto.phase_name(a)
        temp_txt = "—" if t is None else f"{t} °C"
        self.chart.set_live_info(phase, temp_txt)

        self.proc_vars["T"].set(temp_txt)
        self.proc_vars["PHASE"].set(phase)
        self.proc_vars["PROG"].set(proto.prog_name(p))
        self.proc_vars["DLY"].set(str(fields.get("DLY", "—")))
        self.proc_vars["RUN"].set(str(fields.get("RUN", "—")))
        self.proc_vars["EL"].set(str(fields.get("EL", "—")))
        self.proc_vars["DU"].set(str(fields.get("DU", "—")))
        fan = fields.get("F", 0)
        self.proc_vars["F"].set(
            {0: "Apagado", 1: "Encendido", "0": "Apagado", "1": "Encendido"}.get(
                fan, str(fan)
            )
        )
        fl = fields.get("FL", 0)
        self.proc_vars["FL"].set(
            {0: "No", 1: "Sí", "0": "No", "1": "Sí"}.get(fl, str(fl))
        )
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        if p == 1 and a in (2, 3, 4, 5):
            self.proc_vars["RI"].set(f"Rampa {ri + 1}")
        else:
            self.proc_vars["RI"].set("—")
        if a in (0, 8) and delay_cfg is not None:
            self.proc_vars["DLY"].set(delay_cfg)

        self._update_fault_banner(fl)
        self.refresh_objetivo(fields, preheat_en, preheat_pct)
        self.highlight_ramp(p, a, ri)

    def _update_fault_banner(self, fl: Any) -> None:
        try:
            fault = int(fl) != 0
        except (TypeError, ValueError):
            fault = bool(fl)
        if fault:
            self.set_banner("Corte por falla — salidas desactivadas", "#c0392b")
        else:
            cur = self.banner.cget("text")
            if cur.startswith("Corte por falla"):
                self.set_banner("")

    def refresh_objetivo(self, *_args, **_kwargs) -> None:
        """Compat: consigna ya no se muestra en el panel de estado."""
        self._sync_chart_ylim()

    def highlight_ramp(self, prog: int, phase: int, ri: int) -> None:
        for i, lab in enumerate(self.ramp_row_labels):
            on = prog == 1 and phase in (2, 3, 4, 5) and i == ri
            lab.config(
                text=("► Rampa " if on else "Rampa ") + str(i + 1),
                font=("", 10, "bold") if on else ("", 10, "normal"),
            )

    def set_banner(self, text: str, color: str = "#a00") -> None:
        self.banner.config(text=text, fg=color, font=("", 11, "bold"))

    def has_active_ramps(self) -> bool:
        return any(v.get() for v in self.ramp_active)
