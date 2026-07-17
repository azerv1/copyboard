"""Previews and re-copy payloads for the clipping hierarchy."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from copyboard.domain.clipping import (
    ClippingKind,
    ImageClipping,
    TextClipping,
    summarize_as_single_line,
)
from copyboard.domain.content import ClipboardPayload

_MOMENT = datetime(2026, 1, 1, 12, 0, 0)


def test_summarize_collapses_whitespace_and_newlines() -> None:
    assert summarize_as_single_line("hello\n\n  world\t!") == "hello world !"


def test_long_preview_is_truncated_with_ellipsis() -> None:
    clipping = TextClipping(created_at=_MOMENT, size_bytes=0, text="a" * 200)
    preview = clipping.build_preview_text()
    assert preview.endswith("…")
    assert len(preview) <= 80


def test_text_clipping_recopies_as_text_payload() -> None:
    clipping = TextClipping(created_at=_MOMENT, size_bytes=7, text="copy me")
    assert clipping.kind is ClippingKind.TEXT
    assert clipping.to_clipboard_payload() == ClipboardPayload(text="copy me")


def test_image_clipping_recopies_by_path() -> None:
    image_path = Path("/tmp/shot.png")
    clipping = ImageClipping(created_at=_MOMENT, size_bytes=10, path=image_path, image_format="png")
    assert clipping.kind is ClippingKind.IMAGE
    assert clipping.to_clipboard_payload() == ClipboardPayload(image_path=image_path)
