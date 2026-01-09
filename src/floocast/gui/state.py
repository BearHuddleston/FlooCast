"""GUI state management for FlooCast."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GuiState:
    """Holds mutable GUI state that panels need to share."""

    audio_mode: int | None = None
    prefer_lea_enable: bool = False
    start_minimized: bool = False

    public_broadcast_enable: bool = False
    broadcast_high_quality_enable: bool = False
    broadcast_encrypt_enable: bool = False
    broadcast_stop_on_idle_enable: bool = False

    usb_input_enable: bool = False
    led_enable: bool = False
    aptx_lossless_enable: bool = False
    gatt_client_enable: bool = False

    dfu_undergoing: bool = False
    firmware_version: str | None = None
    firmware_variant: str | None = None
    first_batch: bool = True

    paired_devices: list = field(default_factory=list)

    looper: Any = None
    input_devices: list = field(default_factory=list)
    saved_device: str | None = None
    saved_name: str | None = None
    saved_blocksize: int | None = None
