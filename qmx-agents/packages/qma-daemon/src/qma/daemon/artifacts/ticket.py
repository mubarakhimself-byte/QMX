"""AM-03 ``artifact_transfer_ticket`` journal projection (Story 70.2).

Named add on the existing sqlite class — not a new class, not definition-store
slot 17+, not a Library row. Live shape is open tickets. Fold: stream
``noun.verb``, ordering ``journal_seq``, knowledge-time ``as_of`` over
``recorded_at``, equal-instant ascending ``journal_seq``. Do not set
``superseded_by``.

``transfer_artifact`` issues a ticket only when the recorded source origin is
non-loopback TLS on the destination environment inherited allowlist. The daemon
never dials in and never opens an inbound port on the deployed side. Dest
control is notified when live; otherwise the ticket stays ``issued`` until
reconnect. Same-daemon selected instance requires no transfer.
"""

from __future__ import annotations

import fnmatch
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast
from urllib.parse import urlsplit

from qma.core.barriers.credential_allowlist import is_credential_ref_allowed
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.artifacts.store import ArtifactStore, StagedArtifact
from qma.daemon.host_control.local_operator import (
    DEC_0429_SUPERSEDED_BY,
    DEC_0440_SUPERSEDED_BY,
)
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.stores import StoreClass
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.wire.listener import DEFAULT_BIND_HOST, is_loopback_host
from qma.wire.stage_artifact import claim_artifact_store_types_absent_at_inspect_sha
from qma.wire.transfer_artifact import (
    TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA,
    TRANSFER_ARTIFACT_INSPECT_SHA,
    claim_transfer_artifact_existed_at_inspect_sha,
    parse_transfer_artifact_payload,
    require_transfer_artifact_capability,
)
from qma.wire.transfer_complete import (
    parse_transfer_complete_payload,
    require_transfer_complete_capability,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA",
    "ARTIFACT_TRANSFER_TICKET_FOLD_ID",
    "ARTIFACT_TRANSFER_TICKET_INSPECT_SHA",
    "ARTIFACT_TRANSFER_TICKET_NEW_SQLITE_CLASS",
    "ARTIFACT_TRANSFER_TICKET_STORE",
    "ARTIFACT_TRANSFER_TICKET_STORE_CLASS",
    "ARTIFACT_TRANSFER_TICKET_TABLE",
    "DAEMON_DIALS_IN",
    "DAEMON_OPENS_DEST_INBOUND_PORT",
    "DEC_0429_SUPERSEDED_BY",
    "DEC_0440_SUPERSEDED_BY",
    "DEST_CONTROL_NOTIFY_METHOD",
    "INTER_DAEMON_DISCOVERY",
    "LOCAL_INVOKE_FALLBACK",
    "OPEN_TICKET_STATES",
    "TICKET_CLAIMED_EVENT",
    "TICKET_COMPLETE_EVENT",
    "TICKET_ID_PREFIX",
    "TICKET_STATES",
    "TRANSFER_TICKET_HEADER",
    "ArtifactGetRedeem",
    "DestControlHandle",
    "DestControlRegistry",
    "DestinationPlacement",
    "InvokeTransferGate",
    "TransferArtifactResult",
    "TransferCompleteResult",
    "TransferTicket",
    "TransferTicketStore",
    "claim_artifact_store_types_absent_at_inspect_sha",
    "claim_transfer_artifact_existed_at_inspect_sha",
    "gate_invoke_until_transfer_complete",
    "handle_transfer_artifact",
    "handle_transfer_complete",
    "loopback_source_not_get_target",
    "place_dest_pulled_bytes",
    "source_unreachable",
]


ARTIFACT_TRANSFER_TICKET_STORE: Final[str] = "artifact_transfer_ticket"
ARTIFACT_TRANSFER_TICKET_FOLD_ID: Final[str] = "artifact_transfer_ticket"
ARTIFACT_TRANSFER_TICKET_TABLE: Final[str] = "artifact_transfer_ticket"
ARTIFACT_TRANSFER_TICKET_STORE_CLASS: Final[str] = StoreClass.JOURNAL_DERIVED_PROJECTION.value
ARTIFACT_TRANSFER_TICKET_NEW_SQLITE_CLASS: Final[bool] = False
ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA: Final[bool] = (
    TRANSFER_ARTIFACT_EXISTED_AT_INSPECT_SHA
)
ARTIFACT_TRANSFER_TICKET_INSPECT_SHA: Final[str] = TRANSFER_ARTIFACT_INSPECT_SHA
TICKET_ID_PREFIX: Final[str] = "att:"
TICKET_ISSUED_EVENT: Final[str] = "artifact_transfer_ticket.issued"
TICKET_NOTIFIED_EVENT: Final[str] = "artifact_transfer_ticket.notified"
TICKET_CLAIMED_EVENT: Final[str] = "artifact_transfer_ticket.claimed"
TICKET_COMPLETE_EVENT: Final[str] = "artifact_transfer_ticket.complete"
ORIGIN_RECORDED_EVENT: Final[str] = "artifact_transfer_ticket.origin_recorded"
TRANSFER_TICKET_HEADER: Final[str] = "X-QMX-Transfer-Ticket"
_STATE_EVENTS: Final[dict[str, str]] = {
    "issued": TICKET_ISSUED_EVENT,
    "notified": TICKET_NOTIFIED_EVENT,
    "claimed": TICKET_CLAIMED_EVENT,
    "complete": TICKET_COMPLETE_EVENT,
}
DEST_CONTROL_NOTIFY_METHOD: Final[str] = "artifact_transfer_ticket.notified"
TICKET_STATES: Final[frozenset[str]] = frozenset(
    {"issued", "notified", "claimed", "complete", "failed", "expired"}
)
OPEN_TICKET_STATES: Final[frozenset[str]] = frozenset({"issued", "notified", "claimed"})
DAEMON_DIALS_IN: Final[bool] = False
DAEMON_OPENS_DEST_INBOUND_PORT: Final[bool] = False
INTER_DAEMON_DISCOVERY: Final[bool] = False
LOCAL_INVOKE_FALLBACK: Final[bool] = False
_ORIGIN_ROW_ID: Final[str] = "current"

_TICKET_SCHEMA_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS artifact_transfer_ticket (
    ticket_id TEXT PRIMARY KEY NOT NULL,
    source_origin TEXT NOT NULL,
    fp1 TEXT NOT NULL,
    byte_count INTEGER NOT NULL,
    operator_principal TEXT NOT NULL,
    product_session_ref TEXT,
    environment_id TEXT NOT NULL,
    placement_revision TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    credential_ref TEXT NOT NULL,
    state TEXT NOT NULL,
    command_id TEXT NOT NULL,
    durable_command_id TEXT NOT NULL,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS artifact_transfer_source_origin (
    origin_id TEXT PRIMARY KEY NOT NULL,
    source_origin TEXT NOT NULL,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
"""


def source_unreachable(*, field: str = "source_origin", **extra: object) -> TypedRefusal:
    """Typed refusal: loopback / unrecorded / not-allowlisted origin is not a route."""
    details: dict[str, object] = {
        "loopback": True,
        "local_fallback": LOCAL_INVOKE_FALLBACK,
        "daemon_dials_in": DAEMON_DIALS_IN,
        "daemon_opens_dest_inbound_port": DAEMON_OPENS_DEST_INBOUND_PORT,
        "inter_daemon_discovery": INTER_DAEMON_DISCOVERY,
        "default_bind_host": DEFAULT_BIND_HOST,
    }
    details.update(extra)
    return policy_rejection(field, "source_unreachable", **details)


@dataclass(frozen=True, slots=True)
class DestinationPlacement:
    """Registered destination instance / environment for transfer issuance."""

    instance_id: str
    environment_id: str
    placement_revision: str
    credential_ref: str
    same_daemon: bool
    reachable_hosts: tuple[str, ...] = ()


@dataclass
class DestControlHandle:
    """Already-authenticated dest control connection (worker dial-out)."""

    credential_ref: str
    live: bool = True
    notifications: list[Mapping[str, object]] = field(default_factory=list[Mapping[str, object]])

    def notify(self, payload: Mapping[str, object]) -> None:
        if not self.live:
            return
        self.notifications.append(
            MappingProxyType(
                {
                    "jsonrpc": "2.0",
                    "method": DEST_CONTROL_NOTIFY_METHOD,
                    "params": dict(payload),
                }
            )
        )


@dataclass
class DestControlRegistry:
    """In-process dest control connections keyed by machine credential_ref."""

    _handles: dict[str, DestControlHandle] = field(default_factory=dict[str, DestControlHandle])

    def register(self, handle: DestControlHandle) -> DestControlHandle:
        existing = self._handles.get(handle.credential_ref)
        if existing is not None:
            existing.live = handle.live
            return existing
        self._handles[handle.credential_ref] = handle
        return handle

    def disconnect(self, credential_ref: str) -> None:
        handle = self._handles.get(credential_ref)
        if handle is not None:
            handle.live = False

    def get(self, credential_ref: str) -> DestControlHandle | None:
        return self._handles.get(credential_ref)

    def is_live(self, credential_ref: str) -> bool:
        handle = self._handles.get(credential_ref)
        return handle is not None and handle.live


@dataclass(frozen=True, slots=True)
class TransferTicket:
    """Open AM-03 ticket projection row."""

    ticket_id: str
    source_origin: str
    fp1: str
    byte_count: int
    operator_principal: str
    product_session_ref: str | None
    environment_id: str
    placement_revision: str
    instance_id: str
    credential_ref: str
    state: str
    command_id: str
    durable_command_id: str
    journal_seq: int
    recorded_at: int

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "ticket_id": self.ticket_id,
            "source_origin": self.source_origin,
            "fp1": self.fp1,
            "byte_count": self.byte_count,
            "operator_principal": self.operator_principal,
            "environment_id": self.environment_id,
            "placement_revision": self.placement_revision,
            "instance_id": self.instance_id,
            "credential_ref": self.credential_ref,
            "state": self.state,
            "command_id": self.command_id,
            "durable_command_id": self.durable_command_id,
            "journal_seq": self.journal_seq,
            "recorded_at": self.recorded_at,
        }
        if self.product_session_ref is not None:
            payload["product_session_ref"] = self.product_session_ref
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class ArtifactGetRedeem:
    """AM-13 machine byte pull: complete bytes plus the claimed ticket."""

    content: bytes
    ticket: TransferTicket
    content_type: str = "application/octet-stream"

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "ticket_id": self.ticket.ticket_id,
                "fp1": self.ticket.fp1,
                "byte_count": len(self.content),
                "state": self.ticket.state,
                "content_type": self.content_type,
                "invoke": False,
                "pairing_http": False,
                "bff": False,
            }
        )


@dataclass(frozen=True, slots=True)
class TransferCompleteResult:
    """Source ack of dest-authored transfer_complete. Source does not write dest."""

    ticket_id: str
    state: str
    fp1: str
    byte_count: int
    prior_complete: bool = False
    dest_bytes_written_on_source: bool = False
    second_ticket: bool = False

    def to_payload(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "ticket_id": self.ticket_id,
                "state": self.state,
                "fp1": self.fp1,
                "byte_count": self.byte_count,
                "prior_complete": self.prior_complete,
                "dest_bytes_written_on_source": self.dest_bytes_written_on_source,
                "second_ticket": self.second_ticket,
            }
        )


@dataclass(frozen=True, slots=True)
class InvokeTransferGate:
    """Invoke-until-complete transfer gate. Does not grant an instance_id."""

    transfer_gate_satisfied: bool
    instance_id: str
    same_daemon: bool = False
    ticket_id: str | None = None
    fp1: str | None = None
    instance_granted: bool = False
    instance_enabled: bool = False
    instance_guessed: bool = False
    local_fallback: bool = False
    finish_on_local_disk: bool = False
    composer_ref_rewritten: bool = False

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "transfer_gate_satisfied": self.transfer_gate_satisfied,
            "instance_id": self.instance_id,
            "same_daemon": self.same_daemon,
            "instance_granted": self.instance_granted,
            "instance_enabled": self.instance_enabled,
            "instance_guessed": self.instance_guessed,
            "local_fallback": self.local_fallback,
            "finish_on_local_disk": self.finish_on_local_disk,
            "composer_ref_rewritten": self.composer_ref_rewritten,
        }
        if self.ticket_id is not None:
            payload["ticket_id"] = self.ticket_id
        if self.fp1 is not None:
            payload["fp1"] = self.fp1
        return MappingProxyType(payload)


@dataclass(frozen=True, slots=True)
class TransferArtifactResult:
    """Command result: ticket_id for remote transfer, or same-daemon no-op."""

    transfer_required: bool
    ticket_id: str | None = None
    state: str | None = None
    fp1: str | None = None
    local_complete: bool = False

    def to_payload(self) -> Mapping[str, object]:
        payload: dict[str, object] = {"transfer_required": self.transfer_required}
        if self.ticket_id is not None:
            payload["ticket_id"] = self.ticket_id
        if self.state is not None:
            payload["state"] = self.state
        if self.fp1 is not None:
            payload["fp1"] = self.fp1
        if self.local_complete:
            payload["local_complete"] = True
        return MappingProxyType(payload)


def _ensure_schema(sqlite: SingleSqliteWriter) -> None:
    def _ddl(conn: sqlite3.Connection) -> None:
        conn.executescript(_TICKET_SCHEMA_SQL)

    sqlite.run(_ddl)


def _put_origin(
    sqlite: SingleSqliteWriter,
    *,
    source_origin: str,
    journal_seq: int,
    recorded_at: int,
) -> None:
    _ensure_schema(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO artifact_transfer_source_origin "
        "(origin_id, source_origin, journal_seq, recorded_at) VALUES (?, ?, ?, ?)",
        (_ORIGIN_ROW_ID, source_origin, journal_seq, recorded_at),
    )


def _put_ticket(sqlite: SingleSqliteWriter, ticket: TransferTicket) -> None:
    _ensure_schema(sqlite)
    sqlite.execute(
        "INSERT OR REPLACE INTO artifact_transfer_ticket "
        "(ticket_id, source_origin, fp1, byte_count, operator_principal, "
        "product_session_ref, environment_id, placement_revision, instance_id, "
        "credential_ref, state, command_id, durable_command_id, journal_seq, "
        "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            ticket.ticket_id,
            ticket.source_origin,
            ticket.fp1,
            ticket.byte_count,
            ticket.operator_principal,
            ticket.product_session_ref,
            ticket.environment_id,
            ticket.placement_revision,
            ticket.instance_id,
            ticket.credential_ref,
            ticket.state,
            ticket.command_id,
            ticket.durable_command_id,
            ticket.journal_seq,
            ticket.recorded_at,
        ),
    )


def _row_to_ticket(row: tuple[object, ...]) -> TransferTicket | None:
    (
        ticket_id,
        source_origin,
        fp1,
        byte_count,
        operator_principal,
        product_session_ref,
        environment_id,
        placement_revision,
        instance_id,
        credential_ref,
        state,
        command_id,
        durable_command_id,
        journal_seq,
        recorded_at,
    ) = row
    if not isinstance(ticket_id, str) or not isinstance(source_origin, str):
        return None
    if not isinstance(fp1, str) or not isinstance(operator_principal, str):
        return None
    if not isinstance(byte_count, int) or isinstance(byte_count, bool):
        return None
    if product_session_ref is not None and not isinstance(product_session_ref, str):
        return None
    if not isinstance(environment_id, str) or not isinstance(placement_revision, str):
        return None
    if not isinstance(instance_id, str) or not isinstance(credential_ref, str):
        return None
    if not isinstance(state, str) or not isinstance(command_id, str):
        return None
    if not isinstance(durable_command_id, str):
        return None
    if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
        return None
    if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
        return None
    return TransferTicket(
        ticket_id=ticket_id,
        source_origin=source_origin,
        fp1=fp1,
        byte_count=byte_count,
        operator_principal=operator_principal,
        product_session_ref=product_session_ref,
        environment_id=environment_id,
        placement_revision=placement_revision,
        instance_id=instance_id,
        credential_ref=credential_ref,
        state=state,
        command_id=command_id,
        durable_command_id=durable_command_id,
        journal_seq=journal_seq,
        recorded_at=recorded_at,
    )


def _ticket_from_journal_row(row: Mapping[str, object]) -> TransferTicket | None:
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return None
    body = cast("dict[str, object]", payload)
    if "superseded_by" in body:
        return None
    journal_seq = row.get("journal_seq")
    recorded_at = row.get("recorded_at")
    ticket_id = body.get("ticket_id")
    source_origin = body.get("source_origin")
    fp1 = body.get("fp1")
    byte_count = body.get("byte_count")
    operator_principal = body.get("operator_principal")
    product_session_ref = body.get("product_session_ref")
    environment_id = body.get("environment_id")
    placement_revision = body.get("placement_revision")
    instance_id = body.get("instance_id")
    credential_ref = body.get("credential_ref")
    state = body.get("state")
    command_id = body.get("command_id")
    durable_command_id = body.get("durable_command_id")
    if not isinstance(ticket_id, str) or not isinstance(source_origin, str):
        return None
    if not isinstance(fp1, str) or not isinstance(operator_principal, str):
        return None
    if not isinstance(byte_count, int) or isinstance(byte_count, bool):
        return None
    if product_session_ref is not None and (
        not isinstance(product_session_ref, str) or product_session_ref.strip() == ""
    ):
        return None
    if not isinstance(environment_id, str) or not isinstance(placement_revision, str):
        return None
    if not isinstance(instance_id, str) or not isinstance(credential_ref, str):
        return None
    if not isinstance(state, str) or state not in TICKET_STATES:
        return None
    if not isinstance(command_id, str) or not isinstance(durable_command_id, str):
        return None
    if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
        return None
    if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
        return None
    return TransferTicket(
        ticket_id=ticket_id,
        source_origin=source_origin,
        fp1=fp1,
        byte_count=byte_count,
        operator_principal=operator_principal,
        product_session_ref=product_session_ref,
        environment_id=environment_id,
        placement_revision=placement_revision,
        instance_id=instance_id,
        credential_ref=credential_ref,
        state=state,
        command_id=command_id,
        durable_command_id=durable_command_id,
        journal_seq=journal_seq,
        recorded_at=recorded_at,
    )


def _normalize_https_origin(value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return invalid_input(
            "source_origin",
            "recorded source origin is a non-empty https URL",
            given=repr(value),
        )
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return source_unreachable(
            given=value.strip(),
            tls=False,
            loopback=is_loopback_host(parsed.hostname) if parsed.hostname else False,
        )
    hostname = parsed.hostname
    if is_loopback_host(hostname):
        return source_unreachable(given=value.strip(), tls=True, loopback=True)
    origin = f"https://{parsed.netloc}"
    origin_host = urlsplit(origin).hostname
    if origin_host is None or is_loopback_host(origin_host):
        return source_unreachable(given=origin, tls=True, loopback=True)
    return Ok(origin)


def _origin_on_allowlist(origin: str, hosts: Sequence[str]) -> bool:
    parsed = urlsplit(origin)
    hostname = parsed.hostname or ""
    netloc = parsed.netloc
    candidates = {origin, netloc, hostname}
    if parsed.port is not None:
        candidates.add(f"{hostname}:{parsed.port}")
    for pattern in hosts:
        if pattern in candidates:
            return True
        if fnmatch.fnmatchcase(hostname, pattern) or fnmatch.fnmatchcase(netloc, pattern):
            return True
        if fnmatch.fnmatchcase(origin, pattern):
            return True
    return False


def _declare_fold(journal: AuthoritativeJournal) -> Result[None]:
    declared = journal.declare_store(ARTIFACT_TRANSFER_TICKET_STORE)
    if is_refusal(declared):
        return declared
    registered = journal.register_fold(ARTIFACT_TRANSFER_TICKET_FOLD_ID)
    if is_refusal(registered):
        return registered
    return Ok(None)


def _fold_from_journal(
    journal: AuthoritativeJournal,
) -> tuple[tuple[str, int, int] | None, dict[str, TransferTicket]]:
    rows = journal.read_all()
    if is_refusal(rows):
        return None, {}
    origin_row: tuple[str, int, int] | None = None
    origin_key: tuple[int, int] | None = None
    tickets: dict[str, TransferTicket] = {}
    ordered: list[tuple[int, int, TransferTicket]] = []
    for raw in rows.value:
        event = raw.get("event")
        if not isinstance(event, str) or not event.startswith("artifact_transfer_ticket."):
            continue
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            continue
        body = cast("dict[str, object]", payload)
        if "superseded_by" in body:
            continue
        journal_seq = raw.get("journal_seq")
        recorded_at = raw.get("recorded_at")
        if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
            continue
        if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
            continue
        key = (recorded_at, journal_seq)
        if event == ORIGIN_RECORDED_EVENT:
            recorded = body.get("source_origin")
            if (
                isinstance(recorded, str)
                and recorded.strip() != ""
                and (origin_key is None or key >= origin_key)
            ):
                origin_key = key
                origin_row = (recorded, journal_seq, recorded_at)
            continue
        ticket = _ticket_from_journal_row(raw)
        if ticket is None:
            continue
        ordered.append((recorded_at, journal_seq, ticket))
    ordered.sort(key=lambda item: (item[0], item[1]))
    for _recorded_at, _journal_seq, ticket in ordered:
        tickets[ticket.ticket_id] = ticket
    return origin_row, tickets


@dataclass
class TransferTicketStore:
    """AM-03 ticket projection plus dest placement / dest-control registries."""

    journal: AuthoritativeJournal
    sqlite: SingleSqliteWriter
    artifacts: ArtifactStore
    dest_artifacts: ArtifactStore = field(default_factory=ArtifactStore)
    placements: dict[str, DestinationPlacement] = field(
        default_factory=dict[str, DestinationPlacement]
    )
    dest_control: DestControlRegistry = field(default_factory=DestControlRegistry)
    _source_origin: str | None = None

    def restore(self) -> Result[None]:
        """Reload tickets and recorded origin from the journal onto sqlite."""
        declared = _declare_fold(self.journal)
        if is_refusal(declared):
            return declared
        origin_row, tickets = _fold_from_journal(self.journal)
        if origin_row is not None:
            origin, origin_seq, origin_recorded_at = origin_row
            self._source_origin = origin
            _put_origin(
                self.sqlite,
                source_origin=origin,
                journal_seq=origin_seq,
                recorded_at=origin_recorded_at,
            )
        if tickets:
            for ticket in tickets.values():
                _put_ticket(self.sqlite, ticket)
            materialized = self.journal.stores.materialize_on_first_write(
                ARTIFACT_TRANSFER_TICKET_STORE
            )
            if is_refusal(materialized):
                return materialized
        return Ok(None)

    def register_destination(self, placement: DestinationPlacement) -> None:
        self.placements[placement.instance_id] = placement

    def recorded_source_origin(self) -> str | None:
        if self._source_origin is not None:
            return self._source_origin
        _ensure_schema(self.sqlite)
        rows = self.sqlite.execute(
            "SELECT source_origin FROM artifact_transfer_source_origin WHERE origin_id = ?",
            (_ORIGIN_ROW_ID,),
        )
        if not rows or not isinstance(rows[0][0], str):
            return None
        self._source_origin = rows[0][0]
        return self._source_origin

    def record_source_tls_origin(self, origin: object) -> Result[str]:
        """Operator-recorded non-loopback HTTPS origin dest will pull from."""
        normalized = _normalize_https_origin(origin)
        if is_refusal(normalized):
            return normalized
        declared = _declare_fold(self.journal)
        if is_refusal(declared):
            return declared
        append = self.journal.append_event(
            ORIGIN_RECORDED_EVENT,
            payload={"source_origin": normalized.value},
        )
        if is_refusal(append):
            return append
        record = append.value.record
        self._source_origin = normalized.value
        _put_origin(
            self.sqlite,
            source_origin=normalized.value,
            journal_seq=record.journal_seq,
            recorded_at=record.recorded_at,
        )
        return Ok(normalized.value)

    def get(self, ticket_id: str) -> TransferTicket | None:
        _ensure_schema(self.sqlite)
        rows = self.sqlite.execute(
            "SELECT ticket_id, source_origin, fp1, byte_count, operator_principal, "
            "product_session_ref, environment_id, placement_revision, instance_id, "
            "credential_ref, state, command_id, durable_command_id, journal_seq, "
            "recorded_at FROM artifact_transfer_ticket WHERE ticket_id = ?",
            (ticket_id,),
        )
        if not rows:
            return None
        return _row_to_ticket(rows[0])

    def by_durable_command_id(self, durable_command_id: str) -> TransferTicket | None:
        _ensure_schema(self.sqlite)
        rows = self.sqlite.execute(
            "SELECT ticket_id, source_origin, fp1, byte_count, operator_principal, "
            "product_session_ref, environment_id, placement_revision, instance_id, "
            "credential_ref, state, command_id, durable_command_id, journal_seq, "
            "recorded_at FROM artifact_transfer_ticket WHERE durable_command_id = ?",
            (durable_command_id,),
        )
        if not rows:
            return None
        return _row_to_ticket(rows[0])

    def open_tickets(self) -> tuple[TransferTicket, ...]:
        _ensure_schema(self.sqlite)
        rows = self.sqlite.execute(
            "SELECT ticket_id, source_origin, fp1, byte_count, operator_principal, "
            "product_session_ref, environment_id, placement_revision, instance_id, "
            "credential_ref, state, command_id, durable_command_id, journal_seq, "
            "recorded_at FROM artifact_transfer_ticket ORDER BY journal_seq ASC"
        )
        tickets: list[TransferTicket] = []
        for row in rows:
            ticket = _row_to_ticket(row)
            if ticket is not None and ticket.state in OPEN_TICKET_STATES:
                tickets.append(ticket)
        return tuple(tickets)

    def dest_control_up(self, credential_ref: object) -> Result[DestControlHandle]:
        """Dest reconnect: issued tickets for this audience become notified."""
        if not isinstance(credential_ref, str) or credential_ref.strip() == "":
            return invalid_input(
                "credential_ref",
                "dest control audience is a non-empty machine credential_ref",
                given=repr(credential_ref),
            )
        if not is_credential_ref_allowed(credential_ref):
            return policy_rejection(
                "credential_ref",
                "dest control audience must be an allowlisted machine credential_ref",
                given=credential_ref,
            )
        handle = self.dest_control.register(
            DestControlHandle(credential_ref=credential_ref, live=True)
        )
        for ticket in self.open_tickets():
            if ticket.credential_ref != credential_ref or ticket.state != "issued":
                continue
            notified = self._journal_state(ticket, state="notified")
            if is_refusal(notified):
                return notified
            handle.notify(notified.value.to_payload())
        return Ok(handle)

    def dest_control_down(self, credential_ref: str) -> None:
        self.dest_control.disconnect(credential_ref)

    def _journal_state(self, ticket: TransferTicket, *, state: str) -> Result[TransferTicket]:
        declared = _declare_fold(self.journal)
        if is_refusal(declared):
            return declared
        payload = dict(ticket.to_payload())
        payload["state"] = state
        event = _STATE_EVENTS.get(state)
        if event is None:
            return invalid_input("state", "unknown ticket state", given=state)
        append = self.journal.append_event(event, payload=payload)
        if is_refusal(append):
            return append
        record = append.value.record
        updated = TransferTicket(
            ticket_id=ticket.ticket_id,
            source_origin=ticket.source_origin,
            fp1=ticket.fp1,
            byte_count=ticket.byte_count,
            operator_principal=ticket.operator_principal,
            product_session_ref=ticket.product_session_ref,
            environment_id=ticket.environment_id,
            placement_revision=ticket.placement_revision,
            instance_id=ticket.instance_id,
            credential_ref=ticket.credential_ref,
            state=state,
            command_id=ticket.command_id,
            durable_command_id=ticket.durable_command_id,
            journal_seq=record.journal_seq,
            recorded_at=record.recorded_at,
        )
        _put_ticket(self.sqlite, updated)
        materialized = self.journal.stores.materialize_on_first_write(
            ARTIFACT_TRANSFER_TICKET_STORE
        )
        if is_refusal(materialized):
            return materialized
        return Ok(updated)

    def issue(
        self,
        *,
        parsed: Mapping[str, object],
        operator_principal: str,
        source_origin: str,
        byte_count: int,
        dest: DestinationPlacement,
    ) -> Result[TransferTicket]:
        durable = str(parsed["durable_command_id"])
        existing = self.by_durable_command_id(durable)
        if existing is not None:
            return Ok(existing)
        ticket_id = f"{TICKET_ID_PREFIX}{uuid.uuid4().hex}"
        product_session_ref = parsed.get("product_session_ref")
        session = product_session_ref if isinstance(product_session_ref, str) else None
        draft = TransferTicket(
            ticket_id=ticket_id,
            source_origin=source_origin,
            fp1=str(parsed["fp1"]),
            byte_count=byte_count,
            operator_principal=operator_principal,
            product_session_ref=session,
            environment_id=dest.environment_id,
            placement_revision=dest.placement_revision,
            instance_id=dest.instance_id,
            credential_ref=dest.credential_ref,
            state="issued",
            command_id=str(parsed["command_id"]),
            durable_command_id=durable,
            journal_seq=0,
            recorded_at=0,
        )
        issued = self._journal_state(draft, state="issued")
        if is_refusal(issued):
            return issued
        ticket = issued.value
        if self.dest_control.is_live(dest.credential_ref):
            notified = self._journal_state(ticket, state="notified")
            if is_refusal(notified):
                return notified
            handle = self.dest_control.get(dest.credential_ref)
            if handle is not None:
                handle.notify(notified.value.to_payload())
            return notified
        return Ok(ticket)

    def tickets_for_placement(self, *, fp1: str, instance_id: str) -> tuple[TransferTicket, ...]:
        _ensure_schema(self.sqlite)
        rows = self.sqlite.execute(
            "SELECT ticket_id, source_origin, fp1, byte_count, operator_principal, "
            "product_session_ref, environment_id, placement_revision, instance_id, "
            "credential_ref, state, command_id, durable_command_id, journal_seq, "
            "recorded_at FROM artifact_transfer_ticket WHERE fp1 = ? AND "
            "instance_id = ? ORDER BY journal_seq ASC",
            (fp1, instance_id),
        )
        tickets: list[TransferTicket] = []
        for row in rows:
            ticket = _row_to_ticket(row)
            if ticket is not None:
                tickets.append(ticket)
        return tuple(tickets)

    def redeem_get(
        self,
        *,
        ticket_id: object,
        fp1: object,
        credential_ref: object,
    ) -> Result[ArtifactGetRedeem]:
        """Live AM-13 machine GET: notified → claimed; return complete bytes."""
        if not isinstance(ticket_id, str) or ticket_id.strip() == "":
            return invalid_input(
                "ticket_id",
                "X-QMX-Transfer-Ticket is a required ticket_id",
                given=repr(ticket_id),
                invoke=False,
                pairing_http=False,
                bff=False,
            )
        if not isinstance(fp1, str) or fp1.strip() == "":
            return invalid_input("fp1", "GET /artifacts/<fp1> requires an fp1")
        if not isinstance(credential_ref, str) or credential_ref.strip() == "":
            return invalid_input(
                "credential_ref",
                "machine GET audience is a credential_ref",
                given=repr(credential_ref),
            )
        ticket = self.get(ticket_id.strip())
        if ticket is None:
            return policy_rejection(
                "ticket_id",
                "unknown transfer ticket",
                given=ticket_id.strip(),
                invoke=False,
            )
        loopback = loopback_source_not_get_target(ticket.source_origin)
        if is_refusal(loopback):
            return loopback
        if ticket.fp1 != fp1.strip():
            return policy_rejection(
                "fp1",
                "ticket fp1 must match GET /artifacts/<fp1>",
                given=fp1.strip(),
                ticket_fp1=ticket.fp1,
            )
        if ticket.credential_ref != credential_ref:
            return policy_rejection(
                "credential_ref",
                "only the ticket audience may redeem",
                given=credential_ref,
                audience=ticket.credential_ref,
            )
        if ticket.state in {"failed", "expired", "issued"}:
            return policy_rejection(
                "state",
                "ticket must be notified before machine GET redeem",
                given=ticket.state,
                invoke=False,
            )
        staged = self.artifacts.get(ticket.fp1)
        if staged is None:
            return invalid_input(
                "fp1",
                "source local-complete bytes are required for GET redeem",
                given=ticket.fp1,
            )
        claimed = ticket
        if ticket.state == "notified":
            advanced = self._journal_state(ticket, state="claimed")
            if is_refusal(advanced):
                return advanced
            claimed = advanced.value
        return Ok(ArtifactGetRedeem(content=bytes(staged.content), ticket=claimed))

    def complete_ack(self, ticket: TransferTicket) -> Result[TransferTicket]:
        """Record dest-authored complete. Source does not write dest bytes."""
        return self._journal_state(ticket, state="complete")


def _same_daemon_result(fp1: str) -> TransferArtifactResult:
    return TransferArtifactResult(
        transfer_required=False,
        fp1=fp1,
        local_complete=True,
    )


def handle_transfer_artifact(
    store: TransferTicketStore,
    payload: object,
    *,
    capabilities: object,
    principal_class: object,
) -> Result[TransferArtifactResult]:
    """Issue an AM-03 ticket, or report same-daemon local-complete possession."""
    gated = require_transfer_artifact_capability(capabilities)
    if is_refusal(gated):
        return gated
    if principal_class is not PrincipalClass.OPERATOR and principal_class != (
        PrincipalClass.OPERATOR.value
    ):
        return policy_rejection(
            "principal_class",
            "transfer_artifact is operator-issued (AM-09)",
            given=repr(principal_class),
        )
    parsed = parse_transfer_artifact_payload(payload)
    if is_refusal(parsed):
        return parsed
    args = parsed.value
    fp1 = str(args["fp1"])
    staged = store.artifacts.get(fp1)
    if staged is None:
        return invalid_input(
            "fp1",
            "transfer_artifact requires a local-complete fp1 on this daemon",
            given=fp1,
            local_complete=False,
        )
    instance_id = str(args["instance_id"])
    dest = store.placements.get(instance_id)
    same_daemon = dest.same_daemon if dest is not None else args.get("same_daemon") is True
    if dest is None and args.get("same_daemon") is not True:
        return invalid_input(
            "instance_id",
            "destination placement must be registered for a remote transfer",
            given=instance_id,
            local_fallback=LOCAL_INVOKE_FALLBACK,
        )
    if dest is not None:
        for field, expected in (
            ("environment_id", dest.environment_id),
            ("placement_revision", dest.placement_revision),
            ("credential_ref", dest.credential_ref),
        ):
            supplied = args.get(field)
            if supplied is not None and supplied != expected:
                return invalid_input(
                    field,
                    "destination placement fields must match the registered instance",
                    given=repr(supplied),
                    registered=expected,
                )
    if same_daemon:
        return Ok(_same_daemon_result(fp1))
    if dest is None:
        return invalid_input(
            "instance_id",
            "destination placement must be registered for a remote transfer",
            given=instance_id,
            local_fallback=LOCAL_INVOKE_FALLBACK,
        )
    if DAEMON_DIALS_IN or DAEMON_OPENS_DEST_INBOUND_PORT or LOCAL_INVOKE_FALLBACK:
        return source_unreachable(local_invoke=True)
    if not is_credential_ref_allowed(dest.credential_ref):
        return policy_rejection(
            "credential_ref",
            "ticket audience is an exact machine credential_ref on the broker allowlist",
            given=dest.credential_ref,
        )
    origin = store.recorded_source_origin()
    if origin is None:
        return source_unreachable(recorded=False, loopback=True)
    hostname = urlsplit(origin).hostname
    if hostname is None or is_loopback_host(hostname):
        return source_unreachable(given=origin, recorded=True, loopback=True)
    if not _origin_on_allowlist(origin, dest.reachable_hosts):
        return source_unreachable(
            given=origin,
            recorded=True,
            loopback=False,
            allowlisted=False,
            reachable_hosts=list(dest.reachable_hosts),
        )
    operator = (
        principal_class.value
        if isinstance(principal_class, PrincipalClass)
        else str(principal_class)
    )
    ticket = store.issue(
        parsed=args,
        operator_principal=operator,
        source_origin=origin,
        byte_count=staged.byte_count,
        dest=dest,
    )
    if is_refusal(ticket):
        return ticket
    return Ok(
        TransferArtifactResult(
            transfer_required=True,
            ticket_id=ticket.value.ticket_id,
            state=ticket.value.state,
        )
    )


def loopback_source_not_get_target(origin: object) -> Result[str]:
    """Loopback source is never offered as a GET target (AM-13)."""
    if not isinstance(origin, str) or origin.strip() == "":
        return source_unreachable(recorded=False, get_target=True)
    parsed = urlsplit(origin.strip())
    hostname = parsed.hostname
    if hostname is None or is_loopback_host(hostname) or parsed.scheme != "https":
        return source_unreachable(
            given=origin.strip(),
            get_target=True,
            loopback=hostname is None or is_loopback_host(hostname),
            tls=parsed.scheme == "https",
        )
    return Ok(origin.strip())


def place_dest_pulled_bytes(
    store: TransferTicketStore,
    body: object,
    *,
    ticket_id: object,
    interrupted: bool = False,
) -> Result[StagedArtifact]:
    """Dest-only write: verify hash plus byte count, else delete incomplete."""
    if not isinstance(ticket_id, str) or ticket_id.strip() == "":
        return invalid_input("ticket_id", "dest pull names a ticket_id")
    ticket = store.get(ticket_id.strip())
    if ticket is None:
        return policy_rejection("ticket_id", "unknown transfer ticket", given=ticket_id)
    if interrupted or not isinstance(body, bytes):
        store.dest_artifacts.drop_incomplete(ticket.fp1)
        return policy_rejection(
            "body",
            "interrupted dest pull deletes the incomplete object",
            runnable_remote_ref=False,
            dest_object=False,
            ticket_state=ticket.state,
            source_fp1_unchanged=True,
            composer_ref_rewritten=False,
            local_fallback=LOCAL_INVOKE_FALLBACK,
        )
    recomputed = fingerprint_bytes(body).value
    byte_count = len(body)
    if recomputed != ticket.fp1 or byte_count != ticket.byte_count:
        store.dest_artifacts.drop_incomplete(ticket.fp1)
        return policy_rejection(
            "fp1",
            "dest hash and byte_count must match the ticket",
            runnable_remote_ref=False,
            dest_object=False,
            ticket_state=ticket.state,
            source_fp1_unchanged=True,
            composer_ref_rewritten=False,
            local_fallback=LOCAL_INVOKE_FALLBACK,
            given_fp1=recomputed,
            ticket_fp1=ticket.fp1,
            given_byte_count=byte_count,
            ticket_byte_count=ticket.byte_count,
        )
    placed = store.dest_artifacts.stage_complete_bytes(body)
    if is_refusal(placed):
        store.dest_artifacts.drop_incomplete(ticket.fp1)
        return placed
    return placed


def handle_transfer_complete(
    store: TransferTicketStore,
    payload: object,
    *,
    capabilities: object,
    principal_class: object,
) -> Result[TransferCompleteResult]:
    """Source records dest-authored complete. Does not write dest bytes."""
    gated = require_transfer_complete_capability(capabilities)
    if is_refusal(gated):
        return gated
    if principal_class is not PrincipalClass.MACHINE and principal_class != (
        PrincipalClass.MACHINE.value
    ):
        return policy_rejection(
            "principal_class",
            "transfer_complete is dest-authored as a machine principal",
            given=repr(principal_class),
        )
    parsed = parse_transfer_complete_payload(payload)
    if is_refusal(parsed):
        return parsed
    args = parsed.value
    ticket_id = str(args["ticket_id"])
    parsed_fp1 = args["fp1"]
    parsed_count = args["byte_count"]
    parsed_command_id = args["command_id"]
    if not isinstance(parsed_count, int) or isinstance(parsed_count, bool):
        return invalid_input(
            "byte_count",
            "transfer_complete byte_count must be a non-negative integer",
            given=repr(parsed_count),
        )
    ticket = store.get(ticket_id)
    if ticket is None:
        return policy_rejection("ticket_id", "unknown transfer ticket", given=ticket_id)
    if ticket.command_id != str(parsed_command_id):
        return policy_rejection(
            "command_id",
            "transfer_complete identity is ticket_id plus the original command_id",
            given=str(parsed_command_id),
            original=ticket.command_id,
        )
    if ticket.fp1 != str(parsed_fp1) or ticket.byte_count != parsed_count:
        return policy_rejection(
            "fp1",
            "transfer_complete fp1 and byte_count must match the ticket",
            given_fp1=str(parsed_fp1),
            ticket_fp1=ticket.fp1,
            given_byte_count=parsed_count,
            ticket_byte_count=ticket.byte_count,
        )
    if ticket.state == "complete":
        return Ok(
            TransferCompleteResult(
                ticket_id=ticket.ticket_id,
                state=ticket.state,
                fp1=ticket.fp1,
                byte_count=ticket.byte_count,
                prior_complete=True,
            )
        )
    if ticket.state not in {"notified", "claimed"}:
        return policy_rejection(
            "state",
            "transfer_complete requires a notified or claimed ticket",
            given=ticket.state,
        )
    completed = store.complete_ack(ticket)
    if is_refusal(completed):
        return completed
    ack = completed.value
    return Ok(
        TransferCompleteResult(
            ticket_id=ack.ticket_id,
            state=ack.state,
            fp1=ack.fp1,
            byte_count=ack.byte_count,
        )
    )


def gate_invoke_until_transfer_complete(
    store: TransferTicketStore,
    *,
    fp1: object,
    instance_id: object,
) -> Result[InvokeTransferGate]:
    """Refuse remote invoke citing fp1 until the ticket is complete.

    Exactly one instance_id is required (Epic 60). This gate does not grant,
    enable, or guess an instance. Silent local fallback is refused.
    """
    if not isinstance(instance_id, str) or instance_id.strip() == "":
        return invalid_input(
            "instance_id",
            "invoke still needs exactly one instance_id; this story does not "
            "grant, enable, or guess an instance",
            instance_granted=False,
            instance_enabled=False,
            instance_guessed=False,
            local_fallback=LOCAL_INVOKE_FALLBACK,
            finish_on_local_disk=False,
            composer_ref_rewritten=False,
        )
    if not isinstance(fp1, str) or fp1.strip() == "":
        return invalid_input("fp1", "invoke cites an fp1")
    dest = store.placements.get(instance_id.strip())
    if dest is None:
        return invalid_input(
            "instance_id",
            "destination placement must be registered for invoke",
            given=instance_id.strip(),
            instance_granted=False,
            local_fallback=LOCAL_INVOKE_FALLBACK,
            finish_on_local_disk=False,
            composer_ref_rewritten=False,
        )
    if dest.same_daemon:
        return Ok(
            InvokeTransferGate(
                transfer_gate_satisfied=True,
                instance_id=instance_id.strip(),
                same_daemon=True,
                fp1=fp1.strip(),
            )
        )
    tickets = store.tickets_for_placement(fp1=fp1.strip(), instance_id=instance_id.strip())
    complete = [ticket for ticket in tickets if ticket.state == "complete"]
    if not complete:
        return policy_rejection(
            "invoke",
            "invoke refuses until transfer_complete; local-complete is not remote possession",
            local_fallback=LOCAL_INVOKE_FALLBACK,
            finish_on_local_disk=False,
            composer_ref_rewritten=False,
            local_complete_is_remote=False,
            silent_local_fallback=False,
            ticket_complete=False,
            instance_granted=False,
        )
    ticket = complete[-1]
    dest_object = store.dest_artifacts.get(fp1.strip())
    if dest_object is None:
        return policy_rejection(
            "invoke",
            "dest has no runnable remote ref",
            runnable_remote_ref=False,
            local_fallback=LOCAL_INVOKE_FALLBACK,
            finish_on_local_disk=False,
            composer_ref_rewritten=False,
            instance_granted=False,
            ticket_id=ticket.ticket_id,
        )
    return Ok(
        InvokeTransferGate(
            transfer_gate_satisfied=True,
            instance_id=instance_id.strip(),
            ticket_id=ticket.ticket_id,
            fp1=fp1.strip(),
        )
    )
