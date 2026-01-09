"""GUI constants and configuration."""

APP_ICON = "FlooCastApp.ico"
APP_GIF = "FlooCastApp.gif"
APP_TITLE = "FlooCast"
APP_LOGO_PNG = "FlooCastHeader.png"

MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 700

CODEC_STRINGS = [
    "None",
    "CVSD",
    "mSBC/WBS",
    "SBC",
    "aptX\u2122",
    "aptX\u2122 HD",
    "aptX\u2122 Adaptive",
    "LC3",
    "aptX\u2122 Adaptive",
    "aptX\u2122 Lite",
    "aptX\u2122 Lossless",
    "aptX\u2122 Voice",
]


def get_source_state_strings(translate_func):
    _ = translate_func
    return [
        _("Initializing"),
        _("Idle"),
        _("Pairing"),
        _("Connecting"),
        _("Connected"),
        _("Audio starting"),
        _("Audio streaming"),
        _("Audio stopping"),
        _("Disconnecting"),
        _("Voice starting"),
        _("Voice streaming"),
        _("Voice stopping"),
    ]


def get_lea_state_strings(translate_func):
    _ = translate_func
    return [
        _("Disconnected"),
        _("Connected"),
        _("Unicast starting"),
        _("Unicast streaming"),
        _("Broadcast starting"),
        _("Broadcast streaming"),
        _("Streaming stopping"),
    ]
