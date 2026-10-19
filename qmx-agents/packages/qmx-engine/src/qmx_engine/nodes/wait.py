"""The `wait` node, and the clock arithmetic for holds.

The core starts a `wait` node only once its hold is due (`qmx_engine.core.waits`); the node then
passes its input on `main`. `resume_at` is the driver's half of a hold: it turns `seconds` into an
instant on the run's recorded clock, which the core cannot do (AD-6). Every instant the driver
writes, the clock's and a hold's alike, is RFC 3339 in UTC (`utc_text`), and a
naive instant is read as UTC, never as local time (L-37).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from qmx_engine.core.commands import Hold
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok


def utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def utc_text(moment: datetime) -> str:
    return utc(moment).isoformat()


def resume_at(hold: Hold, now: str) -> str | None:
    """`now` plus the hold's seconds, or its `until`, in UTC; None for an event hold."""
    if hold.seconds is not None:
        moment = datetime.fromisoformat(now) + timedelta(seconds=hold.seconds)
    elif hold.until is not None:
        moment = datetime.fromisoformat(hold.until)
    else:
        return None
    return utc_text(moment)


class Wait:
    def run(self, job: NodeJob) -> NodeResult:
        ports = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"main": ports.get("in")})
