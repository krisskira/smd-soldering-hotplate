"""Pestaña Autotune: parámetros del ensayo, estado del proceso y la misma curva."""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING, Any, Optional

import tkinter as tk
from tkinter import ttk

import protocol as proto
import theme as ui_theme
import tune_store
from chart import LiveChart
from constants import (
    MAX_SAMPLES,
    PID_KI_DEFAULT,
    PID_KP_DEFAULT,
    TUNE_CYCLES_DEFAULT,
    TUNE_HYST_X10_DEFAULT,
    TUNE_MAX_S_DEFAULT,
    TUNE_TEMP_C_DEFAULT,
)
from views.layout import add_panel, content_row
from views.status_panel import StatusPanel
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

ENTRY_W = 8


class TuneView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.samples: deque = deque(maxlen=MAX_SAMPLES)
        self.history: list[tuple[float, float, float, float, str]] = []
        self._t0: Optional[float] = None
        self._cycles_target = TUNE_CYCLES_DEFAULT
        self.recording = False
        self._tune_running = False
        self._atune_result_ready = False

        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=(8, 2))
        self.btn_tune = ttk.Button(
            top,
            text="Iniciar autoajuste",
            command=ctrl.toggle_tune,
            style="Accent.TButton",
        )
        self.btn_tune.pack(side=tk.LEFT, padx=(0, 8))
        ToolTip(self.btn_tune, "Inicia o detiene el autoajuste (AT+RUN=2 / AT+STOP).")
        self.banner = tk.Label(top, text="", anchor=tk.W)
        self.banner.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row = content_row(parent)
        config = self._build_config(row, ctrl)
        self.status = StatusPanel(row)
        add_panel(row, config)
        add_panel(row, self.status.frame)

        chart_host = ttk.Frame(parent)
        chart_host.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 6))
        self.chart = LiveChart(
            chart_host,
            title="Curva de autoajuste",
            on_export=ctrl.export_tune_csv,
            on_export_events=ctrl.export_tune_events,
            on_clear=self.clear_chart,
            figsize=(8.6, 3.4),
            x_span_s=float(TUNE_MAX_S_DEFAULT),
            x_locked=True,
        )
        self.var_ttemp.trace_add("write", lambda *_: self.sync_chart_ylim())
        self.var_tmax_s.trace_add("write", lambda *_: self.sync_chart_x())
        self._load_cached_params()
        self.sync_chart_ylim()
        self.sync_chart_x()
        self.apply_theme()

    def _field(
        self,
        parent: ttk.Frame,
        row: int,
        col: int,
        label: str,
        var: tk.StringVar,
        tip: str,
    ) -> None:
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=col, padx=(0, 6), pady=3, sticky=tk.W)
        ent = ttk.Entry(parent, textvariable=var, width=ENTRY_W, justify=tk.RIGHT)
        ent.grid(row=row, column=col + 1, padx=(0, 12), pady=3, sticky=tk.W)
        ToolTip(lbl, tip)
        ToolTip(ent, tip)

    def _build_config(self, parent: ttk.Frame, ctrl: "AppController") -> ttk.LabelFrame:
        box = ttk.LabelFrame(parent, text="Autoajuste")
        body = ttk.Frame(box)
        body.pack(anchor=tk.NW, padx=8, pady=6)

        self.var_ttemp = tk.StringVar(value=str(TUNE_TEMP_C_DEFAULT))
        self.var_tcyc = tk.StringVar(value=str(TUNE_CYCLES_DEFAULT))
        self.var_thyst = tk.StringVar(value=str(TUNE_HYST_X10_DEFAULT))
        self.var_tmax_s = tk.StringVar(value=str(TUNE_MAX_S_DEFAULT))
        self._field(
            body, 0, 0, "Temperatura (°C)", self.var_ttemp,
            "Consigna de oscilación\nRango: Tmin…Tmax−10\nAT+RUN=2,<°C>,…  ·  $HP SET=",
        )
        self._field(
            body, 0, 2, "Ciclos", self.var_tcyc,
            "Ciclos a completar\nRango: 3…10\nAT+RUN=2,…,<ciclos>,…  ·  $HP AC=",
        )
        self._field(
            body, 1, 0, "Histéresis (×10)", self.var_thyst,
            "Banda ± alrededor de la consigna\nRango: 1…99 (×10 → °C)\n"
            "AT+RUN=2,…,<hyst>  ·  ej. 15 = ±1.5 °C",
        )
        self._field(
            body, 1, 2, "Timeout (s)", self.var_tmax_s,
            "Timeout global del autoajuste\nRango: 120…3600 s (default 2000)\n"
            "El eje X de la curva usa este valor.\nAT+CFG=T  ·  $CF AMS=",
        )
        ttk.Button(body, text="Guardar parámetros", command=ctrl.save_tune_params).grid(
            row=2, column=0, columnspan=4, sticky=tk.W, pady=(4, 8)
        )

        ttk.Separator(body, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=4, sticky=tk.EW, pady=(0, 6)
        )

        self.var_phase = tk.StringVar(value="—")
        self.var_pct = tk.StringVar(value="0 %")
        self.var_cycles = tk.StringVar(value="0 / —")
        self.var_ak = tk.StringVar(value=str(PID_KP_DEFAULT))
        self.var_ai = tk.StringVar(value=str(PID_KI_DEFAULT))

        ttk.Label(body, text="Fase").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Label(body, textvariable=self.var_phase).grid(
            row=4, column=1, sticky=tk.W, pady=2
        )
        ttk.Label(body, text="Ciclos").grid(row=4, column=2, sticky=tk.W, pady=2)
        ttk.Label(body, textvariable=self.var_cycles).grid(
            row=4, column=3, sticky=tk.W, pady=2
        )
        ttk.Label(body, text="Progreso").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Label(body, textvariable=self.var_pct).grid(
            row=5, column=1, sticky=tk.W, pady=2
        )
        self.progress = ttk.Progressbar(body, maximum=100, mode="determinate", length=160)
        self.progress.grid(row=5, column=2, columnspan=2, sticky=tk.EW, pady=2)

        ttk.Label(body, text="Kp ×10").grid(row=6, column=0, sticky=tk.W, pady=(8, 2))
        kp = ttk.Label(body, textvariable=self.var_ak)
        kp.grid(row=6, column=1, sticky=tk.W, pady=(8, 2))
        ttk.Label(body, text="Ki ×10").grid(row=6, column=2, sticky=tk.W, pady=(8, 2))
        ki = ttk.Label(body, textvariable=self.var_ai)
        ki.grid(row=6, column=3, sticky=tk.W, pady=(8, 2))
        ToolTip(kp, "Kp del equipo (×10). Al terminar, $HP AK= y se guarda solo en EEPROM.")
        ToolTip(ki, "Ki del equipo (×10). Al terminar, $HP AI=. El lazo no usa Kd.")

        self.btn_apply = ttk.Button(
            body,
            text="Releer ganancias del equipo",
            command=ctrl.apply_atune,
            state=tk.DISABLED,
        )
        self.btn_apply.grid(row=7, column=0, columnspan=4, sticky=tk.W, pady=(6, 2))
        return box

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
        """Largo del eje X = timeout máximo del formulario."""
        if not hasattr(self, "chart"):
            return
        try:
            span = int(self.var_tmax_s.get())
        except ValueError:
            return
        if 120 <= span <= 3600:
            self.chart.set_x_window(float(span), locked=True)

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

    def set_tune_running(self, running: bool) -> None:
        self._tune_running = bool(running)
        self.btn_tune.config(
            text=("Detener autoajuste" if self._tune_running else "Iniciar autoajuste")
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

    def apply_status(self, fields: dict[str, Any], delay_cfg: str | None) -> None:
        self.status.apply_hp(fields, delay_cfg)
        try:
            fault = int(fields.get("FL", 0)) != 0
        except (TypeError, ValueError):
            fault = bool(fields.get("FL"))
        if fault:
            self.banner.config(
                text="Corte por falla — salidas desactivadas", fg="#c0392b"
            )
        elif str(self.banner.cget("text")).startswith("Corte por falla"):
            self.banner.config(text="")

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
            if int(ap) == 2:
                self.var_ak.set(str(fields.get("AK", "—")))
                self.var_ai.set(str(fields.get("AI", "—")))
                self._atune_result_ready = True
            self.btn_apply.config(state=(tk.NORMAL if int(ap) == 2 else tk.DISABLED))

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
        """Copia KP/KI del equipo ($CF o Ajustes) si no hay resultado de tune."""
        if self._atune_result_ready:
            return
        if "KP" in fields:
            self.var_ak.set(str(fields["KP"]))
        if "KI" in fields:
            self.var_ai.set(str(fields["KI"]))

    def hyst_band(self, set_c: float) -> tuple[float, float] | None:
        try:
            hyst = int(self.var_thyst.get()) / 10.0
            return set_c - hyst, set_c + hyst
        except ValueError:
            return None

    def apply_theme(self) -> None:
        self.banner.configure(
            font=ui_theme.font_tuple("body_size"),
            bg=ui_theme.surface_bg(),
        )
        if not self.banner.cget("text"):
            self.banner.configure(fg=ui_theme.get()["body_color"])
        self.status.apply_theme()
        if hasattr(self, "chart"):
            self.chart.apply_theme()
