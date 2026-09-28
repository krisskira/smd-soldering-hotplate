"""Pestaña Conexión: puerto, sesión, sondeo, consola."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import tkinter as tk
from tkinter import ttk

from constants import STAT_INTERVALS_MS
from serial_link import BAUD, list_serial_ports

if TYPE_CHECKING:
    from controller import AppController


class ConnectionView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.poll_stat = tk.BooleanVar(value=True)
        self.stat_interval = tk.StringVar(value="1 s")
        self.port_var = tk.StringVar()

        port_box = ttk.LabelFrame(parent, text="Puerto serie")
        port_box.pack(fill=tk.X, padx=8, pady=(8, 4))
        row = ttk.Frame(port_box)
        row.pack(fill=tk.X, padx=8, pady=8)
        ttk.Label(row, text="Puerto").pack(side=tk.LEFT)
        self.port_cb = ttk.Combobox(row, textvariable=self.port_var, width=28)
        self.port_cb.pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Refrescar", command=self.refresh_ports).pack(side=tk.LEFT)
        ttk.Label(row, text=f"{BAUD} 8N1").pack(side=tk.LEFT, padx=10)
        self.btn_conn = ttk.Button(row, text="Conectar", command=ctrl.toggle_conn)
        self.btn_conn.pack(side=tk.LEFT, padx=4)
        self.btn_ping = ttk.Button(row, text="Ping", command=ctrl.ping)
        # Visible solo con puerto abierto (ver refresh_session_ui)

        mid = ttk.Frame(parent)
        mid.pack(fill=tk.X, padx=8, pady=4)
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)

        sess = ttk.LabelFrame(mid, text="Sesión con el equipo")
        sess.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 4))
        row2 = ttk.Frame(sess)
        row2.pack(fill=tk.X, padx=8, pady=8)
        self.btn_mode = ttk.Button(
            row2, text="Cambiar a modo USB", command=ctrl.toggle_mode
        )
        self.btn_mode.pack(side=tk.LEFT, padx=2)
        self.btn_stat = ttk.Button(
            row2, text="Consultar estado", command=ctrl.query_stat
        )
        self.btn_stat.pack(side=tk.LEFT, padx=2)

        poll = ttk.LabelFrame(mid, text="Actualización automática de estado")
        poll.grid(row=0, column=1, sticky=tk.NSEW, padx=(4, 0))
        row3 = ttk.Frame(poll)
        row3.pack(fill=tk.X, padx=8, pady=8)
        ttk.Checkbutton(
            row3, text="Activar", variable=self.poll_stat, command=ctrl.toggle_stat_poll
        ).pack(side=tk.LEFT)
        ttk.Label(row3, text="cada").pack(side=tk.LEFT, padx=(12, 4))
        self.interval_cb = ttk.Combobox(
            row3,
            textvariable=self.stat_interval,
            values=list(STAT_INTERVALS_MS.keys()),
            width=8,
            state="readonly",
        )
        self.interval_cb.pack(side=tk.LEFT)
        self.interval_cb.bind("<<ComboboxSelected>>", lambda _e: ctrl.toggle_stat_poll())
        ttk.Label(row3, text="(solo en línea)").pack(side=tk.LEFT, padx=10)

        log_hdr = ttk.Frame(parent)
        log_hdr.pack(fill=tk.X, padx=8, pady=(8, 0))
        ttk.Label(log_hdr, text="Consola serie").pack(side=tk.LEFT)
        ttk.Button(log_hdr, text="Limpiar consola", command=self.clear_log).pack(
            side=tk.RIGHT
        )
        self.log = tk.Text(parent, height=36, wrap=tk.NONE, font=("Menlo", 11))
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.refresh_ports()

    def refresh_ports(self) -> None:
        ports = list_serial_ports()
        self.port_cb["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def selected_port(self) -> str:
        return self.port_var.get().strip()

    def log_line(self, direction: str, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log.insert(tk.END, f"{ts} {direction} {text}\n")
        self.log.see(tk.END)

    def clear_log(self) -> None:
        self.log.delete("1.0", tk.END)

    def refresh_session_ui(self, connected: bool, online: bool, usb_mode: bool) -> None:
        self.btn_conn.config(text="Desconectar" if connected else "Conectar")
        self.port_cb.config(state=("disabled" if connected else "readonly"))
        if connected:
            if not self.btn_ping.winfo_ismapped():
                self.btn_ping.pack(side=tk.LEFT, padx=4)
        else:
            self.btn_ping.pack_forget()

        if usb_mode:
            self.btn_mode.config(text="Cambiar a modo Manual")
        else:
            self.btn_mode.config(text="Cambiar a modo USB")
        cmd = tk.NORMAL if online else tk.DISABLED
        self.btn_mode.config(state=cmd)
        self.btn_stat.config(state=cmd)
        self.btn_ping.config(state=(tk.NORMAL if online else tk.DISABLED))
        self.interval_cb.config(state="readonly")

    def stat_interval_ms(self) -> int:
        return STAT_INTERVALS_MS.get(self.stat_interval.get(), 1_000)
