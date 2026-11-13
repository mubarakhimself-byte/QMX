"""The kit's one clock. `SHIP_FAKE_NOW` naming a file makes it read the ISO time written there."""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path


def now() -> dt.datetime:
    """UTC now, or the time in the file `SHIP_FAKE_NOW` names, so tests can move time."""
    fake = os.environ.get("SHIP_FAKE_NOW")
    if fake and Path(fake).is_file():
        when = dt.datetime.fromisoformat(Path(fake).read_text("utf-8").strip())
        return when if when.tzinfo else when.replace(tzinfo=dt.timezone.utc)
    return dt.datetime.now(dt.timezone.utc)
