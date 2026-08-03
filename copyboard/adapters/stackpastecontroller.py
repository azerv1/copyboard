"""Runtime on/off switch for stack-paste mode.

Stack paste is nothing more than a global hotkey binding (``ctrl+v`` by default) that pops the
newest clipping onto the clipboard. Turning the mode off therefore means unbinding that hotkey, so
the user's normal paste behaves normally again. This controller owns that binding's lifetime and
exposes it as a boolean the UI can flip; it depends only on the ``HotkeyBinder`` port, never on Qt.
"""

from __future__ import annotations

from copyboard.adapters.pynputhotkeybinder import HotkeyBinder


class StackPasteController:
    """Binds/unbinds the pop-and-paste hotkey so stack-paste mode can be toggled while running."""

    def __init__(self, hotkey_binder: HotkeyBinder, initially_enabled: bool = False) -> None:
        self._hotkey_binder = hotkey_binder
        self._is_enabled = False
        self.set_enabled(initially_enabled)

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    def set_enabled(self, enabled: bool) -> None:
        """Start or stop the pop-and-paste hotkey binding; re-setting the same state is a no-op."""
        if enabled == self._is_enabled:
            return
        if enabled:
            self._hotkey_binder.start()
        else:
            self._hotkey_binder.stop()
        self._is_enabled = enabled

    def shutdown(self) -> None:
        """Release the hotkey binding on application exit."""
        self.set_enabled(False)
