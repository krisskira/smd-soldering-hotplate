"""Caché local de escalones (ramps.json)."""

from __future__ import annotations

import json
from typing import Callable, Sequence

from constants import RAMPS_CACHE


def load_ramps(
    set_active: Callable[[int, bool], None],
    set_temp: Callable[[int, str], None],
    set_hold: Callable[[int, str], None],
) -> None:
    if not RAMPS_CACHE.exists():
        return
    try:
        data = json.loads(RAMPS_CACHE.read_text(encoding="utf-8"))
        for i, step in enumerate(data.get("steps", [])[:4]):
            set_active(i, bool(step.get("active", i < 2)))
            set_temp(i, str(step.get("temp", 100 + 25 * i)))
            set_hold(i, str(step.get("hold", 60)))
    except Exception:
        pass


def save_ramps(
    active: Sequence[bool],
    temps: Sequence[str],
    holds: Sequence[str],
) -> None:
    data = {
        "n": sum(1 for v in active if v),
        "steps": [
            {
                "active": active[i],
                "temp": int(temps[i] or 0),
                "hold": int(holds[i] or 0),
            }
            for i in range(4)
        ],
    }
    try:
        RAMPS_CACHE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
