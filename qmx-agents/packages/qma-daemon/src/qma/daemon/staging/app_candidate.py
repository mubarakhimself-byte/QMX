"""Journal-authoritative Mini App versions on the existing artifact/SQLite owners."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Final, cast

from qma.core.app_candidate import (
    VERSION_SCHEMA,
    CandidateContent,
    json_object,
    parse_candidate_content,
    token,
    validate_unicode,
)
from qma.core.vocabulary.enums import ArtifactCompleteness, PrincipalClass
from qma.daemon.artifacts.store import ArtifactStore
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.persistence.sqlite_writer import SingleSqliteWriter
from qma.daemon.sessions.product_session import (
    ProductSession,
    ProductSessionService,
    parse_product_session,
)
from qma.wire.app_candidate import (
    CANDIDATE_PROJECTION,
    CANDIDATE_SNAPSHOT_SCHEMA,
    parse_candidate_args,
    require_candidate_capability,
)
from qmf.core import Fingerprint, Ok, Result, is_refusal
from qmf.core.fingerprint import canonical_bytes, fingerprint, fingerprint_bytes
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

SAVED_EVENT: Final[str] = "app_candidate.saved"
_SCHEMA: Final[str] = """
CREATE TABLE IF NOT EXISTS app_candidate_state (
    candidate_id TEXT NOT NULL,
    revision TEXT PRIMARY KEY NOT NULL,
    operation_key TEXT UNIQUE NOT NULL,
    request_fp1 TEXT NOT NULL,
    payload TEXT NOT NULL,
    journal_seq INTEGER UNIQUE NOT NULL
);
CREATE INDEX IF NOT EXISTS app_candidate_head
ON app_candidate_state(candidate_id, journal_seq);
"""


@dataclass
class AppCandidateService:
    """One acceptance path; projection rows are disposable journal folds."""

    journal: AuthoritativeJournal
    sqlite: SingleSqliteWriter
    artifacts: ArtifactStore
    sessions: ProductSessionService
    instance_exists: Callable[[str], bool]
    _dirty: bool = field(default=False, init=False)

    @property
    def authority_lock(self) -> RLock:
        return self.sessions.authority_lock

    def __post_init__(self) -> None:
        declared = self.journal.declare_store(CANDIDATE_PROJECTION)
        registered = self.journal.register_fold(CANDIDATE_PROJECTION)
        if is_refusal(declared) or is_refusal(registered):
            raise RuntimeError("MA02 named candidate fold declaration refused")
        self.sqlite.run(lambda conn: conn.executescript(_SCHEMA))

    def is_candidate_artifact(self, fp1: str) -> bool:
        """Saved versions/content/compositions cannot become runnable draft targets."""
        with self.authority_lock:
            if self._dirty:
                restored = self.restore_from_journal()
                if is_refusal(restored):
                    return True
            for row in self.sqlite.execute("SELECT payload FROM app_candidate_state"):
                version = cast(dict[str, object], json.loads(cast(str, row[0])))
                content = cast(dict[str, object], version["content"])
                composition = cast(dict[str, object], content["composition_ref"])
                if fp1 in (version["revision"], version["content_fp1"], composition["fp1"]):
                    return True
            return False

    def _rows(self, candidate_id: str) -> list[dict[str, object]]:
        return [
            cast(dict[str, object], json.loads(cast(str, row[0])))
            for row in self.sqlite.execute(
                "SELECT payload FROM app_candidate_state WHERE candidate_id = ? "
                "ORDER BY journal_seq",
                (candidate_id,),
            )
        ]

    def _artifact_bytes(self, ref: Mapping[str, object]) -> Result[bytes]:
        parsed = Fingerprint.try_create(ref["fp1"])
        count = ref["byte_count"]
        if is_refusal(parsed):
            return parsed
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return invalid_input("byte_count", "invalid immutable byte count")
        fp1 = parsed.value.value
        held = self.artifacts.get(fp1)
        if (
            held is None
            or held.completeness != ArtifactCompleteness.COMPLETE.value
            or held.byte_count != ref["byte_count"]
            or len(held.content) != ref["byte_count"]
            or fingerprint_bytes(held.content).value != fp1
        ):
            return invalid_input(
                "artifact_ref",
                "reference must match daemon-held local-complete bytes",
                fp1=fp1,
                local_complete=False,
            )
        return Ok(held.content)

    def read_reference(self, ref: Mapping[str, object]) -> Result[bytes]:
        """MA03 reuses exact local-complete immutable-byte verification."""
        return self._artifact_bytes(ref)

    def version_record(self, candidate_id: str, revision: str) -> Mapping[str, object] | None:
        """Trusted recovery seam; public transport must use request authorization."""
        return next((row for row in self._rows(candidate_id) if row["revision"] == revision), None)

    def _content(self, content: CandidateContent) -> Result[None]:
        for ref in content.refs():
            checked = self._artifact_bytes(ref)
            if is_refusal(checked):
                return checked
        composition = self._artifact_bytes(content.refs()[0])
        if is_refusal(composition):
            return composition
        parsed = json_object(composition.value)
        if is_refusal(parsed):
            return parsed
        # This is inert JSON, not an MA03 catalog/operation/renderer verdict.
        return Ok(None)

    def _session(self, ref: object, principal: object) -> Result[ProductSession]:
        if principal is not PrincipalClass.OPERATOR:
            return policy_rejection(
                "principal_class", "candidate access requires an operator pairing"
            )
        found = self.sessions.get(ref)
        if is_refusal(found):
            return found
        if found.value.principal != PrincipalClass.OPERATOR.value:
            return policy_rejection("principal", "candidate session must be operator-owned")
        return found

    def _access(
        self, session: ProductSession, version: Mapping[str, object], owner: str
    ) -> Result[None]:
        if version["owner_principal"] != owner:
            return policy_rejection("owner_principal", "candidate belongs to another operator")
        instance = version.get("instance_id")
        if session.profile == "app-use" and (
            instance is None or instance != session.app_instance_id
        ):
            return policy_rejection("instance_id", "candidate is outside app-use scope")
        if (
            session.profile == "authoring"
            and session.app_instance_id is not None
            and (instance != session.app_instance_id)
        ):
            return policy_rejection("instance_id", "candidate is outside bound authoring scope")
        return Ok(None)

    def request(
        self,
        name: str,
        args: object,
        *,
        principal_class: object,
        owner_principal: object,
        capabilities: object,
        producer_id: object = None,
        request_id: object = None,
    ) -> Result[Mapping[str, object]]:
        gated = require_candidate_capability(name, capabilities)
        if is_refusal(gated):
            return gated
        parsed = parse_candidate_args(name, args)
        if is_refusal(parsed):
            return parsed
        owner = token("owner_principal", owner_principal)
        if is_refusal(owner):
            return owner
        with self.authority_lock:
            session = self._session(parsed.value["product_session_ref"], principal_class)
            if is_refusal(session):
                return session
            if self._dirty:
                restored = self.restore_from_journal()
                if is_refusal(restored):
                    return restored
            if name == "save_app_candidate":
                return self._save(parsed.value, session.value, owner.value, producer_id, request_id)
            candidate_id = cast(str, parsed.value["candidate_id"])
            rows = self._rows(candidate_id)
            if not rows:
                return invalid_input("candidate_id", "candidate not found")
            access = self._access(session.value, rows[-1], owner.value)
            if is_refusal(access):
                return access
            selected = parsed.value.get(
                "revision", parsed.value.get("cursor_revision", rows[-1]["revision"])
            )
            version = next((row for row in rows if row["revision"] == selected), None)
            if version is None:
                return invalid_input("revision", "version is not in this candidate chain")
            result: dict[str, object] = {
                "schema": CANDIDATE_SNAPSHOT_SCHEMA,
                "candidate_id": candidate_id,
                "current_revision": rows[-1]["revision"],
                "validated": False,
                "published": False,
            }
            if name == "get_app_candidate_history":
                # One immutable receipt per page; cursor pins the remaining lineage.
                result["versions"] = [version]
                if "parent_revision" in version:
                    result["next_revision"] = version["parent_revision"]
            else:
                result["version"] = version
            return Ok(result)

    def _save(
        self,
        args: Mapping[str, object],
        session: ProductSession,
        owner: str,
        producer_id: object,
        request_id: object,
    ) -> Result[Mapping[str, object]]:
        if session.profile != "authoring":
            return policy_rejection("profile", "app-use cannot save candidates", saves=False)
        producer = token("producer_id", producer_id)
        if is_refusal(producer):
            return producer
        if not isinstance(request_id, str) or not request_id.strip():
            return invalid_input("id", "candidate save requires a non-empty string request id")
        unicode = validate_unicode(request_id, "id")
        if is_refusal(unicode):
            return unicode
        key_result = fingerprint({"producer_id": producer.value, "id": request_id})
        intent_result = fingerprint({"params": dict(args), "owner_principal": owner})
        if is_refusal(key_result):
            return key_result
        if is_refusal(intent_result):
            return intent_result
        key, intent = key_result.value.value, intent_result.value.value
        prior = self.sqlite.execute(
            "SELECT request_fp1, payload FROM app_candidate_state WHERE operation_key = ?", (key,)
        )
        if prior:
            version = cast(dict[str, object], json.loads(cast(str, prior[0][1])))
            access = self._access(session, version, owner)
            if is_refusal(access):
                return access
            if prior[0][0] != intent:
                return policy_rejection(
                    "id",
                    "operation identity reused with different intent",
                    refusal="idempotency_conflict",
                )
            return Ok(version)
        if args["expected_context_revision"] != session.context_revision:
            return policy_rejection(
                "expected_context_revision",
                "stale authoring context",
                refusal="stale_revision",
                current=session.context_revision,
            )
        content = parse_candidate_content(args["content"])
        if is_refusal(content):
            return content
        refs = self._content(content.value)
        if is_refusal(refs):
            return refs
        rows = self._rows(cast(str, args["candidate_id"])) if "candidate_id" in args else []
        if "candidate_id" in args and not rows:
            return invalid_input("candidate_id", "candidate not found; identity is daemon-issued")
        parent = rows[-1] if rows else None
        if parent is not None:
            access = self._access(session, parent, owner)
            if is_refusal(access):
                return access
            if args["expected_revision"] != parent["revision"]:
                return policy_rejection(
                    "expected_revision",
                    "stale candidate head; reload before saving",
                    refusal="stale_revision",
                    expected=args["expected_revision"],
                    current=parent["revision"],
                    wrote_version=False,
                )
            candidate_id = cast(str, parent["candidate_id"])
            instance = parent.get("instance_id")
            origin = cast(str, parent["originating_authoring_session"])
        else:
            candidate_id = "appcand:" + uuid.uuid4().hex
            instance = args.get("instance_id", session.app_instance_id)
            origin = session.product_session_id
            if session.app_instance_id is not None and instance != session.app_instance_id:
                return policy_rejection("instance_id", "cannot retarget bound authoring scope")
            if instance is not None and not self.instance_exists(cast(str, instance)):
                return policy_rejection(
                    "instance_id", "maintenance target is not an installed instance"
                )
        stored_content = self.artifacts.stage_complete_bytes(content.value.encoded)
        if is_refusal(stored_content):
            return stored_content
        version: dict[str, object] = {
            "schema": VERSION_SCHEMA,
            "candidate_id": candidate_id,
            "content_fp1": stored_content.value.fp1,
            "content_byte_count": stored_content.value.byte_count,
            "owner_principal": owner,
            "principal_class": PrincipalClass.OPERATOR.value,
            "originating_authoring_session": origin,
            "authoring_session": session.product_session_id,
            "context_revision": session.context_revision,
            "operation_key": key,
            "request_fp1": intent,
            "producer_id": producer.value,
            "request_id": request_id,
            "intent": {"params": dict(args), "owner_principal": owner},
        }
        if parent is not None:
            version["parent_revision"] = parent["revision"]
        if instance is not None:
            version["instance_id"] = instance
        encoded = canonical_bytes(version)
        if is_refusal(encoded):
            return encoded
        normalized_version = json_object(encoded.value)
        if is_refusal(normalized_version):
            return normalized_version
        version = normalized_version.value
        stored_version = self.artifacts.stage_complete_bytes(encoded.value)
        if is_refusal(stored_version):
            return stored_version
        event = self.journal.append_event(
            SAVED_EVENT,
            payload={
                "schema": VERSION_SCHEMA,
                "revision": stored_version.value.fp1,
                "version_byte_count": stored_version.value.byte_count,
                "candidate_id": candidate_id,
                "operation_key": key,
                "request_fp1": intent,
                "principal_class": PrincipalClass.OPERATOR.value,
            },
        )
        if is_refusal(event):
            self._dirty = True
            return event
        accepted = {
            **version,
            "revision": stored_version.value.fp1,
            "receipt_fp1": event.value.record.fingerprint,
            "content": content.value.to_payload(),
        }
        try:
            self._insert(accepted, event.value.record.journal_seq)
        except sqlite3.Error, RuntimeError:
            self._dirty = True
            return storage_failure(
                "candidate committed; projection rebuild required",
                context={
                    "field": CANDIDATE_PROJECTION,
                    "operation_committed": True,
                    "candidate_id": candidate_id,
                    "revision": accepted["revision"],
                    "retry_same_id": True,
                },
            )
        return Ok(accepted)

    def _insert(self, version: Mapping[str, object], seq: int) -> None:
        self.sqlite.execute(
            "INSERT INTO app_candidate_state VALUES (?, ?, ?, ?, ?, ?)",
            (
                version["candidate_id"],
                version["revision"],
                version["operation_key"],
                version["request_fp1"],
                json.dumps(dict(version)),
                seq,
            ),
        )
        result = self.journal.stores.materialize_on_first_write(CANDIDATE_PROJECTION)
        if is_refusal(result):
            raise RuntimeError("candidate fold materialization refused")

    def restore_from_journal(self) -> Result[int]:
        """Validate complete history before replacing any derived state."""
        with self.authority_lock:
            stream = self.journal.read_events()
            if is_refusal(stream):
                return stream
            heads: dict[str, dict[str, object]] = {}
            operations: set[str] = set()
            recovered: list[tuple[dict[str, object], int]] = []
            historical_sessions: dict[str, ProductSession] = {}
            for event in stream.value:
                if event.event == SAVED_EVENT or event.event.startswith("product_session."):
                    identity = event.verify_identity()
                    if is_refusal(identity):
                        return identity
                if event.event.startswith("product_session.") and {
                    "product_session_id",
                    "profile",
                    "context",
                } <= set(event.payload):
                    session_record = parse_product_session(dict(event.payload))
                    if is_refusal(session_record):
                        return session_record
                    historical_sessions[session_record.value.product_session_id] = (
                        session_record.value
                    )
                if event.event != SAVED_EVENT:
                    continue
                payload = event.payload
                if set(payload) != {
                    "schema",
                    "revision",
                    "version_byte_count",
                    "candidate_id",
                    "operation_key",
                    "request_fp1",
                    "principal_class",
                }:
                    return invalid_input(CANDIDATE_PROJECTION, "malformed saved event")
                held = self._artifact_bytes(
                    {"fp1": payload["revision"], "byte_count": payload["version_byte_count"]}
                )
                if is_refusal(held):
                    return held
                parsed = json_object(held.value)
                if is_refusal(parsed):
                    return parsed
                version = parsed.value
                required = {
                    "schema",
                    "candidate_id",
                    "content_fp1",
                    "content_byte_count",
                    "owner_principal",
                    "principal_class",
                    "originating_authoring_session",
                    "authoring_session",
                    "context_revision",
                    "operation_key",
                    "request_fp1",
                    "producer_id",
                    "request_id",
                    "intent",
                }
                if not required <= set(version) or not set(version) <= required | {
                    "parent_revision",
                    "instance_id",
                }:
                    return invalid_input(CANDIDATE_PROJECTION, "invalid immutable version envelope")
                if (
                    any(
                        payload[key] != version[key]
                        for key in (
                            "schema",
                            "candidate_id",
                            "operation_key",
                            "request_fp1",
                            "principal_class",
                        )
                    )
                    or version["schema"] != VERSION_SCHEMA
                    or version["principal_class"] != "operator"
                ):
                    return invalid_input(CANDIDATE_PROJECTION, "saved event differs from version")
                canonical = canonical_bytes(version)
                if is_refusal(canonical):
                    return canonical
                if canonical.value != held.value:
                    return invalid_input(CANDIDATE_PROJECTION, "version bytes must be canonical")
                candidate_id = version["candidate_id"]
                if (
                    not isinstance(candidate_id, str)
                    or re.fullmatch(r"appcand:[0-9a-f]{32}", candidate_id) is None
                ):
                    return invalid_input(CANDIDATE_PROJECTION, "invalid daemon candidate identity")
                key = version["operation_key"]
                if not isinstance(key, str) or key in operations:
                    return invalid_input(CANDIDATE_PROJECTION, "duplicate operation receipt")
                parent = heads.get(candidate_id)
                if parent is None:
                    if "parent_revision" in version or (
                        version["originating_authoring_session"] != version["authoring_session"]
                    ):
                        return invalid_input(CANDIDATE_PROJECTION, "orphaned first version")
                elif version.get("parent_revision") != parent["revision"] or any(
                    version.get(k) != parent.get(k)
                    for k in ("owner_principal", "instance_id", "originating_authoring_session")
                ):
                    return invalid_input(CANDIDATE_PROJECTION, "broken parent or provenance chain")
                for session_ref in (
                    version["originating_authoring_session"],
                    version["authoring_session"],
                ):
                    if not isinstance(session_ref, str) or session_ref not in historical_sessions:
                        return invalid_input(CANDIDATE_PROJECTION, "session did not exist at save")
                    session = Ok(historical_sessions[session_ref])
                    if (
                        session.value.profile != "authoring"
                        or session.value.principal != "operator"
                    ):
                        return invalid_input(
                            CANDIDATE_PROJECTION, "saved authority is not authoring"
                        )
                    if session.value.app_instance_id is not None and (
                        session.value.app_instance_id != version.get("instance_id")
                    ):
                        return invalid_input(
                            CANDIDATE_PROJECTION, "recorded scope conflicts with session"
                        )
                context = version["context_revision"]
                if isinstance(context, bool) or not isinstance(context, int) or context < 0:
                    return invalid_input(CANDIDATE_PROJECTION, "invalid recorded context revision")
                editor = historical_sessions[cast(str, version["authoring_session"])]
                if context != editor.context_revision:
                    return invalid_input(
                        CANDIDATE_PROJECTION, "saved context did not match at commit"
                    )
                for value in (version["operation_key"], version["request_fp1"]):
                    checked = Fingerprint.try_create(value)
                    if is_refusal(checked):
                        return checked
                owner = token("owner_principal", version["owner_principal"])
                if is_refusal(owner):
                    return owner
                content_bytes = self._artifact_bytes(
                    {"fp1": version["content_fp1"], "byte_count": version["content_byte_count"]}
                )
                if is_refusal(content_bytes):
                    return content_bytes
                content_json = json_object(content_bytes.value)
                if is_refusal(content_json):
                    return content_json
                content = parse_candidate_content(content_json.value)
                if is_refusal(content):
                    return content
                if content.value.encoded != content_bytes.value:
                    return invalid_input(CANDIDATE_PROJECTION, "content bytes must be canonical")
                producer = token("producer_id", version["producer_id"])
                if is_refusal(producer):
                    return producer
                if not isinstance(version["request_id"], str) or not version["request_id"].strip():
                    return invalid_input(CANDIDATE_PROJECTION, "invalid saved request identity")
                operation = fingerprint(
                    {"producer_id": version["producer_id"], "id": version["request_id"]}
                )
                request_hash = fingerprint(version["intent"])
                if is_refusal(operation):
                    return operation
                if is_refusal(request_hash):
                    return request_hash
                if (
                    operation.value.value != key
                    or request_hash.value.value != version["request_fp1"]
                ):
                    return invalid_input(CANDIDATE_PROJECTION, "receipt identity or intent differs")
                raw_intent = version["intent"]
                if not isinstance(raw_intent, Mapping):
                    return invalid_input(CANDIDATE_PROJECTION, "invalid saved intent")
                saved_intent = cast(Mapping[str, object], raw_intent)
                intent_args = parse_candidate_args("save_app_candidate", saved_intent.get("params"))
                if is_refusal(intent_args):
                    return intent_args
                facts = intent_args.value
                if (
                    set(saved_intent) != {"params", "owner_principal"}
                    or saved_intent["owner_principal"] != version["owner_principal"]
                    or facts["product_session_ref"] != version["authoring_session"]
                    or facts["expected_context_revision"] != context
                    or facts["content"] != content.value.to_payload()
                    or facts.get("expected_revision") != version.get("parent_revision")
                    or (parent is not None and facts.get("candidate_id") != candidate_id)
                    or (
                        parent is None
                        and facts.get("instance_id", editor.app_instance_id)
                        != version.get("instance_id")
                    )
                    or (
                        "instance_id" in facts
                        and facts["instance_id"] != version.get("instance_id")
                    )
                ):
                    return invalid_input(
                        CANDIDATE_PROJECTION, "saved intent conflicts with version facts"
                    )
                refs = self._content(content.value)
                if is_refusal(refs):
                    return refs
                accepted = {
                    **version,
                    "revision": payload["revision"],
                    "receipt_fp1": event.fingerprint,
                    "content": content.value.to_payload(),
                }
                heads[candidate_id] = accepted
                operations.add(key)
                recovered.append((accepted, event.journal_seq))

            def replace(conn: sqlite3.Connection) -> None:
                conn.execute("DELETE FROM app_candidate_state")
                for version, seq in recovered:
                    conn.execute(
                        "INSERT INTO app_candidate_state VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            version["candidate_id"],
                            version["revision"],
                            version["operation_key"],
                            version["request_fp1"],
                            json.dumps(version),
                            seq,
                        ),
                    )

            try:
                self.sqlite.run(replace)
            except sqlite3.Error, RuntimeError:
                return storage_failure(
                    "candidate projection recovery failed", context={"field": CANDIDATE_PROJECTION}
                )
            self._dirty = False
            if recovered:
                self.journal.stores.materialize_on_first_write(CANDIDATE_PROJECTION)
            return Ok(len(recovered))
