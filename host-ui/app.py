#!/usr/bin/env python3
"""Punto de entrada: `python host-ui/app.py`."""

from __future__ import annotations

import sys
from pathlib import Path

# Paquete plano bajo host-ui/ (nombre con guion: no es importable como package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from window import MainWindow


def main() -> None:
    # En el binario (--macos-app-mode=gui) no hay consola: si el arranque falla,
    # el motivo queda en hotplate-studio.log junto al ejecutable.
    try:
        MainWindow().mainloop()
    except Exception:
        import traceback

        here = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        log = here / "hotplate-studio.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
