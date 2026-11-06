"""The attribution mark (C-15, `EXTERNAL.md` section 2): reconcile attributes the test position as
mine.

The rehearsal places one entry through the node's order path and reads the account from a second
session, as a restart's reconcile does; the demo run does the same on his demo account. One PASS or
FAIL line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from qmf.core import is_refusal
from qmf.venue.commands import SubmissionOutcome
from qmn.app.attribution import Claim, attribute

MARK: Final = "attribution"
CLAIM: Final = "reconcile attributes the test position as mine"

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker, or one whose fill carries a label with no node tag on it."""
    import test_app_binding as binding  # noqa: PLC0415 - the tests are found by path

    class Untagged(binding.FakeCTrader):
        def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
            super()._on_ProtoOANewOrderReq(msg_id, {**body, "label": "someone-elses-position"})

    return Untagged(codec) if fault else binding.FakeCTrader(codec)


def crossing(session: Crossing) -> tuple[bool, str]:
    name = session.new_name("attr")
    sent = session.entry(name)
    if is_refusal(sent):
        return False, f"the order was refused ({sent})"
    if getattr(sent.value, "outcome", None) is not SubmissionOutcome.ACCEPTED_BY_VENUE:
        return False, "the order did not fill"
    read = session.adopted(name)
    if is_refusal(read):
        return False, f"the second session's read was refused ({read})"
    attributed = attribute(read.value, tag=session.label.split(":")[1], sent=[name])
    mine = [one for one, state in attributed.positions if state.claim is Claim.MINE]
    return (len(mine) == 1, f"{len(mine)} of {len(attributed.positions)} positions read as mine")


def rehearse(run: Any) -> tuple[bool, str]:
    return crossing(run)


def demo(session: Any) -> tuple[bool, str]:
    return crossing(session)
