"""Headless smoke test: the window builds a row per clipping and Copy re-copies via the service."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from copyboard.adapters.ui.clippingwidget import ClippingWidget
from copyboard.adapters.ui.mainwindow import MainWindow
from copyboard.application.copyboardservice import CopyboardService
from copyboard.config import RetentionPolicy
from copyboard.domain.clippingclassifier import ClippingClassifier
from copyboard.domain.clippinghistory import ClippingHistory
from copyboard.domain.content import ImagePayload, RawClipboardData
from tests.fakes import FakeClipboardSink, FakeClock, FakeVault


def _build_populated_service() -> tuple[CopyboardService, FakeClipboardSink]:
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
    return service, sink


def _build_populated_window() -> tuple[MainWindow, FakeClipboardSink]:
    service, sink = _build_populated_service()
    return MainWindow(service, prune_interval_ms=100_000), sink


def test_window_builds_one_row_per_clipping(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    assert len(window.findChildren(ClippingWidget)) == 2


def test_copy_button_recopies_through_the_service(qt_app: QApplication) -> None:
    window, sink = _build_populated_window()
    copy_buttons = [b for b in window.findChildren(QPushButton) if b.text() == "Copy"]

    copy_buttons[0].click()

    assert len(sink.copied_clippings) == 1


def test_toggle_from_hidden_brings_window_to_front(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    assert not window.isVisible()

    window.toggle_visibility()

    assert window.isVisible()
    window.hide()  # don't leave a visible top-level window alive into teardown


def test_bring_to_front_shows_a_hidden_window(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    window.hide()

    window.bring_to_front()

    assert window.isVisible()
    window.hide()  # don't leave a visible top-level window alive into teardown


def _find_stack_paste_button(window: MainWindow) -> QPushButton:
    buttons = [b for b in window.findChildren(QPushButton) if b.text().startswith("Stack paste:")]
    assert len(buttons) == 1
    return buttons[0]


def test_stack_paste_button_starts_off_by_default(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()

    button = _find_stack_paste_button(window)

    assert not button.isChecked()
    assert button.text() == "Stack paste: Off"


def test_stack_paste_button_reports_each_toggle(qt_app: QApplication) -> None:
    toggles: list[bool] = []
    window = MainWindow(
        _build_populated_service()[0],
        prune_interval_ms=100_000,
        on_stack_paste_toggled=toggles.append,
    )
    button = _find_stack_paste_button(window)

    button.click()
    button.click()

    assert toggles == [True, False]
    assert button.text() == "Stack paste: Off"


def test_stack_paste_button_reflects_the_initial_enabled_state(qt_app: QApplication) -> None:
    window = MainWindow(
        _build_populated_service()[0],
        prune_interval_ms=100_000,
        stack_paste_enabled=True,
    )

    button = _find_stack_paste_button(window)

    assert button.isChecked()
    assert button.text() == "Stack paste: On"


def test_rows_do_not_label_the_clipping_kind(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    # The old header was "KIND · HH:MM:SS"; the kind label (and its "·" separator) is now gone.
    assert all("·" not in label.text() for label in window.findChildren(QLabel))
