"""Ventana principal: cabecera con navegación, páginas y barra de estado."""

from __future__ import annotations

import tkinter as tk

import theme as ui_theme
from controller import AppController
from state import SessionState
from views import (
    AppearanceView,
    ConnectionView,
    HeaderBar,
    HeatView,
    SettingsView,
    StatusBar,
    TuneView,
)
from widgets import ui

MIN_W = 1100
MIN_H = 760


class MainWindow(tk.Tk):
    def __init__(self, *, maximized: bool = True) -> None:
        super().__init__()
        self.title("HotPlate Studio")
        self.geometry("1280x860")
        self.minsize(MIN_W, MIN_H)
        if maximized:
            self.maximize()
            # Aqua ignora el zoom si la ventana aún no está mapeada.
            self.after_idle(self.maximize)

        ui_theme.load()
        ui_theme.apply_ttk(self)
        self.configure(bg=ui.BG)

        self.state = SessionState()
        self.ctrl = AppController(self, self.state)

        self.header = HeaderBar(self, self.select_page, self.ctrl)
        status = StatusBar(self)
        host = tk.Frame(self, bg=ui.BG, bd=0, highlightthickness=0)
        host.pack(fill=tk.BOTH, expand=True)

        # Las páginas se apilan con el tamaño de la ventana y se cambia cuál va delante.
        # Con pack_forget una página oculta mide lo que pide su contenido, y las vistas
        # que se adaptan al ancho (Estado, HUD) oscilan sin fin al recibir $HP.
        self.pages: list[tk.Frame] = []
        for _ in range(5):
            page = tk.Frame(host, bg=ui.BG, bd=0, highlightthickness=0)
            page.place(x=0, y=0, relwidth=1, relheight=1)
            self.pages.append(page)
        tab_conn, tab_heat, tab_tune, tab_set, tab_look = self.pages

        conn = ConnectionView(tab_conn, self.ctrl)
        heat = HeatView(tab_heat, self.ctrl)
        settings = SettingsView(tab_set, self.ctrl)
        appearance = AppearanceView(tab_look, self.ctrl)
        tune = TuneView(tab_tune, self.ctrl)
        # Medir antes de aplicar el tema: al revés, Tk tarda varias veces más en converger.
        self.update_idletasks()

        self._current = -1
        self.select_page(0)
        self.ctrl.bind_views(conn, heat, settings, tune, status, appearance, self.header)
        self.ctrl.apply_theme()
        self.protocol("WM_DELETE_WINDOW", self.ctrl.on_close)

    def maximize(self) -> None:
        """Ventana maximizada (zoom nativo); `self.state` es la sesión, no `wm state`."""
        try:
            self.wm_state("zoomed")
        except tk.TclError:
            w, h = self.winfo_screenwidth(), self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")

    def select_page(self, index: int) -> None:
        if index == self._current:
            return
        self.pages[index].tkraise()
        self._current = index
        self.header.set_current(index)
