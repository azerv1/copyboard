"""Retention behaviour of the in-memory clipping history (count and age limits)."""

from __future__ import annotations

from datetime import datetime, timedelta

from copyboard.config import RetentionPolicy
from copyboard.domain.clipping import Clipping, TextClipping
from copyboard.domain.clippinghistory import ClippingHistory

_BASE = datetime(2026, 1, 1, 12, 0, 0)


def _make_text_clipping(created_at: datetime, text: str) -> TextClipping:
    return TextClipping(created_at=created_at, size_bytes=len(text), text=text)


def _previews_of(clippings: list[Clipping]) -> list[str]:
    return [clipping.build_preview_text() for clipping in clippings]


def test_count_limit_drops_oldest_and_keeps_newest_first() -> None:
    history = ClippingHistory(RetentionPolicy(max_items=2, max_age=timedelta(hours=1)))
    for offset, label in enumerate(["a", "b", "c"]):
        history.add_clipping(_make_text_clipping(_BASE + timedelta(seconds=offset), label))

    assert _previews_of(history.list_clippings_newest_first()) == ["c", "b"]
    assert history.count() == 2


def test_enforce_retention_drops_items_older_than_max_age() -> None:
    history = ClippingHistory(RetentionPolicy(max_items=100, max_age=timedelta(minutes=20)))
    history.add_clipping(_make_text_clipping(_BASE, "old"))
    history.add_clipping(_make_text_clipping(_BASE + timedelta(minutes=19), "recent"))

    removed = history.enforce_retention(_BASE + timedelta(minutes=21))

    assert _previews_of(removed) == ["old"]
    assert _previews_of(history.list_clippings_newest_first()) == ["recent"]


def test_remove_and_find_clipping_by_id() -> None:
    history = ClippingHistory(RetentionPolicy())
    clipping = _make_text_clipping(_BASE, "target")
    history.add_clipping(clipping)

    assert history.find_clipping_by_id(clipping.id) is clipping
    assert history.remove_clipping_by_id(clipping.id) is True
    assert history.remove_clipping_by_id("does-not-exist") is False
    assert history.find_clipping_by_id(clipping.id) is None
