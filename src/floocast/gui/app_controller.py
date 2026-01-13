import gettext
import logging
import os
import re
import sys

import wx

from floocast.audio.aux_input import FlooAuxInput
from floocast.dfu_thread import FlooDfuThread
from floocast.gui.codec_formatter import CodecDisplayFormatter
from floocast.gui.constants import (
    APP_ICON,
    APP_LOGO_PNG,
    APP_TITLE,
    CODEC_STRINGS,
    MAIN_WINDOW_HEIGHT,
    MAIN_WINDOW_WIDTH,
    OFF_SWITCH,
    ON_SWITCH,
    get_lea_state_strings,
    get_source_state_strings,
)
from floocast.gui.context_menu import PairedDeviceMenu
from floocast.gui.delegate import StateMachineDelegate
from floocast.gui.panels import (
    AudioModePanel,
    BroadcastPanel,
    PairedDevicesPanel,
    SettingsPanel,
    VersionPanel,
    WindowPanel,
)
from floocast.gui.state import GuiState
from floocast.gui.toggle_switch import ToggleSwitchController
from floocast.gui.tray_icon import FlooCastTrayIcon
from floocast.protocol.state_machine import FlooStateMachine
from floocast.settings import FlooSettings

logger = logging.getLogger(__name__)


class AppController:
    def __init__(self):
        self.app = wx.App(False)
        self.settings = FlooSettings()

        self.state = GuiState(
            start_minimized=bool(self.settings.get_item("start_minimized") or False),
            saved_blocksize=self.settings.get_item("aux_blocksize"),
            saved_device=self.settings.get_item("aux_input"),
            saved_name=(self.settings.get_item("aux_input") or {}).get("name", "None"),
        )

        self._setup_localization()
        self._setup_frame()
        self._setup_panels()
        self._setup_layout()
        self._setup_state_machine()

    def _setup_localization(self):
        user_locale = wx.Locale.GetSystemLanguage()
        lan = wx.Locale.GetLanguageInfo(user_locale).CanonicalName

        app_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        localedir = app_path + os.sep + "locales"
        translate = gettext.translation("messages", localedir, languages=[lan], fallback=True)
        translate.install()
        self._ = translate.gettext

        self.source_state_str = get_source_state_strings(self._)
        self.lea_state_str = get_lea_state_strings(self._)
        self.codec_formatter = CodecDisplayFormatter(CODEC_STRINGS, self._)
        self.app_path = app_path

    def _setup_frame(self):
        self.frame = wx.Frame(
            None, wx.ID_ANY, "FlooCast", size=wx.Size(MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        )
        self.frame.SetIcon(wx.Icon(APP_ICON))

        self.status_bar = self.frame.CreateStatusBar(name=self._(APP_TITLE))
        self.status_bar.SetStatusText(self._("Initializing"))

        self.on_bitmap = wx.Bitmap(ON_SWITCH)
        self.off_bitmap = wx.Bitmap(OFF_SWITCH)

        self.app_panel = wx.Panel(self.frame)
        self.app_sizer = wx.FlexGridSizer(2, 2, vgap=2, hgap=4)

        self.tray_icon = FlooCastTrayIcon(self.frame, APP_ICON, self._)
        self.tray_icon.run()
        self.frame.Bind(wx.EVT_CLOSE, self._on_quit_window)

    def _setup_panels(self):
        self._setup_audio_mode_panel()
        self._setup_window_panel()
        self._setup_broadcast_panel()
        self._setup_paired_devices_panel()
        self._setup_settings_panel()
        self._setup_version_panel()

    def _setup_audio_mode_panel(self):
        self.audio_mode_panel = AudioModePanel(
            self.app_panel, self._, self.off_bitmap, CODEC_STRINGS
        )
        self.audio_mode_panel.upper_panel.Bind(wx.EVT_RADIOBUTTON, self._on_audio_mode_select)

        self.prefer_lea_toggle = ToggleSwitchController(
            self.audio_mode_panel.prefer_lea_button,
            self.audio_mode_panel.prefer_lea_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("Prefer using LE audio for dual-mode devices"),
            lambda enable: self.state_machine.setPreferLea(enable),
            extra_action=lambda enable: self.new_pairing_button.Enable(
                not (enable and self.paired_device_listbox.GetCount() > 0)
            ),
        )
        self.audio_mode_panel.lower_panel.Bind(
            wx.EVT_CHECKBOX,
            self.prefer_lea_toggle.on_checkbox_click,
            self.audio_mode_panel.prefer_lea_checkbox,
        )
        self.audio_mode_panel.prefer_lea_button.Bind(
            wx.EVT_BUTTON, self.prefer_lea_toggle.on_button_click
        )

    def _setup_window_panel(self):
        self.window_panel = WindowPanel(
            self.app_panel, self._, self.on_bitmap, self.off_bitmap, self.state.start_minimized
        )
        self.window_panel.minimize_button.Bind(wx.EVT_BUTTON, self._on_hide_window)
        self.window_panel.quit_button.Bind(wx.EVT_BUTTON, self._on_quit_window)
        self.window_panel.static_box.Bind(
            wx.EVT_CHECKBOX,
            self._on_start_minimized_checkbox,
            self.window_panel.start_minimized_checkbox,
        )
        self.window_panel.start_minimized_button.Bind(
            wx.EVT_BUTTON, self._on_start_minimized_button
        )

    def _setup_broadcast_panel(self):
        self.broadcast_and_paired_panel = wx.Panel(self.app_panel)
        self.broadcast_and_paired_sizer = wx.BoxSizer(wx.VERTICAL)

        self.state.looper = FlooAuxInput(blocksize=self.state.saved_blocksize)
        self.state.input_devices = self.state.looper.list_additional_inputs()
        self.state.name_input_devices = {d["name"]: d for d in self.state.input_devices}

        self.broadcast_panel = BroadcastPanel(
            self.broadcast_and_paired_panel, self._, self.off_bitmap, self.state.input_devices
        )

        self.public_broadcast_toggle = ToggleSwitchController(
            self.broadcast_panel.public_broadcast_button,
            self.broadcast_panel.public_broadcast_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("Public broadcast"),
            lambda enable: self.state_machine.setPublicBroadcast(enable),
        )
        self.broadcast_panel.switch_panel.Bind(
            wx.EVT_CHECKBOX,
            self.public_broadcast_toggle.on_checkbox_click,
            self.broadcast_panel.public_broadcast_checkbox,
        )
        self.broadcast_panel.public_broadcast_button.Bind(
            wx.EVT_BUTTON, self.public_broadcast_toggle.on_button_click
        )

        self.broadcast_high_quality_toggle = ToggleSwitchController(
            self.broadcast_panel.broadcast_high_quality_button,
            self.broadcast_panel.broadcast_high_quality_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("Broadcast high-quality music, otherwise, voice"),
            lambda enable: self.state_machine.setBroadcastHighQuality(enable),
        )
        self.broadcast_panel.switch_panel.Bind(
            wx.EVT_CHECKBOX,
            self.broadcast_high_quality_toggle.on_checkbox_click,
            self.broadcast_panel.broadcast_high_quality_checkbox,
        )
        self.broadcast_panel.broadcast_high_quality_button.Bind(
            wx.EVT_BUTTON, self.broadcast_high_quality_toggle.on_button_click
        )

        self.broadcast_encrypt_toggle = ToggleSwitchController(
            self.broadcast_panel.broadcast_encrypt_button,
            self.broadcast_panel.broadcast_encrypt_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("Encrypt broadcast; please set a key first"),
            lambda enable: self.state_machine.setBroadcastEncrypt(enable),
        )
        self.broadcast_panel.switch_panel.Bind(
            wx.EVT_CHECKBOX,
            self.broadcast_encrypt_toggle.on_checkbox_click,
            self.broadcast_panel.broadcast_encrypt_checkbox,
        )
        self.broadcast_panel.broadcast_encrypt_button.Bind(
            wx.EVT_BUTTON, self.broadcast_encrypt_toggle.on_button_click
        )

        self.broadcast_stop_on_idle_toggle = ToggleSwitchController(
            self.broadcast_panel.broadcast_stop_on_idle_button,
            self.broadcast_panel.broadcast_stop_on_idle_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("Stop broadcasting immediately when USB audio playback ends"),
            lambda enable: self.state_machine.setBroadcastStopOnIdle(enable),
        )
        self.broadcast_panel.switch_panel.Bind(
            wx.EVT_CHECKBOX,
            self.broadcast_stop_on_idle_toggle.on_checkbox_click,
            self.broadcast_panel.broadcast_stop_on_idle_checkbox,
        )
        self.broadcast_panel.broadcast_stop_on_idle_button.Bind(
            wx.EVT_BUTTON, self.broadcast_stop_on_idle_toggle.on_button_click
        )

        self.broadcast_panel.broadcast_name_entry.Bind(
            wx.EVT_SEARCHCTRL_SEARCH_BTN, self._on_broadcast_name_entry
        )
        self.broadcast_panel.broadcast_name_entry.Bind(
            wx.EVT_KILL_FOCUS, self._on_broadcast_name_entry
        )
        self.broadcast_panel.broadcast_key_entry.Bind(
            wx.EVT_SEARCHCTRL_SEARCH_BTN, self._on_broadcast_key_entry
        )
        self.broadcast_panel.broadcast_key_entry.Bind(
            wx.EVT_KILL_FOCUS, self._on_broadcast_key_entry
        )
        self.broadcast_panel.latency_radio_panel.Bind(
            wx.EVT_RADIOBUTTON, self._on_broadcast_latency_select
        )
        self.broadcast_panel.aux_input_combo.Bind(wx.EVT_COMBOBOX, self._on_input_device_select)

    def _setup_paired_devices_panel(self):
        self.paired_devices_panel = PairedDevicesPanel(self.broadcast_and_paired_panel, self._)
        self.new_pairing_button = self.paired_devices_panel.new_pairing_button
        self.clear_all_button = self.paired_devices_panel.clear_all_button
        self.paired_device_listbox = self.paired_devices_panel.device_listbox

        self.new_pairing_button.Bind(wx.EVT_BUTTON, self._on_new_pairing)
        self.clear_all_button.Bind(wx.EVT_BUTTON, self._on_clear_all)
        self.paired_device_listbox.Bind(wx.EVT_CONTEXT_MENU, self._on_context_menu)

        self.broadcast_and_paired_sizer.Add(
            self.broadcast_panel.sizer, proportion=0, flag=wx.EXPAND
        )
        self.broadcast_and_paired_sizer.Add(
            self.paired_devices_panel.sizer, proportion=1, flag=wx.EXPAND
        )
        self.broadcast_and_paired_panel.SetSizer(self.broadcast_and_paired_sizer)

    def _setup_settings_panel(self):
        self.settings_box = wx.StaticBox(self.app_panel, wx.ID_ANY, self._("Settings"))
        self.settings_box_sizer = wx.StaticBoxSizer(self.settings_box, wx.VERTICAL)
        self.settings_panel_obj = SettingsPanel(
            self.settings_box, self._, self.on_bitmap, self.off_bitmap
        )

        self.usb_input_toggle = ToggleSwitchController(
            self.settings_panel_obj.usb_input_button,
            self.settings_panel_obj.usb_input_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("USB Audio Input"),
            lambda enable: self.state_machine.enableUsbInput(enable),
        )
        self.settings_panel_obj.panel.Bind(
            wx.EVT_CHECKBOX,
            self.usb_input_toggle.on_checkbox_click,
            self.settings_panel_obj.usb_input_checkbox,
        )
        self.settings_panel_obj.usb_input_button.Bind(
            wx.EVT_BUTTON, self.usb_input_toggle.on_button_click
        )

        self.led_toggle = ToggleSwitchController(
            self.settings_panel_obj.led_button,
            self.settings_panel_obj.led_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("LED"),
            lambda enable: self.state_machine.enableLed(enable),
        )
        self.settings_panel_obj.panel.Bind(
            wx.EVT_CHECKBOX,
            self.led_toggle.on_checkbox_click,
            self.settings_panel_obj.led_checkbox,
        )
        self.settings_panel_obj.led_button.Bind(wx.EVT_BUTTON, self.led_toggle.on_button_click)

        self.aptx_lossless_toggle = ToggleSwitchController(
            self.settings_panel_obj.aptx_lossless_button,
            self.settings_panel_obj.aptx_lossless_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            self._("aptX Lossless"),
            lambda enable: self.state_machine.enableAptxLossless(enable),
        )
        self.settings_panel_obj.panel.Bind(
            wx.EVT_CHECKBOX,
            self.aptx_lossless_toggle.on_checkbox_click,
            self.settings_panel_obj.aptx_lossless_checkbox,
        )
        self.settings_panel_obj.aptx_lossless_button.Bind(
            wx.EVT_BUTTON, self.aptx_lossless_toggle.on_button_click
        )

        self.gatt_client_toggle = ToggleSwitchController(
            self.settings_panel_obj.gatt_client_button,
            self.settings_panel_obj.gatt_client_checkbox,
            self.on_bitmap,
            self.off_bitmap,
            self._,
            "GATT " + self._("Client"),
            lambda enable: self.state_machine.enableGattClient(enable),
        )
        self.settings_panel_obj.panel.Bind(
            wx.EVT_CHECKBOX,
            self.gatt_client_toggle.on_checkbox_click,
            self.settings_panel_obj.gatt_client_checkbox,
        )
        self.settings_panel_obj.gatt_client_button.Bind(
            wx.EVT_BUTTON, self.gatt_client_toggle.on_button_click
        )

    def _setup_version_panel(self):
        self.version_panel_obj = VersionPanel(self.settings_box, APP_LOGO_PNG, self._)
        self.dfu_info_bind = False

        self.settings_box_sizer.Add(self.settings_panel_obj.panel, proportion=1, flag=wx.EXPAND)
        self.settings_box_sizer.Add(
            self.version_panel_obj.panel, proportion=3, flag=wx.TOP, border=4
        )

    def _setup_layout(self):
        self.app_sizer.Add(self.audio_mode_panel.sizer, flag=wx.EXPAND | wx.LEFT, border=4)
        self.app_sizer.Add(self.window_panel.sizer, flag=wx.EXPAND | wx.RIGHT, border=4)
        self.app_sizer.Add(self.broadcast_and_paired_panel, flag=wx.EXPAND | wx.LEFT, border=4)
        self.app_sizer.Add(self.settings_box_sizer, flag=wx.EXPAND | wx.RIGHT, border=4)

        self.app_sizer.AddGrowableRow(0, 0)
        self.app_sizer.AddGrowableRow(1, 1)
        self.app_sizer.AddGrowableCol(0, 1)
        self.app_sizer.AddGrowableCol(1, 0)

        self.app_panel.SetSizer(self.app_sizer)
        self._enable_settings_widgets(False)

    def _setup_state_machine(self):
        delegate = StateMachineDelegate(self)
        self.state_machine = FlooStateMachine(delegate)
        self.state_machine.daemon = True
        self.state_machine.start()

    def run(self):
        if self.state.start_minimized:
            self.frame.Iconize(True)
            self.frame.Hide()
        else:
            self.frame.Show(True)
        self.app.MainLoop()

    def update_status_bar(self, info: str):
        self.status_bar.SetStatusText(info)

    def _aux_input_broadcast_enable(self, enable):
        if enable and self.state.saved_name in self.state.name_input_devices:
            self.broadcast_panel.aux_input_combo.SetValue(self.state.saved_name)
            self.state.looper.set_input(self.state.saved_device)
        else:
            self.state.looper.set_input(None)

    def _audio_mode_sel_set(self, mode):
        settings_sizer = self.settings_panel_obj.sizer
        if self.state.hw_with_analog_input:
            settings_sizer.Show(self.settings_panel_obj.usb_input_checkbox)
            settings_sizer.Show(self.settings_panel_obj.usb_input_button)
        else:
            settings_sizer.Hide(self.settings_panel_obj.usb_input_checkbox)
            settings_sizer.Hide(self.settings_panel_obj.usb_input_button)
        if self.state.audio_mode == 0:
            settings_sizer.Show(self.settings_panel_obj.aptx_lossless_checkbox)
            settings_sizer.Show(self.settings_panel_obj.aptx_lossless_button)
            settings_sizer.Hide(self.settings_panel_obj.gatt_client_checkbox)
            settings_sizer.Hide(self.settings_panel_obj.gatt_client_button)
            self.broadcast_panel.static_box.Disable()
        elif self.state.audio_mode == 1:
            settings_sizer.Hide(self.settings_panel_obj.aptx_lossless_checkbox)
            settings_sizer.Hide(self.settings_panel_obj.aptx_lossless_button)
            settings_sizer.Hide(self.settings_panel_obj.gatt_client_checkbox)
            settings_sizer.Hide(self.settings_panel_obj.gatt_client_button)
            self.broadcast_panel.static_box.Disable()
        elif self.state.audio_mode == 2:
            settings_sizer.Hide(self.settings_panel_obj.aptx_lossless_checkbox)
            settings_sizer.Hide(self.settings_panel_obj.aptx_lossless_button)
            settings_sizer.Show(self.settings_panel_obj.gatt_client_checkbox)
            settings_sizer.Show(self.settings_panel_obj.gatt_client_button)
            self.broadcast_panel.static_box.Enable()
        self._aux_input_broadcast_enable(self.state.audio_mode == 2)
        settings_sizer.Layout()

    def _on_audio_mode_select(self, event):
        selected_label = event.GetEventObject().GetLabel()
        if selected_label == self.audio_mode_panel.high_quality_radio.GetLabel():
            self.state.audio_mode = 0
        elif selected_label == self.audio_mode_panel.gaming_radio.GetLabel():
            self.state.audio_mode = 1
        else:
            self.state.audio_mode = 2
        self._audio_mode_sel_set(
            self.state.audio_mode + (0x80 if self.state.hw_with_analog_input else 0x00)
        )
        self.settings_panel_obj.sizer.Layout()
        self.state_machine.setAudioMode(self.state.audio_mode)

    def _on_quit_window(self, event):
        if self.state.looper:
            self.state.looper.stop()
        if hasattr(self, 'state_machine') and self.state_machine:
            if hasattr(self.state_machine, 'inf') and self.state_machine.inf:
                if hasattr(self.state_machine.inf, 'stop'):
                    self.state_machine.inf.stop()
        self.tray_icon.Destroy()
        self.frame.Destroy()

    def _on_hide_window(self, event):
        if self.frame.IsShown():
            self.frame.Hide()

    def _start_minimized_set(self, enable):
        self.state.start_minimized = enable
        self.settings.set_item("start_minimized", enable)
        self.settings.save()
        self.window_panel.start_minimized_button.SetBitmap(
            self.on_bitmap if self.state.start_minimized else self.off_bitmap
        )
        self.window_panel.start_minimized_button.SetToolTip(
            self._("Toggle switch for")
            + " "
            + self._("Start Minimized")
            + " "
            + (self._("On") if self.state.start_minimized else self._("Off"))
        )

    def _on_start_minimized_button(self, event):
        self.window_panel.start_minimized_checkbox.SetValue(not self.state.start_minimized)
        self._start_minimized_set(not self.state.start_minimized)

    def _on_start_minimized_checkbox(self, event):
        self._start_minimized_set(not self.state.start_minimized)

    def _on_broadcast_name_entry(self, event):
        name = self.broadcast_panel.broadcast_name_entry.GetValue()
        name_bytes = name.encode("utf-8")
        if 0 < len(name_bytes) < 31:
            self.state_machine.setBroadcastName(name)
        event.Skip()

    def _on_broadcast_key_entry(self, event):
        key = self.broadcast_panel.broadcast_key_entry.GetValue()
        key_bytes = key.encode("utf-8")
        if 0 < len(key_bytes) < 17:
            self.state_machine.setBroadcastKey(key)
        event.Skip()

    def _on_broadcast_latency_select(self, event):
        selected_label = event.GetEventObject().GetLabel()
        if selected_label == self.broadcast_panel.latency_lowest_radio.GetLabel():
            mode = 1
        elif selected_label == self.broadcast_panel.latency_lower_radio.GetLabel():
            mode = 2
        else:
            mode = 3
        self.state_machine.setBroadcastLatency(mode)

    def _on_input_device_select(self, event):
        self.state.saved_name = self.broadcast_panel.aux_input_combo.GetValue()
        dev = self.state.name_input_devices.get(self.state.saved_name)
        if dev is None:
            return
        self.state.saved_device = self.state.looper.serialize_input_device(dev)
        self.settings.set_item("aux_input", self.state.saved_device)
        self.settings.save()

        self.state.looper.set_input(self.state.saved_device)
        logger.info("User chose: %s -> applied and saved", self.state.saved_name)

    def _on_new_pairing(self, event):
        self.state_machine.setNewPairing()

    def _on_clear_all(self, event):
        self.state_machine.clearAllPairedDevices()

    def _on_context_menu(self, event):
        listbox = event.GetEventObject()
        pos = listbox.ScreenToClient(event.GetPosition())
        item = listbox.HitTest(pos)
        if item != wx.NOT_FOUND:
            listbox.SetSelection(item)
        listbox.PopupMenu(PairedDeviceMenu(listbox, self.state_machine, self._), pos)

    def _update_dfu_info(self, dfu_state: int):
        version_sizer = self.version_panel_obj.sizer
        if dfu_state == FlooDfuThread.DFU_STATE_DONE:
            self.audio_mode_panel.static_box.Enable()
            self.window_panel.static_box.Enable()
            self.broadcast_and_paired_panel.Enable()
            self.settings_panel_obj.panel.Enable()
            self.version_panel_obj.dfu_info.SetLabelText(
                self._("Firmware") + " " + self.state.firmware_version
            )
            self.state.dfu_undergoing = False
        elif dfu_state == FlooDfuThread.DFU_ERROR_NOT_SUPPORTED:
            self.version_panel_obj.dfu_info.SetLabelText(self._("DFU not supported on Linux"))
            self.window_panel.static_box.Enable()
            self.state.dfu_undergoing = False
        elif dfu_state > FlooDfuThread.DFU_STATE_DONE:
            self.version_panel_obj.dfu_info.SetLabelText(self._("Upgrade error"))
            self.window_panel.static_box.Enable()
            self.state.dfu_undergoing = True
        else:
            version_sizer.Hide(self.version_panel_obj.new_firmware_url)
            version_sizer.Show(self.version_panel_obj.dfu_info)
            self.version_panel_obj.dfu_info.SetLabelText(
                self._("Upgrade progress") + (" %d" % dfu_state) + "%"
            )
            if not self.state.dfu_undergoing:
                self.audio_mode_panel.static_box.Disable()
                self.window_panel.static_box.Disable()
                self.broadcast_and_paired_panel.Disable()
                self.settings_panel_obj.panel.Disable()
                self.state.dfu_undergoing = True
        version_sizer.Layout()

    def _on_dfu_button(self, event):
        with wx.FileDialog(
            self.frame,
            self._("Open Firmware file"),
            wildcard="Bin files (*.bin)|*.bin",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            filename = file_dialog.GetPath()
            if filename:
                os.chdir(self.app_path)
                file_basename = os.path.splitext(filename)[0]
                if not re.search(r"\d+$", file_basename):
                    file_basename = file_basename[:-1]
                file_basename += self.state.first_batch
                filename = file_basename + ".bin"
                if os.path.isfile(filename):
                    dfu_thread = FlooDfuThread([self.app_path, filename], self._update_dfu_info)
                    dfu_thread.start()

    def _enable_settings_widgets(self, enable: bool):
        if self.state.dfu_undergoing:
            return
        if enable:
            if self.state.firmware_variant != 0:
                self.audio_mode_panel.static_box.Disable()
            else:
                self.audio_mode_panel.static_box.Enable()
            self.broadcast_and_paired_panel.Enable()
            self.settings_panel_obj.panel.Enable()
            self.paired_devices_panel.static_box.Enable()
            self.version_panel_obj.third_party_link.Refresh()
            self.version_panel_obj.support_link.Refresh()
        else:
            self.audio_mode_panel.static_box.Disable()
            self.broadcast_and_paired_panel.Disable()
            self.settings_panel_obj.panel.Disable()
