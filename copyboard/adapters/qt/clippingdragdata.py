"""Translate a clipping's :class:`ClipboardPayload` into Qt drag data (``QMimeData``).

This mirrors :meth:`QtClipboardSink.copy_clipping_to_system_clipboard` in ``qtclipboard.py`` — the
same payload, just packaged for a ``QDrag`` (drag-out of the viewer) instead of written to the
system clipboard. Kept as a free function so the payload → mime mapping is unit-testable without
simulating a real drag.
"""

from __future__ import annotations

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtGui import QImage

from copyboard.domain.content import ClipboardPayload


def build_drag_mime_data(payload: ClipboardPayload) -> QMimeData:
    """Build the ``QMimeData`` a dragged clipping carries.

    A text payload becomes plain text. An image payload is offered two ways so the widest set of
    drop targets accepts it: as a file URL (file managers, editors, chat apps that take files) and,
    when the file loads, as bitmap image data (image editors and chat apps that take a bitmap). An
    empty payload yields empty mime data — the drag simply carries nothing.
    """
    mime_data = QMimeData()
    if payload.text is not None:
        mime_data.setText(payload.text)
    elif payload.image_path is not None:
        mime_data.setUrls([QUrl.fromLocalFile(str(payload.image_path))])
        image = QImage(str(payload.image_path))
        if not image.isNull():
            mime_data.setImageData(image)
    return mime_data
