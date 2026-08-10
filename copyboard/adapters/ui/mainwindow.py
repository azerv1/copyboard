"""The viewer window: a scrollable, newest-first list of recent clippings.

Implements the application's ``HistoryObserver``. History-change notifications are bounced through a
Qt signal with a queued connection, so the list refresh always runs on the GUI thread regardless of
which thread produced the change. A ``QTimer`` periodically asks the service to drop expired
clippings, which drives time-based retention even when nothing new is copied.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from copyboard.adapters.ui.clippingwidget import ClippingWidget
from copyboard.application.copyboardservice import CopyboardService
from copyboard.application.events import HistoryChangeEvent
from copyboard.config import UIConfig

_DEFAULT_PRUNE_INTERVAL_MS = 1000

_MIN_COLUMN_WIDTH_PX = 280
_MAX_COLUMNS = 4


def compute_column_count(available_width_px: int) -> int:
    """How many card columns fit in ``available_width_px``, clamped to 1..``_MAX_COLUMNS``.

    Keeping this a plain function (rather than reading the widget geometry inline) makes the
    reflow rule testable without constructing a window.
    """
    fitting_columns = available_width_px // _MIN_COLUMN_WIDTH_PX
    return max(1, min(_MAX_COLUMNS, fitting_columns))


class MainWindow(QWidget):
    """Shows the live clipping history and wires row actions back to the service."""

    _history_changed = Signal()

    def __init__(
        self,
        service: CopyboardService,
        ui_config: UIConfig | None = None,
        prune_interval_ms: int = _DEFAULT_PRUNE_INTERVAL_MS,
        on_stack_paste_toggled: Callable[[bool], None] | None = None,
        stack_paste_enabled: bool = False,
    ) -> None:
        super().__init__()
        self._service = service
        self._ui_config = ui_config or UIConfig()
        self._on_stack_paste_toggled = on_stack_paste_toggled
        self.setWindowTitle("Copyboard")
        self.resize(500, 620)
        # Required for Qt to paint the glass theme's stylesheet `background`/`border` on this plain
        # QWidget subclass; without it the translucent gradient frame is never drawn.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer_layout = QVBoxLayout(self)
        outer_layout.addLayout(self._build_header_row(stack_paste_enabled))
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._list_container = QWidget()
        self._list_layout = QGridLayout(self._list_container)
        self._list_layout.setSpacing(6)
        self._column_count = compute_column_count(self.width())
        self._scroll_area.viewport().installEventFilter(self)
        self._scroll_area.setWidget(self._list_container)
        outer_layout.addWidget(self._scroll_area)

        service.register_observer(self)
        self._history_changed.connect(
            self._refresh_clipping_list, Qt.ConnectionType.QueuedConnection
        )

        self._prune_timer = QTimer(self)
        self._prune_timer.timeout.connect(self._service.remove_expired_clippings)
        self._prune_timer.start(prune_interval_ms)

        self._refresh_clipping_list()

    def _build_header_row(self, stack_paste_enabled: bool) -> QHBoxLayout:
        """The window's top strip: the stack-paste toggle, right-aligned above the list."""
        header_layout = QHBoxLayout()
        header_layout.addStretch(1)
        header_layout.addWidget(self._build_stack_paste_button(stack_paste_enabled))
        return header_layout

    def _build_stack_paste_button(self, stack_paste_enabled: bool) -> QPushButton:
        button = QPushButton()
        button.setCheckable(True)
        button.setChecked(stack_paste_enabled)
        button.setToolTip(
            "While on, the paste hotkey pops the newest clipping off the history (LIFO) "
            "instead of pasting the same thing repeatedly."
        )
        button.toggled.connect(self._handle_stack_paste_toggled)
        self._stack_paste_button = button
        self._update_stack_paste_button_text(stack_paste_enabled)
        return button

    def _handle_stack_paste_toggled(self, enabled: bool) -> None:
        self._update_stack_paste_button_text(enabled)
        if self._on_stack_paste_toggled is not None:
            self._on_stack_paste_toggled(enabled)

    def _update_stack_paste_button_text(self, enabled: bool) -> None:
        self._stack_paste_button.setText(f"Stack paste: {'On' if enabled else 'Off'}")

    def on_history_changed(self, event: HistoryChangeEvent) -> None:
        self._history_changed.emit()

    def toggle_visibility(self) -> None:
        """Hide only when already frontmost; otherwise surface the window to the front.

        Pressing the hotkey while the window sits behind another app should raise it, not hide it,
        so we hide only when it is both visible and the active window.
        """
        if self.isVisible() and self.isActiveWindow():
            self.hide()
            return
        self.bring_to_front()

    def bring_to_front(self) -> None:
        """Show, un-minimise, and take focus so the window pops in front of other apps."""
        self.setWindowState(
            (self.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
        )
        self.show()
        self.raise_()
        self.activateWindow()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Reflow the grid when the viewport becomes wide (or narrow) enough for another column.

        The filter watches the scroll area's *viewport* rather than overriding this window's
        ``resizeEvent``: the window resizes before its children do, so reading the viewport width
        there yields the previous size and the column count lags a step behind.
        """
        if watched is self._scroll_area.viewport() and event.type() == QEvent.Type.Resize:
            self._reflow_if_column_count_changed()
        return super().eventFilter(watched, event)

    def _reflow_if_column_count_changed(self) -> None:
        column_count = compute_column_count(self._scroll_area.viewport().width())
        if column_count == self._column_count:
            return
        self._column_count = column_count
        self._refresh_clipping_list()

    def _refresh_clipping_list(self) -> None:
        self._clear_list_layout()
        current_clipboard_id = self._service.get_current_clipboard_clipping_id()
        row, col = 0, 0
        for clipping in self._service.list_clippings_newest_first():
            widget = ClippingWidget(
                clipping,
                self._service.recopy_clipping_by_id,
                self._service.delete_clipping_by_id,
                actions_on_right_click=self._ui_config.actions_on_right_click,
                is_current_clipboard_item=clipping.id == current_clipboard_id,
            )
            self._list_layout.addWidget(widget, row, col)
            col += 1
            if col == self._column_count:
                col = 0
                row += 1
        self._apply_grid_stretch(last_row=row if col else row - 1)

    def _apply_grid_stretch(self, last_row: int) -> None:
        """Give every live column equal width and park the leftover height below the last row.

        Without the trailing row stretch ``QGridLayout`` shares spare vertical space out among the
        card rows; without clearing the stretch on columns beyond the current count, a grid that
        was previously wider keeps reserving space for columns that no longer hold anything.
        """
        for column in range(self._list_layout.columnCount()):
            self._list_layout.setColumnStretch(column, 1 if column < self._column_count else 0)
        for stale_row in range(self._list_layout.rowCount()):
            self._list_layout.setRowStretch(stale_row, 0)
        self._list_layout.setRowStretch(last_row + 1, 1)

    def _clear_list_layout(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
