"""Pestaña Autoajuste PID: parámetros · avance · ganancias · curva."""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING, Any, Optional

import tkinter as tk
from tkinter import ttk

import protocol as proto
import tune_store
from chart import LiveChart
from constants import MAX_SAMPLES
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

ENTRY_W = 12


class TuneView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        # Ventana de visualización (últimas N) vs historial completo (CSV)
        self.samples: deque = deque(maxlen=MAX_SAMPLES)
        self.history: list[tuple[float, float, float, float]] = []
        self._t0: Optional[float] = None
        self._cycles_target = 5
        self.recording = False

        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, padx=8, pady=(8, 4))
        row1.rowconfigure(0, weight=1)

        # --- Parámetros + Guardar ---
        params = ttk.LabelFrame(row1, text="Parámetros de autoajuste")
        self.var_ttemp = tk.StringVar(value="150")
        self.var_tcyc = tk.StringVar(value="5")
        self.var_thyst = tk.StringVar(value="15")
        self.var_tmax_s = tk.StringVar(value="600")
        for r, (lab, var, tip) in enumerate(
            [
                (
                    "Temperatura objetivo (°C)",
                    self.var_ttemp,
                    "Consigna de oscilación\nRango: Tmin…Tmax−10\n"
                    "AT+RUN=2,<°C>,…  ·  $HP SET=",
                ),
                (
                    "Ciclos de oscilación",
                    self.var_tcyc,
                    "Ciclos a completar\nRango: 3…10\n"
                    "AT+RUN=2,…,<ciclos>,…  ·  progreso vs $HP AC=",
                ),
                (
                    "Histéresis (°C ×10)",
                    self.var_thyst,
                    "Banda ± alrededor de la consigna\nRango: 1…99 (×10 → °C)\n"
                    "AT+RUN=2,…,<hyst>  ·  ej. 15 = ±1.5 °C",
                ),
                (
                    "Timeout máximo (s)",
                    self.var_tmax_s,
                    "Timeout global del autoajuste\nRango: 120…3600 s (default 600)\n"
                    "AT+CFG=T,…,<max_s>  ·  AT+RUN=2,…,<max_s>  ·  $CF AMS=",
                ),
            ]
        ):
            lbl = ttk.Label(params, text=lab)
            lbl.grid(row=r, column=0, padx=8, pady=4, sticky=tk.NW)
            e = ttk.Entry(params, textvariable=var, width=ENTRY_W, justify=tk.RIGHT)
            e.grid(row=r, column=1, padx=8, pady=4, sticky=tk.NE)
            ToolTip(lbl, tip)
            ToolTip(e, tip)
        btn_save = ttk.Button(
            params, text="Guardar parámetros", command=ctrl.save_tune_params
        )
        btn_save.grid(row=4, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=(8, 8))
        ToolTip(
            btn_save,
            "Valida y envía AT+CFG=T al equipo (EEPROM).\n"
            "También guarda caché local en el host.\n"
            "Al iniciar: AT+RUN=2 con temp + estos params.",
        )

        # --- Avance ---
        prog = ttk.LabelFrame(row1, text="Avance del proceso")
        self.var_phase = tk.StringVar(value="—")
        self.var_pct = tk.StringVar(value="0 %")
        self.var_cycles = tk.StringVar(value="0 / —")
        ttk.Label(prog, text="Fase").grid(row=0, column=0, padx=8, pady=4, sticky=tk.NW)
        ttk.Label(prog, textvariable=self.var_phase, anchor=tk.E, width=ENTRY_W).grid(
            row=0, column=1, padx=8, pady=4, sticky=tk.NE
        )
        ttk.Label(prog, text="Progreso").grid(
            row=1, column=0, padx=8, pady=4, sticky=tk.NW
        )
        ttk.Label(prog, textvariable=self.var_pct, anchor=tk.E, width=ENTRY_W).grid(
            row=1, column=1, padx=8, pady=4, sticky=tk.NE
        )
        self.progress = ttk.Progressbar(
            prog, maximum=100, mode="determinate", length=140
        )
        self.progress.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=4)
        ttk.Label(prog, text="Ciclos sensados").grid(
            row=3, column=0, padx=8, pady=4, sticky=tk.NW
        )
        ttk.Label(prog, textvariable=self.var_cycles, anchor=tk.E, width=ENTRY_W).grid(
            row=3, column=1, padx=8, pady=4, sticky=tk.NE
        )

        # --- Ganancias + guardar ---
        result = ttk.LabelFrame(row1, text="Ganancias Kp / Ki / Kd (×10)")
        self.var_ak = tk.StringVar(value="—")
        self.var_ai = tk.StringVar(value="—")
        self.var_ad = tk.StringVar(value="—")
        for r, (lab, var, key) in enumerate(
            [
                ("Kp", self.var_ak, "AK"),
                ("Ki", self.var_ai, "AI"),
                ("Kd", self.var_ad, "AD"),
            ]
        ):
            ttk.Label(result, text=lab).grid(row=r, column=0, padx=8, pady=4, sticky=tk.NW)
            val_lbl = ttk.Label(result, textvariable=var, width=ENTRY_W, anchor=tk.E)
            val_lbl.grid(row=r, column=1, padx=8, pady=4, sticky=tk.NE)
            ToolTip(
                val_lbl,
                f"{lab} resultado del autoajuste (×10)\n"
                f"Trama: $HP {key}= (solo con stream)",
            )
        self.btn_apply = ttk.Button(
            result,
            text="Guardar ganancias en PID",
            command=ctrl.apply_atune,
            state=tk.DISABLED,
        )
        self.btn_apply.grid(
            row=3, column=0, columnspan=2, sticky=tk.EW, padx=8, pady=(8, 8)
        )

        self._top_frames = (params, prog, result)
        for i, fr in enumerate(self._top_frames):
            fr.grid(
                row=0,
                column=i,
                sticky=tk.NSEW,
                padx=(0 if i == 0 else 8, 0),
                pady=4,
            )

        # Fila 2: gráfico (controles Iniciar/Detener/CSV en el header)
        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.chart = LiveChart(
            row2,
            title="Curva de calibración",
            on_start=ctrl.run_tune,
            on_stop=ctrl.stop,
            on_export=ctrl.export_tune_csv,
            on_clear=self.clear_chart,
            start_label="Iniciar autoajuste",
            figsize=(8, 3.8),
        )
        self.var_ttemp.trace_add("write", lambda *_: self.sync_chart_ylim())
        self._load_cached_params()
        self.sync_chart_ylim()

    def _load_cached_params(self) -> None:
        data = tune_store.load_tune()
        if not data:
            return
        self.var_ttemp.set(str(data["temp"]))
        self.var_tcyc.set(str(data["cycles"]))
        self.var_thyst.set(str(data["hyst"]))
        self.var_tmax_s.set(str(data.get("max_s", 600)))

    def target_ymax(self) -> float:
        try:
            return max(float(self.var_ttemp.get()) * 1.5, 1.0)
        except ValueError:
            return 150.0

    def sync_chart_ylim(self) -> None:
        if hasattr(self, "chart"):
            self.chart.set_y_max(self.target_ymax())

    def begin_run(self) -> None:
        try:
            self._cycles_target = int(self.var_tcyc.get())
        except ValueError:
            self._cycles_target = 5
        self.recording = True
        self.samples.clear()
        self.history.clear()
        self._t0 = None
        self.chart.clear()
        self.sync_chart_ylim()
        self.progress["value"] = 0
        self.var_pct.set("0 %")
        self.var_cycles.set(f"0 / {self._cycles_target}")
        self.var_phase.set("—")
        self.var_ak.set("—")
        self.var_ai.set("—")
        self.var_ad.set("—")
        self.btn_apply.config(state=tk.DISABLED)

    def stop_recording(self) -> None:
        self.recording = False

    def clear_chart(self) -> None:
        self.samples.clear()
        self.history.clear()
        self._t0 = None
        self.chart.clear()
        self.sync_chart_ylim()

    def apply_atune_fields(self, fields: dict[str, Any]) -> None:
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        ap = fields.get("AP")
        tuning = p == 2 or a == 10 or ap is not None
        if not tuning:
            return

        if ap is not None:
            self.var_phase.set(proto.atune_phase_name(int(ap)))
            ac = int(fields.get("AC", 0))
            tgt = self._cycles_target
            pct = min(100, int(100 * ac / tgt)) if tgt > 0 else 0
            if int(ap) == 2:
                pct = 100
            self.progress["value"] = pct
            self.var_pct.set(f"{pct} %")
            self.var_cycles.set(f"{ac} / {tgt}")
            self.var_ak.set(str(fields.get("AK", "—")))
            self.var_ai.set(str(fields.get("AI", "—")))
            self.var_ad.set(str(fields.get("AD", "—")))
            self.btn_apply.config(
                state=(tk.NORMAL if int(ap) == 2 else tk.DISABLED)
            )

        ap_i = int(ap) if ap is not None else -1
        active = a == 10 or ap_i == 1
        finished = ap_i in (2, 3)
        if not self.recording:
            return
        if not active and not finished:
            return

        t = fields.get("T")
        now = time.time()
        if self._t0 is None:
            self._t0 = now
        try:
            set_c = float(fields.get("SET", float("nan")))
        except (TypeError, ValueError):
            set_c = float("nan")
        try:
            du = float(fields.get("DU", float("nan")))
        except (TypeError, ValueError):
            du = float("nan")
        row = (
            now - self._t0,
            float(t) if t is not None else float("nan"),
            set_c,
            du,
        )
        self.history.append(row)
        self.samples.append(row)
        band = None
        if fields.get("SET") is not None:
            band = self.hyst_band(float(fields["SET"]))
        self.chart.redraw(self.samples, band, y_max=self.target_ymax())

        if finished:
            self.recording = False

    def hyst_band(self, set_c: float) -> tuple[float, float] | None:
        try:
            hyst = int(self.var_thyst.get()) / 10.0
            return set_c - hyst, set_c + hyst
        except ValueError:
            return None
