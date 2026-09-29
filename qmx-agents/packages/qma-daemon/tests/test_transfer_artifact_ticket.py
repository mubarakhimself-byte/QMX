"""Story 70.2 — AM-03 ticket, loopback source_unreachable, live-control notify."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
from pathlib import Path
from typing import cast

from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.artifacts.ticket import (
    ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA,
    ARTIFACT_TRANSFER_TICKET_FOLD_ID,
    ARTIFACT_TRANSFER_TICKET_NEW_SQLITE_CLASS,
    ARTIFACT_TRANSFER_TICKET_STORE,
    ARTIFACT_TRANSFER_TICKET_TABLE,
    DAEMON_DIALS_IN,
    DAEMON_OPENS_DEST_INBOUND_PORT,
    DEC_0429_SUPERSEDED_BY,
    DEC_0440_SUPERSEDED_BY,
    DEST_CONTROL_NOTIFY_METHOD,
    INTER_DAEMON_DISCOVERY,
    LOCAL_INVOKE_FALLBACK,
    DestinationPlacement,
)
from qma.daemon.host_control import host_control_call
from qma.daemon.journal import CLOSED_PROJECTIONS, DEFINITION_STORE_MEMBERS, v1_fold_contract
from qma.daemon.journal.stores import StoreClass
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import TRANSFER_ARTIFACT_CAPABILITY, WIRE_PROTOCOL_VERSION
from qma.wire.transfer_artifact import claim_transfer_artifact_existed_at_inspect_sha
from qmf.core import is_ok, is_refusal
from qmf.core.refusal import RefusalCategory

_ORIGIN = "http://127.0.0.1:5173"
_FIXTURE_TTL = "PT15M"
_TLS_ORIGIN = "https://artifacts.example:8443"
_DEST_CRED = "cred://compute/worker-a"
_PROCESS_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"


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
    writer.write(_client_ws_frame(json.dumps(obj).encode("utf-8")))


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


async def _upgrade_machine_ws(
    host: str,
    port: int,
    credential_ref: str,
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
            "Sec-WebSocket-Protocol": CT40_WS_SUBPROTOCOL,
            "Authorization": f"Bearer {credential_ref}",
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


def _stage(process: DaemonProcess, body: bytes = b"complete-bytes") -> str:
    staged = process.artifacts.stage_complete_bytes(body)
    assert is_ok(staged), staged
    return staged.value.fp1


def _remote_placement(*, same_daemon: bool = False) -> DestinationPlacement:
    return DestinationPlacement(
        instance_id="inst-remote",
        environment_id="env-remote",
        placement_revision="rev-1",
        credential_ref=_DEST_CRED,
        same_daemon=same_daemon,
        reachable_hosts=("artifacts.example", "artifacts.example:8443", _TLS_ORIGIN),
    )


def test_am03_ticket_projection_on_existing_sqlite_class() -> None:
    assert ARTIFACT_TRANSFER_TICKET_STORE in CLOSED_PROJECTIONS
    assert ARTIFACT_TRANSFER_TICKET_STORE not in DEFINITION_STORE_MEMBERS
    assert len(DEFINITION_STORE_MEMBERS) == 16
    assert ARTIFACT_TRANSFER_TICKET_NEW_SQLITE_CLASS is False
    assert ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_transfer_artifact_existed_at_inspect_sha(True))
    contract = v1_fold_contract(ARTIFACT_TRANSFER_TICKET_FOLD_ID)
    assert contract is not None
    assert contract.source_stream == "artifact_transfer_ticket.*"
    assert contract.ordering_key == "journal_seq"
    assert contract.knowledge_time_bound == "as_of_recorded_at"
    assert contract.equal_instant_disposition == "ascending_journal_seq"
    assert DEC_0429_SUPERSEDED_BY is None
    assert DEC_0440_SUPERSEDED_BY is None
    assert DAEMON_DIALS_IN is False
    assert DAEMON_OPENS_DEST_INBOUND_PORT is False
    assert INTER_DAEMON_DISCOVERY is False
    assert LOCAL_INVOKE_FALLBACK is False
    assert StoreClass.JOURNAL_DERIVED_PROJECTION.value == "journal_derived_projection"
    dispatch = _PROCESS_SRC.read_text(encoding="utf-8")
    assert "TRANSFER_ARTIFACT" in dispatch
    assert "handle_transfer_artifact" in dispatch


def test_loopback_source_unreachable_and_same_daemon_skips_ticket(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-2-loopback")
    try:
        fp1 = _stage(process)
        process.register_destination_placement(_remote_placement())
        refused = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-loop",
                "instance_id": "inst-remote",
            }
        )
        assert is_refusal(refused)
        assert refused.category is RefusalCategory.POLICY_REJECTION
        assert refused.context["reason"] == "source_unreachable"
        assert refused.context["local_fallback"] is False
        assert refused.context["daemon_dials_in"] is False
        loopback = process.record_source_tls_origin("https://127.0.0.1:8765")
        assert is_refusal(loopback)
        assert loopback.context["reason"] == "source_unreachable"
        http = process.record_source_tls_origin("http://artifacts.example:8443")
        assert is_refusal(http)
        recorded = process.record_source_tls_origin(_TLS_ORIGIN)
        assert is_ok(recorded), recorded
        process.register_destination_placement(
            DestinationPlacement(
                instance_id="inst-deny",
                environment_id="env-deny",
                placement_revision="rev-x",
                credential_ref=_DEST_CRED,
                same_daemon=False,
                reachable_hosts=("other.example",),
            )
        )
        denied = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-deny-allow",
                "instance_id": "inst-deny",
            }
        )
        assert is_refusal(denied)
        assert denied.context["reason"] == "source_unreachable"
        assert denied.context["allowlisted"] is False
        process.register_destination_placement(
            DestinationPlacement(
                instance_id="inst-local",
                environment_id="env-local",
                placement_revision="rev-0",
                credential_ref=_DEST_CRED,
                same_daemon=True,
            )
        )
        local = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-local",
                "instance_id": "inst-local",
            }
        )
        assert is_ok(local), local
        assert local.value.transfer_required is False
        assert local.value.ticket_id is None
        assert local.value.fp1 == fp1
        assert local.value.local_complete is True
        assert process.transfers.open_tickets() == ()
        assert ARTIFACT_TRANSFER_TICKET_TABLE not in process.sqlite_table_names() or (
            process.transfers.open_tickets() == ()
        )
    finally:
        process.close()


def test_ticket_issued_until_dest_reconnect_then_notified(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-2-ticket")
    try:
        fp1 = _stage(process)
        recorded = process.record_source_tls_origin(_TLS_ORIGIN)
        assert is_ok(recorded), recorded
        process.register_destination_placement(_remote_placement())
        issued = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-1",
                "instance_id": "inst-remote",
                "product_session_ref": "psess:H",
            }
        )
        assert is_ok(issued), issued
        assert issued.value.transfer_required is True
        ticket_id = issued.value.ticket_id
        assert isinstance(ticket_id, str) and ticket_id.startswith("att:")
        assert issued.value.state == "issued"
        ticket = process.transfers.get(ticket_id)
        assert ticket is not None
        assert ticket.fp1 == fp1
        assert ticket.source_origin == _TLS_ORIGIN
        assert ticket.credential_ref == _DEST_CRED
        assert ticket.product_session_ref == "psess:H"
        assert ticket.durable_command_id == "psess:H/cmd-1"
        assert "superseded_by" not in ticket.to_payload()
        replay = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-1",
                "instance_id": "inst-remote",
                "product_session_ref": "psess:H",
            }
        )
        assert is_ok(replay)
        assert replay.value.ticket_id == ticket_id
        handle = process.dest_control_up(_DEST_CRED)
        assert is_ok(handle), handle
        notified = process.transfers.get(ticket_id)
        assert notified is not None
        assert notified.state == "notified"
        assert handle.value.notifications
        note = handle.value.notifications[0]
        assert note["method"] == DEST_CONTROL_NOTIFY_METHOD
        assert "id" not in note
        params_obj = note["params"]
        assert isinstance(params_obj, dict)
        params = cast("dict[str, object]", params_obj)
        assert params["ticket_id"] == ticket_id
        assert params["source_origin"] == _TLS_ORIGIN
        live = process.transfers.open_tickets()
        assert len(live) == 1
        assert live[0].state == "notified"
        rows = process.journal.read_all()
        assert is_ok(rows)
        events = [row["event"] for row in rows.value]
        assert "artifact_transfer_ticket.issued" in events
        assert "artifact_transfer_ticket.notified" in events
        for row in rows.value:
            payload = row.get("payload")
            if isinstance(payload, dict):
                assert "superseded_by" not in payload
        assert ARTIFACT_TRANSFER_TICKET_TABLE in process.sqlite_table_names()
        deny = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-deny",
                "instance_id": "inst-remote",
            },
            capabilities={},
        )
        assert is_refusal(deny)
        assert deny.context["missing"] == TRANSFER_ARTIFACT_CAPABILITY
        machine = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-machine",
                "instance_id": "inst-remote",
            },
            principal_class=PrincipalClass.MACHINE,
        )
        assert is_refusal(machine)
    finally:
        process.close()


def test_live_transfer_artifact_on_bound_pairing_ws(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-2-live-ws")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            fp1 = _stage(process)
            recorded = process.record_source_tls_origin(_TLS_ORIGIN)
            assert is_ok(recorded), recorded
            process.register_destination_placement(_remote_placement())
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={TRANSFER_ARTIFACT_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                result_obj = init_resp["result"]
                assert isinstance(result_obj, dict)
                result = cast("dict[str, object]", result_obj)
                caps_obj = result["capabilities"]
                assert isinstance(caps_obj, dict)
                caps = cast("dict[str, object]", caps_obj)
                assert caps.get(TRANSFER_ARTIFACT_CAPABILITY) is True
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "transfer_artifact",
                        "params": {
                            "fp1": fp1,
                            "command_id": "cmd-live",
                            "instance_id": "inst-remote",
                        },
                    },
                )
                await writer.drain()
                issued = await _ws_read_json(reader)
                assert "error" not in issued, issued
                issued_result_obj = issued["result"]
                assert isinstance(issued_result_obj, dict)
                issued_result = cast("dict[str, object]", issued_result_obj)
                ticket_id = issued_result["ticket_id"]
                assert isinstance(ticket_id, str)
                assert issued_result["state"] == "issued"
                ticket = process.transfers.get(ticket_id)
                assert ticket is not None
                assert ticket.source_origin == _TLS_ORIGIN
                handle = process.dest_control_up(_DEST_CRED)
                assert is_ok(handle), handle
                notified = process.transfers.get(ticket_id)
                assert notified is not None
                assert notified.state == "notified"
                assert handle.value.notifications
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_live_ws_notifies_when_dest_control_is_up(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-2-live-notify")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            fp1 = _stage(process)
            assert is_ok(process.record_source_tls_origin(_TLS_ORIGIN))
            process.register_destination_placement(_remote_placement())
            handle = process.dest_control_up(_DEST_CRED)
            assert is_ok(handle), handle
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={TRANSFER_ARTIFACT_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "transfer_artifact",
                        "params": {
                            "fp1": fp1,
                            "command_id": "cmd-live-up",
                            "instance_id": "inst-remote",
                        },
                    },
                )
                await writer.drain()
                notified = await _ws_read_json(reader)
                assert "error" not in notified, notified
                notified_result_obj = notified["result"]
                assert isinstance(notified_result_obj, dict)
                notified_result = cast("dict[str, object]", notified_result_obj)
                assert notified_result["state"] == "notified"
                assert handle.value.notifications
                note = handle.value.notifications[-1]
                assert note["method"] == DEST_CONTROL_NOTIFY_METHOD
                assert "id" not in note
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_payload_same_daemon_is_not_authority(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-fix-same-daemon")
    try:
        fp1 = _stage(process)
        refused = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-sd",
                "instance_id": "inst-unregistered",
                "same_daemon": True,
            }
        )
        assert is_refusal(refused)
        assert refused.context["local_fallback"] is False
        assert "registered" in str(refused.context.get("reason", ""))
        assert process.transfers.open_tickets() == ()
    finally:
        process.close()


def test_payload_dest_identity_registers_remote(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-fix-payload-dest")
    try:
        fp1 = _stage(process)
        recorded = process.record_source_tls_origin(_TLS_ORIGIN)
        assert is_ok(recorded), recorded
        issued = process.transfer_artifact(
            {
                "fp1": fp1,
                "command_id": "cmd-payload-dest",
                "instance_id": "inst-from-payload",
                "environment_id": "env-remote",
                "placement_revision": "rev-1",
                "credential_ref": _DEST_CRED,
                "reachable_hosts": [
                    "artifacts.example",
                    "artifacts.example:8443",
                    _TLS_ORIGIN,
                ],
                "same_daemon": True,
            }
        )
        assert is_ok(issued), issued
        assert issued.value.transfer_required is True
        ticket_id = issued.value.ticket_id
        assert isinstance(ticket_id, str)
        ticket = process.transfers.get(ticket_id)
        assert ticket is not None
        assert ticket.state == "issued"
        dest = process.transfers.placements.get("inst-from-payload")
        assert dest is not None
        assert dest.same_daemon is False
        assert dest.credential_ref == _DEST_CRED
    finally:
        process.close()


def test_live_machine_ws_notifies_issued_ticket(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-fix-dest-up")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            fp1 = _stage(process)
            recorded = process.record_source_tls_origin(_TLS_ORIGIN)
            assert is_ok(recorded), recorded
            process.register_destination_placement(_remote_placement())
            issued = process.transfer_artifact(
                {
                    "fp1": fp1,
                    "command_id": "cmd-dest-up",
                    "instance_id": "inst-remote",
                }
            )
            assert is_ok(issued), issued
            ticket_id = issued.value.ticket_id
            assert isinstance(ticket_id, str)
            ticket = process.transfers.get(ticket_id)
            assert ticket is not None
            assert ticket.state == "issued"
            _reader, writer = await _upgrade_machine_ws(host, port, _DEST_CRED)
            try:
                notified = process.transfers.get(ticket_id)
                assert notified is not None
                assert notified.state == "notified"
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_live_transfer_after_host_configure_source_origin(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-fix-source-origin")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            fp1 = _stage(process)
            loopback = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={"target": "source-origin", "origin": "https://127.0.0.1:8765"},
            )
            assert is_ok(loopback), loopback
            assert loopback.value.get("ok") is False
            configured = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={"target": "source-origin", "origin": _TLS_ORIGIN},
            )
            assert is_ok(configured), configured
            assert configured.value.get("ok") is True
            placed = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={
                    "target": "dest-placement",
                    "instance_id": "inst-remote",
                    "environment_id": "env-remote",
                    "placement_revision": "rev-1",
                    "credential_ref": _DEST_CRED,
                    "reachable_hosts": [
                        "artifacts.example",
                        "artifacts.example:8443",
                        _TLS_ORIGIN,
                    ],
                },
            )
            assert is_ok(placed), placed
            assert placed.value.get("ok") is True
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={TRANSFER_ARTIFACT_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "transfer_artifact",
                        "params": {
                            "fp1": fp1,
                            "command_id": "cmd-live-origin",
                            "instance_id": "inst-remote",
                        },
                    },
                )
                await writer.drain()
                issued = await _ws_read_json(reader)
                assert "error" not in issued, issued
                issued_result_obj = issued["result"]
                assert isinstance(issued_result_obj, dict)
                issued_result = cast("dict[str, object]", issued_result_obj)
                ticket_id = issued_result["ticket_id"]
                assert isinstance(ticket_id, str)
                assert issued_result["state"] == "issued"
                ticket = process.transfers.get(ticket_id)
                assert ticket is not None
                assert ticket.source_origin == _TLS_ORIGIN
                assert ticket.operator_principal == _record_id
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())
