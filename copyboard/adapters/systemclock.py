"""Real-time :class:`~copyboard.domain.ports.Clock` implementation."""

from __future__ import annotations

from datetime import datetime


class SystemClock:
    """Returns the current local time. Implements the domain ``Clock`` port structurally."""

    def now(self) -> datetime:
        return datetime.now()
