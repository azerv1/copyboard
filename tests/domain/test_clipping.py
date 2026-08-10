"""Previews and re-copy payloads for the clipping hierarchy."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from copyboard.domain.clipping import (
    ClippingKind,
    ImageClipping,
    JsonClipping,
    TextClipping,
    summarize_as_preview_block,
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


def test_preview_block_keeps_the_original_line_breaks() -> None:
    assert summarize_as_preview_block("first\n  second\nthird") == "first\n  second\nthird"


def test_preview_block_keeps_only_the_opening_lines() -> None:
    block = summarize_as_preview_block("\n".join(f"line {n}" for n in range(20)), max_lines=3)
    assert block == "line 0\nline 1\nline 2"


def test_preview_block_truncates_past_the_character_budget() -> None:
    block = summarize_as_preview_block("a" * 900, max_chars=50)
    assert block.endswith("…")
    assert len(block) <= 50


def test_preview_block_leaves_short_text_untouched() -> None:
    assert summarize_as_preview_block("short") == "short"


def test_preview_block_does_not_reformat_json() -> None:
    # A single-line JSON array must be shown exactly as copied, never pretty-printed.
    payload = "[[1771372800000,35232805957.96],[1771459200000,33982301570.40]]"
    clipping = JsonClipping(created_at=_MOMENT, size_bytes=len(payload), text=payload)
    assert clipping.build_preview_block() == payload


def test_preview_block_shows_far_more_than_the_one_line_preview() -> None:
    payload = "x" * 400
    clipping = TextClipping(created_at=_MOMENT, size_bytes=400, text=payload)
    assert len(clipping.build_preview_block()) > len(clipping.build_preview_text())


def test_text_clipping_recopies_as_text_payload() -> None:
    clipping = TextClipping(created_at=_MOMENT, size_bytes=7, text="copy me")
    assert clipping.kind is ClippingKind.TEXT
    assert clipping.to_clipboard_payload() == ClipboardPayload(text="copy me")


def test_image_clipping_recopies_by_path() -> None:
    image_path = Path("/tmp/shot.png")
    clipping = ImageClipping(created_at=_MOMENT, size_bytes=10, path=image_path, image_format="png")
    assert clipping.kind is ClippingKind.IMAGE
    assert clipping.to_clipboard_payload() == ClipboardPayload(image_path=image_path)
