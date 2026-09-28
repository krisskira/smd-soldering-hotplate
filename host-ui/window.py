"""Ventana principal: notebook + barra de estado."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import theme as ui_theme
from controller import AppController
from state import SessionState
from views import ConnectionView, HeatView, SettingsView, StatusBar, TuneView

MIN_W = 1024
MIN_H = 1024


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SMI Hot Plate — Host UI")
        self.geometry(f"{MIN_W}x{MIN_H}")
        self.minsize(MIN_W, MIN_H)

        ui_theme.load()
        ui_theme.apply_ttk(self)

        self.state = SessionState()
        self.ctrl = AppController(self, self.state)

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        tab_conn = ttk.Frame(nb)
        tab_heat = ttk.Frame(nb)
        tab_tune = ttk.Frame(nb)
        tab_set = ttk.Frame(nb)
        nb.add(tab_conn, text="Conexión")
        nb.add(tab_heat, text="Proceso HEAT")
        nb.add(tab_tune, text="Autoajuste PID")
        nb.add(tab_set, text="Ajustes")

        conn = ConnectionView(tab_conn, self.ctrl)
        heat = HeatView(tab_heat, self.ctrl)
        settings = SettingsView(tab_set, self.ctrl)
        tune = TuneView(tab_tune, self.ctrl)
        status = StatusBar(self)

        self.ctrl.bind_views(conn, heat, settings, tune, status)
        self.ctrl.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self.ctrl.on_close)
