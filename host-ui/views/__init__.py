"""Construcción de pestañas Tk (solo UI)."""

from views.appearance_view import AppearanceView
from views.connection_view import ConnectionView
from views.heat_view import HeatView
from views.settings_view import SettingsView
from views.status_bar import StatusBar
from views.tune_view import TuneView

__all__ = [
    "AppearanceView",
    "ConnectionView",
    "HeatView",
    "SettingsView",
    "StatusBar",
    "TuneView",
]
