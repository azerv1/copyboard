"""Guard against re-capturing our own clipboard writes.

When the app re-copies a clipping, the OS fires a clipboard-change signal that would otherwise be
captured as a brand-new clipping — an echo. The sink *arms* the guard just before writing; the
source *consumes* it on the next change and skips that one event. Pure Python, so it is testable
without Qt.
"""

from __future__ import annotations


class ClipboardEchoGuard:
    """A one-shot latch shared by the clipboard sink and source to suppress self-induced changes."""

    def __init__(self) -> None:
        self._armed = False

    def arm(self) -> None:
        self._armed = True

    def consume_if_armed(self) -> bool:
        """Return whether the guard was armed, resetting it either way."""
        was_armed = self._armed
        self._armed = False
        return was_armed
