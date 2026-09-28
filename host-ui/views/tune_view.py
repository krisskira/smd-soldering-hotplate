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
from constants import (
    MAX_SAMPLES,
    PID_KD_DEFAULT,
    PID_KI_DEFAULT,
    PID_KP_DEFAULT,
    TUNE_CYCLES_DEFAULT,
    TUNE_HYST_X10_DEFAULT,
    TUNE_MAX_S_DEFAULT,
    TUNE_TEMP_C_DEFAULT,
)
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

ENTRY_W = 12


class TuneView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        # Ventana de visualización (últimas N) vs historial completo (CSV)
        self.samples: deque = deque(maxlen=MAX_SAMPLES)
        self.history: list[tuple[float, float, float, float, str]] = []
        self._t0: Optional[float] = None
        self._cycles_target = TUNE_CYCLES_DEFAULT
        self.recording = False

        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, padx=8, pady=(8, 4))
        row1.rowconfigure(0, weight=1)

        # --- Parámetros + Guardar ---
        params = ttk.LabelFrame(row1, text="Parámetros de autoajuste")
        self.var_ttemp = tk.StringVar(value=str(TUNE_TEMP_C_DEFAULT))
        self.var_tcyc = tk.StringVar(value=str(TUNE_CYCLES_DEFAULT))
        self.var_thyst = tk.StringVar(value=str(TUNE_HYST_X10_DEFAULT))
        self.var_tmax_s = tk.StringVar(value=str(TUNE_MAX_S_DEFAULT))
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
                    "Timeout global del autoajuste\nRango: 120…3600 s (default 2000)\n"
                    "El eje X de la curva usa este valor.\n"
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
        self._tune_running = False
        btn_tune_bar = ttk.Frame(prog)
        btn_tune_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        self.btn_tune = ttk.Button(
            btn_tune_bar, text="Iniciar autoajuste", command=ctrl.toggle_tune
        )
        self.btn_tune.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ToolTip(
            self.btn_tune,
            "Inicia o detiene el autoajuste (AT+RUN=2 / AT+STOP).",
        )
        prog_body = ttk.Frame(prog)
        prog_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        ttk.Label(prog_body, text="Fase").grid(
            row=0, column=0, padx=0, pady=4, sticky=tk.NW
        )
        ttk.Label(
            prog_body, textvariable=self.var_phase, anchor=tk.E, width=ENTRY_W
        ).grid(row=0, column=1, padx=0, pady=4, sticky=tk.NE)
        ttk.Label(prog_body, text="Progreso").grid(
            row=1, column=0, padx=0, pady=4, sticky=tk.NW
        )
        ttk.Label(
            prog_body, textvariable=self.var_pct, anchor=tk.E, width=ENTRY_W
        ).grid(row=1, column=1, padx=0, pady=4, sticky=tk.NE)
        self.progress = ttk.Progressbar(
            prog_body, maximum=100, mode="determinate", length=140
        )
        self.progress.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=0, pady=4)
        ttk.Label(prog_body, text="Ciclos sensados").grid(
            row=3, column=0, padx=0, pady=4, sticky=tk.NW
        )
        ttk.Label(
            prog_body, textvariable=self.var_cycles, anchor=tk.E, width=ENTRY_W
        ).grid(row=3, column=1, padx=0, pady=4, sticky=tk.NE)
        prog_body.columnconfigure(1, weight=1)

        # --- Ganancias + guardar ---
        result = ttk.LabelFrame(row1, text="Ganancias Kp / Ki / Kd (×10)")
        self.var_ak = tk.StringVar(value=str(PID_KP_DEFAULT))
        self.var_ai = tk.StringVar(value=str(PID_KI_DEFAULT))
        self.var_ad = tk.StringVar(value=str(PID_KD_DEFAULT))
        self._atune_result_ready = False
        apply_bar = ttk.Frame(result)
        apply_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        self.btn_apply = ttk.Button(
            apply_bar,
            text="Guardar ganancias en PID",
            command=ctrl.apply_atune,
            state=tk.DISABLED,
        )
        self.btn_apply.pack(side=tk.LEFT, fill=tk.X, expand=True)
        result_body = ttk.Frame(result)
        result_body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        for r, (lab, var, key) in enumerate(
            [
                ("Kp", self.var_ak, "AK"),
                ("Ki", self.var_ai, "AI"),
                ("Kd", self.var_ad, "AD"),
            ]
        ):
            ttk.Label(result_body, text=lab).grid(
                row=r, column=0, padx=0, pady=4, sticky=tk.NW
            )
            val_lbl = ttk.Label(
                result_body, textvariable=var, width=ENTRY_W, anchor=tk.E
            )
            val_lbl.grid(row=r, column=1, padx=0, pady=4, sticky=tk.NE)
            ToolTip(
                val_lbl,
                f"{lab} del equipo (×10), mismo que Ajustes / $CF.\n"
                f"Tras autoajuste DONE: $HP {key}= y se puede guardar en PID.",
            )
        result_body.columnconfigure(1, weight=1)

        self._top_frames = (params, prog, result)
        for i, fr in enumerate(self._top_frames):
            fr.grid(
                row=0,
                column=i,
                sticky=tk.NSEW,
                padx=(0 if i == 0 else 8, 0),
                pady=4,
            )
        row1.columnconfigure(0, weight=1, uniform="tune")
        row1.columnconfigure(1, weight=1, uniform="tune")
        row1.columnconfigure(2, weight=1, uniform="tune")

        # Fila 2: gráfico (CSV / limpiar en el header)
        row2 = ttk.Frame(parent)
        row2.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.chart = LiveChart(
            row2,
            title="Curva de calibración",
            on_export=ctrl.export_tune_csv,
            on_clear=self.clear_chart,
            figsize=(8, 4.8),
            x_span_s=float(TUNE_MAX_S_DEFAULT),
            x_locked=True,
        )
        self.var_ttemp.trace_add("write", lambda *_: self.sync_chart_ylim())
        self.var_tmax_s.trace_add("write", lambda *_: self.sync_chart_x())
        self._load_cached_params()
        self.sync_chart_ylim()
        self.sync_chart_x()

    def _load_cached_params(self) -> None:
        data = tune_store.load_tune()
        if not data:
            return
        self.var_ttemp.set(str(data["temp"]))
        self.var_tcyc.set(str(data["cycles"]))
        self.var_thyst.set(str(data["hyst"]))
        self.var_tmax_s.set(str(data.get("max_s", TUNE_MAX_S_DEFAULT)))

    def target_ymax(self) -> float:
        try:
            return max(float(self.var_ttemp.get()) * 1.5, 1.0)
        except ValueError:
            return float(TUNE_TEMP_C_DEFAULT) * 1.5

    def sync_chart_ylim(self) -> None:
        if hasattr(self, "chart"):
            self.chart.set_y_max(self.target_ymax())

    def sync_chart_x(self) -> None:
        """Largo y marcas del eje X = timeout máximo del formulario."""
        if not hasattr(self, "chart"):
            return
        try:
            span = int(self.var_tmax_s.get())
        except ValueError:
            return
        if 120 <= span <= 3600:
            self.chart.set_x_span(float(span))

    def begin_run(self) -> None:
        try:
            self._cycles_target = int(self.var_tcyc.get())
        except ValueError:
            self._cycles_target = TUNE_CYCLES_DEFAULT
        self.recording = True
        self.set_tune_running(True)
        self.samples.clear()
        self.history.clear()
        self._t0 = None
        self.sync_chart_x()
        self.chart.clear()
        self.sync_chart_ylim()
        self.progress["value"] = 0
        self.var_pct.set("0 %")
        self.var_cycles.set(f"0 / {self._cycles_target}")
        self.var_phase.set("—")
        self._atune_result_ready = False
        self.btn_apply.config(state=tk.DISABLED)
        # Kp/Ki/Kd siguen mostrando el PID del equipo hasta DONE.

    def set_tune_running(self, running: bool) -> None:
        self._tune_running = bool(running)
        self.btn_tune.config(
            text=(
                "Detener autoajuste" if self._tune_running else "Iniciar autoajuste"
            )
        )

    def is_tune_running(self) -> bool:
        return self._tune_running

    def stop_recording(self) -> None:
        self.recording = False
        self.set_tune_running(False)

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
            # Solo al terminar el autoajuste se sustituyen las ganancias de trabajo.
            if int(ap) == 2:
                self.var_ak.set(str(fields.get("AK", "—")))
                self.var_ai.set(str(fields.get("AI", "—")))
                self.var_ad.set(str(fields.get("AD", "—")))
                self._atune_result_ready = True
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
            proto.chart_atune_label(ap_i) if ap_i >= 0 else "",
        )
        self.history.append(row)
        self.samples.append(row)
        band = None
        if fields.get("SET") is not None:
            band = self.hyst_band(float(fields["SET"]))
        self.chart.redraw(self.history, band, y_max=self.target_ymax())

        if finished:
            self.recording = False
            self.set_tune_running(False)

    def apply_working_pid(self, fields: dict[str, Any]) -> None:
        """Copia KP/KI/KD del device ($CF o Ajustes) si no hay resultado de tune."""
        if self._atune_result_ready:
            return
        if "KP" in fields:
            self.var_ak.set(str(fields["KP"]))
        if "KI" in fields:
            self.var_ai.set(str(fields["KI"]))
        if "KD" in fields:
            self.var_ad.set(str(fields["KD"]))

    def hyst_band(self, set_c: float) -> tuple[float, float] | None:
        try:
            hyst = int(self.var_thyst.get()) / 10.0
            return set_c - hyst, set_c + hyst
        except ValueError:
            return None
