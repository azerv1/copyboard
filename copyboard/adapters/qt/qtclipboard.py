"""Qt-backed clipboard adapters: capture changes and write clippings back.

``QtClipboardSource`` implements the ``ClipboardSource`` port and drives the service on every
clipboard change; ``QtClipboardSink`` implements the ``ClipboardSink`` port. Both share a
:class:`ClipboardEchoGuard` so a re-copy does not get re-captured as a new clipping.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QClipboard, QImage

from copyboard.adapters.clipboardechoguard import ClipboardEchoGuard
from copyboard.domain.clipping import Clipping
from copyboard.domain.content import ImagePayload, RawClipboardData

_DEFAULT_IMAGE_FORMAT = "png"


class QtClipboardSource:
    """Watches the system clipboard and reports new content as :class:`RawClipboardData`.

    The clipboard exposes an image as a raw in-memory ``QImage`` (there is no original file), so we
    serialise it ourselves. ``image_format`` chooses that container — the default ``png`` is
    lossless and transparency-aware, ideal for screenshots; ``jpg`` etc. work if size matters.
    """

    def __init__(
        self,
        clipboard: QClipboard,
        echo_guard: ClipboardEchoGuard,
        image_format: str = _DEFAULT_IMAGE_FORMAT,
    ) -> None:
        self._clipboard = clipboard
        self._echo_guard = echo_guard
        self._image_format = image_format
        self._on_new_content: Callable[[RawClipboardData], None] | None = None
        self._clipboard.dataChanged.connect(self._handle_clipboard_data_changed)

    def set_new_content_listener(self, listener: Callable[[RawClipboardData], None]) -> None:
        self._on_new_content = listener

    def read_current_content(self) -> RawClipboardData:
        image = self._clipboard.image()
        if not image.isNull():
            return RawClipboardData(image=self._encode_image(image))
        text = self._clipboard.text()
        if text:
            return RawClipboardData(text=text)
        return RawClipboardData()

    def _handle_clipboard_data_changed(self) -> None:
        if self._echo_guard.consume_if_armed():
            return
        content = self.read_current_content()
        if content.is_empty() or self._on_new_content is None:
            return
        self._on_new_content(content)

    def _encode_image(self, image: QImage) -> ImagePayload:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, self._image_format.upper().encode("ascii"))
        data = bytes(buffer.data().data())
        buffer.close()
        return ImagePayload(data=data, image_format=self._image_format)


class QtClipboardSink:
    """Writes a clipping's payload back onto the system clipboard."""

    def __init__(self, clipboard: QClipboard, echo_guard: ClipboardEchoGuard) -> None:
        self._clipboard = clipboard
        self._echo_guard = echo_guard

    def copy_clipping_to_system_clipboard(self, clipping: Clipping) -> None:
        payload = clipping.to_clipboard_payload()
        if payload.image_path is not None:
            image = QImage(str(payload.image_path))
            if image.isNull():
                return
            self._echo_guard.arm()
            self._clipboard.setImage(image)
        elif payload.text is not None:
            self._echo_guard.arm()
            self._clipboard.setText(payload.text)
