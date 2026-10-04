"""Offline admitted recall through real plugin startup and authenticated requests."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from qma.core.plugins.context import Disposer
from qma.core.ports.memory import MemoryCandidate, MemoryProvider, parse_memory_candidate
from qma.daemon.plugins.context import DaemonPluginContext
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.contracts import RequestSpec
from qma.daemon.request_runtime.durable_memory import DurableMemory
from qma.daemon.request_runtime.memory_projection import (
    ProviderMemoryProjection,
)
from qma.daemon.request_runtime.providers import ProviderError
from qmf.core import Ok, Result, is_refusal
from test_actor_workflow import accepted, final, setup, wait_status
from test_durable_memory import Bound, candidate
from test_durable_memory import bound as bound_fixture
from test_plugin_loader import _MemoryStub  # pyright: ignore[reportPrivateUsage]
from test_request_runtime_daemon import compose, connection, mint, value

bound = bound_fixture


class FakeMemory(_MemoryStub):
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []
        self.candidates: tuple[MemoryCandidate, ...] = ()
        self.after: Callable[[], None] = lambda: None

    def recall(self, scope: str, token_budget: int) -> Result[tuple[MemoryCandidate, ...]]:
        self.calls.append((scope, token_budget))
        self.after()
        return Ok(self.candidates)

    def admit(self, candidate: MemoryCandidate) -> Result[MemoryCandidate]:
        raise AssertionError("projection must not mirror journal writes")


def selection(root: Path, revision: int = 1) -> None:
    (root / "memory-providers.json").write_text(
        json.dumps(
            {
                "version": 1,
                "desks": {
                    "research": {
                        "plugin_id": "research-corpus",
                        "plugin_version": "0.1.0",
                        "config_revision": revision,
                        "admission": "journal_projection_v1",
                        "policy": {"recall": True, "injection": True},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def install_fake(monkeypatch: pytest.MonkeyPatch, fake: FakeMemory) -> None:
    original = DaemonPluginContext.register_memory_provider

    def register(self: DaemonPluginContext, desk: str, provider: MemoryProvider) -> Disposer:
        return original(self, desk, fake if desk == "research" else provider)

    monkeypatch.setattr(DaemonPluginContext, "register_memory_provider", register)


def pending_spec(process: DaemonProcess, key: str = "pending") -> RequestSpec:
    assert process.agent_requests is not None
    policy = process.agent_requests.policies["global"]
    return RequestSpec(
        key,
        "operator",
        "psess:agent",
        0,
        policy.profile,
        "pending",
        policy.provider_id,
        model=policy.model,
        timeout_seconds=policy.timeout_seconds,
        authoring_task_id=policy.authoring_task_id,
    )


def retained(process: DaemonProcess) -> tuple[MemoryCandidate, ...]:
    events = value(process.journal.read_events())
    result: dict[str, MemoryCandidate] = {}
    for event in events:
        if event.event == "agent_graph.record" and event.payload.get("kind") == "typed_memory":
            for payload in json.loads(str(event.payload["body"]))["revisions"]:
                c = value(parse_memory_candidate(payload))
                result[c.id] = c
    return tuple(result.values())


def test_startup_selected_provider_recall_then_restart_continuity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(
        tmp_path,
        monkeypatch,
        [
            final("first-analysis"),
            final("first-review"),
            final("second-analysis"),
            final("second-review"),
        ],
    )
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    process = compose(tmp_path, boot="provider-one")
    try:
        mint(process)
        first = accepted(process, connection(process))
        wait_status(process, connection(process), first, "completed")
        assert len(fake.calls) == 2, "configured CT43 singleton never reached runtime"
        fake.candidates = retained(process)
        assert len(fake.candidates) == 2
    finally:
        process.close()
    process = compose(tmp_path, boot="provider-two")
    try:
        second = accepted(process, connection(process), "second")
        wait_status(process, connection(process), second, "completed")
        assert len(fake.calls) == 4
        assert all(scope.startswith("actor-memory:") for scope, _ in fake.calls)
        assert fake.calls[:2] == fake.calls[2:]
        for request in scripted.requests[2:]:
            prompt = json.loads(json.loads(request.prompt)["user_request"])
            assert "first-" in prompt["actor_memory"]
    finally:
        process.close()


def project(
    bound: Bound, fake: FakeMemory, request: str = "req:projection"
) -> ProviderMemoryProjection:
    return ProviderMemoryProjection(
        bound[1], fake, lambda: None, binding="host-pin", request_id=request
    )


def test_provider_output_cannot_override_journal_heads_or_scope(bound: Bound) -> None:
    memory, journal, host, _ = bound
    stale = memory.admit(candidate("stale"))
    retired = memory.admit(candidate("retired"))
    expired = memory.admit(candidate("expired", content={"expires_at_ns": 150}))
    memory.admit(candidate("successor", supersession=stale.id))
    value(journal.invalidate(retired.id))
    explicit = memory.admit(candidate("explicit"))
    value(journal.expire(explicit.id))
    active = memory.admit(candidate("active"))
    fake = FakeMemory()
    fake.candidates = (
        stale,
        retired,
        expired,
        explicit,
        replace(active, scope="foreign"),
        replace(active, content={"memory_type": "semantic", "text": "forged"}),
        active,
        active,
    )
    host.now = 150
    projection = project(bound, fake)
    before = len(value(bound[3].read_events()))
    assert value(projection.search()) == (active,)
    # One intent and one observed receipt, no memory mutations or provider writes.
    events = value(bound[3].read_events())[before:]
    assert len(events) == 2
    bodies = [json.loads(str(e.payload["body"])) for e in events]
    assert bodies[1]["selection"][0]["id"] == active.id
    assert all("forged" not in json.dumps(body) for body in bodies)
    value(journal.invalidate(active.id))
    assert value(projection.search()) == ()
    assert len(fake.calls) == 1, "observed receipt must not redispatch provider recall"


def test_provider_retirement_and_revocation_during_callback_withhold_content(bound: Bound) -> None:
    memory, journal, host, _ = bound
    active = memory.admit(candidate())
    fake = FakeMemory()
    fake.candidates = (active,)

    def retire() -> None:
        value(journal.invalidate(active.id))

    fake.after = retire
    assert value(project(bound, fake).search()) == ()
    fake.after = lambda: setattr(host, "active", False)
    with pytest.raises(ProviderError, match="revoked"):
        project(bound, fake, "req:revoked").search()
    host.active = True
    with pytest.raises(ProviderError, match="reconciliation"):
        project(bound, fake, "req:revoked").search()
    assert len(fake.calls) == 2


def test_tokenization_rechecks_retirement_and_never_reveals_selected_content(bound: Bound) -> None:
    memory, journal, _, _ = bound
    active = memory.admit(candidate())
    fake = FakeMemory()
    fake.candidates = (active,)
    facade = DurableMemory(journal, projection=project(bound, fake))

    def count(_text: str) -> int:
        value(journal.invalidate(active.id))
        return 1

    with pytest.raises(ProviderError, match="changed during context"):
        facade.context(max_bytes=8192, max_tokens=8192, count_tokens=count)


@pytest.mark.parametrize("change", ["missing_plugin", "version", "sync", "admission", "revision"])
def test_invalid_or_unavailable_selection_refuses_startup_without_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    setup(tmp_path, monkeypatch, [])
    selection(tmp_path)
    path = tmp_path / "memory-providers.json"
    body = json.loads(path.read_text())
    config = body["desks"]["research"]
    if change == "missing_plugin":
        config["plugin_id"] = "research-unavailable"
    elif change == "version":
        config["plugin_version"] = "9.0.0"
    elif change == "sync":
        config["policy"]["sync"] = True
    elif change == "admission":
        config["admission"] = "automatic"
    else:
        config["config_revision"] = True
    path.write_text(json.dumps(body))
    from qma.daemon.plugins import research_corpus_plugin_load_config

    seed = tmp_path / "seed-corpus"
    seed.mkdir()
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="invalid",
        plugin_load_configs=research_corpus_plugin_load_config(seed),
    )
    assert is_refusal(result)
    assert result.context["field"] == "memory_providers"


def test_duplicate_registration_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = DaemonPluginContext("research-fake")
    ctx.register_memory_provider("research", FakeMemory())
    from qma.daemon.plugins.context import PluginContextError

    with pytest.raises(PluginContextError, match="duplicate singleton"):
        ctx.register_memory_provider("research", FakeMemory())
    ctx.dispose_all()


@pytest.mark.parametrize("change", ["revision", "load_config", "removed"])
def test_accepted_binding_pin_survives_restart_and_refuses_changed_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    setup(tmp_path, monkeypatch, [])
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    process = compose(tmp_path, boot="pin-one")
    try:
        mint(process)
        assert process.agent_requests is not None
        runtime = process.agent_requests.runtime
        spec = pending_spec(process)
        row = value(runtime.submit(spec))
        pin = row.spec.memory_binding_sha256
        assert isinstance(pin, str) and len(pin) == 64
    finally:
        process.close()
    if change == "revision":
        selection(tmp_path, 2)
    elif change == "removed":
        (tmp_path / "memory-providers.json").unlink()
    else:
        # Same selected revision, changed actual operator load config bytes.
        original = DaemonPluginContext.__init__

        def changed(self: DaemonPluginContext, plugin_id: str, **kwargs: Any) -> None:
            if plugin_id == "research-corpus":
                kwargs["load_config"] = dict(kwargs.get("load_config") or {}) | {
                    "new_parameter": True
                }
            original(self, plugin_id, **kwargs)

        monkeypatch.setattr(DaemonPluginContext, "__init__", changed)
    process = compose(tmp_path, boot="pin-two")
    try:
        assert process.agent_requests is not None
        runtime = process.agent_requests.runtime
        assert value(runtime.get(row.request_id)).spec.memory_binding_sha256 == pin
        # Startup recovery validates queued work before scheduling it. The existing
        # bridge records a failed/context_changed row before direct execute runs.
        assert is_refusal(runtime.validate_request_context(row.request_id))
        result = value(runtime.execute(row.request_id))
        assert result.status == "failed" and result.error == "context_changed"
        assert len(fake.calls) == 0
    finally:
        process.close()


def test_plugin_unload_refuses_accepted_work_and_never_calls_disposed_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup(tmp_path, monkeypatch, [])
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    process = compose(tmp_path)
    try:
        mint(process)
        assert process.agent_requests is not None
        runtime = process.agent_requests.runtime
        row = value(runtime.submit(pending_spec(process)))
        process.roster.loader.unload("research-corpus")
        assert is_refusal(runtime.execute(row.request_id))
        assert fake.calls == []
        assert value(runtime.cancel(row.request_id)).status == "cancelled"
    finally:
        process.close()


@pytest.mark.parametrize("bad", ["records", "bytes", "json"])
def test_malformed_provider_output_refuses_without_fallback(bound: Bound, bad: str) -> None:
    memory = bound[0]
    active = memory.admit(candidate())
    fake = FakeMemory()
    fake.candidates = (
        (active,) * 65
        if bad == "records"
        else (replace(active, content={"memory_type": "semantic", "text": "X" * 65536}),)
        if bad == "bytes"
        else (replace(active, content={"memory_type": "semantic", "text": float("nan")}),)
    )
    with pytest.raises(ProviderError, match=r"cap|bytes"):
        project(bound, fake).search()
    assert len(fake.calls) == 1


def test_same_binding_queued_recovery_recalls_provider_after_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripted = setup(tmp_path, monkeypatch, [final("pending-analysis"), final("pending-review")])
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    process = compose(tmp_path, boot="pending-one")
    try:
        mint(process)
        bridge = process.agent_requests
        assert bridge is not None
        row = value(bridge.runtime.submit(pending_spec(process, "pending-same")))
        pin = row.spec.memory_binding_sha256
    finally:
        process.close()
    process = compose(tmp_path, boot="pending-two")
    try:
        wait_status(process, connection(process), row.request_id, "completed")
        assert process.agent_requests is not None
        assert (
            value(process.agent_requests.runtime.get(row.request_id)).spec.memory_binding_sha256
            == pin
        )
        assert len(fake.calls) == 2
        assert len(scripted.requests) == 2
    finally:
        process.close()


@pytest.mark.parametrize("mutation", ["credential_ref", "nonfinite_config"])
def test_live_configuration_mutation_refuses_accepted_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    setup(tmp_path, monkeypatch, [])
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)
    original = DaemonPluginContext.register_memory_provider

    def register(self: DaemonPluginContext, desk: str, provider: MemoryProvider) -> Disposer:
        if desk == "research":
            self.declare_credential_ref("memory", "credential:offline-account-one")
        return original(self, desk, provider)

    monkeypatch.setattr(DaemonPluginContext, "register_memory_provider", register)
    process = compose(tmp_path)
    try:
        mint(process)
        assert process.agent_requests is not None
        runtime = process.agent_requests.runtime
        row = value(runtime.submit(pending_spec(process)))
        plugin = process.roster.loader.get("research-corpus")
        assert plugin is not None
        if mutation == "credential_ref":
            plugin.context.declare_credential_ref("memory", "credential:offline-account-two")
        else:
            # Plugin config is top-level read-only; a supplied nested value need
            # not be. This fixture changes the private value to exercise denial.
            monkeypatch.setattr(plugin.context, "_load_config", {"bad": float("nan")})
        result = runtime.execute(row.request_id)
        assert is_refusal(result) and result.context["field"] == "memory_provider"
        assert fake.calls == []
        assert value(runtime.cancel(row.request_id)).status == "cancelled"
    finally:
        process.close()


@pytest.mark.parametrize("observed", [False, True])
def test_disk_reopen_receipt_never_silently_redispatches(tmp_path: Path, observed: bool) -> None:
    from qma.daemon.request_runtime.durable_memory import JournalMemoryProvider
    from qma.daemon.request_runtime.graph_storage import JournalRecords
    from test_durable_memory import SCOPE, SOURCE, Host, open_journal

    fake = FakeMemory()
    substrate, journal = open_journal(tmp_path)
    host = Host()
    canonical = JournalMemoryProvider(
        JournalRecords(journal), SCOPE.namespace, SOURCE, host.validate, now_ns=lambda: host.now
    )
    active = DurableMemory(canonical).admit(candidate())
    fake.candidates = (active,)
    projection = ProviderMemoryProjection(
        canonical, fake, lambda: None, binding="same-pin", request_id="same-request"
    )
    if observed:
        assert value(projection.search()) == (active,)
    else:

        def lose() -> None:
            raise ProviderError("outcome_unknown", "lost fixture callback")

        fake.after = lose
        with pytest.raises(ProviderError, match="lost fixture"):
            projection.search()
    journal.close()
    substrate.close()
    substrate, journal = open_journal(tmp_path)
    try:
        canonical = JournalMemoryProvider(
            JournalRecords(journal), SCOPE.namespace, SOURCE, host.validate, now_ns=lambda: host.now
        )
        projection = ProviderMemoryProjection(
            canonical, fake, lambda: None, binding="same-pin", request_id="same-request"
        )
        if observed:
            assert value(projection.search()) == (active,)
            value(canonical.invalidate(active.id))
            assert value(projection.search()) == ()
        else:
            with pytest.raises(ProviderError, match="reconciliation"):
                projection.search()
        assert len(fake.calls) == 1
    finally:
        journal.close()
        substrate.close()


def test_selected_projection_through_paired_research_request_and_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import asyncio

    from qma.wire.initialize import WIRE_PROTOCOL_VERSION
    from test_agent_extensions_daemon import offline
    from test_request_runtime_configured_daemon import (
        app_session,
        compose_configured,
        discover,
        sdk_config,
        wait_result,
    )
    from test_request_runtime_daemon import receipt, rpc, ws_connect
    from test_request_runtime_tool_loop import ScriptedText

    instance, contribution, snapshot = discover(tmp_path)
    config = sdk_config("http://127.0.0.1:9876/v1/chat/completions", instance, snapshot)
    config["research_workflow"] = {
        "specialist_id": "selected-memory-analyst",
        "version": "1",
        "instructions": "Synthetic evidence only.",
        "profiles": ["app-reader"],
    }
    scripted = ScriptedText([final("first research summary"), final("second research summary")])
    offline(monkeypatch, scripted)
    selection(tmp_path)
    fake = FakeMemory()
    install_fake(monkeypatch, fake)

    async def run(first: bool) -> None:
        process = compose_configured(tmp_path, config, "paired-one" if first else "paired-two")
        writer = None
        try:
            if first:
                app_session(process, instance, contribution)
            value(await process.bind())
            reader, writer, opening = await ws_connect(process)
            assert b"101 Switching Protocols" in opening
            receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {
                        "protocolVersion": WIRE_PROTOCOL_VERSION,
                        "capabilities": {},
                    },
                )
            )
            accepted = receipt(
                await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    {
                        "product_session_ref": "psess:configured-app",
                        "profile_id": "app-reader",
                        "prompt": "Analyze the pinned permitted corpus.",
                        "idempotency_key": "paired-first" if first else "paired-second",
                    },
                )
            )
            result = await wait_result(reader, writer, str(accepted["request_id"]))
            assert result["status"] == "completed", result
            fake.candidates = retained(process)
            assert len(fake.calls) == (1 if first else 2)
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(run(True))
    asyncio.run(run(False))
    assert fake.calls[0] == fake.calls[1]
    assert fake.calls[0][0].startswith("research-summary:")
    inputs = [
        json.loads(json.loads(request.prompt)["user_request"]) for request in scripted.requests
    ]
    assert inputs[0]["scoped_memory"] is None
    assert inputs[1]["scoped_memory"]["summary"] == "first research summary"
