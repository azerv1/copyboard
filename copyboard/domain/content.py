"""Value objects for clipboard content — the neutral data crossing the port boundary.

These are pure data holders with no behaviour that touches Qt or the OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImagePayload:
    """Encoded bitmap bytes (e.g. PNG) captured from the clipboard."""

    data: bytes
    image_format: str

    @property
    def size_bytes(self) -> int:
        return len(self.data)


@dataclass(frozen=True, slots=True)
class RawClipboardData:
    """A neutral snapshot of the OS clipboard: optional text and/or an image."""

    text: str | None = None
    image: ImagePayload | None = None

    def is_empty(self) -> bool:
        return self.text is None and self.image is None

    def has_image(self) -> bool:
        return self.image is not None

    def has_nonempty_text(self) -> bool:
        return bool(self.text)


@dataclass(frozen=True, slots=True)
class ClipboardPayload:
    """What to place back on the system clipboard when a clipping is re-copied.

    Exactly one field is set: ``text`` for text/url/path clippings, ``image_path`` for images.
    The image bytes are read from ``image_path`` by the (adapter) clipboard sink, keeping the
    domain free of filesystem I/O.
    """

    text: str | None = None
    image_path: Path | None = None
