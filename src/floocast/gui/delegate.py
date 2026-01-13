from __future__ import annotations

import logging
import re
import ssl
import urllib.request
from typing import TYPE_CHECKING

import certifi

from floocast.protocol.state_machine_delegate import FlooStateMachineDelegate

logger = logging.getLogger(__name__)

VERSION_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _is_valid_version(version: str) -> bool:
    """Validate version string to prevent URL injection."""
    return bool(VERSION_PATTERN.match(version)) and len(version) <= 32


def _compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings semantically.

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
    """

    def normalize(v: str) -> list[int | str]:
        parts: list[int | str] = []
        for part in re.split(r"[._-]", v):
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(part)
        return parts

    def _compare_parts(a: int | str, b: int | str) -> int:
        s1, s2 = str(a), str(b)
        if s1 < s2:
            return -1
        if s1 > s2:
            return 1
        return 0

    n1, n2 = normalize(v1), normalize(v2)
    for p1, p2 in zip(n1, n2, strict=False):
        cmp = _compare_parts(p1, p2)
        if cmp != 0:
            return cmp
    if len(n1) < len(n2):
        return -1
    if len(n1) > len(n2):
        return 1
    return 0


if TYPE_CHECKING:
    from floocast.gui.app_controller import AppController


class StateMachineDelegate(FlooStateMachineDelegate):
    def __init__(self, ctrl: AppController):
        self.ctrl = ctrl

    def deviceDetected(self, flag: bool, port: str, version: str | None = None):
        ctrl = self.ctrl
        if flag and version is not None:
            ctrl.update_status_bar(ctrl._("Use FlooGoo dongle on ") + " " + port)
            ctrl.state.first_batch = "" if re.search(r"\d+$", version) else version[-1]
            ctrl.state.firmware_variant = 1 if version.startswith("AS1") else 0
            ctrl.state.firmware_variant = (
                2 if version.startswith("AS2") else ctrl.state.firmware_variant
            )
            ctrl.state.firmware_version = version if ctrl.state.first_batch == "" else version[:-1]
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                if ctrl.state.firmware_variant == 1:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest_as1"
                elif ctrl.state.firmware_variant == 2:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest_as2"
                else:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest"
                latest = urllib.request.urlopen(url, context=ssl_context, timeout=10).read()
                latest = latest.decode("utf-8").rstrip()
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, UnicodeDecodeError, OSError):
                latest = "Unable"

            if latest != "Unable" and not _is_valid_version(latest):
                logger.warning("Invalid version string received: %r", latest)
                latest = "Unable"

            version_sizer = ctrl.version_panel_obj.sizer
            if not ctrl.state.dfu_undergoing:
                if latest == "Unable":
                    ctrl.version_panel_obj.new_firmware_url.SetLabelText(
                        ctrl._("Current firmware: ")
                        + ctrl.state.firmware_version
                        + ctrl._(", check the latest.")
                    )
                    ctrl.version_panel_obj.new_firmware_url.SetURL(
                        "https://www.flairmesh.com/Dongle/FMA120.html"
                    )
                    version_sizer.Show(ctrl.version_panel_obj.new_firmware_url)
                    version_sizer.Layout()
                elif _compare_versions(latest, ctrl.state.firmware_version) > 0:
                    version_sizer.Hide(ctrl.version_panel_obj.dfu_info)
                    ctrl.version_panel_obj.new_firmware_url.SetLabelText(
                        ctrl._("New Firmware is available")
                        + " "
                        + ctrl.state.firmware_version
                        + " -> "
                        + latest
                    )
                    ctrl.version_panel_obj.new_firmware_url.SetURL(
                        "https://www.flairmesh.com/support/FMA120_" + latest + ".zip"
                    )
                    version_sizer.Show(ctrl.version_panel_obj.new_firmware_url)
                    if ctrl.state.firmware_variant == 1:
                        ctrl.version_panel_obj.firmware_desc.SetLabelText(
                            "Auracast\u2122 " + ctrl._("Receiver")
                        )
                        version_sizer.Show(ctrl.version_panel_obj.firmware_desc)
                    elif ctrl.state.firmware_variant == 2:
                        ctrl.version_panel_obj.firmware_desc.SetLabelText(
                            "A2DP - Auracast\u2122 " + ctrl._("Relay")
                        )
                        version_sizer.Show(ctrl.version_panel_obj.firmware_desc)
                    version_sizer.Layout()
                else:
                    ctrl.version_panel_obj.dfu_info.SetLabelText(
                        ctrl._("Firmware") + " " + ctrl.state.firmware_version
                    )
                    version_sizer.Show(ctrl.version_panel_obj.dfu_info)
                    if ctrl.state.firmware_variant == 1:
                        ctrl.version_panel_obj.firmware_desc.SetLabelText(
                            "Auracast\u2122 " + ctrl._("Receiver")
                        )
                        version_sizer.Show(ctrl.version_panel_obj.firmware_desc)
                    elif ctrl.state.firmware_variant == 2:
                        ctrl.version_panel_obj.firmware_desc.SetLabelText(
                            "A2DP - Auracast\u2122 " + ctrl._("Relay")
                        )
                        version_sizer.Show(ctrl.version_panel_obj.firmware_desc)
                    version_sizer.Layout()
        else:
            ctrl.update_status_bar(ctrl._("Please insert your FlooGoo dongle"))
            ctrl.paired_device_listbox.Clear()
            ctrl.version_panel_obj.sizer.Hide(ctrl.version_panel_obj.dfu_info)
        ctrl._enable_settings_widgets(flag)

    def audioModeInd(self, mode: int):
        ctrl = self.ctrl
        ctrl.state.hw_with_analog_input = 1 if (mode & 0x80) == 0x80 else 0
        ctrl.state.audio_mode = mode & 0x03
        if ctrl.state.firmware_variant != 0:
            ctrl.paired_devices_panel.static_box.Enable(True)
        else:
            if ctrl.state.audio_mode == 0:
                ctrl.audio_mode_panel.high_quality_radio.SetValue(True)
                ctrl.broadcast_panel.static_box.Disable()
            elif ctrl.state.audio_mode == 1:
                ctrl.audio_mode_panel.gaming_radio.SetValue(True)
                ctrl.broadcast_panel.static_box.Disable()
            elif ctrl.state.audio_mode == 2:
                ctrl.audio_mode_panel.broadcast_radio.SetValue(True)
                ctrl.broadcast_panel.static_box.Enable()
            ctrl._audio_mode_sel_set(mode)

    def sourceStateInd(self, state: int):
        ctrl = self.ctrl
        ctrl.audio_mode_panel.dongle_state_text.SetLabelText(ctrl.source_state_str[state])
        ctrl.audio_mode_panel.dongle_state_sizer.Layout()

    def leAudioStateInd(self, state: int):
        ctrl = self.ctrl
        ctrl.audio_mode_panel.lea_state_text.SetLabelText(ctrl.lea_state_str[state])
        ctrl.audio_mode_panel.lea_state_sizer.Layout()

    def preferLeaInd(self, state: int):
        self.ctrl.prefer_lea_toggle.set(state == 1, True)

    def broadcastModeInd(self, state: int):
        ctrl = self.ctrl
        ctrl.broadcast_high_quality_toggle.set(state & 4 == 4, True)
        ctrl.public_broadcast_toggle.set(state & 2 == 2, True)
        ctrl.broadcast_encrypt_toggle.set(state & 1 == 1, True)
        ctrl.broadcast_stop_on_idle_toggle.set(state & 8 == 8, True)
        broadcast_latency = (state & 0x30) >> 4
        if broadcast_latency == 1:
            ctrl.broadcast_panel.latency_lowest_radio.SetValue(True)
        elif broadcast_latency == 2:
            ctrl.broadcast_panel.latency_lower_radio.SetValue(True)
        elif broadcast_latency == 3:
            ctrl.broadcast_panel.latency_default_radio.SetValue(True)
        if broadcast_latency == 0:
            ctrl.broadcast_panel.latency_panel.Disable()
            ctrl.broadcast_panel.broadcast_stop_on_idle_checkbox.Disable()
            ctrl.broadcast_panel.broadcast_stop_on_idle_button.Disable()
        else:
            ctrl.broadcast_panel.latency_panel.Enable()
            ctrl.broadcast_panel.broadcast_stop_on_idle_checkbox.Enable()
            ctrl.broadcast_panel.broadcast_stop_on_idle_button.Enable()

    def broadcastNameInd(self, name):
        self.ctrl.broadcast_panel.broadcast_name_entry.SetValue(name)

    def pairedDevicesUpdateInd(self, pairedDevices):
        ctrl = self.ctrl
        ctrl.paired_device_listbox.Clear()
        i = 0
        while i < len(pairedDevices):
            ctrl.paired_device_listbox.Append(pairedDevices[i])
            i = i + 1
        ctrl._update_new_pairing_button_state()

    def audioCodecInUseInd(
        self, codec, rssi, rate, spkSampleRate, micSampleRate, sduInt, transportDelay, presentDelay
    ):
        ctrl = self.ctrl
        label = ctrl.codec_formatter.format(
            codec, rssi, rate, spkSampleRate, micSampleRate, sduInt, transportDelay, presentDelay
        )
        ctrl.audio_mode_panel.codec_in_use_text.SetLabelText(label)
        ctrl.audio_mode_panel.codec_in_use_sizer.Layout()

    def ledEnabledInd(self, enabled):
        self.ctrl.led_toggle.set(enabled, True)

    def aptxLosslessEnabledInd(self, enabled):
        self.ctrl.aptx_lossless_toggle.set(enabled, True)

    def gattClientEnabledInd(self, enabled):
        self.ctrl.gatt_client_toggle.set(enabled, True)

    def audioSourceInd(self, enabled):
        self.ctrl.usb_input_toggle.set(enabled, True)

    def connectionErrorInd(self, error: str):
        ctrl = self.ctrl
        if error == "port_busy":
            ctrl.update_status_bar(
                ctrl._("Port is busy - close other applications using the dongle")
            )
        else:
            ctrl.update_status_bar(ctrl._("Connection error - please reconnect the dongle"))
