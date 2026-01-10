import wx
import wx.lib.agw.hyperlink as hl


class VersionPanel:
    def __init__(self, parent, app_path, app_logo_png, translate):
        self.panel = wx.Panel(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        logo_img = wx.Image(
            app_path + wx.FileName.GetPathSeparator() + app_logo_png, wx.BITMAP_TYPE_PNG
        )
        logo_bitmap = logo_img.ConvertToBitmap()
        self.logo = wx.StaticBitmap(self.panel, wx.ID_ANY, logo_bitmap)
        self.logo.SetToolTip(translate("FlooGoo"))
        self.sizer.Add(self.logo, flag=wx.ALIGN_CENTER)

        copy_right_text = "Copyright© 2023~2025 Flairmesh Technologies."
        self.copy_right_info = wx.StaticText(self.panel, wx.ID_ANY, label=copy_right_text)
        self.sizer.Add(self.copy_right_info, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        font = wx.Font(
            pointSize=10, family=wx.DEFAULT, style=wx.NORMAL, weight=wx.NORMAL, faceName="Consolas"
        )
        dc = wx.ScreenDC()
        dc.SetFont(font)
        dc.GetTextExtent(copy_right_text)

        self.third_party_link = hl.HyperLinkCtrl(
            self.panel,
            wx.ID_ANY,
            translate("Third-Party Software Licenses"),
            URL="https://www.flairmesh.com/support/third_lic.html",
        )
        self.sizer.Add(self.third_party_link, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        self.support_link = hl.HyperLinkCtrl(
            self.panel,
            wx.ID_ANY,
            translate("Support Link"),
            URL="https://www.flairmesh.com/Dongle/FMA120.html",
        )
        self.sizer.Add(self.support_link, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        self.version_info = wx.StaticText(
            self.panel, wx.ID_ANY, label=translate("Version") + " 1.2.0"
        )
        self.sizer.Add(self.version_info, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=4)

        self.dfu_info = wx.StaticText(self.panel, wx.ID_ANY, "")
        self.sizer.Add(self.dfu_info, flag=wx.ALIGN_CENTER)

        self.new_firmware_url = hl.HyperLinkCtrl(
            self.panel, wx.ID_ANY, translate("New Firmware is available"), URL=""
        )
        self.sizer.Add(self.new_firmware_url, flag=wx.ALIGN_CENTER)
        self.sizer.Hide(self.new_firmware_url)

        self.firmware_desc = wx.StaticText(self.panel, wx.ID_ANY, "")
        self.sizer.Add(self.firmware_desc, flag=wx.ALIGN_CENTER | wx.TOP, border=16)
        self.sizer.Hide(self.firmware_desc)

        self.panel.SetSizer(self.sizer)
