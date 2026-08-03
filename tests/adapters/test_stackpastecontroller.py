"""The stack-paste controller binds the hotkey only while the mode is on."""

from __future__ import annotations

from copyboard.adapters.stackpastecontroller import StackPasteController


class FakeHotkeyBinder:
    """Records start/stop calls in order so bindings can be asserted without a real listener."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def start(self) -> None:
        self.calls.append("start")

    def stop(self) -> None:
        self.calls.append("stop")


def test_disabled_controller_never_binds_the_hotkey() -> None:
    binder = FakeHotkeyBinder()

    controller = StackPasteController(binder, initially_enabled=False)

    assert not controller.is_enabled
    assert binder.calls == []


def test_enabled_controller_binds_the_hotkey_immediately() -> None:
    binder = FakeHotkeyBinder()

    controller = StackPasteController(binder, initially_enabled=True)

    assert controller.is_enabled
    assert binder.calls == ["start"]


def test_toggling_off_then_on_rebinds_the_hotkey() -> None:
    binder = FakeHotkeyBinder()
    controller = StackPasteController(binder, initially_enabled=True)

    controller.set_enabled(False)
    controller.set_enabled(True)

    assert controller.is_enabled
    assert binder.calls == ["start", "stop", "start"]


def test_setting_the_same_state_twice_does_nothing() -> None:
    binder = FakeHotkeyBinder()
    controller = StackPasteController(binder, initially_enabled=True)

    controller.set_enabled(True)

    assert binder.calls == ["start"]


def test_shutdown_releases_the_binding() -> None:
    binder = FakeHotkeyBinder()
    controller = StackPasteController(binder, initially_enabled=True)

    controller.shutdown()

    assert not controller.is_enabled
    assert binder.calls == ["start", "stop"]
