"""The node's side of many positions: it says whether the venue keeps positions apart, it compiles
a two-position unit only there, and it runs each held position's own exits.

Both compile tests run the node's own ``compile_staged`` on a deployment staged the way the node
link stages it. The third hosts that compiled unit through the node's own door and reads the step.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import cast

from qmf.core import AccountRole, Instant, VenueId
from qmf.core.refusal import is_refusal
from qmf.risk.paper import ExecutionTarget
from qmf.risk.unit_intent import UnitExitIntent
from qml.compile import CompiledUnit
from qml.protocol.exits import PositionFacts
from qml.protocol.unit import (
    OHLC,
    Account,
    QuoteBar,
    Surface,
    construct_unit,
)
from qml.unit.model import Side
from qmn.app.runtime import compile_staged, parse_deployment, staging_folder
from qmn.app.store import Json

from test_app_runtime import deployment, rig

_MARKET = "fx.eurusd"
_EQUITY = Decimal("10000.00")
_START = 1_742_500_000_000_000_000
_BAR_NS = 900_000_000_000


def _two_positions(*, time_out_bars: str = "48") -> dict[str, object]:
    """The dummy document asking for two positions per market, with no other change."""
    from test_app_runtime import dummy_document

    document = cast("dict[str, object]", json.loads(json.dumps(dummy_document())))
    document["position_limit"] = {"per_instrument": 2}
    numbers = cast("dict[str, dict[str, object]]", document["numbers"])
    numbers["time_out_bars"]["default"] = time_out_bars
    return document


def _compiled(data: Path, *, nets: bool, time_out_bars: str = "48") -> CompiledUnit | str:
    """Compile the staged deployment as the node does, with the account's position model."""
    document = deployment(data)
    document["unit_document"] = cast("Json", _two_positions(time_out_bars=time_out_bars))
    parsed = parse_deployment(cast("Mapping[str, object]", document))
    return compile_staged(parsed, staging_folder(data, "dep-1"), nets_positions=nets)


def test_a_two_position_unit_compiles_where_the_venue_keeps_positions_apart(
    tmp_path: Path,
) -> None:
    setup = rig(tmp_path / "node")

    compiled = _compiled(setup.data, nets=False)

    assert isinstance(compiled, CompiledUnit), compiled
    assert compiled.plan.position_limit == 2


def test_a_two_position_unit_is_refused_by_name_on_a_netting_account(tmp_path: Path) -> None:
    setup = rig(tmp_path / "node")

    refused = _compiled(setup.data, nets=True)

    assert isinstance(refused, str), refused
    assert "holds more than one position per market" in refused
    assert "icmarkets-ctrader nets positions" in refused


def _bar(at: int, low: str) -> QuoteBar:
    bid = OHLC(Decimal("1.09700"), Decimal("1.09720"), Decimal(low), Decimal("1.09690"))
    ask = OHLC(
        bid.open + Decimal("0.00010"),
        bid.high + Decimal("0.00010"),
        bid.low + Decimal("0.00010"),
        bid.close + Decimal("0.00010"),
    )
    return QuoteBar(Instant(at), bid, ask)


class _Latest:
    """The last bar of the series knowable at the instant, as the node's handler serves it."""

    def __init__(self, bars: Sequence[QuoteBar]) -> None:
        self._bars = bars

    def at(self, instant: Instant, /) -> object:
        held = [bar for bar in self._bars if bar.knowable_at.value_ns <= instant.value_ns]
        return held[-1] if held else None


class _Fixed:
    def __init__(self, answer: object) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        del instant
        return self._answer


def _target() -> ExecutionTarget:
    made = ExecutionTarget.try_create(AccountRole.DEMO, VenueId("icmarkets-ctrader"), "a")
    assert not is_refusal(made), made
    return made.value


def test_two_positions_on_one_market_each_run_their_own_exit(tmp_path: Path) -> None:
    """Two longs held on one market, their time exit at one bar: the step closes both, and each
    close names its own position."""
    setup = rig(tmp_path / "node")
    compiled = _compiled(setup.data, nets=False, time_out_bars="1")
    assert isinstance(compiled, CompiledUnit), compiled
    first = PositionFacts(
        "own-1",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.09700"),
        compiled.logic_fingerprint,
        stop=Decimal("1.09500"),
    )
    second = PositionFacts(
        "own-2",
        Side.LONG,
        Decimal("0.10"),
        Decimal("1.09750"),
        compiled.logic_fingerprint,
        stop=Decimal("1.09600"),
    )
    surfaces: dict[str, Surface] = {
        "account": _Fixed(Account(_EQUITY)),
        "own_journal": _Fixed(()),
        "bars:m15:fx.eurusd": _Latest([_bar(_START, "1.09650")]),
        "bars:m15:metal.xauusd": _Latest([]),
        "own_position:fx.eurusd": _Fixed((first, second)),
        "own_position:metal.xauusd": _Fixed(()),
    }
    hosted = construct_unit(
        compiled,
        read_surfaces=surfaces,
        scope_id="dep-1",
        execution_target=_target(),
    )
    assert not is_refusal(hosted), hosted
    unit = hosted.value

    step = unit.on_instant(Instant(_START))

    assert not is_refusal(step), step
    closes = [intent for intent in step.value.intents if isinstance(intent, UnitExitIntent)]
    assert sorted(one.position_ref.position_id for one in closes) == ["own-1", "own-2"]
