"""The temp-dir vault writes readable image files to the OS temp directory."""

from __future__ import annotations

from copyboard.adapters.tempdirvault import TempDirVault


def test_store_image_bytes_writes_a_readable_temp_file() -> None:
    vault = TempDirVault()
    data = b"\x89PNG\r\n\x1a\n fake image bytes"

    stored_path = vault.store_image_bytes(data, suffix=".png")

    try:
        assert stored_path.exists()
        assert stored_path.suffix == ".png"
        assert stored_path.read_bytes() == data
    finally:
        stored_path.unlink()
