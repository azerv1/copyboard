"""Detach decisions: when to re-spawn, and which interpreter avoids a console window."""

from __future__ import annotations

import sys
from pathlib import Path

from copyboard.adapters.processdetach import (
    should_relaunch_detached,
    windowless_python_executable,
)


def test_relaunches_by_default_on_a_clean_environment() -> None:
    assert should_relaunch_detached({}) is True


def test_does_not_relaunch_when_already_the_detached_child() -> None:
    assert should_relaunch_detached({"COPYBOARD_DETACHED": "1"}) is False


def test_does_not_relaunch_when_foreground_is_requested() -> None:
    assert should_relaunch_detached({"COPYBOARD_FOREGROUND": "1"}) is False


def test_windowless_executable_is_an_existing_interpreter() -> None:
    assert Path(windowless_python_executable()).is_file()


def test_prefers_windowless_pythonw_on_windows() -> None:
    executable_name = Path(windowless_python_executable()).name
    if sys.platform == "win32":
        # pythonw.exe when it exists (the whole point), else the python.exe fallback.
        assert executable_name in {"pythonw.exe", "python.exe"}
    else:
        assert executable_name == Path(sys.executable).name
