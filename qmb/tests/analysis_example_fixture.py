"""Provider-free persisted replay builder supplied explicitly to analysis examples."""

from pathlib import Path

from qmb.analysis import CT29ProjectionSource
from qmf.core import Instant, Ok, Result, is_refusal
from replay_fixture_support import build_projection_replay


def analysis_source(root: Path) -> Result[tuple[object, CT29ProjectionSource]]:
    replay = build_projection_replay(
        root,
        registry_as_of=Instant(value_ns=1_700_006_400_000_000_000),
        entry_offsets_hours=(0, 8),
        entry_start_ns=1_700_042_400_000_000_000,
    )
    if is_refusal(replay):
        return replay
    return Ok((replay.value.performance_result, replay.value.source))
