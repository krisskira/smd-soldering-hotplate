#!/usr/bin/env python3
"""PBM 128×64 (P1) → PNG ampliado con aspecto de LCD. Solo biblioteca estándar."""

from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

SCALE = 5
BORDER = 12
OFF = (0xDD, 0xE5, 0xD0)  # fondo del LCD
ON = (0x1E, 0x28, 0x1C)   # píxel encendido
FRAME = (0x3A, 0x3F, 0x45)


def read_pbm(path: Path) -> list[list[int]]:
    toks = path.read_text().split()
    if toks[0] != "P1":
        raise ValueError(f"{path}: no es P1")
    w, h = int(toks[1]), int(toks[2])
    bits = "".join(toks[3:])
    return [[int(bits[y * w + x]) for x in range(w)] for y in range(h)]


def write_png(path: Path, pix: list[list[int]]) -> None:
    h, w = len(pix), len(pix[0])
    ow, oh = w * SCALE + 2 * BORDER, h * SCALE + 2 * BORDER
    raw = bytearray()
    for oy in range(oh):
        raw.append(0)
        for ox in range(ow):
            x, y = (ox - BORDER) // SCALE, (oy - BORDER) // SCALE
            if not (0 <= ox - BORDER < w * SCALE and 0 <= oy - BORDER < h * SCALE):
                raw += bytes(FRAME)
            else:
                raw += bytes(ON if pix[y][x] else OFF)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    path.write_bytes(png)


def main() -> None:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for pbm in sorted(src.glob("*.pbm")):
        write_png(dst / (pbm.stem + ".png"), read_pbm(pbm))
        print(dst / (pbm.stem + ".png"))


if __name__ == "__main__":
    main()
