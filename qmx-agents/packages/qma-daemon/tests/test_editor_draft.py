"""Epic 71 draft save, CAS, query, publish and invocation guards."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.artifacts.store import ArtifactStore, StagedArtifact
from qma.daemon.discovery import FederatedDiscoveryService
from qma.daemon.discovery.federated import ArtifactLibrarySearchPort
from qma.daemon.hooks.registry import HookRegistry
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.knowledge import KnowledgeService, KnowledgeSourceRegistry, PlainFileLibrarySource
from qma.daemon.persistence.substrate import PersistenceSubstrate
from qma.daemon.plugins.packs import DeskPluginRoster
from qma.daemon.process import DaemonProcess
from qma.daemon.staging.editor_draft import EditorDraftHead, EditorDraftService
from qma.wire.auth import format_pairing_authorization
from qma.wire.initialize import (
    GET_EDITOR_DRAFT_HEAD_CAPABILITY,
    PUBLISH_EDITOR_DRAFT_CAPABILITY,
    SAVE_EDITOR_DRAFT_CAPABILITY,
    WireConnection,
)
from qma.wire.selected_ref import parse_selected_refs
from qmf.core import DataDrivenClock, Instant, Ok, Result, is_ok, is_refusal

_CAPS = {
    SAVE_EDITOR_DRAFT_CAPABILITY: True,
    GET_EDITOR_DRAFT_HEAD_CAPABILITY: True,
    PUBLISH_EDITOR_DRAFT_CAPABILITY: True,
}
_ORIGIN = "http://127.0.0.1:5173"


class _EmptyLibrarySearch:
    def search(
        self,
        *,
        kind: str | None = None,
        fp1: str | None = None,
        query: str | None = None,
    ) -> Result[Sequence[Mapping[str, object]]]:
        _ = (kind, fp1, query)
        return Ok(())


def _clock(*, boot: str = "draft-test") -> DataDrivenClock:
    base = 1_700_000_000_000_000_000
    return DataDrivenClock(
        boot_epoch_id=boot,
        wall_instants=tuple(Instant(value_ns=base + i) for i in range(256)),
        monotonic_ns=tuple(i * 1_000 for i in range(256)),
    )


def _service(
    tmp_path: Path,
) -> tuple[PersistenceSubstrate, AuthoritativeJournal, ArtifactStore, EditorDraftService]:
    substrate_result = PersistenceSubstrate.open(
        tmp_path,
        machine="draft-test-host",
        boot_epoch_id="draft-test",
    )
    assert is_ok(substrate_result), substrate_result
    substrate = substrate_result.value
    journal_result = AuthoritativeJournal.bind(substrate, clock=_clock())
    assert is_ok(journal_result), journal_result
    journal = journal_result.value
    artifacts = ArtifactStore()
    service = EditorDraftService(
        journal=journal,
        sqlite=substrate.sqlite,
        artifacts=artifacts,
        authoring_roster_root=tmp_path / "authoring-pack",
    )
    assert is_ok(service.restore_from_journal())
    return substrate, journal, artifacts, service


def _stage(artifacts: ArtifactStore, body: bytes) -> str:
    staged = artifacts.stage_complete_bytes(body)
    assert is_ok(staged), staged
    return staged.value.fp1


def _close(substrate: PersistenceSubstrate, journal: AuthoritativeJournal) -> None:
    journal.close()
    substrate.close()


def test_first_save_mints_id_and_lost_ack_retry_is_idempotent(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        fp1 = _stage(artifacts, b'{"graph":1}')
        payload = {"fp1": fp1, "client_draft_correlation": "tab-save-1"}
        first = service.save_editor_draft(
            payload, operator_principal="operator-1", capabilities=_CAPS
        )
        retry = service.save_editor_draft(
            payload, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(first) and is_ok(retry)
        assert first.value.editor_draft_id.startswith("edraft:")
        assert first.value.editor_draft_id == retry.value.editor_draft_id
        assert first.value.editor_revision == fp1
        journal_events = cast(Result[tuple[object, ...]], journal.read_events())
        assert is_ok(journal_events)
        assert len(journal_events.value) == 1
    finally:
        _close(substrate, journal)


def test_first_save_rejects_incomplete_legacy_staged_artifact(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        staged = artifacts.stage_complete_bytes(b"legacy partial")
        assert is_ok(staged), staged
        artifacts._artifacts[staged.value.fp1] = StagedArtifact(  # pyright: ignore[reportPrivateUsage]
            fp1=staged.value.fp1,
            byte_count=staged.value.byte_count,
            completeness="incomplete",
            content=staged.value.content,
        )
        refused = service.save_editor_draft(
            {"fp1": staged.value.fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_refusal(refused)
        absent_head = service.get_editor_draft_head(
            {"editor_draft_id": staged.value.fp1},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_refusal(absent_head)
    finally:
        _close(substrate, journal)


def test_staged_draft_store_is_not_a_library_search_source(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        fp1 = _stage(artifacts, b"draft bytes are staging only")
        saved = service.save_editor_draft(
            {"fp1": fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(saved), saved
        # The federated facade consumes an injected Library search port. Draft
        # fp1 stays in ArtifactStore and is not adapted into an ArtifactHit row.
        assert not isinstance(artifacts, ArtifactLibrarySearchPort)
        assert not hasattr(artifacts, "search")
        assert artifacts.get(fp1) is not None
        head = service.get_editor_draft_head(
            {"editor_draft_id": saved.value.editor_draft_id},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_ok(head), head
        assert head.value.editor_revision == fp1
        corpus_root = tmp_path / "facade-library"
        corpus_root.mkdir()
        (corpus_root / "notes.md").write_text("draft remains out of Library", encoding="utf-8")
        sources = KnowledgeSourceRegistry()
        bound = sources.bind(
            "draft-test-library",
            PlainFileLibrarySource(root_path=corpus_root, source_id="draft-test-library"),
            plugin_id="draft-test-library",
        )
        assert is_ok(bound), bound
        knowledge = KnowledgeService(sources, hooks=HookRegistry())
        snapshot = knowledge.snapshot("draft-test-library")
        assert is_ok(snapshot), snapshot
        runtime = DeskPluginRoster()
        facade = FederatedDiscoveryService(
            knowledge=knowledge,
            artifacts=_EmptyLibrarySearch(),
            contributions=runtime.loader,
        )
        found = facade.search(
            "draft",
            source_id="draft-test-library",
            snapshot=snapshot.value,
        )
        assert is_ok(found), found
        hit_payloads = [json.dumps(dict(hit.to_payload())) for hit in found.value.hits]
        assert all(fp1 not in payload for payload in hit_payloads)
    finally:
        _close(substrate, journal)


def test_first_save_refuses_supplied_id_missing_bytes_and_correlation_reuse(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        fp1 = _stage(artifacts, b"one")
        supplied = service.save_editor_draft(
            {"editor_draft_id": "edraft:client", "fp1": fp1},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        missing = service.save_editor_draft(
            {"fp1": "fp1:sha256:" + "0" * 64},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        first = service.save_editor_draft(
            {"fp1": fp1, "client_draft_correlation": "correlation-1"},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        other_fp1 = _stage(artifacts, b"two")
        mismatch = service.save_editor_draft(
            {"fp1": other_fp1, "client_draft_correlation": "correlation-1"},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert (
            is_refusal(supplied) and is_refusal(missing) and is_ok(first) and is_refusal(mismatch)
        )
        assert mismatch.context.get("refusal") == "correlation_mismatch"
        journal_events = cast(Result[tuple[object, ...]], journal.read_events())
        assert is_ok(journal_events)
        assert len(journal_events.value) == 1
    finally:
        _close(substrate, journal)


def test_save_requires_owner_and_exact_cas_and_two_service_race_has_one_winner(
    tmp_path: Path,
) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        original = _stage(artifacts, b"r1")
        saved = service.save_editor_draft(
            {"fp1": original}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(saved)
        new_fp1 = _stage(artifacts, b"r2")
        unauthorized = service.save_editor_draft(
            {
                "editor_draft_id": saved.value.editor_draft_id,
                "expected_revision": original,
                "fp1": new_fp1,
            },
            operator_principal="operator-2",
            capabilities=_CAPS,
        )
        stale = service.save_editor_draft(
            {
                "editor_draft_id": saved.value.editor_draft_id,
                "expected_revision": "fp1:stale",
                "fp1": new_fp1,
            },
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_refusal(unauthorized) and is_refusal(stale)
        assert stale.context.get("refusal") == "conflict"

        second = EditorDraftService(
            journal=journal,
            sqlite=substrate.sqlite,
            artifacts=artifacts,
            authoring_roster_root=tmp_path / "authoring-pack",
        )
        fp_a, fp_b = _stage(artifacts, b"client-a"), _stage(artifacts, b"client-b")

        def write(service_to_use: EditorDraftService, fp: str) -> Result[EditorDraftHead]:
            return service_to_use.save_editor_draft(
                {
                    "editor_draft_id": saved.value.editor_draft_id,
                    "expected_revision": original,
                    "fp1": fp,
                },
                operator_principal="operator-1",
                capabilities=_CAPS,
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = (
                pool.submit(write, service, fp_a),
                pool.submit(write, second, fp_b),
            )
            outcomes = [future.result() for future in futures]
        assert sum(is_ok(item) for item in outcomes) == 1
        assert sum(is_refusal(item) for item in outcomes) == 1
        head = service.get_editor_draft_head(
            {"editor_draft_id": saved.value.editor_draft_id},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_ok(head)
        assert head.value.editor_revision in {fp_a, fp_b}
    finally:
        _close(substrate, journal)


def test_head_query_is_owned_capability_gated_and_projection_recovers(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        fp1 = _stage(artifacts, b"recover")
        saved = service.save_editor_draft(
            {"fp1": fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(saved)
        refused = service.get_editor_draft_head(
            {"editor_draft_id": saved.value.editor_draft_id},
            operator_principal="operator-2",
            capabilities=_CAPS,
        )
        mismatch = service.get_editor_draft_head(
            {"editor_draft_id": saved.value.editor_draft_id},
            operator_principal="operator-1",
            capabilities={},
        )
        assert is_refusal(refused) and is_refusal(mismatch)
        assert mismatch.context.get("query_unavailable") is True
        substrate.sqlite.execute("DELETE FROM editor_draft_head")
        restored = service.restore_from_journal()
        assert is_ok(restored) and restored.value == 1
        head = service.get_editor_draft_head(
            {"editor_draft_id": saved.value.editor_draft_id},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_ok(head) and head.value.editor_revision == fp1
    finally:
        _close(substrate, journal)


def test_publish_revalidates_and_roster_stays_unchanged_on_failure(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        invalid_fp1 = _stage(artifacts, b"not json")
        invalid_draft = service.save_editor_draft(
            {"fp1": invalid_fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(invalid_draft)
        invalid_publish = service.publish_editor_draft(
            {
                "editor_draft_id": invalid_draft.value.editor_draft_id,
                "expected_revision": invalid_fp1,
            },
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        roster = tmp_path / "authoring-pack" / "roster.json"
        assert is_refusal(invalid_publish)
        assert not roster.exists()

        body = json.dumps(
            {
                "artifact_kind": "graph_template",
                "qualified_id": "demo:authoring",
                "version": "1.0.0",
                "nodes": [],
                "edges": [],
            },
            sort_keys=True,
        ).encode()
        valid_fp1 = _stage(artifacts, body)
        valid_draft = service.save_editor_draft(
            {"fp1": valid_fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(valid_draft)
        wrong_owner = service.publish_editor_draft(
            {
                "editor_draft_id": valid_draft.value.editor_draft_id,
                "expected_revision": valid_fp1,
            },
            operator_principal="operator-2",
            capabilities=_CAPS,
        )
        stale = service.publish_editor_draft(
            {
                "editor_draft_id": valid_draft.value.editor_draft_id,
                "expected_revision": "fp1:stale",
            },
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_refusal(wrong_owner)
        assert is_refusal(stale)
        assert not roster.exists()
        published = service.publish_editor_draft(
            {
                "editor_draft_id": valid_draft.value.editor_draft_id,
                "expected_revision": valid_fp1,
            },
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_ok(published), published
        roster_data = json.loads(roster.read_text(encoding="utf-8"))
        rows = roster_data["published"]
        assert len(rows) == 1
        assert rows[0]["point"] == "graph_template"
        assert rows[0]["published"] is False
        assert "library" not in rows[0]
        assert published.value["contribution_id"] == rows[0]["contribution_id"]
        # The local authoring roster is not live until the ordinary operator
        # enable flow accepts it through PluginLoader and PluginContext.
        runtime = DeskPluginRoster(authoring_roster_root=tmp_path / "authoring-pack")
        assert runtime.templates.get("demo:authoring") is None
        enabled = runtime.enable_published_authoring_contribution(
            str(published.value["contribution_id"]),
            correlation_id="editor-draft-enable-test",
        )
        assert is_ok(enabled), enabled
        assert runtime.loader.get(enabled.value.manifest.id) is not None
        assert runtime.templates.get("demo:authoring") is not None
        enabled_roster = json.loads(roster.read_text(encoding="utf-8"))
        assert enabled_roster["published"][0]["enabled"] is True
        substrate.sqlite.execute("DELETE FROM editor_draft_head")
        restored = service.restore_from_journal()
        assert is_ok(restored), restored
        head_rows = substrate.sqlite.execute(
            "SELECT contribution_id FROM editor_draft_head WHERE editor_draft_id = ?",
            (valid_draft.value.editor_draft_id,),
        )
        assert head_rows[0][0] == published.value["contribution_id"]
        repeated = service.publish_editor_draft(
            {
                "editor_draft_id": valid_draft.value.editor_draft_id,
                "expected_revision": valid_fp1,
            },
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_ok(repeated)
        assert len(json.loads(roster.read_text(encoding="utf-8"))["published"]) == 1
    finally:
        _close(substrate, journal)


def test_publish_roster_write_failure_preserves_existing_bytes(tmp_path: Path) -> None:
    substrate, journal, artifacts, service = _service(tmp_path)
    try:
        blocked_root = tmp_path / "roster-root-is-a-file"
        blocked_root.write_bytes(b"preserve-me")
        service.authoring_roster_root = blocked_root
        body = json.dumps(
            {
                "artifact_kind": "graph_template",
                "qualified_id": "demo:blocked",
                "version": "1.0.0",
                "nodes": [],
                "edges": [],
            },
            sort_keys=True,
        ).encode()
        fp1 = _stage(artifacts, body)
        saved = service.save_editor_draft(
            {"fp1": fp1}, operator_principal="operator-1", capabilities=_CAPS
        )
        assert is_ok(saved), saved
        refused = service.publish_editor_draft(
            {"editor_draft_id": saved.value.editor_draft_id, "expected_revision": fp1},
            operator_principal="operator-1",
            capabilities=_CAPS,
        )
        assert is_refusal(refused)
        assert blocked_root.read_bytes() == b"preserve-me"
        journal_events = cast(Result[tuple[object, ...]], journal.read_events())
        assert is_ok(journal_events)
        assert [getattr(event, "event", None) for event in journal_events.value] == [
            "editor_draft.saved"
        ]
    finally:
        _close(substrate, journal)


def test_authenticated_http_editor_draft_head_query(tmp_path: Path) -> None:
    async def _run() -> None:
        seed = tmp_path / "seed-corpus"
        seed.mkdir()
        composed = DaemonProcess.compose(
            tmp_path,
            machine="draft-http-test",
            boot_epoch_id="draft-http-test",
            bind_port=0,
            plugin_load_configs={"research-corpus": {"root_path": str(seed)}},
        )
        assert is_ok(composed), composed
        process = composed.value
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            configured = process.configure_pairing_ttl("PT15M")
            assert is_ok(configured), configured
            started = await _http_exchange(
                bound.value.host,
                bound.value.port,
                "POST",
                "/pair/start",
                {"Origin": _ORIGIN, "Host": f"{bound.value.host}:{bound.value.port}"},
            )
            assert started[0] == 200, started
            pending = json.loads(started[1])
            paired = process.pair_pending(pending["pending_code"])
            assert is_ok(paired), paired
            confirmed = await _http_exchange(
                bound.value.host,
                bound.value.port,
                "POST",
                "/pair/confirm",
                {
                    "Origin": _ORIGIN,
                    "Host": f"{bound.value.host}:{bound.value.port}",
                    "Content-Type": "application/json",
                },
                json.dumps({"pending_id": pending["pairing_record_id"]}).encode(),
            )
            assert confirmed[0] == 200, confirmed
            proof = json.loads(confirmed[1])["pairing_proof"]
            auth = format_pairing_authorization(proof)
            assert is_ok(auth), auth

            staged = process.artifacts.stage_complete_bytes(b'{"graph":1}')
            assert is_ok(staged), staged
            saved = process._editor_drafts.save_editor_draft(  # pyright: ignore[reportPrivateUsage]
                {"fp1": staged.value.fp1},
                operator_principal=process._operator_principal(),  # pyright: ignore[reportPrivateUsage]
                capabilities=_CAPS,
            )
            assert is_ok(saved), saved
            response = await _http_exchange(
                bound.value.host,
                bound.value.port,
                "GET",
                f"/q/get_editor_draft_head?editor_draft_id={saved.value.editor_draft_id}",
                {"Origin": _ORIGIN, "Authorization": auth.value},
            )
            assert response[0] == 200, response
            result = json.loads(response[1])["result"]
            assert result == {
                "editor_draft_id": saved.value.editor_draft_id,
                "editor_revision": staged.value.fp1,
            }
            unauthenticated = await _http_exchange(
                bound.value.host,
                bound.value.port,
                "GET",
                f"/q/get_editor_draft_head?editor_draft_id={saved.value.editor_draft_id}",
                {"Origin": _ORIGIN},
            )
            assert unauthenticated[0] in {401, 403}
        finally:
            await process.aclose()

    asyncio.run(_run())


async def _http_exchange(
    host: str,
    port: int,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes = b"",
) -> tuple[int, bytes]:
    reader, writer = await asyncio.open_connection(host, port)
    try:
        rows = [f"{method} {path} HTTP/1.1", *(f"{key}: {value}" for key, value in headers.items())]
        if body:
            rows.append(f"Content-Length: {len(body)}")
        writer.write(("\r\n".join(rows) + "\r\n\r\n").encode("ascii") + body)
        await writer.drain()
        raw = await asyncio.wait_for(reader.read(), timeout=5)
        head, _, payload = raw.partition(b"\r\n\r\n")
        status = int(head.decode("iso-8859-1").split("\r\n", 1)[0].split(" ")[1])
        return status, payload
    finally:
        writer.close()
        await writer.wait_closed()


def test_draft_invoke_refuses_without_jobhandle() -> None:
    process = object.__new__(DaemonProcess)
    targets: tuple[Mapping[str, object], ...] = (
        {"editor_draft_id": "edraft:1"},
        {"editor_revision": "fp1:abc"},
        {"unsaved_buffer": {"nodes": []}},
    )
    for target in targets:
        response = DaemonProcess._gate_live_invoke(  # pyright: ignore[reportPrivateUsage]
            process,
            "start_mission",
            {"params": cast(Mapping[str, object], target)},
            "req-1",
        )
        assert response is not None
        response_map = cast(Mapping[str, object], response)
        error = cast(Mapping[str, object], response_map["error"])
        data = cast(Mapping[str, object], error["data"])
        context = cast(Mapping[str, object], data["context"])
        assert context["refusal"] == "draft_not_runnable"
        assert context["minted_job_handle"] is False


def test_live_json_rpc_dispatch_refuses_draft_before_job_mint() -> None:
    process = object.__new__(DaemonProcess)
    connection = WireConnection()
    connection._authenticated = True  # pyright: ignore[reportPrivateUsage]
    connection._principal_class = PrincipalClass.OPERATOR  # pyright: ignore[reportPrivateUsage]
    connection._initialized = True  # pyright: ignore[reportPrivateUsage]
    connection._producer_id = "editor-draft-test-producer"  # pyright: ignore[reportPrivateUsage]
    response = DaemonProcess._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
        process,
        connection,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "invoke-1",
                "method": "start_mission",
                "params": {"editor_draft_id": "edraft:daemon", "editor_revision": "fp1:abc"},
            }
        ).encode("utf-8"),
        session_key="pairing-test",
        connection_token="connection-test",
    )
    assert response is not None
    response_map = cast(Mapping[str, object], response)
    error = cast(Mapping[str, object], response_map["error"])
    data = cast(Mapping[str, object], error["data"])
    context = cast(Mapping[str, object], data["context"])
    assert context["refusal"] == "draft_not_runnable"
    assert context["minted_job_handle"] is False


def test_selected_refs_reject_editor_draft_ids_and_fields() -> None:
    for ref in (
        {"kind": "template", "id": "edraft:daemon-issued"},
        {"kind": "template", "id": "demo:graph", "editor_revision": "fp1:abc"},
    ):
        refused = parse_selected_refs([ref])
        assert is_refusal(refused)
