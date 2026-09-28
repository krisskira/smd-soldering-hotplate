"""Caché local de parámetros de autoajuste (tune_params.json)."""

from __future__ import annotations

import json
from typing import Optional

from constants import TUNE_CACHE


def load_tune() -> Optional[dict[str, int]]:
    if not TUNE_CACHE.exists():
        return None
    try:
        data = json.loads(TUNE_CACHE.read_text(encoding="utf-8"))
        out = {
            "temp": int(data["temp"]),
            "cycles": int(data["cycles"]),
            "hyst": int(data["hyst"]),
            "max_s": int(data.get("max_s", 600)),
        }
        return out
    except Exception:
        return None


def save_tune(temp: int, cycles: int, hyst: int, max_s: int = 600) -> None:
    data = {"temp": temp, "cycles": cycles, "hyst": hyst, "max_s": max_s}
    try:
        TUNE_CACHE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
