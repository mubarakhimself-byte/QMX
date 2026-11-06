"""The network-cut mark (C-15, `EXTERNAL.md` section 2, TN-01): the socket closed right after a
send leaves exactly one position after reconnect, and no resend.

The rehearsal makes the fake broker carry the entry out and lose its answer, drops the socket and
reopens the session, then reads what the node holds; the demo run sends one order and cuts the
session before reading the answer, then reconnects and reads the account. One PASS or FAIL line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from qmf.core import is_refusal
from qmf.venue.commands import SubmissionOutcome

MARK: Final = "network_cut"
CLAIM: Final = (
    "the socket cut right after a send leaves exactly one position after reconnect, and no resend"
)

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker, or one that lists the held position twice after the reconnect."""
    import test_app_binding as binding  # noqa: PLC0415 - the tests are found by path

    class DoubleListed(binding.FakeCTrader):
        def _on_ProtoOAReconcileReq(self, msg_id: str, _: dict[str, object]) -> None:
            rows = [self._position(one, "POSITION_STATUS_OPEN") for one in self.held.values()]
            self._say(
                "ProtoOAReconcileRes",
                {"ctidTraderAccountId": 4401, "position": [*rows, *rows]},
                msg_id,
            )

    return DoubleListed(codec) if fault else binding.FakeCTrader(codec)


def rehearse(run: Any) -> tuple[bool, str]:
    run.fake.lose_answers = 1
    sent = run.entry(run.new_name("cut"))
    if is_refusal(sent):
        return False, f"the order was refused ({sent})"
    if getattr(sent.value, "outcome", None) is not SubmissionOutcome.UNKNOWN:
        return False, f"the lost answer did not read UNKNOWN ({sent.value.outcome})"
    run.fake.drop_socket()
    run.heal()
    found = [one for one in run.positions() if one.label == run.label]
    return (
        len(found) == 1 and run.entries() == 1,
        f"{len(found)} positions and {run.entries()} order requests after the reconnect",
    )


def demo(session: Crossing) -> tuple[bool, str]:
    pushed = session.push_order(session.new_name("cut"))
    if pushed is None or is_refusal(pushed):
        return False, f"the order did not go down the wire ({pushed})"
    session.venue.close()
    reopened = session.venue.connect()
    if is_refusal(reopened):
        return False, f"the session did not reopen ({reopened})"
    verified = session.venue.verify()
    if is_refusal(verified):
        return False, f"the session did not verify ({verified})"
    found = [one for one in session.positions() if one.label == session.label]
    return (len(found) == 1, f"{len(found)} positions after the reconnect, and no resend")
