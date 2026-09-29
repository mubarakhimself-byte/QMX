"""Story 70.3 — live machine GET redeem, dest-authored transfer_complete, invoke gate."""

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
    LOCAL_INVOKE_FALLBACK,
    DestinationPlacement,
    loopback_source_not_get_target,
)
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import (
    PAIRING_CAPABILITY,
    TRANSFER_COMPLETE_CAPABILITY,
    WIRE_PROTOCOL_VERSION,
)
from qma.wire.transfer_complete import (
    claim_machine_artifact_get_existed_at_inspect_sha,
    claim_transfer_complete_existed_at_inspect_sha,
)
from qmf.core import is_ok, is_refusal

_ORIGIN = "http://127.0.0.1:5173"
_FIXTURE_TTL = "PT15M"
_TLS_ORIGIN = "https://artifacts.example:8443"
_DEST_CRED = "cred://compute/worker-a"
_WRONG_CRED = "cred://compute/worker-b"
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
        assert chunk, "CT-40 socket closed before a JSON-RPC frame"
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


def _issue_notified(process: DaemonProcess, *, command_id: str = "cmd-1") -> tuple[str, str, bytes]:
    body = b"complete-bytes"
    fp1 = _stage(process, body)
    recorded = process.record_source_tls_origin(_TLS_ORIGIN)
    assert is_ok(recorded), recorded
    process.register_destination_placement(_remote_placement())
    handle = process.dest_control_up(_DEST_CRED)
    assert is_ok(handle), handle
    issued = process.transfer_artifact(
        {
            "fp1": fp1,
            "command_id": command_id,
            "instance_id": "inst-remote",
        }
    )
    assert is_ok(issued), issued
    ticket_id = issued.value.ticket_id
    assert isinstance(ticket_id, str)
    ticket = process.transfers.get(ticket_id)
    assert ticket is not None
    assert ticket.state == "notified"
    return ticket_id, fp1, body


def test_inspect_sha_and_live_symbols() -> None:
    assert is_refusal(claim_transfer_complete_existed_at_inspect_sha(True))
    assert is_ok(claim_transfer_complete_existed_at_inspect_sha(False))
    assert is_refusal(claim_machine_artifact_get_existed_at_inspect_sha(True))
    assert is_ok(claim_machine_artifact_get_existed_at_inspect_sha(False))
    dispatch = _PROCESS_SRC.read_text(encoding="utf-8")
    assert "_serve_artifact_machine_get" in dispatch
    assert "handle_transfer_complete" in dispatch
    assert "TRANSFER_COMPLETE" in dispatch
    loopback = loopback_source_not_get_target("https://127.0.0.1:8765")
    assert is_refusal(loopback)
    assert loopback.context["reason"] == "source_unreachable"
    assert loopback.context["get_target"] is True
    assert LOCAL_INVOKE_FALLBACK is False


def test_library_redeem_complete_idempotent_and_invoke_gate(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-3-lib")
    try:
        ticket_id, fp1, body = _issue_notified(process)
        refused_invoke = process.gate_invoke_until_transfer_complete(
            fp1=fp1,
            instance_id="inst-remote",
        )
        assert is_refusal(refused_invoke)
        assert refused_invoke.context["local_fallback"] is False
        assert refused_invoke.context["finish_on_local_disk"] is False
        assert refused_invoke.context["composer_ref_rewritten"] is False
        assert refused_invoke.context["silent_local_fallback"] is False
        guessed = process.gate_invoke_until_transfer_complete(fp1=fp1, instance_id="")
        assert is_refusal(guessed)
        assert guessed.context["instance_guessed"] is False
        redeemed = process.transfers.redeem_get(
            ticket_id=ticket_id,
            fp1=fp1,
            credential_ref=_DEST_CRED,
        )
        assert is_ok(redeemed), redeemed
        assert redeemed.value.content == body
        claimed = process.transfers.get(ticket_id)
        assert claimed is not None
        assert claimed.state == "claimed"
        replay_get = process.transfers.redeem_get(
            ticket_id=ticket_id,
            fp1=fp1,
            credential_ref=_DEST_CRED,
        )
        assert is_ok(replay_get)
        replay_ticket = process.transfers.get(ticket_id)
        assert replay_ticket is not None
        assert replay_ticket.state == "claimed"
        wrong = process.transfers.redeem_get(
            ticket_id=ticket_id,
            fp1=fp1,
            credential_ref=_WRONG_CRED,
        )
        assert is_refusal(wrong)
        placed = process.place_dest_pulled_bytes(body, ticket_id=ticket_id)
        assert is_ok(placed), placed
        dest_fp1 = placed.value.fp1
        operator = process.transfer_complete(
            {
                "ticket_id": ticket_id,
                "fp1": fp1,
                "byte_count": len(body),
                "command_id": "cmd-1",
            },
            principal_class=PrincipalClass.OPERATOR,
        )
        assert is_refusal(operator)
        completed = process.transfer_complete(
            {
                "ticket_id": ticket_id,
                "fp1": fp1,
                "byte_count": len(body),
                "command_id": "cmd-1",
            }
        )
        assert is_ok(completed), completed
        assert completed.value.state == "complete"
        assert completed.value.dest_bytes_written_on_source is False
        assert completed.value.second_ticket is False
        replay = process.transfer_complete(
            {
                "ticket_id": ticket_id,
                "fp1": fp1,
                "byte_count": len(body),
                "command_id": "cmd-1",
            }
        )
        assert is_ok(replay), replay
        assert replay.value.prior_complete is True
        assert replay.value.ticket_id == ticket_id
        assert replay.value.second_ticket is False
        reused = process.place_dest_pulled_bytes(body, ticket_id=ticket_id)
        assert is_ok(reused)
        assert reused.value.fp1 == dest_fp1
        assert reused.value.reused is True
        assert len(process.dest_artifacts.objects()) == 1
        gated = process.gate_invoke_until_transfer_complete(
            fp1=fp1,
            instance_id="inst-remote",
        )
        assert is_ok(gated), gated
        assert gated.value.transfer_gate_satisfied is True
        assert gated.value.instance_granted is False
        assert gated.value.instance_enabled is False
        assert gated.value.instance_guessed is False
        source = process.artifacts.get(fp1)
        assert source is not None
        assert source.content == body
    finally:
        process.close()


def test_interrupt_and_hash_mismatch_delete_incomplete(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="boot-70-3-mismatch")
    try:
        ticket_id, fp1, body = _issue_notified(process, command_id="cmd-mis")
        process.transfers.redeem_get(
            ticket_id=ticket_id,
            fp1=fp1,
            credential_ref=_DEST_CRED,
        )
        interrupted = process.place_dest_pulled_bytes(
            body[:4],
            ticket_id=ticket_id,
            interrupted=True,
        )
        assert is_refusal(interrupted)
        assert interrupted.context["runnable_remote_ref"] is False
        assert interrupted.context["composer_ref_rewritten"] is False
        assert process.dest_artifacts.get(fp1) is None
        mismatch = process.place_dest_pulled_bytes(b"not-the-bytes", ticket_id=ticket_id)
        assert is_refusal(mismatch)
        assert mismatch.context["runnable_remote_ref"] is False
        assert process.dest_artifacts.get(fp1) is None
        claimed = process.transfers.get(ticket_id)
        assert claimed is not None
        assert claimed.state == "claimed"
        still = process.gate_invoke_until_transfer_complete(
            fp1=fp1,
            instance_id="inst-remote",
        )
        assert is_refusal(still)
        assert still.context["local_fallback"] is False
        assert still.context["finish_on_local_disk"] is False
        source = process.artifacts.get(fp1)
        assert source is not None
        assert source.content == body
    finally:
        process.close()


def test_live_machine_get_and_dest_authored_transfer_complete(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-3-live")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            ticket_id, fp1, body = _issue_notified(process, command_id="cmd-live")
            _record_id, proof = await _pair_over_listener(process, host, port)
            pairing_get = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/artifacts/{fp1}",
                    headers={
                        "Host": f"{host}:{port}",
                        "Authorization": f"Bearer pairing:{proof}",
                        "X-QMX-Transfer-Ticket": ticket_id,
                        "Origin": _ORIGIN,
                    },
                ),
            )
            pairing_status, _pairing_headers, pairing_body = _split_http(pairing_get)
            assert pairing_status in {401, 403}, pairing_get
            pairing_json = _json_object(pairing_body)
            refusal_obj = pairing_json["refusal"]
            assert isinstance(refusal_obj, dict)
            refusal = cast("dict[str, object]", refusal_obj)
            context_obj = refusal["context"]
            assert isinstance(context_obj, dict)
            context = cast("dict[str, object]", context_obj)
            assert context.get("pairing_bearer") is True
            wrong_get = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/artifacts/{fp1}",
                    headers={
                        "Host": f"{host}:{port}",
                        "Authorization": f"Bearer {_WRONG_CRED}",
                        "X-QMX-Transfer-Ticket": ticket_id,
                    },
                ),
            )
            wrong_status, _wrong_headers, _wrong_body = _split_http(wrong_get)
            assert wrong_status == 403, wrong_get
            live_get = await _exchange(
                host,
                port,
                _http_bytes(
                    "GET",
                    f"/artifacts/{fp1}",
                    headers={
                        "Host": f"{host}:{port}",
                        "Authorization": f"Bearer {_DEST_CRED}",
                        "X-QMX-Transfer-Ticket": ticket_id,
                    },
                ),
            )
            get_status, get_headers, get_body = _split_http(live_get)
            assert get_status == 200, live_get
            assert get_headers.get("content-type") == "application/octet-stream"
            assert get_body == body
            claimed = process.transfers.get(ticket_id)
            assert claimed is not None
            assert claimed.state == "claimed"
            placed = process.place_dest_pulled_bytes(get_body, ticket_id=ticket_id)
            assert is_ok(placed), placed
            reader, writer = await _upgrade_machine_ws(host, port, _DEST_CRED)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={TRANSFER_COMPLETE_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                result_obj = init_resp["result"]
                assert isinstance(result_obj, dict)
                result = cast("dict[str, object]", result_obj)
                caps_obj = result["capabilities"]
                assert isinstance(caps_obj, dict)
                caps = cast("dict[str, object]", caps_obj)
                assert caps.get(TRANSFER_COMPLETE_CAPABILITY) is True
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "transfer_complete",
                        "params": {
                            "ticket_id": ticket_id,
                            "fp1": fp1,
                            "byte_count": len(body),
                            "command_id": "cmd-live",
                        },
                    },
                )
                await writer.drain()
                completed = await _ws_read_json(reader)
                assert "error" not in completed, completed
                completed_result_obj = completed["result"]
                assert isinstance(completed_result_obj, dict)
                completed_result = cast("dict[str, object]", completed_result_obj)
                assert completed_result["state"] == "complete"
                assert completed_result["dest_bytes_written_on_source"] is False
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "transfer_complete",
                        "params": {
                            "ticket_id": ticket_id,
                            "fp1": fp1,
                            "byte_count": len(body),
                            "command_id": "cmd-live",
                        },
                    },
                )
                await writer.drain()
                replay = await _ws_read_json(reader)
                assert "error" not in replay, replay
                replay_result_obj = replay["result"]
                assert isinstance(replay_result_obj, dict)
                replay_result = cast("dict[str, object]", replay_result_obj)
                assert replay_result["prior_complete"] is True
                assert replay_result["ticket_id"] == ticket_id
                assert replay_result["second_ticket"] is False
            finally:
                writer.close()
                await writer.wait_closed()
            gated = process.gate_invoke_until_transfer_complete(
                fp1=fp1,
                instance_id="inst-remote",
            )
            assert is_ok(gated), gated
            assert gated.value.transfer_gate_satisfied is True
            assert gated.value.instance_granted is False
            assert len(process.dest_artifacts.objects()) == 1
            source = process.artifacts.get(fp1)
            assert source is not None
            assert source.content == body
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_live_start_mission_invoke_gate(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-fix-invoke-gate")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            ticket_id, fp1, body = _issue_notified(process, command_id="cmd-invoke")
            _record_id, proof = await _pair_over_listener(process, host, port)
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={PAIRING_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "start_mission",
                        "params": {
                            "fp1": fp1,
                            "instance_id": "inst-remote",
                        },
                    },
                )
                await writer.drain()
                refused = await _ws_read_json(reader)
                assert "error" in refused, refused
                error_obj = refused["error"]
                assert isinstance(error_obj, dict)
                error = cast("dict[str, object]", error_obj)
                assert error["code"] == -32000
                data_obj = error["data"]
                assert isinstance(data_obj, dict)
                data = cast("dict[str, object]", data_obj)
                context_obj = data["context"]
                assert isinstance(context_obj, dict)
                context = cast("dict[str, object]", context_obj)
                assert context["ticket_complete"] is False
                assert context["local_fallback"] is False
                assert context["silent_local_fallback"] is False
                assert context["finish_on_local_disk"] is False
                redeemed = process.transfers.redeem_get(
                    ticket_id=ticket_id,
                    fp1=fp1,
                    credential_ref=_DEST_CRED,
                )
                assert is_ok(redeemed), redeemed
                placed = process.place_dest_pulled_bytes(body, ticket_id=ticket_id)
                assert is_ok(placed), placed
                completed = process.transfer_complete(
                    {
                        "ticket_id": ticket_id,
                        "fp1": fp1,
                        "byte_count": len(body),
                        "command_id": "cmd-invoke",
                    }
                )
                assert is_ok(completed), completed
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "start_mission",
                        "params": {
                            "fp1": fp1,
                            "instance_id": "inst-remote",
                        },
                    },
                )
                await writer.drain()
                admitted = await _ws_read_json(reader)
                assert "error" in admitted, admitted
                admitted_error_obj = admitted["error"]
                assert isinstance(admitted_error_obj, dict)
                admitted_error = cast("dict[str, object]", admitted_error_obj)
                assert admitted_error["code"] == -32601
                assert admitted_error["message"] == "method not found"
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())
