"""The echo guard is a one-shot latch (pure, no Qt)."""

from __future__ import annotations

from copyboard.adapters.clipboardechoguard import ClipboardEchoGuard


def test_guard_starts_unarmed() -> None:
    assert ClipboardEchoGuard().consume_if_armed() is False


def test_arm_then_consume_returns_true_exactly_once() -> None:
    guard = ClipboardEchoGuard()
    guard.arm()
    assert guard.consume_if_armed() is True
    assert guard.consume_if_armed() is False
