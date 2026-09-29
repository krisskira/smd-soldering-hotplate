#!/usr/bin/env python3
"""Simulación offline del PI predictivo sobre la traza de autotune.

Reproduce t_ref + lookahead para estimar el primer corte de duty en una
subida (RISE/LOOK = app_config.h). No sustituye el banco real.

  python3 docs/heat_predictive_sim.py
"""
from __future__ import annotations

import csv
from pathlib import Path

RISE = 1.2
LOOK = 15.0
KP = 24.6
KI = 1.0
SET = 100.0


def main() -> None:
    path = Path(__file__).with_name("hotplate_tune_trace.csv")
    rows = [(float(r["t_s"]), float(r["T_C"])) for r in csv.DictReader(path.open())]

    t_ref = rows[0][1]
    prev_t = t_ref
    prev_ts = rows[0][0]
    rate = 0.0
    integ = 0.0
    duty = 100.0  # arranque saturado como el firmware en error grande
    cut = None
    tmax = 0.0

    for t_s, T in rows[1:]:
        dt = max(t_s - prev_ts, 0.2)
        rate = 0.75 * rate + 0.25 * ((T - prev_t) / dt)
        prev_t, prev_ts = T, t_s
        tmax = max(tmax, T)

        if t_ref < SET:
            t_ref = min(SET, t_ref + RISE * dt)
        elif t_ref > SET:
            t_ref = max(SET, t_ref - RISE * dt)

        pred = T + rate * LOOK
        err = t_ref - pred
        sat = (duty >= 99 and err > 0) or (duty <= 1 and err < 0)
        if not sat:
            integ = max(-1000.0, min(1000.0, integ + err * dt))
        out = KP * err + KI * integ
        duty = max(0.0, min(100.0, out))

        if cut is None and duty < 50 and 80.0 < T < SET:
            cut = (t_s, T, pred, t_ref, rate)

    print(f"trace={path.name} SET={SET}")
    print(f"trace_peak_T={tmax:.1f} (bang-bang real, overshoot +{tmax - SET:.0f})")
    if cut:
        print(
            f"predictive_cut t={cut[0]:.0f}s T={cut[1]:.1f} "
            f"pred={cut[2]:.1f} t_ref={cut[3]:.1f} rate={cut[4]:.2f}°C/s"
        )
        print(
            f"Corte ~{SET - cut[1]:.0f} °C antes del setpoint "
            f"(LOOK={LOOK:.0f}s, RISE={RISE}°C/s)."
        )
    else:
        print("No se observó corte anticipado; revisar LOOK/RISE en banco.")


if __name__ == "__main__":
    main()
