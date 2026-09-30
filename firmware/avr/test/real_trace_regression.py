#!/usr/bin/env python3
"""Regresiones térmicas contra los CSV medidos en la placa real."""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HEAT_FILES = sorted((ROOT / "docs/heat-results").glob("*.csv")) + [
    ROOT / "firmware/avr/doc/ultimo-heat/hotplate_heat_trace-1.csv"
]
ATUNE_FILES = sorted((ROOT / "docs/atune-results").glob("*.csv"))

T = "Tiempo (s)"
TEMP = "Temperatura medida (°C)"
SET = "Temperatura consignada / SET (°C)"
DUTY = "Potencia calentador (%)"
PHASE = "Fase del proceso"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(row: dict[str, str], key: str) -> float:
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError):
        return math.nan


def relay_spans(data: list[dict[str, str]]) -> list[tuple[bool, float]]:
    """Tramos ON/OFF, en segundos, descartando cambios sin duración."""
    result: list[tuple[bool, float]] = []
    start = number(data[0], T)
    state = number(data[0], DUTY) >= 50.0
    last = start
    for row in data[1:]:
        now = number(row, T)
        new_state = number(row, DUTY) >= 50.0
        if new_state != state:
            result.append((state, max(0.0, last - start)))
            start = now
            state = new_state
        last = now
    result.append((state, max(0.0, last - start)))
    return result


def max_stall_seconds(data: list[dict[str, str]]) -> float:
    """Misma intención que RUN_STALL: DU alto, pendiente plana y fuera de BN=4."""
    best = current = 0.0
    previous: dict[str, str] | None = None
    for row in data:
        if previous is None:
            previous = row
            continue
        dt = number(row, T) - number(previous, T)
        dtemp = number(row, TEMP) - number(previous, TEMP)
        gap = number(row, SET) - number(row, TEMP)
        run = row[PHASE].startswith("Rampa")
        if (
            0.25 <= dt <= 2.0
            and run
            and number(row, DUTY) >= 95.0
            and abs(dtemp) <= 0.2
            and gap > 4.0
        ):
            current += dt
            best = max(best, current)
        else:
            current = 0.0
        previous = row
    return best


def replay_old_pi(data: list[dict[str, str]]) -> tuple[float, float, float]:
    """Reproduce pid.c previo sobre la última captura (Kp/Ki=64/3)."""
    kp, ki = 64, 3
    integral = 0
    previous_t: int | None = None
    reference = 0
    duty = 0
    previous_phase = ""
    comparison: list[float] = []
    plateau_old: list[float] = []
    plateau_new: list[float] = []

    for row in data:
        phase = row[PHASE]
        temp = round(number(row, TEMP) * 10)
        target = round(number(row, SET))
        if math.isnan(number(row, SET)):
            continue
        if phase.startswith("Rampa") and phase != previous_phase:
            previous_t = temp
            reference = temp
        previous_phase = phase
        rate = 0 if previous_t is None else temp - previous_t
        previous_t = temp
        reference = min(target * 10, reference + 12)
        predicted = temp + max(-5000, min(5000, rate * 15))
        error = reference - predicted
        if not ((duty >= 100 and error > 0) or (duty == 0 and error < 0)):
            integral = max(-10000, min(10000, integral + error))

        old_out = (kp * error + (ki * integral) // 100) // 10
        duty = max(0, min(100, max(0, min(1000, old_out)) // 10))

        if phase == "Rampa 3" and number(row, T) >= 700.0:
            comparison.append(abs(duty - number(row, DUTY)))
            plateau_old.append(duty)
            new_out = (kp * error + (ki * integral) // 10) // 10
            plateau_new.append(max(0, min(100, max(0, min(1000, new_out)) // 10)))

    return (
        statistics.median(comparison),
        statistics.median(plateau_old),
        statistics.median(plateau_new),
    )


def main() -> None:
    assert len(HEAT_FILES) >= 5, f"faltan trazas HEAT reales: {len(HEAT_FILES)}"
    assert len(ATUNE_FILES) >= 2, f"faltan trazas autotune reales: {len(ATUNE_FILES)}"

    max_stall = 0.0
    max_temp = -math.inf
    tal_seconds = 0.0
    for path in HEAT_FILES:
        data = rows(path)
        max_temp = max(max_temp, max(number(row, TEMP) for row in data))
        max_stall = max(max_stall, max_stall_seconds(data))
        for first, second in zip(data, data[1:]):
            dt = number(second, T) - number(first, T)
            if 0.25 <= dt <= 2.0 and number(first, TEMP) >= 183.0:
                tal_seconds += dt

    # No debe haber falsos ERROR:9 en ninguna corrida medida.
    assert max_stall < 180.0, max_stall
    # Ningún CSV real valida aún el proceso sobre liquidus.
    assert max_temp < 183.0
    assert tal_seconds == 0.0

    latest = rows(HEAT_FILES[-1])
    diff, old_duty, corrected_duty = replay_old_pi(latest)
    # La fórmula anterior reproduce el atasco real; la corregida recupera autoridad.
    assert diff <= 3.0, diff
    assert 28.0 <= old_duty <= 35.0, old_duty
    assert 55.0 <= corrected_duty <= 65.0, corrected_duty

    worst_ratio = 0.0
    for path in ATUNE_FILES:
        spans = relay_spans(rows(path))
        # Se descarta el primer calentamiento; después se comparan ON con OFF previo.
        for index in range(2, len(spans)):
            on, on_s = spans[index]
            prev_on, off_s = spans[index - 1]
            if on and not prev_on and off_s > 1.0:
                worst_ratio = max(worst_ratio, on_s / off_s)
    # Los autotunes reales a 100 °C no dispararían la regla ON >= 3*OFF.
    assert worst_ratio < 1.0, worst_ratio

    print(
        "real_trace_regression: OK "
        f"(heat={len(HEAT_FILES)}, atune={len(ATUNE_FILES)}, "
        f"Tmax={max_temp:.1f}°C, stall_max={max_stall:.1f}s, "
        f"PI_old={old_duty:.0f}%, PI_fixed={corrected_duty:.0f}%, "
        f"atune_ON/OFF_max={worst_ratio:.2f})"
    )
    print("NOTA: no hay datos reales >=183 °C ni autotune entre 120 y 150 °C.")


if __name__ == "__main__":
    main()
