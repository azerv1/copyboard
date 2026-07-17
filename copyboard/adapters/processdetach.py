"""Re-launch the app as a detached background process so the launching shell is freed.

A tray app should not tie up the terminal it was started from. On first launch we re-spawn a
detached copy of ourselves — guarded by an environment variable so the child does not do it again —
and let the original process exit immediately, returning the shell. Set ``COPYBOARD_FOREGROUND=1``
to skip detaching and run attached to the terminal (useful for development, debugging, and tests).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

_DETACHED_GUARD_ENV = "COPYBOARD_DETACHED"
_FOREGROUND_ENV = "COPYBOARD_FOREGROUND"


def windowless_python_executable() -> str:
    """The interpreter to re-launch with, chosen so no console window ever appears.

    On Windows ``python.exe`` is a console-subsystem binary that briefly allocates a console (a
    visible flash) even when detached, so we prefer ``pythonw.exe`` — the GUI-subsystem interpreter
    that has no console at all — when it sits next to the current interpreter. Elsewhere, and if
    ``pythonw.exe`` is missing, fall back to the current interpreter.
    """
    if sys.platform == "win32":
        windowless = Path(sys.executable).with_name("pythonw.exe")
        if windowless.is_file():
            return str(windowless)
    return sys.executable


def should_relaunch_detached(env: Mapping[str, str]) -> bool:
    """Whether this process should re-spawn itself detached and exit.

    ``False`` when we are already the detached child (the guard is set) or the user asked to stay in
    the foreground; ``True`` otherwise.
    """
    already_detached_child = env.get(_DETACHED_GUARD_ENV) == "1"
    foreground_requested = env.get(_FOREGROUND_ENV) == "1"
    return not (already_detached_child or foreground_requested)


def relaunch_detached() -> None:
    """Spawn a detached copy of this app with no controlling terminal or console window.

    The child re-enters through ``pythonw -m copyboard`` (see :func:`windowless_python_executable`),
    inheriting the environment plus the guard flag so it runs the real app instead of detaching
    again. Standard streams are sent to the null device so nothing keeps the shell open.
    """
    child_env = dict(os.environ)
    child_env[_DETACHED_GUARD_ENV] = "1"
    command = [windowless_python_executable(), "-m", "copyboard", *sys.argv[1:]]

    creation_flags = 0
    start_new_session = False
    if sys.platform == "win32":
        # DETACHED_PROCESS: no console is inherited or created. CREATE_NO_WINDOW belts-and-suspenders
        # against any console-subsystem fallback. Together with pythonw.exe there is no flash.
        creation_flags = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        start_new_session = True

    # Fixed argv, no shell — intentionally not waited on so the app runs independently.
    subprocess.Popen(
        command,
        env=child_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creation_flags,
        start_new_session=start_new_session,
    )
