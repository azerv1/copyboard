"""Translate a clipping's :class:`ClipboardPayload` into Qt drag data (``QMimeData``).

This mirrors :meth:`QtClipboardSink.copy_clipping_to_system_clipboard` in ``qtclipboard.py`` — the
same payload, just packaged for a ``QDrag`` (drag-out of the viewer) instead of written to the
system clipboard. Kept as a free function so the payload → mime mapping is unit-testable without
simulating a real drag.
"""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QUrl

from copyboard.domain.content import ClipboardPayload


def build_drag_mime_data(payload: ClipboardPayload) -> QMimeData:
    """Build the ``QMimeData`` a dragged clipping carries.

    Exactly one representation is offered per payload so a drop target inserts it once: a text
    payload becomes plain text, and an image payload becomes a single file URL pointing at the
    stored bitmap. (Offering an image as *both* a file URL and bitmap data makes some targets — rich
    editors, chat apps — accept both and paste it twice.) An empty payload carries nothing.
    """
    mime_data = QMimeData()
    if payload.text is not None:
        mime_data.setText(payload.text)
    elif payload.image_path is not None:
        mime_data.setUrls([QUrl.fromLocalFile(str(payload.image_path))])
    return mime_data
