"""Barra inferior: LED de enlace + puerto + modo."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import theme as ui_theme
from constants import LED_AMBER, LED_GREEN, LED_RED
from serial_link import BAUD


class StatusBar:
    def __init__(self, parent: tk.Misc) -> None:
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, padx=8, pady=(0, 6))
        self._led = tk.Canvas(bar, width=14, height=14, highlightthickness=0)
        self._led.pack(side=tk.LEFT, padx=(0, 8))
        self._led_id = self._led.create_oval(2, 2, 12, 12, fill=LED_RED, outline="")
        self._label = ttk.Label(bar, text="", anchor=tk.W)
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.apply_theme()

    def apply_theme(self) -> None:
        bg = ui_theme.surface_bg()
        self._led.configure(background=bg)

    def update(
        self, connected: bool, online: bool, port: str, usb_mode: bool = False
    ) -> None:
        if connected and online:
            modo = "USB" if usb_mode else "Manual"
            self._led.itemconfig(self._led_id, fill=LED_GREEN)
            self._label.config(
                text=f"{port} @ {BAUD}  ·  En línea  ·  Modo {modo}"
            )
        elif connected:
            self._led.itemconfig(self._led_id, fill=LED_AMBER)
            self._label.config(text=f"{port} @ {BAUD}  ·  Preguntando al equipo…")
        else:
            self._led.itemconfig(self._led_id, fill=LED_RED)
            self._label.config(text="")
