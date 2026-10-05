"""Tema de HotPlate Studio: defaults, persistencia y aplicación ttk/widgets."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Optional

from constants import ROOT

THEME_CACHE = ROOT / "ui_theme.json"

# Tamaños en píxeles. Defaults = diseño de Stitch (hotplate-studio/design/stitch).
DEFAULT_THEME: dict[str, Any] = {
    "size_unit": "px",
    "font_family": "",
    # Títulos de tarjeta (Soldering Profile, Estado del proceso, Curva en vivo…)
    "frame_title_size": 16,
    "frame_title_weight": "bold",
    "frame_title_color": "#2c3e50",
    # Títulos de bloque dentro de Estado del proceso (Programa, Tiempos…)
    "section_title_size": 10,
    "section_title_weight": "bold",
    "section_title_color": "#5d6d7e",
    # Claves / valores del estado
    "status_key_size": 12,
    "status_key_weight": "normal",
    "status_key_color": "#5d6d7e",
    "status_value_size": 12,
    "status_value_weight": "bold",
    "status_value_color": "#2c3e50",
    # Cuerpo general / inputs / botones
    "body_size": 12,
    "body_color": "#2c3e50",
    "input_size": 12,
    "button_size": 12,
    # Consola serie
    "console_bg": "#1e1e1e",
    "console_fg": "#d4d4d4",
    "console_font_family": "",
    "console_font_size": 11,
    "console_border": "#34495e",
    # Series y marcadores de gráfica
    "chart_temp": "#c0392b",
    "chart_set": "#2980b9",
    "chart_duty": "#27ae60",
    "chart_mark_up": "#8e44ad",
    "chart_mark_down": "#d35400",
    "chart_mark_on": "#27ae60",
    "chart_mark_off": "#7f8c8d",
    "chart_mark_peak": "#6c3483",
    "chart_phase": "#1a5276",
    "chart_band": "#f1c40f",
    "chart_face": "#ffffff",
}

_current: dict[str, Any] = copy.deepcopy(DEFAULT_THEME)
_listeners: list[Callable[[dict[str, Any]], None]] = []


def get() -> dict[str, Any]:
    return copy.deepcopy(_current)


SURFACE = "#f4f6f8"
CARD = "#ffffff"
ACCENT = "#1a5276"
DANGER = "#c0392b"
BORDER = "#c5d0dc"


def surface_bg() -> str:
    return SURFACE


def ui_family(explicit: Optional[str] = None) -> str:
    """Familia usable. Vacío en ajustes = fuente de interfaz por defecto."""
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    fam = str(_current.get("font_family") or "").strip()
    if fam:
        return fam
    from widgets.ui import sans_family

    return sans_family()


def mono_family() -> str:
    fam = str(_current.get("console_font_family") or "").strip()
    if fam:
        return fam
    from widgets.ui import mono_family as _mono

    return _mono()


def px(size_key: str, default: int = 12) -> int:
    try:
        return max(6, int(_current.get(size_key, default)))
    except (TypeError, ValueError):
        return default


def font_tuple(
    size_key: str = "body_size",
    weight_key: Optional[str] = None,
    *,
    family: Optional[str] = None,
) -> tuple:
    """Fuente con tamaño en píxeles (Tk: tamaño negativo)."""
    fam = ui_family(family)
    size = -px(size_key)
    if weight_key:
        w = str(_current.get(weight_key, "normal"))
        return (fam, size, "bold" if w == "bold" else "normal")
    return (fam, size)


def mono_tuple(size_key: str, weight_key: Optional[str] = None) -> tuple:
    """Fuente monoespaciada para valores técnicos, con el tamaño del tema."""
    from widgets.ui import mono_family as _mono

    w = str(_current.get(weight_key, "normal")) if weight_key else "normal"
    return (_mono(), -px(size_key), "bold" if w == "bold" else "normal")


def load() -> dict[str, Any]:
    global _current
    data = copy.deepcopy(DEFAULT_THEME)
    if THEME_CACHE.exists():
        try:
            raw = json.loads(THEME_CACHE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                legacy_pt = raw.get("size_unit") != "px"
                for k, v in raw.items():
                    if k in DEFAULT_THEME and not (legacy_pt and k.endswith("_size")):
                        data[k] = v
                data["size_unit"] = "px"
        except Exception:
            pass
    _current = data
    return get()


def save(theme: Optional[dict[str, Any]] = None) -> None:
    global _current
    if theme is not None:
        merged = copy.deepcopy(DEFAULT_THEME)
        for k, v in theme.items():
            if k in DEFAULT_THEME:
                merged[k] = v
        _current = merged
    try:
        THEME_CACHE.write_text(
            json.dumps(_current, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def reset_defaults() -> dict[str, Any]:
    global _current
    _current = copy.deepcopy(DEFAULT_THEME)
    save()
    return get()


def update(partial: dict[str, Any]) -> dict[str, Any]:
    global _current
    for k, v in partial.items():
        if k in DEFAULT_THEME:
            _current[k] = v
    return get()


def subscribe(cb: Callable[[dict[str, Any]], None]) -> None:
    if cb not in _listeners:
        _listeners.append(cb)


def notify() -> None:
    snap = get()
    for cb in list(_listeners):
        try:
            cb(snap)
        except Exception:
            pass


def apply_ttk(root) -> None:
    """Estilos de toda la app. Clam respeta fuente y color; el tema aqua de macOS no."""
    from tkinter import font as tkfont
    from tkinter import ttk

    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    t = _current
    fam = ui_family()
    from widgets.ui import apply_theme_fonts

    apply_theme_fonts(
        str(t.get("font_family") or ""),
        px("body_size"), px("button_size"), px("input_size"),
    )
    body = -px("body_size")
    frame_font = (fam, -px("frame_title_size"), str(t["frame_title_weight"]))
    body_font = (fam, body)
    btn_font = (fam, -px("button_size"))
    inp_font = (fam, -px("input_size"))
    bg = SURFACE
    fg = str(t["body_color"])
    muted = "#5d6d7e"

    try:
        root.configure(background=bg)
    except Exception:
        pass
    for name, size, weight in (
        ("TkDefaultFont", body, "normal"),
        ("TkTextFont", -px("input_size"), "normal"),
        ("TkHeadingFont", -px("frame_title_size"), str(t["frame_title_weight"])),
        ("TkMenuFont", body, "normal"),
        ("TkCaptionFont", body, "normal"),
        ("TkSmallCaptionFont", min(body + 1, -8), "normal"),
        ("TkTooltipFont", min(body + 1, -8), "normal"),
    ):
        try:
            tkfont.nametofont(name).configure(family=fam, size=size, weight=weight)
        except Exception:
            pass
    try:
        tkfont.nametofont("TkFixedFont").configure(
            family=mono_family(), size=-px("console_font_size", 11)
        )
    except Exception:
        pass

    root.option_add("*Font", body_font)
    root.option_add("*TCombobox*Listbox.font", inp_font)
    root.option_add("*Listbox.font", inp_font)

    style.configure(".", background=bg, foreground=fg, font=body_font)
    style.configure("TFrame", background=bg)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=bg, foreground=fg, font=body_font)
    style.configure("Card.TLabel", background=CARD, foreground=fg, font=body_font)
    style.configure(
        "ActiveRamp.TLabel",
        background="#dcecf4",
        foreground=ACCENT,
        font=(fam, body, "bold"),
    )
    style.configure(
        "Muted.TLabel", background=bg, foreground=muted, font=body_font
    )
    style.configure(
        "Section.TLabel",
        background=bg,
        foreground=muted,
        font=frame_font,
    )
    style.configure(
        "TLabelframe",
        background=bg,
        bordercolor="#c5d0dc",
        lightcolor="#c5d0dc",
        darkcolor="#c5d0dc",
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=bg,
        foreground=muted,
        font=frame_font,
    )
    style.configure(
        "TButton",
        font=btn_font,
        padding=(12, 5),
        background="#e7eef4",
        foreground=fg,
        borderwidth=1,
    )
    style.map(
        "TButton",
        background=[("pressed", "#c5d4e2"), ("active", "#d7e2ec")],
    )
    style.configure(
        "Accent.TButton",
        font=btn_font,
        padding=(14, 6),
        background="#1a5276",
        foreground="#ffffff",
        borderwidth=0,
    )
    style.configure(
        "Danger.TButton",
        font=btn_font,
        padding=(14, 6),
        background=DANGER,
        foreground="#ffffff",
        borderwidth=0,
    )
    style.map(
        "Danger.TButton",
        background=[("pressed", "#922b21"), ("active", "#a93226"), ("disabled", "#d7b8b5")],
        foreground=[("disabled", "#f4f6f8")],
    )
    style.configure(
        "Nav.TButton",
        font=btn_font,
        padding=(14, 7),
        background="#e4eaef",
        foreground="#526577",
        borderwidth=0,
    )
    style.map(
        "Nav.TButton",
        background=[("active", "#d7e2ec"), ("pressed", "#c5d4e2")],
    )
    style.configure(
        "NavSelected.TButton",
        font=btn_font,
        padding=(14, 7),
        background=ACCENT,
        foreground="#ffffff",
        borderwidth=0,
    )
    style.map(
        "NavSelected.TButton",
        background=[("active", "#154360"), ("pressed", "#0e3046")],
    )
    style.map(
        "Accent.TButton",
        background=[
            ("pressed", "#0e3046"),
            ("active", "#154360"),
            ("disabled", "#b7c3ce"),
        ],
        foreground=[("disabled", "#f4f6f8")],
    )
    style.configure("TEntry", font=inp_font, padding=3)
    style.configure("TSpinbox", font=inp_font, padding=2)
    style.configure("TCombobox", font=inp_font, padding=2)
    style.configure("TCheckbutton", background=bg, foreground=fg, font=body_font)
    style.map("TCheckbutton", background=[("active", bg)])
    style.configure("TNotebook", background=bg, borderwidth=0, tabmargins=(6, 6, 6, 0))
    style.configure("Content.TNotebook", background=bg, borderwidth=0, tabmargins=0)
    style.layout("Content.TNotebook.Tab", [])
    style.configure(
        "TNotebook.Tab",
        font=body_font,
        padding=(16, 8),
        background="#e4eaef",
        foreground=fg,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", "#ffffff")],
        foreground=[("selected", "#1a5276")],
    )
    style.configure(
        "Treeview",
        font=body_font,
        rowheight=max(22, px("body_size") + 10),
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground=fg,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        font=(fam, body, "bold"),
        background="#e8eef3",
        foreground="#1a5276",
        relief="flat",
    )
    style.map("Treeview", background=[("selected", "#d6e6f2")], foreground=[("selected", fg)])
    style.configure(
        "TProgressbar", thickness=8, background="#1a5276", troughcolor="#e4eaef"
    )
    style.configure("TSeparator", background="#d5dde5")
    style.configure("TScrollbar", background="#e4eaef", troughcolor=bg, arrowsize=12)
    style.layout(
        "Thin.Vertical.TScrollbar",
        [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
        ]})],
    )
    style.configure(
        "Thin.Vertical.TScrollbar",
        troughcolor="#ffffff",
        background="#c5d0dc",
        bordercolor="#ffffff",
        lightcolor="#c5d0dc",
        darkcolor="#c5d0dc",
        arrowsize=6,
        width=6,
        gripcount=0,
    )
    style.map("Thin.Vertical.TScrollbar", background=[("active", "#94a3b8")])
    style.layout(
        "Dark.Vertical.TScrollbar",
        [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
        ]})],
    )
    style.configure(
        "Dark.Vertical.TScrollbar",
        troughcolor="#1e1e1e",
        background="#3c3c3c",
        bordercolor="#1e1e1e",
        lightcolor="#3c3c3c",
        darkcolor="#3c3c3c",
        arrowsize=6,
        width=8,
        gripcount=0,
    )


def chart_colors() -> dict[str, str]:
    t = _current
    return {
        "temp": str(t["chart_temp"]),
        "set": str(t["chart_set"]),
        "duty": str(t["chart_duty"]),
        "mark_up": str(t["chart_mark_up"]),
        "mark_down": str(t["chart_mark_down"]),
        "mark_on": str(t["chart_mark_on"]),
        "mark_off": str(t["chart_mark_off"]),
        "mark_peak": str(t["chart_mark_peak"]),
        "phase": str(t["chart_phase"]),
        "band": str(t["chart_band"]),
        "face": str(t["chart_face"]),
    }
