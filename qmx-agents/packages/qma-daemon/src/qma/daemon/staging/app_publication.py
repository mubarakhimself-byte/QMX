"""MA04 publication on existing journal/artifact/roster/installed host owners."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import cast

from qma.core.app_candidate import json_object, token, validate_unicode
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.journal.authoritative import JournalEventRecord
from qma.daemon.plugins.lifecycle import AtomicRoster
from qma.daemon.plugins.pack_ui import ensure_plugin_install_records_projection
from qma.daemon.sessions.product_session import ProductSession
from qma.daemon.staging.app_candidate import AppCandidateService
from qma.daemon.staging.app_validation import VALIDATED_EVENT, AppValidationService
from qma.wire.app_candidate import CANDIDATE_CAPABILITIES, invalid_input, policy_rejection
from qma.wire.app_publication import (
    HOST_PLUGIN_ID,
    PUBLICATION_SCHEMA,
    parse_publication_args,
    require_publication_capability,
)
from qma.wire.pack_ui_request import parse_pack_ui_request
from qma.wire.panel_composition import VALIDATION_CAPABILITIES, data_bytes
from qma.wire.schemas import validate_instance
from qmf.core import Ok, Result, is_ok, is_refusal
from qmf.core.fingerprint import fingerprint, fingerprint_bytes
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import storage_failure

PUBLISHED_EVENT = "app_candidate.published"
_SCHEMA = """CREATE TABLE IF NOT EXISTS app_candidate_publication (
candidate_id TEXT NOT NULL, active_revision TEXT PRIMARY KEY NOT NULL,
operation_key TEXT UNIQUE NOT NULL, request_fp1 TEXT NOT NULL,
payload TEXT NOT NULL, journal_seq INTEGER UNIQUE NOT NULL);
CREATE INDEX IF NOT EXISTS app_publication_head
ON app_candidate_publication(candidate_id,journal_seq);"""


@dataclass
class AppPublicationService:
    validation: AppValidationService
    roster: AtomicRoster
    _dirty: bool = field(default=False, init=False)

    @property
    def candidates(self) -> AppCandidateService:
        return self.validation.candidates

    def __post_init__(self) -> None:
        self.candidates.sqlite.run(lambda conn: conn.executescript(_SCHEMA))

    def capabilities(self) -> dict[str, object]:
        limits = self.validation.limits()
        available = (
            is_ok(limits)
            and limits.value is not None
            and self.validation.loader.get(HOST_PLUGIN_ID) is not None
        )
        return {
            "get_app_publication": True,
            "publish_app_candidate": available,
            "undo_app_publication": available,
        }

    def _rows(self, candidate_id: str | None = None) -> list[dict[str, object]]:
        sql = "SELECT payload FROM app_candidate_publication"
        params = () if candidate_id is None else (candidate_id,)
        if candidate_id is not None:
            sql += " WHERE candidate_id=?"
        return [
            cast(dict[str, object], json.loads(cast(str, row[0])))
            for row in self.candidates.sqlite.execute(sql + " ORDER BY journal_seq", params)
        ]

    def _installation(self, body: Mapping[str, object]) -> dict[str, object]:
        return {
            "instance_id": body["instance_id"],
            "availability_revision": body["availability_revision"],
            "plugin_id": HOST_PLUGIN_ID,
            "package_version": body["pack_version"],
            "pack_ui_request": body["pack_ui_request"],
            "diagnostics": [],
        }

    def _insert(self, body: Mapping[str, object], seq: int, conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT INTO app_candidate_publication VALUES(?,?,?,?,?,?)",
            (
                body["candidate_id"],
                body["active_revision"],
                body["operation_key"],
                body["request_fp1"],
                json.dumps(dict(body)),
                seq,
            ),
        )
        row = self._installation(body)
        conn.execute(
            "INSERT OR REPLACE INTO plugin_install_records VALUES(?,?,?,?,?,?,?)",
            (
                row["instance_id"],
                row["availability_revision"],
                row["plugin_id"],
                row["package_version"],
                json.dumps(row["pack_ui_request"], sort_keys=True),
                "[]",
                None,
            ),
        )

    def _access(
        self, session: ProductSession, body: Mapping[str, object], owner: str
    ) -> Result[None]:
        if body["owner_principal"] != owner:
            return policy_rejection("owner_principal", "publication belongs to another operator")
        if session.app_instance_id is not None and session.app_instance_id != body["instance_id"]:
            return policy_rejection("instance_id", "publication is outside immutable session scope")
        if session.profile == "app-use" and session.app_instance_id != body["instance_id"]:
            return policy_rejection("instance_id", "app-use requires exact installed host scope")
        return Ok(None)

    def ensure_current(self) -> Result[None]:
        if not self._dirty:
            return Ok(None)
        restored = self.restore_from_journal()
        if is_refusal(restored):
            return restored
        return self.reconcile_runtime()

    def _proof(
        self, args: Mapping[str, object], owner: str, *, historical: bool
    ) -> Result[Mapping[str, object]]:
        # A projected result cannot authorize an apply without full verified replay.
        restored = self.validation.restore_from_journal()
        if is_refusal(restored):
            return restored
        queried = self.validation.request(
            "get_app_candidate_validation",
            {
                key: args[key]
                for key in ("product_session_ref", "candidate_id", "revision", "validation_fp1")
            },
            principal_class=PrincipalClass.OPERATOR,
            owner_principal=owner,
            capabilities=dict.fromkeys(VALIDATION_CAPABILITIES, True),
        )
        if is_refusal(queried):
            return queried
        result = cast(dict[str, object], queried.value["result"])
        problems = cast(list[dict[str, object]], queried.value["current_errors"])
        if historical:
            problems = [e for e in problems if e["code"] != "STALE_CANDIDATE"]
        if problems or result["status"] != "valid":
            return policy_rejection(
                "validation_fp1", "recorded proof is invalid or stale", current_errors=problems
            )
        if (
            result["owner_principal"] != owner
            or result["product_session_ref"] != args["product_session_ref"]
            or result["context_revision"] != args["expected_context_revision"]
        ):
            return policy_rejection(
                "validation_fp1", "proof must match current authenticated authoring session"
            )
        # Consume the immutable proof and its actual journal receipt.
        events = self.candidates.journal.read_events()
        if is_refusal(events):
            return events
        event = next(
            (
                e
                for e in events.value
                if e.event == VALIDATED_EVENT
                and e.payload.get("validation_fp1") == args["validation_fp1"]
            ),
            None,
        )
        if event is None:
            return invalid_input("validation_fp1", "proof has no journal receipt")
        identity = event.verify_identity()
        if is_refusal(identity):
            return identity
        held = self.candidates.read_reference(
            {"fp1": args["validation_fp1"], "byte_count": event.payload["byte_count"]}
        )
        if is_refusal(held):
            return held
        if held.value != data_bytes(result) or queried.value["receipt_fp1"] != event.fingerprint:
            return invalid_input(
                "validation_fp1", "proof projection differs from authoritative bytes"
            )
        return queried

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
        gated = require_publication_capability(name, capabilities)
        if is_refusal(gated):
            return gated
        parsed = parse_publication_args(name, args)
        if is_refusal(parsed):
            return parsed
        owner = token("owner_principal", owner_principal)
        if is_refusal(owner):
            return owner
        with self.candidates.authority_lock, self.roster.synchronized():
            session = self.candidates.authorize_session(
                parsed.value["product_session_ref"], principal_class
            )
            if is_refusal(session):
                return session
            ready = self.ensure_current()
            if is_refusal(ready):
                return ready
            params = parsed.value
            rows = self._rows(cast(str, params["candidate_id"]))
            if name == "get_app_publication":
                if not rows:
                    return invalid_input("candidate_id", "no committed local publication")
                access = self._access(session.value, rows[-1], owner.value)
                if is_refusal(access):
                    return access
                return Ok(
                    {
                        "schema": PUBLICATION_SCHEMA,
                        "active": rows[-1],
                        "authorizes_invoke": False,
                        "health": "not-observed",
                    }
                )
            if session.value.profile != "authoring":
                return policy_rejection("profile", "app-use cannot publish or undo implementation")
            producer = token("producer_id", producer_id)
            if is_refusal(producer):
                return producer
            unicode = validate_unicode(request_id, "id")
            if is_refusal(unicode):
                return unicode
            if (
                not isinstance(request_id, str)
                or not request_id
                or len(request_id.encode("utf-8")) > 1024
            ):
                return invalid_input("id", "publication requires a bounded string operation id")
            operation = fingerprint({"producer_id": producer.value, "id": request_id})
            intent = fingerprint_bytes(
                data_bytes({"method": name, "params": params, "owner_principal": owner.value})
            )
            if is_refusal(operation):
                return operation
            prior = next(
                (row for row in self._rows() if row["operation_key"] == operation.value.value), None
            )
            if prior is not None:
                access = self._access(session.value, prior, owner.value)
                if is_refusal(access):
                    return access
                if prior["request_fp1"] != intent.value:
                    return policy_rejection(
                        "id",
                        "operation id reused with different intent",
                        refusal="idempotency_conflict",
                    )
                return Ok(prior)
            if params["expected_context_revision"] != session.value.context_revision:
                return policy_rejection(
                    "expected_context_revision",
                    "stale authoring context",
                    refusal="stale_revision",
                    current=session.value.context_revision,
                )
            active = rows[-1] if rows else None
            current = None if active is None else active["active_revision"]
            if params["expected_active_revision"] != current:
                return policy_rejection(
                    "expected_active_revision",
                    "active publication CAS lost",
                    refusal="stale_revision",
                    current=current,
                )
            host = self.validation.loader.get(HOST_PLUGIN_ID)
            if host is None:
                return policy_rejection("instance_id", "trusted authoring host unavailable")
            if active is not None and (
                active["instance_id"] != host.instance_id
                or active["pack_version"] != host.manifest.version
            ):
                return policy_rejection(
                    "instance_id",
                    "published app requires its original trusted host version",
                    refusal="incompatible_host",
                )
            access = self._access(
                session.value,
                {"instance_id": host.instance_id, "owner_principal": owner.value},
                owner.value,
            )
            if is_refusal(access):
                return access
            authorized = self.validation.loader.authorize_hosted_data_publication(principal_class)
            if is_refusal(authorized):
                return authorized
            if params["expected_availability_revision"] != host.availability_revision:
                return policy_rejection(
                    "expected_availability_revision",
                    "installed host CAS lost",
                    refusal="stale_revision",
                    current=host.availability_revision,
                )
            all_rows = self._rows()
            if any(row["candidate_id"] != params["candidate_id"] for row in all_rows):
                return policy_rejection(
                    "candidate_id",
                    "MA04 supports one local data-only app per authoring host",
                    refusal="host_slot_occupied",
                )
            selected = dict(params)
            target = None
            if name == "undo_app_publication":
                target = next(
                    (
                        row
                        for row in rows[:-1]
                        if row["active_revision"] == params["target_publication_revision"]
                    ),
                    None,
                )
                if target is None:
                    return invalid_input(
                        "target_publication_revision",
                        "undo requires a prior committed publication of this app",
                    )
                selected["revision"] = target["revision"]
            version = self.candidates.request(
                "get_app_candidate",
                {key: selected[key] for key in ("product_session_ref", "candidate_id", "revision")},
                principal_class=principal_class,
                owner_principal=owner.value,
                capabilities=dict.fromkeys(CANDIDATE_CAPABILITIES, True),
            )
            if is_refusal(version):
                return version
            proof = self._proof(selected, owner.value, historical=target is not None)
            if is_refusal(proof):
                return proof
            result = cast(dict[str, object], proof.value["result"])
            generation = 1 if active is None else cast(int, active["publication_generation"]) + 1
            base = (
                dict(host.pack_ui_request.request.to_payload())
                if active is None and host.pack_ui_request is not None
                else cast(dict[str, object], active["base_pack_ui_request"])
                if active is not None
                else None
            )
            if base is None:
                return policy_rejection("pack_ui_request", "authoring host projection unavailable")
            views = cast(list[dict[str, object]], result["view_requests"])
            request = {**base, "views": [*cast(list[object], base["views"]), *views]}
            checked = parse_pack_ui_request(request)
            if is_refusal(checked):
                return checked
            if (
                checked.value.pack_id != host.manifest.id
                or checked.value.pack_version != host.manifest.version
            ):
                return policy_rejection(
                    "pack_ui_request", "presentation must match trusted host version"
                )
            if len(data_bytes(request)) > 65536:
                return invalid_input(
                    "pack_ui_request", "installed presentation exceeds 64 KiB ceiling"
                )
            roster = self.roster.load()
            if is_refusal(roster):
                return roster
            body: dict[str, object] = {
                "schema": PUBLICATION_SCHEMA,
                "candidate_id": params["candidate_id"],
                "revision": selected["revision"],
                "content_fp1": result["content_fp1"],
                "validation_fp1": params["validation_fp1"],
                "validation_receipt_fp1": proof.value["receipt_fp1"],
                "catalog_fp1": result["catalog_fp1"],
                "instance_id": host.instance_id,
                "pack_id": HOST_PLUGIN_ID,
                "pack_version": host.manifest.version,
                "local_id": "miniapp-" + cast(str, params["candidate_id"]).removeprefix("appcand:"),
                "publication_generation": generation,
                "availability_revision": self.validation.loader.availability_revision() + 1,
                "roster_generation": cast(int, roster.value.get("roster_generation", 0)) + 1,
                "base_pack_ui_request": base,
                "pack_ui_request": request,
                "owner_principal": owner.value,
                "product_session_ref": session.value.product_session_id,
                "context_revision": session.value.context_revision,
                "producer_id": producer.value,
                "request_id": request_id,
                "operation_key": operation.value.value,
                "request_fp1": intent.value,
                "intent": {"method": name, "params": params, "owner_principal": owner.value},
                "action": "undo"
                if target is not None
                else "replace"
                if active is not None
                else "publish",
            }
            if active is not None:
                body["previous_active_revision"] = active["active_revision"]
            if target is not None:
                body["undo_target_revision"] = target["active_revision"]
            shape = validate_instance(body, "miniapp_publication_record")
            if is_refusal(shape):
                return shape
            encoded = data_bytes(body)
            if len(encoded) > 65536:
                return invalid_input("publication", "publication envelope exceeds 64 KiB ceiling")
            artifact = self.candidates.artifacts.stage_complete_bytes(encoded)
            if is_refusal(artifact):
                return artifact
            event = self.candidates.journal.append_event(
                PUBLISHED_EVENT,
                payload={
                    "schema": PUBLICATION_SCHEMA,
                    "active_revision": artifact.value.fp1,
                    "byte_count": artifact.value.byte_count,
                    "candidate_id": params["candidate_id"],
                    "installation": self._installation(body),
                },
            )
            self._dirty = True
            if is_refusal(event):
                return storage_failure(
                    "journal acceptance unconfirmed; reconcile the same operation",
                    context={
                        "operation_committed": "unknown",
                        "retry_same_id": True,
                        "reconciliation_required": True,
                    },
                )
            accepted = {
                **body,
                "active_revision": artifact.value.fp1,
                "receipt_fp1": event.value.record.fingerprint,
            }
            try:
                ensure_plugin_install_records_projection(self.candidates.sqlite)
                self.candidates.sqlite.run(
                    lambda conn: self._insert(accepted, event.value.record.journal_seq, conn)
                )
                reconciled = self.reconcile_runtime()
                if is_refusal(reconciled):
                    return self._committed(accepted, str(reconciled))
            except (sqlite3.Error, RuntimeError, OSError, ValueError) as exc:
                return self._committed(accepted, str(exc))
            self._dirty = False
            return Ok(accepted)

    @staticmethod
    def _committed(body: Mapping[str, object], reason: str) -> TypedRefusal:
        return storage_failure(
            reason,
            context={
                "operation_committed": True,
                "active_revision": body["active_revision"],
                "receipt_fp1": body["receipt_fp1"],
                "retry_same_id": True,
                "reconciliation_required": True,
            },
        )

    def reconcile_runtime(self) -> Result[None]:
        rows = self._rows()
        if not rows:
            self._dirty = False
            return Ok(None)
        active = rows[-1]
        snapshot = self.roster.load()
        if is_refusal(snapshot):
            return snapshot
        current = snapshot.value.get("miniapp_publication")
        if current != active:
            replacement = {**snapshot.value, "miniapp_publication": active}
            written = self.roster.publish(
                replacement,
                new_generation=max(
                    cast(int, snapshot.value.get("roster_generation", 0)) + 1,
                    cast(int, active["roster_generation"]),
                ),
            )
            if is_refusal(written):
                return written
        applied = self.validation.loader.apply_hosted_data_publication(active)
        if is_refusal(applied):
            return applied
        self._dirty = False
        return Ok(None)

    def restore_from_journal(self) -> Result[int]:
        """Verify the full accepted chain before rebuilding either named projection."""
        with self.candidates.authority_lock, self.roster.synchronized():
            events = self.candidates.journal.read_events()
            if is_refusal(events):
                return events
            recovered: list[tuple[dict[str, object], int]] = []
            operations: set[str] = set()
            head: dict[str, object] | None = None
            proofs: dict[str, JournalEventRecord] = {}
            sessions: dict[str, Mapping[str, object]] = {}
            installations: dict[str, Mapping[str, object]] = {}
            candidate_heads: dict[str, object] = {}
            availability_high_water = 0
            for event in events.value:
                if event.event == "app_candidate.saved":
                    candidate_heads[cast(str, event.payload["candidate_id"])] = event.payload[
                        "revision"
                    ]
                if event.event in {"plugin.enabled", "plugin.pack_ui_projection_failed"}:
                    installations[cast(str, event.payload["instance_id"])] = event.payload
                    availability_high_water = max(
                        availability_high_water, cast(int, event.payload["availability_revision"])
                    )
                if event.event.startswith("product_session.") and "profile" in event.payload:
                    sessions[cast(str, event.payload["product_session_id"])] = event.payload
                if event.event == VALIDATED_EVENT:
                    proofs[cast(str, event.payload["validation_fp1"])] = event
                if event.event != PUBLISHED_EVENT:
                    continue
                identity = event.verify_identity()
                if is_refusal(identity):
                    return identity
                payload = event.payload
                if (
                    set(payload)
                    != {"schema", "active_revision", "byte_count", "candidate_id", "installation"}
                    or payload["schema"] != PUBLICATION_SCHEMA
                    or not isinstance(payload["candidate_id"], str)
                    or not payload["candidate_id"].startswith("appcand:")
                    or isinstance(payload["byte_count"], bool)
                    or not isinstance(payload["byte_count"], int)
                    or not 1 <= payload["byte_count"] <= 65536
                ):
                    return invalid_input("publication", "malformed committed publication event")
                held = self.candidates.read_reference(
                    {"fp1": payload["active_revision"], "byte_count": payload["byte_count"]}
                )
                if is_refusal(held):
                    return held
                parsed = json_object(held.value)
                if is_refusal(parsed):
                    return parsed
                body = parsed.value
                shape = validate_instance(body, "miniapp_publication_record")
                if is_refusal(shape):
                    return shape
                fields = {
                    "schema",
                    "candidate_id",
                    "revision",
                    "content_fp1",
                    "validation_fp1",
                    "validation_receipt_fp1",
                    "catalog_fp1",
                    "instance_id",
                    "pack_id",
                    "pack_version",
                    "local_id",
                    "publication_generation",
                    "availability_revision",
                    "roster_generation",
                    "base_pack_ui_request",
                    "pack_ui_request",
                    "owner_principal",
                    "product_session_ref",
                    "context_revision",
                    "producer_id",
                    "request_id",
                    "operation_key",
                    "request_fp1",
                    "intent",
                    "action",
                }
                if head is not None:
                    fields.add("previous_active_revision")
                if body.get("action") == "undo":
                    fields.add("undo_target_revision")
                if (
                    set(body) != fields
                    or body.get("schema") != PUBLICATION_SCHEMA
                    or body.get("pack_id") != HOST_PLUGIN_ID
                    or body.get("instance_id") != "pack:" + HOST_PLUGIN_ID
                    or body.get("candidate_id") != payload["candidate_id"]
                    or body.get("local_id")
                    != "miniapp-" + payload["candidate_id"].removeprefix("appcand:")
                    or data_bytes(body) != held.value
                ):
                    return invalid_input("publication", "invalid immutable publication envelope")
                for key in (
                    "publication_generation",
                    "availability_revision",
                    "roster_generation",
                    "context_revision",
                ):
                    if (
                        isinstance(body[key], bool)
                        or not isinstance(body[key], int)
                        or cast(int, body[key]) < (0 if key == "context_revision" else 1)
                    ):
                        return invalid_input("publication", "invalid recorded revision")
                if body["publication_generation"] != (
                    1 if head is None else cast(int, head["publication_generation"]) + 1
                ) or body.get("previous_active_revision") != (
                    None if head is None else head["active_revision"]
                ):
                    return invalid_input("publication", "broken publication generation chain")
                if head is not None and (
                    body["candidate_id"] != head["candidate_id"]
                    or body["owner_principal"] != head["owner_principal"]
                    or body["base_pack_ui_request"] != head["base_pack_ui_request"]
                    or body["pack_version"] != head["pack_version"]
                    or cast(int, body["availability_revision"])
                    <= cast(int, head["availability_revision"])
                    or cast(int, body["roster_generation"]) <= cast(int, head["roster_generation"])
                ):
                    return invalid_input(
                        "publication", "publication changes immutable host ownership"
                    )
                raw_intent = body["intent"]
                if not isinstance(raw_intent, dict) or set(cast(dict[str, object], raw_intent)) != {
                    "method",
                    "params",
                    "owner_principal",
                }:
                    return invalid_input("publication", "malformed publication intent")
                intent = cast(dict[str, object], raw_intent)
                args = parse_publication_args(cast(str, intent["method"]), intent["params"])
                key = fingerprint({"producer_id": body["producer_id"], "id": body["request_id"]})
                request = fingerprint_bytes(data_bytes(intent))
                if is_refusal(args) or is_refusal(key):
                    return invalid_input("publication", "invalid operation identity")
                if (
                    key.value.value != body["operation_key"]
                    or key.value.value in operations
                    or request.value != body["request_fp1"]
                    or intent["owner_principal"] != body["owner_principal"]
                    or args.value["candidate_id"] != body["candidate_id"]
                    or args.value["validation_fp1"] != body["validation_fp1"]
                    or args.value["expected_active_revision"]
                    != (None if head is None else head["active_revision"])
                    or args.value["product_session_ref"] != body["product_session_ref"]
                    or args.value["expected_context_revision"] != body["context_revision"]
                ):
                    return invalid_input(
                        "publication", "publication operation/CAS identity mismatch"
                    )
                previous_host = installations.get(cast(str, body["instance_id"]))
                if (
                    previous_host is None
                    or previous_host["package_version"] != body["pack_version"]
                    or args.value["expected_availability_revision"]
                    != previous_host["availability_revision"]
                    or body["availability_revision"] != availability_high_water + 1
                ):
                    return invalid_input("publication", "historical installed host CAS mismatch")
                if (
                    head is None
                    and body["base_pack_ui_request"] != previous_host["pack_ui_request"]
                ):
                    return invalid_input(
                        "publication", "initial host presentation differs from installed owner"
                    )
                if (
                    body["action"] != "undo"
                    and candidate_heads.get(cast(str, body["candidate_id"])) != body["revision"]
                ):
                    return invalid_input("publication", "publication used a stale candidate head")
                origin = sessions.get(cast(str, body["product_session_ref"]))
                if (
                    origin is None
                    or origin.get("profile") != "authoring"
                    or origin.get("principal") != "operator"
                    or origin.get("context_revision") != body["context_revision"]
                ):
                    return invalid_input(
                        "publication", "publication lacks historical authoring authority"
                    )
                if body["action"] == "undo":
                    target = next(
                        (
                            row
                            for row, _ in recovered
                            if row["active_revision"] == body["undo_target_revision"]
                        ),
                        None,
                    )
                    if (
                        intent["method"] != "undo_app_publication"
                        or target is None
                        or target["revision"] != body["revision"]
                        or args.value["target_publication_revision"] != target["active_revision"]
                    ):
                        return invalid_input(
                            "publication", "undo target is not a prior compatible publication"
                        )
                elif (
                    body["action"] != ("publish" if head is None else "replace")
                    or intent["method"] != "publish_app_candidate"
                    or args.value["revision"] != body["revision"]
                ):
                    return invalid_input("publication", "invalid publish/replace action")
                proof_event = proofs.get(cast(str, body["validation_fp1"]))
                if proof_event is None or proof_event.fingerprint != body["validation_receipt_fp1"]:
                    return invalid_input(
                        "publication", "publication lacks preceding validation receipt"
                    )
                proof_payload = proof_event.payload
                proof_bytes = self.candidates.read_reference(
                    {"fp1": body["validation_fp1"], "byte_count": proof_payload["byte_count"]}
                )
                if is_refusal(proof_bytes):
                    return proof_bytes
                proof = json_object(proof_bytes.value)
                if is_refusal(proof):
                    return proof
                if proof.value.get("status") != "valid" or any(
                    proof.value.get(k) != body[k]
                    for k in (
                        "candidate_id",
                        "revision",
                        "content_fp1",
                        "catalog_fp1",
                        "owner_principal",
                        "product_session_ref",
                        "context_revision",
                    )
                ):
                    return invalid_input("publication", "publication differs from verified proof")
                base = parse_pack_ui_request(body["base_pack_ui_request"])
                views = parse_pack_ui_request(body["pack_ui_request"])
                if (
                    is_refusal(base)
                    or is_refusal(views)
                    or base.value.pack_id != HOST_PLUGIN_ID
                    or base.value.pack_version != body["pack_version"]
                    or body["pack_ui_request"]
                    != {
                        **dict(base.value.to_payload()),
                        "views": [
                            *cast(list[object], base.value.to_payload()["views"]),
                            *cast(list[object], proof.value["view_requests"]),
                        ],
                    }
                    or payload["installation"] != self._installation(body)
                ):
                    return invalid_input(
                        "publication", "publication presentation differs from verified adapter"
                    )
                accepted = {
                    **body,
                    "active_revision": payload["active_revision"],
                    "receipt_fp1": event.fingerprint,
                }
                installations[cast(str, body["instance_id"])] = self._installation(body)
                availability_high_water = cast(int, body["availability_revision"])
                recovered.append((accepted, event.journal_seq))
                head = accepted
                operations.add(key.value.value)
            try:
                ensure_plugin_install_records_projection(self.candidates.sqlite)

                def rebuild(conn: sqlite3.Connection) -> None:
                    conn.execute("DELETE FROM app_candidate_publication")
                    for body, seq in recovered:
                        self._insert(body, seq, conn)

                self.candidates.sqlite.run(rebuild)
            except (sqlite3.Error, RuntimeError) as exc:
                return storage_failure(str(exc), context={"field": "app_candidate_publication"})
            self._dirty = bool(recovered)
            return Ok(len(recovered))
