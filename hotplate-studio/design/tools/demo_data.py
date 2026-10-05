"""Datos de demostración: un modelo térmico sencillo de la placa.

No es un equipo real: sirve para que las capturas tengan curvas creíbles.
`sim_heat` devuelve las filas de la curva y un `$HP` por segundo; `sim_tune`
las filas de un autoajuste por histéresis.
"""

from __future__ import annotations

import protocol as proto

PROFILE = [(150, 120), (165, 1), (170, 1), (190, 90)]

T_AMB = 28.0
GAIN = 3.2  # °C por % de potencia en régimen
TAU = 700.0
DEAD_S = 32


class Plate:
    def __init__(self, t0: float = T_AMB) -> None:
        self.t = t0
        self.hist = [0.0] * DEAD_S

    def step(self, duty: float, fan: bool) -> float:
        self.hist.append(duty)
        u = self.hist.pop(0)
        loss = (self.t - T_AMB) * (2.2 if fan else 1.0)
        self.t += (GAIN * u - loss) / TAU
        return round(self.t, 1)


def sim_heat(ramps: list[tuple[int, int]], *, band: int = 4, t_min: int = 50,
             alarm_s: int = 60, stop_at: float | None = None):
    """Filas (t, T, SET_plot, DU, fase) + snapshots $HP por segundo."""
    plate = Plate()
    rows, hp = [], []
    ri, phase, hold_left = 0, 5, 0
    t = 0
    alarm_left = alarm_s
    tl = 0
    while True:
        set_c = ramps[ri][0] if phase in (4, 5) else 0
        temp = plate.t
        if phase in (4, 5):
            slope = (plate.t - (rows[-5][1] if len(rows) >= 5 else plate.t)) / 5.0
            pred = temp + slope * 30.0
            ff = (set_c - T_AMB) / GAIN
            duty = max(0.0, min(100.0, ff + 5.0 * (set_c - pred)))
        else:
            duty = 0.0
        fan = phase in (6, 7)
        duty = float(int(duty))
        temp = plate.step(duty, fan)
        if temp >= 183:
            tl += 1

        if phase == 5 and abs(temp - set_c) <= band:
            phase, hold_left = 4, ramps[ri][1]
        elif phase == 4:
            hold_left -= 1
            if hold_left <= 0:
                if ri + 1 < len(ramps):
                    ri, phase = ri + 1, 5
                else:
                    phase = 7
        elif phase == 7:
            alarm_left -= 1
            if alarm_left <= 0:
                phase = 6
        elif phase == 6 and temp <= t_min:
            phase = 8

        plot_set = float(set_c) if phase in (4, 5) else float("nan")
        rows.append((float(t), temp, plot_set, duty, proto.chart_phase_label(phase, ri)))
        hp.append({
            "T": temp, "P": 1, "A": phase, "SET": ramps[ri][0],
            "RUN": hold_left if phase == 4 else (alarm_left if phase == 7 else 0),
            "EL": t, "DU": int(duty), "F": int(fan), "RI": ri, "FL": 0, "TL": tl,
        })
        t += 1
        if phase == 8 or (stop_at is not None and t >= stop_at):
            break
    return rows, hp


def sim_tune(set_c: int = 150, hyst_x10: int = 15, cycles: int = 5):
    plate = Plate()
    h = hyst_x10 / 10.0
    rows = []
    heating, done_cycles, seen_high = True, 0, False
    t = 0
    while t < 2000:
        if heating and plate.t >= set_c + h:
            heating, seen_high = False, True
        elif not heating and plate.t <= set_c - h:
            heating = True
            if seen_high:
                done_cycles += 1
        duty = 100.0 if heating else 0.0
        temp = plate.step(duty, fan=not heating and seen_high)
        finished = done_cycles >= cycles
        rows.append((float(t), temp, float(set_c), 0.0 if finished else duty,
                     proto.chart_atune_label(2 if finished else 1)))
        t += 1
        if finished:
            break
    return rows, done_cycles
