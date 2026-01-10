import wx


class AudioModePanel:
    def __init__(self, parent, translate, on_bitmap, off_bitmap, codec_strings):
        self.static_box = wx.StaticBox(parent, wx.ID_ANY, translate("Audio Mode"))
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.upper_panel = wx.Panel(self.static_box)
        self.upper_sizer = wx.FlexGridSizer(2, 3, (0, 0))

        self.high_quality_radio = wx.RadioButton(
            self.upper_panel, label=translate("High Quality (one-to-one)"), style=wx.RB_GROUP
        )
        self.gaming_radio = wx.RadioButton(self.upper_panel, label=translate("Gaming (one-to-one)"))
        self.broadcast_radio = wx.RadioButton(self.upper_panel, label=translate("Broadcast"))

        self.dongle_state_box = wx.StaticBox(self.upper_panel, wx.ID_ANY, translate("Dongle State"))
        self.dongle_state_sizer = wx.StaticBoxSizer(self.dongle_state_box, wx.VERTICAL)
        self.dongle_state_text = wx.StaticText(
            self.dongle_state_box, wx.ID_ANY, translate("Initializing")
        )
        self.dongle_state_sizer.Add(
            self.dongle_state_text, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4
        )

        self.lea_state_box = wx.StaticBox(self.upper_panel, wx.ID_ANY, translate("LE Audio State"))
        self.lea_state_sizer = wx.StaticBoxSizer(self.lea_state_box, wx.VERTICAL)
        self.lea_state_text = wx.StaticText(
            self.lea_state_box, wx.ID_ANY, translate("Disconnected")
        )
        self.lea_state_sizer.Add(
            self.lea_state_text, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4
        )

        self.codec_in_use_box = wx.StaticBox(self.upper_panel, wx.ID_ANY, translate("Codec in Use"))
        self.codec_in_use_sizer = wx.StaticBoxSizer(self.codec_in_use_box, wx.VERTICAL)
        self.codec_in_use_text = wx.StaticText(self.codec_in_use_box, wx.ID_ANY, codec_strings[0])
        self.codec_in_use_sizer.Add(
            self.codec_in_use_text, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, border=4
        )

        self.upper_sizer.Add(self.high_quality_radio, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.Add(self.gaming_radio, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.Add(self.broadcast_radio, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.Add(self.dongle_state_sizer, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.Add(self.lea_state_sizer, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.Add(self.codec_in_use_sizer, flag=wx.EXPAND | wx.ALL, border=4)
        self.upper_sizer.AddGrowableRow(0, 1)
        self.upper_sizer.AddGrowableRow(1, 1)
        self.upper_sizer.AddGrowableCol(0, 1)
        self.upper_sizer.AddGrowableCol(1, 1)
        self.upper_sizer.AddGrowableCol(2, 2)
        self.upper_panel.SetSizer(self.upper_sizer)

        self.lower_panel = wx.Panel(self.static_box)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.prefer_lea_checkbox = wx.CheckBox(
            self.lower_panel,
            wx.ID_ANY,
            label=translate("Prefer using LE audio for dual-mode devices")
            + " ("
            + translate("Must be disabled for")
            + " "
            + "aptX™ Lossless"
            + ")",
        )
        self.prefer_lea_button = wx.Button(
            self.lower_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.prefer_lea_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("Prefer using LE audio for dual-mode devices")
            + " "
            + translate("Off")
        )
        self.prefer_lea_button.SetBitmap(off_bitmap)

        self.lower_sizer.Add(self.prefer_lea_checkbox, flag=wx.EXPAND, proportion=1)
        self.lower_sizer.Add(self.prefer_lea_button, proportion=0)
        self.lower_panel.SetSizer(self.lower_sizer)

        self.sizer.Add(self.upper_panel, flag=wx.EXPAND)
        self.sizer.Add(self.lower_panel, flag=wx.EXPAND)
