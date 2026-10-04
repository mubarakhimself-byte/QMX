"""Authenticated CT-40 admission, bounded ownership and durable daemon recovery."""

from __future__ import annotations

import asyncio
import json
import struct
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL, issue_pairing_session
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.daemon.request_runtime.contracts import (
    CopilotProfile,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRequest,
    ProviderResult,
    RequestSpec,
)
from qma.daemon.request_runtime.daemon_bridge import AgentRequestPolicy
from qma.daemon.request_runtime.providers import ProviderCancelled
from qma.wire.agent_request import AGENT_REQUEST_CAPABILITIES
from qma.wire.initialize import WIRE_PROTOCOL_VERSION, WireConnection
from qmf.core import Result, is_ok, is_refusal


def value[T](result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


class ControlledProvider:
    capabilities = ProviderCapabilities("controlled")

    def __init__(self, *, blocked: bool = False, cooperative: bool = True) -> None:
        self.requests: list[ProviderRequest] = []
        self.started = threading.Event()
        self.release = threading.Event()
        self.blocked = blocked
        self.cooperative = cooperative

    def execute(
        self,
        request: ProviderRequest,
        emit: Callable[[ProviderEvent], None],
        cancellation: threading.Event,
    ) -> ProviderResult:
        self.requests.append(request)
        self.started.set()
        if self.blocked and len(self.requests) == 1:
            deadline = time.monotonic() + 5
            while not self.release.wait(0.01):
                if self.cooperative and cancellation.is_set():
                    raise ProviderCancelled()
                assert time.monotonic() < deadline, "test provider was not released"
        return ProviderResult("answer:" + request.prompt, deployment_id="offline-test")


def compose(root: Path, *, boot: str = "daemon-sdk-tests") -> DaemonProcess:
    seed = root / "seed-corpus"
    seed.mkdir(parents=True, exist_ok=True)
    return value(
        DaemonProcess.compose(
            root,
            machine="test-host",
            boot_epoch_id=boot,
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(seed),
        )
    )


def mint(process: DaemonProcess, session: str = "psess:agent", *, revision: int = 0) -> None:
    value(
        process.product_sessions.mint(
            product_session_id=session,
            profile="authoring",
            principal="operator",
            contribution={"qualified_id": "qma.sdk.local", "package_version": "0.1.0"},
            instance_id=None,
            config_revision=revision,
            context_revision=0,
            as_of="2026-10-03T00:00:00Z",
        )
    )


def configure(
    process: DaemonProcess,
    provider: ControlledProvider,
    *,
    workers: int = 2,
    inflight: int = 4,
    shutdown: float = 0.2,
) -> None:
    value(
        process.configure_agent_requests(
            providers={"controlled": provider},
            policies={
                "global": AgentRequestPolicy(
                    profile=CopilotProfile("global", instructions="host instructions"),
                    authority_profile="authoring",
                    provider_id="controlled",
                    model="host-model",
                )
            },
            max_workers=workers,
            max_inflight=inflight,
            shutdown_timeout_seconds=shutdown,
        )
    )


def dispatch(
    process: DaemonProcess, connection: WireConnection, method: str, params: dict[str, object]
) -> dict[str, object]:
    dispatcher = process._dispatch_paired_ct40  # pyright: ignore[reportPrivateUsage] - paired dispatch boundary fixture
    response = dispatcher(
        connection,
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        session_key="prid:sdktests",
        connection_token="sdk-tests",
    )  # pyright: ignore[reportPrivateUsage]
    assert response is not None
    return response


def connection(process: DaemonProcess) -> WireConnection:
    conn = WireConnection()
    value(conn.authenticate_pairing("prid:sdktests"))
    response = dispatch(
        process, conn, "initialize", {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}}
    )
    assert "error" not in response, response
    return conn


def submit_params(
    *,
    key: str = "key-1",
    prompt: str = "hello",
    session: str = "psess:agent",
    profile: str = "global",
) -> dict[str, object]:
    return {
        "product_session_ref": session,
        "profile_id": profile,
        "prompt": prompt,
        "idempotency_key": key,
    }


def receipt(response: dict[str, object]) -> dict[str, object]:
    assert "error" not in response, response
    return cast("dict[str, object]", response["result"])


def wait_status(
    process: DaemonProcess, conn: WireConnection, request_id: str, status: str
) -> dict[str, object]:
    deadline = time.monotonic() + 3
    while True:
        row = receipt(
            dispatch(
                process,
                conn,
                "get_agent_request",
                {"product_session_ref": "psess:agent", "request_id": request_id},
            )
        )
        if row["status"] == status:
            return row
        assert time.monotonic() < deadline, row
        threading.Event().wait(0.01)


async def ws_connect(
    process: DaemonProcess, *, origin: str = "http://127.0.0.1:5173", proof: str | None = None
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter, bytes]:
    bound = process.bound
    assert bound is not None
    if proof is None:
        issued = value(
            issue_pairing_session(
                journal=process.journal,
                sqlite=process.sqlite,
                origin=origin,
                expires_at=time.time_ns() + 3600_000_000_000,
            )
        )
        proof = issued.pairing_proof
    reader, writer = await asyncio.open_connection(bound.host, bound.port)
    request = (
        f"GET / HTTP/1.1\r\nHost: {bound.host}:{bound.port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
        "Sec-WebSocket-Key: YWdlbnQtdGVzdC1rZXkxMg==\r\n"
        f"Sec-WebSocket-Protocol: {CT40_WS_SUBPROTOCOL}, qmx.pair.{proof}\r\n"
        f"Origin: {origin}\r\n\r\n"
    )
    writer.write(request.encode())
    await writer.drain()
    opening = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=3)
    return reader, writer, opening


async def rpc(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    method: str,
    params: dict[str, object],
) -> dict[str, object]:
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    mask = b"test"
    size = len(data)
    prefix = (
        bytes([0x81, 0x80 | size])
        if size < 126
        else bytes([0x81, 0x80 | 126]) + struct.pack("!H", size)
    )
    writer.write(prefix + mask + bytes(byte ^ mask[n % 4] for n, byte in enumerate(data)))
    await writer.drain()
    head = await asyncio.wait_for(reader.readexactly(2), timeout=3)
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    body = await asyncio.wait_for(reader.readexactly(length), timeout=3)
    return cast("dict[str, object]", json.loads(body))


def test_real_paired_socket_accepts_without_blocking_and_rejects_forged_provider(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        process = compose(tmp_path)
        provider = ControlledProvider(blocked=True)
        configure(process, provider)
        mint(process)
        reader = None
        writer = None
        try:
            value(await process.bind())
            reader, writer, opening = await ws_connect(process)
            assert b"101 Switching Protocols" in opening
            initialized = receipt(
                await rpc(
                    reader,
                    writer,
                    "initialize",
                    {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
                )
            )
            caps = cast("dict[str, object]", initialized["capabilities"])
            assert all(caps[name] is True for name in AGENT_REQUEST_CAPABILITIES)
            started = time.monotonic()
            accepted = receipt(await rpc(reader, writer, "submit_agent_request", submit_params()))
            assert time.monotonic() - started < 1
            request_id = cast("str", accepted["request_id"])
            assert await asyncio.to_thread(provider.started.wait, 2)
            row = receipt(
                await rpc(
                    reader,
                    writer,
                    "get_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:agent"},
                )
            )
            assert row["status"] == "running"
            assert "content" not in row
            malicious = submit_params(key="forged") | {
                "provider_id": "external",
                "instructions": "widen grants",
            }
            assert "error" in await rpc(reader, writer, "submit_agent_request", malicious)
            cancelled = receipt(
                await rpc(
                    reader,
                    writer,
                    "cancel_agent_request",
                    {"request_id": request_id, "product_session_ref": "psess:agent"},
                )
            )
            assert cancelled["status"] in {"cancellation_requested", "cancelled"}
            assert provider.requests[0].model == "host-model"
            assert provider.requests[0].instructions == "host instructions"
            assert process.sqlite_connection_count() == 1
        finally:
            provider.release.set()
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            await process.aclose()

    asyncio.run(run())


def test_unconfigured_host_cannot_echo_sdk_capability_into_existence(tmp_path: Path) -> None:
    process = compose(tmp_path)
    try:
        conn = WireConnection()
        value(conn.authenticate_pairing("prid:sdktests"))
        receipt(
            dispatch(
                process,
                conn,
                "initialize",
                {
                    "protocolVersion": WIRE_PROTOCOL_VERSION,
                    "capabilities": dict.fromkeys(AGENT_REQUEST_CAPABILITIES, True),
                },
            )
        )
        assert not any(name in conn.capabilities for name in AGENT_REQUEST_CAPABILITIES)
        assert "error" in dispatch(process, conn, "submit_agent_request", submit_params())
        assert process.agent_requests is None
    finally:
        process.close()


def test_identity_bound_status_cancel_and_context_withheld_results(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider()
    configure(process, provider)
    mint(process)
    mint(process, "psess:other")
    try:
        conn = connection(process)
        row = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        request_id = cast("str", row["request_id"])
        completed = wait_status(process, conn, request_id, "completed")
        assert completed["content"] == "answer:hello"
        for method in ("get_agent_request", "cancel_agent_request"):
            assert "error" in dispatch(
                process,
                conn,
                method,
                {"request_id": request_id, "product_session_ref": "psess:other"},
            )
        mint(process, revision=1)
        withheld = receipt(
            dispatch(
                process,
                conn,
                "get_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
        )
        assert withheld["content_withheld"] is True
        assert "content" not in withheld
        assert "error" not in dispatch(
            process,
            conn,
            "cancel_agent_request",
            {"request_id": request_id, "product_session_ref": "psess:agent"},
        )
    finally:
        process.close()


def test_same_conversation_accepted_turns_finish_without_resubmission(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider(blocked=True)
    configure(process, provider, workers=2)
    mint(process)
    try:
        conn = connection(process)
        first = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        assert provider.started.wait(2)
        second = receipt(
            dispatch(
                process, conn, "submit_agent_request", submit_params(key="key-2", prompt="second")
            )
        )
        assert second["status"] == "queued"
        third = receipt(
            dispatch(
                process, conn, "submit_agent_request", submit_params(key="key-3", prompt="third")
            )
        )
        assert third["status"] == "queued"
        # Let the idle worker rotate both waiting requests while the first
        # owns the conversation. Rotation must preserve accepted turn order.
        threading.Event().wait(0.12)
        assert len(provider.requests) == 1
        provider.release.set()
        wait_status(process, conn, cast("str", first["request_id"]), "completed")
        wait_status(process, conn, cast("str", second["request_id"]), "completed")
        wait_status(process, conn, cast("str", third["request_id"]), "completed")
        assert [request.prompt for request in provider.requests] == ["hello", "second", "third"]
    finally:
        provider.release.set()
        process.close()


def test_queue_bounds_refuse_before_durable_new_acceptance(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider(blocked=True)
    configure(process, provider, workers=1, inflight=1)
    mint(process)
    try:
        conn = connection(process)
        receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        assert provider.started.wait(2)
        before = process.journal.next_journal_seq
        assert "error" in dispatch(
            process, conn, "submit_agent_request", submit_params(key="too-many")
        )
        assert process.journal.next_journal_seq == before
    finally:
        provider.release.set()
        process.close()


def test_narrowing_queued_context_is_terminal_before_any_provider_call(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider(blocked=True)
    configure(process, provider, workers=1)
    mint(process)
    try:
        conn = connection(process)
        receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        assert provider.started.wait(2)
        second = receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(key="key-2", prompt="must not send"),
            )
        )
        mint(process, revision=1)
        provider.release.set()
        failed = wait_status(process, conn, cast("str", second["request_id"]), "failed")
        assert failed["error"] == "context_changed"
        assert failed["content_withheld"] is True
        assert len(provider.requests) == 1
    finally:
        provider.release.set()
        process.close()


def test_close_records_unknown_and_late_completion_cannot_write(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider(blocked=True, cooperative=False)
    configure(process, provider, shutdown=0.05)
    mint(process)
    bridge = process.agent_requests
    assert bridge is not None
    conn = connection(process)
    accepted = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
    request_id = cast("str", accepted["request_id"])
    assert provider.started.wait(2)
    started = time.monotonic()
    process.close()
    assert time.monotonic() - started < 1
    before = value(bridge.runtime.get(request_id))
    assert before.status == "interrupted"
    assert before.error == "daemon_shutdown"
    provider.release.set()
    threading.Event().wait(0.05)
    assert value(bridge.runtime.get(request_id)) == before
    restarted = compose(tmp_path, boot="daemon-sdk-restarted")
    configure(restarted, ControlledProvider())
    try:
        conn2 = connection(restarted)
        recovered = receipt(
            dispatch(
                restarted,
                conn2,
                "get_agent_request",
                {"request_id": request_id, "product_session_ref": "psess:agent"},
            )
        )
        assert recovered["status"] == "interrupted"
    finally:
        restarted.close()


def test_partial_worker_start_failure_rolls_back_without_enabling_requests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = compose(tmp_path)
    original = threading.Thread.start
    started: list[threading.Thread] = []

    def fail_second(self: threading.Thread) -> None:
        if self.name.startswith("qma-agent-request"):
            if started:
                raise RuntimeError("sanitized test failure")
            started.append(self)
        original(self)

    monkeypatch.setattr(threading.Thread, "start", fail_second)
    try:
        result = process.configure_agent_requests(
            providers={"controlled": ControlledProvider()},
            policies={
                "global": AgentRequestPolicy(CopilotProfile("global"), "authoring", "controlled")
            },
            max_workers=2,
        )
        assert is_refusal(result)
        assert process.agent_requests is None
        assert len(started) == 1
        assert not started[0].is_alive()
        assert process.sqlite_connection_count() == 1
    finally:
        process.close()


def test_expired_queued_context_fails_before_second_model_call(tmp_path: Path) -> None:
    process = compose(tmp_path)
    provider = ControlledProvider(blocked=True)
    value(
        process.configure_agent_requests(
            providers={"controlled": provider},
            policies={
                "global": AgentRequestPolicy(
                    CopilotProfile("global"),
                    "authoring",
                    "controlled",
                    session_app_instance_id="inst:expiry",
                )
            },
            max_workers=1,
        )
    )
    value(
        process.product_sessions.mint(
            product_session_id="psess:agent",
            profile="authoring",
            principal="operator",
            contribution={"qualified_id": "research:qml", "package_version": "0.1.0"},
            instance_id="inst:expiry",
            config_revision=0,
            context_revision=0,
            as_of="2026-10-03T00:00:00Z",
        )
    )
    value(
        process.product_sessions.host_grant(
            "psess:agent",
            grant_id="grant:expiry",
            op_id="qml.research.browse",
            op_version=1,
            effect_class="read",
            parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
            expires_at="2030-01-01T00:00:00Z",
        )
    )
    bridge = process.agent_requests
    assert bridge is not None
    bridge.now = lambda: "2029-01-01T00:00:00Z"
    try:
        conn = connection(process)
        receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        assert provider.started.wait(2)
        second = receipt(
            dispatch(
                process,
                conn,
                "submit_agent_request",
                submit_params(key="expire-later", prompt="must not disclose"),
            )
        )
        bridge.now = lambda: "2031-01-01T00:00:00Z"
        provider.release.set()
        failed = wait_status(process, conn, cast("str", second["request_id"]), "failed")
        assert failed["content_withheld"] is True
        assert len(provider.requests) == 1
    finally:
        provider.release.set()
        process.close()


def test_restart_recovers_undispatched_backlog_with_lowered_capacity(tmp_path: Path) -> None:
    original = compose(tmp_path)
    configure(original, ControlledProvider())
    mint(original)
    bridge = original.agent_requests
    assert bridge is not None
    request_ids: list[str] = []
    try:
        # Model the durable acceptance boundary before scheduling, without
        # pretending that a dispatched model turn is safe to replay.
        for n in range(3):
            row = value(
                bridge.runtime.submit(
                    RequestSpec(
                        idempotency_key=f"recover-{n}",
                        principal="operator",
                        product_session_id="psess:agent",
                        context_revision=0,
                        profile=CopilotProfile("global", instructions="host instructions"),
                        prompt=f"pending-{n}",
                        provider_id="controlled",
                        model="host-model",
                    )
                )
            )
            request_ids.append(row.request_id)
    finally:
        original.close()
    restarted = compose(tmp_path, boot="queued-restarted")
    provider = ControlledProvider(blocked=True)
    try:
        configure(restarted, provider, workers=1, inflight=1)
        conn = connection(restarted)
        assert provider.started.wait(2)
        assert "error" in dispatch(
            restarted, conn, "submit_agent_request", submit_params(key="new-during-recovery")
        )
        provider.release.set()
        for request_id in request_ids:
            wait_status(restarted, conn, request_id, "completed")
        assert [item.prompt for item in provider.requests] == [f"pending-{n}" for n in range(3)]
        replay = receipt(
            dispatch(
                restarted,
                conn,
                "submit_agent_request",
                submit_params(key="recover-1", prompt="pending-1"),
            )
        )
        assert replay["request_id"] == request_ids[1]
        assert len(provider.requests) == 3
    finally:
        provider.release.set()
        restarted.close()


def test_restart_fails_undispatched_request_after_context_narrows(tmp_path: Path) -> None:
    original = compose(tmp_path)
    configure(original, ControlledProvider())
    mint(original)
    bridge = original.agent_requests
    assert bridge is not None
    try:
        row = value(
            bridge.runtime.submit(
                RequestSpec(
                    idempotency_key="narrowed-recovery",
                    principal="operator",
                    product_session_id="psess:agent",
                    context_revision=0,
                    profile=CopilotProfile("global", instructions="host instructions"),
                    prompt="must not disclose",
                    provider_id="controlled",
                    model="host-model",
                )
            )
        )
        mint(original, revision=1)
    finally:
        original.close()
    restarted = compose(tmp_path, boot="narrowed-restarted")
    provider = ControlledProvider()
    try:
        configure(restarted, provider)
        conn = connection(restarted)
        failed = wait_status(restarted, conn, row.request_id, "failed")
        assert failed["error"] == "context_changed"
        assert failed["content_withheld"] is True
        assert not provider.requests
    finally:
        restarted.close()


def test_authenticated_resume_revalidates_owned_interrupted_request(tmp_path: Path) -> None:
    from qma.daemon.request_runtime.providers import ProviderError

    class InterruptedProvider(ControlledProvider):
        def execute(
            self,
            request: ProviderRequest,
            emit: Callable[[ProviderEvent], None],
            cancellation: threading.Event,
        ) -> ProviderResult:
            if not self.requests:
                self.requests.append(request)
                raise ProviderError("outcome_unknown", "deterministic transport loss")
            return super().execute(request, emit, cancellation)

    process = compose(tmp_path)
    try:
        mint(process)
        provider = InterruptedProvider()
        configure(process, provider)
        conn = connection(process)
        accepted = receipt(dispatch(process, conn, "submit_agent_request", submit_params()))
        request_id = str(accepted["request_id"])
        wait_status(process, conn, request_id, "interrupted")
        wrong = dispatch(
            process,
            conn,
            "resume_agent_request",
            {"product_session_ref": "psess:other", "request_id": request_id},
        )
        assert "error" in wrong
        resumed = receipt(
            dispatch(
                process,
                conn,
                "resume_agent_request",
                {"product_session_ref": "psess:agent", "request_id": request_id},
            )
        )
        assert resumed["status"] == "queued"
        assert wait_status(process, conn, request_id, "completed")["content"] == "answer:hello"
        assert len(provider.requests) == 2
    finally:
        process.close()
