#!/usr/bin/env python3
"""Punto de entrada: `python host-ui/app.py`."""

from __future__ import annotations

import sys
from pathlib import Path

# Paquete plano bajo host-ui/ (nombre con guion: no es importable como package).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from window import MainWindow


def main() -> None:
    MainWindow().mainloop()


if __name__ == "__main__":
    main()
