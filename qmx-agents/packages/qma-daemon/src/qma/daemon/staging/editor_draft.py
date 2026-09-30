"""Daemon owned, CAS protected editor drafts (Epic 71; AM-03/AM-09).

Draft bytes remain in the complete artifact staging channel. This module only
names those immutable bytes, folds the current head into the existing daemon
SQLite journal projection, and publishes validated graph contributions into
the machine local authoring roster.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qma.core.vocabulary.enums import ArtifactCompleteness
from qma.daemon.artifacts.store import ArtifactStore, StagedArtifact
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.plugins.lifecycle import AtomicRoster
from qma.daemon.taskgraph.execution import validate_graph_template_topology
from qma.daemon.taskgraph.records import GraphTemplate
from qma.wire.editor_draft import (
    EDITOR_DRAFT_PROJECTION,
    GET_EDITOR_DRAFT_HEAD_CAPABILITY,
    PUBLISH_EDITOR_DRAFT_CAPABILITY,
    SAVE_EDITOR_DRAFT_CAPABILITY,
    require_editor_draft_capability,
)
from qmf.core import Ok, Result, TypedRefusal, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "EDITOR_DRAFT_HEAD_EVENT_SAVED",
    "EDITOR_DRAFT_HEAD_TABLE",
    "EDITOR_DRAFT_PUBLISH_REFUSED_AT_INSPECT_SHA",
    "EditorDraftHead",
    "EditorDraftService",
]

EDITOR_DRAFT_HEAD_TABLE: Final[str] = EDITOR_DRAFT_PROJECTION
EDITOR_DRAFT_HEAD_EVENT_SAVED: Final[str] = "editor_draft.saved"
EDITOR_DRAFT_PUBLISHED_EVENT: Final[str] = "editor_draft.published"
EDITOR_DRAFT_PUBLISH_REFUSED_AT_INSPECT_SHA: Final[bool] = False

_SCHEMA_SQL: Final[str] = f"""
CREATE TABLE IF NOT EXISTS {EDITOR_DRAFT_HEAD_TABLE} (
    editor_draft_id TEXT PRIMARY KEY NOT NULL,
    owner_principal TEXT NOT NULL,
    editor_revision TEXT NOT NULL,
    client_draft_correlation TEXT,
    correlation_fp1 TEXT,
    contribution_id TEXT,
    journal_seq INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS editor_draft_correlation_unique
ON {EDITOR_DRAFT_HEAD_TABLE} (client_draft_correlation)
WHERE client_draft_correlation IS NOT NULL;
"""


def _require_token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or value.strip() == "":
        return invalid_input(field, f"{field} must be a non-empty string", given=repr(value))
    return Ok(value.strip())


def _conflict(expected: object, current: str) -> TypedRefusal:
    return policy_rejection(
        "expected_revision",
        "editor draft head compare-and-set conflict; reload the current head",
        refusal="conflict",
        expected=expected,
        current=current,
    )


@dataclass(frozen=True, slots=True)
class EditorDraftHead:
    """The snapshot query shape. Draft ids and revisions are not runnable refs."""

    editor_draft_id: str
    editor_revision: str
    owner_principal: str

    def to_payload(self, *, include_owner: bool = False) -> Mapping[str, object]:
        payload: dict[str, object] = {
            "editor_draft_id": self.editor_draft_id,
            "editor_revision": self.editor_revision,
        }
        if include_owner:
            payload["owner_principal"] = self.owner_principal
        return MappingProxyType(payload)


@dataclass(slots=True)
class EditorDraftService:
    """Sole issuer and CAS writer for editor draft identity and publication."""

    journal: AuthoritativeJournal
    sqlite: SingleSqliteWriter
    artifacts: ArtifactStore
    authoring_roster_root: Path

    def __post_init__(self) -> None:
        declared = self.journal.declare_store(
            EDITOR_DRAFT_PROJECTION,
            fold_metadata=None,
        )
        if is_refusal(declared):
            raise RuntimeError("editor_draft_head projection declaration was refused")
        registered = self.journal.register_fold(EDITOR_DRAFT_PROJECTION)
        if is_refusal(registered):
            raise RuntimeError("editor_draft_head fold declaration was refused")
        self._ensure_schema()

    def restore_from_journal(self) -> Result[int]:
        """Rebuild the named SQLite projection from the authoritative journal."""
        stream = self.journal.read_events()
        if is_refusal(stream):
            return stream
        latest: dict[str, tuple[object, ...]] = {}
        for event in stream.value:
            payload = event.payload
            if event.event == EDITOR_DRAFT_PUBLISHED_EVENT:
                draft_id = payload.get("editor_draft_id")
                revision = payload.get("editor_revision")
                contribution_id = payload.get("contribution_id")
                prior = latest.get(draft_id) if isinstance(draft_id, str) else None
                if (
                    prior is not None
                    and prior[2] == revision
                    and isinstance(contribution_id, str)
                    and contribution_id
                ):
                    latest[cast(str, draft_id)] = (
                        *prior[:5],
                        contribution_id,
                        event.journal_seq,
                        event.recorded_at,
                    )
                continue
            if event.event != EDITOR_DRAFT_HEAD_EVENT_SAVED:
                continue
            draft_id = payload.get("editor_draft_id")
            owner = payload.get("owner_principal")
            revision = payload.get("editor_revision")
            if not all(isinstance(value, str) and value for value in (draft_id, owner, revision)):
                return invalid_input(
                    EDITOR_DRAFT_PROJECTION,
                    "journal editor_draft.saved event has an invalid head shape",
                    journal_seq=event.journal_seq,
                )
            latest[cast(str, draft_id)] = (
                cast(str, draft_id),
                cast(str, owner),
                cast(str, revision),
                payload.get("client_draft_correlation"),
                payload.get("correlation_fp1"),
                None,
                event.journal_seq,
                event.recorded_at,
            )

        def _replace(conn: object) -> int:
            raw = cast("sqlite3.Connection", conn)
            raw.execute("DELETE FROM editor_draft_head")
            raw.executemany(
                "INSERT INTO editor_draft_head "
                "(editor_draft_id, owner_principal, editor_revision, "
                "client_draft_correlation, correlation_fp1, contribution_id, "
                "journal_seq, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                latest.values(),
            )
            return len(latest)

        restored = self.sqlite.run(_replace)
        materialized = self.journal.stores.materialize_on_first_write(EDITOR_DRAFT_PROJECTION)
        if is_refusal(materialized):
            return materialized
        return Ok(restored)

    def _ensure_schema(self) -> None:
        self.sqlite.run(lambda conn: conn.executescript(_SCHEMA_SQL))

    def _row(self, draft_id: str) -> tuple[object, ...] | None:
        rows = self.sqlite.execute(
            "SELECT editor_draft_id, owner_principal, editor_revision, "
            "client_draft_correlation, correlation_fp1, contribution_id, "
            "journal_seq, recorded_at FROM editor_draft_head "
            "WHERE editor_draft_id = ?",
            (draft_id,),
        )
        return rows[0] if rows else None

    def _artifact(self, fp1: object) -> Result[StagedArtifact]:
        token = _require_token("fp1", fp1)
        if is_refusal(token):
            return token
        staged = self.artifacts.get(token.value)
        if staged is None:
            return invalid_input(
                "fp1",
                "save names an artifact already held local-complete by this daemon",
                given=token.value,
                local_complete=False,
            )
        if staged.completeness != ArtifactCompleteness.COMPLETE.value:
            return invalid_input(
                "fp1",
                "draft bytes must be local-complete before save",
                given=token.value,
                completeness=staged.completeness,
            )
        recomputed = fingerprint_bytes(staged.content).value
        if staged.fp1 != token.value or recomputed != token.value:
            return policy_rejection(
                "fp1",
                "staged bytes no longer match the immutable named fp1",
                given=token.value,
                actual=staged.fp1,
                recomputed=recomputed,
            )
        return Ok(staged)

    def save_editor_draft(
        self,
        payload: object,
        *,
        operator_principal: object,
        capabilities: object | None = None,
    ) -> Result[EditorDraftHead]:
        gate = require_editor_draft_capability(capabilities, SAVE_EDITOR_DRAFT_CAPABILITY)
        if is_refusal(gate):
            return gate
        if not isinstance(payload, Mapping):
            return invalid_input("payload", "save_editor_draft payload must be an object")
        values = cast(Mapping[str, object], payload)
        principal = _require_token("operator_principal", operator_principal)
        if is_refusal(principal):
            return principal
        artifact = self._artifact(values.get("fp1"))
        if is_refusal(artifact):
            return artifact
        raw_id = values.get("editor_draft_id")
        raw_expected = values.get("expected_revision")
        correlation_raw = values.get("client_draft_correlation")
        if correlation_raw is not None:
            correlation = _require_token("client_draft_correlation", correlation_raw)
            if is_refusal(correlation):
                return correlation
        else:
            correlation = Ok(None)

        def _mutate(conn: sqlite3.Connection) -> Result[EditorDraftHead]:
            if "editor_draft_id" not in values:
                if raw_expected not in (None, ""):
                    return invalid_input(
                        "expected_revision",
                        "first save omits expected_revision or supplies an empty value",
                        given=repr(raw_expected),
                    )
                if correlation.value is not None:
                    rows = conn.execute(
                        "SELECT editor_draft_id, owner_principal, editor_revision, "
                        "correlation_fp1 FROM editor_draft_head "
                        "WHERE client_draft_correlation = ?",
                        (correlation.value,),
                    ).fetchall()
                    if rows:
                        draft_id, owner, revision, prior_fp1 = rows[0]
                        if owner != principal.value:
                            return policy_rejection(
                                "client_draft_correlation",
                                "correlation is scoped to its original operator principal",
                                owner=owner,
                            )
                        if prior_fp1 != artifact.value.fp1 or revision != artifact.value.fp1:
                            return policy_rejection(
                                "client_draft_correlation",
                                "correlation reuse with different fp1 refuses without forking",
                                refusal="correlation_mismatch",
                                existing_fp1=prior_fp1,
                                given_fp1=artifact.value.fp1,
                            )
                        return Ok(EditorDraftHead(str(draft_id), str(revision), str(owner)))
                draft_id = f"edraft:{uuid.uuid4().hex}"
                event_payload: dict[str, object] = {
                    "editor_draft_id": draft_id,
                    "editor_revision": artifact.value.fp1,
                    "owner_principal": principal.value,
                }
                if correlation.value is not None:
                    event_payload["client_draft_correlation"] = correlation.value
                    event_payload["correlation_fp1"] = artifact.value.fp1
                appended = self.journal.append_event(
                    EDITOR_DRAFT_HEAD_EVENT_SAVED,
                    payload=event_payload,
                )
                if is_refusal(appended):
                    return appended
                recorded = appended.value.record.recorded_at
                seq = appended.value.record.journal_seq
                conn.execute(
                    "INSERT INTO editor_draft_head "
                    "(editor_draft_id, owner_principal, editor_revision, "
                    "client_draft_correlation, correlation_fp1, contribution_id, "
                    "journal_seq, recorded_at) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                    (
                        draft_id,
                        principal.value,
                        artifact.value.fp1,
                        correlation.value,
                        artifact.value.fp1 if correlation.value else None,
                        seq,
                        recorded,
                    ),
                )
                materialized = self.journal.stores.materialize_on_first_write(
                    EDITOR_DRAFT_PROJECTION
                )
                if is_refusal(materialized):
                    return materialized
                return Ok(EditorDraftHead(draft_id, artifact.value.fp1, principal.value))

            if not isinstance(raw_id, str) or raw_id.strip() == "":
                return invalid_input("editor_draft_id", "editor_draft_id must be non-empty")
            draft_id = raw_id.strip()
            row = conn.execute(
                "SELECT editor_draft_id, owner_principal, editor_revision, "
                "client_draft_correlation, correlation_fp1, contribution_id, "
                "journal_seq, recorded_at FROM editor_draft_head "
                "WHERE editor_draft_id = ?",
                (draft_id,),
            ).fetchone()
            if row is None:
                return policy_rejection(
                    "editor_draft_id",
                    "subsequent save must name an existing daemon-issued draft",
                    editor_draft_id=draft_id,
                )
            if row[1] != principal.value:
                return policy_rejection(
                    "editor_draft_id",
                    "only the owner operator may save this editor draft",
                    owner=row[1],
                )
            current = str(row[2])
            if raw_expected != current:
                return _conflict(raw_expected, current)
            event_payload = {
                "editor_draft_id": draft_id,
                "editor_revision": artifact.value.fp1,
                "owner_principal": principal.value,
            }
            if row[3] is not None:
                event_payload["client_draft_correlation"] = row[3]
            if row[4] is not None:
                event_payload["correlation_fp1"] = row[4]
            appended = self.journal.append_event(
                EDITOR_DRAFT_HEAD_EVENT_SAVED, payload=event_payload
            )
            if is_refusal(appended):
                return appended
            updated = conn.execute(
                "UPDATE editor_draft_head SET editor_revision = ?, "
                "journal_seq = ?, recorded_at = ? WHERE editor_draft_id = ? "
                "AND editor_revision = ?",
                (
                    artifact.value.fp1,
                    appended.value.record.journal_seq,
                    appended.value.record.recorded_at,
                    draft_id,
                    current,
                ),
            )
            if updated.rowcount != 1:
                latest = conn.execute(
                    "SELECT editor_revision FROM editor_draft_head WHERE editor_draft_id = ?",
                    (draft_id,),
                ).fetchone()
                return _conflict(raw_expected, str(latest[0]) if latest else "missing")
            return Ok(EditorDraftHead(draft_id, artifact.value.fp1, principal.value))

        try:
            return self.sqlite.run(_mutate)
        except sqlite3.IntegrityError as exc:
            return policy_rejection(
                "client_draft_correlation",
                "correlation was already used by another first save",
                refusal="correlation_mismatch",
                error=str(exc),
            )

    def get_editor_draft_head(
        self,
        payload: object,
        *,
        operator_principal: object,
        capabilities: object | None = None,
    ) -> Result[EditorDraftHead]:
        gate = require_editor_draft_capability(capabilities, GET_EDITOR_DRAFT_HEAD_CAPABILITY)
        if is_refusal(gate):
            return gate
        if not isinstance(payload, Mapping):
            return invalid_input("payload", "get_editor_draft_head payload must be an object")
        values = cast(Mapping[str, object], payload)
        draft = _require_token("editor_draft_id", values.get("editor_draft_id"))
        if is_refusal(draft):
            return draft
        principal = _require_token("operator_principal", operator_principal)
        if is_refusal(principal):
            return principal
        row = self._row(draft.value)
        if row is None:
            return policy_rejection(
                "editor_draft_id",
                "no durable editor draft head exists for this id",
                editor_draft_id=draft.value,
            )
        if row[1] != principal.value:
            return policy_rejection(
                "editor_draft_id",
                "only the owner operator may read this editor draft head",
                owner=row[1],
            )
        return Ok(EditorDraftHead(str(row[0]), str(row[2]), str(row[1])))

    def publish_editor_draft(
        self,
        payload: object,
        *,
        operator_principal: object,
        capabilities: object | None = None,
    ) -> Result[Mapping[str, object]]:
        gate = require_editor_draft_capability(capabilities, PUBLISH_EDITOR_DRAFT_CAPABILITY)
        if is_refusal(gate):
            return gate
        if not isinstance(payload, Mapping):
            return invalid_input("payload", "publish_editor_draft payload must be an object")
        values = cast(Mapping[str, object], payload)
        draft = _require_token("editor_draft_id", values.get("editor_draft_id"))
        if is_refusal(draft):
            return draft
        principal = _require_token("operator_principal", operator_principal)
        if is_refusal(principal):
            return principal

        def _publish(conn: sqlite3.Connection) -> Result[Mapping[str, object]]:
            row = conn.execute(
                "SELECT editor_draft_id, owner_principal, editor_revision, "
                "client_draft_correlation, correlation_fp1, contribution_id, "
                "journal_seq, recorded_at FROM editor_draft_head "
                "WHERE editor_draft_id = ?",
                (draft.value,),
            ).fetchone()
            if row is None:
                return policy_rejection("editor_draft_id", "unknown daemon-issued editor draft")
            if row[1] != principal.value:
                return policy_rejection(
                    "editor_draft_id",
                    "only the owner operator may publish this editor draft",
                    owner=row[1],
                )
            if values.get("expected_revision") != row[2]:
                return _conflict(values.get("expected_revision"), str(row[2]))
            artifact = self._artifact(row[2])
            if is_refusal(artifact):
                return artifact
            parsed = _parse_graph_template(artifact.value.content)
            if is_refusal(parsed):
                return parsed
            valid = validate_graph_template_topology(parsed.value)
            if is_refusal(valid):
                return valid
            contribution_id = f"authoring-contribution:{draft.value}:{row[2]}"
            roster = AtomicRoster(self.authoring_roster_root)
            loaded = roster.load()
            if is_refusal(loaded):
                return loaded
            prior = dict(loaded.value)
            contributions = prior.get("published", [])
            if not isinstance(contributions, list):
                return invalid_input("authoring_roster", "published roster must be a list")
            updated = list(cast(list[object], contributions))
            record = {
                "contribution_id": contribution_id,
                "point": "graph_template",
                "qualified_id": parsed.value.qualified_id,
                "version": parsed.value.version,
                "editor_revision": str(row[2]),
                "bytes": artifact.value.content.decode("utf-8"),
                "published": False,
            }
            kept: list[object] = []
            for item in updated:
                if (
                    isinstance(item, Mapping)
                    and cast(Mapping[str, object], item).get("contribution_id") == contribution_id
                ):
                    continue
                kept.append(cast(object, item))
            updated = kept
            updated.append(record)
            prior["published"] = updated
            written = roster.publish(prior)
            if is_refusal(written):
                return written
            appended = self.journal.append_event(
                EDITOR_DRAFT_PUBLISHED_EVENT,
                payload={
                    "editor_draft_id": draft.value,
                    "editor_revision": str(row[2]),
                    "owner_principal": str(row[1]),
                    "contribution_id": contribution_id,
                    "qualified_id": parsed.value.qualified_id,
                    "version": parsed.value.version,
                },
            )
            if is_refusal(appended):
                restored_roster = roster.publish(loaded.value)
                return restored_roster if is_refusal(restored_roster) else appended
            conn.execute(
                "UPDATE editor_draft_head SET contribution_id = ?, journal_seq = ?, "
                "recorded_at = ? "
                "WHERE editor_draft_id = ? AND editor_revision = ?",
                (
                    contribution_id,
                    appended.value.record.journal_seq,
                    appended.value.record.recorded_at,
                    draft.value,
                    row[2],
                ),
            )
            return Ok(
                MappingProxyType(
                    {
                        "editor_draft_id": draft.value,
                        "editor_revision": str(row[2]),
                        "contribution_id": contribution_id,
                        "point": "graph_template",
                        "qualified_id": parsed.value.qualified_id,
                        "version": parsed.value.version,
                        "published": False,
                    }
                )
            )

        return self.sqlite.run(_publish)


def _parse_graph_template(content: bytes) -> Result[GraphTemplate]:
    try:
        raw = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return invalid_input(
            "graph_template",
            "draft bytes are not valid UTF-8 JSON",
            error=str(exc),
        )
    if not isinstance(raw, dict):
        return invalid_input("graph_template", "draft must encode a graph_template object")
    obj = cast(dict[str, object], raw)
    if obj.get("artifact_kind", "graph_template") != "graph_template":
        return invalid_input("artifact_kind", "published draft bytes must be graph_template")
    try:
        qualified_id = obj.get("qualified_id")
        version = obj.get("version")
        nodes = obj.get("nodes", [])
        edges = obj.get("edges", [])
        if not isinstance(qualified_id, str) or not isinstance(version, str):
            return invalid_input("graph_template", "qualified_id and version are required strings")
        if not isinstance(nodes, list) or not all(
            isinstance(item, Mapping) for item in cast(list[object], nodes)
        ):
            return invalid_input("nodes", "graph_template nodes must be a list of objects")
        if not isinstance(edges, list) or not all(
            isinstance(item, Mapping) for item in cast(list[object], edges)
        ):
            return invalid_input("edges", "graph_template edges must be a list of objects")
        template = GraphTemplate(
            qualified_id=qualified_id,
            version=version,
            nodes=tuple(cast(Mapping[str, object], item) for item in cast(list[object], nodes)),
            edges=tuple(cast(Mapping[str, object], item) for item in cast(list[object], edges)),
        )
    except (TypeError, ValueError) as exc:
        return invalid_input("graph_template", str(exc))
    return Ok(template)
