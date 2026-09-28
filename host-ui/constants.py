"""Constantes de la herramienta host (UI + sondeo)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAMPS_CACHE = ROOT / "ramps.json"
TUNE_CACHE = ROOT / "tune_params.json"

MAX_SAMPLES = 900
POLL_MS = 50
# Fallback genérico; HEAT usa CHART_HEAT_X_SPAN_S (origen fijo en 0).
CHART_X_SPAN_S = 300.0
CHART_HEAT_X_SPAN_S = 2000.0

# Valores de fábrica (EEPROM / campos de la app antes de leer $CF).
TUNE_TEMP_C_DEFAULT = 100
TUNE_CYCLES_DEFAULT = 5
TUNE_HYST_X10_DEFAULT = 15
TUNE_MAX_S_DEFAULT = 2000
TEMP_MIN_C_DEFAULT = 50
TEMP_MAX_C_DEFAULT = 250
PID_KP_DEFAULT = 246
PID_KI_DEFAULT = 10
PID_KD_DEFAULT = 400

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
