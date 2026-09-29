"""Daemon handler for addable CT-40 query ``list_mailbox`` (Story 69.2; AM-08).

COMP-QMA-WIRE owns the query name. COMP-QMA-DAEMON owns this handler and the
mailbox fold. Seed 9/7/10 stay the seed. No new CT.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final
from urllib.parse import parse_qs

from qma.core.ports.mailbox import ENVELOPE_PRODUCT_SESSION_FIELD
from qma.daemon.bus.mailbox import MailboxStore, admit_named_product_session
from qma.daemon.sessions.product_session import ProductSessionService
from qma.wire.list_mailbox import (
    LIST_MAILBOX_CAPABILITY,
    LIST_MAILBOX_HTTP_PATH,
    MailboxSnapshot,
    parse_list_mailbox_args,
    require_list_mailbox_capability,
)
from qmf.core import Result, is_refusal

__all__ = [
    "LIST_MAILBOX_CAPABILITY",
    "LIST_MAILBOX_HTTP_PATH",
    "handle_list_mailbox_query",
    "query_string_to_args",
]


_PRESENT_CAPS: Final[Mapping[str, object]] = MappingProxyType({LIST_MAILBOX_CAPABILITY: True})


def query_string_to_args(query: str | None) -> Mapping[str, object]:
    """Map an HTTP query string onto list_mailbox args (first value per key)."""
    if query is None or query.strip() == "":
        return MappingProxyType({})
    parsed = parse_qs(query, keep_blank_values=True)
    outbound: dict[str, object] = {}
    for key, values in parsed.items():
        if not values:
            continue
        outbound[key] = values[0]
    return MappingProxyType(outbound)


def handle_list_mailbox_query(
    store: MailboxStore,
    args: object,
    *,
    operator_principal: object,
    sessions: ProductSessionService | None,
    capabilities: object = _PRESENT_CAPS,
) -> Result[MailboxSnapshot]:
    """Admit ``list_mailbox`` by principal equality, then fold the snapshot.

    Missing capability is typed ``query_unavailable``, never a successful empty
    mailbox. A present query on a new ``psess:`` with zero rows is empty.
    """
    gated = require_list_mailbox_capability(capabilities)
    if is_refusal(gated):
        return gated
    parsed = parse_list_mailbox_args(args)
    if is_refusal(parsed):
        return parsed
    named = parsed.value
    if ENVELOPE_PRODUCT_SESSION_FIELD in named:
        admitted = admit_named_product_session(
            named,
            operator_principal=operator_principal,
            sessions=sessions,
        )
        if is_refusal(admitted):
            return admitted
    return store.list_mailbox(named)
