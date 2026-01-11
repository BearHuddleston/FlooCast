"""GUI components for FlooCast."""

from floocast.gui.codec_formatter import CodecDisplayFormatter
from floocast.gui.constants import (
    APP_GIF,
    APP_ICON,
    APP_LOGO_PNG,
    APP_TITLE,
    CODEC_STRINGS,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    get_lea_state_strings,
    get_source_state_strings,
)
from floocast.gui.state import GuiState
from floocast.gui.toggle_switch import ToggleSwitchController
from floocast.gui.tray_icon import FlooCastTrayIcon

__all__ = [
    "APP_GIF",
    "APP_ICON",
    "APP_LOGO_PNG",
    "APP_TITLE",
    "CODEC_STRINGS",
    "CodecDisplayFormatter",
    "MAIN_WINDOW_HEIGHT",
    "MAIN_WINDOW_WIDTH",
    "FlooCastTrayIcon",
    "GuiState",
    "ToggleSwitchController",
    "get_lea_state_strings",
    "get_source_state_strings",
]
