"""Componentes visuales de HotPlate Studio: tarjetas, botones, chips y campos.

Todo se dibuja con Tk puro para reproducir el diseño de Stitch
(`hotplate-studio/design/stitch/`): esquinas redondeadas, bordes de 1 px y
fuentes en píxeles. Las medidas vienen de las clases Tailwind del HTML.
"""

from __future__ import annotations

import math
import sys
import weakref
from typing import Callable, Iterable, Optional

import tkinter as tk
from tkinter import font as tkfont

# ---------------------------------------------------------------- tokens

BG = "#f4f6f8"
CARD = "#ffffff"
BORDER = "#c5d0dc"
SUBTLE = "#dce3eb"
TEXT = "#2c3e50"
MUTED = "#5d6d7e"
FAINT = "#72787f"
SLATE = "#64748b"
ACCENT = "#1a5276"
ACCENT_HOVER = "#154360"
ACCENT_ACTIVE = "#0e3046"
SOFT = "#edf4ff"
SOFT_HOVER = "#d9eaff"
HOVER = "#e7eef4"
RED = "#c0392b"
BLUE = "#2980b9"
GREEN = "#27ae60"
DANGER = "#dc2626"
DANGER_HOVER = "#b91c1c"
ERROR = "#ba1a1a"
ERROR_SOFT = "#ffdad6"
FOOTER_BG = "#f8fafc"

_families: Optional[set[str]] = None


def _family_set() -> set[str]:
    global _families
    if _families is None:
        try:
            _families = set(tkfont.families())
        except tk.TclError:
            return set()
    return _families


def sans_family() -> str:
    """Inter si está instalada; si no, la fuente de sistema (SF en macOS), de métricas parecidas."""
    fams = _family_set()
    if "Inter" in fams:
        return "Inter"
    if sys.platform == "darwin":
        return ".AppleSystemUIFont"
    for name in ("Segoe UI", "DejaVu Sans", "Helvetica"):
        if name in fams:
            return name
    return "Helvetica"


def mono_family() -> str:
    fams = _family_set()
    for name in ("JetBrains Mono", "SF Mono", "Menlo", "Monaco", "Courier"):
        if name in fams:
            return name
    return "Courier"


_FONTS: dict[str, tkfont.Font] = {}
_SCALE = {"body": 1.0, "button": 1.0, "input": 1.0}
_SANS_OVERRIDE: Optional[str] = None
_LIVE: "weakref.WeakSet[tk.Misc]" = weakref.WeakSet()


def _font(kind: str, px: int, weight: str, italic: bool, role: str) -> str:
    w = "bold" if weight in ("bold", "semibold") else "normal"
    name = f"hp-{kind}-{int(px)}-{w}-{'i' if italic else 'r'}-{role}"
    if name not in _FONTS:
        _FONTS[name] = tkfont.Font(
            name=name,
            family=(mono_family() if kind == "mono" else (_SANS_OVERRIDE or sans_family())),
            size=-max(6, round(px * _SCALE.get(role, 1.0))),
            weight=w,
            slant=("italic" if italic else "roman"),
        )
    return name


def sans(px: int, weight: str = "normal", italic: bool = False, role: str = "body") -> str:
    """Fuente de interfaz a `px` píxeles (escalada por el tema). semibold se aproxima a bold."""
    return _font("sans", px, weight, italic, role)


def mono(px: int, weight: str = "normal", role: str = "body") -> str:
    return _font("mono", px, weight, False, role)


def with_role(font, role: str):
    """Misma fuente con otro rol de escala (botones, campos)."""
    if isinstance(font, str) and font.startswith("hp-"):
        _hp, kind, px, weight, slant, _role = font.split("-")
        return _font(kind, int(px), weight, slant == "i", role)
    return font


def apply_theme_fonts(family: str, body_px: int, button_px: int, input_px: int) -> None:
    """Reconfigura en vivo todas las fuentes y redibuja los componentes."""
    global _SANS_OVERRIDE
    _SANS_OVERRIDE = family.strip() or None
    _SCALE["body"] = max(body_px, 6) / 12.0
    _SCALE["button"] = max(button_px, 6) / 12.0
    _SCALE["input"] = max(input_px, 6) / 12.0
    for name, fnt in _FONTS.items():
        _hp, kind, px, _w, _s, role = name.split("-")
        fnt.configure(
            family=(mono_family() if kind == "mono" else (_SANS_OVERRIDE or sans_family())),
            size=-max(6, round(int(px) * _SCALE.get(role, 1.0))),
        )
    for widget in list(_LIVE):
        try:
            widget.refresh()  # type: ignore[attr-defined]
        except tk.TclError:
            pass


def scaled(base: int, font) -> int:
    """Alto de caja `base` escalado con el tamaño de fuente del tema (1:1 en defaults)."""
    if isinstance(font, str) and font.startswith("hp-"):
        return max(1, round(base * _SCALE.get(font.split("-")[-1], 1.0)))
    return base


def _as_font(font) -> tkfont.Font:
    if isinstance(font, str) and font in _FONTS:
        return _FONTS[font]
    return tkfont.Font(font=font)


def measure(font, text: str) -> int:
    return _as_font(font).measure(text)


def line_height(font) -> int:
    return _as_font(font).metrics("linespace")


def blend(color: str, over: str, alpha: float) -> str:
    """`color` con opacidad `alpha` sobre `over`."""
    def rgb(c: str) -> tuple[int, int, int]:
        c = c.lstrip("#")
        return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)

    try:
        a, b = rgb(color), rgb(over)
    except (ValueError, IndexError):
        return color
    mix = [round(x * alpha + y * (1 - alpha)) for x, y in zip(a, b)]
    return "#%02x%02x%02x" % tuple(mix)


def parent_bg(widget: tk.Misc) -> str:
    try:
        return str(widget.cget("bg"))
    except tk.TclError:
        try:
            return str(widget.cget("background"))
        except tk.TclError:
            return BG


# ------------------------------------------------------------ geometría


def rounded_points(
    x0: float, y0: float, x1: float, y1: float, radii: Iterable[float]
) -> list[float]:
    """Contorno de un rectángulo con radios (tl, tr, br, bl)."""
    tl, tr, br, bl = (max(0.0, float(r)) for r in radii)
    lim = min((x1 - x0) / 2.0, (y1 - y0) / 2.0)
    tl, tr, br, bl = (min(r, lim) for r in (tl, tr, br, bl))
    pts: list[float] = []

    def arc(cx: float, cy: float, r: float, a0: float, a1: float) -> None:
        if r <= 0:
            pts.extend((cx, cy))
            return
        steps = max(4, int(r))
        for i in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * i / steps)
            pts.extend((cx + r * math.cos(a), cy + r * math.sin(a)))

    arc(x0 + tl, y0 + tl, tl, 180, 270)
    arc(x1 - tr, y0 + tr, tr, 270, 360)
    arc(x1 - br, y1 - br, br, 0, 90)
    arc(x0 + bl, y1 - bl, bl, 90, 180)
    return pts


def round_rect(
    canvas: tk.Canvas,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    r: float,
    *,
    fill: str = "",
    outline: str = "",
    width: float = 1,
    radii: Optional[tuple[float, float, float, float]] = None,
    tags: str = "",
) -> int:
    """Caja redondeada que cubre los píxeles x0…x1 / y0…y1 (Tk Aqua: coordenadas enteras)."""
    if not outline:
        x1, y1 = x1 + 1, y1 + 1
    pts = rounded_points(x0, y0, x1, y1, radii if radii is not None else (r, r, r, r))
    return canvas.create_polygon(
        pts, fill=fill, outline=outline, width=width if outline else 0, tags=tags
    )


# ---------------------------------------------------------------- iconos


def draw_icon(
    canvas: tk.Canvas, name: str, x: float, y: float, size: float, color: str
) -> None:
    """Iconos vectoriales simples inspirados en Material Symbols."""
    s = size / 24.0

    def P(px: float, py: float) -> tuple[float, float]:
        return x + px * s, y + py * s

    w = max(1.4, 2.0 * s)
    line = dict(fill=color, width=w, capstyle=tk.ROUND, joinstyle=tk.ROUND)
    if name == "heat":
        for off in (-4, 0, 4):
            pts = []
            for i in range(13):
                t = i / 12.0
                pts.extend(P(12 + off + 1.3 * math.sin(t * 3 * math.pi), 4 + 16 * t))
            canvas.create_line(*pts, smooth=True, **line)
    elif name == "tune":
        for yy, kx in ((6, 15), (12, 8), (18, 13)):
            canvas.create_line(*P(3, yy), *P(21, yy), **line)
            canvas.create_line(*P(kx, yy - 2.6), *P(kx, yy + 2.6), **line)
    elif name == "monitor":
        canvas.create_line(
            *P(2, 12), *P(7, 12), *P(9.5, 6), *P(13, 18), *P(15.5, 10),
            *P(17, 12), *P(22, 12), **line,
        )
    elif name == "board":
        canvas.create_rectangle(*P(5, 5), *P(19, 19), outline=color, width=w)
        canvas.create_rectangle(*P(9, 9), *P(15, 15), outline=color, width=w)
        for k in (8, 12, 16):
            canvas.create_line(*P(k, 2), *P(k, 5), **line)
            canvas.create_line(*P(k, 19), *P(k, 22), **line)
            canvas.create_line(*P(2, k), *P(5, k), **line)
            canvas.create_line(*P(19, k), *P(22, k), **line)
    elif name == "chart":
        canvas.create_line(
            *P(3, 18), *P(9, 11), *P(13, 15), *P(21, 6), **line
        )
    elif name == "stop":
        canvas.create_oval(*P(3, 3), *P(21, 21), outline=color, width=w)
        canvas.create_rectangle(*P(9, 9), *P(15, 15), fill=color, outline=color)
    elif name == "play":
        canvas.create_polygon(
            *P(8, 5), *P(19, 12), *P(8, 19), fill=color, outline=color
        )
    elif name == "download":
        canvas.create_line(*P(12, 4), *P(12, 15), **line)
        canvas.create_line(*P(7, 10.5), *P(12, 15.5), *P(17, 10.5), **line)
        canvas.create_line(*P(5, 20), *P(19, 20), **line)
    elif name == "sync":
        canvas.create_arc(
            *P(4, 4), *P(20, 20), start=20, extent=150, style=tk.ARC,
            outline=color, width=w,
        )
        canvas.create_arc(
            *P(4, 4), *P(20, 20), start=200, extent=150, style=tk.ARC,
            outline=color, width=w,
        )
        canvas.create_polygon(*P(3, 9.5), *P(5.5, 13.5), *P(8, 9.5), fill=color, outline=color)
        canvas.create_polygon(*P(16, 14.5), *P(18.5, 10.5), *P(21, 14.5), fill=color, outline=color)
    elif name == "save":
        canvas.create_rectangle(*P(4, 4), *P(20, 20), outline=color, width=w)
        canvas.create_rectangle(*P(8, 4), *P(15, 9), outline=color, width=w)
        canvas.create_rectangle(*P(8, 13), *P(16, 20), outline=color, width=w)
    elif name == "info":
        canvas.create_oval(*P(2.5, 2.5), *P(21.5, 21.5), outline=color, width=w)
        canvas.create_line(*P(12, 11), *P(12, 17), **line)
        canvas.create_oval(*P(11, 6.5), *P(13, 8.5), fill=color, outline=color)
    elif name == "timer":
        canvas.create_oval(*P(4, 5), *P(20, 21), outline=color, width=w)
        canvas.create_line(*P(12, 9), *P(12, 13.5), **line)
        canvas.create_line(*P(9, 2.5), *P(15, 2.5), **line)
    elif name == "close":
        canvas.create_line(*P(6, 6), *P(18, 18), **line)
        canvas.create_line(*P(18, 6), *P(6, 18), **line)
    elif name == "verified":
        canvas.create_oval(*P(2.5, 2.5), *P(21.5, 21.5), outline=color, width=w)
        canvas.create_line(*P(7.5, 12.5), *P(10.5, 15.5), *P(16.5, 9), **line)
    elif name == "chevron":
        canvas.create_line(*P(7, 10), *P(12, 15), *P(17, 10), **line)


class Icon(tk.Canvas):
    def __init__(
        self, parent: tk.Misc, name: str, *, size: int = 20, color: str = ACCENT,
        bg: Optional[str] = None,
    ) -> None:
        super().__init__(
            parent, width=size, height=size, bg=bg or parent_bg(parent),
            highlightthickness=0, bd=0,
        )
        self._name = name
        self._size = size
        self.set_color(color)

    def set_color(self, color: str) -> None:
        self.delete("all")
        draw_icon(self, self._name, 0, 0, self._size, color)


# ---------------------------------------------------------------- Box


class Box(tk.Frame):
    """Contenedor redondeado. El contenido va en `.body`.

    `padx`/`pady` son el padding CSS: con borde se suma 1 px (el borde queda fuera).
    `bands` pinta franjas de color (cabecera o pie) recortadas a las esquinas;
    `accent` dibuja la barra lateral izquierda de las tarjetas de Ajustes.
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        fill: str = CARD,
        border: Optional[str] = BORDER,
        radius: int = 8,
        padx: int | tuple[int, int] = 0,
        pady: int | tuple[int, int] = 0,
        bg: Optional[str] = None,
        accent: Optional[str] = None,
        accent_width: int = 6,
        border_left: Optional[tuple[str, int]] = None,
    ) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, bd=0, highlightthickness=0)
        self._fill = fill
        self._border = border
        self._radius = radius
        self._accent = accent
        self._accent_w = accent_width
        self._border_left = border_left
        self._bands: list[tuple[tk.Misc, str, str, bool]] = []
        self._cv = tk.Canvas(self, bg=outer, highlightthickness=0, bd=0)
        self._cv.place(x=0, y=0, relwidth=1, relheight=1)
        if border:
            padx, pady = _grow(padx), _grow(pady)
        self.body = tk.Frame(self, bg=fill, bd=0, highlightthickness=0)
        self.body.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)
        self.bind("<Configure>", lambda _e: self.redraw(), add="+")

    def set_fill(self, fill: str, border: Optional[str] = None) -> None:
        self._fill = fill
        if border is not None:
            self._border = border
        self.body.configure(bg=fill)
        self.redraw()

    def set_border_left(self, spec: Optional[tuple[str, int]]) -> None:
        self._border_left = spec
        self.redraw()

    def add_band(
        self, widget: tk.Misc, color: str, where: str = "bottom", *, rule: bool = True
    ) -> None:
        """Pinta una franja redondeada detrás de `widget` hasta el borde de la caja."""
        self._bands.append((widget, color, where, rule))
        widget.bind("<Configure>", lambda _e: self.redraw(), add="+")
        widget.bind("<Map>", lambda _e: self.redraw(), add="+")

    def set_band_color(self, widget: tk.Misc, color: str) -> None:
        self._bands = [
            (w, (color if w is widget else c), where, rule)
            for w, c, where, rule in self._bands
        ]
        self.redraw()

    def redraw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        r = self._radius
        x0, y0, x1, y1 = 0, 0, w - 1, h - 1
        if self._accent:
            round_rect(cv, x0, y0, x1, y1, r, fill=self._accent)
            aw = self._accent_w
            round_rect(
                cv, x0 + aw, y0, x1, y1, r, fill=self._fill, radii=(0, r, r, 0)
            )
        else:
            round_rect(cv, x0, y0, x1, y1, r, fill=self._fill)
        for widget, color, where, rule in self._bands:
            try:
                if not widget.winfo_ismapped():
                    continue
                wy = widget.winfo_rooty() - self.winfo_rooty()
                wh = widget.winfo_height()
            except tk.TclError:
                continue
            left = x0 + (self._accent_w if self._accent else 0)
            if where == "bottom":
                radii = (0, 0, r, 0 if self._accent else r)
                round_rect(cv, left, wy, x1, y1, r, fill=color, radii=radii)
                if rule:
                    cv.create_line(left, wy, x1, wy, fill=SUBTLE)
            else:
                radii = (0 if self._accent else r, r, 0, 0)
                round_rect(cv, left, y0, x1, wy + wh, r, fill=color, radii=radii)
                if rule:
                    cv.create_line(left, wy + wh, x1, wy + wh, fill=SUBTLE)
        if self._border_left:
            color, bw = self._border_left
            cv.create_rectangle(0, 0, bw, h, fill=color, outline="")
        if self._border:
            round_rect(cv, x0, y0, x1, y1, r, outline=self._border, width=1)


def _grow(pad):
    if isinstance(pad, tuple):
        return tuple(p + 1 for p in pad)
    return pad + 1


def card(parent: tk.Misc, **kw) -> Box:
    kw.setdefault("padx", 20)
    kw.setdefault("pady", 20)
    return Box(parent, **kw)


def block(parent: tk.Misc, **kw) -> Box:
    """Bloque gris `bg-[#f4f6f8] p-2.5 rounded border-[#dce3eb]`."""
    kw.setdefault("fill", BG)
    kw.setdefault("border", SUBTLE)
    kw.setdefault("radius", 4)
    kw.setdefault("padx", 10)
    kw.setdefault("pady", 10)
    return Box(parent, **kw)


def hline(parent: tk.Misc, color: str = SUBTLE) -> tk.Frame:
    return tk.Frame(parent, bg=color, height=1, bd=0, highlightthickness=0)


def vline(parent: tk.Misc, color: str = SUBTLE) -> tk.Frame:
    return tk.Frame(parent, bg=color, width=1, bd=0, highlightthickness=0)


def label(
    parent: tk.Misc, text: str = "", *, font: tuple = None, fg: str = TEXT,
    bg: Optional[str] = None, textvariable: Optional[tk.Variable] = None, **kw,
) -> tk.Label:
    opts = dict(
        bg=bg or parent_bg(parent), fg=fg, font=font or sans(12), bd=0,
        padx=0, pady=0, highlightthickness=0,
    )
    opts.update(kw)
    if textvariable is not None:
        return tk.Label(parent, textvariable=textvariable, **opts)
    return tk.Label(parent, text=text, **opts)


class Paragraph(tk.Canvas):
    """Párrafo con ajuste de línea y paso fijo (`leading-*` de CSS)."""

    def __init__(self, parent: tk.Misc, text: str = "", *, font: tuple = None,
                 fg: str = TEXT, line_h: int = 20, bg: Optional[str] = None) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, height=line_h, bd=0, highlightthickness=0)
        self._text = text
        self._font = font or sans(12)
        self._fg = fg
        self._line_h = line_h
        self._width = 0
        self.bind("<Configure>", self._on_configure, add="+")
        _LIVE.add(self)

    def _on_configure(self, e) -> None:
        if e.width != self._width:
            self._width = e.width
            self._render()

    def _wrap(self, width: int) -> list[str]:
        lines: list[str] = []
        for chunk in self._text.split("\n"):
            cur = ""
            for word in chunk.split(" "):
                probe = f"{cur} {word}" if cur else word
                if cur and measure(self._font, probe) > width:
                    lines.append(cur)
                    cur = word
                else:
                    cur = probe
            lines.append(cur)
        return lines

    def _render(self) -> None:
        self.delete("all")
        if self._width < 20:
            return
        pitch = scaled(self._line_h, self._font)
        lines = self._wrap(self._width)
        for i, text in enumerate(lines):
            self.create_text(0, i * pitch + pitch / 2, text=text, anchor=tk.W,
                             fill=self._fg, font=self._font)
        tk.Canvas.configure(self, height=max(1, len(lines)) * pitch)

    def refresh(self) -> None:
        self._render()

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        for key, attr in (("text", "_text"), ("fg", "_fg"), ("font", "_font")):
            if key in kw:
                setattr(self, attr, kw.pop(key))
        if kw:
            tk.Canvas.configure(self, **kw)
        self._render()

    config = configure


class Line(tk.Frame):
    """Etiqueta dentro de una caja de alto fijo (line-height de CSS)."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str = "",
        *,
        font: tuple = None,
        fg: str = TEXT,
        height: int = 16,
        width: Optional[int] = None,
        anchor: str = tk.W,
        bg: Optional[str] = None,
        textvariable: Optional[tk.Variable] = None,
        **label_kw,
    ) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, height=height, bd=0, highlightthickness=0)
        if width is not None:
            self.configure(width=width)
        self.pack_propagate(False)
        self.grid_propagate(False)
        opts = dict(bg=outer, fg=fg, font=font or sans(12), bd=0, padx=0, pady=0)
        opts.update(label_kw)
        if textvariable is not None:
            self.label = tk.Label(self, textvariable=textvariable, **opts)
        else:
            self.label = tk.Label(self, text=text, **opts)
        relx = {tk.W: 0.0, tk.E: 1.0, tk.CENTER: 0.5}.get(anchor, 0.0)
        self.label.place(relx=relx, rely=0.5, anchor=anchor)
        self._fixed_width = width is not None
        self._base_h = height
        if not self._fixed_width:
            self._auto_width()
            self.label.bind("<Configure>", lambda _e: self._auto_width(), add="+")
        _LIVE.add(self)

    def refresh(self) -> None:
        try:
            tk.Frame.configure(self, height=scaled(self._base_h, self.label.cget("font")))
        except tk.TclError:
            pass
        self._auto_width()

    def _auto_width(self) -> None:
        if self._fixed_width:
            return
        try:
            width = self.label.winfo_reqwidth()
            if int(tk.Frame.cget(self, "width")) != width:
                tk.Frame.configure(self, width=width)
        except tk.TclError:
            pass

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        label_keys = {"text", "fg", "font", "textvariable", "foreground", "cursor"}
        lk = {k: kw.pop(k) for k in list(kw) if k in label_keys}
        if "bg" in kw:
            lk["bg"] = kw["bg"]
        if lk:
            self.label.configure(**lk)
            self._auto_width()
        return super().configure(**kw) if kw else None

    config = configure  # type: ignore[assignment]

    def cget(self, key: str):  # type: ignore[override]
        if key in ("text", "fg", "font", "foreground"):
            return self.label.cget(key)
        return super().cget(key)


class CardHeader(tk.Frame):
    """Cabecera de tarjeta: icono + título a la izquierda, `.right` para chips/botones."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        *,
        icon: Optional[str] = None,
        height: int = 24,
        title_font: Optional[tuple] = None,
        title_fg: str = TEXT,
        rule: str = SUBTLE,
        pad_bottom: int = 8,
        icon_size: int = 20,
        gap: int = 8,
    ) -> None:
        bg = parent_bg(parent)
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        row = tk.Frame(self, bg=bg, height=height)
        row.pack(fill=tk.X)
        row.pack_propagate(False)
        self.row = row
        if icon:
            self.icon = Icon(row, icon, size=icon_size, color=ACCENT, bg=bg)
            self.icon.pack(side=tk.LEFT, padx=(0, gap))
        self.title = Line(
            row, title, font=title_font or sans(16, "bold"), fg=title_fg,
            height=height, bg=bg,
        )
        self.title.pack(side=tk.LEFT)
        self.right = tk.Frame(row, bg=bg)
        self.right.pack(side=tk.RIGHT, fill=tk.Y)
        if pad_bottom:
            tk.Frame(self, bg=bg, height=pad_bottom).pack(fill=tk.X)
        if rule:
            hline(self, rule).pack(fill=tk.X)


# -------------------------------------------------------------- Button

_VARIANTS: dict[str, dict[str, Optional[str]]] = {
    "primary": dict(bg=ACCENT, fg="#ffffff", hover=ACCENT_HOVER, active=ACCENT_ACTIVE, border=None),
    "danger": dict(bg=DANGER, fg="#ffffff", hover=DANGER_HOVER, active="#991b1b", border=None),
    "danger-flat": dict(bg=RED, fg="#ffffff", hover="#a93226", active="#922b21", border=None),
    "secondary": dict(bg=BG, fg=TEXT, hover=HOVER, active="#dbe4ec", border=BORDER),
    "white": dict(bg=CARD, fg=TEXT, hover="#f9fafb", active=HOVER, border=BORDER),
    "soft": dict(bg=SOFT, fg=ACCENT, hover=SOFT_HOVER, active="#c7defa", border=BORDER),
    "outline-danger": dict(bg=CARD, fg=ERROR, hover=ERROR_SOFT, active="#ffc4bd", border=ERROR),
    "tab": dict(bg="", fg=MUTED, hover="", active="", border=None, hover_fg=TEXT),
    "tab-active": dict(bg=ACCENT, fg="#ffffff", hover=ACCENT, active=ACCENT, border=None),
    "ghost": dict(bg="", fg="#7efba4", hover="", active="", border=None, hover_fg="#ffffff"),
}

_STYLE_ALIASES = {
    "Accent.TButton": "primary",
    "Danger.TButton": "danger",
    "TButton": "secondary",
}


class Button(tk.Canvas):
    """Botón plano redondeado. Acepta `config(text=, state=, style=)` como ttk."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        *,
        variant: str = "secondary",
        font: Optional[tuple] = None,
        padx: int = 12,
        height: int = 28,
        radius: int = 6,
        icon: Optional[str] = None,
        icon_size: int = 16,
        gap: int = 8,
        width: Optional[int] = None,
        state: str = tk.NORMAL,
        style: Optional[str] = None,
        bg: Optional[str] = None,
    ) -> None:
        self._outer = bg or parent_bg(parent)
        super().__init__(
            parent, height=height, width=10, bg=self._outer,
            highlightthickness=0, bd=0, cursor="pointinghand",
        )
        self._text = text
        self._command = command
        self._variant = _STYLE_ALIASES.get(style or "", variant)
        self._font = with_role(font or sans(12), "button")
        self._padx = padx
        self._h = height
        self._r = radius
        self._icon = icon
        self._icon_size = icon_size
        self._gap = gap
        self._fixed_w = width
        self._state = str(state)
        self._hover = False
        self._pressed = False
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._render()
        _LIVE.add(self)

    def refresh(self) -> None:
        self._render()

    # compat ttk/tk -----------------------------------------------------
    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        redraw = False
        for key in ("text", "command", "state", "style", "variant", "padx", "icon"):
            if key not in kw:
                continue
            val = kw.pop(key)
            if key == "text":
                self._text = str(val)
            elif key == "command":
                self._command = val
            elif key == "state":
                self._state = str(val)
            elif key == "style":
                self._variant = _STYLE_ALIASES.get(str(val), self._variant)
            elif key == "padx":
                self._padx = int(val)
            elif key == "icon":
                self._icon = val
            else:
                self._variant = str(val)
            redraw = True
        result = super().configure(**kw) if kw else None
        if redraw:
            self._render()
        return result

    config = configure  # type: ignore[assignment]

    def cget(self, key: str):  # type: ignore[override]
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)

    def state(self, spec=None):  # ttk compat
        if spec is None:
            return (self._state,)
        for item in spec:
            if item == "disabled":
                self._state = tk.DISABLED
            elif item == "!disabled":
                self._state = tk.NORMAL
        self._render()
        return None

    # dibujo -------------------------------------------------------------
    def _colors(self) -> tuple[str, str, Optional[str]]:
        v = _VARIANTS.get(self._variant, _VARIANTS["secondary"])
        bg = v["bg"] or ""
        fg = v["fg"] or TEXT
        if self._state == tk.DISABLED:
            base = bg or self._outer
            return (
                blend(base, self._outer, 0.55) if bg else "",
                blend(fg, base, 0.55),
                blend(v["border"], self._outer, 0.55) if v["border"] else None,
            )
        if self._pressed and v["active"]:
            bg = v["active"]
        elif self._hover and v["hover"]:
            bg = v["hover"]
        if self._hover and v.get("hover_fg"):
            fg = v["hover_fg"]  # type: ignore[assignment]
        return bg, fg, v["border"]

    def _render(self) -> None:
        self.delete("all")
        text_w = measure(self._font, self._text) if self._text else 0
        icon_w = self._icon_size + (self._gap if self._text else 0) if self._icon else 0
        w = self._fixed_w or (text_w + icon_w + 2 * self._padx)
        h = scaled(self._h, self._font) if self._text else self._h
        super().configure(width=w, height=h, bg=self._outer)
        bg, fg, border = self._colors()
        if bg or border:
            round_rect(
                self, 0, 0, w - 1, h - 1, self._r,
                fill=bg, outline=border or "", width=1,
            )
        x = (w - (text_w + icon_w)) / 2.0
        cy = h / 2.0
        if self._icon:
            draw_icon(self, self._icon, x, cy - self._icon_size / 2.0, self._icon_size, fg)
            x += icon_w
        if self._text:
            self.create_text(x, cy, text=self._text, anchor=tk.W, fill=fg, font=self._font)
        self.configure(cursor=("arrow" if self._state == tk.DISABLED else "pointinghand"))

    def set_outer_bg(self, color: str) -> None:
        self._outer = color
        self._render()

    def _set_hover(self, on: bool) -> None:
        self._hover = on
        if not on:
            self._pressed = False
        self._render()

    def _on_press(self, _e=None) -> None:
        if self._state == tk.DISABLED:
            return
        self._pressed = True
        self._render()

    def _on_release(self, e=None) -> None:
        if self._state == tk.DISABLED or not self._pressed:
            return
        self._pressed = False
        self._render()
        inside = e is None or (0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height())
        if inside and self._command:
            self._command()

    def invoke(self) -> None:
        if self._state != tk.DISABLED and self._command:
            self._command()


# ---------------------------------------------------------------- Chip


class Chip(tk.Canvas):
    """Etiqueta con fondo redondeado (badge / pastilla)."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str = "",
        *,
        fill: str = "#f1f5f9",
        fg: str = "#475569",
        border: Optional[str] = None,
        font: Optional[tuple] = None,
        padx: int = 8,
        height: int = 20,
        radius: int = 4,
        dot: Optional[str] = None,
        bg: Optional[str] = None,
        textvariable: Optional[tk.StringVar] = None,
    ) -> None:
        self._outer = bg or parent_bg(parent)
        super().__init__(
            parent, height=height, width=10, bg=self._outer,
            highlightthickness=0, bd=0,
        )
        self._text = text
        self._fill = fill
        self._fg = fg
        self._border = border
        self._font = font or sans(12)
        self._padx = padx
        self._h = height
        self._r = radius
        self._dot = dot
        self._var = textvariable
        if textvariable is not None:
            textvariable.trace_add("write", lambda *_: self._render())
        self._render()
        _LIVE.add(self)

    def refresh(self) -> None:
        self._render()

    def set(self, text: Optional[str] = None, **kw) -> None:
        if text is not None:
            self._text = text
        for key in ("fill", "fg", "border", "dot"):
            if key in kw:
                setattr(self, "_" + key, kw[key])
        self._render()

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        changed = False
        if "text" in kw:
            self._text = str(kw.pop("text"))
            changed = True
        if "bg_fill" in kw:
            self._fill = kw.pop("bg_fill")
            changed = True
        result = super().configure(**kw) if kw else None
        if changed:
            self._render()
        return result

    config = configure  # type: ignore[assignment]

    def cget(self, key: str):  # type: ignore[override]
        if key == "text":
            return self._current_text()
        return super().cget(key)

    def _current_text(self) -> str:
        return self._var.get() if self._var is not None else self._text

    def _render(self) -> None:
        self.delete("all")
        text = self._current_text()
        dot_w = 14 if self._dot else 0
        w = measure(self._font, text) + 2 * self._padx + dot_w
        h = scaled(self._h, self._font)
        super().configure(width=w, height=h, bg=self._outer)
        round_rect(
            self, 0, 0, w - 1, h - 1, self._r,
            fill=self._fill, outline=self._border or "", width=1,
        )
        x = self._padx
        cy = h / 2.0
        if self._dot:
            self.create_oval(x, cy - 4, x + 8, cy + 4, fill=self._dot, outline="")
            x += dot_w
        self.create_text(x, cy, text=text, anchor=tk.W, fill=self._fg, font=self._font)


class Dot(tk.Canvas):
    def __init__(self, parent: tk.Misc, color: str = GREEN, size: int = 8, bg=None) -> None:
        super().__init__(
            parent, width=size, height=size, bg=bg or parent_bg(parent),
            highlightthickness=0, bd=0,
        )
        self._size = size
        self.set(color)

    def set(self, color: str) -> None:
        self.delete("all")
        self.create_oval(0, 0, self._size, self._size, fill=color, outline="")


# --------------------------------------------------------------- Field


STEPPER_W = 9


class Field(tk.Frame):
    """Campo de texto redondeado con sufijo opcional (unidad)."""

    def __init__(
        self,
        parent: tk.Misc,
        textvariable: tk.Variable,
        *,
        width: Optional[int] = None,
        height: int = 26,
        font: Optional[tuple] = None,
        fill: str = CARD,
        border: str = SUBTLE,
        radius: int = 4,
        padx: int = 8,
        suffix: Optional[str] = None,
        suffix_font: Optional[tuple] = None,
        suffix_var: Optional[tk.StringVar] = None,
        justify: str = tk.RIGHT,
        bg: Optional[str] = None,
        fg: str = TEXT,
        stepper: Optional[tuple[int, int]] = None,
    ) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, height=height, bd=0, highlightthickness=0)
        if width is not None:
            self.configure(width=width)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._var = textvariable
        self._fill = fill
        self._border = border
        self._radius = radius
        self._focus = False
        self._disabled = False
        self._cv = tk.Canvas(self, bg=outer, highlightthickness=0, bd=0)
        self._cv.place(x=0, y=0, relwidth=1, relheight=1)
        sfont = suffix_font or mono(11)
        suffix_w = 0
        self.suffix: Optional[tk.Label] = None
        if suffix or suffix_var is not None:
            self.suffix = tk.Label(
                self, text=suffix or "", textvariable=suffix_var, bg=fill, fg=MUTED,
                font=sfont, bd=0, padx=0, pady=0,
            )
            probe = suffix or (suffix_var.get() if suffix_var else "")
            suffix_w = measure(sfont, probe) + 6
            self.suffix.place(relx=1.0, x=-padx, rely=0.5, anchor=tk.E)
        self._bounds = stepper
        if stepper is not None:
            spin = tk.Canvas(self, width=STEPPER_W, height=18, bg=fill, highlightthickness=0,
                             bd=0, cursor="arrow")
            spin.place(relx=1.0, x=-4, rely=0.5, anchor=tk.E)
            for pts in ((1, 7, 4.5, 3, 8, 7), (1, 11, 4.5, 15, 8, 11)):
                spin.create_line(*pts, fill=MUTED, width=1.2, capstyle=tk.ROUND,
                                 joinstyle=tk.ROUND)
            spin.bind("<ButtonPress-1>", lambda e: self.step(1 if e.y < 9 else -1))
            for widget in (spin, self):
                widget.bind("<MouseWheel>", lambda e: self.step(1 if e.delta > 0 else -1),
                            add="+")
            suffix_w += STEPPER_W + 2
        self.entry = tk.Entry(
            self, textvariable=textvariable, bd=0, relief=tk.FLAT,
            highlightthickness=0, bg=fill, fg=fg, insertbackground=fg,
            font=with_role(font or mono(12), "input"), justify=justify,
            disabledbackground=fill, disabledforeground=MUTED,
            readonlybackground=fill,
        )
        self.entry.place(
            x=padx, rely=0.5, anchor=tk.W, relwidth=1.0,
            width=-(2 * padx + suffix_w),
        )
        self.entry.bind("<FocusIn>", lambda _e: self._set_focus(True), add="+")
        self.entry.bind("<FocusOut>", lambda _e: self._set_focus(False), add="+")
        self.bind("<Configure>", lambda _e: self._redraw(), add="+")
        self._base_h = height
        _LIVE.add(self)

    def refresh(self) -> None:
        tk.Frame.configure(self, height=scaled(self._base_h, self.entry.cget("font")))

    def step(self, delta: int) -> str:
        """Paso ±1 dentro de `stepper` (flechas de `input type=number`)."""
        if self._bounds is None or self._disabled:
            return "break"
        lo, hi = self._bounds
        try:
            value = int(float(str(self._var.get()).strip()))
        except (TypeError, ValueError):
            value = lo
        self._var.set(str(max(lo, min(hi, value + delta))))
        return "break"

    def _set_focus(self, on: bool) -> None:
        self._focus = on
        self._redraw()

    def set_outer_bg(self, color: str) -> None:
        tk.Frame.configure(self, bg=color)
        self._cv.configure(bg=color)

    def set_border(self, color: str) -> None:
        self._border = color
        self._redraw()

    def set_state(self, state: str) -> None:
        self._disabled = state in (tk.DISABLED, "disabled", "readonly")
        self.entry.configure(state=state)
        self._redraw()

    def _redraw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        border = ACCENT if self._focus else self._border
        round_rect(cv, 0, 0, w - 1, h - 1, self._radius, fill=self._fill,
                   outline=border, width=1)


# -------------------------------------------------------------- Select


class Select(tk.Frame):
    """Desplegable plano (valor + chevron) con menú emergente."""

    def __init__(
        self,
        parent: tk.Misc,
        textvariable: tk.StringVar,
        values: Iterable[str] = (),
        *,
        width: Optional[int] = None,
        height: int = 26,
        font: Optional[tuple] = None,
        fill: str = CARD,
        border: str = BORDER,
        radius: int = 4,
        padx: int = 8,
        on_select: Optional[Callable[[], None]] = None,
        bg: Optional[str] = None,
        editable: bool = False,
    ) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, height=height, bd=0, highlightthickness=0)
        if width is not None:
            self.configure(width=width)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._var = textvariable
        self._values = list(values)
        self._on_select = on_select
        self._fill = fill
        self._border = border
        self._radius = radius
        self._disabled = False
        self._font = with_role(font or mono(11), "input")
        self._cv = tk.Canvas(self, bg=outer, highlightthickness=0, bd=0, cursor="pointinghand")
        self._cv.place(x=0, y=0, relwidth=1, relheight=1)
        self._padx = padx
        self._editable = editable
        self.entry: Optional[tk.Entry] = None
        if editable:
            self.entry = tk.Entry(
                self, textvariable=textvariable, bd=0, relief=tk.FLAT,
                highlightthickness=0, bg=fill, fg=TEXT, font=self._font,
                insertbackground=TEXT,
            )
            self.entry.place(x=padx, rely=0.5, anchor=tk.W, relwidth=1.0, width=-(padx + 24))
        self._cv.bind("<ButtonPress-1>", self._popup)
        self.bind("<Configure>", lambda _e: self._redraw(), add="+")
        textvariable.trace_add("write", lambda *_: self._redraw())

    def set_values(self, values: Iterable[str]) -> None:
        self._values = list(values)

    def __setitem__(self, key: str, value) -> None:
        if key == "values":
            self.set_values(value)
        else:
            super().__setitem__(key, value)

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        if "state" in kw:
            state = str(kw.pop("state"))
            self._disabled = state == tk.DISABLED or state == "disabled"
            if self.entry is not None:
                self.entry.configure(state=("disabled" if self._disabled else "normal"))
            self._redraw()
        if "values" in kw:
            self.set_values(kw.pop("values"))
        return super().configure(**kw) if kw else None

    config = configure  # type: ignore[assignment]

    def _redraw(self) -> None:
        cv = self._cv
        cv.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        fill = self._fill if not self._disabled else blend(self._fill, BG, 0.6)
        round_rect(cv, 0, 0, w - 1, h - 1, self._radius, fill=fill,
                   outline=self._border, width=1)
        fg = TEXT if not self._disabled else blend(TEXT, fill, 0.6)
        if self.entry is None:
            cv.create_text(self._padx, h / 2.0, text=self._var.get(), anchor=tk.W,
                           fill=fg, font=self._font)
        else:
            self.entry.configure(bg=fill, disabledbackground=fill, disabledforeground=fg)
        draw_icon(cv, "chevron", w - 20, h / 2.0 - 7, 14, "#7f8c8d")

    def _popup(self, _e=None) -> None:
        if self._disabled or not self._values:
            return
        menu = tk.Menu(self, tearoff=0)
        for value in self._values:
            menu.add_command(label=value, command=lambda v=value: self._choose(v))
        menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())

    def _choose(self, value: str) -> None:
        self._var.set(value)
        if self._on_select:
            self._on_select()


# ----------------------------------------------------------- CheckBox


class CheckBox(tk.Frame):
    """Casilla 14–16 px con texto opcional, ligada a una BooleanVar."""

    def __init__(
        self,
        parent: tk.Misc,
        variable: tk.BooleanVar,
        text: str = "",
        *,
        command: Optional[Callable[[], None]] = None,
        size: int = 14,
        font: Optional[tuple] = None,
        fg: str = TEXT,
        gap: int = 6,
        bg: Optional[str] = None,
        fade: bool = True,
    ) -> None:
        outer = bg or parent_bg(parent)
        super().__init__(parent, bg=outer, bd=0, highlightthickness=0)
        self._fade = fade
        self._var = variable
        self._command = command
        self._size = size
        self._disabled = False
        self._outer = outer
        self._box = tk.Canvas(self, width=size, height=size, bg=outer,
                              highlightthickness=0, bd=0, cursor="pointinghand")
        self._box.pack(side=tk.LEFT)
        self._label: Optional[tk.Label] = None
        if text:
            self._label = tk.Label(self, text=text, bg=outer, fg=fg,
                                   font=font or sans(12), bd=0, padx=0, pady=0)
            self._label.pack(side=tk.LEFT, padx=(gap, 0))
            self._label.bind("<ButtonRelease-1>", self._toggle)
        self._fg = fg
        self._box.bind("<ButtonRelease-1>", self._toggle)
        variable.trace_add("write", lambda *_: self._render())
        self._render()

    def configure(self, cnf=None, **kw):  # type: ignore[override]
        if cnf:
            kw.update(cnf)
        if "state" in kw:
            self.set_disabled(str(kw.pop("state")) in (tk.DISABLED, "disabled"))
        if "command" in kw:
            self._command = kw.pop("command")
        return super().configure(**kw) if kw else None

    config = configure  # type: ignore[assignment]

    def state(self, spec=None):  # ttk compat
        if spec:
            for item in spec:
                if item == "disabled":
                    self.set_disabled(True)
                elif item == "!disabled":
                    self.set_disabled(False)

    def set_outer_bg(self, color: str) -> None:
        self._outer = color
        tk.Frame.configure(self, bg=color)
        self._box.configure(bg=color)
        if self._label is not None:
            self._label.configure(bg=color)
        self._render()

    def set_disabled(self, on: bool) -> None:
        self._disabled = on
        self._box.configure(cursor=("arrow" if on else "pointinghand"))
        if self._label is not None:
            self._label.configure(fg=blend(self._fg, self._outer, 0.8) if on else self._fg)
        self._render()

    def _toggle(self, _e=None) -> None:
        if self._disabled:
            return
        self._var.set(not bool(self._var.get()))
        if self._command:
            self._command()

    def _render(self) -> None:
        cv = self._box
        cv.delete("all")
        s = self._size
        on = bool(self._var.get())
        fill = ACCENT if on else CARD
        border = ACCENT if on else "#94a3b8"
        if self._disabled and self._fade:
            fill = blend(fill, self._outer, 0.6)
            border = blend(border, self._outer, 0.6)
        round_rect(cv, 0, 0, s - 1, s - 1, 3, fill=fill, outline=border)
        if on:
            cv.create_line(
                s * 0.26, s * 0.52, s * 0.44, s * 0.70, s * 0.76, s * 0.32,
                fill="#ffffff", width=max(1.6, s / 8), capstyle=tk.ROUND, joinstyle=tk.ROUND,
            )


# --------------------------------------------------------------- Spin


class Spin(Field):
    """Campo numérico con flechas arriba/abajo."""

    def __init__(
        self, parent: tk.Misc, textvariable: tk.Variable, *, from_: int, to: int,
        fmt: str = "{}", **kw,
    ) -> None:
        kw.setdefault("justify", tk.LEFT)
        super().__init__(parent, textvariable, **kw)
        self._var = textvariable
        self._lo, self._hi, self._fmt = from_, to, fmt
        arrows = tk.Canvas(self, width=12, height=18, bg=self._fill,
                           highlightthickness=0, bd=0, cursor="pointinghand")
        arrows.place(relx=1.0, x=-6, rely=0.5, anchor=tk.E)
        arrows.create_polygon(3, 7, 6, 3, 9, 7, fill="#7f8c8d", outline="")
        arrows.create_polygon(3, 11, 6, 15, 9, 11, fill="#7f8c8d", outline="")
        arrows.bind("<ButtonRelease-1>", lambda e: self._step(1 if e.y < 9 else -1))
        self.entry.place_configure(width=-(2 * 8 + 14))
        self.entry.bind("<MouseWheel>", lambda e: self._step(1 if e.delta > 0 else -1))

    def _step(self, delta: int) -> None:
        try:
            value = int(float(self._var.get()))
        except (TypeError, ValueError):
            value = self._lo
        value = max(self._lo, min(self._hi, value + delta))
        self._var.set(self._fmt.format(value))


# ---------------------------------------------------------- ScrollPage


class ScrollPage(tk.Frame):
    """Página con desplazamiento vertical; el contenido va en `.inner`.

    La barra flota sobre el margen derecho (como el scroll overlay de macOS) para
    que el ancho útil sea el mismo con o sin desbordamiento.
    """

    def __init__(self, parent: tk.Misc, *, bg: str = BG) -> None:
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self._canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=4
        )
        self._bar = tk.Canvas(self, width=6, bg=bg, highlightthickness=0, bd=0)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.inner = tk.Frame(self._canvas, bg=bg, bd=0, highlightthickness=0)
        self._win = self._canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.inner.bind("<Configure>", self._on_inner)
        self._canvas.bind("<Configure>", self._on_canvas)
        self._bar.bind("<B1-Motion>", self._drag)
        self._bar.bind("<ButtonPress-1>", self._drag)
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")

    def _on_inner(self, _e=None) -> None:
        req = self.inner.winfo_reqheight()
        view = self._canvas.winfo_height()
        # min-h-screen: el contenido con expand ocupa al menos el alto visible.
        self._canvas.itemconfigure(self._win, height=max(req, view))
        self._canvas.configure(scrollregion=(0, 0, self.inner.winfo_reqwidth(),
                                             max(req, view)))
        self._sync_bar()

    def _on_canvas(self, e) -> None:
        self._canvas.itemconfigure(self._win, width=e.width)
        self._on_inner()

    def _overflow(self) -> bool:
        return self.inner.winfo_reqheight() > self._canvas.winfo_height() + 1

    def _sync_bar(self) -> None:
        if self._overflow():
            if not self._bar.winfo_ismapped():
                self._bar.place(relx=1.0, x=-3, y=0, relheight=1.0, anchor=tk.NE)
        else:
            self._canvas.yview_moveto(0)
            if self._bar.winfo_ismapped():
                self._bar.place_forget()
            return
        top, bottom = self._canvas.yview()
        h = self._bar.winfo_height()
        self._bar.delete("all")
        round_rect(self._bar, 0, top * h, 6, bottom * h, 3, fill=BORDER)

    def _drag(self, e) -> None:
        h = max(self._bar.winfo_height(), 1)
        top, bottom = self._canvas.yview()
        self._canvas.yview_moveto(max(0.0, e.y / h - (bottom - top) / 2))
        self._sync_bar()

    def _on_wheel(self, e) -> None:
        if not self.winfo_ismapped() or not self._overflow():
            return
        try:
            widget = self.winfo_containing(e.x_root, e.y_root)
        except (tk.TclError, KeyError):
            return
        while widget is not None and widget is not self:
            if getattr(widget, "_hp_own_wheel", False):
                return
            widget = widget.master
        if widget is None:
            return
        self._canvas.yview_scroll(int(-e.delta), "units")
        self._sync_bar()

    def scroll_to(self, fraction: float) -> None:
        self._canvas.yview_moveto(fraction)
        self._sync_bar()
