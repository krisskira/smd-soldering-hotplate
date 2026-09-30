"""Filas de paneles: ancho al contenido y la misma altura."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def content_row(parent: tk.Misc, *, padx: int = 8, pady: int = 4) -> ttk.Frame:
    """Fila horizontal. Los paneles se añaden con `add_panel`."""
    row = ttk.Frame(parent)
    row.pack(fill=tk.X, anchor=tk.NW, padx=padx, pady=pady)
    row.rowconfigure(0, weight=1)
    row._hp_col = 0  # type: ignore[attr-defined]
    return row


def add_panel(row: ttk.Frame, panel: tk.Misc, *, gap: int = 8) -> None:
    """Coloca el panel a su ancho natural y lo estira a la altura de la fila."""
    col = int(getattr(row, "_hp_col", 0))
    setattr(row, "_hp_col", col + 1)
    row.columnconfigure(col, weight=1, uniform="hp-panels")
    panel.grid(
        row=0,
        column=col,
        sticky=tk.NSEW,
        padx=(0 if col == 0 else gap, 0),
        pady=0,
    )
