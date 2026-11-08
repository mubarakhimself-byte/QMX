"""The `partial` mark (C-15, `EXTERNAL.md` section 2): a part-volume close keeps the label on
the remainder.

The rehearsal asks the fake broker through the real codec for half the position and reads the rest
back through the node; the demo run asks cTrader's demo broker. One PASS or FAIL line.
"""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import importlib
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Final, cast

from qmf.core import is_refusal
from qmf.venue.commands import SubmissionOutcome

MARK: Final = "partial_keeps_label"
CLAIM: Final = "a partial close keeps the label on the remainder"
REMAINDER: Final = Decimal("0.005")
"""Half of the probe's one-hundredth of a lot, in lots."""

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker, or an older one that closes the whole position whatever volume it is
    asked for."""
    binding: Any = cast(Any, importlib.import_module("test_app_binding"))

    class WholePositionClose(binding.FakeCTrader):
        def _on_ProtoOAClosePositionReq(self, msg_id: str, body: dict[str, object]) -> None:
            held = self.held.get(int(str(body["positionId"])))
            whole = 0 if held is None else held.volume
            super()._on_ProtoOAClosePositionReq(msg_id, {**body, "volume": str(whole)})

    return WholePositionClose(codec) if fault else binding.FakeCTrader(codec)


def crossing(session: Crossing) -> tuple[bool, str]:
    name = session.new_name("part")
    sent = session.entry(name)
    if is_refusal(sent):
        return False, f"the order was refused ({sent})"
    if getattr(sent.value, "outcome", None) is not SubmissionOutcome.ACCEPTED_BY_VENUE:
        return False, "the order did not fill"
    before = [one for one in session.broker_positions() if one[0] == session.label]
    if len(before) != 1:
        return False, f"{len(before)} positions carry this probe's label before the close"
    read = session.close_part(name)
    if read is None or is_refusal(read):
        return False, f"the part-volume close was refused ({read})"
    after = [one for one in session.broker_positions() if one[0] == session.label]
    if len(after) != 1:
        return False, f"{len(after)} positions carry the label after the partial close"
    label, lots, _stop = after[0]
    return (
        lots == REMAINDER and label == session.label,
        f"the remainder carries {label!r} at {lots} lots",
    )


def rehearse(run: Any) -> tuple[bool, str]:
    return crossing(run)


def demo(session: Any) -> tuple[bool, str]:
    return crossing(session)
