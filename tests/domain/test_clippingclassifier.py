"""Classification rules: the raw clipboard snapshot maps to the most specific clipping kind."""

from __future__ import annotations

from datetime import datetime

import pytest

from copyboard.domain.clipping import ClippingKind
from copyboard.domain.clippingclassifier import ClippingClassifier
from copyboard.domain.content import ImagePayload, RawClipboardData
from tests.fakes import FakeClock, FakeVault

_MOMENT = datetime(2026, 1, 1, 12, 0, 0)


def _make_classifier() -> tuple[ClippingClassifier, FakeVault]:
    vault = FakeVault()
    classifier = ClippingClassifier(vault=vault, clock=FakeClock(_MOMENT))
    return classifier, vault


@pytest.mark.parametrize(
    ("text", "expected_kind"),
    [
        ("https://example.com/page?q=1", ClippingKind.URL),
        (r"C:\Users\me\notes.txt", ClippingKind.PATH),
        ("/home/me/project/main.py", ClippingKind.PATH),
        ('{"name": "copyboard", "count": 3}', ClippingKind.JSON),
        ("# Heading\n\nSome prose here.", ClippingKind.MARKDOWN),
        ("git commit -m 'wip'", ClippingKind.COMMAND),
        ("just some ordinary words", ClippingKind.TEXT),
    ],
)
def test_text_is_classified_by_priority(text: str, expected_kind: ClippingKind) -> None:
    classifier, _ = _make_classifier()
    clipping = classifier.classify_clipboard_content(RawClipboardData(text=text))
    assert clipping is not None
    assert clipping.kind is expected_kind
    assert clipping.created_at == _MOMENT


def test_image_is_stored_in_vault_and_referenced_by_path() -> None:
    classifier, vault = _make_classifier()
    payload = ImagePayload(data=b"\x89PNG\r\n\x1a\n", image_format="png")
    clipping = classifier.classify_clipboard_content(RawClipboardData(image=payload))
    assert clipping is not None
    assert clipping.kind is ClippingKind.IMAGE
    assert clipping.size_bytes == len(payload.data)
    assert vault.stored_images == [(payload.data, ".png")]


def test_empty_clipboard_yields_no_clipping() -> None:
    classifier, _ = _make_classifier()
    assert classifier.classify_clipboard_content(RawClipboardData()) is None
