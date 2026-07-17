"""Cross-platform global hotkey via ``pynput`` (Windows / macOS / X11).

``pynput`` runs its keyboard listener on a background thread, so the ``on_triggered`` callback fires
off the GUI thread. The composition root passes a callback that marshals onto the Qt event loop
(a queued signal), keeping this adapter free of any Qt dependency.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from pynput import keyboard

_MODIFIER_ALIASES = {"win": "cmd", "super": "cmd", "meta": "cmd", "control": "ctrl"}
_MODIFIER_NAMES = {"ctrl", "shift", "alt", "cmd"}


def to_pynput_hotkey_format(hotkey: str) -> str:
    """Convert a friendly combo like ``ctrl+shift+h`` to pynput's ``<ctrl>+<shift>+h``."""
    tokens = []
    for raw_part in hotkey.split("+"):
        part = raw_part.strip().lower()
        if not part:
            continue
        canonical = _MODIFIER_ALIASES.get(part, part)
        tokens.append(f"<{canonical}>" if canonical in _MODIFIER_NAMES else canonical)
    return "+".join(tokens)


class HotkeyBinder(Protocol):
    """A startable/stoppable global-hotkey binding — a UI-layer interaction port."""

    def start(self) -> None: ...

    def stop(self) -> None: ...


class PynputHotkeyBinder:
    """Binds a single global hotkey to a callback using a ``pynput`` listener thread."""

    def __init__(self, hotkey: str, on_triggered: Callable[[], None]) -> None:
        self._pynput_hotkey = to_pynput_hotkey_format(hotkey)
        self._on_triggered = on_triggered
        self._listener: Any = None

    def start(self) -> None:
        self._listener = keyboard.GlobalHotKeys({self._pynput_hotkey: self._on_triggered})
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
