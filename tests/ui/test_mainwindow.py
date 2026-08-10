"""Headless smoke test: the window builds a row per clipping and Copy re-copies via the service."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from copyboard.adapters.ui.clippingwidget import ClippingWidget
from copyboard.adapters.ui.mainwindow import MainWindow, compute_column_count
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


def test_column_count_grows_with_the_available_width() -> None:
    assert compute_column_count(400) == 1
    assert compute_column_count(600) == 2
    assert compute_column_count(900) == 3


def test_column_count_never_drops_below_one_or_exceeds_the_cap() -> None:
    assert compute_column_count(0) == 1
    assert compute_column_count(-50) == 1
    # A very wide window must not spread cards into an unreadable number of thin columns.
    assert compute_column_count(4000) == 4


def test_widening_the_window_reflows_into_more_columns(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    window.show()
    window.resize(500, 620)
    qt_app.processEvents()
    narrow_columns = window._column_count

    window.resize(1400, 620)
    qt_app.processEvents()

    # The reflow keys off the scroll area's viewport, not the window: the window resizes before
    # its children do, so reading its own width here would lag a step behind.
    assert window._column_count > narrow_columns
    window.hide()  # don't leave a visible top-level window alive into teardown


def test_clippings_are_dealt_across_the_columns_in_turn(qt_app: QApplication) -> None:
    # A mixed text/image history used to leave an empty cell wherever an image forced a row flush.
    # Cards now go into per-column stacks, one after another, so no gap can open up mid-list.
    service, _ = _build_populated_service()
    service.handle_new_clipboard_content(RawClipboardData(text="third"))
    window = MainWindow(service, prune_interval_ms=100_000)
    columns = window._column_layouts

    assert len(columns) == window._column_count
    card_counts = [
        column.count() - 1 for column in columns
    ]  # -1 for each column's trailing stretch
    assert sum(card_counts) == len(window.findChildren(ClippingWidget))
    # Dealing in turn means no column ever runs more than one card ahead of another.
    assert max(card_counts) - min(card_counts) <= 1


def test_rows_do_not_label_the_clipping_kind(qt_app: QApplication) -> None:
    window, _ = _build_populated_window()
    # The old header was "KIND · HH:MM:SS"; the kind label (and its "·" separator) is now gone.
    assert all("·" not in label.text() for label in window.findChildren(QLabel))
