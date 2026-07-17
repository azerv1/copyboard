"""``should_relaunch_detached`` decides whether to re-spawn detached based on the environment."""

from __future__ import annotations

from copyboard.adapters.processdetach import should_relaunch_detached


def test_relaunches_by_default_on_a_clean_environment() -> None:
    assert should_relaunch_detached({}) is True


def test_does_not_relaunch_when_already_the_detached_child() -> None:
    assert should_relaunch_detached({"COPYBOARD_DETACHED": "1"}) is False


def test_does_not_relaunch_when_foreground_is_requested() -> None:
    assert should_relaunch_detached({"COPYBOARD_FOREGROUND": "1"}) is False
