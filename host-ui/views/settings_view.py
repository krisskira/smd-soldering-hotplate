"""Pestaña Ajustes: límites, flujo HEAT, PID + apariencia."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import colorchooser, ttk

import protocol as proto
import theme as ui_theme
from constants import (
    PID_KI_DEFAULT,
    PID_KP_DEFAULT,
    TEMP_MAX_C_DEFAULT,
    TEMP_MIN_C_DEFAULT,
)
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

ENTRY_W = 12
FONT_FAMILIES = ("", "Helvetica", "Arial", "Menlo", "Courier", "Times")
WEIGHTS = ("normal", "bold")


def _num_entry(parent: ttk.Frame, var: tk.StringVar) -> ttk.Entry:
    return ttk.Entry(parent, textvariable=var, width=ENTRY_W, justify=tk.RIGHT)


def _delay_clock(parent: ttk.Frame, hours: tk.StringVar, minutes: tk.StringVar) -> ttk.Frame:
    """Reloj HH:MM. Horas 0…12, minutos 0…59."""
    box = ttk.Frame(parent)
    ttk.Spinbox(
        box, from_=0, to=12, width=3, textvariable=hours,
        justify=tk.RIGHT, format="%02.0f",
    ).pack(side=tk.LEFT)
    ttk.Label(box, text=":").pack(side=tk.LEFT, padx=2)
    ttk.Spinbox(
        box, from_=0, to=59, width=3, textvariable=minutes,
        justify=tk.RIGHT, format="%02.0f",
    ).pack(side=tk.LEFT)
    return box


def _labeled_row(
    parent: ttk.Frame,
    row: int,
    label: str,
    widget: tk.Misc,
    tip_title: str,
    tip_rango: str,
    tip_trama: str,
) -> None:
    lbl = ttk.Label(parent, text=label)
    lbl.grid(row=row, column=0, padx=4, pady=4, sticky=tk.W)
    widget.grid(row=row, column=1, padx=4, pady=4, sticky=tk.E)
    tip = f"{tip_title}\nRango / escala: {tip_rango}\nTrama / comando: {tip_trama}"
    ToolTip(lbl, tip)
    ToolTip(widget, tip)


def _save_bar(parent: ttk.LabelFrame, text: str, command) -> None:
    bar = ttk.Frame(parent)
    bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
    ttk.Button(bar, text=text, command=command).pack(side=tk.LEFT)


class SettingsView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self._theme_vars: dict[str, tk.Variable] = {}

        # Contenedor con scroll para caber equipo + tema
        outer = ttk.Frame(parent)
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content = ttk.Frame(canvas)
        win = canvas.create_window((0, 0), window=content, anchor=tk.NW)

        def _on_cfg(_e=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(win, width=canvas.winfo_width())

        content.bind("<Configure>", _on_cfg)
        canvas.bind("<Configure>", _on_cfg)

        top = ttk.Frame(content)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(top, text="Leer ajustes del equipo", command=ctrl.read_cfg).pack(
            side=tk.LEFT
        )

        grid = ttk.Frame(content)
        grid.pack(fill=tk.X, padx=8, pady=4)
        grid.columnconfigure(0, weight=1, uniform="set")
        grid.columnconfigure(1, weight=1, uniform="set")

        g1 = ttk.LabelFrame(grid, text="Límites de temperatura")
        g1.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 4), pady=4)
        _save_bar(g1, "Guardar límites", ctrl.write_safety)
        body1 = ttk.Frame(g1)
        body1.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_mn = tk.StringVar(value=str(TEMP_MIN_C_DEFAULT))
        self.var_mx = tk.StringVar(value=str(TEMP_MAX_C_DEFAULT))
        _labeled_row(
            body1, 0, "Temperatura mínima (°C)", _num_entry(body1, self.var_mn),
            "Temperatura mínima", "30…100 °C", "$CF MN=  ·  AT+CFG=S,<min>,<max>",
        )
        _labeled_row(
            body1, 1, "Temperatura máxima (°C)", _num_entry(body1, self.var_mx),
            "Temperatura máxima", "40…250 °C, ≥ mínima", "$CF MX=  ·  AT+CFG=S,<min>,<max>",
        )
        body1.columnconfigure(1, weight=1)

        g_pre = ttk.LabelFrame(grid, text="Meseta de las rampas")
        g_pre.grid(row=0, column=1, sticky=tk.NSEW, padx=(4, 0), pady=4)
        _save_bar(g_pre, "Guardar bandas", ctrl.write_heat)
        body_pre = ttk.Frame(g_pre)
        body_pre.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_bn = tk.StringVar(value="4")
        self.var_bx = tk.StringVar(value="6")
        _labeled_row(
            body_pre, 0, "Banda entrada (±°C)", _num_entry(body_pre, self.var_bn),
            "Banda para pasar de subida a meseta", "1…15 °C",
            "$CF BN=  ·  AT+CFG=B,<bn>,<bx>",
        )
        _labeled_row(
            body_pre, 1, "Banda salida (±°C)", _num_entry(body_pre, self.var_bx),
            "Se guarda con la banda de entrada",
            "≥ entrada … 20 °C. La meseta ya no se aborta por salirse",
            "$CF BX=  ·  AT+CFG=B,<bn>,<bx>",
        )
        body_pre.columnconfigure(1, weight=1)

        g_run = ttk.LabelFrame(grid, text="Arranque y finalización de HEAT")
        g_run.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 4), pady=4)
        _save_bar(g_run, "Guardar arranque / fin", ctrl.write_heat)
        body_run = ttk.Frame(g_run)
        body_run.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_dly_h = tk.StringVar(value="0")
        self.var_dly_m = tk.StringVar(value="0")
        self.var_air = tk.BooleanVar(value=True)
        self.var_dly_h.trace_add("write", self._lock_delay_at_12h)
        _labeled_row(
            body_run, 0, "Retraso de arranque",
            _delay_clock(body_run, self.var_dly_h, self.var_dly_m),
            "Retraso de arranque",
            "00:00 … 12:00 (horas:minutos). 00:00 = inmediato. En 12:00 los minutos quedan en 00",
            "$CF DLY=<s>  ·  AT+CFG=H,<s>,<air>  ·  también en $HP DLY=",
        )
        _labeled_row(
            body_run, 1, "Aire al enfriar",
            ttk.Checkbutton(body_run, variable=self.var_air),
            "Aire / ventilador al enfriar", "0 = off, 1 = on al terminar HEAT",
            "$CF AIR=  ·  AT+CFG=H",
        )
        body_run.columnconfigure(1, weight=1)

        g3 = ttk.LabelFrame(grid, text="Ganancias PI (valores ×10)")
        g3.grid(row=1, column=1, sticky=tk.NSEW, padx=(4, 0), pady=4)
        _save_bar(g3, "Sobrescribir valores PID", ctrl.write_pid)
        body_pid = ttk.Frame(g3)
        body_pid.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_kp = tk.StringVar(value=str(PID_KP_DEFAULT))
        self.var_ki = tk.StringVar(value=str(PID_KI_DEFAULT))
        for i, (lab, var, tip_name, trama) in enumerate(
            [
                ("Proporcional Kp", self.var_kp, "Kp ×10", "$CF KP=  ·  AT+CFG=P"),
                ("Integral Ki", self.var_ki, "Ki ×10", "$CF KI=  ·  AT+CFG=P"),
            ]
        ):
            _labeled_row(
                body_pid, i, lab, _num_entry(body_pid, var),
                tip_name, "0…999 (unidad ×10 en EEPROM)", trama,
            )
        body_pid.columnconfigure(1, weight=1)

        ttk.Label(
            content,
            text=(
                "Guardar bandas envía AT+CFG=B. Guardar arranque / fin envía "
                "AT+CFG=H,<delay>,<air>."
            ),
            wraplength=900,
        ).pack(anchor=tk.W, padx=8, pady=(0, 4))

        self._build_theme_panel(content)

    def _build_theme_panel(self, parent: ttk.Frame) -> None:
        box = ttk.LabelFrame(parent, text="Apariencia de la aplicación")
        box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 12))

        bar = ttk.Frame(box)
        bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        ttk.Button(bar, text="Aplicar y guardar tema", command=self._ctrl.save_theme).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(
            bar, text="Restaurar defaults", command=self._ctrl.reset_theme
        ).pack(side=tk.LEFT)

        nb = ttk.Notebook(box)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_f = ttk.Frame(nb)
        tab_c = ttk.Frame(nb)
        tab_log = ttk.Frame(nb)
        tab_ui = ttk.Frame(nb)
        nb.add(tab_f, text="Fuentes")
        nb.add(tab_c, text="Gráficas")
        nb.add(tab_log, text="Consola serie")
        nb.add(tab_ui, text="Controles")

        t = ui_theme.load()
        self._fill_theme_vars(t)

        # --- Fuentes ---
        self._font_row(tab_f, 0, "Familia general", "font_family", FONT_FAMILIES)
        self._size_weight_color(
            tab_f, 1, "Títulos de frames (LabelFrame)",
            "frame_title_size", "frame_title_weight", "frame_title_color",
        )
        self._size_weight_color(
            tab_f, 2, "Títulos de sección (Estado del proceso)",
            "section_title_size", "section_title_weight", "section_title_color",
        )
        self._size_weight_color(
            tab_f, 3, "Claves (etiquetas de estado)",
            "status_key_size", "status_key_weight", "status_key_color",
        )
        self._size_weight_color(
            tab_f, 4, "Valores (estado del proceso)",
            "status_value_size", "status_value_weight", "status_value_color",
        )

        # --- Gráficas ---
        chart_rows = [
            ("Temperatura medida", "chart_temp"),
            ("SET / objetivo", "chart_set"),
            ("Potencia DU", "chart_duty"),
            ("Marcador cruce ↑", "chart_mark_up"),
            ("Marcador cruce ↓", "chart_mark_down"),
            ("Calentador ON", "chart_mark_on"),
            ("Calentador OFF", "chart_mark_off"),
            ("Cresta", "chart_mark_peak"),
            ("Inicio de fase", "chart_phase"),
            ("Banda histéresis", "chart_band"),
            ("Fondo de ejes", "chart_face"),
        ]
        for i, (lab, key) in enumerate(chart_rows):
            self._color_row(tab_c, i, lab, key)

        # --- Consola ---
        self._font_row(
            tab_log, 0, "Familia (consola)", "console_font_family",
            ("Menlo", "Courier", "Monaco", "Consolas", "Helvetica"),
        )
        self._spin_row(tab_log, 1, "Tamaño", "console_font_size", 8, 22)
        self._color_row(tab_log, 2, "Fondo", "console_bg")
        self._color_row(tab_log, 3, "Texto", "console_fg")
        self._color_row(tab_log, 4, "Borde", "console_border")

        # --- Controles ---
        self._spin_row(tab_ui, 0, "Texto general (pt)", "body_size", 8, 18)
        self._color_row(tab_ui, 1, "Color texto general", "body_color")
        self._spin_row(tab_ui, 2, "Inputs (pt)", "input_size", 8, 18)
        self._spin_row(tab_ui, 3, "Botones (pt)", "button_size", 8, 18)

    def _fill_theme_vars(self, t: dict[str, Any]) -> None:
        for k, v in t.items():
            if isinstance(v, bool):
                self._theme_vars[k] = tk.BooleanVar(value=v)
            elif isinstance(v, int):
                self._theme_vars[k] = tk.IntVar(value=v)
            else:
                self._theme_vars[k] = tk.StringVar(value=str(v))

    def _var(self, key: str) -> tk.Variable:
        return self._theme_vars[key]

    def _font_row(
        self, parent: ttk.Frame, row: int, label: str, key: str, families: tuple
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=3)
        cb = ttk.Combobox(
            parent, textvariable=self._var(key), values=list(families), width=16
        )
        cb.grid(row=row, column=1, sticky=tk.W, padx=6, pady=3)

    def _spin_row(
        self, parent: ttk.Frame, row: int, label: str, key: str, lo: int, hi: int
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=3)
        sp = ttk.Spinbox(
            parent, from_=lo, to=hi, textvariable=self._var(key), width=8
        )
        sp.grid(row=row, column=1, sticky=tk.W, padx=6, pady=3)

    def _color_row(self, parent: ttk.Frame, row: int, label: str, key: str) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=3)
        fr = ttk.Frame(parent)
        fr.grid(row=row, column=1, sticky=tk.W, padx=6, pady=3)
        ent = ttk.Entry(fr, textvariable=self._var(key), width=10)
        ent.pack(side=tk.LEFT)
        swatch = tk.Label(fr, width=3, background=str(self._var(key).get()))
        swatch.pack(side=tk.LEFT, padx=4)

        def pick(_k=key, _sw=swatch) -> None:
            cur = str(self._var(_k).get())
            rgb, hx = colorchooser.askcolor(color=cur, title=label)
            if hx:
                self._var(_k).set(hx)
                _sw.configure(background=hx)

        def sync_swatch(*_a, _k=key, _sw=swatch) -> None:
            try:
                _sw.configure(background=str(self._var(_k).get()))
            except Exception:
                pass

        self._var(key).trace_add("write", sync_swatch)
        ttk.Button(fr, text="…", width=3, command=pick).pack(side=tk.LEFT)

    def _size_weight_color(
        self,
        parent: ttk.Frame,
        row: int,
        label: str,
        size_k: str,
        weight_k: str,
        color_k: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=3)
        fr = ttk.Frame(parent)
        fr.grid(row=row, column=1, sticky=tk.W, padx=6, pady=3)
        ttk.Spinbox(
            fr, from_=8, to=22, textvariable=self._var(size_k), width=5
        ).pack(side=tk.LEFT)
        ttk.Combobox(
            fr, textvariable=self._var(weight_k), values=list(WEIGHTS), width=8
        ).pack(side=tk.LEFT, padx=4)
        ent = ttk.Entry(fr, textvariable=self._var(color_k), width=9)
        ent.pack(side=tk.LEFT)
        swatch = tk.Label(fr, width=3, background=str(self._var(color_k).get()))
        swatch.pack(side=tk.LEFT, padx=4)

        def pick(_k=color_k, _sw=swatch) -> None:
            rgb, hx = colorchooser.askcolor(
                color=str(self._var(_k).get()), title=label
            )
            if hx:
                self._var(_k).set(hx)
                _sw.configure(background=hx)

        def sync(*_a, _k=color_k, _sw=swatch) -> None:
            try:
                _sw.configure(background=str(self._var(_k).get()))
            except Exception:
                pass

        self._var(color_k).trace_add("write", sync)
        ttk.Button(fr, text="…", width=3, command=pick).pack(side=tk.LEFT)

    def collect_theme(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, var in self._theme_vars.items():
            default = ui_theme.DEFAULT_THEME[k]
            raw = var.get()
            if isinstance(default, int):
                try:
                    out[k] = int(raw)
                except (TypeError, ValueError):
                    out[k] = default
            else:
                out[k] = str(raw)
        return out

    def reload_theme_vars(self) -> None:
        t = ui_theme.get()
        for k, v in t.items():
            if k in self._theme_vars:
                self._theme_vars[k].set(v)

    def _lock_delay_at_12h(self, *_args: object) -> None:
        try:
            hours = int(self.var_dly_h.get())
        except (TypeError, ValueError):
            return
        if hours >= 12 and self.var_dly_m.get() not in ("0", "00"):
            self.var_dly_m.set("0")

    def delay_seconds(self) -> int:
        hours = int(self.var_dly_h.get())
        minutes = 0 if hours >= 12 else int(self.var_dly_m.get())
        return proto.delay_hm_to_s(hours, minutes)

    def delay_clock(self) -> str:
        return proto.fmt_hhmm_s(self.delay_seconds())

    def apply_cf(self, fields: dict[str, Any], state_tmin_tmax) -> None:
        if "MN" in fields:
            self.var_mn.set(str(fields["MN"]))
            state_tmin_tmax.tmin = int(fields["MN"])
        if "MX" in fields:
            self.var_mx.set(str(fields["MX"]))
            state_tmin_tmax.tmax = int(fields["MX"])
        if "AIR" in fields:
            self.var_air.set(int(fields["AIR"]) != 0)
        if "DLY" in fields:
            try:
                hours, minutes = proto.delay_s_to_hm(int(fields["DLY"]))
            except (TypeError, ValueError):
                hours, minutes = 0, 0
            self.var_dly_h.set(str(hours))
            self.var_dly_m.set(str(minutes))
        for src, var in (
            ("BN", self.var_bn),
            ("BX", self.var_bx),
            ("KP", self.var_kp),
            ("KI", self.var_ki),
        ):
            if src in fields:
                var.set(str(fields[src]))
