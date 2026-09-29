"""Estado del proceso ($HP), compartido por HEAT y Autotune."""

from __future__ import annotations

from typing import Any

import tkinter as tk
from tkinter import ttk

import protocol as proto
import theme as ui_theme
from widgets.tooltip import ToolTip

# Dos columnas. La etiqueta corta cabe junto al panel de configuración;
# el tooltip guarda el significado del campo en la trama.
STATUS_COLUMNS: list[list[tuple[str, list[tuple[str, str, str]]]]] = [
    [
        (
            "Programa",
            [
                ("PROG", "Programa", "P= en $HP. HEAT o Autoajuste."),
                ("PHASE", "Fase", "A= en $HP. Nombre de la fase en curso."),
            ],
        ),
        (
            "Temperatura",
            [
                ("T", "Medida (°C)", "T= temperatura de la placa, o — si el sensor no vale."),
                ("SET", "Consigna (°C)", "SET= objetivo actual del lazo o del autoajuste."),
            ],
        ),
        (
            "Tiempos",
            [
                ("DLY", "Retraso", "DLY= espera antes de calentar, reloj hh:mm (tope 12:00)."),
                ("RUN", "Restante (s)", "RUN= segundos que quedan en este paso."),
                ("EL", "Transcurrido (s)", "EL= segundos desde el arranque del ciclo."),
            ],
        ),
    ],
    [
        (
            "Salidas",
            [
                ("DU", "Calentador (%)", "DU= potencia del banco PTC, 0…100 %."),
                ("F", "Aire", "F= ventilador. En HEAT, al enfriar si el aire está activo."),
            ],
        ),
        (
            "Perfil",
            [
                ("RI", "Escalón", "RI= rampa en curso durante subida o meseta de HEAT."),
            ],
        ),
        (
            "Seguridad",
            [
                ("FL", "Falla", "FL= corte por falla. Las salidas quedan apagadas."),
            ],
        ),
    ],
]


class StatusPanel:
    def __init__(self, parent: ttk.Frame) -> None:
        self.frame = ttk.LabelFrame(parent, text="Estado del proceso")
        keys = [
            key
            for cols in STATUS_COLUMNS
            for _, rows in cols
            for key, _, _ in rows
        ]
        self.vars = {key: tk.StringVar(value="—") for key in keys}
        self._section_labels: list[ttk.Label] = []
        self._key_labels: list[ttk.Label] = []
        self._value_labels: list[ttk.Label] = []

        body = ttk.Frame(self.frame)
        body.pack(anchor=tk.NW, padx=6, pady=6)
        for col_i, sections in enumerate(STATUS_COLUMNS):
            col = ttk.Frame(body)
            col.grid(row=0, column=col_i, sticky=tk.NW, padx=(0, 10) if col_i == 0 else 0)
            row = 0
            for title, fields in sections:
                st = ttk.Label(col, text=title, anchor=tk.W)
                st.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
                self._section_labels.append(st)
                row += 1
                ttk.Separator(col, orient=tk.HORIZONTAL).grid(
                    row=row, column=0, columnspan=2, sticky=tk.EW, pady=(0, 3)
                )
                row += 1
                for key, label, tip in fields:
                    k_lbl = ttk.Label(col, text=label, anchor=tk.W)
                    k_lbl.grid(row=row, column=0, sticky=tk.W, padx=(4, 10), pady=1)
                    v_lbl = ttk.Label(col, textvariable=self.vars[key], anchor=tk.W)
                    v_lbl.grid(row=row, column=1, sticky=tk.W, pady=1)
                    ToolTip(k_lbl, tip)
                    ToolTip(v_lbl, tip)
                    self._key_labels.append(k_lbl)
                    self._value_labels.append(v_lbl)
                    row += 1
        self.apply_theme()

    def apply_hp(self, fields: dict[str, Any], delay_cfg: str | None) -> None:
        t = fields.get("T")
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        self.vars["T"].set("—" if t is None else f"{t} °C")
        set_v = fields.get("SET")
        self.vars["SET"].set("—" if set_v is None else f"{set_v} °C")
        self.vars["PHASE"].set(proto.phase_name(a))
        self.vars["PROG"].set(proto.prog_name(p) if p in (1, 2) else "—")
        dly = fields.get("DLY", "—")
        try:
            dly_txt = proto.fmt_hhmm_s(int(dly))
        except (TypeError, ValueError):
            dly_txt = str(dly)
        self.vars["DLY"].set(dly_txt)
        self.vars["RUN"].set(str(fields.get("RUN", "—")))
        self.vars["EL"].set(str(fields.get("EL", "—")))
        self.vars["DU"].set(str(fields.get("DU", "—")))
        fan = fields.get("F", 0)
        self.vars["F"].set(
            {0: "Apagado", 1: "Encendido", "0": "Apagado", "1": "Encendido"}.get(
                fan, str(fan)
            )
        )
        fl = fields.get("FL", 0)
        self.vars["FL"].set(
            {0: "No", 1: "Sí", "0": "No", "1": "Sí"}.get(fl, str(fl))
        )
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        if p == 1 and a in (4, 5):
            self.vars["RI"].set(f"Rampa {ri + 1}")
        else:
            self.vars["RI"].set("—")
        if a in (0, 8) and delay_cfg is not None:
            self.vars["DLY"].set(delay_cfg)

    def apply_theme(self) -> None:
        t = ui_theme.get()
        for lbl in self._section_labels:
            lbl.configure(
                font=ui_theme.font_tuple("section_title_size", "section_title_weight"),
                foreground=t["section_title_color"],
            )
        for lbl in self._key_labels:
            lbl.configure(
                font=ui_theme.font_tuple("status_key_size", "status_key_weight"),
                foreground=t["status_key_color"],
            )
        for lbl in self._value_labels:
            lbl.configure(
                font=ui_theme.font_tuple("status_value_size", "status_value_weight"),
                foreground=t["status_value_color"],
            )
