"""Composition root — the only place concrete adapters are wired into the service.

Builds the Qt application, the pure core (classifier, history, service) and every adapter
(clock, vault, clipboard source/sink, viewer, tray, global hotkey), connects them, and runs the
event loop. The global hotkey fires on a background thread, so its callback is bounced onto the GUI
thread through a queued Qt signal.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from copyboard.adapters.clipboardechoguard import ClipboardEchoGuard
from copyboard.adapters.pynputhotkeybinder import PynputHotkeyBinder
from copyboard.adapters.qt.qtclipboard import QtClipboardSink, QtClipboardSource
from copyboard.adapters.systemclock import SystemClock
from copyboard.adapters.tempdirvault import TempDirVault
from copyboard.adapters.ui.mainwindow import MainWindow
from copyboard.adapters.ui.trayicon import TrayIcon, create_default_tray_icon
from copyboard.application.copyboardservice import CopyboardService
from copyboard.config import AppConfig
from copyboard.config_loading import (
    DEFAULT_CONFIG_FILENAME,
    load_app_config_from_json,
    write_default_config_file,
)
from copyboard.domain.clippingclassifier import ClippingClassifier
from copyboard.domain.clippinghistory import ClippingHistory


class _HotkeyToggleBridge(QObject):
    """Marshals the background-thread hotkey callback onto the Qt GUI thread."""

    triggered = Signal()


def _open_config_in_editor(config_path: Path, config: AppConfig) -> None:
    """Open ``config.json`` in the OS default editor, seeding it with defaults if absent."""
    if not config_path.is_file():
        write_default_config_file(config_path, config)
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(config_path.resolve())))


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config_path = Path(DEFAULT_CONFIG_FILENAME)
    config = load_app_config_from_json(config_path)

    clock = SystemClock()
    classifier = ClippingClassifier(vault=TempDirVault(), clock=clock)
    history = ClippingHistory(config.retention)
    echo_guard = ClipboardEchoGuard()
    clipboard = app.clipboard()
    sink = QtClipboardSink(clipboard, echo_guard)
    service = CopyboardService(classifier=classifier, history=history, clock=clock, sink=sink)

    source = QtClipboardSource(clipboard, echo_guard)
    source.set_new_content_listener(service.handle_new_clipboard_content)

    window = MainWindow(service)
    window.show()

    tray = TrayIcon(
        create_default_tray_icon(),
        window.toggle_visibility,
        lambda: _open_config_in_editor(config_path, config),
        app.quit,
    )
    tray.show()

    bridge = _HotkeyToggleBridge()
    bridge.triggered.connect(window.toggle_visibility, Qt.ConnectionType.QueuedConnection)
    hotkey = PynputHotkeyBinder(config.hotkey.toggle_viewer_hotkey, lambda: bridge.triggered.emit())
    hotkey.start()

    try:
        return app.exec()
    finally:
        hotkey.stop()


if __name__ == "__main__":
    raise SystemExit(main())
