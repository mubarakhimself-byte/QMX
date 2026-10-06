"""MA04 real backend owners: lifecycle, fencing, failure barriers and recovery."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.artifacts.store import StagedArtifact
from qma.daemon.plugins.loader import LoadedPlugin
from qma.daemon.process import DaemonProcess
from qma.daemon.staging.app_publication import PUBLISHED_EVENT
from qma.wire.app_publication import PUBLICATION_CAPABILITIES
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import storage_failure
from test_app_candidate import mint, process, save
from test_app_validation import LIMITS, example, need, validate


@pytest.fixture
def owner(tmp_path: Path) -> Iterator[DaemonProcess]:
    (tmp_path / "operator-config.json").write_text(
        json.dumps({"miniapp_validation_limits": LIMITS})
    )
    p = process(tmp_path)
    mint(p)
    mint(p, "psess:app", "app-use", "pack:dev-factory")
    mint(p, "psess:other", "app-use", "pack:analysis-backtest")
    try:
        yield p
    finally:
        p.close()


def version(p: DaemonProcess, body: Any, rid: str, previous: Any = None) -> Any:
    raw = json.dumps(body).encode()
    staged = need(p.artifacts.stage_complete_bytes(raw))
    content: dict[str, object] = {
        "schema": "qma.miniapp.candidate-content.v1",
        "kind": "data-only",
        "metadata": {"title": "Lifecycle", "description": ""},
        "composition_ref": {
            "fp1": staged.fp1,
            "byte_count": len(raw),
            "media_type": "application/json",
        },
        "source_refs": [],
        "asset_refs": [],
    }
    args = (
        {}
        if previous is None
        else {"candidate_id": previous["candidate_id"], "expected_revision": previous["revision"]}
    )
    return save(p, content, rid, **args)


def host(p: DaemonProcess) -> LoadedPlugin:
    loaded = p.roster.loader.get("dev-factory")
    assert loaded is not None
    return loaded


def params(p: DaemonProcess, candidate: Any, proof: Any, active: Any = None) -> dict[str, Any]:
    return {
        "product_session_ref": "psess:author",
        "candidate_id": candidate["candidate_id"],
        "revision": candidate["revision"],
        "validation_fp1": proof["validation_fp1"],
        "expected_context_revision": 0,
        "expected_active_revision": None if active is None else active["active_revision"],
        "expected_availability_revision": host(p).availability_revision,
    }


def call(
    p: DaemonProcess,
    args: Any,
    rid: str = "publish",
    name: str = "publish_app_candidate",
    caps: Any = None,
    principal: Any = PrincipalClass.OPERATOR,
) -> Any:
    return p.app_publication_request(
        name,
        args,
        operator_principal=principal,
        capabilities=dict.fromkeys(PUBLICATION_CAPABILITIES, True) if caps is None else caps,
        producer_id="ma04",
        request_id=rid,
    )


def setup(p: DaemonProcess) -> tuple[Any, Any, Any]:
    body, _ = example(p)
    first = version(p, body, "first")
    proof = validate(p, first, body["catalog_fp1"])
    return body, first, proof


def view(p: DaemonProcess, active: Any) -> Any:
    result = p.get_pack_ui_request(
        {
            "instance_id": active["instance_id"],
            "availability_revision": active["availability_revision"],
        },
        operator_principal=PrincipalClass.OPERATOR,
        capabilities={"get_pack_ui_request": True},
    )
    return need(result).to_payload()


def publications(p: DaemonProcess) -> list[Any]:
    return [e for e in need(p.journal.read_events()) if e.event == PUBLISHED_EVENT]


def test_create_publish_replace_undo_and_restart(owner: DaemonProcess, tmp_path: Path) -> None:
    p = owner
    body, first, proof = setup(p)
    args = params(p, first, proof)
    a = need(call(p, args))
    assert a["publication_generation"] == 1 and a["action"] == "publish"
    assert view(p, a)["pack_ui_request"] == a["pack_ui_request"]
    assert len(a["pack_ui_request"]["views"]) == 2
    assert need(call(p, args)) == a
    body["panels"][0]["elements"]["text"]["props"]["text"] = "Maintenance"
    second = version(p, body, "second", first)
    secondproof = validate(p, second, body["catalog_fp1"])
    assert view(p, a)["pack_ui_request"] == a["pack_ui_request"]
    b = need(call(p, params(p, second, secondproof, a), "replace"))
    assert (
        b["publication_generation"] == 2
        and b["action"] == "replace"
        and b["previous_active_revision"] == a["active_revision"]
    )
    assert b["pack_ui_request"] != a["pack_ui_request"]
    assert is_refusal(
        p.get_pack_ui_request(
            {"instance_id": a["instance_id"], "availability_revision": a["availability_revision"]},
            operator_principal=PrincipalClass.OPERATOR,
            capabilities={"get_pack_ui_request": True},
        )
    )
    undo = params(p, first, proof, b)
    undo.pop("revision")
    undo["target_publication_revision"] = a["active_revision"]
    c = need(call(p, undo, "undo", "undo_app_publication"))
    assert (
        c["publication_generation"] == 3
        and c["action"] == "undo"
        and c["pack_ui_request"] == a["pack_ui_request"]
    )
    assert c["active_revision"] not in {a["active_revision"], b["active_revision"]}
    assert need(call(p, undo, "undo", "undo_app_publication")) == c
    assert len(publications(p)) == 3
    p.sqlite.execute("DELETE FROM app_candidate_publication")
    p.sqlite.execute("DELETE FROM plugin_install_records")
    p.close()
    reopened = process(tmp_path, "ma04-restart")
    try:
        assert need(call(reopened, undo, "undo", "undo_app_publication")) == c
        assert view(reopened, c)["pack_ui_request"] == c["pack_ui_request"]
        assert host(reopened).availability_revision == c["availability_revision"]
        assert len(publications(reopened)) == 3
        assert host(reopened).grant_record_ids == ()
        rows = [
            row
            for row in reopened.roster.loader.published_contributions()
            if row.qualified_id == "dev-factory:" + c["local_id"]
        ]
        assert len(rows) == 1 and rows[0].point == "toolset"
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "mutation",
    [
        "no-proof",
        "wrong-proof-version",
        "app-use",
        "cross-scope",
        "stale-active",
        "stale-host",
        "stale-context",
        "machine",
        "invalid-composition",
        "extra-grant",
        "numeric-cap",
        "false-cap",
        "missing-cap",
        "id-conflict",
        "second-app",
    ],
)
def test_denials_preserve_last_good(owner: DaemonProcess, mutation: str) -> None:
    p = owner
    body, first, proof = setup(p)
    args = params(p, first, proof)
    a = need(call(p, args))
    body["panels"][0]["title"] = "Next"
    second = version(p, body, "second", first)
    secondproof = validate(p, second, body["catalog_fp1"])
    args = params(p, second, secondproof, a)
    principal = PrincipalClass.OPERATOR
    caps = None
    rid = "denied"
    if mutation == "no-proof":
        args["validation_fp1"] = "fp1:sha256:" + "0" * 64
    elif mutation == "wrong-proof-version":
        args["validation_fp1"] = proof["validation_fp1"]
    elif mutation == "app-use":
        args["product_session_ref"] = "psess:app"
    elif mutation == "cross-scope":
        mint(p, "psess:bound", "authoring", "pack:research-corpus")
        args["product_session_ref"] = "psess:bound"
    elif mutation == "stale-active":
        args["expected_active_revision"] = None
    elif mutation == "stale-host":
        args["expected_availability_revision"] -= 1
    elif mutation == "stale-context":
        args["expected_context_revision"] = 1
    elif mutation == "machine":
        principal = PrincipalClass.MACHINE
    elif mutation == "invalid-composition":
        body["panels"][0]["elements"]["text"]["props"]["eval"] = "no"
        third = version(p, body, "third", second)
        invalid = validate(p, third, body["catalog_fp1"])
        args = params(p, third, invalid, a)
    elif mutation == "extra-grant":
        args["grant_id"] = "forged"
    elif mutation.endswith("cap"):
        caps = (
            {}
            if mutation == "missing-cap"
            else {"publish_app_candidate": 1 if mutation == "numeric-cap" else False}
        )
    elif mutation == "id-conflict":
        rid = "publish"
    elif mutation == "second-app":
        third = version(p, body, "third")
        thirdproof = validate(p, third, body["catalog_fp1"])
        args = params(p, third, thirdproof)
    refused = call(p, args, rid, caps=caps, principal=principal)
    assert is_refusal(refused), refused
    assert view(p, a)["pack_ui_request"] == a["pack_ui_request"] and len(publications(p)) == 1


def test_app_use_read_scope_and_no_write(owner: DaemonProcess) -> None:
    _, first, proof = setup(owner)
    a = need(call(owner, params(owner, first, proof)))
    read = {"candidate_id": first["candidate_id"], "product_session_ref": "psess:app"}
    assert need(call(owner, read, name="get_app_publication"))["active"] == a
    read["product_session_ref"] = "psess:other"
    assert is_refusal(call(owner, read, name="get_app_publication"))


@pytest.mark.parametrize(
    "boundary", ["journal-before", "journal-lost-response", "projection", "roster", "runtime"]
)
@pytest.mark.parametrize("restart", [False, True])
def test_failure_barrier_and_retry(
    owner: DaemonProcess,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    restart: bool,
    tmp_path: Path,
) -> None:
    p = owner
    body, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    body["panels"][0]["title"] = "Updated"
    second = version(p, body, "second", first)
    proof2 = validate(p, second, body["catalog_fp1"])
    args = params(p, second, proof2, a)

    def failed_roster(*args: Any, **kwargs: Any) -> TypedRefusal:
        return storage_failure("injected roster write")

    def failed_runtime(*args: Any, **kwargs: Any) -> TypedRefusal:
        return storage_failure("injected runtime")

    with monkeypatch.context() as m:
        if boundary.startswith("journal"):
            original = p.journal.append_event

            def append(event: str, **kwargs: Any) -> Any:
                if event != PUBLISHED_EVENT:
                    return original(event, **kwargs)
                if boundary == "journal-lost-response":
                    need(original(event, **kwargs))
                return storage_failure("injected journal boundary")

            m.setattr(p.journal, "append_event", append)
        elif boundary == "projection":

            def fail(*args: Any, **kwargs: Any) -> None:
                raise sqlite3.OperationalError("injected projection")

            m.setattr(p.app_publication, "_insert", fail)
        elif boundary == "roster":
            m.setattr(
                p.app_publication.roster,
                "publish",
                failed_roster,
            )
        else:
            m.setattr(
                p.roster.loader,
                "apply_hosted_data_publication",
                failed_runtime,
            )
        refusal = call(p, args, "boundary")
        assert is_refusal(refusal)
        assert host(p).availability_revision == a["availability_revision"]
        if boundary not in {"journal-before", "journal-lost-response"}:
            assert refusal.context["operation_committed"] is True
    if restart:
        p.close()
        p = process(tmp_path, "boundary-reopen")
    accepted = need(call(p, args, "boundary"))
    assert accepted["publication_generation"] == 2
    assert need(call(p, args, "boundary")) == accepted and len(publications(p)) == 2
    assert view(p, accepted)["pack_ui_request"] == accepted["pack_ui_request"]
    if restart:
        p.close()


def test_competing_active_revision_cas(owner: DaemonProcess) -> None:
    _, first, proof = setup(owner)
    args = params(owner, first, proof)
    with ThreadPoolExecutor(max_workers=2) as pool:

        def publish(rid: str) -> Any:
            return call(owner, args, rid)

        results = list(pool.map(publish, ["one", "two"]))
    assert sum(is_ok(r) for r in results) == 1 and len(publications(owner)) == 1
    refusal = next(r for r in results if is_refusal(r))
    assert refusal.context["refusal"] == "stale_revision"


@pytest.mark.parametrize("change", ["catalog", "dependency", "source", "proof-projection"])
def test_currentness_is_rechecked_at_apply(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, change: str
) -> None:
    p = owner
    _, first, proof = setup(p)
    args = params(p, first, proof)
    if change == "catalog":
        limits = {**LIMITS, "max_elements": 79}
        (tmp_path / "operator-config.json").write_text(
            json.dumps({"miniapp_validation_limits": limits})
        )
    elif change == "dependency":
        p.roster.loader.unload("analysis-backtest")
    elif change == "source":
        original = p.artifacts.get
        ref = proof["result"]["composition_ref"]["fp1"]

        def missing(fp: str) -> StagedArtifact | None:
            return None if fp == ref else original(fp)

        monkeypatch.setattr(p.artifacts, "get", missing)
    else:
        body = json.loads(
            cast(str, p.sqlite.execute("SELECT payload FROM app_candidate_validation")[0][0])
        )
        body["view_requests"] = []
        p.sqlite.execute("UPDATE app_candidate_validation SET payload=?", (json.dumps(body),))
    applied = call(p, args)
    if change == "proof-projection":
        assert is_ok(applied) and len(publications(p)) == 1
    else:
        assert is_refusal(applied) and publications(p) == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("candidate_id", 1),
        ("revision", "forged"),
        ("publication_generation", True),
        ("context_revision", None),
        (
            "intent",
            {"method": ["publish_app_candidate"], "params": {}, "owner_principal": "operator"},
        ),
        ("pack_ui_request", {"views": []}),
        ("unexpected", "field"),
    ],
)
def test_rehashed_malformed_envelope_refuses_before_projection_rebuild(
    owner: DaemonProcess,
    field: str,
    value: Any,
) -> None:
    p = owner
    _, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    body = {k: v for k, v in a.items() if k not in {"active_revision", "receipt_fp1"}}
    body[field] = value
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    artifact = need(p.artifacts.stage_complete_bytes(encoded))
    need(
        p.journal.append_event(
            PUBLISHED_EVENT,
            payload={
                "schema": "qma.miniapp.publication.v1",
                "active_revision": artifact.fp1,
                "byte_count": len(encoded),
                "candidate_id": body["candidate_id"],
                "installation": publications(p)[-1].payload["installation"],
            },
        )
    )
    before = p.sqlite.execute("SELECT payload FROM app_candidate_publication")
    refused = p.app_publication.restore_from_journal()
    assert (
        is_refusal(refused)
        and p.sqlite.execute("SELECT payload FROM app_candidate_publication") == before
    )


def test_current_trusted_host_permission_refuses(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qma.wire.app_candidate import policy_rejection

    _, first, proof = setup(owner)

    def revoke(manifest: Any) -> TypedRefusal:
        return policy_rejection("permissions", "revoked")

    monkeypatch.setattr(owner.roster.loader, "_check_permissions", revoke)
    assert is_refusal(call(owner, params(owner, first, proof))) and publications(owner) == []


def test_runtime_staging_failure_keeps_context_and_retry_has_bounded_cleanup(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    body, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    snap = host(p).context.snapshot()
    body["panels"][0]["title"] = "New"
    second = version(p, body, "new", first)
    proof2 = validate(p, second, body["catalog_fp1"])
    args = params(p, second, proof2, a)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("injected staging")

    with monkeypatch.context() as m:
        m.setattr(p.roster.loader, "_stage_published", fail)
        assert is_refusal(call(p, args, "stage-failure"))
    assert host(p).context.snapshot() == snap
    b = need(call(p, args, "stage-failure"))
    assert host(p).context.snapshot()["exit_stack_depth"] == snap["exit_stack_depth"]
    assert view(p, b)["pack_ui_request"] == b["pack_ui_request"]
    p.roster.loader.unload("dev-factory")
    assert not [
        r for r in p.roster.loader.published_contributions() if r.plugin_id == "dev-factory"
    ]


def test_structured_staleness_refusal_serializes_nested_field_errors() -> None:
    from qma.daemon import process as module
    from qma.wire.app_candidate import policy_rejection

    refusal = policy_rejection(
        "validation_fp1", "stale", current_errors=[{"code": "STALE_CATALOG", "path": "catalog_fp1"}]
    )
    encoded = json.dumps(module._jsonrpc_refusal("stale", refusal))  # pyright: ignore[reportPrivateUsage]
    context = json.loads(encoded)["error"]["data"]["context"]
    assert context["current_errors"] == [{"code": "STALE_CATALOG", "path": "catalog_fp1"}]


def test_publication_keeps_existing_admitted_job_identity(
    owner: DaemonProcess, tmp_path: Path
) -> None:
    from test_epic73_cancel_wire import _persist_task  # pyright: ignore[reportPrivateUsage]

    p = owner
    actor, task = _persist_task(p, "ma04-existing-job")
    admitted = need(
        p.backtesting.jobs.submit(
            owner=actor.value,
            task_id=task,
            job_id="job:ma04-existing",
            logical_run_id="run:ma04-existing",
            attempt_id=4,
            originating_product_session_ref="psess:other",
        )
    )
    before = admitted.to_payload()
    body, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    body["panels"][0]["title"] = "Replaced"
    second = version(p, body, "job-maintenance", first)
    proof2 = validate(p, second, body["catalog_fp1"])
    b = need(call(p, params(p, second, proof2, a), "job-replace"))
    undo = params(p, first, proof, b)
    undo.pop("revision")
    undo["target_publication_revision"] = a["active_revision"]
    need(call(p, undo, "job-undo", "undo_app_publication"))
    current = p.backtesting.jobs.handle_for(admitted.job_id)
    assert current is not None and current.to_payload() == before
    p.close()
    reopened = process(tmp_path, "existing-job-reopen")
    try:
        current = reopened.backtesting.jobs.handle_for(admitted.job_id)
        assert current is not None
        # Existing restart policy owns state; publication never rewrites job lineage.
        for key in (
            "job_id",
            "task_id",
            "owner",
            "logical_run_id",
            "attempt_id",
            "originating_product_session_ref",
        ):
            assert current.to_payload().get(key) == before.get(key)
    finally:
        reopened.close()


def test_changed_host_package_version_cannot_create_incompatible_receipt(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    body, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    body["panels"][0]["title"] = "Maintenance"
    second = version(p, body, "new-host-candidate", first)
    proof2 = validate(p, second, body["catalog_fp1"])
    args = params(p, second, proof2, a)
    monkeypatch.setattr(host(p), "manifest", replace(host(p).manifest, version="0.2.0"))
    denied = call(p, args, "changed-host-version")
    assert is_refusal(denied) and denied.context["refusal"] == "incompatible_host"
    assert len(publications(p)) == 1


@pytest.mark.parametrize("fault", ["delete", "payload", "identity"])
def test_live_projection_divergence_repairs_identical_receipt(
    owner: DaemonProcess, fault: str
) -> None:
    p = owner
    _, first, proof = setup(p)
    args = params(p, first, proof)
    a = need(call(p, args))
    depth = host(p).context.snapshot()["exit_stack_depth"]
    if fault == "delete":
        p.sqlite.execute("DELETE FROM app_candidate_publication")
    elif fault == "payload":
        p.sqlite.execute("UPDATE app_candidate_publication SET payload='{}'")
    else:
        p.sqlite.execute("UPDATE app_candidate_publication SET operation_key='wrong'")
    assert need(call(p, args)) == a
    read = need(
        call(
            p,
            {"product_session_ref": "psess:app", "candidate_id": first["candidate_id"]},
            name="get_app_publication",
        )
    )
    assert read["active"] == a
    assert view(p, a)["pack_ui_request"] == a["pack_ui_request"]
    assert len(publications(p)) == 1 and host(p).availability_revision == a["availability_revision"]
    assert host(p).context.snapshot()["exit_stack_depth"] == depth
    stale = {**args, "expected_availability_revision": host(p).availability_revision}
    assert is_refusal(call(p, stale, "new-null-cas")) and len(publications(p)) == 1


@pytest.mark.parametrize("fault", ["action", "generation", "intent"])
def test_live_rehashed_history_refuses_reads_retries_and_new_work(
    owner: DaemonProcess, fault: str
) -> None:
    p = owner
    _, first, proof = setup(p)
    args = params(p, first, proof)
    a = need(call(p, args))
    body = {k: v for k, v in a.items() if k not in {"active_revision", "receipt_fp1"}}
    if fault == "action":
        body["action"] = "undo"
    elif fault == "generation":
        body["publication_generation"] = 8
    else:
        body["request_fp1"] = "fp1:sha256:" + "0" * 64
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    artifact = need(p.artifacts.stage_complete_bytes(raw))
    need(
        p.journal.append_event(
            PUBLISHED_EVENT,
            payload={
                "schema": "qma.miniapp.publication.v1",
                "active_revision": artifact.fp1,
                "byte_count": len(raw),
                "candidate_id": a["candidate_id"],
                "installation": publications(p)[-1].payload["installation"],
            },
        )
    )  # pyright: ignore[reportPrivateUsage]
    events = [e.to_row() for e in need(p.journal.read_events())]
    projection = p.sqlite.execute("SELECT * FROM app_candidate_publication")
    installed = p.sqlite.execute("SELECT * FROM plugin_install_records")
    for result in (
        call(p, args),
        call(p, params(p, first, proof, a), "new-after-corruption"),
        call(
            p,
            {"product_session_ref": "psess:author", "candidate_id": first["candidate_id"]},
            name="get_app_publication",
        ),
    ):
        assert is_refusal(result)
    assert [e.to_row() for e in need(p.journal.read_events())] == events
    assert p.sqlite.execute("SELECT * FROM app_candidate_publication") == projection
    assert p.sqlite.execute("SELECT * FROM plugin_install_records") == installed
    assert (
        need(
            p.app_publication.candidates.read_reference(
                {"fp1": artifact.fp1, "byte_count": len(raw)}
            )
        )
        == raw
    )
    assert host(p).availability_revision == a["availability_revision"]


@pytest.mark.parametrize("operation", ["disable", "unload", "detach"])
def test_dependency_owner_cannot_cross_proof_append_activation(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    p = owner
    _, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    args = params(p, first, proof, a)
    staged, resume, attempted, departed = (threading.Event() for _ in range(4))
    original = p.artifacts.stage_complete_bytes
    activation_dependencies: list[bool] = []
    apply = p.roster.loader.apply_hosted_data_publication

    def pause(raw: bytes) -> Any:
        if json.loads(raw).get("schema") == "qma.miniapp.publication.v1":
            staged.set()
            assert resume.wait(15)
        return original(raw)

    def observe(payload: Any) -> Any:
        activation_dependencies.append(p.roster.loader.get("analysis-backtest") is not None)
        return apply(payload)

    def change() -> Any:
        attempted.set()
        if operation == "disable":
            answer = p.roster.loader.disable("analysis-backtest", principal=PrincipalClass.OPERATOR)
            assert is_ok(answer)
        elif operation == "unload":
            answer = p.roster.loader.unload("analysis-backtest")
        else:
            answer = p.roster.loader.detach_keep_bytes("analysis-backtest")
        departed.set()
        return answer

    monkeypatch.setattr(p.artifacts, "stage_complete_bytes", pause)
    monkeypatch.setattr(p.roster.loader, "apply_hosted_data_publication", observe)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            publication = pool.submit(call, p, args, "atomic-replacement")
            assert staged.wait(15)
            dependency = pool.submit(change)
            assert attempted.wait(15)
            blocked = not departed.wait(0.25)
            resume.set()
            b = need(publication.result(timeout=20))
            dependency.result(timeout=20)
            assert blocked and activation_dependencies and all(activation_dependencies)
        assert b["publication_generation"] == 2 and len(publications(p)) == 2
        assert p.roster.loader.get("analysis-backtest") is None
        assert is_refusal(call(p, params(p, first, proof, b), "after-departure"))
        assert len(publications(p)) == 2
    finally:
        resume.set()


def test_permission_revocation_at_staging_refuses_before_acceptance(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    _, first, proof = setup(p)
    original = p.artifacts.stage_complete_bytes
    from qma.wire.app_candidate import policy_rejection

    def revoked(manifest: Any) -> Any:
        return policy_rejection("permissions", "revoked at staging")

    def change(raw: bytes) -> Any:
        answer = original(raw)
        if json.loads(raw).get("schema") == "qma.miniapp.publication.v1":
            monkeypatch.setattr(p.roster.loader, "_check_permissions", revoked)
        return answer

    monkeypatch.setattr(p.artifacts, "stage_complete_bytes", change)
    assert is_refusal(call(p, params(p, first, proof)))
    assert publications(p) == []


def test_live_projection_repair_failure_preserves_receipt_for_retry(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    _, first, proof = setup(p)
    args = params(p, first, proof)
    a = need(call(p, args))
    p.sqlite.execute("DELETE FROM app_candidate_publication")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise sqlite3.OperationalError("interrupted live repair")

    with monkeypatch.context() as m:
        m.setattr(p.app_publication, "_insert", fail)
        refusal = call(p, args)
        assert is_refusal(refusal) and refusal.context["reconciliation_required"] is True
        assert refusal.context["retry_same_id"] is True
    assert need(call(p, args)) == a and len(publications(p)) == 1


def test_reentrant_corrupt_history_at_staging_refuses_before_append(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    _, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    malformed = {k: v for k, v in a.items() if k not in {"active_revision", "receipt_fp1"}}
    malformed["action"] = "undo"
    bad_raw = json.dumps(
        malformed, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    bad = need(p.artifacts.stage_complete_bytes(bad_raw))
    original = p.artifacts.stage_complete_bytes
    injected = False

    def change(raw: bytes) -> Any:
        nonlocal injected
        result = original(raw)
        if not injected and json.loads(raw).get("schema") == "qma.miniapp.publication.v1":
            injected = True
            need(
                p.journal.append_event(
                    PUBLISHED_EVENT,
                    payload={
                        "schema": "qma.miniapp.publication.v1",
                        "active_revision": bad.fp1,
                        "byte_count": len(bad_raw),
                        "candidate_id": a["candidate_id"],
                        "installation": publications(p)[-1].payload["installation"],
                    },
                )
            )  # pyright: ignore[reportPrivateUsage]
        return result

    monkeypatch.setattr(p.artifacts, "stage_complete_bytes", change)
    result = call(p, params(p, first, proof, a), "after-staging-corruption")
    assert is_refusal(result) and len(publications(p)) == 2
    assert host(p).availability_revision == a["availability_revision"]
    assert (
        need(
            p.app_publication.candidates.read_reference(
                {"fp1": bad.fp1, "byte_count": len(bad_raw)}
            )
        )
        == bad_raw
    )


def test_concurrent_history_append_is_ordered_after_publication(
    owner: DaemonProcess, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = owner
    _, first, proof = setup(p)
    a = need(call(p, params(p, first, proof)))
    args = params(p, first, proof, a)
    malformed = {k: v for k, v in a.items() if k not in {"active_revision", "receipt_fp1"}}
    malformed["action"] = "undo"
    raw = json.dumps(malformed, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    bad = need(p.artifacts.stage_complete_bytes(raw))
    payload = {
        "schema": "qma.miniapp.publication.v1",
        "active_revision": bad.fp1,
        "byte_count": len(raw),
        "candidate_id": a["candidate_id"],
        "installation": publications(p)[-1].payload["installation"],
    }  # pyright: ignore[reportPrivateUsage]
    staged, resume, attempted, appended = (threading.Event() for _ in range(4))
    original = p.artifacts.stage_complete_bytes

    def pause(encoded: bytes) -> Any:
        if json.loads(encoded).get("schema") == "qma.miniapp.publication.v1":
            staged.set()
            assert resume.wait(15)
        return original(encoded)

    def corrupt() -> Any:
        attempted.set()
        answer = need(p.journal.append_event(PUBLISHED_EVENT, payload=payload))
        appended.set()
        return answer

    monkeypatch.setattr(p.artifacts, "stage_complete_bytes", pause)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            publication = pool.submit(call, p, args, "journal-atomic")
            assert staged.wait(15)
            injected = pool.submit(corrupt)
            assert attempted.wait(15)
            blocked = not appended.wait(0.25)
            resume.set()
            b = need(publication.result(timeout=20))
            injected.result(timeout=20)
            assert blocked
        assert [e.payload["active_revision"] for e in publications(p)] == [
            a["active_revision"],
            b["active_revision"],
            bad.fp1,
        ]
        assert is_refusal(call(p, params(p, first, proof, b), "after-concurrent-corruption"))
        assert len(publications(p)) == 3
    finally:
        resume.set()
