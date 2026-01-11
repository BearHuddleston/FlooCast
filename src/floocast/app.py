# !/usr/bin/env python
import gettext
import logging
import os
import re
import ssl
import sys
import urllib.request

import certifi
import wx

from floocast.audio.aux_input import FlooAuxInput
from floocast.dfu_thread import FlooDfuThread
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
from floocast.protocol.state_machine_delegate import FlooStateMachineDelegate
from floocast.settings import FlooSettings

logger = logging.getLogger(__name__)

appIcon = APP_ICON
appGif = APP_GIF
appTitle = APP_TITLE
appLogoPng = APP_LOGO_PNG
codecStr = CODEC_STRINGS
mainWindowWidth = MAIN_WINDOW_WIDTH
mainWindowHeight = MAIN_WINDOW_HEIGHT
userLocale = wx.Locale.GetSystemLanguage()
lan = wx.Locale.GetLanguageInfo(userLocale).CanonicalName

# Set the local directory
app_path = os.path.abspath(os.path.dirname(sys.argv[0]))
localedir = app_path + os.sep + "locales"
# Set up your magic function
translate = gettext.translation("messages", localedir, languages=[lan], fallback=True)
translate.install()
_ = translate.gettext

sourceStateStr = get_source_state_strings(_)
leaStateStr = get_lea_state_strings(_)
codecFormatter = CodecDisplayFormatter(codecStr, _)

# create root window
app = wx.App(False)
settings = FlooSettings()

state = GuiState(
    start_minimized=bool(settings.get_item("start_minimized") or False),
    saved_blocksize=settings.get_item("aux_blocksize"),
    saved_device=settings.get_item("aux_input"),
    saved_name=(settings.get_item("aux_input") or {}).get("name", "None"),
)

appFrame = wx.Frame(None, wx.ID_ANY, "FlooCast", size=wx.Size(mainWindowWidth, mainWindowHeight))
appFrame.SetIcon(wx.Icon(app_path + os.sep + appIcon))

statusBar = appFrame.CreateStatusBar(name=_("Status Bar"))
statusBar.SetStatusText(_("Initializing"))


# Update the status bar
def update_status_bar(info: str):
    global statusBar
    statusBar.SetStatusText(info)


# Define On/Off Images
on = wx.Bitmap(
    app_path + os.sep + "onS.png",
)
off = wx.Bitmap(app_path + os.sep + "offS.png")

appPanel = wx.Panel(appFrame)
appSizer = wx.FlexGridSizer(2, 2, vgap=2, hgap=4)

# Audio mode panel
audioModePanel = AudioModePanel(appPanel, _, off, codecStr)
audioModeSb = audioModePanel.static_box
audioModeSbSizer = audioModePanel.sizer
audioModeUpperPanel = audioModePanel.upper_panel
audioModeUpperPanelSizer = audioModePanel.upper_sizer
audioModeHighQualityRadioButton = audioModePanel.high_quality_radio
audioModeGamingRadioButton = audioModePanel.gaming_radio
audioModeBroadcastRadioButton = audioModePanel.broadcast_radio
dongleStateSb = audioModePanel.dongle_state_box
dongleStateSbSizer = audioModePanel.dongle_state_sizer
dongleStateText = audioModePanel.dongle_state_text
leaStateSb = audioModePanel.lea_state_box
leaStateSbSizer = audioModePanel.lea_state_sizer
leaStateText = audioModePanel.lea_state_text
codecInUseSb = audioModePanel.codec_in_use_box
codecInUseSbSizer = audioModePanel.codec_in_use_sizer
codecInUseText = audioModePanel.codec_in_use_text
audioModeLowerPanel = audioModePanel.lower_panel
audioModeLowerPanelSizer = audioModePanel.lower_sizer
preferLeaCheckBox = audioModePanel.prefer_lea_checkbox
preferLeButton = audioModePanel.prefer_lea_button


def aux_input_broadcast_enable(enable):
    if enable and state.saved_name in state.name_input_devices:
        auxInputComboBox.SetValue(state.saved_name)
        state.looper.set_input(state.saved_device)
    else:
        state.looper.set_input(None)


def audio_mode_sel_set(mode):
    if state.hw_with_analog_input:
        settingsPanelSizer.Show(usbInputCheckBox)
        settingsPanelSizer.Show(usbInputEnableButton)
    else:
        settingsPanelSizer.Hide(usbInputCheckBox)
        settingsPanelSizer.Hide(usbInputEnableButton)
    if state.audio_mode == 0:
        settingsPanelSizer.Show(aptxLosslessCheckBox)
        settingsPanelSizer.Show(aptxLosslessEnableButton)
        settingsPanelSizer.Hide(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Hide(gattClientWithBroadcastEnableButton)
        leBroadcastSb.Disable()
    elif state.audio_mode == 1:
        settingsPanelSizer.Hide(aptxLosslessCheckBox)
        settingsPanelSizer.Hide(aptxLosslessEnableButton)
        settingsPanelSizer.Hide(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Hide(gattClientWithBroadcastEnableButton)
        leBroadcastSb.Disable()
    elif state.audio_mode == 2:
        settingsPanelSizer.Hide(aptxLosslessCheckBox)
        settingsPanelSizer.Hide(aptxLosslessEnableButton)
        settingsPanelSizer.Show(gattClientWithBroadcastCheckBox)
        settingsPanelSizer.Show(gattClientWithBroadcastEnableButton)
        leBroadcastSb.Enable()
    aux_input_broadcast_enable(state.audio_mode == 2)
    settingsPanelSizer.Layout()


def audio_mode_sel(event):
    selectedLabel = event.GetEventObject().GetLabel()
    if selectedLabel == audioModeHighQualityRadioButton.GetLabel():
        state.audio_mode = 0
    elif selectedLabel == audioModeGamingRadioButton.GetLabel():
        state.audio_mode = 1
    else:
        state.audio_mode = 2
    audio_mode_sel_set(state.audio_mode + (0x80 if state.hw_with_analog_input else 0x00))
    settingsPanelSizer.Layout()
    flooSm.setAudioMode(state.audio_mode)


audioModeUpperPanel.Bind(wx.EVT_RADIOBUTTON, audio_mode_sel)

preferLeaToggle = ToggleSwitchController(
    preferLeButton,
    preferLeaCheckBox,
    on,
    off,
    _,
    _("Prefer using LE audio for dual-mode devices"),
    lambda enable: flooSm.setPreferLea(enable),
    extra_action=lambda enable: newPairingButton.Enable(
        not (enable and pairedDeviceListbox.GetCount() > 0)
    ),
)
audioModeLowerPanel.Bind(wx.EVT_CHECKBOX, preferLeaToggle.on_checkbox_click, preferLeaCheckBox)
preferLeButton.Bind(wx.EVT_BUTTON, preferLeaToggle.on_button_click)


# Window panel


def quit_all():
    appFrame.Close()


# Define a function for quit the window
def quit_window(event):
    windowIcon.Destroy()
    appFrame.Destroy()


# Hide the window and show on the system taskbar
def hide_window(event):
    if appFrame.IsShown():
        appFrame.Hide()


windowIcon = FlooCastTrayIcon(appFrame, app_path + os.sep + appIcon, _)
windowIcon.run()
appFrame.Bind(wx.EVT_CLOSE, quit_window)

windowPanel = WindowPanel(appPanel, _, on, off, state.start_minimized)
windowSb = windowPanel.static_box
windowSbSizer = windowPanel.sizer
minimizeButton = windowPanel.minimize_button
quitButton = windowPanel.quit_button
startMinimizedPanel = windowPanel.start_minimized_panel
startMinimizedPanelSizer = windowPanel.start_minimized_sizer
startMinimizedCheckBox = windowPanel.start_minimized_checkbox
startMinimizedButton = windowPanel.start_minimized_button
minimizeButton.Bind(wx.EVT_BUTTON, hide_window)
quitButton.Bind(wx.EVT_BUTTON, quit_window)


def start_minimized_enable_switch_set(enable):
    state.start_minimized = enable
    settings.set_item("start_minimized", enable)
    settings.save()
    startMinimizedButton.SetBitmap(on if state.start_minimized else off)
    startMinimizedButton.SetToolTip(
        _("Toggle switch for")
        + " "
        + _("Start Minimized")
        + " "
        + (_("On") if state.start_minimized else _("Off"))
    )


def start_minimized_enable_button(event):
    startMinimizedCheckBox.SetValue(not state.start_minimized)
    start_minimized_enable_switch_set(not state.start_minimized)


def start_minimized_enable_switch(event):
    start_minimized_enable_switch_set(not state.start_minimized)


windowSb.Bind(wx.EVT_CHECKBOX, start_minimized_enable_switch, startMinimizedCheckBox)
startMinimizedButton.Bind(wx.EVT_BUTTON, start_minimized_enable_button)

# A combined panel for broadcast settings and paired devices
broadcastAndPairedDevicePanel = wx.Panel(appPanel)
broadcastAndPairedDeviceSizer = wx.BoxSizer(wx.VERTICAL)

state.looper = FlooAuxInput(blocksize=state.saved_blocksize)
state.input_devices = state.looper.list_additional_inputs()
state.name_input_devices = {d["name"]: d for d in state.input_devices}

broadcastPanel = BroadcastPanel(broadcastAndPairedDevicePanel, _, off, state.input_devices)
leBroadcastSb = broadcastPanel.static_box
leBroadcastSbSizer = broadcastPanel.sizer
leBroadcastSwitchPanel = broadcastPanel.switch_panel
leBroadcastSwitchPanelSizer = broadcastPanel.switch_panel_sizer
publicBroadcastCheckBox = broadcastPanel.public_broadcast_checkbox
publicBroadcastButton = broadcastPanel.public_broadcast_button
broadcastHighQualityCheckBox = broadcastPanel.broadcast_high_quality_checkbox
broadcastHighQualityButton = broadcastPanel.broadcast_high_quality_button
broadcastEncryptCheckBox = broadcastPanel.broadcast_encrypt_checkbox
broadcastEncryptButton = broadcastPanel.broadcast_encrypt_button
broadcastStopOnIdleCheckBox = broadcastPanel.broadcast_stop_on_idle_checkbox
broadcastStopOnIdleButton = broadcastPanel.broadcast_stop_on_idle_button
leBroadcastEntryPanel = broadcastPanel.entry_panel
leBroadcastEntryPanelSizer = broadcastPanel.entry_panel_sizer
broadcastNameLabel = broadcastPanel.broadcast_name_label
broadcastNameEntry = broadcastPanel.broadcast_name_entry
broadcastKey = broadcastPanel.broadcast_key_label
broadcastKeyEntry = broadcastPanel.broadcast_key_entry
leBroadcastLatencyPanel = broadcastPanel.latency_panel
leBroadcastLatencyPanelSizer = broadcastPanel.latency_panel_sizer
broadcastLatencyLabel = broadcastPanel.broadcast_latency_label
leBroadcastLatencyRadioPanel = broadcastPanel.latency_radio_panel
leBroadcastLatencyRadioPanelSizer = broadcastPanel.latency_radio_sizer
latencyLowestRadioButton = broadcastPanel.latency_lowest_radio
latencyLowerRadioButton = broadcastPanel.latency_lower_radio
latencyDefaultRadioButton = broadcastPanel.latency_default_radio
leBroadcastAuxInputPanel = broadcastPanel.aux_input_panel
leBroadcastAuxInputPanelSizer = broadcastPanel.aux_input_panel_sizer
auxInputLabel = broadcastPanel.aux_input_label
auxInputComboBox = broadcastPanel.aux_input_combo

publicBroadcastToggle = ToggleSwitchController(
    publicBroadcastButton,
    publicBroadcastCheckBox,
    on,
    off,
    _,
    _("Public broadcast"),
    lambda enable: flooSm.setPublicBroadcast(enable),
)
leBroadcastSwitchPanel.Bind(
    wx.EVT_CHECKBOX, publicBroadcastToggle.on_checkbox_click, publicBroadcastCheckBox
)
publicBroadcastButton.Bind(wx.EVT_BUTTON, publicBroadcastToggle.on_button_click)

broadcastHighQualityToggle = ToggleSwitchController(
    broadcastHighQualityButton,
    broadcastHighQualityCheckBox,
    on,
    off,
    _,
    _("Broadcast high-quality music, otherwise, voice"),
    lambda enable: flooSm.setBroadcastHighQuality(enable),
)
leBroadcastSwitchPanel.Bind(
    wx.EVT_CHECKBOX, broadcastHighQualityToggle.on_checkbox_click, broadcastHighQualityCheckBox
)
broadcastHighQualityButton.Bind(wx.EVT_BUTTON, broadcastHighQualityToggle.on_button_click)

broadcastEncryptToggle = ToggleSwitchController(
    broadcastEncryptButton,
    broadcastEncryptCheckBox,
    on,
    off,
    _,
    _("Encrypt broadcast; please set a key first"),
    lambda enable: flooSm.setBroadcastEncrypt(enable),
)
leBroadcastSwitchPanel.Bind(
    wx.EVT_CHECKBOX, broadcastEncryptToggle.on_checkbox_click, broadcastEncryptCheckBox
)
broadcastEncryptButton.Bind(wx.EVT_BUTTON, broadcastEncryptToggle.on_button_click)

broadcastStopOnIdleToggle = ToggleSwitchController(
    broadcastStopOnIdleButton,
    broadcastStopOnIdleCheckBox,
    on,
    off,
    _,
    _("Stop broadcasting immediately when USB audio playback ends"),
    lambda enable: flooSm.setBroadcastStopOnIdle(enable),
)
leBroadcastSwitchPanel.Bind(
    wx.EVT_CHECKBOX, broadcastStopOnIdleToggle.on_checkbox_click, broadcastStopOnIdleCheckBox
)
broadcastStopOnIdleButton.Bind(wx.EVT_BUTTON, broadcastStopOnIdleToggle.on_button_click)


# Broadcast name entry function
def broadcast_name_entry(event):
    name = broadcastNameEntry.GetValue()
    # print("new broadcast name", name)
    nameBytes = name.encode("utf-8")
    if 0 < len(nameBytes) < 31:
        flooSm.setBroadcastName(name)
    event.Skip()


broadcastNameEntry.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, broadcast_name_entry)
broadcastNameEntry.Bind(wx.EVT_KILL_FOCUS, broadcast_name_entry)


# Broadcast key entry function
def broadcast_key_entry(event):
    key = broadcastKeyEntry.GetValue()
    keyBytes = key.encode("utf-8")
    if 0 < len(keyBytes) < 17:
        flooSm.setBroadcastKey(key)
    event.Skip()


broadcastKeyEntry.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, broadcast_key_entry)
broadcastKeyEntry.Bind(wx.EVT_KILL_FOCUS, broadcast_key_entry)


def broadcast_latency_sel(event):
    selectedLabel = event.GetEventObject().GetLabel()
    if selectedLabel == latencyLowestRadioButton.GetLabel():
        mode = 1
    elif selectedLabel == latencyLowerRadioButton.GetLabel():
        mode = 2
    else:
        mode = 3
    flooSm.setBroadcastLatency(mode)


leBroadcastLatencyRadioPanel.Bind(wx.EVT_RADIOBUTTON, broadcast_latency_sel)


# AUX Input device select function
def input_device_on_select(event):
    state.saved_name = auxInputComboBox.GetValue()
    dev = state.name_input_devices.get(state.saved_name)

    # Save new selection
    state.saved_device = state.looper.serialize_input_device(dev)
    settings.set_item("aux_input", state.saved_device)
    settings.save()

    # Apply runtime
    state.looper.set_input(state.saved_device)

    logger.info("User chose: %s -> applied and saved", state.saved_name)


auxInputComboBox.Bind(wx.EVT_COMBOBOX, input_device_on_select)

pairedDevicesPanel = PairedDevicesPanel(broadcastAndPairedDevicePanel, _)
pairedDevicesSb = pairedDevicesPanel.static_box
pairedDevicesSbPanelSizer = pairedDevicesPanel.sizer
pairedDevicesSbButtonPanel = pairedDevicesPanel.button_panel
pairedDevicesSbButtonPanelSizer = pairedDevicesPanel.button_panel_sizer


# New pairing button function
def button_new_pairing(event):
    flooSm.setNewPairing()


# Clear all paired device function
def button_clear_all(event):
    flooSm.clearAllPairedDevices()


newPairingButton = pairedDevicesPanel.new_pairing_button
clearAllButton = pairedDevicesPanel.clear_all_button
newPairingButton.Bind(wx.EVT_BUTTON, button_new_pairing)
clearAllButton.Bind(wx.EVT_BUTTON, button_clear_all)


class PopMenu(wx.Menu):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        listBox = parent
        self.index = listBox.GetSelection()
        # menu item Connect/Disconnect
        menuItemConnection = wx.MenuItem(
            self,
            wx.ID_ANY,
            _("Connect") if self.index > 0 or flooSm.sourceState < 4 else _("Disconnect"),
        )
        self.Bind(wx.EVT_MENU, self.connect_disconnect_selected, menuItemConnection)
        self.Append(menuItemConnection)
        # menu item clear
        menuItemDelete = wx.MenuItem(self, wx.ID_ANY, _("Delete"))
        self.Bind(wx.EVT_MENU, self.delete_selected, menuItemDelete)
        self.Append(menuItemDelete)

    def delete_selected(self, e):
        flooSm.clearIndexedDevice(self.index)

    def connect_disconnect_selected(self, e):
        flooSm.toggleConnection(self.index)


def OnContextMenu(Event):
    listBox = Event.GetEventObject()
    pos = listBox.ScreenToClient(Event.GetPosition())
    item = listBox.HitTest(pos)
    if item != wx.NOT_FOUND:
        listBox.SetSelection(item)
    listBox.PopupMenu(PopMenu(listBox), pos)


pairedDeviceListbox = pairedDevicesPanel.device_listbox
pairedDeviceListbox.Bind(wx.EVT_CONTEXT_MENU, OnContextMenu)
currentPairedDeviceList = []

broadcastAndPairedDeviceSizer.Add(leBroadcastSbSizer, proportion=0, flag=wx.EXPAND)
broadcastAndPairedDeviceSizer.Add(pairedDevicesSbPanelSizer, proportion=1, flag=wx.EXPAND)
broadcastAndPairedDevicePanel.SetSizer(broadcastAndPairedDeviceSizer)

# Settings panel
aboutSb = wx.StaticBox(appPanel, wx.ID_ANY, _("Settings"))
aboutSbSizer = wx.StaticBoxSizer(aboutSb, wx.VERTICAL)
settingsPanelObj = SettingsPanel(aboutSb, _, on, off)
settingsPanel = settingsPanelObj.panel
settingsPanelSizer = settingsPanelObj.sizer
usbInputCheckBox = settingsPanelObj.usb_input_checkbox
usbInputEnableButton = settingsPanelObj.usb_input_button
ledCheckBox = settingsPanelObj.led_checkbox
ledEnableButton = settingsPanelObj.led_button
aptxLosslessCheckBox = settingsPanelObj.aptx_lossless_checkbox
aptxLosslessEnableButton = settingsPanelObj.aptx_lossless_button
gattClientWithBroadcastCheckBox = settingsPanelObj.gatt_client_checkbox
gattClientWithBroadcastEnableButton = settingsPanelObj.gatt_client_button

versionPanelObj = VersionPanel(aboutSb, app_path, appLogoPng, _)
versionPanel = versionPanelObj.panel
versionPanelSizer = versionPanelObj.sizer
logoStaticBmp = versionPanelObj.logo
thirdPartyLink = versionPanelObj.third_party_link
supportLink = versionPanelObj.support_link
versionInfo = versionPanelObj.version_info
dfuInfo = versionPanelObj.dfu_info
newFirmwareUrl = versionPanelObj.new_firmware_url
firmwareDesc = versionPanelObj.firmware_desc

usbInputToggle = ToggleSwitchController(
    usbInputEnableButton,
    usbInputCheckBox,
    on,
    off,
    _,
    _("USB Audio Input"),
    lambda enable: flooSm.enableUsbInput(enable),
)
settingsPanel.Bind(wx.EVT_CHECKBOX, usbInputToggle.on_checkbox_click, usbInputCheckBox)
usbInputEnableButton.Bind(wx.EVT_BUTTON, usbInputToggle.on_button_click)

ledToggle = ToggleSwitchController(
    ledEnableButton,
    ledCheckBox,
    on,
    off,
    _,
    _("LED"),
    lambda enable: flooSm.enableLed(enable),
)
settingsPanel.Bind(wx.EVT_CHECKBOX, ledToggle.on_checkbox_click, ledCheckBox)
ledEnableButton.Bind(wx.EVT_BUTTON, ledToggle.on_button_click)

aptxLosslessToggle = ToggleSwitchController(
    aptxLosslessEnableButton,
    aptxLosslessCheckBox,
    on,
    off,
    _,
    _("aptX Lossless"),
    lambda enable: flooSm.enableAptxLossless(enable),
)
settingsPanel.Bind(wx.EVT_CHECKBOX, aptxLosslessToggle.on_checkbox_click, aptxLosslessCheckBox)
aptxLosslessEnableButton.Bind(wx.EVT_BUTTON, aptxLosslessToggle.on_button_click)

gattClientToggle = ToggleSwitchController(
    gattClientWithBroadcastEnableButton,
    gattClientWithBroadcastCheckBox,
    on,
    off,
    _,
    "GATT " + _("Client"),
    lambda enable: flooSm.enableGattClient(enable),
)
settingsPanel.Bind(
    wx.EVT_CHECKBOX, gattClientToggle.on_checkbox_click, gattClientWithBroadcastCheckBox
)
gattClientWithBroadcastEnableButton.Bind(wx.EVT_BUTTON, gattClientToggle.on_button_click)


dfuInfoBind = False


def update_dfu_info(dfu_state: int):
    if dfu_state == FlooDfuThread.DFU_STATE_DONE:
        audioModeSb.Enable()
        windowSb.Enable()
        broadcastAndPairedDevicePanel.Enable()
        settingsPanel.Enable()
        dfuInfo.SetLabelText(_("Firmware") + " " + state.firmware_version)
        state.dfu_undergoing = False
    elif dfu_state == FlooDfuThread.DFU_ERROR_NOT_SUPPORTED:
        dfuInfo.SetLabelText(_("DFU not supported on Linux"))
        windowSb.Enable()
        state.dfu_undergoing = False
    elif dfu_state > FlooDfuThread.DFU_STATE_DONE:
        dfuInfo.SetLabelText(_("Upgrade error"))
        windowSb.Enable()
        state.dfu_undergoing = True
    else:
        versionPanelSizer.Hide(newFirmwareUrl)
        versionPanelSizer.Show(dfuInfo)
        dfuInfo.SetLabelText(_("Upgrade progress") + (" %d" % dfu_state) + "%")
        if not state.dfu_undergoing:
            audioModeSb.Disable()
            windowSb.Disable()
            broadcastAndPairedDevicePanel.Disable()
            settingsPanel.Disable()
            state.dfu_undergoing = True
    versionPanelSizer.Layout()


def button_dfu(event):
    with wx.FileDialog(
        appFrame,
        _("Open Firmware file"),
        wildcard="Bin files (*.bin)|*.bin",
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
    ) as fileDialog:
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return  # the user changed their mind

        # Proceed loading the file chosen by the user
        filename = fileDialog.GetPath()
        if filename:
            os.chdir(app_path)
            # os.add_dll_directory(app_path)
            fileBasename = os.path.splitext(filename)[0]
            if not re.search(r"\d+$", fileBasename):
                fileBasename = fileBasename[:-1]
            fileBasename += state.first_batch
            filename = fileBasename + ".bin"
            if os.path.isfile(filename):
                dfuThread = FlooDfuThread([app_path, filename], update_dfu_info)
                dfuThread.start()


aboutSbSizer.Add(settingsPanel, proportion=1, flag=wx.EXPAND)
aboutSbSizer.Add(versionPanel, proportion=3, flag=wx.TOP, border=4)

appSizer.Add(audioModeSbSizer, flag=wx.EXPAND | wx.LEFT, border=4)
appSizer.Add(windowSbSizer, flag=wx.EXPAND | wx.RIGHT, border=4)
appSizer.Add(broadcastAndPairedDevicePanel, flag=wx.EXPAND | wx.LEFT, border=4)
appSizer.Add(aboutSbSizer, flag=wx.EXPAND | wx.RIGHT, border=4)

appSizer.AddGrowableRow(0, 0)
appSizer.AddGrowableRow(1, 1)
appSizer.AddGrowableCol(0, 1)
appSizer.AddGrowableCol(1, 0)

appPanel.SetSizer(appSizer)


def enable_settings_widgets(enable: bool):
    if state.dfu_undergoing:
        return
    if enable:
        if state.firmware_variant != 0:
            audioModeSb.Disable()
        else:
            audioModeSb.Enable()
        broadcastAndPairedDevicePanel.Enable()
        settingsPanel.Enable()
        pairedDevicesSb.Enable()
        thirdPartyLink.Refresh()
        supportLink.Refresh()
    else:
        audioModeSb.Disable()
        broadcastAndPairedDevicePanel.Disable()
        settingsPanel.Disable()


enable_settings_widgets(False)

if state.start_minimized:
    appFrame.Iconize(True)
    appFrame.Hide()
else:
    appFrame.Show(True)


# All GUI object initialized, start FlooStateMachine
class FlooSmDelegate(FlooStateMachineDelegate):
    def deviceDetected(self, flag: bool, port: str, version: str = None):
        global dfuInfoBind

        if flag:
            update_status_bar(_("Use FlooGoo dongle on ") + " " + port)
            state.first_batch = "" if re.search(r"\d+$", version) else version[-1]
            state.firmware_variant = 1 if version.startswith("AS1") else 0
            state.firmware_variant = 2 if version.startswith("AS2") else state.firmware_variant
            state.firmware_version = version if state.first_batch == "" else version[:-1]
            # firmwareVersion = firmwareVersion[2:] if a2dpSink else firmwareVersion
            try:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                if state.firmware_variant == 1:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest_as1"
                elif state.firmware_variant == 2:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest_as2"
                else:
                    url = "https://www.flairmesh.com/Dongle/FMA120/latest"
                latest = urllib.request.urlopen(url, context=ssl_context, timeout=10).read()
                latest = latest.decode("utf-8").rstrip()
            except (urllib.error.URLError, TimeoutError):
                latest = "Unable"

            if not state.dfu_undergoing:
                if latest == "Unable":
                    newFirmwareUrl.SetLabelText(
                        _("Current firmware: ") + state.firmware_version + _(", check the latest.")
                    )
                    newFirmwareUrl.SetURL("https://www.flairmesh.com/Dongle/FMA120.html")
                    versionPanelSizer.Show(newFirmwareUrl)
                    versionPanelSizer.Layout()
                elif latest > state.firmware_version:
                    versionPanelSizer.Hide(dfuInfo)
                    newFirmwareUrl.SetLabelText(
                        _("New Firmware is available")
                        + " "
                        + state.firmware_version
                        + " -> "
                        + latest
                    )
                    newFirmwareUrl.SetURL(
                        "https://www.flairmesh.com/support/FMA120_" + latest + ".zip"
                    )
                    versionPanelSizer.Show(newFirmwareUrl)
                    if state.firmware_variant == 1:
                        firmwareDesc.SetLabelText("Auracast\u2122 " + _("Receiver"))
                        versionPanelSizer.Show(firmwareDesc)
                    elif state.firmware_variant == 2:
                        firmwareDesc.SetLabelText("A2DP - Auracast\u2122 " + _("Relay"))
                        versionPanelSizer.Show(firmwareDesc)
                    versionPanelSizer.Layout()
                else:
                    dfuInfo.SetLabelText(_("Firmware") + " " + state.firmware_version)
                    versionPanelSizer.Show(dfuInfo)
                    if state.firmware_variant == 1:
                        firmwareDesc.SetLabelText("Auracast\u2122 " + _("Receiver"))
                        versionPanelSizer.Show(firmwareDesc)
                    elif state.firmware_variant == 2:
                        firmwareDesc.SetLabelText("A2DP - Auracast\u2122 " + _("Relay"))
                        versionPanelSizer.Show(firmwareDesc)
                    versionPanelSizer.Layout()
        else:
            update_status_bar(_("Please insert your FlooGoo dongle"))
            pairedDeviceListbox.Clear()
            versionPanelSizer.Hide(dfuInfo)
        enable_settings_widgets(flag)

    def audioModeInd(self, mode: int):
        state.hw_with_analog_input = 1 if (mode & 0x80) == 0x80 else 0
        state.audio_mode = mode & 0x03
        if state.firmware_variant != 0:
            pairedDevicesSb.Enable(True)
        else:
            if state.audio_mode == 0:
                audioModeHighQualityRadioButton.SetValue(True)
                leBroadcastSb.Disable()
            elif state.audio_mode == 1:
                audioModeGamingRadioButton.SetValue(True)
                leBroadcastSb.Disable()
            elif state.audio_mode == 2:
                audioModeBroadcastRadioButton.SetValue(True)
                leBroadcastSb.Enable()
            audio_mode_sel_set(mode)

    def sourceStateInd(self, state: int):
        dongleStateText.SetLabelText(sourceStateStr[state])
        dongleStateSbSizer.Layout()

    def leAudioStateInd(self, state: int):
        leaStateText.SetLabelText(leaStateStr[state])
        leaStateSbSizer.Layout()

    def preferLeaInd(self, state: int):
        preferLeaToggle.set(state == 1, True)

    def broadcastModeInd(self, state: int):
        broadcastHighQualityToggle.set(state & 4 == 4, True)
        publicBroadcastToggle.set(state & 2 == 2, True)
        broadcastEncryptToggle.set(state & 1 == 1, True)
        broadcastStopOnIdleToggle.set(state & 8 == 8, True)
        broadcastLatency = (state & 0x30) >> 4
        if broadcastLatency == 1:
            latencyLowestRadioButton.SetValue(True)
        elif broadcastLatency == 2:
            latencyLowerRadioButton.SetValue(True)
        elif broadcastLatency == 3:
            latencyDefaultRadioButton.SetValue(True)
        if broadcastLatency == 0:
            leBroadcastLatencyPanel.Disable()
            broadcastStopOnIdleCheckBox.Disable()
            broadcastStopOnIdleButton.Disable()
        else:
            leBroadcastLatencyPanel.Enable()
            broadcastStopOnIdleCheckBox.Enable()
            broadcastStopOnIdleButton.Enable()

    def broadcastNameInd(self, name):
        broadcastNameEntry.SetValue(name)

    def pairedDevicesUpdateInd(self, pairedDevices):
        pairedDeviceListbox.Clear()
        i = 0
        while i < len(pairedDevices):
            # print(pairedDevices[i])
            pairedDeviceListbox.Append(pairedDevices[i])
            i = i + 1
        newPairingButton.Enable(False if preferLeaToggle.enabled and i > 0 else True)
        # clearAllButton.Enable(True if i > 0 else False)

    def audioCodecInUseInd(
        self, codec, rssi, rate, spkSampleRate, micSampleRate, sduInt, transportDelay, presentDelay
    ):
        label = codecFormatter.format(
            codec, rssi, rate, spkSampleRate, micSampleRate, sduInt, transportDelay, presentDelay
        )
        codecInUseText.SetLabelText(label)
        codecInUseSbSizer.Layout()

    def ledEnabledInd(self, enabled):
        ledToggle.set(enabled, True)

    def aptxLosslessEnabledInd(self, enabled):
        aptxLosslessToggle.set(enabled, True)

    def gattClientEnabledInd(self, enabled):
        gattClientToggle.set(enabled, True)

    def audioSourceInd(self, enabled):
        usbInputToggle.set(enabled, True)

    def connectionErrorInd(self, error: str):
        if error == "port_busy":
            update_status_bar(_("Port is busy - close other applications using the dongle"))
        else:
            update_status_bar(_("Connection error - please reconnect the dongle"))


flooSmDelegate = FlooSmDelegate()
flooSm = FlooStateMachine(flooSmDelegate)
flooSm.daemon = True
flooSm.start()

app.MainLoop()
