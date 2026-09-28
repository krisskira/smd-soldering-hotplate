"""Reglas de objetivo HEAT (espejo del pipeline del device)."""

from __future__ import annotations

from typing import Sequence


def planned_heat_target(
    preheat_en: str,
    preheat_pct: str,
    temps: Sequence[str],
    active: Sequence[bool],
) -> tuple[str, str]:
    """Devuelve (objetivo_texto, origen_texto) según perfil local."""
    idxs = [i for i, on in enumerate(active) if on]
    if not idxs:
        return "—", "Sin escalones activos en el perfil"
    try:
        r1 = int(temps[idxs[0]])
    except (ValueError, IndexError):
        return "—", "Temperatura de rampa 1 inválida"
    if preheat_en == "1":
        try:
            cap = int(r1 * int(preheat_pct) / 100)
        except ValueError:
            cap = r1
        n = idxs[0] + 1
        return (
            f"{cap} → {r1}",
            f"Al iniciar: precalentado ({preheat_pct}% de rampa {n}), luego rampa {n}",
        )
    n = idxs[0] + 1
    return str(r1), f"Al iniciar: rampa {n} del perfil"


def live_heat_objetivo(
    last_hp: dict,
    preheat_en: str,
    preheat_pct: str,
    temps: Sequence[str],
    active: Sequence[bool],
) -> tuple[str, str]:
    """Objetivo mostrado: vivo si el proceso lo usa; si no, plan de rampas."""
    a = int(last_hp.get("A", 0)) if last_hp else 0
    p = int(last_hp.get("P", 0)) if last_hp else 0
    set_c = last_hp.get("SET") if last_hp else None

    if p == 2 or a == 10:
        return (
            "—" if set_c is None else str(set_c),
            "Autoajuste PID (temperatura de oscilación)",
        )
    if p == 1 and a in (2, 3):
        return (
            "—" if set_c is None else str(set_c),
            f"Precalentado: {preheat_pct}% de la temperatura de la rampa 1",
        )
    if p == 1 and a in (4, 5):
        ri = int(last_hp.get("RI", 0))
        return (
            "—" if set_c is None else str(set_c),
            f"Temperatura definida en la rampa {ri + 1}",
        )
    tgt, src = planned_heat_target(preheat_en, preheat_pct, temps, active)
    if p == 1 and a == 1:
        return tgt, "Aún en espera; después " + src.lower()
    return tgt, src
