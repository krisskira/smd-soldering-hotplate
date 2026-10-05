"""Pestaña HEAT: acción + HUD · perfil y estado · curva con registro de eventos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk

import protocol as proto
import theme as ui_theme
from chart import HEAT_LEGEND, LiveChart
from constants import TEMP_SET_CEILING_C
from views.status_panel import HeatHud, StatusPanel, _fmt_clock
from widgets import ui
from widgets.tooltip import ToolTip

# Margen del eje Y de temperatura por encima del escalón más alto activo.
CHART_HEAT_Y_MARGIN_C = 50.0

ACTIVE_ROW_BG = "#e8f1f8"
ACTIVE_ROW_MARK = "#dae1ea"
ROW_H = 39
COL_USE = 48
COL_NUM = 112

if TYPE_CHECKING:
    from controller import AppController


class HeatView:
    def __init__(self, parent: tk.Misc, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self._heat_running = False
        self._hi = (0, 0, 0)
        self._applying_ramps = False
        self._synced_snapshot = None

        page = ui.ScrollPage(parent)
        page.pack(fill=tk.BOTH, expand=True)
        self.page = page
        root = tk.Frame(page.inner, bg=ui.BG)
        root.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # 1 · Fila de acción
        top = tk.Frame(root, bg=ui.BG, height=36)
        top.pack(fill=tk.X)
        top.pack_propagate(False)
        self.btn_heat = ui.Button(
            top, "Iniciar HEAT", command=ctrl.toggle_heat, variant="primary",
            font=ui.sans(14), padx=16, height=36, radius=8, icon="play", icon_size=18,
        )
        self.btn_heat.pack(side=tk.LEFT)
        ToolTip(self.btn_heat, "Inicia o detiene HEAT (AT+RUN=1 / AT+STOP).")
        self.phase_chip = ui.Chip(
            top, "Inactivo", fill="#f0f9ff", fg=ui.ACCENT, border="#bae6fd",
            font=ui.sans(12, "bold"), padx=12, height=30, radius=15, dot="#94a3b8",
        )
        self.phase_chip.pack(side=tk.LEFT, padx=(12, 0))
        self.run_note = ui.Line(top, "", font=ui.mono(12), fg=ui.SLATE, height=16)
        self.run_note.pack(side=tk.LEFT, padx=(12, 0))
        self.banner = ui.label(top, "", font=ui.sans(12, "bold"), fg=ui.RED, anchor=tk.E)
        self.banner.pack(side=tk.RIGHT)

        # 2 · HUD
        self.telemetry = HeatHud(root)
        self.telemetry.frame.pack(fill=tk.X, pady=(16, 0))

        # 3 · Perfil + estado
        row = tk.Frame(root, bg=ui.BG)
        row.pack(fill=tk.X, pady=(16, 0))
        row.columnconfigure(0, weight=1, uniform="cards")
        row.columnconfigure(1, weight=1, uniform="cards")
        self._build_ramps_panel(row)
        self._ramps_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 8))
        self.status = StatusPanel(row, icon="monitor", stream_chip=True, split_profile=True)
        self.status.frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(8, 0))

        # 4 · Curva
        self.chart = LiveChart(
            root,
            title="Curva en vivo",
            on_export=ctrl.export_csv,
            on_export_events=ctrl.export_heat_events,
            on_clear=ctrl.clear_plot,
            x_span_s=self.planned_x_span(),
            x_locked=False,
            legend=HEAT_LEGEND,
        )
        self.chart.frame.pack(fill=tk.X, pady=(16, 0))
        self._sync_chart_ylim()
        self.apply_theme()

    # ------------------------------------------------------------ perfil
    def _build_ramps_panel(self, parent: tk.Misc) -> None:
        box = ui.card(parent)
        self._ramps_frame = box
        body = box.body
        head = ui.CardHeader(body, "Soldering Profile", icon="tune")
        head.pack(fill=tk.X)
        self.sync_chip = ui.Chip(
            head.right, "Cambios sin guardar", fill="#f1f5f9", fg="#475569",
            border="#e2e8f0", font=ui.sans(12), padx=10, height=22, radius=11,
        )
        self.sync_chip.pack(side=tk.RIGHT)
        ui.Line(
            body, "Escalones contiguos desde la rampa 1. Guardar envía el perfil; Leer pide $R.",
            font=ui.sans(11), fg=ui.MUTED, height=17,
        ).pack(anchor=tk.W, pady=(8, 12))

        table = ui.Box(body, fill=ui.CARD, border=ui.BORDER, radius=6)
        table.pack(fill=tk.X)
        tbody = table.body
        hdr = tk.Frame(tbody, bg=ui.BG, height=32)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        hdr.grid_propagate(False)
        self._grid_columns(hdr)
        for col, title in enumerate(("USAR", "ESCALÓN", "°C", "S (MESETA)")):
            ui.Line(
                hdr, title, font=ui.sans(11, "bold"), fg=ui.MUTED, height=16, bg=ui.BG,
                anchor=(tk.CENTER if col == 0 else tk.W),
            ).grid(row=0, column=col, sticky=(tk.EW if col == 0 else tk.W),
                   padx=(0 if col == 0 else 12, 0), pady=(7, 7))
        ui.hline(tbody).pack(fill=tk.X)

        self.ramp_active: list[tk.BooleanVar] = []
        self.ramp_temp: list[tk.StringVar] = []
        self.ramp_hold: list[tk.StringVar] = []
        self.ramp_row_labels: list[ui.Line] = []
        self._ramp_checks: list[ui.CheckBox] = []
        self._ramp_rows: list[dict[str, Any]] = []

        for i in range(4):
            if i:
                ui.hline(tbody).pack(fill=tk.X)
            av = tk.BooleanVar(value=(i < 2))
            tv = tk.StringVar(value=str(100 + 25 * i))
            hv = tk.StringVar(value="60")
            self.ramp_active.append(av)
            self.ramp_temp.append(tv)
            self.ramp_hold.append(hv)
            rowf = tk.Frame(tbody, bg=ui.CARD, height=ROW_H - 1)
            rowf.pack(fill=tk.X)
            rowf.pack_propagate(False)
            rowf.grid_propagate(False)
            marker = tk.Frame(rowf, bg=ui.CARD, width=3)
            marker.place(x=0, y=0, relheight=1)
            self._grid_columns(rowf)
            rowf.rowconfigure(0, weight=1)
            cb = ui.CheckBox(rowf, av, size=16, fade=False)
            if i == 0:
                av.set(True)
                cb.set_disabled(True)
            else:
                cb.configure(command=self._on_ramp_active_toggle)
            cb.grid(row=0, column=0)
            self._ramp_checks.append(cb)
            rl = ui.Line(rowf, f"Rampa {i + 1}", font=ui.sans(12), fg=ui.TEXT, height=16)
            rl.grid(row=0, column=1, sticky=tk.W, padx=(12, 0))
            self.ramp_row_labels.append(rl)
            cells = []
            for col, (var, unit) in enumerate(((tv, "°C"), (hv, "s")), start=2):
                cell = tk.Frame(rowf, bg=ui.CARD)
                cell.grid(row=0, column=col, sticky=tk.W, padx=(12, 0))
                field = ui.Field(cell, var, width=64, height=26, font=ui.mono(12))
                field.pack(side=tk.LEFT)
                unit_lbl = ui.label(cell, unit, font=ui.mono(11), fg=ui.MUTED)
                unit_lbl.pack(side=tk.LEFT, padx=(4, 0))
                cells.append((cell, field, unit_lbl))
            ToolTip(cells[0][1].entry, f"°C del escalón {i + 1} · no decreciente · AT+CFG=R")
            ToolTip(cells[1][1].entry, f"Meseta del escalón {i + 1} en segundos · 1…3600")
            self._ramp_rows.append(dict(frame=rowf, marker=marker, check=cb, label=rl, cells=cells))

        foot = tk.Frame(body, bg=ui.CARD)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        ui.hline(foot).pack(fill=tk.X, pady=(16, 12))
        btns = tk.Frame(foot, bg=ui.CARD)
        btns.pack(fill=tk.X)
        ui.Button(btns, "Leer rampas", command=self._ctrl.read_ramps, variant="secondary",
                  height=30, radius=6).pack(side=tk.LEFT)
        ui.Button(btns, "Guardar rampas activas", command=self._ctrl.write_all_ramps,
                  variant="primary", font=ui.sans(12, "bold"), padx=16, height=32,
                  radius=8).pack(side=tk.RIGHT)
        notes = tk.Frame(foot, bg=ui.CARD)
        notes.pack(fill=tk.X, pady=(6, 0))
        rules = ui.Line(
            notes,
            f"1–4 escalones · °C no decreciente, Tmin…{TEMP_SET_CEILING_C} °C · meseta 1…3600 s",
            font=ui.sans(10), fg=ui.FAINT, height=15,
        )
        eeprom = ui.Line(
            notes, "El equipo corre el perfil guardado en EEPROM",
            font=ui.sans(10, italic=True), fg=ui.MUTED, height=15,
        )

        def place_notes(e) -> None:
            inline = e.width >= rules.winfo_reqwidth() + eeprom.winfo_reqwidth() + 12
            if getattr(notes, "_hp_inline", None) == inline:
                return
            notes._hp_inline = inline  # type: ignore[attr-defined]
            eeprom.grid(row=(0 if inline else 1), column=(1 if inline else 0),
                        sticky=("e" if inline else "w"))

        notes.columnconfigure(1, weight=1)
        rules.grid(row=0, column=0, sticky="w")
        eeprom.grid(row=0, column=1, sticky="e")
        notes._hp_inline = True  # type: ignore[attr-defined]
        notes.bind("<Configure>", place_notes, add="+")

        for v in self.ramp_temp + self.ramp_hold + self.ramp_active:
            v.trace_add("write", lambda *_: self._on_ramp_edit())

    @staticmethod
    def _grid_columns(frame: tk.Frame) -> None:
        frame.columnconfigure(0, minsize=COL_USE, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, minsize=COL_NUM, weight=0)
        frame.columnconfigure(3, minsize=COL_NUM, weight=0)

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
            text=("Detener HEAT" if self._heat_running else "Iniciar HEAT"),
            style=("Danger.TButton" if self._heat_running else "Accent.TButton"),
            icon=("stop" if self._heat_running else "play"),
        )
        if not self._heat_running:
            self.run_note.configure(text="")

    def is_heat_running(self) -> bool:
        return self._heat_running

    def _on_ramp_edit(self) -> None:
        self.sync_chart_x()
        self._sync_chart_ylim()
        self.refresh_objetivo()
        self.telemetry.total_steps = sum(1 for v in self.ramp_active if v.get())
        if not self._applying_ramps:
            self.sync_chip.set("Cambios sin guardar", fill="#fff4ce", fg="#9a6700",
                               border="#f5d77a")

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
        self._applying_ramps = True
        for i in range(4):
            if i < len(steps):
                temp, hold = steps[i]
                if temp > 0:
                    self.ramp_temp[i].set(str(temp))
                if hold > 0:
                    self.ramp_hold[i].set(str(hold))
            self.ramp_active[i].set(i < n)
        self.ramp_active[0].set(True)
        self._applying_ramps = False
        self._synced_snapshot = self.ramp_snapshot()
        self.sync_chip.set("Sincronizado con el equipo", fill="#f1f5f9", fg="#475569",
                           border="#e2e8f0")
        self.sync_chart_x()
        self._sync_chart_ylim()
        self.refresh_objetivo()

    def apply_hp(self, fields: dict[str, Any], delay_cfg: str | None) -> None:
        self.telemetry.apply_hp(fields)
        self.status.apply_hp(fields, delay_cfg)
        self._update_fault_banner(fields.get("FL", 0))
        self.refresh_objetivo()
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        phase = int(fields.get("A", 0))
        prog = int(fields.get("P", 0))
        phase_text = proto.phase_name(phase)
        if phase in (4, 5):
            phase_text = f"{phase_text} · Rampa {ri + 1}"
        dot = {0: "#94a3b8", 8: "#94a3b8", 1: "#f39c12", 7: ui.RED, 9: ui.RED}.get(phase, ui.GREEN)
        self.phase_chip.set(phase_text, dot=dot)
        if prog == 1 and phase in (1, 2, 3, 4, 5, 6, 7):
            self.run_note.configure(text=f"AT+RUN=1 · en curso {_fmt_clock(fields.get('EL', 0))}")
        elif not self._heat_running:
            self.run_note.configure(text="")
        self.highlight_ramp(prog, phase, ri)

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
        body = ui_theme.px("body_size")
        fam = ui_theme.ui_family()
        for i, row in enumerate(self._ramp_rows):
            on = prog == 1 and phase in (4, 5) and i == ri
            bg = ACTIVE_ROW_BG if on else ui.CARD
            row["frame"].configure(bg=bg)
            row["marker"].configure(bg=(ACTIVE_ROW_MARK if on else bg))
            row["marker"].lift()
            row["check"].set_outer_bg(bg)
            row["label"].configure(
                text=("► Rampa " if on else "Rampa ") + str(i + 1),
                font=(fam, -body, "bold" if on else "normal"),
                fg=(ui.ACCENT if on else ui.TEXT),
                bg=bg,
            )
            for cell, field, unit in row["cells"]:
                cell.configure(bg=bg)
                field.set_outer_bg(bg)
                field.set_border(ui.BORDER if on else ui.SUBTLE)
                unit.configure(bg=bg)

    def set_banner(self, text: str, color: str = "#a00") -> None:
        self.banner.config(text=text, fg=color)

    def apply_theme(self) -> None:
        self.banner.configure(font=ui_theme.font_tuple("body_size", None))
        self.status.apply_theme()
        prog, phase, ri = self._hi
        self.highlight_ramp(prog, phase, ri)
        if hasattr(self, "chart"):
            self.chart.apply_theme()

    def has_active_ramps(self) -> bool:
        self.ramp_active[0].set(True)
        return True
