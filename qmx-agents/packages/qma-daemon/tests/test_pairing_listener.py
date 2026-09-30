"""Pairing HTTP/WS production wiring on the bound CT-40 listener."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
from pathlib import Path
from typing import cast

from pytest import MonkeyPatch
from qma.core.ontology import ActorId, DeskSlug, Quant, RoleName
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL, PairingWsHandle
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.plugins.lifecycle import AtomicRoster
from qma.daemon.plugins.packs import DeskPluginRoster
from qma.daemon.process import DaemonProcess
from qma.daemon.taskgraph.records import GraphTemplate
from qma.wire.auth import format_pairing_authorization
from qma.wire.initialize import (
    GET_EDITOR_DRAFT_HEAD_CAPABILITY,
    PUBLISH_EDITOR_DRAFT_CAPABILITY,
    SAVE_EDITOR_DRAFT_CAPABILITY,
    WIRE_PROTOCOL_VERSION,
    WireConnection,
)
from qmf.core import Result, is_ok
from qmf.data.store.refusals import policy_rejection

_ORIGIN = "http://127.0.0.1:5173"
_FIXTURE_TTL = "PT15M"


def _seed_configs(tmp_path: Path) -> dict[str, dict[str, object]]:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return research_corpus_plugin_load_config(seed)


def _compose(tmp_path: Path, *, boot: str) -> DaemonProcess:
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id=boot,
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_ok(result), result
    return result.value


def _http_bytes(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> bytes:
    hdrs = dict(headers or {})
    if body and "Content-Length" not in hdrs:
        hdrs["Content-Length"] = str(len(body))
    lines = [f"{method} {path} HTTP/1.1"]
    for key, value in hdrs.items():
        lines.append(f"{key}: {value}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body


def _split_http(raw: bytes) -> tuple[int, dict[str, str], bytes]:
    head, _, body = raw.partition(b"\r\n\r\n")
    lines = head.decode("iso-8859-1").split("\r\n")
    status = int(lines[0].split(" ")[1])
    headers: dict[str, str] = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        if name:
            headers[name.strip().casefold()] = value.strip()
    return status, headers, body


async def _exchange(host: str, port: int, request: bytes) -> bytes:
    reader, writer = await asyncio.open_connection(host, port)
    try:
        writer.write(request)
        await writer.drain()
        return await asyncio.wait_for(reader.read(), timeout=5.0)
    finally:
        writer.close()
        await writer.wait_closed()


def _json_object(body: bytes) -> dict[str, object]:
    parsed: object = json.loads(body.decode("utf-8"))
    assert isinstance(parsed, dict)
    return cast("dict[str, object]", parsed)


async def _pair_over_listener(process: DaemonProcess, host: str, port: int) -> tuple[str, str]:
    configured = process.configure_pairing_ttl(_FIXTURE_TTL)
    assert is_ok(configured), configured
    started_raw = await _exchange(
        host,
        port,
        _http_bytes("POST", "/pair/start", headers={"Origin": _ORIGIN, "Host": f"{host}:{port}"}),
    )
    status, _headers, body = _split_http(started_raw)
    assert status == 200, started_raw
    started = _json_object(body)
    pending_id = started["pairing_record_id"]
    code = started["pending_code"]
    assert isinstance(pending_id, str)
    assert isinstance(code, str)
    paired = process.pair_pending(code)
    assert is_ok(paired), paired
    confirm_raw = await _exchange(
        host,
        port,
        _http_bytes(
            "POST",
            "/pair/confirm",
            headers={
                "Origin": _ORIGIN,
                "Host": f"{host}:{port}",
                "Content-Type": "application/json",
            },
            body=json.dumps({"pending_id": pending_id}).encode("utf-8"),
        ),
    )
    confirm_status, _confirm_headers, confirm_body = _split_http(confirm_raw)
    assert confirm_status == 200, confirm_raw
    issued = _json_object(confirm_body)
    proof = issued["pairing_proof"]
    record_id = issued["pairing_record_id"]
    assert isinstance(proof, str)
    assert isinstance(record_id, str)
    return record_id, proof


def test_pair_http_and_authenticated_bearer_on_bound_listener(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-68-listener-http")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            options_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "OPTIONS",
                    "/pair/start",
                    headers={
                        "Origin": _ORIGIN,
                        "Access-Control-Request-Method": "POST",
                    },
                ),
            )
            options_status, options_headers, options_body = _split_http(options_raw)
            assert options_status == 204
            assert options_body == b""
            assert options_headers.get("access-control-allow-origin") == _ORIGIN
            auth = format_pairing_authorization(proof)
            assert is_ok(auth), auth
            authed = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    "/q/list_mailbox",
                    headers={"Origin": _ORIGIN, "Authorization": auth.value},
                ),
            )
            authed_status, _authed_headers, authed_body = _split_http(authed)
            assert authed_status == 200
            listed = _json_object(authed_body)
            assert listed["ok"] is True
            result = listed["result"]
            assert isinstance(result, dict)
            assert result["query"] == "list_mailbox"
            assert result["product_chat"] is False
            assert result["rows"] == []
            unauth = await _exchange(
                host,
                port,
                _http_bytes("GET", "/q/list_mailbox", headers={"Origin": _ORIGIN}),
            )
            unauth_status, _unauth_headers, _unauth_body = _split_http(unauth)
            assert unauth_status in {401, 403}
            renew_unauth = await _exchange(
                host,
                port,
                _http_bytes("POST", "/pair/renew", headers={"Origin": _ORIGIN}),
            )
            renew_status, _renew_headers, _renew_body = _split_http(renew_unauth)
            assert renew_status in {401, 403}
            host_raw = await _exchange(
                host,
                port,
                _http_bytes("POST", "/host/stop", headers={"Origin": _ORIGIN}),
            )
            host_status, _host_headers, _host_body = _split_http(host_raw)
            assert host_status in {401, 403}
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_ws_upgrade_registers_and_close_shuts_the_socket(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-68-listener-ws")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            record_id, proof = await _pair_over_listener(process, host, port)
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            handshake = _http_bytes(
                "GET",
                "/",
                headers={
                    "Host": f"{host}:{port}",
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                    "Sec-WebSocket-Version": "13",
                    "Sec-WebSocket-Key": key,
                    "Sec-WebSocket-Protocol": f"{CT40_WS_SUBPROTOCOL}, qmx.pair.{proof}",
                    "Origin": _ORIGIN,
                },
            )
            reader, writer = await asyncio.open_connection(host, port)
            try:
                writer.write(handshake)
                await writer.drain()
                raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5.0)
                status, headers, _body = _split_http(raw)
                assert status == 101, raw
                assert headers.get("sec-websocket-protocol") == CT40_WS_SUBPROTOCOL
                assert "sec-websocket-accept" in headers
                revoked = process.pair_revoke(pairing_record_id=record_id)
                assert is_ok(revoked), revoked
                leftover = await asyncio.wait_for(reader.read(), timeout=5.0)
                assert leftover == b""
            finally:
                writer.close()
                await writer.wait_closed()
            refused_key = base64.b64encode(os.urandom(16)).decode("ascii")
            refused_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    "/",
                    headers={
                        "Host": f"{host}:{port}",
                        "Upgrade": "websocket",
                        "Connection": "Upgrade",
                        "Sec-WebSocket-Version": "13",
                        "Sec-WebSocket-Key": refused_key,
                        "Sec-WebSocket-Protocol": CT40_WS_SUBPROTOCOL,
                        "Origin": _ORIGIN,
                    },
                ),
            )
            refused_status, _refused_headers, _refused_body = _split_http(refused_raw)
            assert refused_status != 101
            assert refused_status in {400, 401, 403}
        finally:
            await process.aclose()

    asyncio.run(_run())


def _client_ws_frame(payload: bytes) -> bytes:
    mask = os.urandom(4)
    header = bytearray()
    header.append(0x81)
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    header.extend(mask)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return bytes(header) + masked


def _decode_server_ws_frame(buf: bytes) -> tuple[int, bytes, bytes] | None:
    if len(buf) < 2:
        return None
    opcode = buf[0] & 0x0F
    masked = (buf[1] & 0x80) != 0
    length = buf[1] & 0x7F
    offset = 2
    if length == 126:
        if len(buf) < 4:
            return None
        length = struct.unpack("!H", buf[2:4])[0]
        offset = 4
    elif length == 127:
        if len(buf) < 10:
            return None
        length = struct.unpack("!Q", buf[2:10])[0]
        offset = 10
    mask = b""
    if masked:
        if len(buf) < offset + 4:
            return None
        mask = buf[offset : offset + 4]
        offset += 4
    if len(buf) < offset + length:
        return None
    payload = buf[offset : offset + length]
    if masked:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    return opcode, payload, buf[offset + length :]


def _ws_write(writer: asyncio.StreamWriter, obj: dict[str, object]) -> None:
    payload = json.dumps(obj).encode("utf-8")
    writer.write(_client_ws_frame(payload))


async def _ws_read_json(reader: asyncio.StreamReader) -> dict[str, object]:
    buf = b""
    while True:
        chunk = await asyncio.wait_for(reader.read(65536), timeout=5.0)
        assert chunk, "paired CT-40 socket closed before a JSON-RPC frame"
        buf += chunk
        decoded = _decode_server_ws_frame(buf)
        if decoded is None:
            continue
        opcode, payload, buf = decoded
        if opcode != 0x1:
            continue
        parsed: object = json.loads(payload.decode("utf-8"))
        assert isinstance(parsed, dict)
        return cast("dict[str, object]", parsed)


async def _upgrade_paired_ws(
    host: str,
    port: int,
    proof: str,
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    handshake = _http_bytes(
        "GET",
        "/",
        headers={
            "Host": f"{host}:{port}",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": key,
            "Sec-WebSocket-Protocol": f"{CT40_WS_SUBPROTOCOL}, qmx.pair.{proof}",
            "Origin": _ORIGIN,
        },
    )
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(handshake)
    await writer.drain()
    raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=5.0)
    status, headers, _body = _split_http(raw)
    assert status == 101, raw
    assert headers.get("sec-websocket-protocol") == CT40_WS_SUBPROTOCOL
    return reader, writer


def _actor(slug: str) -> ActorId:
    minted = ActorId.mint(DeskSlug.RESEARCH, slug)
    assert is_ok(minted)
    return minted.value


def _quant(*, slug: str) -> Quant:
    return Quant(
        actor_id=_actor(slug),
        desk=DeskSlug.RESEARCH,
        quant_slug=slug,
        role=RoleName.RESEARCHER,
        name=f"Quant {slug}",
        lead=False,
    )


def _mint_process_session(process: DaemonProcess) -> None:
    minted = process.product_sessions.mint(
        product_session_id="psess:H",
        profile="authoring",
        principal="operator",
        contribution={"package_version": "0.1.0", "qualified_id": "analysis-backtest:qmb"},
        instance_id=None,
        config_revision=4,
        as_of="2026-09-20T00:00:00Z",
        granted_ops=(),
        selected_refs=(),
        scope_path=[{"kind": "desk", "id": "research"}],
    )
    assert is_ok(minted), minted


async def _initialize_ws(
    writer: asyncio.StreamWriter,
    reader: asyncio.StreamReader,
    *,
    capabilities: dict[str, object],
    req_id: int = 1,
) -> dict[str, object]:
    _ws_write(
        writer,
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": WIRE_PROTOCOL_VERSION,
                "capabilities": capabilities,
            },
        },
    )
    await writer.drain()
    return await _ws_read_json(reader)


def test_live_send_message_on_bound_pairing_ws(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-69-live-send")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            sender = _quant(slug="alpha")
            recipient = _quant(slug="beta")
            assert is_ok(process.mailboxes.open_for_quant(sender))
            assert is_ok(process.mailboxes.open_for_quant(recipient))
            _mint_process_session(process)
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(writer, reader, capabilities={})
                assert "error" not in init_resp, init_resp
                result_obj = init_resp["result"]
                assert isinstance(result_obj, dict)
                result = cast("dict[str, object]", result_obj)
                producer_id = result["producer_id"]
                assert isinstance(producer_id, str)
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "send_message",
                        "params": {
                            "msg_id": "msg-live",
                            "from": sender.actor_id.value,
                            "to": recipient.actor_id.value,
                            "kind": "handoff",
                            "correlation_id": "corr-live",
                            "body": {"text": "hello"},
                            "priority": 1,
                            "product_session_ref": "psess:H",
                            "producer_id": producer_id,
                            "wire_id": "C1",
                        },
                    },
                )
                await writer.drain()
                sent = await _ws_read_json(reader)
                assert "error" not in sent, sent
                sent_result = sent["result"]
                assert isinstance(sent_result, dict)
                assert sent_result["msg_id"] == "msg-live"
                landed = process.mailboxes.record_for("msg-live")
                assert landed is not None
                assert landed.envelope.product_session_ref == "psess:H"
                assert landed.producer_id == producer_id
                assert landed.wire_id == "C1"
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_live_editor_draft_commands_query_and_capability_mismatch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-71-editor-live")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host, port = bound.value.host, bound.value.port
            record_id, proof = await _pair_over_listener(process, host, port)
            auth = format_pairing_authorization(proof)
            assert is_ok(auth), auth
            unrelated_template = GraphTemplate(qualified_id="demo:live-editor", version="0.9.0")
            assert is_ok(process.roster.templates.register(unrelated_template))
            roster = AtomicRoster(tmp_path / "authoring-pack")
            initial_roster = roster.load()
            assert is_ok(initial_roster), initial_roster
            unrelated_provider: dict[str, object] = {
                "contribution_id": "pack:live-unrelated",
                "point": "graph_template",
                "qualified_id": "demo:live-editor",
                "version": "0.9.0",
                "published": True,
                "enabled": True,
            }
            seeded_roster = dict(initial_roster.value)
            seeded_roster["published"] = [unrelated_provider]
            assert is_ok(roster.publish(seeded_roster))
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                initialized = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={
                        SAVE_EDITOR_DRAFT_CAPABILITY: True,
                        GET_EDITOR_DRAFT_HEAD_CAPABILITY: True,
                        PUBLISH_EDITOR_DRAFT_CAPABILITY: True,
                    },
                )
                assert "error" not in initialized, initialized
                result = cast("dict[str, object]", initialized["result"])
                capabilities = cast("dict[str, object]", result["capabilities"])
                assert capabilities.get(SAVE_EDITOR_DRAFT_CAPABILITY) is True
                assert capabilities.get(GET_EDITOR_DRAFT_HEAD_CAPABILITY) is True
                assert capabilities.get(PUBLISH_EDITOR_DRAFT_CAPABILITY) is True

                staged = process.artifacts.stage_complete_bytes(
                    json.dumps(
                        {
                            "artifact_kind": "graph_template",
                            "qualified_id": "demo:live-editor",
                            "version": "1.0.0",
                            "nodes": [],
                            "edges": [],
                        },
                        sort_keys=True,
                    ).encode()
                )
                assert is_ok(staged), staged
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": SAVE_EDITOR_DRAFT_CAPABILITY,
                        "params": {"fp1": staged.value.fp1},
                    },
                )
                await writer.drain()
                saved = await _ws_read_json(reader)
                assert "error" not in saved, saved
                saved_result = cast("dict[str, object]", saved["result"])
                draft_id = saved_result["editor_draft_id"]
                assert isinstance(draft_id, str)

                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": PUBLISH_EDITOR_DRAFT_CAPABILITY,
                        "params": {
                            "editor_draft_id": draft_id,
                            "expected_revision": staged.value.fp1,
                        },
                    },
                )
                await writer.drain()
                published = await _ws_read_json(reader)
                assert "error" not in published, published
                first_result = cast("dict[str, object]", published["result"])
                first_contribution_id = first_result["contribution_id"]
                assert isinstance(first_contribution_id, str)
            finally:
                writer.close()
                await writer.wait_closed()

            enabled = process.roster.enable_published_authoring_contribution(
                first_contribution_id,
                principal=PrincipalClass.OPERATOR,
                correlation_id="live-editor-replacement-enable",
            )
            assert is_ok(enabled), enabled
            first_plugin_id = enabled.value.manifest.id
            assert process.roster.templates.get_versioned("demo:live-editor", "1.0.0") is not None

            # Reconnect through the same authenticated transport for the successor.
            second_reader, second_writer = await _upgrade_paired_ws(host, port, proof)
            try:
                second_init = await _initialize_ws(
                    second_writer,
                    second_reader,
                    capabilities={
                        SAVE_EDITOR_DRAFT_CAPABILITY: True,
                        GET_EDITOR_DRAFT_HEAD_CAPABILITY: True,
                        PUBLISH_EDITOR_DRAFT_CAPABILITY: True,
                    },
                )
                assert "error" not in second_init, second_init
                successor = process.artifacts.stage_complete_bytes(
                    json.dumps(
                        {
                            "artifact_kind": "graph_template",
                            "qualified_id": "demo:live-editor",
                            "version": "2.0.0",
                            "nodes": [],
                            "edges": [],
                        },
                        sort_keys=True,
                    ).encode()
                )
                assert is_ok(successor), successor
                _ws_write(
                    second_writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": SAVE_EDITOR_DRAFT_CAPABILITY,
                        "params": {"fp1": successor.value.fp1},
                    },
                )
                await second_writer.drain()
                second_saved = await _ws_read_json(second_reader)
                assert "error" not in second_saved, second_saved
                successor_draft = cast("dict[str, object]", second_saved["result"])
                successor_draft_id = successor_draft["editor_draft_id"]
                assert isinstance(successor_draft_id, str)

                publish_request: dict[str, object] = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": PUBLISH_EDITOR_DRAFT_CAPABILITY,
                    "params": {
                        "editor_draft_id": successor_draft_id,
                        "expected_revision": successor.value.fp1,
                    },
                }

                original_retire = DeskPluginRoster.retire_replaced_authoring_contribution

                def refuse_first_retirement(
                    _roster: DeskPluginRoster,
                    _contribution_id: str,
                    _qualified_id: str,
                    _version: str,
                    *,
                    principal: object,
                ) -> Result[None]:
                    _ = principal
                    return policy_rejection("plugin.enable", "simulated lost-ack cleanup failure")

                monkeypatch.setattr(
                    DeskPluginRoster,
                    "retire_replaced_authoring_contribution",
                    refuse_first_retirement,
                )
                _ws_write(second_writer, publish_request)
                await second_writer.drain()
                first_ack = await _ws_read_json(second_reader)
                assert "error" in first_ack, first_ack
                # The publication transaction already committed before runtime
                # retirement refused; ignore this response as a lost ack and retry.
                after_first_ack_roster = roster.load()
                after_first_ack_events = process.journal.read_events()
                assert is_ok(after_first_ack_roster) and is_ok(after_first_ack_events)
                generation = after_first_ack_roster.value["roster_generation"]
                publish_event_count = sum(
                    event.event == "editor_draft.published"
                    for event in after_first_ack_events.value
                )
                assert first_plugin_id in process.roster.loader.loaded_ids()
                assert (
                    process.roster.templates.get_versioned("demo:live-editor", "1.0.0") is not None
                )
                successor_row = next(
                    row
                    for row in cast(
                        list[dict[str, object]], after_first_ack_roster.value["published"]
                    )
                    if row.get("version") == "2.0.0"
                )
                assert successor_row["enabled"] is False

                monkeypatch.setattr(
                    DeskPluginRoster,
                    "retire_replaced_authoring_contribution",
                    original_retire,
                )
                retry_request = dict(publish_request)
                retry_request["id"] = 4
                _ws_write(second_writer, retry_request)
                await second_writer.drain()
                retried = await _ws_read_json(second_reader)
                assert "error" not in retried, retried
                retried_result = cast("dict[str, object]", retried["result"])
                assert retried_result["contribution_id"] != first_contribution_id
                final_roster = roster.load()
                final_events = process.journal.read_events()
                assert is_ok(final_roster) and is_ok(final_events)
                assert final_roster.value["roster_generation"] == generation
                assert (
                    sum(event.event == "editor_draft.published" for event in final_events.value)
                    == publish_event_count
                )
                rows = cast(list[dict[str, object]], final_roster.value["published"])
                assert any(row.get("contribution_id") == "pack:live-unrelated" for row in rows)
                assert any(
                    row.get("version") == "2.0.0" and row.get("enabled") is False for row in rows
                )
                assert first_plugin_id not in process.roster.loader.loaded_ids()
                assert process.roster.templates.get_versioned("demo:live-editor", "1.0.0") is None
                assert (
                    process.roster.templates.get_versioned("demo:live-editor", "0.9.0")
                    is unrelated_template
                )
            finally:
                second_writer.close()
                await second_writer.wait_closed()

            queried = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/q/get_editor_draft_head?editor_draft_id={draft_id}",
                    headers={"Origin": _ORIGIN, "Authorization": auth.value},
                ),
            )
            query_status, _query_headers, query_body = _split_http(queried)
            assert query_status == 200, queried
            assert _json_object(query_body)["result"] == {
                "editor_draft_id": draft_id,
                "editor_revision": staged.value.fp1,
            }
            machine_http = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/q/get_editor_draft_head?editor_draft_id={draft_id}",
                    headers={
                        "Origin": _ORIGIN,
                        "Authorization": "Bearer cred://machine/editor-test",
                    },
                ),
            )
            machine_status, _machine_headers, machine_body = _split_http(machine_http)
            assert machine_status in {401, 403}, machine_http
            assert _json_object(machine_body).get("ok") is False

            # A paired machine connection is refused before draft service access.
            machine = WireConnection()
            machine._authenticated = True  # pyright: ignore[reportPrivateUsage]
            machine._principal_class = PrincipalClass.MACHINE  # pyright: ignore[reportPrivateUsage]
            machine._initialized = True  # pyright: ignore[reportPrivateUsage]
            machine._producer_id = "machine-editor-test"  # pyright: ignore[reportPrivateUsage]
            machine._capabilities = {SAVE_EDITOR_DRAFT_CAPABILITY: True}  # pyright: ignore[reportPrivateUsage]
            refused = process._dispatch_paired_ct40(  # pyright: ignore[reportPrivateUsage]
                machine,
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 4,
                        "method": SAVE_EDITOR_DRAFT_CAPABILITY,
                        "params": {"fp1": staged.value.fp1},
                    }
                ).encode(),
                session_key=record_id,
                connection_token="machine-editor-test",
            )
            assert refused is not None and "error" in refused
            error = cast("dict[str, object]", refused["error"])
            data = cast("dict[str, object]", error["data"])
            context = cast("dict[str, object]", data["context"])
            assert context["field"] == "principal_class"

            # A second operator session negotiates save only; publish and the
            # authenticated HTTP query both report their missing capability.
            _second_record, second_proof = await _pair_over_listener(process, host, port)
            second_auth = format_pairing_authorization(second_proof)
            assert is_ok(second_auth), second_auth
            second_reader, second_writer = await _upgrade_paired_ws(host, port, second_proof)
            try:
                init = await _initialize_ws(
                    second_writer,
                    second_reader,
                    capabilities={SAVE_EDITOR_DRAFT_CAPABILITY: True},
                )
                assert "error" not in init, init
                result = cast("dict[str, object]", init["result"])
                negotiated = cast("dict[str, object]", result["capabilities"])
                assert negotiated.get(GET_EDITOR_DRAFT_HEAD_CAPABILITY) is not True
                assert negotiated.get(PUBLISH_EDITOR_DRAFT_CAPABILITY) is not True
                _ws_write(
                    second_writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 5,
                        "method": PUBLISH_EDITOR_DRAFT_CAPABILITY,
                        "params": {
                            "editor_draft_id": draft_id,
                            "expected_revision": staged.value.fp1,
                        },
                    },
                )
                await second_writer.drain()
                publish_refusal = await _ws_read_json(second_reader)
                error = cast("dict[str, object]", publish_refusal["error"])
                data = cast("dict[str, object]", error["data"])
                context = cast("dict[str, object]", data["context"])
                assert context["missing"] == PUBLISH_EDITOR_DRAFT_CAPABILITY
            finally:
                second_writer.close()
                await second_writer.wait_closed()

            second_query = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/q/get_editor_draft_head?editor_draft_id={draft_id}",
                    headers={"Origin": _ORIGIN, "Authorization": second_auth.value},
                ),
            )
            status, _headers, body = _split_http(second_query)
            assert status in {400, 403}, second_query
            refusal_body = _json_object(body)
            refusal = cast("dict[str, object]", refusal_body["refusal"])
            context = cast("dict[str, object]", refusal["context"])
            assert context["missing"] == GET_EDITOR_DRAFT_HEAD_CAPABILITY
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_list_mailbox_http_follows_initialize_capabilities(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-69-list-caps")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            auth = format_pairing_authorization(proof)
            assert is_ok(auth), auth
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                omitted = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={"commands": True},
                )
                assert "error" not in omitted, omitted
                omit_result_obj = omitted["result"]
                assert isinstance(omit_result_obj, dict)
                omit_caps = cast("dict[str, object]", omit_result_obj)
                advertised_obj = omit_caps["capabilities"]
                assert isinstance(advertised_obj, dict)
                advertised = cast("dict[str, object]", advertised_obj)
                assert advertised.get("list_mailbox") is not True
            finally:
                writer.close()
                await writer.wait_closed()
            unavailable = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    "/q/list_mailbox",
                    headers={"Origin": _ORIGIN, "Authorization": auth.value},
                ),
            )
            unavail_status, _unavail_headers, unavail_body = _split_http(unavailable)
            assert unavail_status in {400, 403}
            refused = _json_object(unavail_body)
            refusal_obj = refused["refusal"]
            assert isinstance(refusal_obj, dict)
            refusal = cast("dict[str, object]", refusal_obj)
            context_obj = refusal["context"]
            assert isinstance(context_obj, dict)
            context = cast("dict[str, object]", context_obj)
            assert context["reason"] == "query_unavailable"
            assert context["name"] == "list_mailbox"
            assert context["empty_mailbox"] is False
            assert refused.get("ok") is False

            _present_id, present_proof = await _pair_over_listener(process, host, port)
            present_auth = format_pairing_authorization(present_proof)
            assert is_ok(present_auth), present_auth
            _mint_process_session(process)
            present_reader, present_writer = await _upgrade_paired_ws(host, port, present_proof)
            try:
                present_init = await _initialize_ws(
                    present_writer,
                    present_reader,
                    capabilities={"list_mailbox": True},
                )
                assert "error" not in present_init, present_init
            finally:
                present_writer.close()
                await present_writer.wait_closed()
            empty_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    "/q/list_mailbox?product_session_ref=psess:H",
                    headers={"Origin": _ORIGIN, "Authorization": present_auth.value},
                ),
            )
            empty_status, _empty_headers, empty_body = _split_http(empty_raw)
            assert empty_status == 200, empty_raw
            empty = _json_object(empty_body)
            assert empty["ok"] is True
            empty_result = empty["result"]
            assert isinstance(empty_result, dict)
            assert empty_result["query"] == "list_mailbox"
            assert empty_result["product_chat"] is True
            assert empty_result["product_session_ref"] == "psess:H"
            assert empty_result["rows"] == []
            host_raw = await _exchange(
                host,
                port,
                _http_bytes("POST", "/host/stop", headers={"Origin": _ORIGIN}),
            )
            host_status, _host_headers, _host_body = _split_http(host_raw)
            assert host_status in {401, 403}
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_pairing_ws_handle_close_closes_writer() -> None:
    class _Writer:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

        def is_closing(self) -> bool:
            return self.closed

    writer = _Writer()
    handle = PairingWsHandle(proof_fp1="fp1:test", writer=writer)
    handle.close()
    assert handle.closed is True
    assert writer.closed is True
    handle.close()
    assert writer.closed is True
