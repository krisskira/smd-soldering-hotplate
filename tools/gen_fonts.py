#!/usr/bin/env python3
"""
Genera las fuentes derivadas/dibujadas de lib/fonts/.

    cd firmware/avr && python3 tools/gen_fonts.py

  font6x8_bold.c  negrita derivada de font5x7.c (trazo +1 columna, avance 7)
  font8x12.c      dígitos grandes para temperatura (dibujo abajo)

Para retocar un glifo: editar el dibujo ('#' = píxel encendido) y regenerar.
'\\xB0' es el grado ('°').
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "lib", "fonts")
DEG = "\xb0"


def c_char(ch):
    if ch == DEG:
        return "grados"
    if ch == " ":
        return "espacio"
    return "'%s'" % ch


def load_5x7():
    src = open(os.path.join(FONTS, "font5x7.c")).read()
    body = re.search(r"font5x7_data\[\] PROGMEM = \{(.*?)\};", src, re.S).group(1)
    vals = [int(v, 16) for v in re.findall(r"0x[0-9A-Fa-f]+", body)]
    assert len(vals) == 96 * 5, len(vals)
    return [vals[i * 5:i * 5 + 5] for i in range(96)]


def gen_bold():
    glyphs = load_5x7()
    lines = [
        "/* Generado por tools/gen_fonts.py — no editar a mano. */",
        "/*",
        " * font6x8_bold — texto destacado (títulos).",
        " * Negrita de font5x7: cada columna OR la anterior (6 px de trazo).",
        " * Avance 7: 1 px de separación, las letras no se pegan.",
        " * 7 filas de tinta; con la interlínea ocupa una celda de 6×8.",
        " */",
        '#include "font.h"',
        "#include <avr/pgmspace.h>",
        "",
        "static const uint8_t font6x8_bold_data[] PROGMEM = {",
    ]
    for i, g in enumerate(glyphs):
        cols = [(g[c] if c < 5 else 0) | (g[c - 1] if c > 0 else 0) for c in range(6)]
        name = "grados" if i == 95 else c_char(chr(32 + i))
        if name in ("'*'", "'/'"):
            name = "0x%02X" % (32 + i)
        lines.append("    " + ", ".join("0x%02X" % v for v in cols) + ",  /* %s */" % name)
    lines += [
        "};",
        "",
        "const font_t FONT_6X8_BOLD = {",
        "    font6x8_bold_data, 0, 6u, 7u, 7u, 32u, 95u, 95u, FONT_COLS",
        "};",
    ]
    return "\n".join(lines) + "\n"


def rows_font(name, doc, glyphs, w, h, advance, symbol):
    order = "".join(ch for ch, _ in glyphs)
    lines = [
        "/* Generado por tools/gen_fonts.py — no editar a mano. */",
        "/*",
    ]
    lines += [" * " + d for d in doc]
    lines += [
        " * Formato FONT_ROWS: 1 byte por fila, MSB = izquierda.",
        " */",
        '#include "font.h"',
        "#include <avr/pgmspace.h>",
        "",
        "static const char %s_map[] PROGMEM = \"%s\";" % (
            name, "".join("\\xB0\" \"" if ch == DEG else ch for ch in order)),
        "",
        "static const uint8_t %s_data[] PROGMEM = {" % name,
    ]
    for ch, art in glyphs:
        assert len(art) == h, (name, ch, len(art))
        lines.append("    /* %s */" % c_char(ch))
        for row in art:
            assert len(row) == w, (name, ch, row)
            v = 0
            for x, px in enumerate(row):
                if px == "#":
                    v |= 0x80 >> x
            lines.append("    0x%02X,  /* %s */" % (v, row.replace(".", " ")))
    lines += [
        "};",
        "",
        "const font_t %s = {" % symbol,
        "    %s_data, %s_map, %du, %du, %du, 0u, 0u, FONT_NO_GLYPH, FONT_ROWS" % (
            name, name, w, h, advance),
        "};",
    ]
    return "\n".join(lines) + "\n"


# ---------- 8×12: temperatura ----------

G8X12 = [
    (" ", ["........"] * 12),
    ("-", ["........"] * 5 + [".######.", ".######."] + ["........"] * 5),
    (".", ["........"] * 10 + ["...##...", "...##..."]),
    (":", ["........"] * 3 + ["...##...", "...##..."] + ["........"] * 3
          + ["...##...", "...##..."] + ["........"] * 2),
    ("0", ["..####..", ".######.", "##....##", "##....##", "##...###", "##..####",
           "####..##", "###...##", "##....##", "##....##", ".######.", "..####.."]),
    ("1", ["...##...", "..###...", ".####...", "...##...", "...##...", "...##...",
           "...##...", "...##...", "...##...", "...##...", ".######.", ".######."]),
    ("2", ["..####..", ".######.", "##....##", "......##", ".....##.", "....##..",
           "...##...", "..##....", ".##.....", "##......", "########", "########"]),
    ("3", [".######.", "########", "......##", ".....##.", "....##..", "...####.",
           "......##", "......##", "......##", "##....##", ".######.", "..####.."]),
    ("4", ["....###.", "...####.", "..##.##.", ".##..##.", "##...##.", "##...##.",
           "########", "########", ".....##.", ".....##.", ".....##.", ".....##."]),
    ("5", ["########", "########", "##......", "##......", "######..", "#######.",
           "......##", "......##", "......##", "##....##", ".######.", "..####.."]),
    ("6", ["..####..", ".##.....", "##......", "##......", "######..", "#######.",
           "##....##", "##....##", "##....##", "##....##", ".######.", "..####.."]),
    ("7", ["########", "########", "......##", ".....##.", ".....##.", "....##..",
           "....##..", "...##...", "...##...", "..##....", "..##....", "..##...."]),
    ("8", ["..####..", ".##..##.", "##....##", "##....##", ".##..##.", "..####..",
           ".##..##.", "##....##", "##....##", "##....##", ".######.", "..####.."]),
    ("9", ["..####..", ".######.", "##....##", "##....##", "##....##", ".#######",
           "..######", "......##", "......##", ".....##.", "....##..", ".####..."]),
    (DEG, ["..###...", ".##.##..", ".##.##..", "..###..."] + ["........"] * 8),
    ("C", ["..#####.", ".##...##", "##......", "##......", "##......", "##......",
           "##......", "##......", "##......", "##......", ".##...##", "..#####."]),
    ("F", ["########", "########", "##......", "##......", "######..", "######..",
           "##......", "##......", "##......", "##......", "##......", "##......"]),
    ("%", ["##....##", "##...##.", ".....##.", "....##..", "....##..", "...##...",
           "...##...", "..##....", "..##....", ".##.....", ".##...##", "##....##"]),
]


def main():
    out = {
        "font6x8_bold.c": gen_bold(),
        "font8x12.c": rows_font(
            "font8x12",
            ["font8x12 — texto grande (temperatura).",
             "Solo \" -.:0123456789°CF%\": ahorra flash frente a ASCII completo.",
             "Trazo de 2 px; avance 9."],
            G8X12, 8, 12, 9, "FONT_8X12"),
    }
    for name, text in out.items():
        path = os.path.join(FONTS, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("escrito", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
