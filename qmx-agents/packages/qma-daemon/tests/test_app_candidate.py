"""MA02 real owner persistence/CAS/authority/failure tests; no provider or UI."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import cast

import pytest
from qma.core.app_candidate import CONTENT_SCHEMA
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.staging.app_candidate import SAVED_EVENT, AppCandidateService
from qma.wire.app_candidate import CANDIDATE_CAPABILITIES
from qma.wire.schemas import validate_instance
from qmf.core import Result, is_ok, is_refusal
from qmf.core.fingerprint import canonical_bytes, fingerprint
from qmf.data.store.refusals import policy_rejection


def process(root: Path, boot: str = "ma02-test") -> DaemonProcess:
    corpus = root / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    result = DaemonProcess.compose(
        root,
        machine="ma02-host",
        boot_epoch_id=boot,
        plugin_load_configs=research_corpus_plugin_load_config(corpus),
    )
    assert is_ok(result), result
    p = result.value
    assert is_ok(p.configure_pairing_ttl("PT15M"))
    return p


def mint(
    p: DaemonProcess,
    ref: str = "psess:author",
    profile: str = "authoring",
    instance: str | None = None,
    principal: str = "operator",
) -> None:
    result = p.product_sessions.mint(
        product_session_id=ref,
        profile=profile,
        principal=principal,
        contribution={"qualified_id": "analysis-backtest:qmb", "package_version": "0.1.0"},
        instance_id=instance,
        config_revision=4,
        as_of="2026-10-05T00:00:00Z",
        granted_ops=(),
        selected_refs=(),
        scope_path=[{"kind": "desk", "id": "research"}],
    )
    assert is_ok(result), result


def content(
    p: DaemonProcess, title: str = "A", composition: bytes = b'{"widget":"read"}'
) -> dict[str, object]:
    staged = p.artifacts.stage_complete_bytes(composition)
    assert is_ok(staged), staged
    asset = p.artifacts.stage_complete_bytes(b"\x00\xfflong-inert-asset")
    assert is_ok(asset)
    return {
        "schema": CONTENT_SCHEMA,
        "kind": "data-only",
        "metadata": {"title": title, "description": "A persisted draft"},
        "composition_ref": {
            "fp1": staged.value.fp1,
            "byte_count": len(composition),
            "media_type": "application/json",
        },
        "source_refs": [],
        "asset_refs": [
            {
                "fp1": asset.value.fp1,
                "byte_count": asset.value.byte_count,
                "media_type": "application/octet-stream",
            }
        ],
    }


def call(
    p: DaemonProcess,
    name: str,
    args: object,
    rid: str = "one",
    principal: object = PrincipalClass.OPERATOR,
) -> Result[Mapping[str, object]]:
    return p.app_candidate_request(
        name,
        args,
        operator_principal=principal,
        capabilities=dict.fromkeys(CANDIDATE_CAPABILITIES, True),
        producer_id="ma02-producer",
        request_id=rid,
    )


def save(
    p: DaemonProcess, data: dict[str, object], rid: str = "one", **extra: object
) -> Mapping[str, object]:
    result = call(
        p,
        "save_app_candidate",
        {
            "product_session_ref": "psess:author",
            "expected_context_revision": 0,
            "content": data,
            **extra,
        },
        rid,
    )
    assert is_ok(result), result
    assert is_ok(validate_instance(result.value, "app_candidate_version"))
    return result.value


def read(
    p: DaemonProcess, candidate: Mapping[str, object], **extra: object
) -> Mapping[str, object]:
    result = call(
        p,
        "get_app_candidate",
        {"product_session_ref": "psess:author", "candidate_id": candidate["candidate_id"], **extra},
    )
    assert is_ok(result), result
    assert is_ok(validate_instance(result.value, "app_candidate_snapshot"))
    return result.value


def count(p: DaemonProcess) -> int:
    events = p.journal.read_events()
    assert is_ok(events)
    return len([e for e in events.value if e.event == SAVED_EVENT])


def test_restart_exact_versions_receipts_and_projection_rebuild(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        data = content(p)
        first = save(p, data)
        second = save(
            p,
            content(p, "B"),
            "two",
            candidate_id=first["candidate_id"],
            expected_revision=first["revision"],
        )
        third = save(
            p,
            data,
            "three",
            candidate_id=first["candidate_id"],
            expected_revision=second["revision"],
        )
        assert third["content_fp1"] == first["content_fp1"]
        assert third["revision"] != first["revision"]
        assert third["parent_revision"] == second["revision"]
        assert p.sqlite.connection_count_evidence() == 1
        p.sqlite.execute("DELETE FROM app_candidate_state")
    finally:
        p.close()
    p = process(tmp_path, "ma02-reopen")
    try:
        assert read(p, first)["version"] == third
        assert read(p, first, revision=first["revision"])["version"] == first
        assert save(p, data) == first
        assert count(p) == 3
        cursor: object = third["revision"]
        history: list[object] = []
        while cursor:
            page = call(
                p,
                "get_app_candidate_history",
                {
                    "product_session_ref": "psess:author",
                    "candidate_id": first["candidate_id"],
                    "cursor_revision": cursor,
                },
            )
            assert is_ok(page), page
            versions = cast(list[dict[str, object]], page.value["versions"])
            history.append(versions[0]["revision"])
            cursor = page.value.get("next_revision")
        assert history == [third["revision"], second["revision"], first["revision"]]
    finally:
        p.close()


def test_competing_same_base_serializes_without_lost_data(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        first = save(p, content(p))
        left, right = content(p, "Left"), content(p, "Right")

        def edit(item: tuple[str, dict[str, object]]) -> Result[Mapping[str, object]]:
            rid, data = item
            return call(
                p,
                "save_app_candidate",
                {
                    "product_session_ref": "psess:author",
                    "expected_context_revision": 0,
                    "candidate_id": first["candidate_id"],
                    "expected_revision": first["revision"],
                    "content": data,
                },
                rid,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, [("left", left), ("right", right)]))
        accepted = [r.value for r in results if is_ok(r)]
        denied = [r for r in results if is_refusal(r)]
        assert len(accepted) == len(denied) == 1
        assert denied[0].context["refusal"] == "stale_revision"
        assert denied[0].context["wrote_version"] is False
        assert count(p) == 2
        assert read(p, first)["version"] == accepted[0]
        assert read(p, first, revision=first["revision"])["version"] == first
    finally:
        p.close()


def test_scope_profile_provenance_context_and_receipt_conflicts(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        mint(p, "psess:app", "app-use", "pack:analysis-backtest")
        mint(p, "psess:other", "app-use", "pack:dev-factory")
        mint(p, "psess:machine", "authoring", None, "machine")
        data = content(p)
        first = save(p, data, instance_id="pack:analysis-backtest")
        before = count(p)
        base = {
            "product_session_ref": "psess:author",
            "expected_context_revision": 0,
            "content": data,
        }
        for args in [
            {**base, "product_session_ref": "psess:app"},
            {**base, "product_session_ref": "psess:machine"},
            {**base, "product_session_ref": "psess:unknown"},
            {**base, "product_session_ref": "psess:app", "profile": "authoring"},
            {**base, "originating_authoring_session": "psess:author"},
            {**base, "parent_revision": first["revision"]},
            {**base, "expected_context_revision": 1},
            {**base, "candidate_id": "appcand:forged", "expected_revision": first["revision"]},
            {
                **base,
                "candidate_id": first["candidate_id"],
                "expected_revision": first["revision"],
                "instance_id": "pack:dev-factory",
            },
        ]:
            result = call(p, "save_app_candidate", args, json.dumps(args))
            assert is_refusal(result), result
        assert is_refusal(call(p, "save_app_candidate", base, "machine", PrincipalClass.MACHINE))
        assert is_refusal(
            call(p, "save_app_candidate", {**base, "content": content(p, "Changed")}, "one")
        )
        assert count(p) == before
        good = call(
            p,
            "get_app_candidate",
            {"product_session_ref": "psess:app", "candidate_id": first["candidate_id"]},
        )
        assert is_ok(good), good
        bad = call(
            p,
            "get_app_candidate",
            {"product_session_ref": "psess:other", "candidate_id": first["candidate_id"]},
        )
        assert is_refusal(bad) and bad.context["field"] == "instance_id"
        newer = save(
            p,
            content(p, "Second"),
            "second",
            candidate_id=first["candidate_id"],
            expected_revision=first["revision"],
        )
        assert newer["originating_authoring_session"] == "psess:author"
    finally:
        p.close()


@pytest.mark.parametrize(
    "body", [b"not JSON", b"[]", b'{"a":1,"a":2}', b'{"n":NaN}', b'{"n":1e999}']
)
def test_composition_malformed_refuses_before_candidate_commit(tmp_path: Path, body: bytes) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        result = call(
            p,
            "save_app_candidate",
            {
                "product_session_ref": "psess:author",
                "expected_context_revision": 0,
                "content": content(p, composition=body),
            },
        )
        assert is_refusal(result)
        assert count(p) == 0
    finally:
        p.close()


def test_reference_integrity_unknown_schema_and_inert_code(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        sentinel = tmp_path / "never-executed"
        code = f"__import__('pathlib').Path({str(sentinel)!r}).write_text('bad')"
        data = content(p, composition=json.dumps({"note": code}).encode())
        first = save(p, data)
        assert not sentinel.exists()
        assert p.app_candidates.is_candidate_artifact(cast(str, first["revision"]))
        for change in [
            {"kind": "executable"},
            {"entrypoint": code},
            {
                "composition_ref": {
                    "fp1": "fp1:sha256:" + "0" * 64,
                    "byte_count": 1,
                    "media_type": "application/json",
                }
            },
            {
                "composition_ref": {
                    **cast(dict[str, object], data["composition_ref"]),
                    "byte_count": 99,
                }
            },
            {"metadata": {"title": "A", "description": "", "grant_id": "forged"}},
        ]:
            result = call(
                p,
                "save_app_candidate",
                {
                    "product_session_ref": "psess:author",
                    "expected_context_revision": 0,
                    "content": {**data, **change},
                },
                json.dumps(change),
            )
            assert is_refusal(result), result
        assert count(p) == 1 and not sentinel.exists()
    finally:
        p.close()


def test_precommit_failure_then_retry_and_postcommit_projection_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        data = content(p)
        original = p.journal.append_event

        def fail(event: object, **kwargs: object) -> object:
            if event == SAVED_EVENT:
                return policy_rejection("test", "injected precommit failure")
            return original(event, **kwargs)  # type: ignore[arg-type]

        with monkeypatch.context() as patch:
            patch.setattr(p.journal, "append_event", fail)
            denied = call(
                p,
                "save_app_candidate",
                {
                    "product_session_ref": "psess:author",
                    "expected_context_revision": 0,
                    "content": data,
                },
            )
            assert is_refusal(denied)
        assert count(p) == 0
        first = save(p, data)

        def bad_projection(*_args: object, **_kwargs: object) -> None:
            raise sqlite3.OperationalError("injected projection failure")

        args = {
            "product_session_ref": "psess:author",
            "expected_context_revision": 0,
            "candidate_id": first["candidate_id"],
            "expected_revision": first["revision"],
            "content": content(p, "After"),
        }
        with monkeypatch.context() as patch:
            patch.setattr(AppCandidateService, "_insert", bad_projection)
            result = call(p, "save_app_candidate", args, "postcommit")
            assert is_refusal(result) and result.context["operation_committed"] is True
        recovered = call(p, "save_app_candidate", args, "postcommit")
        assert is_ok(recovered), recovered
        assert read(p, first)["version"] == recovered.value
        assert count(p) == 2
    finally:
        p.close()


def test_orphaned_journal_version_fails_recovery_preserving_projection(tmp_path: Path) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        first = save(p, content(p))
        held = p.artifacts.get(cast(str, first["revision"]))
        assert held is not None
        bad = p.journal.append_event(
            SAVED_EVENT,
            payload={
                "schema": first["schema"],
                "revision": first["revision"],
                "version_byte_count": held.byte_count,
                "candidate_id": first["candidate_id"],
                "operation_key": first["operation_key"],
                "request_fp1": first["request_fp1"],
                "principal_class": "operator",
            },
        )
        assert is_ok(bad)
        result = p.app_candidates.restore_from_journal()
        assert is_refusal(result)
        assert p.sqlite.execute("SELECT count(*) FROM app_candidate_state")[0][0] == 1
    finally:
        p.close()
    corpus = tmp_path / "corpus"
    reopened = DaemonProcess.compose(
        tmp_path,
        machine="ma02-host",
        boot_epoch_id="corrupt-reopen",
        plugin_load_configs=research_corpus_plugin_load_config(corpus),
    )
    assert is_refusal(reopened), reopened
    assert not (tmp_path / ".daemon_writer").exists()


@pytest.mark.parametrize("mutation", ["producer", "request-id", "identity", "scope", "context"])
def test_self_consistent_forged_version_refuses_recovery(tmp_path: Path, mutation: str) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        first = save(p, content(p))
        held = p.artifacts.get(cast(str, first["revision"]))
        assert held is not None
        version = json.loads(held.content)
        version["candidate_id"] = "appcand:" + "0" * 32
        version["request_id"] = "forged"
        if mutation == "producer":
            version["producer_id"] = ""
        elif mutation == "request-id":
            version["request_id"] = 123
        elif mutation == "identity":
            version["candidate_id"] = "appcand:client-named"
        elif mutation == "scope":
            version["instance_id"] = "pack:analysis-backtest"
        else:
            version["context_revision"] = 1
            version["intent"]["params"]["expected_context_revision"] = 1
        operation = fingerprint(
            {"producer_id": version["producer_id"], "id": version["request_id"]}
        )
        intent = fingerprint(version["intent"])
        assert is_ok(operation) and is_ok(intent)
        version["operation_key"] = operation.value.value
        version["request_fp1"] = intent.value.value
        encoded = canonical_bytes(version)
        assert is_ok(encoded)
        staged = p.artifacts.stage_complete_bytes(encoded.value)
        assert is_ok(staged)
        event = p.journal.append_event(
            SAVED_EVENT,
            payload={
                "schema": version["schema"],
                "revision": staged.value.fp1,
                "version_byte_count": staged.value.byte_count,
                "candidate_id": version["candidate_id"],
                "operation_key": version["operation_key"],
                "request_fp1": version["request_fp1"],
                "principal_class": "operator",
            },
        )
        assert is_ok(event)
        restored = p.app_candidates.restore_from_journal()
        assert is_refusal(restored), restored
        assert p.sqlite.execute("SELECT count(*) FROM app_candidate_state")[0][0] == 1
    finally:
        p.close()


def test_journal_commit_then_refusal_reconciles_same_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        args = {
            "product_session_ref": "psess:author",
            "expected_context_revision": 0,
            "content": content(p),
        }
        original = p.journal.append_event

        def uncertain(event: object, **kwargs: object) -> object:
            accepted = original(event, **kwargs)  # type: ignore[arg-type]
            if event == SAVED_EVENT:
                assert is_ok(accepted)
                return policy_rejection("test", "injected failure after durable append")
            return accepted

        with monkeypatch.context() as patch:
            patch.setattr(p.journal, "append_event", uncertain)
            refused = call(p, "save_app_candidate", args, "lost-ack")
            assert is_refusal(refused)
        assert count(p) == 1
        accepted = call(p, "save_app_candidate", args, "lost-ack")
        assert is_ok(accepted), accepted
        saved_events = p.journal.read_events()
        assert is_ok(saved_events)
        receipt = next(e.fingerprint for e in saved_events.value if e.event == SAVED_EVENT)
        assert accepted.value["receipt_fp1"] == receipt
        assert call(p, "save_app_candidate", args, "lost-ack") == accepted
        assert count(p) == 1
    finally:
        p.close()


@pytest.mark.parametrize("request_id", [None, 123, ""])
def test_save_requires_retryable_string_operation_id(tmp_path: Path, request_id: object) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        data = content(p)
        refused = p.app_candidate_request(
            "save_app_candidate",
            {
                "product_session_ref": "psess:author",
                "expected_context_revision": 0,
                "content": data,
            },
            operator_principal=PrincipalClass.OPERATOR,
            capabilities=dict.fromkeys(CANDIDATE_CAPABILITIES, True),
            producer_id="ma02-producer",
            request_id=request_id,
        )
        assert is_refusal(refused)
        assert count(p) == 0
    finally:
        p.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "fingerprint",
        "recorded_at",
        "world",
        "scope_path",
        "session_receipt",
        "class",
        "missing_class",
        "extra_envelope",
        "extra_scope",
        "event",
        "journal_seq",
        "occurred_at",
        "payload",
        "boolean_seq",
        "missing_fingerprint",
    ],
)
def test_corrupted_journal_receipt_refuses_restart_without_replacing_projection(
    tmp_path: Path, mutation: str
) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        first = save(p, content(p))
        before = p.sqlite.execute("SELECT * FROM app_candidate_state ORDER BY journal_seq")
    finally:
        p.close()
    journal = tmp_path / "qmf-data/live/journal/qma-daemon-events/000000.jsonl"
    rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    saved = next(row for row in rows if row["event"] == SAVED_EVENT)
    if mutation == "session_receipt":
        saved = next(row for row in rows if row["event"].startswith("product_session."))
    if mutation in ("fingerprint", "session_receipt"):
        saved["fingerprint"] = "fp1:sha256:" + "0" * 64
    elif mutation == "recorded_at":
        saved["recorded_at"] += 1
    elif mutation == "world":
        saved["world"] = "replay"
    elif mutation == "scope_path":
        saved["scope_path"] = [{"kind": "desk", "id": "changed"}]
    elif mutation == "class":
        saved["class"] = "corrupt-event-class"
    elif mutation == "missing_class":
        del saved["class"]
    elif mutation == "extra_envelope":
        saved["ignored"] = "corrupt envelope field"
    elif mutation == "extra_scope":
        saved["scope_path"] = [{"kind": "desk", "id": "research", "ignored": "corrupt"}]
    elif mutation == "event":
        saved["event"] = "app_candidate.not_saved"
    elif mutation == "journal_seq":
        saved["journal_seq"] += 1
    elif mutation == "occurred_at":
        saved["occurred_at"] += 1
    elif mutation == "payload":
        saved["payload"]["revision"] = "fp1:sha256:" + "0" * 64
    elif mutation == "boolean_seq":
        saved["journal_seq"] = True
    else:
        del saved["fingerprint"]
    if mutation in ("class", "missing_class", "extra_envelope", "extra_scope", "boolean_seq"):
        rehashed = fingerprint({key: value for key, value in saved.items() if key != "fingerprint"})
        assert is_ok(rehashed)
        saved["fingerprint"] = rehashed.value.value
    journal.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    corrupted = journal.read_bytes()
    reopened = DaemonProcess.compose(
        tmp_path,
        machine="ma02-host",
        boot_epoch_id="bad-receipt",
        plugin_load_configs=research_corpus_plugin_load_config(tmp_path / "corpus"),
    )
    assert is_refusal(reopened), reopened
    assert reopened.context["field"] == ("world" if mutation == "world" else "journal_event")
    with closing(
        sqlite3.connect(f"file:{(tmp_path / 'daemon/daemon.sqlite').as_posix()}?mode=ro", uri=True)
    ) as conn:
        assert (
            conn.execute("SELECT * FROM app_candidate_state ORDER BY journal_seq").fetchall()
            == before
        )
    assert before[0][4] and first["receipt_fp1"] != "fp1:sha256:" + "0" * 64
    assert journal.read_bytes() == corrupted
    assert not (tmp_path / ".daemon_writer").exists()


@pytest.mark.parametrize("field", ["title", "description", "media_type", "request_id"])
@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_malformed_unicode_refuses_without_save_and_valid_unicode_remains_usable(
    tmp_path: Path, field: str, surrogate: str
) -> None:
    p = process(tmp_path)
    try:
        mint(p)
        data = content(p)
        args: dict[str, object] = {
            "product_session_ref": "psess:author",
            "expected_context_revision": 0,
            "content": data,
        }
        request_id = "malformed"
        if field == "request_id":
            request_id = surrogate
        elif field == "media_type":
            cast(dict[str, object], data["composition_ref"])["media_type"] = surrogate
        else:
            cast(dict[str, object], data["metadata"])[field] = surrogate
        before = p.journal.read_events()
        assert is_ok(before)
        refused = call(p, "save_app_candidate", args, request_id)
        assert is_refusal(refused)
        assert refused.category.value == "invalid input"
        assert p.journal.read_events() == before
        valid = content(p, "Café e\u0301 📈")
        accepted = save(p, valid, "保存-π-📊")
        assert (
            cast(dict[str, object], cast(dict[str, object], accepted["content"])["metadata"])[
                "title"
            ]
            == "Café é 📈"
        )
        assert count(p) == 1
        assert save(p, valid, "保存-π-📊") == accepted
    finally:
        p.close()
