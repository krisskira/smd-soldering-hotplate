"""Tooltip con retardo; compatible con ttk en macOS."""

from __future__ import annotations

import tkinter as tk


class ToolTip:
    def __init__(self, widget: tk.Misc, text: str) -> None:
        self.widget = widget
        self.text = text
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        # Mantener referencia viva (evita GC que deja tooltips sin texto)
        widget._smi_tooltip = self  # type: ignore[attr-defined]
        for seq in ("<Enter>", "<FocusIn>"):
            widget.bind(seq, self._schedule, add="+")
        for seq in ("<Leave>", "<FocusOut>", "<ButtonPress>"):
            widget.bind(seq, self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._unschedule()
        self._after_id = self.widget.after(350, self._show)

    def _unschedule(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._tip is not None or not self.text:
            return
        # Posición bajo el widget (coords absolutas de pantalla)
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except tk.TclError:
            return

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        # macOS: evitar ventana vacía hasta actualizar geometría
        tw.withdraw()

        frm = tk.Frame(tw, background="#333333", padx=1, pady=1)
        frm.pack()
        lbl = tk.Label(
            frm,
            text=self.text,
            justify=tk.LEFT,
            background="#fff8dc",
            foreground="#111111",
            font=("TkDefaultFont", 11),
            padx=8,
            pady=6,
            wraplength=360,
        )
        lbl.pack()
        tw.update_idletasks()
        tw.geometry(f"+{x}+{y}")
        tw.deiconify()
        self._tip = tw

    def _hide(self, _event=None) -> None:
        self._unschedule()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None
