"""Pestaña Ajustes: límites, bandas de meseta, arranque de HEAT y ganancias PI."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Optional

import tkinter as tk

import protocol as proto
from constants import (
    PID_KI_DEFAULT,
    PID_KP_DEFAULT,
    TEMP_MAX_C_DEFAULT,
    TEMP_MAX_C_HI,
    TEMP_MIN_C_DEFAULT,
    TEMP_SET_CEILING_C,
)
from widgets import ui
from widgets.tooltip import ToolTip

if TYPE_CHECKING:
    from controller import AppController

PRIMARY_DARK = "#003b5a"
TERMINAL_BG = "#1e1e1e"


def _tip(title: str, rango: str, trama: str) -> str:
    return f"{title}\nRango / escala: {rango}\nTrama / comando: {trama}"


class SettingsView:
    def __init__(self, parent: tk.Misc, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.var_mn = tk.StringVar(value=str(TEMP_MIN_C_DEFAULT))
        self.var_mx = tk.StringVar(value=str(TEMP_MAX_C_DEFAULT))
        self.var_bn = tk.StringVar(value="4")
        self.var_bx = tk.StringVar(value="6")
        self.var_dly_h = tk.StringVar(value="0")
        self.var_dly_m = tk.StringVar(value="0")
        self.var_air = tk.BooleanVar(value=True)
        self.var_kp = tk.StringVar(value=str(PID_KP_DEFAULT))
        self.var_ki = tk.StringVar(value=str(PID_KI_DEFAULT))
        self.tx_safety = tk.StringVar()
        self.tx_band = tk.StringVar()
        self.tx_heat = tk.StringVar()
        self.tx_pid = tk.StringVar()
        self.var_kp_real = tk.StringVar(value="—")
        self.var_ki_real = tk.StringVar(value="—")
        self.last_read = tk.StringVar(value="Todavía no leído del equipo")

        page = ui.ScrollPage(parent)
        page.pack(fill=tk.BOTH, expand=True)
        self.page = page
        root = tk.Frame(page.inner, bg=ui.BG)
        root.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 24))

        # Cabecera
        hero = ui.Box(root, fill=ui.CARD, border=ui.SUBTLE, radius=12, padx=20, pady=20)
        hero.pack(fill=tk.X)
        left = tk.Frame(hero.body, bg=ui.CARD)
        left.pack(side=tk.LEFT)
        ui.Line(left, "Ajustes del equipo", font=ui.sans(18, "bold"), fg=ui.TEXT, height=28).pack(
            anchor=tk.W
        )
        ui.Line(
            left,
            "Límites, bandas de meseta, arranque de HEAT y ganancias PI. "
            "Se guardan en la EEPROM del equipo.",
            font=ui.sans(12), fg=ui.MUTED, height=16,
        ).pack(anchor=tk.W, pady=(2, 0))
        right = tk.Frame(hero.body, bg=ui.CARD)
        right.pack(side=tk.RIGHT)
        ui.Button(right, "Leer ajustes del equipo", command=ctrl.read_cfg, variant="secondary",
                  font=ui.sans(12, "bold"), height=30, radius=8, icon="sync", icon_size=15,
                  gap=6).pack(side=tk.RIGHT)
        ui.Line(right, textvariable=self.last_read, font=ui.mono(12), fg=ui.MUTED,
                height=16).pack(side=tk.RIGHT, padx=(0, 12))

        grid = tk.Frame(root, bg=ui.BG)
        grid.pack(fill=tk.X, pady=(20, 0))
        grid.columnconfigure(0, weight=1, uniform="settings")
        grid.columnconfigure(1, weight=1, uniform="settings")

        # 1 · Límites
        body, fields = self._card(
            grid, 0, 0, "1. Límites de temperatura", ui.RED, self.tx_safety,
            "Guardar límites", ctrl.write_safety,
        )
        self._number_field(
            fields, 0, "Temperatura mínima", self.var_mn, "°C", "Rango: 30 … 100 °C",
            "Fin del enfriamiento de HEAT",
            _tip("Temperatura mínima", "30…100 °C", "$CF MN=  ·  AT+CFG=S,<min>,<max>"),
        )
        self._number_field(
            fields, 1, "Temperatura máxima", self.var_mx, "°C",
            f"Rango: 40 … {TEMP_MAX_C_HI} °C (≥ mínima)", "Corte de seguridad: salidas OFF",
            _tip(
                "Temperatura máxima",
                f"40…{TEMP_MAX_C_HI} °C, ≥ mínima. Corte de seguridad; la consigna no pasa "
                f"de {TEMP_SET_CEILING_C} °C",
                "$CF MX=  ·  AT+CFG=S,<min>,<max>",
            ),
        )
        self._callout(
            body,
            f"La consigna nunca pasa de {TEMP_SET_CEILING_C} °C ni de la máxima. Deja la "
            "máxima unos °C por encima de la consigna más alta.",
            icon="info", icon_color=ui.BLUE, fill=ui.SOFT, border=ui.SOFT_HOVER, fg=ui.TEXT,
        )

        # 2 · Bandas
        body, fields = self._card(
            grid, 0, 1, "2. Meseta de las rampas", ui.BLUE, self.tx_band,
            "Guardar bandas", ctrl.write_heat,
        )
        self._number_field(
            fields, 0, "Banda de entrada", self.var_bn, "±°C", "Rango: 1 … 15 °C",
            "Con |T−SET| ≤ banda empieza a contar la meseta",
            _tip("Banda para pasar de subida a meseta", "1…15 °C",
                 "$CF BN=  ·  AT+CFG=B,<bn>,<bx>"),
        )
        self._number_field(
            fields, 1, "Banda de salida", self.var_bx, "±°C", "Rango: entrada … 20 °C",
            "La meseta ya no se aborta por salirse de la banda",
            _tip("Se guarda con la banda de entrada",
                 "≥ entrada … 20 °C. La meseta ya no se aborta por salirse",
                 "$CF BX=  ·  AT+CFG=B,<bn>,<bx>"),
        )
        self._callout(
            body,
            "Define el rango de tolerancia para dar por alcanzada y sostenida la "
            "temperatura objetivo.",
            icon="tune", icon_color=ui.MUTED, fill=ui.blend(ui.BG, ui.CARD, 0.6),
            border=ui.blend(ui.SUBTLE, ui.CARD, 0.6), fg=ui.MUTED, center=True,
        )

        # 3 · Arranque y fin
        body, fields = self._card(
            grid, 1, 0, "3. Arranque y fin de HEAT", ui.GREEN, self.tx_heat,
            "Guardar arranque / fin", ctrl.write_heat,
        )
        self._delay_field(fields)
        self._air_field(fields)
        self._callout(
            body,
            "El retraso programa una cuenta atrás antes de ejecutar el ciclo térmico "
            "seleccionado.",
            icon="timer", icon_color=ui.MUTED, fill=ui.blend(ui.BG, ui.CARD, 0.6),
            border=ui.blend(ui.SUBTLE, ui.CARD, 0.6), fg=ui.MUTED, center=True,
        )

        # 4 · Ganancias PI
        body, fields = self._card(
            grid, 1, 1, "4. Ganancias PI", "#006497", self.tx_pid,
            "Sobrescribir valores PID", ctrl.write_pid, danger=True,
        )
        self._gain_field(
            fields, 0, "Proporcional Kp (×10)", self.var_kp, "/ 10", self.var_kp_real,
            _tip("Kp ×10", "0…999 (Kp ×10 en EEPROM)", "$CF KP=  ·  AT+CFG=P"),
        )
        self._gain_field(
            fields, 1, "Integral Ki (×100)", self.var_ki, "/ 100", self.var_ki_real,
            _tip("Ki ×100", "0…999 (Ki ×100 en EEPROM)", "$CF KI=  ·  AT+CFG=P"),
        )
        self._callout(
            body, "El autoajuste las escribe al terminar. El lazo no usa Kd.",
            icon="info", icon_color=ui.MUTED, fill=ui.BG, border=ui.SUBTLE, fg=ui.MUTED,
        )

        self.var_dly_h.trace_add("write", self._lock_delay_at_12h)
        for var in (
            self.var_mn, self.var_mx, self.var_bn, self.var_bx, self.var_dly_h,
            self.var_dly_m, self.var_air, self.var_kp, self.var_ki,
        ):
            var.trace_add("write", self._update_previews)
        self._update_previews()

    # -------------------------------------------------------------- piezas
    def _card(
        self, parent: tk.Misc, row: int, col: int, title: str, accent: str,
        tx_var: tk.StringVar, button: str, command: Callable[[], None], danger: bool = False,
    ) -> tuple[tk.Frame, tk.Frame]:
        box = ui.Box(parent, fill=ui.CARD, border=ui.SUBTLE, radius=12, accent=accent,
                     accent_width=6, padx=(5, 3), pady=(3, 3))
        box.grid(row=row, column=col, sticky=tk.NSEW,
                 padx=((0, 10) if col == 0 else (10, 0)), pady=((0, 20) if row == 0 else 0))
        parent.rowconfigure(row, weight=1)
        inner = box.body
        foot = tk.Frame(inner, bg=ui.BG, height=50)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        foot.pack_propagate(False)
        box.add_band(foot, ui.BG, "bottom")
        ui.hline(foot).pack(side=tk.TOP, fill=tk.X)
        ui.Chip(foot, textvariable=tx_var, fill=TERMINAL_BG, fg=ui.GREEN, font=ui.mono(12),
                padx=8, height=21, radius=4, bg=ui.BG).pack(side=tk.LEFT, padx=(18, 0), pady=(3, 0))
        ui.Button(foot, button, command=command,
                  variant=("outline-danger" if danger else "primary"),
                  font=ui.sans(12, "bold"), padx=16, height=28, radius=8,
                  bg=ui.BG).pack(side=tk.RIGHT, padx=(0, 16), pady=(3, 0))
        body = tk.Frame(inner, bg=ui.CARD)
        body.pack(fill=tk.BOTH, expand=True, padx=(18, 16), pady=(16, 20))
        ui.Line(body, title, font=ui.sans(14, "bold"), fg=ui.TEXT, height=20).pack(anchor=tk.W)
        fields = tk.Frame(body, bg=ui.CARD)
        fields.pack(fill=tk.X, pady=(15, 0))
        fields.columnconfigure(0, weight=1, uniform="fields")
        fields.columnconfigure(1, weight=1, uniform="fields")
        return body, fields

    def _cell(self, parent: tk.Frame, col: int) -> tk.Frame:
        cell = tk.Frame(parent, bg=ui.CARD)
        cell.grid(row=0, column=col, sticky=tk.NSEW, padx=((0, 8) if col == 0 else (8, 0)))
        return cell

    def _number_field(
        self, parent: tk.Frame, col: int, label: str, var: tk.StringVar, suffix: str,
        range_text: str, help_text: str, tip: str,
    ) -> None:
        cell = self._cell(parent, col)
        lbl = ui.Line(cell, label, font=ui.sans(12, "bold"), fg=ui.TEXT, height=18)
        lbl.pack(anchor=tk.W)
        field = ui.Field(cell, var, height=30, font=ui.mono(12), fill=ui.BG, border=ui.SUBTLE,
                         radius=8, padx=12, justify=tk.LEFT, suffix=suffix,
                         suffix_font=ui.mono(12))
        field.pack(fill=tk.X, pady=(4, 0))
        ui.Line(cell, range_text, font=ui.mono(11), fg=ui.MUTED, height=17).pack(
            anchor=tk.W, pady=(1, 0)
        )
        ui.Paragraph(cell, help_text, font=ui.sans(11), fg=ui.MUTED, line_h=14).pack(
            fill=tk.X, pady=(6, 0)
        )
        ToolTip(lbl.label, tip)
        ToolTip(field.entry, tip)

    def _delay_field(self, parent: tk.Frame) -> None:
        cell = self._cell(parent, 0)
        tip = _tip(
            "Retraso de arranque",
            "00:00 … 12:00 (horas:minutos). 00:00 = inmediato. En 12:00 los minutos quedan en 00",
            "$CF DLY=<s>  ·  AT+CFG=H,<s>,<air>  ·  también en $HP DLY=",
        )
        lbl = ui.Line(cell, "Retraso de arranque", font=ui.sans(12, "bold"), fg=ui.TEXT,
                      height=18)
        lbl.pack(anchor=tk.W)
        clock = ui.Box(cell, fill=ui.BG, border=ui.SUBTLE, radius=8, padx=8, pady=4)
        clock.pack(fill=tk.X, pady=(4, 0))
        for index, (var, hi) in enumerate(((self.var_dly_h, 12), (self.var_dly_m, 59))):
            if index:
                ui.label(clock.body, ":", font=ui.mono(12, "bold"), fg=ui.MUTED).pack(
                    side=tk.LEFT, padx=6
                )
            field = ui.Field(clock.body, var, width=48, height=22, font=ui.mono(12),
                             justify=tk.CENTER, padx=4)
            field.pack(side=tk.LEFT)
            field.entry.bind("<MouseWheel>", lambda e, v=var, h=hi: self._step(v, h, e), add="+")
            field.entry.bind("<Up>", lambda _e, v=var, h=hi: self._step(v, h, None, 1), add="+")
            field.entry.bind("<Down>", lambda _e, v=var, h=hi: self._step(v, h, None, -1), add="+")
            ToolTip(field.entry, tip)
        ui.label(clock.body, "hh:mm", font=ui.mono(12), fg=ui.MUTED).pack(side=tk.LEFT, padx=(10, 0))
        ui.Line(cell, "Rango: 00:00 … 12:00", font=ui.mono(11), fg=ui.MUTED, height=17).pack(
            anchor=tk.W, pady=(2, 0)
        )
        ui.Paragraph(cell, "00:00 = inmediato; a las 12 h los minutos quedan en 00",
                     font=ui.sans(11), fg=ui.MUTED, line_h=14).pack(fill=tk.X, pady=(5, 0))
        ToolTip(lbl.label, tip)

    @staticmethod
    def _step(var: tk.StringVar, hi: int, event, delta: Optional[int] = None) -> str:
        if delta is None:
            delta = 1 if event is not None and event.delta > 0 else -1
        try:
            value = int(var.get())
        except (TypeError, ValueError):
            value = 0
        var.set(f"{max(0, min(hi, value + delta)):02d}")
        return "break"

    def _air_field(self, parent: tk.Frame) -> None:
        cell = self._cell(parent, 1)
        tip = _tip("Aire / ventilador al enfriar", "0 = off, 1 = on al terminar HEAT",
                   "$CF AIR=  ·  AT+CFG=H")
        ui.Line(cell, "Ventilación asistida", font=ui.sans(12, "bold"), fg=ui.TEXT,
                height=18).pack(anchor=tk.W)
        box = ui.Box(cell, fill=ui.BG, border=ui.SUBTLE, radius=8, padx=10, pady=10)
        box.pack(fill=tk.X, pady=(4, 0))
        check = ui.CheckBox(box.body, self.var_air, size=16)
        check.pack(side=tk.LEFT, anchor=tk.N, pady=(2, 0))
        col = tk.Frame(box.body, bg=ui.BG)
        col.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        title = ui.Line(col, "Aire al enfriar", font=ui.sans(12, "bold"), fg=ui.TEXT, height=16)
        title.pack(anchor=tk.W)
        ui.Paragraph(col, "Ventilador encendido en Alarma y Enfriando hasta Tmin",
                     font=ui.sans(11), fg=ui.MUTED, line_h=14).pack(fill=tk.X, pady=(2, 0))
        for widget in (title.label, box.body, col):
            widget.bind("<ButtonRelease-1>", lambda _e: self.var_air.set(not self.var_air.get()),
                        add="+")
        ToolTip(check, tip)
        ToolTip(title.label, tip)

    def _gain_field(
        self, parent: tk.Frame, col: int, label: str, var: tk.StringVar, suffix: str,
        real_var: tk.StringVar, tip: str,
    ) -> None:
        cell = self._cell(parent, col)
        lbl = ui.Line(cell, label, font=ui.sans(12, "bold"), fg=ui.TEXT, height=16)
        lbl.pack(anchor=tk.W)
        field = ui.Field(cell, var, height=30, font=ui.mono(12), fill=ui.BG, border=ui.SUBTLE,
                         radius=8, padx=12, justify=tk.LEFT, suffix=suffix,
                         suffix_font=ui.mono(12))
        field.pack(fill=tk.X, pady=(4, 0))
        row = tk.Frame(cell, bg=ui.CARD, height=17)
        row.pack(fill=tk.X, pady=(4, 0))
        row.pack_propagate(False)
        ui.Line(row, "Rango: 0 … 999", font=ui.mono(11), fg=ui.MUTED, height=17).pack(side=tk.LEFT)
        ui.Line(row, textvariable=real_var, font=ui.mono(11, "bold"), fg=PRIMARY_DARK,
                height=17).pack(side=tk.RIGHT)
        ui.Line(row, "Valor real:", font=ui.mono(11), fg=ui.TEXT, height=17).pack(
            side=tk.RIGHT, padx=(0, 6)
        )
        ToolTip(lbl.label, tip)
        ToolTip(field.entry, tip)

    def _callout(
        self, parent: tk.Frame, text: str, *, icon: str, icon_color: str, fill: str,
        border: str, fg: str, center: bool = False,
    ) -> None:
        box = ui.Box(parent, fill=fill, border=border, radius=8, padx=10, pady=10)
        box.pack(fill=tk.X, pady=(20, 0))
        ui.Icon(box.body, icon, size=16, color=icon_color, bg=fill).pack(
            side=tk.LEFT, anchor=(tk.CENTER if center else tk.N), pady=(0 if center else 1, 0)
        )
        lbl = ui.label(box.body, text, font=ui.sans(12), fg=fg, justify=tk.LEFT, anchor=tk.W)
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        box.body.bind("<Configure>", lambda e: lbl.configure(wraplength=max(e.width - 30, 120)),
                      add="+")

    # --------------------------------------------------------------- datos
    def apply_theme(self) -> None:
        pass

    def _update_previews(self, *_args: object) -> None:
        try:
            delay = self.delay_seconds()
        except (TypeError, ValueError):
            delay = "?"
        self.tx_safety.set(f"TX: AT+CFG=S,{self.var_mn.get()},{self.var_mx.get()}")
        self.tx_band.set(f"TX: AT+CFG=B,{self.var_bn.get()},{self.var_bx.get()}")
        self.tx_heat.set(f"TX: AT+CFG=H,{delay},{1 if self.var_air.get() else 0}")
        self.tx_pid.set(f"TX: AT+CFG=P,{self.var_kp.get()},{self.var_ki.get()}")
        try:
            self.var_kp_real.set(f"{float(self.var_kp.get()) / 10.0:.1f}")
        except ValueError:
            self.var_kp_real.set("—")
        try:
            self.var_ki_real.set(f"{float(self.var_ki.get()) / 100.0:.2f}")
        except ValueError:
            self.var_ki_real.set("—")

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
        self.last_read.set(
            f"Leído del equipo ($CF) · {datetime.now().strftime('%H:%M:%S')}"
        )
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
            self.var_dly_h.set(f"{hours:02d}")
            self.var_dly_m.set(f"{minutes:02d}")
        for src, var in (
            ("BN", self.var_bn),
            ("BX", self.var_bx),
            ("KP", self.var_kp),
            ("KI", self.var_ki),
        ):
            if src in fields:
                var.set(str(fields[src]))
