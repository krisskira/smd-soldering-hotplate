"""Pestaña Conexión: puerto, sesión, sondeo y consola serie."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import theme as ui_theme
from constants import STAT_INTERVALS_MS
from serial_link import BAUD, list_serial_ports
from widgets import ui

if TYPE_CHECKING:
    from controller import AppController

TITLE_FG = "#091d2e"
TERM_TIME = "#7f8c8d"
TERM_TX = "#3498db"
TERM_RX = "#2ecc71"
TERM_ERR = "#e74c3c"
TERM_H = 420
TERM_CORNER = 7
FILTERS = ("Todos", "Solo TX", "Solo RX", "Errores")


class ConnectionView:
    def __init__(self, parent: tk.Misc, ctrl: "AppController") -> None:
        self._ctrl = ctrl
        self.poll_stat = tk.BooleanVar(value=True)
        self.stat_interval = tk.StringVar(value="1 s")
        self.port_var = tk.StringVar()
        self._poll_locked = False
        self._poll_disabled = False
        self.log_filter = tk.StringVar(value="Todos")
        self.auto_scroll = tk.BooleanVar(value=True)
        self._log_rows: list[tuple[str, str, str]] = []

        root = tk.Frame(parent, bg=ui.BG)
        root.pack(fill=tk.BOTH, expand=True, padx=16, pady=(20, 12))

        band = tk.Frame(root, bg=ui.BG)
        band.pack(fill=tk.X)
        for col in range(3):
            band.columnconfigure(col, weight=1, uniform="conn")

        # Puerto serie
        port_box, body, foot = self._card(band, "Puerto serie")
        port_box.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 8))
        self.link_chip = ui.Chip(
            self._chip_slot, "Desconectado", fill="#f1f5f9", fg=ui.SLATE, border="#e2e8f0",
            font=ui.mono(10, "bold"), padx=8, height=20, radius=4, dot="#94a3b8",
        )
        self.link_chip.pack(side=tk.RIGHT)
        row = tk.Frame(body, bg=ui.CARD)
        row.pack(fill=tk.X)
        ui.Line(row, "Puerto:", font=ui.sans(12), fg=ui.MUTED, height=34, width=48).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ui.Button(row, "Refrescar", command=self.refresh_ports, variant="secondary",
                  padx=10, height=28, radius=4).pack(side=tk.RIGHT, padx=(8, 0))
        self.port_cb = ui.Select(row, self.port_var, (), height=34, fill=ui.BG,
                                 font=ui.mono(11))
        self.port_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ui.Line(body, f"{BAUD} 8N1", font=ui.mono(11), fg=ui.MUTED, height=17).pack(
            anchor=tk.W, padx=(56, 0), pady=(8, 3)
        )
        self.btn_conn = ui.Button(foot, "Conectar", command=ctrl.toggle_conn, variant="primary",
                                  height=28, radius=4)
        self.btn_conn.pack(side=tk.LEFT)
        self.btn_ping = ui.Button(foot, "Ping", command=ctrl.ping, variant="secondary",
                                  height=28, radius=4)

        # Sesión
        sess_box, body, foot = self._card(band, "Sesión")
        sess_box.grid(row=0, column=1, sticky=tk.NSEW, padx=4)
        self.mode_chip = ui.Chip(
            self._chip_slot, "Modo Manual", fill=ui.ACCENT, fg="#ffffff",
            font=ui.mono(10, "bold"), padx=8, height=20, radius=4,
        )
        self.mode_chip.pack(side=tk.RIGHT)
        self.session_note = ui.Paragraph(
            body,
            "En modo USB el HotPanel solo muestra la temperatura y el botón EXIT. "
            "RUN, STOP y CFG requieren modo USB.",
            font=ui.sans(12), fg=ui.MUTED, line_h=20,
        )
        self.session_note.pack(fill=tk.X)
        self.btn_mode = ui.Button(foot, "Cambiar a modo USB", command=ctrl.toggle_mode,
                                  variant="secondary", height=28, radius=4)
        self.btn_mode.pack(side=tk.LEFT)
        self.btn_stat = ui.Button(foot, "Consultar estado", command=ctrl.query_stat,
                                  variant="secondary", height=28, radius=4)
        self.btn_stat.pack(side=tk.LEFT, padx=(8, 0))

        # Sondeo
        poll_box, body, foot = self._card(band, "Sondeo de estado")
        poll_box.grid(row=0, column=2, sticky=tk.NSEW, padx=(8, 0))
        row3 = tk.Frame(body, bg=ui.CARD)
        row3.pack(fill=tk.X)
        self.poll_cb = ui.CheckBox(row3, self.poll_stat, "Activar", command=ctrl.toggle_stat_poll,
                                   size=14, font=ui.sans(12))
        self.poll_cb.pack(side=tk.LEFT)
        ui.Line(row3, "cada", font=ui.sans(12), fg=ui.MUTED, height=22).pack(
            side=tk.LEFT, padx=(12, 8)
        )
        self.interval_cb = ui.Select(
            row3, self.stat_interval, list(STAT_INTERVALS_MS.keys()), width=72, height=22,
            fill=ui.BG, font=ui.mono(11), on_select=ctrl.toggle_stat_poll,
        )
        self.interval_cb.pack(side=tk.LEFT)
        self.poll_note = ui.Line(foot, "", font=ui.sans(11), fg=ui.MUTED, height=17)
        self.poll_note.pack(side=tk.LEFT)
        self.stat_interval.trace_add("write", lambda *_: self._sync_poll_note())

        # Consola
        # overflow-hidden: cabecera y consola llegan al borde; las esquinas las pintan
        # las franjas de la caja (pady = radio - 1).
        log_box = ui.Box(root, fill=ui.CARD, border=ui.BORDER, radius=8, padx=0,
                         pady=TERM_CORNER)
        self._log_box = log_box
        log_box.pack(fill=tk.X, pady=(12, 0))
        hdr = tk.Frame(log_box.body, bg=ui.CARD, height=42 - TERM_CORNER)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        ui.Line(hdr, "Consola serie", font=ui.sans(13, "bold"), fg=TITLE_FG, height=20).pack(
            side=tk.LEFT, padx=(13, 8)
        )
        ui.Line(hdr, "Tráfico AT: órdenes, respuestas y tramas $HP.", font=ui.sans(12),
                fg=ui.MUTED, height=20).pack(side=tk.LEFT)
        actions = tk.Frame(hdr, bg=ui.CARD)
        actions.pack(side=tk.RIGHT, padx=(0, 13))
        ui.Button(actions, "Exportar", command=self.export_log, variant="secondary",
                  font=ui.sans(11), padx=8, height=22, radius=4).pack(side=tk.RIGHT)
        ui.Button(actions, "Limpiar", command=self.clear_log, variant="secondary",
                  font=ui.sans(11), padx=8, height=22, radius=4).pack(side=tk.RIGHT, padx=(0, 6))
        ui.vline(actions, ui.BORDER).pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 6), pady=2)
        ui.CheckBox(actions, self.auto_scroll, "Auto-scroll", size=14, font=ui.sans(11),
                    fg=ui.MUTED).pack(side=tk.RIGHT, padx=(0, 12))
        seg = ui.Box(actions, fill=ui.BG, border=ui.blend(ui.BORDER, ui.BG, 0.7), radius=4,
                     padx=2, pady=2)
        seg.pack(side=tk.RIGHT, padx=(0, 12))
        self._filter_btns: dict[str, ui.Button] = {}
        for text in FILTERS:
            btn = ui.Button(seg.body, text, command=lambda t=text: self._set_filter(t),
                            variant="tab", font=ui.sans(11), padx=8, height=20, radius=4)
            btn.pack(side=tk.LEFT)
            self._filter_btns[text] = btn
        self._set_filter("Todos")
        rule = ui.hline(log_box.body, ui.BORDER)
        rule.pack(fill=tk.X)
        self._term_rule = rule
        log_box.add_band(rule, ui.BORDER, "top", rule=False)
        log_box.add_band(hdr, ui.CARD, "top", rule=False)

        term = tk.Frame(log_box.body, height=TERM_H - TERM_CORNER, bg="#1e1e1e")
        term.pack(fill=tk.X)
        term.pack_propagate(False)
        log_box.add_band(term, "#1e1e1e", "bottom", rule=False)
        self._term = term
        self.log = tk.Text(term, wrap=tk.NONE, borderwidth=0, padx=16, pady=12, cursor="xterm")
        scroll = ttk.Scrollbar(term, orient=tk.VERTICAL, command=self.log.yview,
                               style="Dark.Vertical.TScrollbar")
        self.log.configure(yscrollcommand=lambda lo, hi: self._on_log_scroll(scroll, lo, hi))
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log._hp_own_wheel = True  # type: ignore[attr-defined]
        self.apply_theme()
        self.refresh_ports()
        self._sync_poll_note()

    def _on_log_scroll(self, scroll: ttk.Scrollbar, lo: str, hi: str) -> None:
        """Barra solo con desbordamiento (scroll overlay de macOS)."""
        scroll.set(lo, hi)
        needed = float(lo) > 0.0 or float(hi) < 1.0
        if needed and not scroll.winfo_ismapped():
            scroll.pack(side=tk.RIGHT, fill=tk.Y, before=self.log)
        elif not needed and scroll.winfo_ismapped():
            scroll.pack_forget()

    def _card(self, parent: tk.Misc, title: str) -> tuple[ui.Box, tk.Frame, tk.Frame]:
        box = ui.Box(parent, fill=ui.CARD, border=ui.BORDER, radius=8, padx=14, pady=14)
        body = box.body
        head = tk.Frame(body, bg=ui.CARD, height=21)
        head.pack(fill=tk.X)
        head.pack_propagate(False)
        ui.Line(head, title, font=ui.sans(13, "bold"), fg=TITLE_FG, height=20).pack(side=tk.LEFT)
        self._chip_slot = tk.Frame(head, bg=ui.CARD)
        self._chip_slot.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Frame(body, bg=ui.CARD, height=8).pack(fill=tk.X)
        ui.hline(body, ui.BG).pack(fill=tk.X)
        foot = tk.Frame(body, bg=ui.CARD)
        foot.pack(side=tk.BOTTOM, fill=tk.X)
        ui.hline(foot, ui.BG).pack(fill=tk.X, side=tk.TOP, pady=(16, 10))
        foot_row = tk.Frame(foot, bg=ui.CARD)
        foot_row.pack(fill=tk.X)
        content = tk.Frame(body, bg=ui.CARD)
        content.pack(fill=tk.X, pady=(12, 0))
        return box, content, foot_row

    def _set_filter(self, text: str) -> None:
        self.log_filter.set(text)
        for name, btn in self._filter_btns.items():
            btn.configure(variant=("tab-active" if name == text else "tab"))
        if hasattr(self, "log"):
            self._render_log()

    def _sync_poll_note(self) -> None:
        if self._ctrl.state.usb_mode:
            self.poll_note.configure(text="Pausado: en USB el equipo envía $HP cada 1 s")
        elif self._poll_locked:
            self.poll_note.configure(text="HEAT en curso: AT+STAT? cada 1 s")
        else:
            self.poll_note.configure(text=f"AT+STAT? cada {self.stat_interval.get()}")

    def _set_poll_controls(self, enabled: bool) -> None:
        self._poll_disabled = not enabled
        self.poll_cb.set_disabled(not enabled)
        self.interval_cb.configure(state=(tk.NORMAL if enabled else tk.DISABLED))

    def set_poll_locked(self, locked: bool) -> None:
        """Durante HEAT: fuerza Activar + 1 s y bloquea los controles."""
        self._poll_locked = bool(locked)
        if locked:
            self.poll_stat.set(True)
            self.stat_interval.set("1 s")
            self._set_poll_controls(False)
        elif not self._ctrl.state.usb_mode:
            self._set_poll_controls(True)
        self._sync_poll_note()

    def apply_theme(self) -> None:
        t = ui_theme.get()
        fam = ui_theme.mono_family()
        size = ui_theme.px("console_font_size", 11)
        font = (fam, -size)
        bold = (fam, -size, "bold")
        bg = str(t["console_bg"])
        fg = str(t["console_fg"])
        border = str(t["console_border"])
        self._term.configure(bg=bg)
        self._log_box.set_band_color(self._term, bg)
        self._term_rule.configure(bg=border)
        self._log_box.set_band_color(self._term_rule, border)
        self.log.configure(
            font=font, bg=bg, fg=fg, insertbackground=fg, highlightthickness=0,
            selectbackground="#264f78", selectforeground="#ffffff",
        )
        mono_w = ui.measure(font, "0")
        time_w = max(96, mono_w * 13)
        self.log.configure(tabs=(time_w + 14, "center", time_w + 28, "left"))
        lines = ui.line_height(font)
        extra = max(0, 22 - lines)
        self.log.configure(spacing1=extra // 2, spacing3=extra - extra // 2)
        self.log.tag_configure("ts", foreground=TERM_TIME)
        self.log.tag_configure("TX", foreground=TERM_TX, font=bold)
        self.log.tag_configure("RX", foreground=TERM_RX, font=bold)
        self.log.tag_configure("RX_text", foreground=TERM_RX)
        self.log.tag_configure("frame", foreground=fg)
        self.log.tag_configure("!!", foreground=TERM_ERR, font=bold)
        self.log.tag_configure("--", foreground=TERM_TIME, font=bold)
        self.log.tag_configure("--text", foreground=TERM_TIME)

    def refresh_ports(self) -> None:
        ports = list_serial_ports()
        self.port_cb.set_values(ports)
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def selected_port(self) -> str:
        return self.port_var.get().strip()

    def _insert_row(self, ts: str, direction: str, text: str) -> None:
        if direction == "TX":
            text_tag = "TX"
        elif direction == "RX":
            text_tag = "frame" if text.startswith("$") else "RX_text"
        elif direction == "!!":
            text_tag = "!!"
        else:
            text_tag = "--text"
        self.log.insert(tk.END, ts, "ts")
        self.log.insert(tk.END, f"\t{direction}\t", direction if direction in ("TX", "RX", "!!") else "--")
        self.log.insert(tk.END, f"{text}\n", text_tag)

    def log_line(self, direction: str, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_rows.append((ts, direction, text))
        if self._matches_filter(direction):
            self._insert_row(ts, direction, text)
            if self.auto_scroll.get():
                self.log.see(tk.END)

    def _matches_filter(self, direction: str) -> bool:
        selected = self.log_filter.get()
        return (
            selected == "Todos"
            or (selected == "Solo TX" and direction == "TX")
            or (selected == "Solo RX" and direction == "RX")
            or (selected == "Errores" and direction == "!!")
        )

    def _render_log(self) -> None:
        self.log.delete("1.0", tk.END)
        for ts, direction, text in self._log_rows:
            if self._matches_filter(direction):
                self._insert_row(ts, direction, text)
        if self.auto_scroll.get():
            self.log.see(tk.END)

    def clear_log(self) -> None:
        self._log_rows.clear()
        self.log.delete("1.0", tk.END)

    def export_log(self) -> None:
        text = "\n".join(
            f"{ts} {direction} {line}" for ts, direction, line in self._log_rows
        ).strip()
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
        self.btn_conn.config(
            text=("Desconectar" if connected else "Conectar"),
            variant=("danger-flat" if connected else "primary"),
        )
        self.port_cb.configure(state=(tk.DISABLED if connected else tk.NORMAL))
        if connected:
            if not self.btn_ping.winfo_ismapped():
                self.btn_ping.pack(side=tk.LEFT, padx=(8, 0))
        else:
            self.btn_ping.pack_forget()
        if connected and online:
            self.link_chip.set("En línea", fill="#e8f8f0", fg=ui.GREEN,
                               border=ui.blend(ui.GREEN, "#e8f8f0", 0.3), dot=ui.GREEN)
        elif connected:
            self.link_chip.set("Preguntando…", fill="#fef5e7", fg="#b9770e",
                               border=ui.blend("#f39c12", "#fef5e7", 0.3), dot="#f39c12")
        else:
            self.link_chip.set("Desconectado", fill="#f1f5f9", fg=ui.SLATE,
                               border="#e2e8f0", dot="#94a3b8")
        self.mode_chip.set("Modo USB" if usb_mode else "Modo Manual")

        self.btn_mode.config(text=("Cambiar a modo Manual" if usb_mode else "Cambiar a modo USB"))
        cmd = tk.NORMAL if online else tk.DISABLED
        self.btn_mode.config(state=cmd)
        self.btn_stat.config(state=cmd)
        self.btn_ping.config(state=cmd)
        if usb_mode:
            self._set_poll_controls(False)
        elif not self._poll_locked:
            self._set_poll_controls(True)
        self._sync_poll_note()

    def stat_interval_ms(self) -> int:
        return STAT_INTERVALS_MS.get(self.stat_interval.get(), 1_000)
