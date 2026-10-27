"""Which CCXT exchanges give QMX a demo mode, asked of CCXT itself rather than kept by hand."""

from __future__ import annotations

import functools
from typing import Any


@functools.cache
def demo_refusal(exchange: str) -> str | None:
    """The line that refuses a demo account on `exchange`, or None when CCXT gives it a demo mode
    or knows no such exchange (that keeps its own refusal). It runs what a demo read runs, on a
    fresh exchange object with no keys, which opens no socket; a CCXT upgrade changes the answer
    by itself. Cached per exchange id for the process's life."""
    import ccxt  # pyright: ignore[reportMissingTypeStubs] # noqa: PLC0415 - untyped upstream

    if exchange not in ccxt.exchanges:
        return None
    probe: Any = getattr(ccxt, exchange)({})
    try:
        probe.set_sandbox_mode(True)
    except Exception:
        return (
            f"{exchange} has no demo mode in CCXT, so QMX cannot read a demo account there; "
            "use a live read-only key or another exchange"
        )
    return None
