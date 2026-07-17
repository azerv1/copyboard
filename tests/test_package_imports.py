"""Smoke test: the package and its pure layers import without pulling in Qt."""

from __future__ import annotations

import copyboard


def test_package_exposes_version() -> None:
    assert copyboard.__version__ == "0.1.0"
