"""Estado de sesión y telemetría (sin widgets Tk)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

from constants import MAX_SAMPLES, TEMP_MAX_C_DEFAULT, TEMP_MIN_C_DEFAULT


@dataclass
class SessionState:
    device_online: bool = False
    usb_mode: bool = False
    conn_port: str = ""
    tmin: int = TEMP_MIN_C_DEFAULT
    tmax: int = TEMP_MAX_C_DEFAULT
    last_hp: dict[str, Any] = field(default_factory=dict)
    last_cf: dict[str, Any] = field(default_factory=dict)
    samples: deque = field(default_factory=lambda: deque(maxlen=MAX_SAMPLES))
    # Historial completo del proceso (CSV); `samples` es solo ventana de gráfica
    trace: list = field(default_factory=list)
    t0: Optional[float] = None
    recording_heat: bool = False
    # Evita que un STAT? IDLE pendiente desarme la captura justo antes del
    # OK de AT+RUN=1. Solo se acepta IDLE como fin tras ver HEAT activo.
    heat_seen_active: bool = False
    poll_stat_enabled: bool = True
    stat_interval_label: str = "1 s"

    def reset_link(self) -> None:
        self.device_online = False
        self.usb_mode = False
        self.conn_port = ""
        self.recording_heat = False
        self.heat_seen_active = False

    def clear_samples(self) -> None:
        self.samples.clear()
        self.trace.clear()
        self.t0 = None
        self.heat_seen_active = False

    def append_sample(
        self,
        t_s: float,
        t_c: float,
        set_c: float,
        du: float,
        phase: str = "",
    ) -> None:
        row = (t_s, t_c, set_c, du, phase)
        self.trace.append(row)
        self.samples.append(row)
