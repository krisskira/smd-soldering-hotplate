"""Pestaña Ajustes: límites, flujo HEAT, PID (rejilla 2 columnas)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

ENTRY_W = 12


def _num_entry(parent: ttk.Frame, var: tk.StringVar) -> ttk.Entry:
    return ttk.Entry(parent, textvariable=var, width=ENTRY_W, justify=tk.RIGHT)


def _tip(widget: tk.Misc, title: str, rangos: str, trama: str) -> None:
    ToolTip(
        widget,
        f"{title}\nRango / escala: {rangos}\nTrama / comando: {trama}",
    )


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
    """Botón de guardar anclado abajo a la izquierda del frame."""
    bar = ttk.Frame(parent)
    bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
    ttk.Button(bar, text=text, command=command).pack(side=tk.LEFT)


class SettingsView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl

        top = ttk.Frame(parent)
        top.pack(fill=tk.X, padx=8, pady=6)
        ttk.Button(top, text="Leer ajustes del equipo", command=ctrl.read_cfg).pack(
            side=tk.LEFT
        )

        grid = ttk.Frame(parent)
        grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        grid.columnconfigure(0, weight=1, uniform="set")
        grid.columnconfigure(1, weight=1, uniform="set")

        # --- Límites ---
        g1 = ttk.LabelFrame(grid, text="Límites de temperatura")
        g1.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 4), pady=4)
        _save_bar(g1, "Guardar límites", ctrl.write_safety)
        body1 = ttk.Frame(g1)
        body1.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_mn = tk.StringVar(value="40")
        self.var_mx = tk.StringVar(value="200")
        _labeled_row(
            body1, 0, "Temperatura mínima (°C)", _num_entry(body1, self.var_mn),
            "Temperatura mínima", "30…100 °C", "$CF MN=  ·  AT+CFG=S,<min>,<max>",
        )
        _labeled_row(
            body1, 1, "Temperatura máxima (°C)", _num_entry(body1, self.var_mx),
            "Temperatura máxima", "40…250 °C, ≥ mínima", "$CF MX=  ·  AT+CFG=S,<min>,<max>",
        )
        body1.columnconfigure(1, weight=1)

        # --- Precalentado ---
        g_pre = ttk.LabelFrame(grid, text="Precalentado (fase de HEAT)")
        g_pre.grid(row=0, column=1, sticky=tk.NSEW, padx=(4, 0), pady=4)
        _save_bar(g_pre, "Guardar precalentado", ctrl.write_heat)
        body_pre = ttk.Frame(g_pre)
        body_pre.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_ph = tk.BooleanVar(value=True)
        self.var_pct = tk.StringVar(value="80")
        self.var_sb = tk.StringVar(value="30")
        _labeled_row(
            body_pre, 0, "Activar precalentado",
            ttk.Checkbutton(body_pre, variable=self.var_ph),
            "Activar precalentado", "0 = apagado, 1 = activo",
            "$CF PH=  ·  AT+CFG=H,<en>,…",
        )
        _labeled_row(
            body_pre, 1, "% de la rampa 1", _num_entry(body_pre, self.var_pct),
            "% de la rampa 1", "50…100, paso 5", "$CF PCT=  ·  AT+CFG=H",
        )
        _labeled_row(
            body_pre, 2, "Estabilización (s)", _num_entry(body_pre, self.var_sb),
            "Tiempo de estabilización", "1…3600 s", "$CF SB=  ·  AT+CFG=H",
        )
        body_pre.columnconfigure(1, weight=1)

        # --- Arranque ---
        g_run = ttk.LabelFrame(grid, text="Arranque y finalización de HEAT")
        g_run.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 4), pady=4)
        _save_bar(g_run, "Guardar arranque / fin", ctrl.write_heat)
        body_run = ttk.Frame(g_run)
        body_run.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_dly = tk.StringVar(value="0")
        self.var_air = tk.BooleanVar(value=True)
        self.var_snd = tk.BooleanVar(value=True)
        _labeled_row(
            body_run, 0, "Retraso de arranque (s)", _num_entry(body_run, self.var_dly),
            "Retraso de arranque", "0…3600 s (0 = inmediato)",
            "$CF DLY=  ·  AT+CFG=H  ·  también en $HP DLY=",
        )
        _labeled_row(
            body_run, 1, "Aire al enfriar",
            ttk.Checkbutton(body_run, variable=self.var_air),
            "Aire / ventilador al enfriar", "0 = off, 1 = on al terminar HEAT",
            "$CF AIR=  ·  AT+CFG=H",
        )
        _labeled_row(
            body_run, 2, "Sonido de navegación",
            ttk.Checkbutton(body_run, variable=self.var_snd),
            "Sonido de navegación (beeps UI)", "0 = off, 1 = on",
            "$CF SND=  ·  AT+CFG=H",
        )
        body_run.columnconfigure(1, weight=1)

        # --- PID ---
        g3 = ttk.LabelFrame(grid, text="Ganancias PID (valores ×10)")
        g3.grid(row=1, column=1, sticky=tk.NSEW, padx=(4, 0), pady=4)
        _save_bar(g3, "Sobrescribir valores PID", ctrl.write_pid)
        body_pid = ttk.Frame(g3)
        body_pid.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.var_kp = tk.StringVar(value="20")
        self.var_ki = tk.StringVar(value="5")
        self.var_kd = tk.StringVar(value="10")
        for i, (lab, var, tip_name, trama) in enumerate(
            [
                ("Proporcional Kp", self.var_kp, "Kp ×10", "$CF KP=  ·  AT+CFG=P"),
                ("Integral Ki", self.var_ki, "Ki ×10", "$CF KI=  ·  AT+CFG=P"),
                ("Derivativo Kd", self.var_kd, "Kd ×10", "$CF KD=  ·  AT+CFG=P"),
            ]
        ):
            _labeled_row(
                body_pid, i, lab, _num_entry(body_pid, var),
                tip_name, "0…999 (unidad ×10 en EEPROM)", trama,
            )
        body_pid.columnconfigure(1, weight=1)

        ttk.Label(
            parent,
            text=(
                "Guardar precalentado y Guardar arranque / fin envían juntos "
                "AT+CFG=H (flujo HEAT completo)."
            ),
            wraplength=900,
        ).pack(anchor=tk.W, padx=8, pady=(0, 8))

    def apply_cf(self, fields: dict[str, Any], state_tmin_tmax) -> None:
        if "MN" in fields:
            self.var_mn.set(str(fields["MN"]))
            state_tmin_tmax.tmin = int(fields["MN"])
        if "MX" in fields:
            self.var_mx.set(str(fields["MX"]))
            state_tmin_tmax.tmax = int(fields["MX"])
        if "PH" in fields:
            self.var_ph.set(int(fields["PH"]) != 0)
        if "AIR" in fields:
            self.var_air.set(int(fields["AIR"]) != 0)
        if "SND" in fields:
            self.var_snd.set(int(fields["SND"]) != 0)
        for src, var in (
            ("PCT", self.var_pct),
            ("SB", self.var_sb),
            ("DLY", self.var_dly),
            ("KP", self.var_kp),
            ("KI", self.var_ki),
            ("KD", self.var_kd),
        ):
            if src in fields:
                var.set(str(fields[src]))

    def preheat_en_str(self) -> str:
        return "1" if self.var_ph.get() else "0"
