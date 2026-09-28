"""Tema de la Host UI: defaults, persistencia y aplicación ttk/widgets."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Optional

from constants import ROOT

THEME_CACHE = ROOT / "ui_theme.json"

# Defaults: títulos de frame −2 pt vs 12 y gris medio; secciones de estado
# al tamaño del cuerpo y más discretas.
DEFAULT_THEME: dict[str, Any] = {
    "font_family": "",
    # Títulos LabelFrame (antes 12 bold negro → 10 bold gris)
    "frame_title_size": 10,
    "frame_title_weight": "bold",
    "frame_title_color": "#5d6d7e",
    # Títulos de bloque dentro de Estado del proceso (Programa, Tiempos…)
    "section_title_size": 11,
    "section_title_weight": "normal",
    "section_title_color": "#7f8c8d",
    # Claves / valores del estado
    "status_key_size": 11,
    "status_key_weight": "normal",
    "status_key_color": "#7f8c8d",
    "status_value_size": 11,
    "status_value_weight": "normal",
    "status_value_color": "#2c3e50",
    # Cuerpo general / inputs / botones
    "body_size": 11,
    "body_color": "#2c3e50",
    "input_size": 11,
    "button_size": 11,
    # Consola serie
    "console_bg": "#1e1e1e",
    "console_fg": "#d4d4d4",
    "console_font_family": "Menlo",
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


def font_tuple(
    size_key: str = "body_size",
    weight_key: Optional[str] = None,
    *,
    family: Optional[str] = None,
) -> tuple:
    fam = family if family is not None else _current.get("font_family") or ""
    size = int(_current.get(size_key, 11))
    if weight_key:
        w = str(_current.get(weight_key, "normal"))
        return (fam, size, w)
    return (fam, size)


def load() -> dict[str, Any]:
    global _current
    data = copy.deepcopy(DEFAULT_THEME)
    if THEME_CACHE.exists():
        try:
            raw = json.loads(THEME_CACHE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if k in DEFAULT_THEME:
                        data[k] = v
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
    """Estilos ttk globales (frames, labels, botones, entries)."""
    from tkinter import ttk

    style = ttk.Style(root)
    t = _current
    fam = t.get("font_family") or ""
    frame_font = (fam, int(t["frame_title_size"]), str(t["frame_title_weight"]))
    body_font = (fam, int(t["body_size"]))
    btn_font = (fam, int(t["button_size"]))
    inp_font = (fam, int(t["input_size"]))

    style.configure(
        "TLabelframe.Label",
        font=frame_font,
        foreground=str(t["frame_title_color"]),
    )
    style.configure("TLabel", font=body_font, foreground=str(t["body_color"]))
    style.configure("TButton", font=btn_font)
    style.configure("TEntry", font=inp_font)
    style.configure("TCheckbutton", font=body_font)
    style.configure("TCombobox", font=inp_font)
    style.configure("TNotebook.Tab", font=body_font)


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
