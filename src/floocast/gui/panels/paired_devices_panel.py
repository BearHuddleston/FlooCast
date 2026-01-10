import wx


class PairedDevicesPanel:
    def __init__(self, parent, translate):
        self.static_box = wx.StaticBox(parent, wx.ID_ANY, translate("Most Recently Used Devices"))
        self.sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.button_panel = wx.Panel(self.static_box)
        self.button_panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.new_pairing_button = wx.Button(
            self.button_panel, wx.ID_ANY, label=translate("Add device")
        )
        self.clear_all_button = wx.Button(
            self.button_panel, wx.ID_ANY, label=translate("Clear All")
        )
        self.button_panel_sizer.Add(self.new_pairing_button, flag=wx.LEFT)
        self.button_panel_sizer.AddStretchSpacer()
        self.button_panel_sizer.Add(self.clear_all_button, flag=wx.RIGHT)
        self.button_panel.SetSizer(self.button_panel_sizer)

        self.device_listbox = wx.ListBox(self.static_box, style=wx.LB_SINGLE | wx.LB_ALWAYS_SB)

        self.sizer.Add(self.button_panel, proportion=0, flag=wx.EXPAND)
        self.sizer.Add(self.device_listbox, proportion=1, flag=wx.EXPAND)
