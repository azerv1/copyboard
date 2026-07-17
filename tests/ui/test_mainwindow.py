"""Headless smoke test: the window builds a row per clipping and Copy re-copies via the service."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QApplication, QPushButton

from copyboard.adapters.ui.clippingwidget import ClippingWidget
from copyboard.adapters.ui.mainwindow import MainWindow
from copyboard.application.copyboardservice import CopyboardService
from copyboard.config import RetentionPolicy
from copyboard.domain.clippingclassifier import ClippingClassifier
from copyboard.domain.clippinghistory import ClippingHistory
from copyboard.domain.content import ImagePayload, RawClipboardData
from tests.fakes import FakeClipboardSink, FakeClock, FakeVault


def _build_populated_window() -> tuple[MainWindow, FakeClipboardSink]:
    clock = FakeClock(datetime(2026, 1, 1, 12, 0, 0))
    sink = FakeClipboardSink()
    service = CopyboardService(
        classifier=ClippingClassifier(vault=FakeVault(), clock=clock),
        history=ClippingHistory(RetentionPolicy()),
        clock=clock,
        sink=sink,
    )
    service.handle_new_clipboard_content(RawClipboardData(text="hello world"))
    service.handle_new_clipboard_content(RawClipboardData(image=ImagePayload(b"x", "png")))
    return MainWindow(service, prune_interval_ms=100_000), sink


def test_window_builds_one_row_per_clipping(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    assert len(window.findChildren(ClippingWidget)) == 2


def test_copy_button_recopies_through_the_service(qt_app: QApplication) -> None:
    window, sink = _build_populated_window()
    copy_buttons = [b for b in window.findChildren(QPushButton) if b.text() == "Copy"]

    copy_buttons[0].click()

    assert len(sink.copied_clippings) == 1
