#!/usr/bin/env python3
"""Arma los MP4 del tutorial y el promo: subtítulos quemados, sin voz.

Fuentes: fotos y clips en ~/Downloads/fotos-hotplate, pantallas de la landing
y la música CC0 del kit de edición. Salida en tutorials/videos y referencias/.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PHOTOS = Path("/Users/david/Downloads/fotos-hotplate")
MEDIA = REPO / "landing-page" / "public" / "media"
LIB = Path("/Users/david/.agents/skills/editing-videos/library")
WORK = Path("/tmp/hp-edit")
OUT = ROOT / "videos"
REF = ROOT / "referencias"
AUDIO = ROOT / "audio"

W, H, FPS = 1920, 1080, 30
BG = (20, 15, 12)
INK = (251, 245, 239)
AMBER = (245, 165, 36)
ORANGE = (217, 72, 26)
RED = (226, 59, 59)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

MUSIC_PROMO = LIB / "music" / "music-inspiring-orchestral.mp3"
MUSIC_TUTORIAL = LIB / "music" / "music-ambient-piano.mp3"
WHOOSH = LIB / "sfx" / "whoosh-soft.wav"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, text=True, capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-2000:]
        raise RuntimeError(f"falló: {' '.join(args[:8])}\n{tail}")
    return proc


def ass_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def check_caption(lines: list[str], dur: float) -> None:
    if len(lines) > 2:
        raise ValueError(f"más de 2 líneas: {lines}")
    for line in lines:
        if len(line) > 42:
            raise ValueError(f"{len(line)} caracteres: {line}")
    words = sum(len(line.split()) for line in lines)
    need = max(1.5, words * 0.33 + 0.5)
    if dur < need:
        raise ValueError(f"plano de {dur:.2f}s corto para «{lines}» (hace falta {need:.2f}s)")


def stripe(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle((0, 1062, 640, 1080), fill=ORANGE)
    draw.rectangle((640, 1062, 1280, 1080), fill=AMBER)
    draw.rectangle((1280, 1062, 1920, 1080), fill=RED)


def title_card(path: Path, kicker: str, title: str) -> None:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    stripe(draw)
    draw.text((140, 390), kicker.upper(), font=ImageFont.truetype(FONT, 32), fill=AMBER)
    draw.text((140, 450), title, font=ImageFont.truetype(FONT_B, 78), fill=INK)
    im.save(path)


def end_card(path: Path, hero: Path) -> None:
    base = Image.open(hero).convert("RGB")
    base = ImageOps.fit(base, (W, H), Image.Resampling.LANCZOS)
    shade = Image.new("RGB", (W, H), (12, 8, 6))
    im = Image.blend(base, shade, 0.28)
    draw = ImageDraw.Draw(im)
    stripe(draw)
    im.save(path, quality=92)


def lcd_card(src: Path, path: Path) -> None:
    im = Image.new("RGB", (W, H), BG)
    lcd = Image.open(src).convert("RGB")
    scale = 3 if lcd.width >= 400 else 6
    lcd = lcd.resize((lcd.width * scale, lcd.height * scale), Image.Resampling.NEAREST)
    pad = 36
    bezel = Image.new("RGB", (lcd.width + pad * 2, lcd.height + pad * 2), (32, 36, 40))
    bezel.paste(lcd, (pad, pad))
    bezel.thumbnail((1500, 720), Image.Resampling.NEAREST)
    x = (W - bezel.width) // 2
    y = (H - 150 - bezel.height) // 2
    im.paste(bezel, (x, y))
    im.save(path)


def ui_card(src: Path, path: Path) -> None:
    shot = Image.open(src).convert("RGB")
    bg = ImageOps.fit(shot, (W, H), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(26))
    bg = ImageEnhance.Brightness(bg).enhance(0.38)
    shot.thumbnail((1480, 760), Image.Resampling.LANCZOS)
    x = (W - shot.width) // 2
    y = 28 + max(0, (860 - shot.height) // 2)
    frame = Image.new("RGB", (shot.width + 16, shot.height + 16), (255, 250, 246))
    frame.paste(shot, (8, 8))
    bg.paste(frame, (x - 8, y - 8))
    bg.save(path, quality=92)


def cover_still(src: Path, path: Path) -> None:
    im = ImageOps.fit(Image.open(src).convert("RGB"), (W, H), Image.Resampling.LANCZOS)
    im.save(path, quality=92)


def contain_still(src: Path, path: Path) -> None:
    shot = Image.open(src).convert("RGB")
    bg = ImageOps.fit(shot, (W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(22))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    shot.thumbnail((1760, 920), Image.Resampling.LANCZOS)
    x = (W - shot.width) // 2
    y = (H - shot.height) // 2 - 20
    bg.paste(shot, (x, y))
    bg.save(path, quality=92)


def arch_card(path: Path) -> None:
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)
    stripe(draw)
    draw.text((140, 180), "CÓMO ESTÁ ARMADO STUDIO", font=ImageFont.truetype(FONT, 32), fill=AMBER)
    boxes = [
        ("Vistas", "Dibujan la ventana.\nCada botón pide\nuna acción."),
        ("Controlador", "Una orden AT\nen vuelo. Espera\nOK o ERROR."),
        ("Puerto serie", "19200 8N1.\n$HP cada segundo\nen modo USB."),
    ]
    font_h = ImageFont.truetype(FONT_B, 40)
    font_b = ImageFont.truetype(FONT, 32)
    for i, (title, body) in enumerate(boxes):
        x = 140 + i * 580
        draw.rounded_rectangle((x, 300, x + 520, 760), radius=18, fill=(36, 26, 22))
        draw.rectangle((x, 300, x + 12, 760), fill=ORANGE if i == 0 else AMBER if i == 1 else RED)
        draw.text((x + 40, 340), title, font=font_h, fill=INK)
        draw.multiline_text((x + 40, 430), body, font=font_b, fill=(220, 206, 196), spacing=10)
    im.save(path)


def save_ref(src: Path, dest: Path, max_w: int = 1600) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    im.thumbnail((max_w, max_w), Image.Resampling.LANCZOS)
    im.save(dest, quality=84, optimize=True)


def grab(src: Path, second: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-ss", f"{second:.3f}", "-i", str(src),
        "-frames:v", "1", "-vf", "scale=1600:-2", str(dest),
        "-hide_banner", "-loglevel", "error",
    ])


def kenburns(src: Path, dst: Path, dur: float, motion: str) -> None:
    n = int(round(dur * FPS))
    if motion == "in":
        z, x, y = "min(1+on*0.00065,1.08)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "out":
        z, x, y = "max(1.0,1.08-on*0.00065)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "right":
        z, x, y = "1.06", "(iw-iw/zoom)*on/max(1,on)", "ih/2-(ih/zoom/2)"
        x = f"(iw-iw/zoom)*on/{max(n - 1, 1)}"
    else:
        z, x, y = "1.06", f"(iw-iw/zoom)*(1-on/{max(n - 1, 1)})", "ih/2-(ih/zoom/2)"
    vf = (
        "scale=2304:1296:force_original_aspect_ratio=increase,crop=2304:1296,"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps={FPS},setsar=1,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(src), "-vf", vf,
        "-frames:v", str(n), "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-an", str(dst),
        "-hide_banner", "-loglevel", "error",
    ])


def clip(src: Path, dst: Path, start: float, dur: float) -> None:
    vf = (
        "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        f"fps={FPS},setsar=1,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
        "-vf", vf, "-an", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", str(dst),
        "-hide_banner", "-loglevel", "error",
    ])


def concat(parts: list[Path], dst: Path) -> None:
    listing = dst.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(dst), "-hide_banner", "-loglevel", "error",
    ])


def write_captions(cues: list[tuple[float, float, list[str]]], ass: Path, srt: Path) -> None:
    events = []
    blocks = []
    for i, (a, b, lines) in enumerate(cues, start=1):
        events.append(
            f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Narr,,0,0,0,,{r'\N'.join(lines)}"
        )
        blocks.append(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n" + "\n".join(lines) + "\n")
    ass.write_text(
        "\n".join([
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Narr,Arial,48,&H00EFF5FB,&H000000FF,&H000C0F14,&H64000000,0,0,0,0,100,100,0,0,1,3,0,2,140,140,72,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
            *events,
            "",
        ]),
        encoding="utf-8",
    )
    srt.write_text("\n".join(blocks) + "\n", encoding="utf-8")


def loudnorm_music(src: Path, dur: float, dst: Path) -> None:
    trimmed = dst.with_name(dst.stem + "-trim.wav")
    run([
        "ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.3f}",
        "-af", "afade=t=in:st=0:d=0.6,afade=t=out:st=" + f"{max(dur - 1.4, 0):.3f}" + ":d=1.3",
        "-ar", "48000", "-ac", "2", str(trimmed),
        "-hide_banner", "-loglevel", "error",
    ])
    probe = subprocess.run(
        ["ffmpeg", "-i", str(trimmed), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        text=True, capture_output=True,
    )
    raw = probe.stderr
    data = json.loads(raw[raw.rfind("{") : raw.rfind("}") + 1])
    af = (
        "loudnorm=I=-14:TP=-1.5:LRA=11:"
        f"measured_I={data['input_i']}:measured_TP={data['input_tp']}:"
        f"measured_LRA={data['input_lra']}:measured_thresh={data['input_thresh']}:"
        f"offset={data['target_offset']}:linear=true"
    )
    run([
        "ffmpeg", "-y", "-i", str(trimmed), "-af", af,
        "-ar", "48000", "-ac", "2", str(dst),
        "-hide_banner", "-loglevel", "error",
    ])
    trimmed.unlink(missing_ok=True)


def render_sub_png(lines: list[str], path: Path) -> None:
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bar = Image.new("RGBA", (W, 132), (12, 8, 6, 188))
    im.paste(bar, (0, H - 132), bar)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 46)
    line_h = 58
    y0 = H - 132 + (132 - line_h * len(lines)) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        y = y0 + i * line_h
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            draw.text((x + dx, y + dy), line, font=font, fill=(20, 15, 12, 255))
        draw.text((x, y), line, font=font, fill=(251, 245, 239, 255))
    im.save(path)


def finish(video: Path, cues: list[tuple[float, float, list[str]]], music: Path, dest: Path, whoosh: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dur = cues[-1][1] + 0.08
    srt = dest.with_suffix(".srt")
    write_captions(cues, dest.with_suffix(".ass"), srt)
    bed = dest.with_name(dest.stem + "-bed.wav")
    loudnorm_music(music, dur, bed)
    subdir = WORK / "subs" / dest.stem
    if subdir.exists():
        shutil.rmtree(subdir)
    subdir.mkdir(parents=True)
    pngs = []
    for i, (_, _, lines) in enumerate(cues):
        png = subdir / f"{i:02d}.png"
        render_sub_png(lines, png)
        pngs.append(png)
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(bed)]
    for png in pngs:
        cmd += ["-loop", "1", "-i", str(png)]
    chains = []
    prev = "0:v"
    for i, (a, b, _) in enumerate(cues):
        out = f"v{i}"
        chains.append(
            f"[{prev}][{i + 2}:v]overlay=0:0:format=auto:enable='between(t,{a:.3f},{b:.3f})'[{out}]"
        )
        prev = out
    if whoosh:
        cmd += ["-i", str(WHOOSH)]
        wx = 2 + len(pngs)
        chains.append(
            f"[{wx}:a]adelay=80|80,volume=0.4[fx];"
            "[1:a][fx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        )
        maps = ["-map", f"[{prev}]", "-map", "[a]"]
    else:
        maps = ["-map", f"[{prev}]", "-map", "1:a"]
    run([
        *cmd, "-filter_complex", ";".join(chains), *maps,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", "-shortest", str(dest),
        "-hide_banner", "-loglevel", "error",
    ])
    bed.unlink(missing_ok=True)
    dest.with_suffix(".ass").unlink(missing_ok=True)


def build_film(name: str, shots: list[dict], music: Path, whoosh: bool) -> None:
    folder = WORK / name
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    parts: list[Path] = []
    cues: list[tuple[float, float, list[str]]] = []
    clock = 0.0
    t0 = time.time()
    for i, shot in enumerate(shots):
        check_caption(shot["cap"], shot["dur"])
        seg = folder / f"{i:02d}.mp4"
        if shot["kind"] == "clip":
            clip(shot["src"], seg, shot["ss"], shot["dur"])
        else:
            kenburns(shot["src"], seg, shot["dur"], shot.get("motion", "in"))
        parts.append(seg)
        cues.append((clock + 0.08, clock + shot["dur"] - 0.08, shot["cap"]))
        clock += shot["dur"]
        print(f"  {name} {i + 1}/{len(shots)} {clock:.1f}s", flush=True)
    silent = folder / "silent.mp4"
    concat(parts, silent)
    finish(silent, cues, music, OUT / f"{name}.mp4", whoosh)
    print(f"{name}: {clock:.1f}s en {time.time() - t0:.0f}s → {OUT / (name + '.mp4')}", flush=True)


def prepare() -> dict[str, Path]:
    WORK.mkdir(parents=True, exist_ok=True)
    frames = WORK / "frames"
    frames.mkdir(exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    for src in (MUSIC_PROMO, MUSIC_TUTORIAL, WHOOSH):
        shutil.copy2(src, AUDIO / src.name)

    hero = MEDIA / "hero-producto.jpg"
    end_card(frames / "end-promo.png", hero)

    lcds = {
        "idle": MEDIA / "hotpanel-idle.png",
        "wait": MEDIA / "hotpanel-wait.png",
        "ramp": MEDIA / "hotpanel-ramp.png",
        "hold": MEDIA / "hotpanel-hold.png",
        "alarm": MEDIA / "hotpanel-alarm.png",
        "usb": MEDIA / "hotpanel-usb.png",
        "delay": MEDIA / "hotpanel-delay.png",
        "settings": MEDIA / "hotpanel-settings.png",
    }
    for key, src in lcds.items():
        lcd_card(src, frames / f"lcd-{key}.png")
        save_ref(src, REF / "03-firmware" / f"hotpanel-{key}.png")

    ui = {
        "heat": MEDIA / "studio-heat.webp",
        "autotune": MEDIA / "studio-autotune.webp",
        "settings": MEDIA / "studio-settings.webp",
        "connection": MEDIA / "studio-connection.webp",
    }
    for key, src in ui.items():
        png = frames / f"ui-src-{key}.png"
        run(["ffmpeg", "-y", "-i", str(src), "-frames:v", "1", str(png), "-hide_banner", "-loglevel", "error"])
        ui_card(png, frames / f"ui-{key}.png")
        save_ref(png, REF / "04-studio" / f"studio-{key}.jpg")

    arch_card(frames / "arch.png")
    title_card(frames / "t-pcb.png", "Tutorial  01", "Fabricar la PCB")
    title_card(frames / "t-3d.png", "Tutorial  02", "Modelar la carcasa")
    title_card(frames / "t-fw.png", "Tutorial  03", "El firmware")
    title_card(frames / "t-studio.png", "Tutorial  04", "HotPlate Studio")
    title_card(frames / "t-cal.png", "Tutorial  05", "Calibrar el equipo")

    photos = {
        "cad": PHOTOS / "631B320D-A635-40E2-9D51-FBA8F1878F00.jpg",
        "device": PHOTOS / "IMG_5725.jpeg",
        "front": PHOTOS / "IMG_5724.jpeg",
        "side": PHOTOS / "IMG_5723.jpeg",
        "posts": PHOTOS / "IMG_5721.jpeg",
        "traces": PHOTOS / "IMG_4602.jpeg",
        "board": PHOTOS / "IMG_4603.jpeg",
        "mill": PHOTOS / "IMG_4218.jpeg",
        "knob": PHOTOS / "2816DE32-93F3-488F-8843-60551075CC0D.jpg",
    }
    for key, src in photos.items():
        if key == "cad":
            contain_still(src, frames / f"{key}.png")
        else:
            cover_still(src, frames / f"{key}.png")

    save_ref(photos["cad"], REF / "02-modelado" / "modelo-y-equipo.jpg")
    save_ref(photos["device"], REF / "02-modelado" / "equipo-terminado.jpg")
    save_ref(photos["side"], REF / "02-modelado" / "lateral-impreso.jpg")
    save_ref(photos["posts"], REF / "02-modelado" / "placa-y-postes.jpg")
    save_ref(photos["knob"], REF / "02-modelado" / "perilla.jpg")
    save_ref(photos["front"], REF / "02-modelado" / "frente.jpg")
    save_ref(photos["traces"], REF / "01-pcb" / "pistas-fresadas.jpg")
    save_ref(photos["board"], REF / "01-pcb" / "placa-de-cobre.jpg")
    save_ref(photos["mill"], REF / "01-pcb" / "fresa-en-el-cobre.jpg")
    save_ref(hero, REF / "hero-producto.jpg")
    grab(PHOTOS / "IMG_4211.MOV", 8, REF / "01-pcb" / "cnc-trabajando.jpg")
    grab(PHOTOS / "IMG_4569.MOV", 12, REF / "01-pcb" / "revision-microscopio.jpg")
    (REF / "05-calibracion").mkdir(parents=True, exist_ok=True)
    shutil.copy2(REF / "04-studio" / "studio-settings.jpg", REF / "05-calibracion" / "ajustes.jpg")
    shutil.copy2(REF / "04-studio" / "studio-autotune.jpg", REF / "05-calibracion" / "autotune.jpg")
    shutil.copy2(REF / "04-studio" / "studio-heat.jpg", REF / "05-calibracion" / "ciclo-heat.jpg")
    shutil.copy2(REF / "04-studio" / "studio-connection.jpg", REF / "05-calibracion" / "conexion.jpg")
    return {
        "frames": frames,
        "hero": hero,
    }


def films(frames: Path) -> None:
    f = frames
    build_film("promo", [
        {"kind": "clip", "src": PHOTOS / "IMG_5730.MOV", "ss": 1.2, "dur": 6.0, "cap": ["Soldadura SMD, con perfil y control."]},
        {"kind": "still", "src": f / "lcd-ramp.png", "dur": 5.5, "motion": "in", "cap": ["Fase, consigna y tiempo, en la LCD."]},
        {"kind": "still", "src": f / "ui-heat.png", "dur": 6.0, "motion": "in", "cap": ["Studio dibuja la curva en vivo, a 1 Hz."]},
        {"kind": "clip", "src": PHOTOS / "IMG_4211.MOV", "ss": 8.0, "dur": 5.5, "cap": ["La PCB se fresa en cobre, en el taller."]},
        {"kind": "clip", "src": PHOTOS / "IMG_4569.MOV", "ss": 12.0, "dur": 5.5, "cap": ["Cada pista se revisa antes de armar."]},
        {"kind": "still", "src": f / "cad.png", "dur": 5.5, "motion": "out", "cap": ["La carcasa se modela en Fusion 360."]},
        {"kind": "still", "src": f / "ui-settings.png", "dur": 5.5, "motion": "right", "cap": ["Límites, bandas de meseta y el PI."]},
        {"kind": "clip", "src": PHOTOS / "IMG_5729.MOV", "ss": 1.0, "dur": 5.0, "cap": ["Hardware, firmware y software, juntos."]},
        {"kind": "still", "src": f / "end-promo.png", "dur": 5.0, "motion": "in", "cap": ["HotPlate. Abierto y repetible."]},
    ], MUSIC_PROMO, whoosh=False)

    build_film("01-pcb", [
        {"kind": "still", "src": f / "t-pcb.png", "dur": 4.2, "motion": "in", "cap": ["Del plano KiCad al cobre fresado."]},
        {"kind": "clip", "src": PHOTOS / "IMG_4211.MOV", "ss": 4.0, "dur": 6.5, "cap": ["Una fresa aísla las pistas en la placa."]},
        {"kind": "still", "src": f / "mill.png", "dur": 6.0, "motion": "in", "cap": ["El cobre sobrante se retira paso a paso."]},
        {"kind": "clip", "src": PHOTOS / "IMG_4211.MOV", "ss": 22.0, "dur": 6.0, "cap": ["La máquina recorre el contorno del plano."]},
        {"kind": "clip", "src": PHOTOS / "IMG_4569.MOV", "ss": 8.0, "dur": 6.5, "cap": ["El microscopio busca cortes y puentes."]},
        {"kind": "still", "src": f / "traces.png", "dur": 6.0, "motion": "right", "cap": ["Pads y pistas quedan en el cobre."]},
        {"kind": "still", "src": f / "board.png", "dur": 6.0, "motion": "out", "cap": ["Control y potencia, en la misma placa."]},
    ], MUSIC_TUTORIAL, whoosh=True)

    build_film("02-modelado-3d", [
        {"kind": "still", "src": f / "t-3d.png", "dur": 4.2, "motion": "in", "cap": ["La carcasa se diseña antes de imprimir."]},
        {"kind": "still", "src": f / "cad.png", "dur": 7.0, "motion": "in", "cap": ["Frente, perilla y ventana para la LCD."]},
        {"kind": "still", "src": f / "side.png", "dur": 6.0, "motion": "right", "cap": ["El lateral lleva el relieve de las pistas."]},
        {"kind": "still", "src": f / "posts.png", "dur": 6.0, "motion": "in", "cap": ["Cuatro postes separan la placa caliente."]},
        {"kind": "still", "src": f / "knob.png", "dur": 5.5, "motion": "in", "cap": ["La perilla se imprime aparte de la tapa."]},
        {"kind": "still", "src": f / "device.png", "dur": 6.5, "motion": "out", "cap": ["Tapa, base y perilla salen de Fusion 360."]},
    ], MUSIC_TUTORIAL, whoosh=True)

    build_film("03-firmware", [
        {"kind": "still", "src": f / "t-fw.png", "dur": 4.5, "motion": "in", "cap": ["C bare-metal en un ATmega16 a 8 MHz."]},
        {"kind": "still", "src": f / "lcd-idle.png", "dur": 4.8, "motion": "in", "cap": ["En reposo, el equipo espera el RUN."]},
        {"kind": "still", "src": f / "lcd-wait.png", "dur": 4.8, "motion": "in", "cap": ["La espera programada cuenta atrás."]},
        {"kind": "still", "src": f / "lcd-ramp.png", "dur": 5.2, "motion": "in", "cap": ["En RUN persigue la consigna del paso."]},
        {"kind": "still", "src": f / "lcd-hold.png", "dur": 5.0, "motion": "in", "cap": ["La meseta sostiene el tiempo marcado."]},
        {"kind": "still", "src": f / "lcd-alarm.png", "dur": 5.0, "motion": "in", "cap": ["Al terminar corta el calor y avisa."]},
        {"kind": "still", "src": f / "lcd-usb.png", "dur": 5.0, "motion": "in", "cap": ["En USB, Studio toma el mando."]},
        {"kind": "still", "src": f / "front.png", "dur": 5.5, "motion": "out", "cap": ["Pantalla y control caben en el mismo chip."]},
    ], MUSIC_TUTORIAL, whoosh=True)

    build_film("04-hotplate-studio", [
        {"kind": "still", "src": f / "t-studio.png", "dur": 4.5, "motion": "in", "cap": ["Una app de escritorio para el ciclo."]},
        {"kind": "still", "src": f / "ui-connection.png", "dur": 6.5, "motion": "in", "cap": ["Enlaza el puerto a 19200 y pasa a USB."]},
        {"kind": "still", "src": f / "ui-heat.png", "dur": 7.0, "motion": "right", "cap": ["Edita hasta cuatro escalones y lanza HEAT."]},
        {"kind": "still", "src": f / "arch.png", "dur": 6.5, "motion": "in", "cap": ["Una orden AT a la vez, y espera el OK."]},
        {"kind": "still", "src": f / "ui-settings.png", "dur": 6.5, "motion": "in", "cap": ["Lo de Ajustes se guarda en la EEPROM."]},
        {"kind": "still", "src": f / "device.png", "dur": 5.5, "motion": "out", "cap": ["El perfil queda guardado en el equipo."]},
    ], MUSIC_TUTORIAL, whoosh=True)

    build_film("05-calibracion", [
        {"kind": "still", "src": f / "t-cal.png", "dur": 4.5, "motion": "in", "cap": ["Calibrar es medir, no adivinar la curva."]},
        {"kind": "still", "src": f / "ui-connection.png", "dur": 6.0, "motion": "in", "cap": ["En línea, Studio lee los ajustes."]},
        {"kind": "still", "src": f / "ui-settings.png", "dur": 7.0, "motion": "right", "cap": ["Mínima, máxima, bandas y ganancias PI."]},
        {"kind": "still", "src": f / "ui-autotune.png", "dur": 7.0, "motion": "in", "cap": ["Oscila y guarda Kp y Ki solo al final."]},
        {"kind": "still", "src": f / "ui-heat.png", "dur": 7.0, "motion": "in", "cap": ["Un ciclo HEAT comprueba la curva real."]},
        {"kind": "still", "src": f / "front.png", "dur": 5.5, "motion": "out", "cap": ["Si el sensor falla, el calor no arranca."]},
    ], MUSIC_TUTORIAL, whoosh=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prepared = prepare()
    films(prepared["frames"])


if __name__ == "__main__":
    main()
