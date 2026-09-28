"""Constructores AT y parse de tramas del Hot Plate (usb-automation.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

AT_LINE_MAX = 32  # incluye NUL; payload útil = 31
PAYLOAD_MAX = AT_LINE_MAX - 1

PHASE_NAMES = {
    0: "Inactivo",
    1: "Espera (retraso)",
    2: "Precalentado",
    3: "Estabilizando",
    4: "Hold",
    5: "En rampa",
    6: "Enfriando",
    7: "Alarma",
    8: "Terminado",
    9: "Falla",
    10: "Autoajuste",
}

PROG_NAMES = {1: "HEAT", 2: "Autoajuste PID"}

ERROR_NAMES = {
    1: "comando inválido",
    2: "parámetro inválido",
    3: "se requiere modo USB",
    4: "equipo ocupado",
    5: "programa en curso",
    6: "sensor inválido",
    7: "sobretemperatura",
    8: "abortado en el equipo",
}

ALARM_NAMES = {2: "HEAT terminado"}

ATUNE_PHASE_NAMES = {
    0: "Inactivo",
    1: "En curso",
    2: "Listo",
    3: "Fallido",
}


class ProtocolError(ValueError):
    pass


def _cmd(line: str) -> str:
    if len(line) > PAYLOAD_MAX:
        raise ProtocolError(f"línea > {PAYLOAD_MAX} chars: {line!r}")
    return line


def cmd_at() -> str:
    return _cmd("AT")


def cmd_stat() -> str:
    return _cmd("AT+STAT?")


def cmd_mode(on: int) -> str:
    if on not in (0, 1):
        raise ProtocolError("MODE debe ser 0 o 1")
    return _cmd(f"AT+MODE={on}")


def cmd_run_heat() -> str:
    return _cmd("AT+RUN=1")


def cmd_run_tune(
    temp: int, cycles: int, hyst: int, max_s: int | None = None
) -> str:
    if max_s is None:
        return _cmd(f"AT+RUN=2,{temp},{cycles},{hyst}")
    return _cmd(f"AT+RUN=2,{temp},{cycles},{hyst},{max_s}")


def cmd_stop() -> str:
    return _cmd("AT+STOP")


def cmd_cfg_query() -> str:
    return _cmd("AT+CFG?")


def cmd_cfg_ramps_query() -> str:
    return _cmd("AT+CFG=R?")


def cmd_cfg_safety(mn: int, mx: int) -> str:
    return _cmd(f"AT+CFG=S,{mn},{mx}")


def cmd_cfg_heat(
    en: int, pct: int, stab: int, delay: int, air: int, snd: int
) -> str:
    return _cmd(f"AT+CFG=H,{en},{pct},{stab},{delay},{air},{snd}")


def cmd_cfg_pid(kp: int, ki: int, kd: int) -> str:
    return _cmd(f"AT+CFG=P,{kp},{ki},{kd}")


def cmd_cfg_ramp(idx: int, temp: int, hold: int) -> str:
    return _cmd(f"AT+CFG=R,{idx},{temp},{hold}")


def cmd_cfg_apply_atune() -> str:
    return _cmd("AT+CFG=A")


def cmd_cfg_tune(cycles: int, hyst: int, max_s: int) -> str:
    return _cmd(f"AT+CFG=T,{cycles},{hyst},{max_s}")


# --- validación (espejo firmware) ---

def validate_safety(mn: int, mx: int) -> Optional[str]:
    if not (30 <= mn <= 100):
        return "min debe estar en 30..100"
    if not (40 <= mx <= 250):
        return "max debe estar en 40..250"
    if mn > mx:
        return "min no puede ser mayor que max"
    return None


def validate_heat(
    en: int, pct: int, stab: int, delay: int, air: int, snd: int
) -> Optional[str]:
    for name, v in (("en", en), ("air", air), ("snd", snd)):
        if v not in (0, 1):
            return f"{name} debe ser 0 o 1"
    if not (50 <= pct <= 100) or (pct % 5) != 0:
        return "pct debe estar en 50..100 paso 5"
    if not (1 <= stab <= 3600):
        return "stab debe estar en 1..3600"
    if not (0 <= delay <= 3600):
        return "delay debe estar en 0..3600"
    return None


def validate_pid(kp: int, ki: int, kd: int) -> Optional[str]:
    for name, v in (("kp", kp), ("ki", ki), ("kd", kd)):
        if not (0 <= v <= 999):
            return f"{name} debe estar en 0..999"
    return None


def validate_ramp(
    idx: int, temp: int, hold: int, tmin: int, tmax: int
) -> Optional[str]:
    if not (0 <= idx <= 3):
        return "índice de rampa debe ser 0..3"
    # temp=0: deshabilitar desde idx (firmware); rampa 1 (idx 0) no.
    if temp == 0:
        if idx == 0:
            return "la rampa 1 no se puede deshabilitar (temp=0)"
        if not (1 <= hold <= 3600):
            return "hold debe estar en 1..3600"
        return None
    if not (tmin <= temp <= tmax):
        return f"temp debe estar en {tmin}..{tmax}"
    if not (1 <= hold <= 3600):
        return "hold debe estar en 1..3600"
    return None


def validate_tune(
    temp: int,
    cycles: int,
    hyst: int,
    tmin: int,
    tmax: int,
    max_s: int | None = None,
) -> Optional[str]:
    if not (tmin <= temp <= tmax - 10):
        return f"temp debe estar en {tmin}..{tmax - 10}"
    if not (3 <= cycles <= 10):
        return "ciclos debe estar en 3..10"
    if not (1 <= hyst <= 99):
        return "hyst (×10) debe estar en 1..99"
    if max_s is not None and not (120 <= max_s <= 3600):
        return "timeout max_s debe estar en 120..3600"
    return None


def validate_tune_cfg(cycles: int, hyst: int, max_s: int) -> Optional[str]:
    if not (3 <= cycles <= 10):
        return "ciclos debe estar en 3..10"
    if not (1 <= hyst <= 99):
        return "hyst (×10) debe estar en 1..99"
    if not (120 <= max_s <= 3600):
        return "timeout max_s debe estar en 120..3600"
    return None


# --- parse ---

@dataclass
class Parsed:
    kind: str
    fields: dict[str, Any] = field(default_factory=dict)
    raw: str = ""


def _parse_kv(body: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not body:
        return out
    for part in body.split(","):
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key == "T" and val == "---":
            out[key] = None
            continue
        if "." in val:
            try:
                out[key] = float(val)
                continue
            except ValueError:
                pass
        try:
            out[key] = int(val)
        except ValueError:
            out[key] = val
    return out


def _parse_ramps(body: str) -> dict[str, Any]:
    """$R,N=<n>,0=<°C>/<s>,1=... → {n, steps: [(t,s), ...]}"""
    fields = _parse_kv(body)
    n = int(fields.get("N", 0))
    steps: list[tuple[int, int]] = []
    for i in range(4):
        raw = fields.get(str(i))
        if isinstance(raw, str) and "/" in raw:
            a, b = raw.split("/", 1)
            steps.append((int(a), int(b)))
        else:
            steps.append((0, 0))
    return {"n": n, "steps": steps, **{k: v for k, v in fields.items() if k == "N"}}


def parse_line(line: str) -> Parsed:
    s = line.strip()
    if not s:
        return Parsed("RAW", raw=s)
    if s == "OK":
        return Parsed("OK", raw=s)
    if s == "HP":
        return Parsed("BOOT", raw=s)
    if s.startswith("ERROR:"):
        try:
            code = int(s[6:])
        except ValueError:
            return Parsed("RAW", raw=s)
        return Parsed(
            "ERROR",
            {"code": code, "name": ERROR_NAMES.get(code, "?")},
            raw=s,
        )
    if s.startswith("ALARM:"):
        try:
            code = int(s[6:])
        except ValueError:
            return Parsed("RAW", raw=s)
        return Parsed(
            "ALARM",
            {"code": code, "name": ALARM_NAMES.get(code, "?")},
            raw=s,
        )
    if s.startswith("$HP"):
        body = s[3:].lstrip(",")
        return Parsed("HP", _parse_kv(body), raw=s)
    if s.startswith("$CF"):
        body = s[3:].lstrip(",")
        return Parsed("CF", _parse_kv(body), raw=s)
    if s.startswith("$R"):
        body = s[2:].lstrip(",")
        return Parsed("R", _parse_ramps(body), raw=s)
    return Parsed("RAW", raw=s)


def phase_name(a: int) -> str:
    return PHASE_NAMES.get(a, str(a))


def chart_phase_label(a: int, ri: Any = None) -> str:
    """Nombre corto para el marcador de fase en la curva."""
    if a == 1:
        return "Espera"
    if a == 5:
        if isinstance(ri, int):
            return f"Rampa {ri + 1}"
        return "Rampa"
    return PHASE_NAMES.get(a, str(a))


def chart_atune_label(ap: int) -> str:
    return {0: "Inactivo", 1: "Ajuste", 2: "Listo", 3: "Fallido"}.get(ap, str(ap))


def prog_name(p: int) -> str:
    return PROG_NAMES.get(p, str(p))


def atune_phase_name(ap: int) -> str:
    return ATUNE_PHASE_NAMES.get(ap, str(ap))
