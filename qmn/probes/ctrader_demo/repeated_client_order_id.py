"""The duplicate mark (C-15, `EXTERNAL.md` section 2): a second order with the same
`clientOrderId` is either refused by cTrader or accepted, and the probe records which.

The rehearsal sends both orders down the real codec to the fake broker; the demo run sends them to
cTrader's demo broker. One PASS or FAIL line, and the recorded answer is on it.
"""

# pyright: reportUnknownMemberType=false

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, Final, cast

MARK: Final = "repeated_client_order_id"
CLAIM: Final = (
    "a second order with the same clientOrderId is refused or accepted, and which is recorded"
)

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker, or one that answers the second order with silence."""
    binding: Any = cast(Any, importlib.import_module("test_app_binding"))

    class SilentSecond(binding.FakeCTrader):
        seen = 0

        def _on_ProtoOANewOrderReq(self, msg_id: str, body: dict[str, object]) -> None:
            self.seen += 1
            if self.seen > 1:
                return
            super()._on_ProtoOANewOrderReq(msg_id, body)

    return SilentSecond(codec) if fault else binding.FakeCTrader(codec)


def crossing(session: Crossing) -> tuple[bool, str]:
    answer = session.duplicate(session.new_name("dup"))
    if answer.startswith(("accepted", "refused")):
        return True, answer
    return False, answer


def rehearse(run: Any) -> tuple[bool, str]:
    return crossing(run)


def demo(session: Any) -> tuple[bool, str]:
    return crossing(session)
