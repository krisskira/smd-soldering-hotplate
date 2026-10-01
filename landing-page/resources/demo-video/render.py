#!/usr/bin/env python3
"""Video demo de HotPlate: reproduce una traza HEAT real con el HotPanel real.

La temperatura, la consigna, la potencia y las fases salen del CSV exportado
por HotPlate Studio. Cada fotograma del LCD lo dibuja build/replay, que enlaza
home_view.c del firmware. Pillow compone LCD + gráfica y ffmpeg codifica.

    python render.py [--csv RUTA] [--out DIR]
"""

from __future__ import annotations

import argparse
import bisect
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_CSV = REPO / "docs/heat-results/hotplate_heat_trace-4.csv"
DEFAULT_OUT = HERE.parents[1] / "public/media"

W, H, FPS, SS = 1280, 720, 30, 2  # SS: supersampling para líneas suaves

# El CSV empieza con el precalentado del firmware anterior. El firmware actual
# arranca directo en la rampa 1, así que el demo empieza ahí.
START_PHASE = "Rampa 1"
HOLDS = {1: 30, 2: 60, 3: 30, 4: 30}
SPEED_HEAT, SPEED_COOL = 16, 120
INTRO_S, OUTRO_S = 1.2, 2.8

PH = {"IDLE": 0, "HOLD": 4, "RUN": 5, "COOLDOWN": 6, "ALARM": 7, "DONE": 8}

BG_TOP, BG_BOTTOM = (22, 16, 13), (10, 9, 9)
TEXT, MUTED, FAINT = (245, 239, 233), (168, 162, 158), (70, 62, 58)
TEMP, SETC, POWER = (255, 107, 61), (96, 165, 250), (52, 211, 153)
LCD_OFF, LCD_ON, BEZEL = (0xDD, 0xE5, 0xD0), (0x1E, 0x28, 0x1C), (35, 38, 43)
PHASE_COLORS = {
    "Rampa": (249, 115, 22),
    "Meseta": (251, 191, 36),
    "Alarma": (239, 68, 68),
    "Enfriando": (56, 189, 248),
    "Terminado": (163, 163, 163),
}


@dataclass
class Sample:
    t: float
    temp: float
    set: float | None
    power: float
    phase: str


def load(path: Path) -> list[Sample]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            values = list(row.values())
            rows.append(
                Sample(
                    t=float(values[0]),
                    temp=float(values[1]),
                    set=None if values[2] in ("", "nan") else float(values[2]),
                    power=float(values[3]),
                    phase=values[4],
                )
            )
    start = next(s.t for s in rows if s.phase == START_PHASE)
    trace = [s for s in rows if s.t >= start]
    for s in trace:
        s.t -= start
    return trace


def phase_kind(phase: str) -> tuple[str, int]:
    name, _, number = phase.partition(" ")
    return name, int(number) if number.isdigit() else 0


def segments(trace: list[Sample]) -> list[tuple[str, float, float]]:
    out: list[list] = []
    for s in trace:
        if not out or out[-1][0] != s.phase:
            out.append([s.phase, s.t, s.t])
        out[-1][2] = s.t
    for i in range(len(out) - 1):
        out[i][2] = out[i + 1][1]
    return [tuple(x) for x in out]


def schedule(trace: list[Sample]) -> list[tuple[float | None, int]]:
    """(tiempo de traza o None para reposo, velocidad) por fotograma."""
    cool = next(s.t for s in trace if s.phase == "Enfriando")
    end = trace[-1].t
    frames: list[tuple[float | None, int]] = [(None, SPEED_HEAT)] * int(INTRO_S * FPS)
    n = int(cool / SPEED_HEAT * FPS)
    frames += [(cool * i / n, SPEED_HEAT) for i in range(n)]
    n = int((end - cool) / SPEED_COOL * FPS)
    frames += [(cool + (end - cool) * i / n, SPEED_COOL) for i in range(n + 1)]
    frames += [(end, SPEED_COOL)] * int(OUTRO_S * FPS)
    return frames


class Trace:
    def __init__(self, trace: list[Sample]):
        self.samples = trace
        self.times = [s.t for s in trace]

    def at(self, t: float) -> tuple[Sample, float, int]:
        i = max(0, bisect.bisect_right(self.times, t) - 1)
        a = self.samples[i]
        b = self.samples[min(i + 1, len(self.samples) - 1)]
        k = 0.0 if b.t == a.t else (t - a.t) / (b.t - a.t)
        return a, a.temp + (b.temp - a.temp) * k, i

    def phase_start(self, i: int) -> float:
        phase = self.samples[i].phase
        while i > 0 and self.samples[i - 1].phase == phase:
            i -= 1
        return self.samples[i].t


def lcd_state(tr: Trace, t: float | None) -> str:
    if t is None:
        s = tr.samples[0]
        return f"{PH['IDLE']} {round(s.temp * 10)} 0 0 0 0"
    sample, temp, i = tr.at(t)
    kind, n = phase_kind(sample.phase)
    ramp = max(n - 1, 0) if n else 3
    set_c = int(sample.set) if sample.set is not None else 130
    if kind == "Rampa":
        phase, remain = PH["RUN"], HOLDS[n]
    elif kind == "Meseta":
        phase, remain = PH["HOLD"], max(0, round(HOLDS[n] - (t - tr.phase_start(i))))
    elif kind == "Alarma":
        phase, remain = PH["ALARM"], 0
    elif kind == "Enfriando":
        phase, remain = PH["COOLDOWN"], 0
    else:
        phase, remain = PH["DONE"], 0
    return f"{phase} {round(temp * 10)} {ramp} {set_c} {remain} {int(t)}"


def render_lcd(lines: list[str]) -> list[Image.Image]:
    replay = HERE / "build/replay"
    raw = subprocess.run([str(replay)], input="\n".join(lines).encode(), capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 64, 128)
    palette = np.array([LCD_OFF, LCD_ON], dtype=np.uint8)
    cache: dict[bytes, Image.Image] = {}
    out = []
    for fb in frames:
        key = fb.tobytes()
        if key not in cache:
            cache[key] = Image.fromarray(palette[fb]).resize((128 * 4 * SS, 64 * 4 * SS), Image.NEAREST)
        out.append(cache[key])
    return out


def fonts() -> dict[str, ImageFont.FreeTypeFont]:
    regular, semi = HERE / "fonts/Poppins-Regular.ttf", HERE / "fonts/Poppins-SemiBold.ttf"
    size = lambda path, px: ImageFont.truetype(str(path), px * SS)  # noqa: E731
    return {
        "title": size(semi, 30),
        "sub": size(regular, 16),
        "label": size(regular, 14),
        "value": size(semi, 24),
        "small": size(regular, 12),
        "badge": size(semi, 15),
        "phase": size(semi, 12),
    }


def mmss(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def background() -> Image.Image:
    y = np.linspace(0, 1, H * SS)[:, None]
    x = np.linspace(0, 1, W * SS)[None, :]
    top, bottom = np.array(BG_TOP), np.array(BG_BOTTOM)
    base = top[None, None, :] * (1 - y[..., None]) + bottom[None, None, :] * y[..., None]
    glow = np.exp(-(((x - 0.15) ** 2) / 0.05 + ((y - 0.1) ** 2) / 0.08))[..., None] * np.array([70, 28, 8])
    img = np.clip(base + glow, 0, 255).astype(np.uint8)
    return Image.fromarray(np.broadcast_to(img, (H * SS, W * SS, 3)).copy())


class Chart:
    X0, X1, Y0, Y1 = 640, 1232, 150, 560
    TMIN, TMAX = 40, 140

    def __init__(self, tr: Trace, f):
        self.tr, self.f = tr, f

    def x(self, t: float, tmax: float) -> float:
        return (self.X0 + (self.X1 - self.X0) * t / tmax) * SS

    def y(self, temp: float) -> float:
        return (self.Y1 - (self.Y1 - self.Y0) * (temp - self.TMIN) / (self.TMAX - self.TMIN)) * SS

    def yp(self, power: float) -> float:
        return (self.Y1 - (self.Y1 - self.Y0) * power / 100) * SS

    def draw(self, d: ImageDraw.ImageDraw, t: float | None):
        f = self.f
        tmax = max(480.0, (t or 0) * 1.04)
        for temp in range(self.TMIN, self.TMAX + 1, 20):
            yy = self.y(temp)
            d.line([(self.X0 * SS, yy), (self.X1 * SS, yy)], fill=FAINT, width=SS)
            d.text((self.X0 * SS - 12 * SS, yy), f"{temp}", font=f["small"], fill=MUTED, anchor="rm")
        d.text((self.X0 * SS - 12 * SS, (self.Y0 - 24) * SS), "°C", font=f["small"], fill=MUTED, anchor="rm")
        d.text((self.X1 * SS, (self.Y0 - 24) * SS), "potencia %", font=f["small"], fill=POWER, anchor="rm")
        step = 60 if tmax <= 600 else 300
        for s in range(0, int(tmax) + 1, step):
            xx = self.x(s, tmax)
            d.line([(xx, self.Y1 * SS), (xx, (self.Y1 + 6) * SS)], fill=MUTED, width=SS)
            d.text((xx, (self.Y1 + 12) * SS), mmss(s), font=f["small"], fill=MUTED, anchor="mt")
        d.line([(self.X0 * SS, self.Y1 * SS), (self.X1 * SS, self.Y1 * SS)], fill=MUTED, width=SS)

        if t is None:
            return
        _, temp_now, i = self.tr.at(t)
        pts = self.tr.samples[: i + 1]

        for phase, a, b in segments(self.tr.samples):
            if a > t or not phase.startswith(("Rampa", "Meseta", "Alarma", "Enfriando")):
                continue
            xa = self.x(a, tmax)
            d.line([(xa, self.Y0 * SS), (xa, self.Y1 * SS)], fill=(60, 52, 48), width=SS)

        power = [(self.x(s.t, tmax), self.yp(s.power)) for s in pts]
        if len(power) > 1:
            d.line(power, fill=(28, 92, 72), width=SS)

        runs: list[list] = []
        for s in pts:
            if s.set is None:
                continue
            if runs and runs[-1][0] == s.set:
                runs[-1][2] = s.t
            else:
                runs.append([s.set, s.t, s.t])
        for set_c, a, b in runs:
            y = self.y(set_c)
            xa, xb = self.x(a, tmax), self.x(min(t, b + 1), tmax)
            dash, gap = 9 * SS, 6 * SS
            while xa < xb:
                d.line([(xa, y), (min(xa + dash, xb), y)], fill=SETC, width=2 * SS)
                xa += dash + gap

        line = [(self.x(s.t, tmax), self.y(s.temp)) for s in pts] + [(self.x(t, tmax), self.y(temp_now))]
        if len(line) > 1:
            d.line(line, fill=(120, 45, 25), width=10 * SS, joint="curve")
            d.line(line, fill=TEMP, width=4 * SS, joint="curve")
        cx, cy = line[-1]
        r = 7 * SS
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEMP, outline=TEXT, width=2 * SS)
        right = cx > (self.X1 - 100) * SS
        d.text((cx + (-12 if right else 12) * SS, cy - 12 * SS), f"{temp_now:.1f} °C", font=f["badge"], fill=TEXT, anchor="rs" if right else "ls")


def phase_bar(d: ImageDraw.ImageDraw, tr: Trace, t: float | None, f):
    x0, x1, y0, y1 = 48, 1232, 628, 656
    end = tr.samples[-1].t
    d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=8 * SS, fill=(32, 28, 26))
    if t is None:
        return
    for phase, a, b in segments(tr.samples):
        if a > t:
            break
        kind, n = phase_kind(phase)
        color = PHASE_COLORS.get(kind, MUTED)
        xa = x0 + (x1 - x0) * a / end
        xb = x0 + (x1 - x0) * min(b, t) / end
        if xb - xa < 1:
            continue
        d.rectangle([xa * SS, y0 * SS, xb * SS, y1 * SS], fill=color)
        label = {"Rampa": f"R{n}", "Meseta": f"M{n}", "Alarma": "ALM", "Enfriando": "Enfriamiento con aire", "Terminado": ""}[kind]
        if label and (xb - xa) * SS > d.textlength(label, font=f["phase"]) + 8 * SS:
            d.text(((xa + xb) / 2 * SS, (y0 + y1) / 2 * SS), label, font=f["phase"], fill=(20, 16, 14), anchor="mm")
    d.text((x0 * SS, (y1 + 14) * SS), "Rampa: sube a la consigna  ·  Meseta: sostiene el tiempo del escalón  ·  ALM: aviso de fin", font=f["small"], fill=MUTED, anchor="lt")


def card(d, x, y, w, label, value, f, bar: float | None = None, color=TEXT):
    d.rounded_rectangle([x * SS, y * SS, (x + w) * SS, (y + 86) * SS], radius=14 * SS, fill=(30, 26, 24), outline=(52, 46, 42), width=SS)
    d.text(((x + 16) * SS, (y + 14) * SS), label, font=f["label"], fill=MUTED, anchor="lt")
    d.text(((x + 16) * SS, (y + 38) * SS), value, font=f["value"], fill=color, anchor="lt")
    if bar is not None:
        bx0, bx1, by = x + 16, x + w - 16, y + 74
        d.rounded_rectangle([bx0 * SS, by * SS, bx1 * SS, (by + 5) * SS], radius=3 * SS, fill=(55, 48, 44))
        if bar > 0:
            d.rounded_rectangle([bx0 * SS, by * SS, (bx0 + (bx1 - bx0) * bar / 100) * SS, (by + 5) * SS], radius=3 * SS, fill=POWER)


def compose(bg, lcd, tr: Trace, chart: Chart, t, speed, f) -> Image.Image:
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.text((48 * SS, 40 * SS), "HotPlate · ciclo HEAT real", font=f["title"], fill=TEXT, anchor="lt")
    d.text((48 * SS, 84 * SS), "Traza del banco (28-09-2026) · la pantalla la dibuja home_view.c del firmware", font=f["sub"], fill=MUTED, anchor="lt")

    badge = f"×{speed}"
    bw = d.textlength(badge, font=f["badge"]) / SS + 28
    d.rounded_rectangle([(1232 - bw) * SS, 42 * SS, 1232 * SS, 74 * SS], radius=16 * SS, fill=(62, 34, 20), outline=TEMP, width=SS)
    d.text(((1232 - bw / 2) * SS, 58 * SS), badge, font=f["badge"], fill=TEMP, anchor="mm")
    d.text(((1232 - bw - 14) * SS, 58 * SS), f"t = {mmss(t or 0)}", font=f["sub"], fill=MUTED, anchor="rm")

    lx, ly = 48, 150
    d.rounded_rectangle([lx * SS, ly * SS, (lx + 544) * SS, (ly + 288) * SS], radius=22 * SS, fill=BEZEL, outline=(70, 74, 80), width=SS)
    img.paste(lcd, ((lx + 16) * SS, (ly + 16) * SS))

    if t is None:
        sample, temp = tr.samples[0], tr.samples[0].temp
    else:
        sample, temp, _ = tr.at(t)
    card(d, 48, 474, 172, "Temperatura", f"{temp:.1f} °C", f, color=TEMP)
    card(d, 234, 474, 172, "Consigna", f"{sample.set:.0f} °C" if sample.set and t is not None else "—", f, color=SETC)
    card(d, 420, 474, 172, "Calentador", f"{sample.power:.0f} %" if t is not None else "0 %", f, bar=sample.power if t is not None else 0, color=POWER)

    chart.draw(d, t)
    phase_bar(d, tr, t, f)
    return img.resize((W, H), Image.LANCZOS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    tr = Trace(load(args.csv))
    frames = schedule(tr.samples)
    lcds = render_lcd([lcd_state(tr, t) for t, _ in frames])
    f = fonts()
    bg = background()
    chart = Chart(tr, f)

    args.out.mkdir(parents=True, exist_ok=True)
    mp4 = args.out / "hotplate-demo.mp4"
    poster_at = next(i for i, (t, _) in enumerate(frames) if t is not None and t >= 380)

    ffmpeg = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE,
    )
    for i, ((t, speed), lcd) in enumerate(zip(frames, lcds)):
        frame = compose(bg, lcd, tr, chart, t, speed, f)
        if i == poster_at:
            frame.save(args.out / "hotplate-demo-poster.jpg", quality=86)
        ffmpeg.stdin.write(frame.tobytes())
        if i % 150 == 0:
            print(f"{i}/{len(frames)}", flush=True)
    ffmpeg.stdin.close()
    ffmpeg.wait()
    print(f"{mp4}\n{args.out / 'hotplate-demo-poster.jpg'} · {len(frames) / FPS:.1f} s")


if __name__ == "__main__":
    main()
