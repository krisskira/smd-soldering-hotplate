#!/usr/bin/env bash
# Genera el video demo de la landing a partir de una traza HEAT real.
#   ./build.sh            → ../../public/media/hotplate-demo.mp4 + póster
# Requiere gcc, ffmpeg y Python con Pillow + numpy (el .venv del repo sirve).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
fw="$here/../../../firmware/avr"
python="${PYTHON:-$here/../../../.venv/bin/python}"
[ -x "$python" ] || python=python3

mkdir -p "$here/build"
gcc -std=c11 -O2 -Wall -Wno-unused-function \
  -I"$fw/tools/ui_screens" -I"$fw" -I"$fw/src" -I"$fw/src/ui" -I"$fw/src/ui/core" -I"$fw/lib" -I"$fw/config" \
  -o "$here/build/replay" "$here/replay.c" \
  "$fw/src/ui/home_view.c" "$fw/src/ui/core/ui_text.c" "$fw/src/ui/core/ui_components.c" \
  "$fw/lib/i18n/i18n.c" "$fw/lib/st7920/st7920_text.c" "$fw/lib/fonts/font.c" \
  "$fw/lib/fonts/font5x7.c" "$fw/lib/fonts/font8x12.c" "$fw/lib/fonts/font_icons.c"

"$python" "$here/render.py" "$@"
