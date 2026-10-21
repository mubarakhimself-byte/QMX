"""P-EV: event triggers read the Hub's ref log, so a fire lands within two ticks and a claim
round trip stays under a second (TRG2b's first Build box, AD-64, Library AD-11).

Run from `qmx-agents/` with the agents venv, on the PC:

    uv run --no-sync python ../scripts/probes/server/p_ev.py

The probe is the `pev` lane of `scripts/live/server/e63_chain.py`, which owns the server recipe: one
process on the server holds the Library (one writer per root), serves the Hub's door from it and
runs the engine over the same store at the default 60 s tick. The PC lands one `bias` artifact in
its own store and syncs the run ref to the Hub, so the fire follows a row that arrived by
replication. Pass is a fire within two ticks of the object reaching the Hub and a claim round trip
under 1 s at p95; the result sets `scheduler.tick` for event triggers, so the push stream on the
engine event stream ships only when this fails.

Writes `<TRG2B_EVIDENCE>/owner-trg2b-pev.log`.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

HERE: Final = Path(__file__).resolve().parent
LANES: Final = HERE.parents[1] / "live" / "server"


def main(argv: Sequence[str] | None = None) -> int:
    sys.path.insert(0, str(LANES))
    from e63_chain import main as lane  # noqa: PLC0415

    return lane(["--lane", "pev", *(argv or ())])


if __name__ == "__main__":
    raise SystemExit(main())
