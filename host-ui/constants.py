"""Constantes de la herramienta host (UI + sondeo)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAMPS_CACHE = ROOT / "ramps.json"
TUNE_CACHE = ROOT / "tune_params.json"

MAX_SAMPLES = 900
POLL_MS = 50
# Ventana inicial del eje X (Tiempo s) en todas las gráficas LiveChart.
CHART_X_SPAN_S = 300.0

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
