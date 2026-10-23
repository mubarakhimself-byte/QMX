"""Download-once policy: runs never fetch from a provider (B-11, AR-54), and the checks a
typed-partition replay read applies before it trusts a price file (W12, N2).

The CT-10 reader trusts an admission boundary on the way in. The typed-partition reader takes
files the market-data door materialised, so the same four facts are checked here instead: the
world is replay, the file's streamed fingerprint is the one claimed for it, the holdout seal
does not cover a row, and every row belongs to the split role the run asked for.
"""

from __future__ import annotations

import re
from typing import Final

from qmf.core.chrono import Instant
from qmf.core.fingerprint import World
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.seal import HoldoutSeal
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest

from qmb._refuse import invalid, policy

__all__ = [
    "check_typed_fingerprint",
    "check_typed_instant",
    "check_typed_sealed",
    "check_typed_world",
    "refuse_run_provider_fetch",
]

_FINGERPRINT: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")


def refuse_run_provider_fetch(*, request: object | None = None) -> Result[None]:
    """Refuse a run-loop / backtest / sweep attempt to fetch from a provider.

    ``data download`` is the sole provider-fetch surface. Runs read only
    qmf-data rooms; a provider fetch from a run is a ``policy rejection``.
    """
    context: dict[str, object] = {
        "signal": "refuse-run-provider-fetch",
        "sole_fetch_surface": "qmb data download",
        "contract": "B-11",
    }
    if request is not None:
        context["request"] = repr(request)
    return policy(
        "provider_fetch",
        "runs read only qmf-data rooms and never fetch from a provider; "
        "qmb data download is the sole provider-fetch surface (AR-54, DEC-0166)",
        **context,
    )


def check_typed_world(world: object) -> Result[World]:
    """Coerce a typed read's world and require replay, as ``read_recorded_replay_source`` does."""
    checked: object = world
    if isinstance(world, str):
        try:
            checked = World(world)
        except ValueError:
            return invalid("world", "typed replay data is read from a QMF world", given=world)
    if not isinstance(checked, World):
        return invalid("world", "typed replay data names its QMF world", given=repr(world))
    if checked is not World.REPLAY:
        return policy("world", "QMB typed replay materialization requires world=replay")
    return Ok(checked)


def check_typed_fingerprint(
    *, series: object, month: object, claimed: object, computed: str
) -> Result[str]:
    """Require the fingerprint claimed for a partition to be the one its rows hash to.

    ``computed`` is what the rows hash to through the writer that defines the encoding. A
    claim that is not a sha256 token is the caller's mistake; a well-formed claim that differs
    is a governed-evidence miss, because those bytes are not that partition, and a replay over
    them would cite a release it never read.
    """
    if not isinstance(claimed, str) or _FINGERPRINT.fullmatch(claimed) is None:
        return invalid(
            "fingerprint", "a typed partition is claimed by its sha256 token", given=repr(claimed)
        )
    if claimed != computed:
        return policy(
            "fingerprint",
            "the file's rows hash to the fingerprint claimed for this partition",
            series=series,
            month=month,
            claimed=claimed,
            computed=computed,
        )
    return Ok(claimed)


def check_typed_sealed(*, seal: HoldoutSeal, month: object, instant_ns: int) -> Result[None]:
    """Refuse a typed row inside the sealed no-peek window, naming the month (F8, D-5)."""
    position = SplitBoundary.try_create(instant_ns)
    if is_refusal(position):
        return position
    sealed = seal.is_sealed(position.value)
    if is_refusal(sealed):
        return sealed
    if sealed.value:
        return policy(
            "seal",
            "a typed replay read stays outside the holdout seal; a sealed month is refused at "
            "the door that served it and never replayed",
            month=month,
            instant_ns=instant_ns,
            seal_boundary=seal.seal_boundary.label(),
        )
    return Ok(None)


def check_typed_instant(
    *, manifest: SplitManifest, role: SegmentRole, month: object, instant_ns: int
) -> Result[None]:
    """Require one typed row to belong to the split role the run asked for (CT-12)."""
    instant = Instant.try_create(instant_ns)
    if is_refusal(instant):
        return instant
    index = manifest.instant_segment_index(instant.value)
    if index is None:
        return invalid(
            "split_role",
            "every typed row falls inside the CT-12 split it is replayed against",
            month=month,
            instant_ns=instant_ns,
        )
    purged = manifest.purge_zone_refusal(instant.value, index)
    if purged is not None:
        return purged
    actual = manifest.segments[index].role
    if actual is not role:
        return policy(
            "split_role",
            "every typed row belongs to the requested CT-12 role",
            month=month,
            instant_ns=instant_ns,
            expected=role.value,
            actual=actual.value,
        )
    return Ok(None)
