import wx


class BroadcastPanel:
    def __init__(self, parent, translate, on_bitmap, off_bitmap, input_devices):
        self.static_box = wx.StaticBox(parent, wx.ID_ANY, translate("LE Broadcast"))
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.switch_panel = wx.Panel(self.static_box)
        self.switch_panel_sizer = wx.FlexGridSizer(5, 2, (0, 0))

        self.public_broadcast_checkbox = wx.CheckBox(
            self.switch_panel,
            wx.ID_ANY,
            label=translate("Public broadcast")
            + " ("
            + translate("Must be enabled for compatibility with")
            + " Auracast™)",
        )
        self.public_broadcast_button = wx.Button(
            self.switch_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.public_broadcast_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("Public broadcast")
            + " "
            + translate("Off")
        )
        self.public_broadcast_button.SetBitmap(off_bitmap)

        self.broadcast_high_quality_checkbox = wx.CheckBox(
            self.switch_panel,
            wx.ID_ANY,
            label=translate("Broadcast high-quality music, otherwise, voice")
            + " ("
            + translate("Must be disabled for compatibility with")
            + " Auracast™)",
        )
        self.broadcast_high_quality_button = wx.Button(
            self.switch_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.broadcast_high_quality_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("Broadcast high-quality music, otherwise, voice")
            + " "
            + translate("Off")
        )
        self.broadcast_high_quality_button.SetBitmap(off_bitmap)

        self.broadcast_encrypt_checkbox = wx.CheckBox(
            self.switch_panel,
            wx.ID_ANY,
            label=translate("Encrypt broadcast; please set a key first"),
        )
        self.broadcast_encrypt_button = wx.Button(
            self.switch_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.broadcast_encrypt_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("Encrypt broadcast; please set a key first")
            + " "
            + translate("Off")
        )
        self.broadcast_encrypt_button.SetBitmap(off_bitmap)

        self.broadcast_stop_on_idle_checkbox = wx.CheckBox(
            self.switch_panel,
            wx.ID_ANY,
            label=translate("Stop broadcasting immediately when USB audio playback ends"),
        )
        self.broadcast_stop_on_idle_button = wx.Button(
            self.switch_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.broadcast_stop_on_idle_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("Stop broadcasting immediately when USB audio playback ends")
            + " "
            + translate("Off")
        )
        self.broadcast_stop_on_idle_button.SetBitmap(off_bitmap)

        self.switch_panel_sizer.Add(self.public_broadcast_checkbox, flag=wx.ALIGN_LEFT)
        self.switch_panel_sizer.Add(self.public_broadcast_button, flag=wx.ALIGN_RIGHT)
        self.switch_panel_sizer.Add(self.broadcast_high_quality_checkbox, flag=wx.ALIGN_LEFT)
        self.switch_panel_sizer.Add(self.broadcast_high_quality_button, flag=wx.ALIGN_RIGHT)
        self.switch_panel_sizer.Add(self.broadcast_encrypt_checkbox, flag=wx.ALIGN_LEFT)
        self.switch_panel_sizer.Add(self.broadcast_encrypt_button, flag=wx.ALIGN_RIGHT)
        self.switch_panel_sizer.Add(self.broadcast_stop_on_idle_checkbox, flag=wx.ALIGN_LEFT)
        self.switch_panel_sizer.Add(self.broadcast_stop_on_idle_button, flag=wx.ALIGN_RIGHT)
        self.switch_panel_sizer.AddGrowableCol(0, 0)
        self.switch_panel_sizer.AddGrowableCol(1, 1)
        self.switch_panel.SetSizer(self.switch_panel_sizer)

        self.entry_panel = wx.Panel(self.static_box)
        self.entry_panel_sizer = wx.FlexGridSizer(2, 2, (0, 0))

        self.broadcast_name_label = wx.StaticText(
            self.entry_panel, wx.ID_ANY, label=translate("Broadcast Name, maximum 30 characters")
        )
        self.broadcast_name_entry = wx.SearchCtrl(self.entry_panel, wx.ID_ANY)
        self.broadcast_name_entry.ShowSearchButton(False)
        self.broadcast_name_entry.SetHint(
            translate("Input a new name of no more than 30 characters then press <ENTER>")
        )
        self.broadcast_name_entry.SetDescriptiveText(
            translate("Input a new name of no more than 30 characters then press <ENTER>")
        )

        self.broadcast_key_label = wx.StaticText(
            self.entry_panel, wx.ID_ANY, label=translate("Broadcast Key, maximum 16 characters")
        )
        self.broadcast_key_entry = wx.SearchCtrl(self.entry_panel, wx.ID_ANY, style=wx.TE_PASSWORD)
        self.broadcast_key_entry.ShowSearchButton(False)
        self.broadcast_key_entry.SetDescriptiveText(translate("Input a new key then press <ENTER>"))

        self.entry_panel_sizer.Add(
            self.broadcast_name_label, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        )
        self.entry_panel_sizer.Add(self.broadcast_name_entry, flag=wx.EXPAND | wx.LEFT, border=8)
        self.entry_panel_sizer.Add(
            self.broadcast_key_label, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        )
        self.entry_panel_sizer.Add(self.broadcast_key_entry, flag=wx.EXPAND | wx.LEFT, border=8)
        self.entry_panel_sizer.AddGrowableCol(0, 1)
        self.entry_panel_sizer.AddGrowableCol(1, 1)
        self.entry_panel.SetSizer(self.entry_panel_sizer)

        self.latency_panel = wx.Panel(self.static_box)
        self.latency_panel_sizer = wx.FlexGridSizer(1, 2, (0, 0))
        self.broadcast_latency_label = wx.StaticText(
            self.latency_panel, wx.ID_ANY, label=translate("Broadcast Latency")
        )
        self.latency_panel_sizer.Add(
            self.broadcast_latency_label, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        )

        self.latency_radio_panel = wx.Panel(self.latency_panel)
        self.latency_radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.latency_lowest_radio = wx.RadioButton(
            self.latency_radio_panel, label=translate("Lowest"), style=wx.RB_GROUP
        )
        self.latency_lower_radio = wx.RadioButton(
            self.latency_radio_panel, label=translate("Lower")
        )
        self.latency_default_radio = wx.RadioButton(
            self.latency_radio_panel, label=translate("Default")
        )
        self.latency_radio_sizer.Add(self.latency_lowest_radio, 0, wx.EXPAND | wx.LEFT, 10)
        self.latency_radio_sizer.Add(self.latency_lower_radio, 0, wx.EXPAND | wx.LEFT, 10)
        self.latency_radio_sizer.Add(self.latency_default_radio, 0, wx.EXPAND | wx.LEFT, 10)
        self.latency_radio_panel.SetSizer(self.latency_radio_sizer)

        self.latency_panel_sizer.Add(
            self.latency_radio_panel, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8
        )
        self.latency_panel_sizer.AddGrowableCol(1, 1)
        self.latency_panel.SetSizer(self.latency_panel_sizer)

        self.aux_input_panel = wx.Panel(self.static_box)
        self.aux_input_panel_sizer = wx.FlexGridSizer(1, 2, (0, 0))
        self.aux_input_label = wx.StaticText(
            self.aux_input_panel, wx.ID_ANY, label=translate("Broadcast Additional Audio Input")
        )
        self.aux_input_combo = wx.ComboBox(
            self.aux_input_panel,
            style=wx.CB_READONLY,
            choices=[device["name"] for device in input_devices],
        )
        self.aux_input_panel_sizer.Add(
            self.aux_input_label, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        )
        self.aux_input_panel_sizer.Add(
            self.aux_input_combo, flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8
        )
        self.aux_input_panel_sizer.AddGrowableCol(1, 1)
        self.aux_input_panel.SetSizer(self.aux_input_panel_sizer)

        self.sizer.Add(self.switch_panel, flag=wx.EXPAND | wx.TOP, border=4)
        self.sizer.Add(self.entry_panel, flag=wx.EXPAND | wx.TOP, border=4)
        self.sizer.Add(self.latency_panel, flag=wx.EXPAND | wx.TOP, border=4)
        self.sizer.Add(self.aux_input_panel, flag=wx.EXPAND | wx.TOP, border=4)

        self.on_bitmap = on_bitmap
        self.off_bitmap = off_bitmap
