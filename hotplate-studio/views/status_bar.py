"""Cabecera (marca, navegación, modo) y barra inferior (LED + puerto + modo)."""

from __future__ import annotations

from typing import Callable

import tkinter as tk

from constants import LED_AMBER, LED_GREEN, LED_RED
from serial_link import BAUD
from widgets import ui

PAGES = ("Conexión", "HEAT", "Autotune", "Ajustes", "Apariencia")


class HeaderBar:
    """Cabecera `h-14 px-6`: logo, pestañas segmentadas, chip de modo y botón."""

    def __init__(
        self, parent: tk.Misc, on_select: Callable[[int], None], ctrl
    ) -> None:
        self._on_select = on_select
        self.frame = tk.Frame(parent, bg=ui.CARD, height=55, bd=0, highlightthickness=0)
        self.frame.pack(fill=tk.X, side=tk.TOP)
        self.frame.pack_propagate(False)
        tk.Frame(parent, bg=ui.BORDER, height=1).pack(fill=tk.X, side=tk.TOP)

        left = tk.Frame(self.frame, bg=ui.CARD)
        left.pack(side=tk.LEFT, padx=(24, 0), fill=tk.Y)
        logo = tk.Canvas(left, width=32, height=32, bg=ui.CARD, highlightthickness=0, bd=0)
        ui.round_rect(logo, 0, 0, 31, 31, 8, fill=ui.ACCENT)
        ui.draw_icon(logo, "heat", 6, 6, 20, "#ffffff")
        logo.pack(side=tk.LEFT)
        ui.label(left, "HotPlate Studio", font=ui.sans(18, "bold"), fg=ui.TEXT).pack(
            side=tk.LEFT, padx=(12, 0)
        )

        nav = ui.Box(left, fill="#e4eaef", border=None, radius=8, padx=4, pady=4)
        nav.pack(side=tk.LEFT, padx=(24, 0))
        self._nav: list[ui.Button] = []
        for index, text in enumerate(PAGES):
            btn = ui.Button(
                nav.body,
                text,
                command=lambda i=index: self._on_select(i),
                variant="tab",
                font=ui.sans(14),
                padx=12,
                height=28,
                radius=6,
            )
            btn.pack(side=tk.LEFT, padx=(0 if index == 0 else 4, 0))
            self._nav.append(btn)

        right = tk.Frame(self.frame, bg=ui.CARD)
        right.pack(side=tk.RIGHT, padx=(0, 24), fill=tk.Y)
        self.btn_mode = ui.Button(
            right,
            "Cambiar a modo USB",
            command=ctrl.toggle_mode,
            variant="white",
            padx=12,
            height=30,
        )
        self.btn_mode.pack(side=tk.RIGHT)
        self.mode_chip = ui.Chip(
            right,
            "Modo Manual",
            fill=ui.ACCENT,
            fg="#ffffff",
            font=ui.mono(12, "bold"),
            padx=12,
            height=24,
            radius=6,
        )
        self.mode_chip.pack(side=tk.RIGHT, padx=(0, 12))

    def set_current(self, index: int) -> None:
        for i, btn in enumerate(self._nav):
            active = i == index
            btn.configure(variant=("tab-active" if active else "tab"), padx=(14 if active else 12))

    def update(self, online: bool, usb_mode: bool) -> None:
        mode = "USB" if usb_mode else "Manual"
        self.mode_chip.set(f"Modo {mode}")
        self.btn_mode.configure(
            text=f"Cambiar a modo {'Manual' if usb_mode else 'USB'}",
            state=(tk.NORMAL if online else tk.DISABLED),
        )


class StatusBar:
    """Pie `h-7` gris claro con LED de enlace y texto monoespaciado."""

    def __init__(self, parent: tk.Misc) -> None:
        bar = tk.Frame(parent, bg=ui.FOOTER_BG, height=27, bd=0, highlightthickness=0)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        tk.Frame(parent, bg=ui.BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)
        self._led = ui.Dot(bar, LED_RED, size=8, bg=ui.FOOTER_BG)
        self._led.pack(side=tk.LEFT, padx=(16, 8))
        self._label = ui.label(
            bar, "", font=ui.mono(12), fg=ui.TEXT, bg=ui.FOOTER_BG, anchor=tk.W
        )
        self._label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def apply_theme(self) -> None:
        pass

    def update(
        self, connected: bool, online: bool, port: str, usb_mode: bool = False
    ) -> None:
        if connected and online:
            modo = "USB" if usb_mode else "Manual"
            self._led.set(LED_GREEN)
            self._label.config(text=f"{port} @ {BAUD} · En línea · Modo {modo}")
        elif connected:
            self._led.set(LED_AMBER)
            self._label.config(text=f"{port} @ {BAUD} · Preguntando al equipo…")
        else:
            self._led.set(LED_RED)
            self._label.config(text="")
