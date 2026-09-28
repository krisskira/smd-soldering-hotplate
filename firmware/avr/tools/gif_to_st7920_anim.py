#!/usr/bin/env python3
"""
GIF (o secuencia de frames) → C PROGMEM para animaciones ST7920 (frame 0 + diffs).

Uso:
  python3 tools/gif_to_st7920_anim.py ../../icons/source/icons8-temperature.gif \\
      -o icons/animated/temperature.c --name temperature --size 32

Requisitos: Pillow (`pip install Pillow`).

Formato de salida (compatible con st7920_animation_t):
  - NAME_frame_0[]           frame completo en PROGMEM
  - NAME_diff_N_offsets[]    offsets de bytes que cambian (frame N)
  - NAME_diff_N_values[]     valores nuevos
  - NAME_diff_offsets[]      array de punteros a offsets (índice 0 = frame 1)
  - NAME_diff_values[]       array de punteros a valores
  - NAME_diff_counts[]       conteo por frame
  - macros NAME_FRAME_* / NAME_BYTES_PER_*
"""

from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys


def _require_pillow():
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.stderr.write("Falta Pillow. Instala con: pip install Pillow\n")
        sys.exit(1)


def gif_frames(path: pathlib.Path, size: int):
    from PIL import Image

    im = Image.open(path)
    frames = []
    try:
        while True:
            frame = im.convert("L").resize((size, size), Image.Resampling.NEAREST)
            # 1-bit: umbral
            bw = frame.point(lambda p: 255 if p >= 128 else 0, mode="1")
            frames.append(bw)
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    if not frames:
        raise SystemExit(f"Sin frames en {path}")
    return frames


def pack_frame(img) -> bytes:
    """Filas MSB-izquierda, (w+7)//8 bytes por fila."""
    w, h = img.size
    bpr = (w + 7) // 8
    out = bytearray(bpr * h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if px[x, y]:  # blanco = bit 1 (píxel encendido en ST7920 típico)
                out[y * bpr + (x >> 3)] |= 0x80 >> (x & 7)
    return bytes(out)


def diffs(prev: bytes, cur: bytes):
    offs, vals = [], []
    for i, (a, b) in enumerate(zip(prev, cur)):
        if a != b:
            offs.append(i)
            vals.append(b)
    return offs, vals


def emit_c(name: str, frames_bytes: list[bytes], size: int, src: str) -> str:
    bpr = (size + 7) // 8
    bpf = bpr * size
    n = len(frames_bytes)
    upper = name.upper()
    lines = []
    lines.append(f"// Auto-generated from {src}")
    lines.append(f"// Generated: {dt.datetime.now().isoformat(timespec='milliseconds')}")
    lines.append("// Modo DIFF: frame 0 completo + solo bytes que cambiaron. Formato ST7920.")
    lines.append("// STORE_IN_FLASH: Arduino=PROGMEM; C estándar=PROGMEM vacío.")
    lines.append("")
    lines.append("#include <stdint.h>")
    lines.append("")
    lines.append("#ifdef __AVR__")
    lines.append("  #include <avr/pgmspace.h>")
    lines.append("#else")
    lines.append("  #define PROGMEM")
    lines.append("  #define pgm_read_byte(addr)  (*(const uint8_t *)(addr))")
    lines.append("  #define pgm_read_word(addr) (*(const uint16_t *)(addr))")
    lines.append("#endif")
    lines.append("")
    lines.append(f"#define {upper}_FRAME_WIDTH   {size}")
    lines.append(f"#define {upper}_FRAME_HEIGHT  {size}")
    lines.append(f"#define {upper}_BYTES_PER_ROW (({upper}_FRAME_WIDTH + 7) / 8)")
    lines.append(f"#define {upper}_FRAME_COUNT   {n}")
    lines.append(f"#define {upper}_BYTES_PER_FRAME {bpf}")
    lines.append("")
    lines.append(f"const uint8_t {name}_frame_0[] PROGMEM = {{")
    f0 = frames_bytes[0]
    for i in range(0, len(f0), 16):
        chunk = ", ".join(f"0x{b:02X}" for b in f0[i : i + 16])
        lines.append(f"    {chunk},")
    lines.append("};")
    lines.append("")

    off_names, val_names, counts = [], [], []
    buf = bytearray(f0)
    for fi in range(1, n):
        offs, vals = diffs(bytes(buf), frames_bytes[fi])
        for o, v in zip(offs, vals):
            buf[o] = v
        counts.append(len(offs))
        on = f"{name}_diff_{fi}_offsets"
        vn = f"{name}_diff_{fi}_values"
        off_names.append(on)
        val_names.append(vn)
        lines.append(f"// Frame {fi} diff: {len(offs)} bytes")
        lines.append(f"const uint16_t {name}_diff_{fi}_count = {len(offs)};")
        if offs:
            lines.append(f"const uint16_t {on}[] PROGMEM = {{")
            for i in range(0, len(offs), 12):
                chunk = ", ".join(str(x) for x in offs[i : i + 12])
                lines.append(f"    {chunk},")
            lines.append("};")
            lines.append(f"const uint8_t {vn}[] PROGMEM = {{")
            for i in range(0, len(vals), 12):
                chunk = ", ".join(f"0x{b:02X}" for b in vals[i : i + 12])
                lines.append(f"    {chunk},")
            lines.append("};")
        else:
            lines.append(f"const uint16_t {on}[] PROGMEM = {{}};")
            lines.append(f"const uint8_t {vn}[] PROGMEM = {{}};")
        lines.append("")

    lines.append(f"const uint16_t* const {name}_diff_offsets[] PROGMEM = {{")
    lines.append("    " + ",\n    ".join(off_names))
    lines.append("};")
    lines.append(f"const uint8_t* const {name}_diff_values[] PROGMEM = {{")
    lines.append("    " + ",\n    ".join(val_names))
    lines.append("};")
    lines.append(
        f"const uint16_t {name}_diff_counts[] PROGMEM = {{ "
        + ", ".join(str(c) for c in counts)
        + " }};"
    )
    lines.append("")
    lines.append(f"uint16_t {name}_frame_count = {n};")
    lines.append(f"uint16_t {name}_frame_width = {size};")
    lines.append(f"uint16_t {name}_frame_height = {size};")
    lines.append(f"uint16_t {name}_bytes_per_frame = {bpf};")
    lines.append("")
    return "\n".join(lines)


def main():
    _require_pillow()
    ap = argparse.ArgumentParser(description="GIF → animación ST7920 (frame0 + diffs)")
    ap.add_argument("gif", type=pathlib.Path, help="GIF de origen")
    ap.add_argument("-o", "--output", type=pathlib.Path, required=True)
    ap.add_argument("--name", required=True, help="Prefijo C (p.ej. temperature)")
    ap.add_argument("--size", type=int, default=32, help="Lado en píxeles (cuadrado)")
    args = ap.parse_args()

    frames = gif_frames(args.gif, args.size)
    packed = [pack_frame(f) for f in frames]
    text = emit_c(args.name, packed, args.size, args.gif.name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)
    print(f"Wrote {args.output} ({len(packed)} frames, {args.size}x{args.size})")


if __name__ == "__main__":
    main()
