"""Pestaña Conexión: puerto, sesión, sondeo y consola serie."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import theme as ui_theme
from constants import STAT_INTERVALS_MS
from serial_link import BAUD, list_serial_ports
from views.layout import add_panel, content_row

if TYPE_CHECKING:
    from controller import AppController


class ConnectionView:
    def __init__(self, parent: ttk.Frame, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.poll_stat = tk.BooleanVar(value=True)
        self.stat_interval = tk.StringVar(value="1 s")
        self.port_var = tk.StringVar()
        self._poll_locked = False

        band = content_row(parent, pady=(8, 4))

        port_box = ttk.LabelFrame(band, text="Puerto serie")
        row = ttk.Frame(port_box)
        row.pack(padx=8, pady=8)
        ttk.Label(row, text="Puerto").pack(side=tk.LEFT)
        self.port_cb = ttk.Combobox(row, textvariable=self.port_var, width=28)
        self.port_cb.pack(side=tk.LEFT, padx=6)
        ttk.Button(row, text="Refrescar", command=self.refresh_ports).pack(side=tk.LEFT)
        ttk.Label(row, text=f"{BAUD} 8N1").pack(side=tk.LEFT, padx=10)
        self.btn_conn = ttk.Button(
            row, text="Conectar", command=ctrl.toggle_conn, style="Accent.TButton"
        )
        self.btn_conn.pack(side=tk.LEFT, padx=4)
        self.btn_ping = ttk.Button(row, text="Ping", command=ctrl.ping)

        sess = ttk.LabelFrame(band, text="Sesión")
        row2 = ttk.Frame(sess)
        row2.pack(padx=8, pady=8)
        self.btn_mode = ttk.Button(
            row2, text="Cambiar a modo USB", command=ctrl.toggle_mode
        )
        self.btn_mode.pack(side=tk.LEFT, padx=2)
        self.btn_stat = ttk.Button(
            row2, text="Consultar estado", command=ctrl.query_stat
        )
        self.btn_stat.pack(side=tk.LEFT, padx=2)

        poll = ttk.LabelFrame(band, text="Sondeo de estado")
        row3 = ttk.Frame(poll)
        row3.pack(padx=8, pady=8)
        self.poll_cb = ttk.Checkbutton(
            row3, text="Activar", variable=self.poll_stat, command=ctrl.toggle_stat_poll
        )
        self.poll_cb.pack(side=tk.LEFT)
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
        self.poll_note = ttk.Label(poll, text="", style="Muted.TLabel")
        self.poll_note.pack(padx=8, pady=(0, 6), anchor=tk.W)

        add_panel(band, port_box)
        add_panel(band, sess)
        add_panel(band, poll)

        log_box = ttk.LabelFrame(parent, text="Consola serie")
        log_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        log_hdr = ttk.Frame(log_box)
        log_hdr.pack(fill=tk.X, padx=8, pady=(6, 0))
        ttk.Label(
            log_hdr,
            text="Tráfico AT: órdenes, respuestas y tramas $HP.",
            style="Muted.TLabel",
        ).pack(side=tk.LEFT)
        ttk.Button(log_hdr, text="Exportar", command=self.export_log).pack(
            side=tk.RIGHT, padx=(4, 0)
        )
        ttk.Button(log_hdr, text="Limpiar", command=self.clear_log).pack(side=tk.RIGHT)
        self.log = tk.Text(log_box, height=16, wrap=tk.NONE, borderwidth=0)
        self.log.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.apply_theme()
        self.refresh_ports()

    def set_poll_locked(self, locked: bool) -> None:
        """Durante HEAT: fuerza Activar + 1 s y bloquea los controles."""
        self._poll_locked = bool(locked)
        if locked:
            self.poll_stat.set(True)
            self.stat_interval.set("1 s")
            self.poll_cb.config(state=tk.DISABLED)
            self.interval_cb.config(state=tk.DISABLED)
        elif not self._ctrl.state.usb_mode:
            self.poll_cb.config(state=tk.NORMAL)
            self.interval_cb.config(state="readonly")

    def apply_theme(self) -> None:
        t = ui_theme.get()
        fam = t.get("console_font_family") or "Menlo"
        self.log.configure(
            font=(fam, int(t["console_font_size"])),
            bg=str(t["console_bg"]),
            fg=str(t["console_fg"]),
            insertbackground=str(t["console_fg"]),
            highlightbackground=str(t["console_border"]),
            highlightcolor=str(t["console_border"]),
            highlightthickness=1,
        )

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

    def export_log(self) -> None:
        text = self.log.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Consola", "La consola está vacía")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Texto", "*.log"), ("Texto", "*.txt")],
            initialfile="hotplate_consola.log",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        messagebox.showinfo("Consola", f"Guardado {path}")

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
        if usb_mode:
            self.poll_cb.config(state=tk.DISABLED)
            self.interval_cb.config(state=tk.DISABLED)
            self.poll_note.config(text="Pausado: en USB el equipo envía $HP cada 1 s")
        else:
            self.poll_note.config(text="")
            if not self._poll_locked:
                self.poll_cb.config(state=tk.NORMAL)
                self.interval_cb.config(state="readonly")

    def stat_interval_ms(self) -> int:
        return STAT_INTERVALS_MS.get(self.stat_interval.get(), 1_000)
