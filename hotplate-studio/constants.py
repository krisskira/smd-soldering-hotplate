"""Constantes de HotPlate Studio (UI + sondeo)."""

import sys
from pathlib import Path

def _app_dir() -> Path:
    """Carpeta de datos: junto al binario compilado, o host-ui/ en código fuente."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = _app_dir()
RAMPS_CACHE = ROOT / "ramps.json"
TUNE_CACHE = ROOT / "tune_params.json"

MAX_SAMPLES = 900
POLL_MS = 50
# Eje X de respaldo. HEAT calcula la ventana desde el perfil y crece si
# el proceso la supera; Autotune la deja fija en el timeout.
CHART_X_SPAN_S = 300.0

# Valores de fábrica (EEPROM / campos de la app antes de leer $CF).
TUNE_TEMP_C_DEFAULT = 150
TUNE_CYCLES_DEFAULT = 5
TUNE_HYST_X10_DEFAULT = 15
TUNE_MAX_S_DEFAULT = 2000
ATUNE_SET_LO_C = 120
ATUNE_SET_HI_C = 150
TEMP_MIN_C_DEFAULT = 50
TEMP_MAX_C_DEFAULT = 210
TEMP_MAX_C_HI = 260
TEMP_SET_CEILING_C = 250
PID_KP_DEFAULT = 246
PID_KI_DEFAULT = 10
PID_KD_DEFAULT = 0  # autotune PI; lazo usa lookahead compile-time

STAT_INTERVALS_MS = {
    "1 s": 1_000,
    "3 s": 3_000,
    "5 s": 5_000,
    "10 s": 10_000,
    "15 s": 15_000,
    "30 s": 30_000,
    "1 min": 60_000,
    "3 min": 180_000,
    "5 min": 300_000,
}

LED_RED = "#c0392b"
LED_GREEN = "#27ae60"
LED_AMBER = "#f39c12"
