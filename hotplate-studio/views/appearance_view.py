"""Pestaña Apariencia: fuentes, gráficas y consola de HotPlate Studio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

import tkinter as tk
from tkinter import colorchooser

import theme as ui_theme
from widgets import ui

if TYPE_CHECKING:
    from controller import AppController

SYSTEM = "Sistema"
FONT_FAMILIES = (SYSTEM, "Helvetica", "Arial", "Menlo", "Courier", "Times")
CONSOLE_FAMILIES = (SYSTEM, "Menlo", "Courier", "Monaco", "Consolas", "Helvetica")
WEIGHTS = ("normal", "bold")
FAMILY_KEYS = ("font_family", "console_font_family")

LABEL = "#334155"
INPUT_BORDER = "#cbd5e1"
PANEL = "#f8fafc"
PANEL_BORDER = "#e2e8f0"
CAPTION = "#64748b"
SWATCH_BORDER = "#9ca3af"
GAP = 32
INPUT_H = 34
SIZE_RANGE = (6, 40)

CHART_ROWS = (
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
)

CAPTION_PREVIEW = "Previsualización inmediata según los valores configurados a la izquierda."
CAPTION_CONSOLE = "La consola usa esta familia, tamaño y colores. El tráfico no cambia."
CONSOLE_SAMPLE = (
    "18:02:11.440  TX  AT",
    "18:02:11.477  RX  OK",
    "18:02:11.553  RX  $HP,T=31.6,P=0,A=0,SET=0,DLY=0,RUN=0,EL=0,DU=0,F=0,RI=0,FL=0,TL=0",
)


class AppearanceView:
    def __init__(self, parent: tk.Misc, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self._theme_vars: dict[str, tk.Variable] = {}
        self._fill_theme_vars(ui_theme.load())

        page = ui.ScrollPage(parent)
        page.pack(fill=tk.BOTH, expand=True)
        self.page = page
        root = tk.Frame(page.inner, bg=ui.BG)
        root.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        head = tk.Frame(root, bg=ui.BG)
        head.pack(fill=tk.X)
        left = tk.Frame(head, bg=ui.BG)
        left.pack(side=tk.LEFT)
        ui.Line(left, "Apariencia", font=ui.sans(20, "bold"), fg=ui.TEXT, height=28).pack(
            anchor=tk.W
        )
        ui.Line(
            left,
            "Familia, texto, campos y botones cubren toda la interfaz. "
            "El estado del proceso usa sus propias filas de sección, clave y valor.",
            font=ui.sans(13), fg=ui.MUTED, height=20,
        ).pack(anchor=tk.W, pady=(2, 0))
        right = tk.Frame(head, bg=ui.BG)
        right.pack(side=tk.RIGHT, anchor=tk.N, pady=(4, 0))
        ui.Line(right, "ui_theme.json", font=ui.mono(12), fg=ui.MUTED, height=16).pack(
            side=tk.RIGHT
        )
        ui.Chip(
            right, "Solo en este equipo", fill="#f1f5f9", fg="#475569", border=INPUT_BORDER,
            font=ui.sans(11, "bold"), padx=8, height=23, radius=4,
        ).pack(side=tk.RIGHT, padx=(0, 10))

        card = ui.Box(root, fill=ui.CARD, border=ui.BORDER, radius=4, padx=1, pady=1)
        card.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        body = card.body

        tabs = tk.Frame(body, bg=ui.CARD)
        tabs.pack(fill=tk.X, padx=18)
        tab_rule = ui.hline(body, ui.SUBTLE)
        tab_rule.pack(fill=tk.X)
        card.add_band(tab_rule, ui.SUBTLE, "top", rule=False)
        card.add_band(tabs, ui.CARD, "top", rule=False)

        foot = tk.Frame(body, bg=PANEL)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        card.add_band(foot, PANEL, "bottom", rule=False)
        foot_rule = ui.hline(foot, PANEL_BORDER)
        foot_rule.pack(fill=tk.X)
        bar = tk.Frame(foot, bg=PANEL)
        bar.pack(fill=tk.X, padx=22, pady=12)
        ui.Button(
            bar, "Aplicar y guardar tema", command=ctrl.save_theme, variant="primary",
            font=ui.sans(12, "bold"), padx=16, height=28, radius=4,
        ).pack(side=tk.LEFT)
        restore = ui.Button(
            bar, "Restaurar defaults", command=ctrl.reset_theme, variant="white",
            font=ui.sans(12), padx=16, height=28, radius=4,
        )
        restore.pack(side=tk.LEFT, padx=(12, 0))

        self._host = tk.Frame(body, bg=ui.CARD)
        self._host.pack(fill=tk.BOTH, expand=True)
        self._tabs: dict[str, tuple[tk.Frame, tk.Frame, tk.Canvas]] = {}
        self._pages: dict[str, tk.Frame] = {}
        for name in ("Fuentes", "Gráficas", "Consola serie"):
            self._make_tab(tabs, name)

        form_f, prev_f = self._split("Fuentes", CAPTION_PREVIEW)
        form_c, prev_c = self._split("Gráficas", CAPTION_PREVIEW)
        form_s, prev_s = self._split("Consola serie", CAPTION_CONSOLE)

        rows_f = [
            lambda p: self._select_row(p, "Familia general", "font_family", FONT_FAMILIES),
            lambda p: self._number_row(p, "Texto general (px)", "body_size"),
            lambda p: self._color_row(p, "Color del texto general", "body_color"),
            lambda p: self._number_row(p, "Campos (px)", "input_size"),
            lambda p: self._number_row(p, "Botones (px)", "button_size"),
            None,
            lambda p: self._style_row(p, "Títulos de paneles", "frame_title"),
            lambda p: self._style_row(p, "Estado · títulos de sección", "section_title"),
            lambda p: self._style_row(p, "Estado · etiquetas", "status_key"),
            lambda p: self._style_row(p, "Estado · valores", "status_value"),
        ]
        self._stack(form_f, rows_f, gap=14, label_span=5)
        self._stack(
            form_c,
            [(lambda p, lab=lab, key=key: self._color_row(p, lab, key)) for lab, key in CHART_ROWS],
            gap=10, label_span=6,
        )
        self._stack(
            form_s,
            [
                lambda p: self._select_row(
                    p, "Familia (consola)", "console_font_family", CONSOLE_FAMILIES
                ),
                lambda p: self._number_row(p, "Tamaño", "console_font_size", suffix="px"),
                lambda p: self._color_row(p, "Fondo", "console_bg"),
                lambda p: self._color_row(p, "Texto", "console_fg"),
                lambda p: self._color_row(p, "Borde", "console_border"),
            ],
            gap=14, label_span=5,
        )

        self._build_font_preview(prev_f)
        self._build_chart_preview(prev_c)
        self._build_console_preview(prev_s)
        self.select_tab("Fuentes")
        for var in self._theme_vars.values():
            var.trace_add("write", self._refresh_previews)
        self._refresh_previews()

    # ---------------------------------------------------------------- estructura

    def _make_tab(self, bar: tk.Frame, name: str) -> None:
        cell = tk.Frame(bar, bg=ui.CARD, cursor="pointinghand")
        cell.pack(side=tk.LEFT, padx=(0 if not self._tabs else 24, 0))
        tk.Frame(cell, bg=ui.CARD, height=12).pack(fill=tk.X)
        text = ui.Line(cell, name, font=ui.sans(12), fg=ui.MUTED, height=16, cursor="pointinghand")
        text.pack(anchor=tk.W)
        tk.Frame(cell, bg=ui.CARD, height=9).pack(fill=tk.X)
        underline = tk.Canvas(cell, width=1, height=2, bg=ui.CARD, highlightthickness=0, bd=0)
        underline.pack(fill=tk.X)
        for widget in (cell, text, text.label, underline):
            widget.bind("<ButtonRelease-1>", lambda _e, n=name: self.select_tab(n))
        self._tabs[name] = (cell, text, underline)

    def select_tab(self, name: str) -> None:
        for tab, (_cell, text, underline) in self._tabs.items():
            on = tab == name
            text.configure(font=ui.sans(12, "bold" if on else "normal"),
                           fg=ui.ACCENT if on else ui.MUTED)
            underline.configure(bg=ui.ACCENT if on else ui.CARD)
            page = self._pages[tab]
            if on:
                page.pack(fill=tk.BOTH, expand=True)
            else:
                page.pack_forget()

    def _split(self, name: str, caption: str) -> tuple[tk.Frame, tk.Frame]:
        page = tk.Frame(self._host, bg=ui.CARD)
        self._pages[name] = page
        grid = tk.Frame(page, bg=ui.CARD)
        grid.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        grid.rowconfigure(0, weight=1)
        form = tk.Frame(grid, bg=ui.CARD)
        form.grid(row=0, column=0, sticky="new", padx=(0, 16))
        preview = ui.Box(grid, fill=PANEL, border=PANEL_BORDER, radius=4, padx=20, pady=20)
        preview.grid(row=0, column=2, sticky="nsew")

        def fit(e) -> None:
            unit = (e.width - 11 * GAP) / 12.0
            grid.columnconfigure(0, minsize=int(7 * unit + 6 * GAP))
            grid.columnconfigure(1, minsize=GAP)
            grid.columnconfigure(2, minsize=int(5 * unit + 4 * GAP), weight=1)

        grid.bind("<Configure>", fit, add="+")
        form.bind("<Configure>", lambda e: self._fit_form(form, e.width), add="+")

        body = preview.body
        head = tk.Frame(body, bg=PANEL)
        head.pack(fill=tk.X)
        ui.Line(head, "MUESTRA EN VIVO DEL TEMA", font=ui.sans(12, "bold"), fg=ui.TEXT,
                height=16).pack(side=tk.LEFT)
        ui.Line(head, "Escala 1:1", font=ui.sans(11), fg=ui.MUTED, height=16).pack(
            side=tk.RIGHT
        )
        tk.Frame(body, bg=PANEL, height=8).pack(fill=tk.X)
        ui.hline(body, INPUT_BORDER).pack(fill=tk.X)
        foot = tk.Frame(body, bg=PANEL)
        foot.pack(side=tk.BOTTOM, fill=tk.X, pady=(16, 0))
        ui.hline(foot, ui.blend(PANEL_BORDER, PANEL, 0.8)).pack(fill=tk.X)
        ui.Line(foot, caption, font=ui.sans(11, italic=True), fg=CAPTION, height=16).pack(
            anchor=tk.W, pady=(12, 0)
        )
        sample = tk.Frame(body, bg=PANEL)
        sample.pack(fill=tk.X, pady=(16, 0))
        return form, sample

    def _fit_form(self, form: tk.Frame, width: int) -> None:
        span = getattr(form, "_hp_label_span", 5)
        form.columnconfigure(0, minsize=int(width * span / 12.0))

    def _stack(
        self, form: tk.Frame, rows: list[Optional[Callable[[tk.Frame], None]]],
        *, gap: int, label_span: int,
    ) -> None:
        form._hp_label_span = label_span  # type: ignore[attr-defined]
        form.columnconfigure(1, weight=1)
        r = 0
        for build in rows:
            pad = (0 if r == 0 else gap, 0)
            if build is None:
                ui.hline(form, "#f1f5f9").grid(row=r, column=0, columnspan=2, sticky="ew",
                                                pady=pad)
                tk.Frame(form, bg=ui.CARD, height=6).grid(row=r + 1, column=0, columnspan=2)
                r += 2
                continue
            label, control, stretch = build(form)
            label.grid(row=r, column=0, sticky="w", pady=pad)
            control.grid(row=r, column=1, sticky=("ew" if stretch else "w"), pady=pad)
            r += 1

    # ------------------------------------------------------------------ filas

    def _label(self, parent: tk.Frame, text: str) -> ui.Line:
        return ui.Line(parent, text, font=ui.sans(12), fg=LABEL, height=16)

    def _field(self, parent: tk.Frame, key: str, width: int,
               stepper: Optional[tuple[int, int]] = None) -> ui.Field:
        field = ui.Field(parent, self._var(key), width=width, height=INPUT_H, font=ui.mono(12),
                         border=INPUT_BORDER, radius=4, justify=tk.LEFT, stepper=stepper)
        if stepper is not None:
            field.entry.bind("<Up>", lambda _e: field.step(1), add="+")
            field.entry.bind("<Down>", lambda _e: field.step(-1), add="+")
        return field

    def _select_row(
        self, parent: tk.Frame, text: str, key: str, values: tuple[str, ...]
    ) -> tuple[tk.Misc, tk.Misc, bool]:
        select = ui.Select(parent, self._var(key), values, height=26, font=ui.sans(12),
                           border=INPUT_BORDER, radius=4, padx=10)
        return self._label(parent, text), select, True

    def _number_row(
        self, parent: tk.Frame, text: str, key: str, suffix: Optional[str] = None
    ) -> tuple[tk.Misc, tk.Misc, bool]:
        row = tk.Frame(parent, bg=ui.CARD)
        self._field(row, key, 96, stepper=SIZE_RANGE).pack(side=tk.LEFT)
        if suffix:
            ui.Line(row, suffix, font=ui.sans(12), fg=ui.MUTED, height=16).pack(
                side=tk.LEFT, padx=(8, 0)
            )
        return self._label(parent, text), row, False

    def _color_controls(self, row: tk.Frame, key: str, width: int, title: str) -> None:
        self._field(row, key, width).pack(side=tk.LEFT)
        swatch = tk.Canvas(row, width=20, height=20, bg=ui.CARD, highlightthickness=0, bd=0)
        swatch.pack(side=tk.LEFT, padx=(8, 0))
        var = self._var(key)

        def paint(*_a) -> None:
            swatch.delete("all")
            try:
                ui.round_rect(swatch, 0, 0, 19, 19, 2, fill=str(var.get()),
                              outline=SWATCH_BORDER)
            except tk.TclError:
                ui.round_rect(swatch, 0, 0, 19, 19, 2, fill=ui.CARD,
                              outline=SWATCH_BORDER)

        def pick() -> None:
            try:
                _rgb, hx = colorchooser.askcolor(color=str(var.get()), title=title)
            except tk.TclError:
                _rgb, hx = colorchooser.askcolor(title=title)
            if hx:
                var.set(hx.upper())

        var.trace_add("write", paint)
        paint()
        ui.Button(row, "…", command=pick, variant="white", font=ui.mono(12), padx=8,
                  height=22, radius=4).pack(side=tk.LEFT, padx=(8, 0))

    def _color_row(self, parent: tk.Frame, text: str, key: str) -> tuple[tk.Misc, tk.Misc, bool]:
        row = tk.Frame(parent, bg=ui.CARD)
        self._color_controls(row, key, 112, text)
        return self._label(parent, text), row, False

    def _style_row(
        self, parent: tk.Frame, text: str, prefix: str
    ) -> tuple[tk.Misc, tk.Misc, bool]:
        row = tk.Frame(parent, bg=ui.CARD)
        self._field(row, f"{prefix}_size", 64, stepper=SIZE_RANGE).pack(side=tk.LEFT)
        weight_w = max(ui.measure(ui.sans(12), w) for w in WEIGHTS) + 16 + 24
        ui.Select(row, self._var(f"{prefix}_weight"), WEIGHTS, width=weight_w, height=26,
                  font=ui.sans(12), border=INPUT_BORDER, radius=4, padx=8).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        tk.Frame(row, bg=ui.CARD, width=8).pack(side=tk.LEFT)
        self._color_controls(row, f"{prefix}_color", 96, text)
        return self._label(parent, text), row, False

    # -------------------------------------------------------------- muestras

    def _build_font_preview(self, parent: tk.Frame) -> None:
        box = ui.Box(parent, fill=ui.CARD, border=ui.BORDER, radius=4, padx=16, pady=16)
        box.pack(fill=tk.X)
        body = box.body
        top = tk.Frame(body, bg=ui.CARD)
        top.pack(fill=tk.X)
        self.preview_title = ui.label(top, "ESTADO DEL PROCESO")
        self.preview_title.pack(side=tk.LEFT)
        ui.label(top, "$HP · 1 Hz", font=ui.mono(10), fg="#94a3b8").pack(side=tk.RIGHT)

        inner = ui.Box(body, fill="#fafbfc", border=PANEL_BORDER, radius=4, padx=12, pady=12)
        inner.pack(fill=tk.X, pady=(14, 0))
        sec = inner.body
        self.preview_section = ui.label(sec, "PROGRAMA")
        self.preview_section.pack(anchor=tk.W)
        self._preview_rows: list[tuple[tk.Label, tk.Label, bool]] = []
        for key, value, is_mono in (
            ("Programa", "HEAT", True),
            ("Fase", "Meseta", False),
            ("Medida", "188.1 °C", True),
        ):
            row = tk.Frame(sec, bg="#fafbfc")
            row.pack(fill=tk.X, pady=(8, 0))
            k = ui.label(row, key)
            k.pack(side=tk.LEFT)
            v = ui.label(row, value)
            v.pack(side=tk.RIGHT)
            self._preview_rows.append((k, v, is_mono))

        buttons = tk.Frame(body, bg=ui.CARD)
        buttons.pack(fill=tk.X, pady=(18, 0))
        self.preview_button = ui.Button(buttons, "Iniciar HEAT", variant="primary",
                                        font=ui.sans(11), padx=12, height=28, radius=4)
        self.preview_button.pack(side=tk.LEFT)
        ui.Button(buttons, "Cancelar", variant="white", font=ui.sans(11), padx=12, height=28,
                  radius=4).pack(side=tk.LEFT, padx=(8, 0))

    def _build_chart_preview(self, parent: tk.Frame) -> None:
        box = ui.Box(parent, fill=ui.CARD, border=ui.BORDER, radius=4, padx=12, pady=12)
        box.pack(fill=tk.X)
        self.chart_preview = tk.Canvas(box.body, height=224, bg=ui.CARD, highlightthickness=1,
                                       highlightbackground=PANEL_BORDER, bd=0)
        self.chart_preview.pack(fill=tk.X)
        self.chart_preview.bind("<Configure>", lambda _e: self._draw_chart(), add="+")
        ui.hline(box.body, "#f1f5f9").pack(fill=tk.X, pady=(10, 0))
        legend = tk.Frame(box.body, bg=ui.CARD)
        legend.pack(fill=tk.X, pady=(4, 0))
        legend.columnconfigure(0, weight=1, uniform="lg")
        legend.columnconfigure(1, weight=1, uniform="lg")
        self._legend_marks: list[tuple[tk.Canvas, str, str]] = []
        items = (
            ("line", "chart_temp", "Temperatura medida"),
            ("dash", "chart_set", "SET / objetivo"),
            ("line", "chart_duty", "Potencia DU"),
            ("band", "chart_band", "Banda histéresis"),
            ("up", "chart_mark_up", "Cruce ↑"),
            ("down", "chart_mark_down", "Cruce ↓"),
            ("peak", "chart_mark_peak", "Cresta"),
            ("phase", "chart_phase", "Inicio de fase"),
        )
        for i, (kind, key, text) in enumerate(items):
            cell = tk.Frame(legend, bg=ui.CARD)
            cell.grid(row=i // 2, column=i % 2, sticky="w", pady=(0 if i < 2 else 6, 0),
                      padx=(0, 8 if i % 2 == 0 else 0))
            mark = tk.Canvas(cell, width=12, height=16, bg=ui.CARD, highlightthickness=0, bd=0)
            mark.pack(side=tk.LEFT)
            ui.Line(cell, text, font=ui.mono(11), fg=LABEL, height=16).pack(
                side=tk.LEFT, padx=(6, 0)
            )
            self._legend_marks.append((mark, kind, key))

    def _build_console_preview(self, parent: tk.Frame) -> None:
        self.console_preview = tk.Canvas(parent, height=102, highlightthickness=1, bd=0)
        self.console_preview.pack(fill=tk.X)
        self.console_preview.bind("<Configure>", lambda _e: self._draw_console(), add="+")

    # ------------------------------------------------------------ refresco

    def _text(self, key: str, fallback: str) -> str:
        raw = str(self._var(key).get()).strip()
        return raw or fallback

    def _number(self, key: str, fallback: int) -> int:
        try:
            return max(6, int(self._var(key).get()))
        except (TypeError, ValueError, tk.TclError):
            return fallback

    def _color(self, key: str) -> str:
        value = self._text(key, str(ui_theme.DEFAULT_THEME[key]))
        try:
            self.chart_preview.winfo_rgb(value)
        except tk.TclError:
            return str(ui_theme.DEFAULT_THEME[key])
        return value

    def _family(self) -> str:
        fam = self._text("font_family", SYSTEM)
        return ui.sans_family() if fam == SYSTEM else fam

    def _style_font(self, prefix: str, *, mono: bool = False) -> tuple:
        fam = ui.mono_family() if mono else self._family()
        weight = "bold" if self._text(f"{prefix}_weight", "normal") == "bold" else "normal"
        return (fam, -self._number(f"{prefix}_size", 12), weight)

    def _refresh_previews(self, *_args: object) -> None:
        try:
            self.preview_title.configure(font=self._style_font("frame_title"),
                                         fg=self._color("frame_title_color"))
            self.preview_section.configure(font=self._style_font("section_title"),
                                           fg=self._color("section_title_color"))
            for k, v, is_mono in self._preview_rows:
                k.configure(font=self._style_font("status_key"),
                            fg=self._color("status_key_color"))
                v.configure(font=self._style_font("status_value", mono=is_mono),
                            fg=self._color("status_value_color"))
        except tk.TclError:
            pass
        self._draw_chart()
        self._draw_legend()
        self._draw_console()

    def _draw_chart(self) -> None:
        c = self.chart_preview
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10:
            return
        c.delete("all")
        c.configure(bg=self._color("chart_face"))
        sx, sy = (w - 2) / 460.0, (h - 2) / 210.0

        def p(x: float, y: float) -> tuple[float, float]:
            return 1 + x * sx, 1 + y * sy

        for y in (20, 55, 90, 125, 160):
            c.create_line(*p(40, y), *p(445, y), fill="#edf2f7")
        for x in (115, 195, 275, 355, 435):
            c.create_line(*p(x, 20), *p(x, 180), fill="#edf2f7")
        for y, text in ((24, "250°"), (59, "200°"), (94, "150°"), (129, "100°"),
                        (164, "50°"), (183, "0°")):
            c.create_text(*p(34, y), text=text, anchor=tk.SE, fill="#94a3b8", font=ui.mono(9))
        c.create_line(*p(40, 180), *p(445, 180), fill=INPUT_BORDER)
        c.create_line(*p(40, 15), *p(40, 180), fill=INPUT_BORDER)
        face = self._color("chart_face")
        c.create_rectangle(*p(40, 55), *p(445, 75), outline="",
                           fill=ui.blend(self._color("chart_band"), face, 0.22))
        c.create_line(*p(190, 20), *p(190, 180), fill=self._color("chart_phase"), dash=(4, 3),
                      width=1.5)
        c.create_line(*p(40, 65), *p(445, 65), fill=self._color("chart_set"), dash=(5, 3),
                      width=1.8)
        duty = (40, 135, 115, 135, 150, 145, 210, 160, 260, 152, 310, 162, 370, 156, 445, 158)
        c.create_line(*[v for i in range(0, len(duty), 2) for v in p(duty[i], duty[i + 1])],
                      fill=self._color("chart_duty"), width=1.6)
        temp = _quad_path(((40, 175), (85, 165), (125, 120), (215, 62), (255, 58), (310, 66),
                           (445, 64)))
        c.create_line(*[v for x, y in temp for v in p(x, y)], fill=self._color("chart_temp"),
                      width=2.2, smooth=False)
        for pts, key in (
            ((205, 58, 200, 68, 210, 68), "chart_mark_up"),
            ((255, 52, 260, 58, 255, 64, 250, 58), "chart_mark_peak"),
            ((310, 73, 305, 63, 315, 63), "chart_mark_down"),
        ):
            c.create_polygon(*[v for i in range(0, len(pts), 2) for v in p(pts[i], pts[i + 1])],
                             fill=self._color(key), outline="")

    def _draw_legend(self) -> None:
        for mark, kind, key in self._legend_marks:
            mark.delete("all")
            color = self._color(key)
            if kind == "line":
                mark.create_rectangle(0, 7, 12, 9, fill=color, outline="")
            elif kind == "dash":
                mark.create_text(6, 8, text="- -", fill=color, font=ui.mono(9, "bold"))
            elif kind == "band":
                mark.create_rectangle(1, 4, 11, 12, fill=ui.blend(color, ui.CARD, 0.8),
                                      outline=INPUT_BORDER)
            elif kind == "up":
                mark.create_polygon(6, 3, 1, 12, 11, 12, fill=color, outline="")
            elif kind == "down":
                mark.create_polygon(1, 4, 11, 4, 6, 13, fill=color, outline="")
            elif kind == "peak":
                mark.create_polygon(6, 2, 11, 8, 6, 14, 1, 8, fill=color, outline="")
            else:
                mark.create_line(6, 2, 6, 14, fill=color, dash=(2, 2), width=2)

    def _draw_console(self) -> None:
        c = self.console_preview
        c.delete("all")
        fam = self._text("console_font_family", SYSTEM)
        fam = ui.mono_family() if fam == SYSTEM else fam
        size = self._number("console_font_size", 11)
        font = (fam, -size)
        pitch = round(size * 1.625)
        # Como el <div> de la muestra: ajuste en espacios, space-y-1.5 entre entradas.
        avail = max(40, c.winfo_width() - 2 * 17)
        entries = [self._wrap_words(line, font, avail) for line in CONSOLE_SAMPLE]
        n_lines = sum(len(e) for e in entries)
        c.configure(
            bg=self._color("console_bg"),
            highlightbackground=self._color("console_border"),
            highlightcolor=self._color("console_border"),
            height=16 * 2 + n_lines * pitch + (len(entries) - 1) * 6,
        )
        y = 16 + pitch / 2.0
        for wrapped in entries:
            for text in wrapped:
                c.create_text(17, y, text=text, anchor=tk.W, fill=self._color("console_fg"),
                              font=font)
                y += pitch
            y += 6

    @staticmethod
    def _wrap_words(text: str, font: tuple, width: int) -> list[str]:
        lines: list[str] = []
        cur = ""
        for word in text.split(" "):
            probe = f"{cur} {word}" if cur else word
            if cur.strip() and ui.measure(font, probe) > width:
                lines.append(cur.rstrip())
                cur = word
            else:
                cur = probe
        lines.append(cur)
        return lines

    # ------------------------------------------------------------------ tema

    def _fill_theme_vars(self, t: dict[str, Any]) -> None:
        for k, v in t.items():
            if k == "size_unit":
                continue
            v = _display(k, v)
            if isinstance(v, bool):
                self._theme_vars[k] = tk.BooleanVar(value=v)
            else:
                self._theme_vars[k] = tk.StringVar(value=str(v))

    def _var(self, key: str) -> tk.Variable:
        return self._theme_vars[key]

    def collect_theme(self) -> dict[str, Any]:
        out: dict[str, Any] = {"size_unit": "px"}
        for k, var in self._theme_vars.items():
            default = ui_theme.DEFAULT_THEME[k]
            raw = var.get()
            if isinstance(default, int):
                try:
                    out[k] = max(6, int(str(raw).strip()))
                except (TypeError, ValueError):
                    out[k] = default
            elif k in FAMILY_KEYS:
                out[k] = "" if str(raw).strip() in ("", SYSTEM) else str(raw).strip()
            elif k.endswith("_color") or k.startswith(("chart_", "console_")):
                value = str(raw).strip()
                try:
                    self.chart_preview.winfo_rgb(value)
                    out[k] = value
                except tk.TclError:
                    out[k] = default
            else:
                out[k] = str(raw)
        return out

    def apply_theme(self) -> None:
        self._refresh_previews()

    def reload_theme_vars(self) -> None:
        t = ui_theme.get()
        for k, v in t.items():
            if k not in self._theme_vars:
                continue
            self._theme_vars[k].set(_display(k, v))


def _display(key: str, value: Any) -> Any:
    """Valor tal como se ve en el formulario (familia vacía = Sistema, hex en mayúsculas)."""
    if key in FAMILY_KEYS and not str(value).strip():
        return SYSTEM
    if isinstance(value, str) and value.startswith("#"):
        return value.upper()
    return value


def _quad_path(pts: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    """`M p0 Q p1 p2 T p3 Q p4 p5 T p6` del SVG de Stitch, muestreado."""
    out: list[tuple[float, float]] = []

    def quad(a, b, c, steps: int = 18) -> None:
        for i in range(steps + 1):
            t = i / steps
            x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0]
            y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]
            out.append((x, y))

    p0, c1, p1, p2, c3, p3, p4 = pts
    quad(p0, c1, p1)
    c2 = (2 * p1[0] - c1[0], 2 * p1[1] - c1[1])
    quad(p1, c2, p2)
    quad(p2, c3, p3)
    c4 = (2 * p3[0] - c3[0], 2 * p3[1] - c3[1])
    quad(p3, c4, p4)
    return out
