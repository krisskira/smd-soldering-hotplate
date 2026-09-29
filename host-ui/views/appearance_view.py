"""Pestaña Apariencia: fuentes, gráficas y consola de HotPlate Studio."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import colorchooser, ttk

import theme as ui_theme

if TYPE_CHECKING:
    from controller import AppController

FONT_FAMILIES = ("Helvetica", "Arial", "Menlo", "Courier", "Times")
WEIGHTS = ("normal", "bold")


class AppearanceView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self._theme_vars: dict[str, tk.Variable] = {}

        outer = ttk.Frame(parent)
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0, background=ui_theme.surface_bg())
        self._canvas = canvas
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

        head = ttk.Frame(content)
        head.pack(fill=tk.X, padx=8, pady=(10, 2))
        ttk.Label(head, text="HotPlate Studio", style="Section.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            content,
            text=(
                "Familia, texto, campos y botones cubren toda la interfaz. "
                "El estado del proceso usa sus propias filas de sección, clave y valor."
            ),
            style="Muted.TLabel",
            wraplength=880,
        ).pack(anchor=tk.W, padx=8, pady=(2, 4))

        box = ttk.LabelFrame(content, text="Apariencia")
        box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 12))

        bar = ttk.Frame(box)
        bar.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        ttk.Button(bar, text="Aplicar y guardar tema", command=ctrl.save_theme).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(bar, text="Restaurar defaults", command=ctrl.reset_theme).pack(
            side=tk.LEFT
        )

        nb = ttk.Notebook(box)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tab_f = ttk.Frame(nb)
        tab_c = ttk.Frame(nb)
        tab_log = ttk.Frame(nb)
        nb.add(tab_f, text="Fuentes")
        nb.add(tab_c, text="Gráficas")
        nb.add(tab_log, text="Consola serie")

        t = ui_theme.load()
        self._fill_theme_vars(t)
        if not str(self._theme_vars["font_family"].get()).strip():
            self._theme_vars["font_family"].set("Helvetica")

        self._font_row(tab_f, 0, "Familia general", "font_family", FONT_FAMILIES)
        self._spin_row(tab_f, 1, "Texto general (pt)", "body_size", 8, 18)
        self._color_row(tab_f, 2, "Color del texto general", "body_color")
        self._spin_row(tab_f, 3, "Campos (pt)", "input_size", 8, 18)
        self._spin_row(tab_f, 4, "Botones (pt)", "button_size", 8, 18)
        self._size_weight_color(
            tab_f, 5, "Títulos de paneles",
            "frame_title_size", "frame_title_weight", "frame_title_color",
        )
        self._size_weight_color(
            tab_f, 6, "Estado · títulos de sección",
            "section_title_size", "section_title_weight", "section_title_color",
        )
        self._size_weight_color(
            tab_f, 7, "Estado · etiquetas",
            "status_key_size", "status_key_weight", "status_key_color",
        )
        self._size_weight_color(
            tab_f, 8, "Estado · valores",
            "status_value_size", "status_value_weight", "status_value_color",
        )

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

        self._font_row(
            tab_log, 0, "Familia (consola)", "console_font_family",
            ("Menlo", "Courier", "Monaco", "Consolas", "Helvetica"),
        )
        self._spin_row(tab_log, 1, "Tamaño", "console_font_size", 8, 22)
        self._color_row(tab_log, 2, "Fondo", "console_bg")
        self._color_row(tab_log, 3, "Texto", "console_fg")
        self._color_row(tab_log, 4, "Borde", "console_border")

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
        ttk.Entry(fr, textvariable=self._var(key), width=10).pack(side=tk.LEFT)
        swatch = tk.Label(fr, width=3, background=str(self._var(key).get()))
        swatch.pack(side=tk.LEFT, padx=4)

        def pick(_k=key, _sw=swatch) -> None:
            _rgb, hx = colorchooser.askcolor(color=str(self._var(_k).get()), title=label)
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
        ttk.Spinbox(fr, from_=8, to=22, textvariable=self._var(size_k), width=5).pack(
            side=tk.LEFT
        )
        ttk.Combobox(
            fr, textvariable=self._var(weight_k), values=list(WEIGHTS), width=8
        ).pack(side=tk.LEFT, padx=4)
        ttk.Entry(fr, textvariable=self._var(color_k), width=9).pack(side=tk.LEFT)
        swatch = tk.Label(fr, width=3, background=str(self._var(color_k).get()))
        swatch.pack(side=tk.LEFT, padx=4)

        def pick(_k=color_k, _sw=swatch) -> None:
            _rgb, hx = colorchooser.askcolor(color=str(self._var(_k).get()), title=label)
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

    def apply_theme(self) -> None:
        self._canvas.configure(background=ui_theme.surface_bg())

    def reload_theme_vars(self) -> None:
        t = ui_theme.get()
        for k, v in t.items():
            if k in self._theme_vars:
                self._theme_vars[k].set(v)
