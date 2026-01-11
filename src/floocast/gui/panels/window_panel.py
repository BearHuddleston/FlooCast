import wx


class WindowPanel:
    def __init__(self, parent, translate, on_bitmap, off_bitmap, start_minimized):
        self.static_box = wx.StaticBox(parent, wx.ID_ANY, translate("Window"))
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.minimize_button = wx.Button(
            self.static_box, label=translate("Minimize to System Tray")
        )
        self.quit_button = wx.Button(self.static_box, label=translate("Quit App"))

        self.start_minimized_panel = wx.Panel(self.static_box)
        self.start_minimized_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.start_minimized_checkbox = wx.CheckBox(
            self.start_minimized_panel, wx.ID_ANY, label=translate("Start Minimized")
        )
        self.start_minimized_checkbox.SetValue(start_minimized)
        self.start_minimized_button = wx.Button(
            self.start_minimized_panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )

        if start_minimized:
            self.start_minimized_button.SetToolTip(
                translate("Toggle switch for")
                + " "
                + translate("Start Minimized")
                + " "
                + translate("On")
            )
            self.start_minimized_button.SetBitmap(on_bitmap)
        else:
            self.start_minimized_button.SetToolTip(
                translate("Toggle switch for")
                + " "
                + translate("Start Minimized")
                + " "
                + translate("Off")
            )
            self.start_minimized_button.SetBitmap(off_bitmap)

        self.start_minimized_sizer.Add(
            self.start_minimized_checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 0
        )
        self.start_minimized_sizer.AddStretchSpacer(1)
        self.start_minimized_sizer.Add(self.start_minimized_button, 0, wx.ALIGN_CENTER_VERTICAL)
        self.start_minimized_panel.SetSizer(self.start_minimized_sizer)

        self.sizer.AddStretchSpacer()
        self.sizer.Add(
            self.minimize_button, proportion=2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10
        )
        self.sizer.AddStretchSpacer()
        self.sizer.Add(
            self.quit_button, proportion=2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10
        )
        self.sizer.AddStretchSpacer()
        self.sizer.Add(
            self.start_minimized_panel, proportion=2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=0
        )
