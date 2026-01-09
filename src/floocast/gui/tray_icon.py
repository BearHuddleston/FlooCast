"""System tray icon using pystray for GNOME AppIndicator support."""

import os

import pystray
import wx
from PIL import Image


class FlooCastTrayIcon:
    def __init__(self, frame, icon_path, translate_func=None):
        self.frame = frame
        self.icon = None
        self._ = translate_func or (lambda x: x)

        if os.path.exists(icon_path):
            self.image = Image.open(icon_path)
        else:
            self.image = Image.new("RGB", (64, 64), color="blue")

        self._create_icon()

    def _create_icon(self):
        _ = self._
        menu = pystray.Menu(
            pystray.MenuItem(_("Show Window"), self._on_show, default=True),
            pystray.MenuItem(_("Minimize to System Tray"), self._on_minimize),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(_("Quit"), self._on_quit),
        )
        self.icon = pystray.Icon("FlooCast", self.image, "FlooCast", menu)

    def run(self):
        self.icon.run_detached()

    def _restore_window(self):
        if not self.frame.IsShown():
            self.frame.Show(True)
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        try:
            self.frame.Restore()
        except Exception:
            pass
        self.frame.Raise()
        child = self.frame.FindFocus() or self.frame.FindWindowById(wx.ID_ANY)
        (child or self.frame).SetFocus()
        if not self.frame.IsActive():
            try:
                flag = getattr(wx, "USER_ATTENTION_INFO", 0)
                self.frame.RequestUserAttention(flag)
            except Exception:
                try:
                    self.frame.RequestUserAttention()
                except Exception:
                    pass

    def _on_show(self, icon=None, item=None):
        wx.CallAfter(self._restore_window)

    def _on_minimize(self, icon=None, item=None):
        def _hide():
            if not self.frame.IsIconized():
                self.frame.Iconize(True)
            if self.frame.IsShown():
                self.frame.Hide()

        wx.CallAfter(_hide)

    def _on_quit(self, icon=None, item=None):
        def _close():
            self.icon.stop()
            self.frame.Close()

        wx.CallAfter(_close)

    def Destroy(self):
        if self.icon:
            self.icon.stop()
