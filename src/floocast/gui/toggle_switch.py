"""Toggle switch controller for checkbox/button pairs."""


class ToggleSwitchController:
    def __init__(
        self,
        button,
        checkbox,
        on_bitmap,
        off_bitmap,
        translate,
        label,
        state_machine_action,
        extra_action=None,
    ):
        self._button = button
        self._checkbox = checkbox
        self._on_bitmap = on_bitmap
        self._off_bitmap = off_bitmap
        self._translate = translate
        self._label = label
        self._state_machine_action = state_machine_action
        self._extra_action = extra_action
        self._enabled = False

    @property
    def enabled(self):
        return self._enabled

    def set(self, enable, is_notify):
        self._enabled = enable
        self._button.SetBitmap(self._on_bitmap if enable else self._off_bitmap)
        self._button.SetToolTip(
            self._translate("Toggle switch for")
            + " "
            + self._label
            + " "
            + (self._translate("On") if enable else self._translate("Off"))
        )
        if is_notify:
            self._checkbox.SetValue(enable)
        else:
            self._state_machine_action(enable)
        if self._extra_action:
            self._extra_action(enable)

    def on_button_click(self, event):
        self._checkbox.SetValue(not self._enabled)
        self.set(not self._enabled, False)

    def on_checkbox_click(self, event):
        self.set(not self._enabled, False)
