import wx


class SettingsPanel:
    def __init__(self, parent, translate, on_bitmap, off_bitmap):
        self.panel = wx.Panel(parent)
        self.sizer = wx.FlexGridSizer(4, 2, (5, 0))

        self.usb_input_checkbox = wx.CheckBox(
            self.panel, wx.ID_ANY, label=translate("USB Audio Input")
        )
        self.usb_input_button = wx.Button(self.panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
        self.usb_input_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("USB Audio Input")
            + " "
            + translate(" Off")
        )
        self.usb_input_button.SetBitmap(off_bitmap)

        self.led_checkbox = wx.CheckBox(self.panel, wx.ID_ANY, label=translate("LED"))
        self.led_button = wx.Button(self.panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
        self.led_button.SetToolTip(
            translate("Toggle switch for") + " " + translate("LED") + " " + translate(" Off")
        )
        self.led_button.SetBitmap(off_bitmap)

        self.aptx_lossless_checkbox = wx.CheckBox(self.panel, wx.ID_ANY, label="aptX™ Lossless")
        self.aptx_lossless_button = wx.Button(
            self.panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE
        )
        self.aptx_lossless_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + translate("aptX Lossless")
            + " "
            + translate("Off")
        )
        self.aptx_lossless_button.SetBitmap(off_bitmap)

        self.gatt_client_checkbox = wx.CheckBox(
            self.panel, wx.ID_ANY, label="GATT " + translate("Client")
        )
        self.gatt_client_button = wx.Button(self.panel, wx.ID_ANY, style=wx.NO_BORDER | wx.MINIMIZE)
        self.gatt_client_button.SetToolTip(
            translate("Toggle switch for")
            + " "
            + ("GATT ")
            + translate("Client")
            + " "
            + translate("Off")
        )
        self.gatt_client_button.SetBitmap(off_bitmap)

        self.sizer.Add(self.usb_input_checkbox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(self.usb_input_button, flag=wx.ALIGN_RIGHT)
        self.sizer.Add(self.led_checkbox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(self.led_button, flag=wx.ALIGN_RIGHT)
        self.sizer.Add(
            self.aptx_lossless_checkbox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL
        )
        self.sizer.Add(self.aptx_lossless_button, flag=wx.ALIGN_RIGHT)
        self.sizer.Add(self.gatt_client_checkbox, 1, flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(self.gatt_client_button, flag=wx.ALIGN_RIGHT)

        self.sizer.Hide(self.usb_input_checkbox)
        self.sizer.Hide(self.usb_input_button)
        self.sizer.Hide(self.aptx_lossless_checkbox)
        self.sizer.Hide(self.aptx_lossless_button)
        self.sizer.Hide(self.gatt_client_checkbox)
        self.sizer.Hide(self.gatt_client_button)

        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableCol(1, 0)
        self.panel.SetSizer(self.sizer)

        self.on_bitmap = on_bitmap
        self.off_bitmap = off_bitmap
