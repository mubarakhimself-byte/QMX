"""The `label` mark (C-15, `EXTERNAL.md` section 2): a market order carries its label to the
position the broker opens.

The rehearsal trades the real node's order path over the fake broker with the real codec; the demo
run asks cTrader's demo broker the same thing. One PASS or FAIL line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from qmf.core import is_refusal
from qmf.venue.commands import SubmissionOutcome

MARK: Final = "label_survives"
CLAIM: Final = (
    "a market order with label and relativeStopLoss fills, and its position keeps the label"
)

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker, or one that fills the order and answers no label on the position."""
    import test_app_binding as binding  # noqa: PLC0415 - the tests are found by path

    class DropsLabel(binding.FakeCTrader):
        def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
            super()._on_ProtoOANewOrderReq(msg_id, {**body, "label": ""})

    return DropsLabel(codec) if fault else binding.FakeCTrader(codec)


def crossing(session: Crossing) -> tuple[bool, str]:
    sent = session.entry(session.new_name("label"))
    if is_refusal(sent):
        return False, f"the order was refused ({sent})"
    outcome = getattr(sent.value, "outcome", None)
    if outcome is not SubmissionOutcome.ACCEPTED_BY_VENUE:
        return False, f"the order did not fill ({outcome})"
    found = [one for one in session.broker_positions() if one[0] == session.label]
    if len(found) != 1:
        return False, f"{len(found)} positions carry this probe's label {session.label!r}"
    _, _lots, stop = found[0]
    session.observations["the fill's stop on the position"] = stop
    return (stop is not None, f"the position carries {session.label!r} and its stop {stop}")


def rehearse(run: Any) -> tuple[bool, str]:
    return crossing(run)


def demo(session: Any) -> tuple[bool, str]:
    return crossing(session)
