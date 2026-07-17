"""The clipping hierarchy — one class per kind of thing that can be copied.

A ``Clipping`` is an immutable value object. Behaviour that touches Qt or the OS lives in adapters;
these classes only produce pure previews and re-copy payloads.

The text-based kinds (text, url, command, json, markdown) share an intermediate
``TextualClipping`` base so the shared preview/re-copy behaviour is written once; each concrete
class differs only by its :class:`ClippingKind`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from copyboard.domain.content import ClipboardPayload

_PREVIEW_MAX_LENGTH = 80


class ClippingKind(Enum):
    """The category a captured clipping falls into."""

    TEXT = "text"
    URL = "url"
    PATH = "path"
    IMAGE = "image"
    COMMAND = "command"
    JSON = "json"
    MARKDOWN = "markdown"


def summarize_as_single_line(text: str, max_length: int = _PREVIEW_MAX_LENGTH) -> str:
    """Collapse whitespace and truncate ``text`` to a compact one-line preview."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[: max_length - 1].rstrip() + "…"


@dataclass(frozen=True, kw_only=True)
class Clipping(ABC):
    """Base class for every captured clipping.

    ``kw_only`` keeps construction unambiguous and side-steps dataclass inheritance field-ordering.
    """

    created_at: datetime
    size_bytes: int
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    @abstractmethod
    def kind(self) -> ClippingKind:
        """The category this clipping belongs to."""

    @abstractmethod
    def build_preview_text(self) -> str:
        """A short, human-readable one-line description for the viewer."""

    @abstractmethod
    def to_clipboard_payload(self) -> ClipboardPayload:
        """What to place back on the system clipboard when re-copied."""


@dataclass(frozen=True, kw_only=True)
class TextualClipping(Clipping, ABC):
    """Shared base for every clipping whose payload is a plain string of text."""

    text: str

    def build_preview_text(self) -> str:
        return summarize_as_single_line(self.text)

    def to_clipboard_payload(self) -> ClipboardPayload:
        return ClipboardPayload(text=self.text)


@dataclass(frozen=True, kw_only=True)
class TextClipping(TextualClipping):
    """Arbitrary copied text that matched no more specific kind."""

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.TEXT


@dataclass(frozen=True, kw_only=True)
class UrlClipping(TextualClipping):
    """Copied text recognised as a URL."""

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.URL


@dataclass(frozen=True, kw_only=True)
class CommandClipping(TextualClipping):
    """Copied text recognised as a shell / CLI command."""

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.COMMAND


@dataclass(frozen=True, kw_only=True)
class JsonClipping(TextualClipping):
    """Copied text recognised as a JSON document."""

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.JSON


@dataclass(frozen=True, kw_only=True)
class MarkdownClipping(TextualClipping):
    """Copied text recognised as Markdown."""

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.MARKDOWN


@dataclass(frozen=True, kw_only=True)
class PathClipping(Clipping):
    """Copied text recognised as a filesystem path. References the existing OS file (no copy)."""

    path: Path

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.PATH

    def build_preview_text(self) -> str:
        return summarize_as_single_line(str(self.path))

    def to_clipboard_payload(self) -> ClipboardPayload:
        return ClipboardPayload(text=str(self.path))


@dataclass(frozen=True, kw_only=True)
class ImageClipping(Clipping):
    """A bitmap copied to the clipboard, spilled to a temp file and referenced by path."""

    path: Path
    image_format: str

    @property
    def kind(self) -> ClippingKind:
        return ClippingKind.IMAGE

    def build_preview_text(self) -> str:
        return f"Image ({self.image_format.upper()}, {self.size_bytes} bytes)"

    def to_clipboard_payload(self) -> ClipboardPayload:
        return ClipboardPayload(image_path=self.path)
