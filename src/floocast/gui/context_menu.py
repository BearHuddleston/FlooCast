from collections.abc import Callable

import wx

from floocast.protocol.state_machine import FlooStateMachine


class PairedDeviceMenu(wx.Menu):
    def __init__(self, parent, state_machine: FlooStateMachine, _: Callable[[str], str]):
        super().__init__()
        self.parent = parent
        self.state_machine = state_machine
        self._ = _
        listbox = parent
        self.index = listbox.GetSelection()

        menu_item_connection = wx.MenuItem(
            self,
            wx.ID_ANY,
            _("Connect") if self.index > 0 or state_machine.sourceState < 4 else _("Disconnect"),
        )
        self.Bind(wx.EVT_MENU, self._on_connect_disconnect, menu_item_connection)
        self.Append(menu_item_connection)

        menu_item_delete = wx.MenuItem(self, wx.ID_ANY, _("Delete"))
        self.Bind(wx.EVT_MENU, self._on_delete, menu_item_delete)
        self.Append(menu_item_delete)

    def _on_delete(self, e):
        self.state_machine.clearIndexedDevice(self.index)

    def _on_connect_disconnect(self, e):
        self.state_machine.toggleConnection(self.index)
