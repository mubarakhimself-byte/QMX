"""status: what the coordinator reads on every wake and heartbeat tick.

For each held slice it reports liveness: a new push (the remote sha changed since the last tick) or
a heartbeat file touched by the timed wrapper. Neither within liveness_stale_s means STALE: the
coordinator saves leftovers, resets and restarts it (recover, then dispatch). It also reports the
hold, a pending usage reset, the breaker, free seats and which slices could start now.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from ship import state as st
from ship.gitx import GitError, remote_sha
from ship.layout import Program
from ship.settings import Settings
from ship.state import Status


def status(program: Program, settings: Settings, now: dt.datetime | None = None) -> tuple[bool, list[str]]:
    now = now or dt.datetime.now(dt.timezone.utc)
    lines: list[str] = []
    ok = True
    with st.locked(program) as state:
        repo = Path(state.repo)
        for sl in state.slices.values():
            if sl.status != Status.HELD:
                continue
            try:
                pushed = remote_sha(repo, state.remote, sl.branch, settings.net_timeout_s)
            except GitError:
                pushed = sl.seen_sha
            if pushed and pushed != sl.seen_sha:
                sl.seen_sha, sl.seen_at = pushed, now.isoformat(timespec="seconds")
            times = [dt.datetime.fromisoformat(sl.holder.started)]
            if sl.seen_at:
                times.append(dt.datetime.fromisoformat(sl.seen_at))
            beat = program.heartbeat(sl.id)
            if beat.exists():
                times.append(dt.datetime.fromtimestamp(beat.stat().st_mtime, dt.timezone.utc))
            quiet = (now - max(times)).total_seconds()
            if quiet >= settings.liveness_stale_s:
                ok = False
                lines.append(f"STALE {sl.id} {quiet / 60:.0f} min without a push or heartbeat ({sl.holder.dispatch_id})")
            else:
                lines.append(f"UP {sl.id} {quiet / 60:.0f} min since last sign of life")
        held = state.held_count()
        startable = sorted(s.id for s in state.slices.values() if s.status == Status.PENDING
                           and all(state.slices[d].status == Status.LANDED for d in s.depends_on))
        breaker = state.breaker_tripped(settings.breaker_parks)
        usage = state.usage_reset_at
    if program.hold.exists():
        lines.append(f"HOLD {program.hold.read_text('utf-8').strip()}")
    if usage and dt.datetime.fromisoformat(usage) > now:
        lines.append(f"USAGE limit until {usage}")
    if breaker:
        ok = False
        lines.append(f"BREAKER tripped: {settings.breaker_parks} quality parks in a row; stop the run")
    lines.append(f"SEATS {held} of {settings.seats} held; could start: {startable}")
    return ok, lines
