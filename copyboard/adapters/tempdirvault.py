"""Store image bytes in the OS temp directory and reference them by path.

Implements the domain ``ClippingVault`` port. Uses stdlib ``tempfile`` so it works on Windows,
Linux and macOS, and writes files the OS is responsible for cleaning up — there is no managed
folder and no explicit deletion.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class TempDirVault:
    """Writes image bytes to a uniquely named temp file and returns its path."""

    def __init__(self, filename_prefix: str = "copyboard_") -> None:
        self._filename_prefix = filename_prefix

    def store_image_bytes(self, data: bytes, suffix: str) -> Path:
        with tempfile.NamedTemporaryFile(
            prefix=self._filename_prefix, suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(data)
            return Path(temp_file.name)
