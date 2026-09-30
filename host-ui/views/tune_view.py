"""Pestaña Autotune: parámetros del ensayo, progreso, resultado, estado y curva."""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING, Any, Optional

import tkinter as tk

import protocol as proto
import tune_store
from chart import TUNE_LEGEND, LiveChart
from constants import (
    ATUNE_SET_HI_C,
    ATUNE_SET_LO_C,
    MAX_SAMPLES,
    PID_KI_DEFAULT,
    PID_KP_DEFAULT,
    TUNE_CYCLES_DEFAULT,
    TUNE_HYST_X10_DEFAULT,
    TUNE_MAX_S_DEFAULT,
    TUNE_TEMP_C_DEFAULT,
)
from views.status_panel import StatusPanel, TuneHud
from widgets import ui
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

BANNER_OK = "#005a2c"
BANNER_OK_BORDER = "#00401e"
BANNER_OK_SOFT = "#7efba4"
PROGRESS_STATES = ("Inactivo", "En curso", "Listo", "Fallido")
PROGRESS_COLORS = {"En curso": ui.ACCENT, "Listo": ui.GREEN, "Fallido": ui.RED}


def _hyst_text(raw: str) -> str:
    try:
        return f"±{int(raw) / 10:.1f} °C"
    except (TypeError, ValueError):
        return "±— °C"


class TuneView:
    def __init__(self, parent: tk.Misc, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.samples: deque = deque(maxlen=MAX_SAMPLES)
        self.history: list[tuple[float, float, float, float, str]] = []
        self._t0: Optional[float] = None
        self._cycles_target = TUNE_CYCLES_DEFAULT
        self.recording = False
        self._tune_running = False
        self._atune_result_ready = False

        self.var_ttemp = tk.StringVar(value=str(TUNE_TEMP_C_DEFAULT))
        self.var_tcyc = tk.StringVar(value=str(TUNE_CYCLES_DEFAULT))
        self.var_thyst = tk.StringVar(value=str(TUNE_HYST_X10_DEFAULT))
        self.var_tmax_s = tk.StringVar(value=str(TUNE_MAX_S_DEFAULT))
        self.var_hyst_txt = tk.StringVar(value=_hyst_text(self.var_thyst.get()))

        page = ui.ScrollPage(parent)
        page.pack(fill=tk.BOTH, expand=True)
        self.page = page
        root = tk.Frame(page.inner, bg=ui.BG)
        root.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # 1 · Acción + aviso
        top = tk.Frame(root, bg=ui.BG, height=42)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        self.btn_tune = ui.Button(
            top, "Iniciar autoajuste", command=ctrl.toggle_tune, variant="primary",
            font=ui.sans(14, "bold"), padx=20, height=36, radius=6, icon="play", icon_size=18,
        )
        self.btn_tune.pack(side=tk.LEFT)
        ToolTip(self.btn_tune, "Inicia o detiene el autoajuste (AT+RUN=2 / AT+STOP).")
        self._build_banner(top)

        # 2 · HUD
        self.telemetry = TuneHud(root)
        self.telemetry.frame.pack(fill=tk.X, pady=(16, 0))

        # 3 · Autoajuste + estado
        row = tk.Frame(root, bg=ui.BG)
        row.pack(fill=tk.X, pady=(16, 0))
        row.columnconfigure(0, weight=1, uniform="cards")
        row.columnconfigure(1, weight=1, uniform="cards")
        config = self._build_config(row, ctrl)
        config.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 8))
        self.status = StatusPanel(row, icon="board", stream_chip=False, split_profile=False)
        self.status.frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(8, 0))

        # 4 · Curva
        self.chart = LiveChart(
            root,
            title="Curva de autoajuste",
            on_export=ctrl.export_tune_csv,
            on_export_events=ctrl.export_tune_events,
            on_clear=self.clear_chart,
            x_span_s=float(TUNE_MAX_S_DEFAULT),
            x_locked=True,
            legend=TUNE_LEGEND,
            events_height=474,
        )
        self.chart.frame.pack(fill=tk.X, pady=(16, 0))
        self.var_ttemp.trace_add("write", lambda *_: self._on_temp_change())
        self.var_tmax_s.trace_add("write", lambda *_: self.sync_chart_x())
        self.var_thyst.trace_add("write", lambda *_: self._on_hyst_change())
        self._load_cached_params()
        self._on_temp_change()
        self._on_hyst_change()
        self.sync_chart_x()
        self.apply_theme()

    # ------------------------------------------------------------ aviso
    def _build_banner(self, parent: tk.Misc) -> None:
        self._banner_box = ui.Box(parent, fill=BANNER_OK, border=BANNER_OK_BORDER, radius=6,
                                  padx=16, pady=0, bg=ui.BG)
        body = self._banner_box.body
        self._banner_icon = ui.Icon(body, "verified", size=20, color=BANNER_OK_SOFT, bg=BANNER_OK)
        self._banner_icon.pack(side=tk.LEFT, padx=(0, 10))
        self._banner_title = ui.label(body, "", font=ui.sans(14, "bold"), fg="#ffffff")
        self._banner_title.pack(side=tk.LEFT)
        self.banner = ui.label(body, "", font=ui.sans(14), fg=BANNER_OK_SOFT)
        self.banner.pack(side=tk.LEFT, padx=(10, 0))
        self.banner_close = ui.Button(
            body, "", command=self.dismiss_banner, variant="ghost", icon="close",
            icon_size=18, padx=0, height=36, gap=0,
        )
        self.banner_close.pack(side=tk.RIGHT)
        ToolTip(self.banner_close, "Cerrar aviso")

    def _show_banner(self, title: str, text: str, *, ok: bool) -> None:
        fill = BANNER_OK if ok else ui.ERROR
        border = BANNER_OK_BORDER if ok else "#93000a"
        soft = BANNER_OK_SOFT if ok else "#ffdad6"
        self._banner_box.set_fill(fill, border)
        for widget in (self._banner_title, self.banner):
            widget.configure(bg=fill)
        self._banner_icon.configure(bg=fill)
        self._banner_icon._name = "verified" if ok else "info"
        self._banner_icon.set_color(soft)
        self._banner_title.configure(text=title)
        self.banner.configure(text=text, fg=soft)
        self.banner_close.set_outer_bg(fill)
        if not self._banner_box.winfo_ismapped():
            self._banner_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0))

    def dismiss_banner(self) -> None:
        self.banner.configure(text="")
        self._banner_title.configure(text="")
        self._banner_box.pack_forget()

    # ------------------------------------------------------- autoajuste
    def _param_block(
        self, parent: tk.Misc, label: str, range_text: str, var: tk.StringVar,
        suffix: Optional[str], tip: str, suffix_var: Optional[tk.StringVar] = None,
    ) -> ui.Box:
        box = ui.block(parent)
        body = box.body
        head = tk.Frame(body, bg=ui.BG, height=17)
        head.pack(fill=tk.X)
        head.pack_propagate(False)
        lbl = ui.Line(head, label, font=ui.sans(12, "bold"), fg=ui.TEXT, height=16)
        lbl.pack(side=tk.LEFT)
        rng = ui.Line(head, range_text, font=ui.sans(11), fg=ui.MUTED, height=16)
        rng.pack(side=tk.RIGHT)
        field = ui.Field(body, var, height=26, font=ui.mono(12), justify=tk.LEFT, padx=10,
                         suffix=suffix, suffix_var=suffix_var)
        field.pack(fill=tk.X, pady=(4, 0))
        ToolTip(lbl.label, tip)
        ToolTip(field.entry, tip)
        box.range_label = rng  # type: ignore[attr-defined]
        return box

    def _section_title(self, parent: tk.Misc, text: str) -> ui.Line:
        return ui.Line(parent, text.upper(), font=ui.sans(12, "bold"), fg=ui.TEXT, height=16)

    def _build_config(self, parent: tk.Misc, ctrl: "AppController") -> ui.Box:
        box = ui.card(parent)
        body = box.body
        ui.CardHeader(body, "Autoajuste", icon="tune").pack(fill=tk.X)

        sec = tk.Frame(body, bg=ui.CARD)
        sec.pack(fill=tk.X, pady=(16, 0))
        self._section_title(sec, "Parámetros del ensayo").pack(anchor=tk.W)
        grid = tk.Frame(sec, bg=ui.CARD)
        grid.pack(fill=tk.X, pady=(10, 0))
        grid.columnconfigure(0, weight=1, uniform="params")
        grid.columnconfigure(1, weight=1, uniform="params")
        specs = (
            ("Temperatura", f"{ATUNE_SET_LO_C}…{ATUNE_SET_HI_C} °C", self.var_ttemp, "°C", None,
             "Consigna de oscilación\nRango: 120…150 °C, dentro de Tmin…Tmax−10\n"
             "AT+RUN=2,<°C>,…  ·  $HP SET="),
            ("Ciclos", "3…10 ciclos", self.var_tcyc, "ciclos", None,
             "Ciclos a completar\nRango: 3…10\nAT+RUN=2,…,<ciclos>,…  ·  $HP AC="),
            ("Histéresis (×10)", "", self.var_thyst, None, self.var_hyst_txt,
             "Banda ± alrededor de la consigna\nRango: 1…99 (×10 → °C)\n"
             "AT+RUN=2,…,<hyst>  ·  ej. 15 = ±1.5 °C"),
            ("Timeout", "120…3600 s", self.var_tmax_s, "s", None,
             "Timeout global del autoajuste\nRango: 120…3600 s (default 2000)\n"
             "El eje X de la curva usa este valor.\nAT+CFG=T  ·  $CF AMS="),
        )
        self._hyst_range: Optional[ui.Line] = None
        for index, (label, rng, var, suffix, suffix_var, tip) in enumerate(specs):
            block = self._param_block(grid, label, rng, var, suffix, tip, suffix_var)
            r, c = divmod(index, 2)
            block.grid(row=r, column=c, sticky=tk.NSEW,
                       padx=((0, 6) if c == 0 else (6, 0)), pady=((0, 12) if r == 0 else 0))
            if suffix_var is not None:
                self._hyst_range = block.range_label  # type: ignore[attr-defined]
        note_row = tk.Frame(sec, bg=ui.CARD)
        note_row.pack(fill=tk.X, pady=(14, 0))
        ui.Button(note_row, "Guardar parámetros", command=ctrl.save_tune_params, variant="soft",
                  font=ui.sans(12, "bold"), height=30, radius=4, icon="save", icon_size=15,
                  gap=6).pack(side=tk.RIGHT, padx=(8, 0))
        ui.label(
            note_row,
            "La temperatura solo se usa en el próximo inicio; Guardar envía "
            "AT+CFG=T,ciclos,hist,timeout",
            font=ui.sans(11, italic=True), fg=ui.MUTED, justify=tk.LEFT, anchor=tk.W,
            wraplength=360,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ui.hline(body).pack(fill=tk.X, pady=(16, 0))

        prog = tk.Frame(body, bg=ui.CARD)
        prog.pack(fill=tk.X, pady=(16, 0))
        head = tk.Frame(prog, bg=ui.CARD, height=16)
        head.pack(fill=tk.X)
        head.pack_propagate(False)
        self._section_title(head, "Progreso").pack(side=tk.LEFT)
        self.var_phase = tk.StringVar(value="—")
        self.var_pct = tk.StringVar(value="0 %")
        self.var_cycles = tk.StringVar(value="0 / —")
        ui.Line(head, textvariable=self.var_pct, font=ui.mono(12, "bold"), fg=ui.ACCENT,
                height=16).pack(side=tk.RIGHT)
        cyc = tk.Frame(head, bg=ui.CARD)
        cyc.pack(side=tk.RIGHT, padx=(0, 12))
        ui.Line(cyc, "Ciclos:", font=ui.mono(12), fg=ui.MUTED, height=16).pack(side=tk.LEFT)
        ui.Line(cyc, textvariable=self.var_cycles, font=ui.mono(12, "bold"), fg=ui.TEXT,
                height=16).pack(side=tk.LEFT, padx=(6, 0))
        fase = tk.Frame(head, bg=ui.CARD)
        fase.pack(side=tk.RIGHT, padx=(0, 12))
        ui.Line(fase, "Fase:", font=ui.sans(12), fg=ui.TEXT, height=16).pack(side=tk.LEFT)
        self._phase_value = ui.Line(fase, textvariable=self.var_phase, font=ui.sans(12, "bold"),
                                    fg=ui.MUTED, height=16)
        self._phase_value.pack(side=tk.LEFT, padx=(4, 0))
        self._progress_bar = tk.Canvas(prog, height=10, bg=ui.CARD, highlightthickness=0, bd=0)
        self._progress_bar.pack(fill=tk.X, pady=(6, 0))
        self._progress_bar.bind("<Configure>", lambda _e: self._paint_progress(), add="+")
        self._progress_pct = 0
        legend = tk.Frame(prog, bg=ui.CARD)
        legend.pack(fill=tk.X, pady=(6, 0))
        self._legend_bits: dict[str, ui.Line] = {}
        for index, name in enumerate(reversed(PROGRESS_STATES)):
            if index:
                ui.Line(legend, "·", font=ui.sans(11), fg=ui.FAINT, height=16).pack(
                    side=tk.RIGHT, padx=4
                )
            bit = ui.Line(legend, name, font=ui.sans(11), fg=ui.FAINT, height=16)
            bit.pack(side=tk.RIGHT)
            self._legend_bits[name] = bit
        self.progress_legend = legend

        ui.hline(body).pack(fill=tk.X, pady=(16, 0))

        res = tk.Frame(body, bg=ui.CARD)
        res.pack(fill=tk.X, pady=(16, 0))
        self._section_title(res, "Resultado (Ziegler–Nichols PI)").pack(anchor=tk.W)
        tiles = tk.Frame(res, bg=ui.CARD)
        tiles.pack(fill=tk.X, pady=(10, 0))
        tiles.columnconfigure(0, weight=1, uniform="gains")
        tiles.columnconfigure(1, weight=1, uniform="gains")
        self.var_ak = tk.StringVar(value=str(PID_KP_DEFAULT))
        self.var_ai = tk.StringVar(value=str(PID_KI_DEFAULT))
        self.var_kp_real = tk.StringVar(value=f"Valor real {PID_KP_DEFAULT / 10:.1f}")
        self.var_ki_real = tk.StringVar(value=f"Valor real {PID_KI_DEFAULT / 100:.2f}")
        for col, (title, var, real, badge, fill, border, fg, tip) in enumerate((
            ("Kp ×10", self.var_ak, self.var_kp_real, "Kp", "#cce5ff", "#77c2ff", "#004f79",
             "Kp del equipo (×10). Al terminar, $HP AK= y se guarda solo en EEPROM."),
            ("Ki ×100", self.var_ai, self.var_ki_real, "Ki", BANNER_OK_SOFT, "#58d683",
             BANNER_OK_BORDER, "Ki del equipo (×100). Al terminar, $HP AI=. El lazo no usa Kd."),
        )):
            tile = ui.block(tiles, padx=12, pady=12)
            tile.grid(row=0, column=col, sticky=tk.NSEW, padx=((0, 6) if col == 0 else (6, 0)))
            left = tk.Frame(tile.body, bg=ui.BG)
            left.pack(side=tk.LEFT)
            ui.Line(left, title, font=ui.sans(11), fg=ui.MUTED, height=17).pack(anchor=tk.W)
            value = ui.Line(left, textvariable=var, font=ui.mono(24, "bold"), fg=ui.ACCENT,
                            height=32)
            value.pack(anchor=tk.W)
            ui.Line(left, textvariable=real, font=ui.mono(11), fg=ui.MUTED, height=17).pack(
                anchor=tk.W
            )
            ToolTip(value.label, tip)
            ui.Chip(tile.body, badge, fill=fill, fg=fg, border=border, font=ui.mono(14, "bold"),
                    padx=9, height=36, radius=4).pack(side=tk.RIGHT)
        apply_row = tk.Frame(res, bg=ui.CARD)
        apply_row.pack(fill=tk.X, pady=(12, 0))
        self.btn_apply = ui.Button(
            apply_row, "Releer ganancias del equipo", command=ctrl.apply_atune, variant="soft",
            font=ui.sans(12, "bold"), height=30, radius=4, icon="sync", icon_size=16, gap=6,
            state=tk.DISABLED,
        )
        self.btn_apply.pack(side=tk.RIGHT)
        return box

    def _paint_progress(self) -> None:
        cv = self._progress_bar
        cv.delete("all")
        w = max(cv.winfo_width(), 10)
        ui.round_rect(cv, 0, 0, w, 10, 5, fill="#e7eef4")
        if self._progress_pct > 0:
            fw = max(10.0, w * min(self._progress_pct, 100) / 100.0)
            ui.round_rect(cv, 0, 0, fw, 10, 5, fill=ui.ACCENT)

    def _set_progress(self, pct: int, phase: str) -> None:
        self._progress_pct = int(pct)
        self._paint_progress()
        self.var_pct.set(f"{pct} %")
        self.var_phase.set(phase)
        self._phase_value.configure(fg=PROGRESS_COLORS.get(phase, ui.MUTED))
        for name, bit in self._legend_bits.items():
            on = name == phase
            bit.configure(
                fg=(PROGRESS_COLORS.get(name, ui.MUTED) if on else ui.FAINT),
                font=ui.sans(11, "bold" if on else "normal"),
            )

    def _on_temp_change(self) -> None:
        self.sync_chart_ylim()
        raw = self.var_ttemp.get().strip()
        self.chart.set_legend_text("set", f"SET ({raw} °C)" if raw else "SET")

    def _on_hyst_change(self) -> None:
        text = _hyst_text(self.var_thyst.get())
        self.var_hyst_txt.set(text)
        if self._hyst_range is not None:
            self._hyst_range.configure(text=f"1…99 ({text})")
        self.chart.set_legend_text("band", f"Banda histéresis ({text})")

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
        self._set_progress(0, "—")
        self.var_cycles.set(f"0 / {self._cycles_target}")
        self.telemetry.set_cycles(f"0 / {self._cycles_target}")
        self._atune_result_ready = False
        self.btn_apply.config(state=tk.DISABLED)
        self.dismiss_banner()

    def set_tune_running(self, running: bool) -> None:
        self._tune_running = bool(running)
        self.btn_tune.config(
            text=("Detener autoajuste" if self._tune_running else "Iniciar autoajuste"),
            style=("Danger.TButton" if self._tune_running else "Accent.TButton"),
            icon=("stop" if self._tune_running else "play"),
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
        self.telemetry.apply_hp(fields)
        self.status.apply_hp(fields, delay_cfg)
        try:
            fault = int(fields.get("FL", 0)) != 0
        except (TypeError, ValueError):
            fault = bool(fields.get("FL"))
        if fault:
            self._show_banner("Corte por falla", "— salidas desactivadas", ok=False)
        elif self._banner_title.cget("text") == "Corte por falla":
            self.dismiss_banner()

    def apply_atune_fields(self, fields: dict[str, Any]) -> None:
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        ap = fields.get("AP")
        tuning = p == 2 or a == 10 or ap is not None
        if not tuning:
            return

        if ap is not None:
            ac = int(fields.get("AC", 0))
            tgt = self._cycles_target
            pct = min(100, int(100 * ac / tgt)) if tgt > 0 else 0
            if int(ap) == 2:
                pct = 100
            self._set_progress(pct, proto.atune_phase_name(int(ap)))
            self.var_cycles.set(f"{ac} / {tgt}")
            self.telemetry.set_cycles(f"{ac} / {tgt}")
            if int(ap) == 2:
                self.var_ak.set(str(fields.get("AK", "—")))
                self.var_ai.set(str(fields.get("AI", "—")))
                try:
                    self.var_kp_real.set(f"Valor real {float(fields.get('AK')) / 10:.1f}")
                    self.var_ki_real.set(f"Valor real {float(fields.get('AI')) / 100:.2f}")
                except (TypeError, ValueError):
                    pass
                self._atune_result_ready = True
                self._show_banner(
                    "Autoajuste listo", "— Kp y Ki guardados en la EEPROM del equipo", ok=True
                )
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
            self.var_kp_real.set(f"Valor real {float(fields['KP']) / 10:.1f}")
        if "KI" in fields:
            self.var_ai.set(str(fields["KI"]))
            self.var_ki_real.set(f"Valor real {float(fields['KI']) / 100:.2f}")

    def hyst_band(self, set_c: float) -> tuple[float, float] | None:
        try:
            hyst = int(self.var_thyst.get()) / 10.0
            return set_c - hyst, set_c + hyst
        except ValueError:
            return None

    def apply_theme(self) -> None:
        self.status.apply_theme()
        if hasattr(self, "chart"):
            self.chart.apply_theme()
