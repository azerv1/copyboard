"""A single row in the viewer: a clipping's preview plus Copy / Delete actions.

Pure view code. It shows the clipping's ``build_preview_text`` (or, for images, a thumbnail rendered
from the temp-file path) under a muted timestamp; the kind is deliberately not labelled. User
actions are forwarded through injected callbacks so the widget never touches the service or domain
logic directly.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QDrag, QMouseEvent, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from copyboard.adapters.qt.clippingdragdata import build_drag_mime_data
from copyboard.domain.clipping import Clipping, ImageClipping

_THUMBNAIL_WIDTH = 160
_THUMBNAIL_HEIGHT = 90


class ClippingWidget(QWidget):
    """Renders one clipping and forwards Copy/Delete to the given callbacks by clipping id."""

    def __init__(
        self,
        clipping: Clipping,
        on_recopy: Callable[[str], None],
        on_delete: Callable[[str], None],
    ) -> None:
        super().__init__()
        self._clipping_id = clipping.id
        self._clipboard_payload = clipping.to_clipboard_payload()
        self._on_recopy = on_recopy
        self._on_delete = on_delete
        self._drag_start_position: QPoint | None = None

        row = QHBoxLayout(self)
        row.addLayout(self._build_content_column(clipping), stretch=1)
        row.addWidget(self._build_copy_button())
        row.addWidget(self._build_delete_button())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Presses that land on the Copy/Delete buttons are consumed by them and never reach here, so
        # a drag only ever begins from the preview/content area.
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not event.buttons() & Qt.MouseButton.LeftButton:
            return
        if self._drag_start_position is None:
            return
        moved_far_enough = (
            event.position().toPoint() - self._drag_start_position
        ).manhattanLength() >= QApplication.startDragDistance()
        if moved_far_enough:
            self._start_drag()

    def _start_drag(self) -> None:
        self._drag_start_position = None
        drag = QDrag(self)
        drag.setMimeData(build_drag_mime_data(self._clipboard_payload))
        # CopyAction: dragging out never removes the clipping from history.
        drag.exec(Qt.DropAction.CopyAction)

    def _build_content_column(self, clipping: Clipping) -> QVBoxLayout:
        # The kind (url/path/…) is intentionally not shown — the user can tell at a glance, so the
        # row stays uncluttered. A muted timestamp is the only chrome above the content.
        column = QVBoxLayout()
        timestamp = QLabel(f"{clipping.created_at:%H:%M:%S}")
        timestamp.setStyleSheet("color: gray; font-size: 11px;")
        column.addWidget(timestamp)
        column.addWidget(self._build_preview_label(clipping))
        return column

    def _build_preview_label(self, clipping: Clipping) -> QLabel:
        if isinstance(clipping, ImageClipping):
            return self._build_thumbnail_label(clipping)
        label = QLabel(clipping.build_preview_text())
        label.setWordWrap(True)
        return label

    def _build_thumbnail_label(self, clipping: ImageClipping) -> QLabel:
        label = QLabel()
        pixmap = QPixmap(str(clipping.path))
        if pixmap.isNull():
            label.setText(clipping.build_preview_text())
            return label
        label.setPixmap(
            pixmap.scaled(
                _THUMBNAIL_WIDTH,
                _THUMBNAIL_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        return label

    def _build_copy_button(self) -> QPushButton:
        button = QPushButton("Copy")
        button.clicked.connect(self._request_recopy)
        return button

    def _build_delete_button(self) -> QPushButton:
        button = QPushButton("Delete")
        button.clicked.connect(self._request_delete)
        return button

    def _request_recopy(self) -> None:
        self._on_recopy(self._clipping_id)

    def _request_delete(self) -> None:
        self._on_delete(self._clipping_id)
