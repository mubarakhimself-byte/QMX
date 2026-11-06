"""The refresh mark (C-15, `EXTERNAL.md` section 2, TN-05): a forced grant refresh stores the new
grant before discarding the old, the session comes back ready, and a second refresher is refused.

The rehearsal drives the node's own `Grants` over the fake token endpoint and the fake broker; the
demo run does the same on the node's grant store and cTrader's token endpoint, on his demo account.
One PASS or FAIL line.
"""

from __future__ import annotations

import importlib
import json
import time
from typing import TYPE_CHECKING, Any, Final, cast

from qmf.core import is_refusal
from qmn.app.grants import Grant, Grants, TokenEndpoint, registration

MARK: Final = "refresh"
CLAIM: Final = (
    "a forced grant refresh stores the new grant before discarding the old, the session comes"
    " back ready, and a second refresher is refused"
)

if TYPE_CHECKING:
    from run import Crossing


def broker(codec: Any, *, fault: bool) -> Any:
    """The fake broker as it is; this mark's fault is in the token endpoint, not here."""
    binding: Any = cast(Any, importlib.import_module("test_app_binding"))

    return binding.FakeCTrader(codec)


class _Refusing:
    """One grant slot that refuses the new ciphertext, so the old material must stay."""

    def __init__(self, held: str) -> None:
        self.held = held

    @property
    def name(self) -> str:
        return "probe-refusing"

    def read(self) -> str | None:
        return self.held

    def write(self, text: str, /) -> None:
        raise OSError("the probe's store refused the write")

    def delete(self) -> None:
        self.held = None


def rehearse(run: Any) -> tuple[bool, str]:
    """The node's own refresher over the rig's grant store and token endpoint."""
    binding: Any = cast(Any, importlib.import_module("test_app_binding"))

    app = registration(binding.KEYS)
    if app is None:
        return False, "the rig's keys document names no trading app"
    tokens = run.rig.tokens
    if run.fault:
        tokens.refuse_refresh = True
    grants = run.rig.door.grants
    before = run.rig.grants.held or "{}"
    kept = grants.refresh(app)
    if is_refusal(kept):
        return False, f"the refresh was refused ({kept.context.get('code')})"
    stored = json.loads(run.rig.grants.held or "{}")
    if stored.get("access_token") == json.loads(before).get("access_token"):
        return False, "the store still holds the old access token"
    run.fake.tokens.add(str(stored["access_token"]))
    reopened = run.venue.connect()
    if is_refusal(reopened):
        return False, f"the session did not reopen ({reopened.context.get('code')})"
    verified = run.venue.verify()
    if is_refusal(verified):
        return False, f"the session did not come back ready ({verified.context.get('code')})"
    gate = grants.gate
    acquired = gate.acquire(grants.ref)
    if is_refusal(acquired):
        return False, f"the gate was already held ({acquired.context.get('code')})"
    try:
        second = grants.refresh(app)
    finally:
        gate.release(grants.ref)
    if not is_refusal(second) or second.context.get("code") != "refresh_in_flight":
        return False, f"a second refresher was not refused in flight ({second!r})"

    refusing = _Refusing(before)
    held_back = Grants(refusing, TokenEndpoint(fetch=tokens), lambda: False, time.time_ns)
    refused = held_back.refresh(app)
    kept_pair = held_back.held()
    old = Grant.parse(before)
    if not is_refusal(refused) or refused.context.get("code") != "grant_not_stored":
        return False, f"a store that refuses the write was not named ({refused!r})"
    if old is None or kept_pair is None or kept_pair.tokens.access == old.tokens.access:
        return False, "the new pair was not held after the store refused it"
    if refusing.held != before:
        return False, "the old grant was discarded before the new one was stored"
    return True, (
        "the store took the new pair before the old was let go, the session reads ready, a second"
        " refresher was refused in flight, and a refusing store kept the new pair"
    )


def demo(session: Crossing) -> tuple[bool, str]:
    return session.refresh()
