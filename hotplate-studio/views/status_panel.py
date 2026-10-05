"""Estado del proceso ($HP) y HUD de telemetría, compartidos por HEAT y Autotune."""

from __future__ import annotations

from typing import Any, Optional

import tkinter as tk

import protocol as proto
import theme as ui_theme
from widgets import ui
from widgets.tooltip import ToolTip

# Dos columnas de bloques. La clave es corta (sin unidades; la unidad va en el
# valor) y el tooltip guarda el significado del campo en la trama.
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
                ("T", "Medida", "T= temperatura de la placa, o — si el sensor no vale."),
                ("SET", "Consigna", "SET= objetivo actual del lazo o del autoajuste."),
            ],
        ),
        (
            "Tiempos",
            [
                ("DLY", "Retraso", "DLY= espera antes de calentar, reloj hh:mm (tope 12:00)."),
                ("RUN", "Restante", "RUN= segundos que quedan en este paso."),
                ("EL", "Transcurrido", "EL= segundos desde el arranque del ciclo."),
            ],
        ),
    ],
    [
        (
            "Salidas",
            [
                ("DU", "Calentador", "DU= potencia del banco PTC, 0…100 %."),
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
        (
            "Sobre 183 °C",
            [
                (
                    "TL",
                    "Segundos",
                    "TL= segundos con la placa ≥ 183 °C. Sigue en la bajada. No es el tiempo de meseta.",
                ),
                (
                    "TC",
                    "Primer cruce",
                    "TC= transcurrido al cruzar 183 °C por primera vez.",
                ),
                ("PK", "Pico", "PK= pico de la placa en este ciclo."),
                (
                    "MS",
                    "Subida máx.",
                    "MS= máxima subida, en °C·10 por segundo.",
                ),
            ],
        ),
    ],
]

# Valores con color propio; el resto usa el color de "Estado · valores".
_VALUE_COLORS = {
    "T": ui.RED,
    "SET": ui.BLUE,
    "PHASE": ui.ACCENT,
    "RI": ui.ACCENT,
}
# Valores que se muestran en peso normal (dato secundario).
_LIGHT_VALUES = {"DLY"}


def _phase_dot(phase: int) -> str:
    if phase in (7, 9):
        return ui.RED
    if phase in (0, 8):
        return "#94a3b8"
    if phase == 1:
        return "#f39c12"
    return ui.GREEN


def _fmt_temp(value: Any) -> str:
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{v:.1f}" if isinstance(value, float) or "." in str(value) else f"{int(v)}"


def _fmt_clock(seconds: Any) -> str:
    try:
        sec = max(int(seconds), 0)
    except (TypeError, ValueError):
        return "—"
    return f"{sec // 60:02d}:{sec % 60:02d}"


class _HudCell(tk.Frame):
    def __init__(self, parent: tk.Misc, title: str, *, divider: bool, pad: tuple[int, int],
                 title_font: tuple, title_upper: bool = True,
                 divider_side: str = tk.LEFT) -> None:
        super().__init__(parent, bg=ui.CARD)
        if divider:
            ui.vline(self).pack(side=divider_side, fill=tk.Y)
        self.inner = tk.Frame(self, bg=ui.CARD)
        self.inner.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=pad)
        self.head = tk.Frame(self.inner, bg=ui.CARD)
        self.head.pack(fill=tk.X)
        ui.Line(
            self.head, title.upper() if title_upper else title, font=title_font,
            fg=ui.MUTED, height=15 if title_upper else 16,
        ).pack(side=tk.LEFT)


class HeatHud:
    """HUD de HEAT: 8 columnas con divisores (`grid-cols-8 divide-x`)."""

    def __init__(self, parent: tk.Misc) -> None:
        self.box = ui.Box(parent, fill=ui.CARD, border=ui.BORDER, radius=12, padx=20,
                          pady=(12, 13))
        self.frame = self.box
        body = self.box.body
        self.vars = {k: tk.StringVar(value="—") for k in ("T", "SET", "PHASE", "RI", "DU", "RUN", "EL", "F")}
        titles = (
            "Temperatura medida", "Consigna", "Fase", "Escalón",
            "Calentador", "Restante", "Transcurrido", "Aire",
        )
        head_font = ui.sans(10, "bold")
        cells: list[_HudCell] = []
        for col, title in enumerate(titles):
            pad = (0, 16) if col == 0 else ((16, 0) if col == 7 else (16, 16))
            cell = _HudCell(body, title, divider=col > 0, pad=pad, title_font=head_font)
            cell.grid(row=0, column=col, sticky=tk.EW)
            body.columnconfigure(col, weight=1, uniform="hud")
            cells.append(cell)
        body.rowconfigure(0, weight=1)

        def fit(e) -> None:
            # grid-cols-8 mientras quepa; si no, cada columna conserva su contenido.
            need = max(cell.winfo_reqwidth() for cell in cells) * len(cells)
            uniform = "hud" if e.width >= need else ""
            if getattr(body, "_hp_uniform", None) == uniform:
                return
            body._hp_uniform = uniform  # type: ignore[attr-defined]
            for col in range(len(cells)):
                body.columnconfigure(col, uniform=uniform)

        body.bind("<Configure>", fit, add="+")

        # 1. Temperatura medida
        c = cells[0].inner
        row = tk.Frame(c, bg=ui.CARD)
        row.pack(fill=tk.X, pady=(2, 0))
        self._t_value = ui.Line(row, "—", font=ui.mono(30, "bold"), fg=ui.RED, height=30)
        self._t_value.pack(side=tk.LEFT)
        ui.Line(row, "°C", font=ui.mono(12), fg=ui.MUTED, height=16).pack(
            side=tk.LEFT, padx=(4, 0), anchor=tk.S, pady=(0, 1)
        )
        sensor = ui.Chip(
            c, "Sensor PT100", fill=ui.BG, fg=ui.MUTED, border=ui.SUBTLE,
            font=ui.sans(10), padx=6, height=16, radius=4,
        )
        sensor.pack(anchor=tk.W, pady=(4, 0))
        ToolTip(self._t_value, "T= temperatura de la placa (PT100 · MAX31865).")

        # 2. Consigna
        c = cells[1].inner
        self._set_value = ui.Line(c, "—", font=ui.mono(16, "bold"), fg=ui.BLUE, height=24)
        self._set_value.pack(anchor=tk.W, pady=(4, 0))
        ui.Line(c, "Objetivo paso", font=ui.mono(10), fg=ui.FAINT, height=15).pack(
            anchor=tk.W, pady=(4, 0)
        )

        # 3. Fase
        c = cells[2].inner
        row = tk.Frame(c, bg=ui.CARD, height=24)
        row.pack(fill=tk.X, pady=(4, 0))
        self._phase_dot = ui.Dot(row, "#94a3b8", size=8, bg=ui.CARD)
        self._phase_dot.pack(side=tk.LEFT, padx=(0, 6))
        self._phase_value = ui.Line(row, "—", font=ui.sans(14, "bold"), fg=ui.TEXT, height=24)
        self._phase_value.pack(side=tk.LEFT)
        self._phase_sub = ui.Line(c, "—", font=ui.mono(10), fg=ui.FAINT, height=15)
        self._phase_sub.pack(anchor=tk.W, pady=(4, 0))

        # 4. Escalón
        c = cells[3].inner
        self._ri_value = ui.Line(c, "—", font=ui.mono(16, "bold"), fg=ui.ACCENT, height=24)
        self._ri_value.pack(anchor=tk.W, pady=(4, 0))
        self._ri_sub = ui.Line(c, "—", font=ui.mono(10), fg=ui.FAINT, height=15)
        self._ri_sub.pack(anchor=tk.W, pady=(4, 0))

        # 5. Calentador
        c = cells[4]
        self._du_value = ui.Line(c.head, "—", font=ui.mono(12, "bold"), fg=ui.GREEN, height=15)
        self._du_value.pack(side=tk.RIGHT)
        self._du_bar = tk.Canvas(c.inner, width=1, height=6, bg=ui.CARD, highlightthickness=0, bd=0)
        self._du_bar.pack(fill=tk.X, pady=(6, 6))
        self._du_bar.bind("<Configure>", lambda _e: self._paint_bar(), add="+")
        self._du_pct = 0.0
        ui.Line(c.inner, "Potencia DU", font=ui.mono(10), fg=ui.FAINT, height=15).pack(anchor=tk.W)

        # 6. Restante
        c = cells[5].inner
        self._run_value = ui.Line(c, "—", font=ui.mono(16, "bold"), fg=ui.TEXT, height=24)
        self._run_value.pack(anchor=tk.W, pady=(4, 0))
        ui.Line(c, "Paso actual", font=ui.mono(10), fg=ui.FAINT, height=15).pack(
            anchor=tk.W, pady=(4, 0)
        )

        # 7. Transcurrido
        c = cells[6].inner
        row = tk.Frame(c, bg=ui.CARD)
        row.pack(fill=tk.X, pady=(4, 0))
        self._el_value = ui.Line(row, "—", font=ui.mono(14, "bold"), fg=ui.TEXT, height=20)
        self._el_value.pack(side=tk.LEFT)
        self._el_clock = ui.Line(row, "", font=ui.mono(11), fg=ui.SLATE, height=20)
        self._el_clock.pack(side=tk.LEFT, padx=(4, 0))
        ui.Line(c, "Total ciclo", font=ui.mono(10), fg=ui.FAINT, height=15).pack(
            anchor=tk.W, pady=(4, 0)
        )

        # 8. Aire
        c = cells[7].inner
        self._fan_chip = ui.Chip(
            c, "—", fill="#f1f5f9", fg="#475569", border=ui.SUBTLE,
            font=ui.sans(12, "bold"), padx=6, height=22, radius=4,
        )
        self._fan_chip.pack(anchor=tk.W, pady=(4, 0))
        self._fan_sub = ui.Line(c, "Ventilador (F=0)", font=ui.mono(10), fg=ui.FAINT, height=15)
        self._fan_sub.pack(anchor=tk.W, pady=(4, 0))
        self._paint_bar()

    def _paint_bar(self) -> None:
        cv = self._du_bar
        cv.delete("all")
        w = max(cv.winfo_width(), 10)
        ui.round_rect(cv, 0, 0, w - 1, 5, 3, fill="#e7eef4", outline=ui.SUBTLE)
        if self._du_pct > 0:
            fw = max(6.0, (w - 2) * min(self._du_pct, 100.0) / 100.0)
            ui.round_rect(cv, 1, 1, 1 + fw, 5, 2, fill=ui.GREEN)

    def apply_hp(self, fields: dict[str, Any]) -> None:
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        temp = fields.get("T")
        self._t_value.configure(text=_fmt_temp(temp))
        set_v = fields.get("SET")
        self._set_value.configure(text=("—" if set_v is None else f"{set_v} °C"))
        self._phase_value.configure(text=proto.phase_name(a))
        self._phase_dot.set(_phase_dot(a))
        sub = {4: "Manteniendo", 5: "Subiendo", 1: "Esperando", 6: "Bajando"}.get(a, "—")
        self._phase_sub.configure(text=sub)
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        if p == 1 and a in (4, 5):
            self._ri_value.configure(text=f"Rampa {ri + 1}")
            self._ri_sub.configure(text=f"Paso {ri + 1} de {self.total_steps}")
        else:
            self._ri_value.configure(text="—")
            self._ri_sub.configure(text="—")
        du = fields.get("DU")
        try:
            self._du_pct = float(du)
        except (TypeError, ValueError):
            self._du_pct = 0.0
        self._du_value.configure(text=("—" if du is None else f"{du} %"))
        self._paint_bar()
        run = fields.get("RUN")
        self._run_value.configure(text=("—" if run is None else f"{run} s"))
        el = fields.get("EL")
        self._el_value.configure(text=("—" if el is None else f"{el} s"))
        self._el_clock.configure(text=("" if el is None else f"({_fmt_clock(el)})"))
        fan = str(fields.get("F", 0))
        self._fan_chip.set("Encendido" if fan == "1" else "Apagado")
        self._fan_sub.configure(text=f"Ventilador (F={fan})")

    total_steps = 4


class TuneHud:
    """HUD de Autotune: 7 métricas en fila (`flex justify-between`)."""

    def __init__(self, parent: tk.Misc) -> None:
        self.box = ui.Box(parent, fill=ui.CARD, border=ui.BORDER, radius=8, padx=24,
                          pady=(11, 12))
        self.frame = self.box
        body = self.box.body
        titles = ("Consigna", "Fase", "Ciclos", "Calentador", "Aire", "Transcurrido")
        cells: list[_HudCell] = []
        first = _HudCell(body, "Temperatura medida", divider=True, pad=(0, 32),
                         title_font=ui.sans(11, "bold"), divider_side=tk.RIGHT)
        first.grid(row=0, column=0, sticky=tk.NSEW)
        row = tk.Frame(first.inner, bg=ui.CARD)
        # items-baseline: el chip baja ~3 px bajo la línea del número.
        row.pack(fill=tk.X, pady=(2, 3))
        self._t_value = ui.Line(row, "—", font=ui.mono(36, "bold"), fg=ui.TEXT, height=36)
        self._t_value.pack(side=tk.LEFT)
        ui.Line(row, "°C", font=ui.mono(16), fg=ui.MUTED, height=24).pack(
            side=tk.LEFT, padx=(8, 0), anchor=tk.S
        )
        ui.Chip(
            row, "Sensor PT100", fill=ui.BG, fg=ui.MUTED, border=ui.SUBTLE,
            font=ui.sans(11), padx=6, height=18, radius=4,
        ).pack(side=tk.LEFT, padx=(16, 0), anchor=tk.S, pady=(0, 2))
        # justify-between + items-center: el hueco libre va entre celdas y cada una
        # (salvo la última) lleva su border-r a la altura de su propio contenido.
        for col, title in enumerate(titles, start=1):
            last = col == len(titles)
            cell = _HudCell(body, title, divider=not last,
                            pad=((24, 0) if last else (24, 24)),
                            title_font=ui.sans(11, "bold"), title_upper=False,
                            divider_side=tk.RIGHT)
            cell.grid(row=0, column=col * 2)
            body.columnconfigure(col * 2 - 1, weight=1)
            cells.append(cell)
        self._set_value = self._metric(cells[0], ui.BLUE)
        phase_row = tk.Frame(cells[1].inner, bg=ui.CARD, height=24)
        phase_row.pack(fill=tk.X, pady=(2, 0))
        self._phase_dot = ui.Dot(phase_row, "#94a3b8", size=8, bg=ui.CARD)
        self._phase_dot.pack(side=tk.LEFT, padx=(0, 6))
        self._phase_value = ui.Line(phase_row, "—", font=ui.sans(14, "bold"), height=20)
        self._phase_value.pack(side=tk.LEFT)
        self._cyc_value = self._metric(cells[2])
        self._du_value = self._metric(cells[3])
        self._fan_value = self._metric(cells[4])
        self._el_value = self._metric(cells[5])
        self._cycles_target: Optional[int] = None

    def _metric(self, cell: _HudCell, fg: str = ui.TEXT) -> ui.Line:
        line = ui.Line(cell.inner, "—", font=ui.mono(16, "bold"), fg=fg, height=24)
        line.pack(anchor=tk.W)
        return line

    def set_cycles(self, text: str) -> None:
        self._cyc_value.configure(text=text)

    def apply_hp(self, fields: dict[str, Any]) -> None:
        a = int(fields.get("A", 0))
        self._t_value.configure(text=_fmt_temp(fields.get("T")))
        set_v = fields.get("SET")
        self._set_value.configure(text=("—" if set_v is None else f"{set_v} °C"))
        ap = fields.get("AP")
        if ap is not None:
            name = proto.atune_phase_name(int(ap))
            dot = {1: ui.GREEN, 2: ui.GREEN, 3: ui.RED}.get(int(ap), "#94a3b8")
        else:
            name = proto.phase_name(a)
            dot = _phase_dot(a)
        self._phase_value.configure(text=name)
        self._phase_dot.set(dot)
        du = fields.get("DU")
        self._du_value.configure(text=("—" if du is None else f"{du} %"))
        self._fan_value.configure(text=("Encendido" if str(fields.get("F", 0)) == "1" else "Apagado"))
        el = fields.get("EL")
        self._el_value.configure(text=("—" if el is None else f"{el} s"))


class StatusPanel:
    """Tarjeta «Estado del proceso»: bloques grises de clave/valor en dos columnas."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        icon: str = "monitor",
        stream_chip: bool = True,
        split_profile: bool = True,
    ) -> None:
        self.frame = ui.card(parent)
        body = self.frame.body
        keys = [key for cols in STATUS_COLUMNS for _, rows in cols for key, _, _ in rows]
        self.vars = {key: tk.StringVar(value="—") for key in keys}
        self._section_labels: list[ui.Line] = []
        self._key_labels: list[ui.Line] = []
        self._value_labels: dict[str, ui.Line] = {}

        self.header = ui.CardHeader(body, "Estado del proceso", icon=icon)
        self.header.pack(fill=tk.X)
        self._stream_chip: Optional[ui.Chip] = None
        if stream_chip:
            self._stream_chip = ui.Chip(
                self.header.right, "Manual · sondeo", fill="#f1f5f9", fg=ui.SLATE,
                border="#e2e8f0", font=ui.mono(12), padx=8, height=22, radius=4,
            )
            self._stream_chip.pack(side=tk.RIGHT)

        grid = tk.Frame(body, bg=ui.CARD)
        grid.pack(fill=tk.X, pady=(12, 0))
        grid.columnconfigure(0, weight=1, uniform="status")
        grid.columnconfigure(1, weight=1, uniform="status")
        sections = {title: rows for column in STATUS_COLUMNS for title, rows in column}
        left = tk.Frame(grid, bg=ui.CARD)
        left.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 8))
        right = tk.Frame(grid, bg=ui.CARD)
        right.grid(row=0, column=1, sticky=tk.NSEW, padx=(8, 0))
        for title in ("Programa", "Temperatura", "Tiempos"):
            self._block(left, title, sections[title]).pack(fill=tk.X, pady=(0, 10))
        self._block(right, "Salidas", sections["Salidas"]).pack(fill=tk.X, pady=(0, 10))
        if split_profile:
            pair = tk.Frame(right, bg=ui.CARD)
            pair.pack(fill=tk.X, pady=(0, 10))
            pair.columnconfigure(0, weight=1, uniform="pair")
            pair.columnconfigure(1, weight=1, uniform="pair")
            prof = self._block(pair, "Perfil", sections["Perfil"])
            safe = self._block(pair, "Seguridad", sections["Seguridad"])

            def stack(e, prof=prof, safe=safe, pair=pair) -> None:
                side = e.width >= 2 * max(prof.winfo_reqwidth(), safe.winfo_reqwidth()) + 8
                if getattr(pair, "_hp_side", None) == side:
                    return
                pair._hp_side = side  # type: ignore[attr-defined]
                prof.grid(row=0, column=0, columnspan=(1 if side else 2), sticky=tk.NSEW,
                          padx=((0, 4) if side else 0), pady=(0 if side else (0, 10)))
                safe.grid(row=(0 if side else 1), column=(1 if side else 0),
                          columnspan=(1 if side else 2), sticky=tk.NSEW,
                          padx=((4, 0) if side else 0))

            pair.bind("<Configure>", stack, add="+")
            prof.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 4))
            safe.grid(row=0, column=1, sticky=tk.NSEW, padx=(4, 0))
            pair._hp_side = True  # type: ignore[attr-defined]
        else:
            for title in ("Perfil", "Seguridad"):
                self._block(right, title, sections[title]).pack(fill=tk.X, pady=(0, 10))
        self._block(right, "Sobre 183 °C", sections["Sobre 183 °C"]).pack(fill=tk.X)
        self._fault = False
        self.apply_theme()

    def _block(self, parent: tk.Misc, title: str, rows) -> ui.Box:
        box = ui.block(parent)
        inner = box.body
        sec = ui.Line(inner, title.upper(), font=ui.sans(10, "bold"), fg=ui.MUTED, height=16)
        sec.pack(anchor=tk.W)
        self._section_labels.append(sec)
        for key, label, tip in rows:
            row = tk.Frame(inner, bg=ui.BG)
            row.pack(fill=tk.X, pady=(4, 0))
            k = ui.Line(row, label, font=ui.mono(12), fg=ui.MUTED, height=16)
            k.pack(side=tk.LEFT)
            v = ui.Line(row, "—", font=ui.mono(12, "bold"), fg=ui.TEXT, height=16, anchor=tk.E)
            v.pack(side=tk.RIGHT, padx=(8, 0))
            ToolTip(k.label, tip)
            ToolTip(v.label, tip)
            self._key_labels.append(k)
            self._value_labels[key] = v
            self.vars[key].trace_add("write", lambda *_a, key=key: self._sync_value(key))
        return box

    def set_stream_mode(self, usb_mode: bool) -> None:
        if self._stream_chip is not None:
            self._stream_chip.set("$HP · 1 Hz" if usb_mode else "Manual · sondeo")

    def _sync_value(self, key: str) -> None:
        lbl = self._value_labels.get(key)
        if lbl is None:
            return
        text = self.vars[key].get()
        t = ui_theme.get()
        weight_key = "status_value_weight"
        if key in _LIGHT_VALUES or text == "—":
            font = ui_theme.mono_tuple("status_value_size")
        else:
            font = ui_theme.mono_tuple("status_value_size", weight_key)
        color = _VALUE_COLORS.get(key, str(t["status_value_color"]))
        if key == "DU":
            color = ui.GREEN if text not in ("—", "0 %") else str(t["status_value_color"])
        if key == "FL":
            color = ui.RED if self._fault else "#047857"
        if text == "—":
            color = str(t["status_value_color"])
        lbl.configure(text=text, font=font, fg=color)

    def apply_hp(self, fields: dict[str, Any], delay_cfg: str | None) -> None:
        t = fields.get("T")
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        self.vars["T"].set("—" if t is None else f"{_fmt_temp(t)} °C")
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
        run = fields.get("RUN")
        idle_run = run is None or (p != 1 and str(run) == "0")
        self.vars["RUN"].set("—" if idle_run else f"{run} s")
        el = fields.get("EL")
        self.vars["EL"].set("—" if el is None else f"{el} s")
        du = fields.get("DU")
        self.vars["DU"].set("—" if du is None else f"{du} %")
        fan = fields.get("F", 0)
        self.vars["F"].set(
            {0: "Apagado", 1: "Encendido", "0": "Apagado", "1": "Encendido"}.get(fan, str(fan))
        )
        fl = fields.get("FL", 0)
        try:
            self._fault = int(fl) != 0
        except (TypeError, ValueError):
            self._fault = bool(fl)
        self.vars["FL"].set("Sí" if self._fault else "No")
        try:
            ri = int(fields.get("RI", 0))
        except (TypeError, ValueError):
            ri = 0
        if p == 1 and a in (4, 5):
            self.vars["RI"].set(f"Rampa {ri + 1}")
        else:
            self.vars["RI"].set("—")
        tl = fields.get("TL")
        self.vars["TL"].set("—" if tl is None else f"{tl} s")
        tc = fields.get("TC")
        self.vars["TC"].set("—" if not tc else f"{tc} s")
        pk = fields.get("PK")
        self.vars["PK"].set("—" if not pk else f"{pk} °C")
        ms = fields.get("MS")
        if ms is None:
            self.vars["MS"].set("—")
        else:
            self.vars["MS"].set(f"{float(ms) / 10.0:.1f} °C/s")
        if a in (0, 8) and delay_cfg is not None:
            self.vars["DLY"].set(delay_cfg)

    def apply_theme(self) -> None:
        t = ui_theme.get()
        for lbl in self._section_labels:
            lbl.configure(
                font=ui_theme.font_tuple("section_title_size", "section_title_weight"),
                fg=t["section_title_color"],
            )
        for lbl in self._key_labels:
            lbl.configure(
                font=ui_theme.mono_tuple("status_key_size", "status_key_weight"),
                fg=t["status_key_color"],
            )
        for key in self._value_labels:
            self._sync_value(key)
