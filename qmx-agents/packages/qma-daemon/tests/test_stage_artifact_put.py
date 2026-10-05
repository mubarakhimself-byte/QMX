"""Story 70.1 — authenticated PUT /artifacts/stage on the bound listener."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import struct
from collections.abc import Mapping
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from qma.core.vocabulary.enums import ArtifactCompleteness
from qma.daemon.artifacts import (
    ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA,
    ArtifactStore,
    claim_stage_artifact_put_existed_at_inspect_sha,
    handle_stage_artifact_put,
)
from qma.daemon.host_control import host_control_call
from qma.daemon.journal.clock import InjectedUtcClock
from qma.daemon.journal.variables import (
    ARTIFACT_STAGE_MAX_BYTES_KEY,
    ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
    GovernedVariableRegistry,
)
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.auth import format_pairing_authorization
from qma.wire.initialize import PAIRING_CAPABILITY, WIRE_PROTOCOL_VERSION
from qma.wire.stage_artifact import STAGE_ARTIFACT_CAPABILITY, STAGE_ARTIFACT_HTTP_PATH
from qmf.core import Instant, Ok, Result, is_ok, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
from qmf.core.refusal import RefusalCategory
from qmf.data.store.journal import JournalStore
from qmf.data.store.refusals import storage_failure

_ORIGIN = "http://127.0.0.1:5173"
_FIXTURE_TTL = "PT15M"
_PROCESS_SRC = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "process.py"
_ARTIFACTS_ROOT = Path(__file__).resolve().parents[1] / "src" / "qma" / "daemon" / "artifacts"


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


def _refusal_context(body: bytes) -> dict[str, object]:
    payload = _json_object(body)
    refusal_obj = payload["refusal"]
    assert isinstance(refusal_obj, dict)
    refusal = cast("dict[str, object]", refusal_obj)
    context_obj = refusal["context"]
    assert isinstance(context_obj, dict)
    return cast("dict[str, object]", context_obj)


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


def _inject_stage_max(process: DaemonProcess, value: int) -> None:
    written = process.variables.variable_set(
        ARTIFACT_STAGE_MAX_BYTES_KEY,
        value,
        principal_class="operator",
        journal=process.journal,
    )
    assert is_ok(written), written


def _bearer(proof: str) -> str:
    auth = format_pairing_authorization(proof)
    assert is_ok(auth), auth
    return auth.value


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


def test_gap_0110_builtin_row_mints_no_number() -> None:
    registry = GovernedVariableRegistry.with_builtins()
    row = registry.get(ARTIFACT_STAGE_MAX_BYTES_KEY)
    assert is_ok(row)
    assert row.value.default is None
    assert row.value.registry_key == ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY
    missing = registry.artifact_stage_max_bytes()
    assert is_refusal(missing)
    assert missing.category is RefusalCategory.POLICY_REJECTION
    assert missing.context["wrote_object"] is False


def test_library_put_reuses_fp1_and_claims_inspect_absence() -> None:
    assert ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA is False
    assert is_refusal(claim_stage_artifact_put_existed_at_inspect_sha(True))
    store = ArtifactStore()
    body = b"stage-bytes"
    first = handle_stage_artifact_put(
        store,
        body,
        content_length=len(body),
        max_bytes=1024,
        capabilities={STAGE_ARTIFACT_CAPABILITY: True},
    )
    assert is_ok(first)
    assert first.value.fp1 == fingerprint_bytes(body).value
    assert first.value.byte_count == len(body)
    assert first.value.completeness == ArtifactCompleteness.COMPLETE.value
    assert first.value.reused is False
    payload = dict(first.value.to_payload())
    assert payload["local_complete"] is True
    assert "app_instance_id" not in payload
    assert "upload_bytes" not in payload
    assert "local_path" not in payload
    second = handle_stage_artifact_put(
        store,
        body,
        content_length=len(body),
        max_bytes=1024,
        capabilities={STAGE_ARTIFACT_CAPABILITY: True},
    )
    assert is_ok(second)
    assert second.value.fp1 == first.value.fp1
    assert second.value.reused is True
    assert len(store.objects()) == 1
    missing = handle_stage_artifact_put(
        store,
        body,
        content_length=len(body),
        max_bytes=None,
        capabilities={STAGE_ARTIFACT_CAPABILITY: True},
    )
    assert is_refusal(missing)
    assert missing.context["wrote_object"] is False


def test_listener_wires_put_not_library_only() -> None:
    text = _PROCESS_SRC.read_text(encoding="utf-8")
    assert "handle_stage_artifact_put" in text
    assert "_serve_stage_artifact_put" in text
    assert "STAGE_ARTIFACT_HTTP_PATH" in text
    assert "_MAX_HTTP_BODY" in text
    for path in _ARTIFACTS_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "write_text" not in source
        assert "Path.write_text" not in source


def test_live_put_stage_is_local_complete_possession(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-1-live-put")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            missing_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=b"too-soon",
                ),
            )
            missing_status, _missing_headers, missing_body = _split_http(missing_raw)
            assert missing_status in {400, 403}, missing_raw
            missing_ctx = _refusal_context(missing_body)
            assert missing_ctx["registry_key"] == ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY
            assert missing_ctx["wrote_object"] is False
            assert process.artifacts.objects() == ()

            _inject_stage_max(process, 131072)
            payload = b"local-complete-bytes"
            expected_fp1 = fingerprint_bytes(payload).value
            put_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=payload,
                ),
            )
            status, headers, body = _split_http(put_raw)
            assert status == 200, put_raw
            assert headers.get("access-control-allow-origin") == _ORIGIN
            assert headers.get("access-control-allow-origin") != "*"
            listed = _json_object(body)
            assert listed["ok"] is True
            result = listed["result"]
            assert isinstance(result, dict)
            assert result["fp1"] == expected_fp1
            assert result["byte_count"] == len(payload)
            assert result["completeness"] == ArtifactCompleteness.COMPLETE.value
            assert result["local_complete"] is True
            assert "app_instance_id" not in result
            held = process.artifacts.get(expected_fp1)
            assert held is not None
            assert held.content == payload
            assert proof not in body.decode("utf-8")

            reuse_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=payload,
                ),
            )
            reuse_status, _reuse_headers, reuse_body = _split_http(reuse_raw)
            assert reuse_status == 200, reuse_raw
            reused = _json_object(reuse_body)
            reuse_result = reused["result"]
            assert isinstance(reuse_result, dict)
            assert reuse_result["fp1"] == expected_fp1
            assert len(process.artifacts.objects()) == 1

            oversized = b"x" * 65537
            big_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=oversized,
                ),
            )
            big_status, _big_headers, big_body = _split_http(big_raw)
            assert big_status == 200, big_raw
            big = _json_object(big_body)
            big_result = big["result"]
            assert isinstance(big_result, dict)
            assert big_result["byte_count"] == len(oversized)
            assert big_result["fp1"] == fingerprint_bytes(oversized).value
            assert big_result["completeness"] == ArtifactCompleteness.COMPLETE.value
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_live_put_refuses_unauthenticated_oversize_and_options(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-1-refuse")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            record_id, proof = await _pair_over_listener(process, host, port)
            _inject_stage_max(process, 16)
            options_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "OPTIONS",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={
                        "Origin": _ORIGIN,
                        "Access-Control-Request-Method": "PUT",
                    },
                ),
            )
            options_status, options_headers, options_body = _split_http(options_raw)
            assert options_status == 204
            assert options_body == b""
            assert options_headers.get("access-control-allow-origin") == _ORIGIN
            assert options_headers.get("access-control-allow-origin") != "*"
            assert "upgrade" not in options_headers
            assert "set-cookie" not in options_headers
            assert "pairing_proof" not in options_body.decode("ascii")

            unauth = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN},
                    body=b"no-auth",
                ),
            )
            unauth_status, _unauth_headers, _unauth_body = _split_http(unauth)
            assert unauth_status in {401, 403}
            assert process.artifacts.objects() == ()

            as_id = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={
                        "Origin": _ORIGIN,
                        "Authorization": f"Bearer pairing:{record_id}",
                    },
                    body=b"as-id",
                ),
            )
            as_id_status, _as_id_headers, _as_id_body = _split_http(as_id)
            assert as_id_status in {400, 401, 403}
            assert process.artifacts.objects() == ()

            unpaired = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={
                        "Origin": "http://127.0.0.1:9",
                        "Authorization": _bearer(proof),
                    },
                    body=b"unpaired",
                ),
            )
            unpaired_status, _unpaired_headers, _unpaired_body = _split_http(unpaired)
            assert unpaired_status in {401, 403}
            assert process.artifacts.objects() == ()

            oversize = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={
                        "Origin": _ORIGIN,
                        "Authorization": _bearer(proof),
                        "Content-Length": "32",
                    },
                ),
            )
            oversize_status, _oversize_headers, oversize_body = _split_http(oversize)
            assert oversize_status in {400, 403}, oversize
            oversize_ctx = _refusal_context(oversize_body)
            assert oversize_ctx["wrote_object"] is False
            assert process.artifacts.objects() == ()

            missing_cl = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                ),
            )
            missing_status, _missing_headers, missing_body = _split_http(missing_cl)
            assert missing_status in {400, 403}
            missing_ctx = _refusal_context(missing_body)
            assert missing_ctx["wrote_object"] is False
            assert "Content-Length" in str(missing_ctx["reason"])
            assert process.artifacts.objects() == ()

            revoked = process.pair_revoke(pairing_record_id=record_id)
            assert is_ok(revoked), revoked
            after = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=b"revoked",
                ),
            )
            after_status, _after_headers, _after_body = _split_http(after)
            assert after_status in {401, 403}
            assert process.artifacts.objects() == ()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_interrupted_put_deletes_incomplete_bytes(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-1-interrupt")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            _inject_stage_max(process, 4096)
            reader, writer = await asyncio.open_connection(host, port)
            try:
                writer.write(
                    _http_bytes(
                        "PUT",
                        STAGE_ARTIFACT_HTTP_PATH,
                        headers={
                            "Origin": _ORIGIN,
                            "Authorization": _bearer(proof),
                            "Content-Length": "64",
                        },
                        body=b"partial",
                    )
                )
                await writer.drain()
                if writer.can_write_eof():
                    writer.write_eof()
                raw = await asyncio.wait_for(reader.read(), timeout=5.0)
            finally:
                writer.close()
                await writer.wait_closed()
            assert process.artifacts.objects() == ()
            if raw:
                status, _headers, body = _split_http(raw)
                assert status in {400, 403}
                ctx = _refusal_context(body)
                assert ctx["wrote_object"] is False
                assert "interrupted" in str(ctx["reason"])
                assert ctx.get("completeness") == ArtifactCompleteness.PARTIAL.value
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_jsonrpc_stage_artifact_refused_on_live_ws(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-1-jsonrpc")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={STAGE_ARTIFACT_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                result_obj = init_resp["result"]
                assert isinstance(result_obj, dict)
                result = cast("dict[str, object]", result_obj)
                caps_obj = result["capabilities"]
                assert isinstance(caps_obj, dict)
                caps = cast("dict[str, object]", caps_obj)
                assert caps.get(STAGE_ARTIFACT_CAPABILITY) is True
                _ws_write(
                    writer,
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": STAGE_ARTIFACT_CAPABILITY,
                        "params": {},
                    },
                )
                await writer.drain()
                refused = await _ws_read_json(reader)
                error_obj = refused["error"]
                assert isinstance(error_obj, dict)
                error = cast("dict[str, object]", error_obj)
                data_obj = error["data"]
                assert isinstance(data_obj, dict)
                data = cast("dict[str, object]", data_obj)
                context_obj = data["context"]
                assert isinstance(context_obj, dict)
                context = cast("dict[str, object]", context_obj)
                assert context["jsonrpc_stage_artifact"] is False
                assert context["http_put"] == STAGE_ARTIFACT_HTTP_PATH
                assert process.artifacts.objects() == ()
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_initialize_omit_stage_artifact_refuses_put(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-1-omit-cap")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            _inject_stage_max(process, 1024)
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                omitted = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={"list_mailbox": True},
                )
                assert "error" not in omitted, omitted
                omit_result = omitted["result"]
                assert isinstance(omit_result, dict)
                omit_caps = cast("dict[str, object]", omit_result)
                advertised_obj = omit_caps["capabilities"]
                assert isinstance(advertised_obj, dict)
                advertised = cast("dict[str, object]", advertised_obj)
                assert advertised.get(STAGE_ARTIFACT_CAPABILITY) is not True
            finally:
                writer.close()
                await writer.wait_closed()
            put_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=b"cap-miss",
                ),
            )
            status, _headers, body = _split_http(put_raw)
            assert status in {400, 403}, put_raw
            ctx = _refusal_context(body)
            assert ctx["missing"] == STAGE_ARTIFACT_CAPABILITY
            assert ctx["empty_upload"] is False
            assert process.artifacts.objects() == ()
        finally:
            await process.aclose()

    asyncio.run(_run())


def test_initialize_pairing_only_then_put_stage(tmp_path: Path) -> None:
    async def _run() -> None:
        process = _compose(tmp_path, boot="boot-70-fix-home-put")
        try:
            bound = await process.bind()
            assert is_ok(bound), bound
            host = bound.value.host
            port = bound.value.port
            _record_id, proof = await _pair_over_listener(process, host, port)
            _inject_stage_max(process, 1024)
            reader, writer = await _upgrade_paired_ws(host, port, proof)
            try:
                init_resp = await _initialize_ws(
                    writer,
                    reader,
                    capabilities={PAIRING_CAPABILITY: True},
                )
                assert "error" not in init_resp, init_resp
                result_obj = init_resp["result"]
                assert isinstance(result_obj, dict)
                result = cast("dict[str, object]", result_obj)
                caps_obj = result["capabilities"]
                assert isinstance(caps_obj, dict)
                caps = cast("dict[str, object]", caps_obj)
                assert caps.get(PAIRING_CAPABILITY) is True
                assert caps.get(STAGE_ARTIFACT_CAPABILITY) is True
            finally:
                writer.close()
                await writer.wait_closed()
            payload = b"home-put-bytes"
            put_raw = await _exchange(
                host,
                port,
                _http_bytes(
                    "PUT",
                    STAGE_ARTIFACT_HTTP_PATH,
                    headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    body=payload,
                ),
            )
            status, _headers, body = _split_http(put_raw)
            assert status == 200, put_raw
            listed = _json_object(body)
            result_obj = listed["result"]
            assert isinstance(result_obj, dict)
            result = cast("dict[str, object]", result_obj)
            fp1 = result["fp1"]
            assert isinstance(fp1, str)
            assert fp1 == fingerprint_bytes(payload).value
            assert result["local_complete"] is True
            held = process.artifacts.get(fp1)
            assert held is not None
            assert held.content == payload
        finally:
            await process.aclose()

    asyncio.run(_run())


def _assert_host_refusal(reply: Result[Mapping[str, object]]) -> None:
    assert is_ok(reply), reply
    assert reply.value["ok"] is False, reply


def _assert_cap(process: DaemonProcess, expected: int) -> None:
    cap = process.variables.artifact_stage_max_bytes()
    assert is_ok(cap) and cap.value == expected


def _cap_receipts(process: DaemonProcess) -> list[object]:
    rows = process.journal.read_events()
    assert is_ok(rows)
    return [
        e
        for e in rows.value
        if e.event == "variable.set" and e.payload.get("name") == ARTIFACT_STAGE_MAX_BYTES_KEY
    ]


def test_local_cap_config_restart_and_upload_boundary(tmp_path: Path) -> None:
    async def run() -> None:
        process = _compose(tmp_path, boot="cap-first")
        try:
            bound = await process.bind()
            assert is_ok(bound)
            host, port = bound.value.host, bound.value.port
            _, proof = await _pair_over_listener(process, host, port)

            async def put(body: bytes) -> tuple[int, dict[str, str], bytes]:
                return _split_http(
                    await _exchange(
                        host,
                        port,
                        _http_bytes(
                            "PUT",
                            "/artifacts/stage",
                            body=body,
                            headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                        ),
                    )
                )

            assert (await put(b"fresh"))[0] == 403
            assert process.artifacts.objects() == ()
            for value in [True, -1, 1.5, "16", None]:
                refused = await asyncio.to_thread(
                    host_control_call,
                    tmp_path,
                    "configure",
                    fields={"target": "artifact-stage-max-bytes", "max_bytes": value},
                )
                _assert_host_refusal(refused)
            for fields in [
                {"target": "unknown", "max_bytes": 16},
                {"target": "artifact-stage-max-bytes", "max_bytes": 16, "key": "other"},
            ]:
                _assert_host_refusal(
                    await asyncio.to_thread(host_control_call, tmp_path, "configure", fields=fields)
                )
            assert _cap_receipts(process) == []
            for token in ["wrong", "pairing:" + proof]:
                _assert_host_refusal(
                    await asyncio.to_thread(
                        host_control_call,
                        tmp_path,
                        "configure",
                        fields={"target": "artifact-stage-max-bytes", "max_bytes": 16},
                        token=token,
                    )
                )
            configured = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={"target": "artifact-stage-max-bytes", "max_bytes": 16},
            )
            assert is_ok(configured) and configured.value["ok"] is True
            for body in [b"below", b"x" * 16]:
                status, _, raw = await put(body)
                assert status == 200
                assert json.loads(raw)["result"]["fp1"] == fingerprint_bytes(body).value
            assert (await put(b"x" * 17))[0] == 403
            assert len(process.artifacts.objects()) == 2
            changed = await asyncio.to_thread(
                host_control_call,
                tmp_path,
                "configure",
                fields={"target": "artifact-stage-max-bytes", "max_bytes": 8},
            )
            assert is_ok(changed) and changed.value["ok"] is True
            receipts = _cap_receipts(process)
            assert len(receipts) == 2
        finally:
            await process.aclose()
        # Stale file setup is not a cap writer, and cannot override the journal.
        (tmp_path / "operator-config.json").write_text(
            json.dumps({"artifact_stage_max_bytes": 999})
        )
        reopened = _compose(tmp_path, boot="cap-reopened")
        try:
            _assert_cap(reopened, 8)
            assert _cap_receipts(reopened) == receipts
            bound = await reopened.bind()
            assert is_ok(bound)
            for body, expected_status in [(b"y" * 8, 200), (b"y" * 9, 403)]:
                raw = await _exchange(
                    bound.value.host,
                    bound.value.port,
                    _http_bytes(
                        "PUT",
                        "/artifacts/stage",
                        body=body,
                        headers={"Origin": _ORIGIN, "Authorization": _bearer(proof)},
                    ),
                )
                assert _split_http(raw)[0] == expected_status
        finally:
            await reopened.aclose()

    asyncio.run(run())


def test_failed_journal_write_does_not_change_cap(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="cap-write-failure")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        process.journal.close()
        assert is_refusal(process.configure_artifact_stage_max_bytes(32))
        _assert_cap(process, 16)
    finally:
        process.close()


@pytest.mark.parametrize("value", [True, -1, "16"])
def test_invalid_latest_journal_cap_refuses_reopen(tmp_path: Path, value: object) -> None:
    process = _compose(tmp_path, boot="cap-invalid")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        assert is_ok(
            process.variables.variable_set(
                ARTIFACT_STAGE_MAX_BYTES_KEY,
                value,
                principal_class="operator",
                journal=process.journal,
            )
        )
    finally:
        process.close()
    from qma.daemon.plugins import research_corpus_plugin_load_config

    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="cap-invalid-reopen",
        bind_port=0,
        plugin_load_configs=research_corpus_plugin_load_config(tmp_path / "seed-corpus"),
    )
    assert is_refusal(result)


def test_zero_and_operator_only_registry_boundary(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="cap-zero")
    try:
        for principal in ["machine", "agent"]:
            assert is_refusal(
                process.variables.variable_set(
                    ARTIFACT_STAGE_MAX_BYTES_KEY,
                    16,
                    principal_class=principal,
                    journal=process.journal,
                )
            )
        assert is_refusal(
            process.variables.variable_set(
                "pairing.session_ttl", "PT15M", principal_class="operator", journal=process.journal
            )
        )
        assert is_ok(process.configure_artifact_stage_max_bytes(0))
    finally:
        process.close()
    reopened = _compose(tmp_path, boot="cap-zero-reopen")
    try:
        _assert_cap(reopened, 0)
    finally:
        reopened.close()


def _fixture_wall_now(nanoseconds: int) -> Ok[Instant]:
    instant = Instant.try_create(nanoseconds)
    assert is_ok(instant)
    return Ok(instant.value)


@pytest.mark.parametrize(
    "times",
    [
        (200_000_000_000, 100_000_000_000, 50_000_000_000),
        (200_000_000_000, 200_000_000_000, 200_000_000_000),
    ],
)
def test_cap_restart_uses_journal_sequence_across_clock_steps(
    tmp_path: Path, times: tuple[int, int, int]
) -> None:
    process = _compose(tmp_path, boot="cap-clock-order")
    try:
        for value, wall in zip((16, 8), times[:2], strict=True):
            with patch.object(InjectedUtcClock, "wall_now", return_value=_fixture_wall_now(wall)):
                assert is_ok(process.configure_artifact_stage_max_bytes(value))
        _assert_cap(process, 8)
        before = _cap_receipts(process)
    finally:
        process.close()
    reopened = _compose(tmp_path, boot="cap-clock-reopen")
    try:
        _assert_cap(reopened, 8)
        assert _cap_receipts(reopened) == before
        with patch.object(InjectedUtcClock, "wall_now", return_value=_fixture_wall_now(times[2])):
            assert is_ok(reopened.configure_artifact_stage_max_bytes(0))
        before_zero = _cap_receipts(reopened)
        rows = reopened.journal.read_events()
        assert is_ok(rows)
        caps = [
            e
            for e in rows.value
            if e.event == "variable.set" and e.payload.get("name") == ARTIFACT_STAGE_MAX_BYTES_KEY
        ]
        assert [e.recorded_at for e in caps] == list(times)
        assert [e.journal_seq for e in caps] == sorted(e.journal_seq for e in caps)
    finally:
        reopened.close()
    zero = _compose(tmp_path, boot="cap-clock-zero")
    try:
        _assert_cap(zero, 0)
        assert _cap_receipts(zero) == before_zero
    finally:
        zero.close()


@pytest.mark.parametrize("value", [True, -1, "16"])
@pytest.mark.parametrize("latest_wall", [100_000_000_000, 200_000_000_000])
def test_invalid_highest_sequence_cap_refuses_repeat_restart(
    tmp_path: Path, value: object, latest_wall: int
) -> None:
    process = _compose(tmp_path, boot="cap-clock-invalid")
    try:
        with patch.object(
            InjectedUtcClock, "wall_now", return_value=_fixture_wall_now(200_000_000_000)
        ):
            assert is_ok(process.configure_artifact_stage_max_bytes(16))
        with patch.object(
            InjectedUtcClock, "wall_now", return_value=_fixture_wall_now(latest_wall)
        ):
            assert is_ok(
                process.variables.variable_set(
                    ARTIFACT_STAGE_MAX_BYTES_KEY,
                    value,
                    principal_class="operator",
                    journal=process.journal,
                )
            )
        assert is_refusal(process.variables.artifact_stage_max_bytes())
    finally:
        process.close()
    for _ in range(2):
        result = DaemonProcess.compose(
            tmp_path,
            machine="test-host",
            boot_epoch_id="invalid-retry",
            bind_port=0,
            plugin_load_configs=_seed_configs(tmp_path),
        )
        assert is_refusal(result) and result.category is RefusalCategory.INVALID_INPUT
        assert result.context["registry_key"] == ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY


@pytest.mark.parametrize(
    "field,bad",
    [("scope", "desk"), ("home", "record"), ("registry_key", "registry:other"), ("name", "other")],
)
def test_selected_cap_receipt_metadata_cannot_restore_global_value(
    tmp_path: Path, field: str, bad: str
) -> None:
    process = _compose(tmp_path, boot="cap-metadata")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        payload: dict[str, object] = {
            "name": ARTIFACT_STAGE_MAX_BYTES_KEY,
            "registry_key": ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
            "value": 8,
            "home": "registry",
            "scope": "global",
        }
        payload[field] = bad
        assert is_ok(process.journal.append_event("variable.set", payload=payload))
        assert is_refusal(process.variables.restore_artifact_stage_max_bytes(process.journal))
        _assert_cap(process, 16)
    finally:
        process.close()


def test_scoped_cap_receipt_cannot_restore_global_value(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="cap-wrong-scope")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        assert is_ok(
            process.variables.variable_set(
                ARTIFACT_STAGE_MAX_BYTES_KEY,
                8,
                principal_class="operator",
                journal=process.journal,
                scope_path=[{"kind": "desk", "id": "test-desk"}],
            )
        )
        assert is_refusal(process.variables.restore_artifact_stage_max_bytes(process.journal))
    finally:
        process.close()
    result = DaemonProcess.compose(
        tmp_path,
        machine="test-host",
        boot_epoch_id="scope-reopen",
        bind_port=0,
        plugin_load_configs=_seed_configs(tmp_path),
    )
    assert is_refusal(result)


@pytest.mark.parametrize(
    "field,bad",
    [("payload", []), ("scope_path", "invalid"), ("journal_seq", True), ("journal_seq", 0)],
)
def test_malformed_cap_event_read_refuses_without_registry_mutation(
    tmp_path: Path, field: str, bad: object
) -> None:
    process = _compose(tmp_path, boot="cap-corrupt-shape")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        rows = process.journal.read_all()
        assert is_ok(rows)
        altered = [dict(row) for row in rows.value]
        altered[-1][field] = bad
        with patch.object(JournalStore, "read_stream", return_value=Ok(altered)):
            assert is_refusal(process.variables.restore_artifact_stage_max_bytes(process.journal))
        _assert_cap(process, 16)
    finally:
        process.close()


def test_cap_restore_propagates_journal_storage_refusal(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="cap-read-failure")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        refusal = storage_failure("injected unreadable journal")
        with patch.object(JournalStore, "read_stream", return_value=refusal):
            assert process.variables.restore_artifact_stage_max_bytes(process.journal) == refusal
        _assert_cap(process, 16)
    finally:
        process.close()


def test_stage_cap_storage_append_refusal_preserves_value_receipts_and_sequence(
    tmp_path: Path,
) -> None:
    process = _compose(tmp_path, boot="cap-append-failure")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        before = _cap_receipts(process)
        next_sequence = process.journal.next_journal_seq
        refusal = storage_failure("injected append storage failure")
        with patch.object(JournalStore, "append", return_value=refusal):
            assert process.configure_artifact_stage_max_bytes(8) == refusal
        _assert_cap(process, 16)
        assert _cap_receipts(process) == before
        assert process.journal.next_journal_seq == next_sequence
    finally:
        process.close()


def test_duplicate_cap_journal_sequence_refuses_ambiguous_replay(tmp_path: Path) -> None:
    process = _compose(tmp_path, boot="cap-duplicate-sequence")
    try:
        assert is_ok(process.configure_artifact_stage_max_bytes(16))
        assert is_ok(process.configure_artifact_stage_max_bytes(8))
        rows = process.journal.read_all()
        assert is_ok(rows)
        altered = [dict(row) for row in rows.value]
        altered[-1]["journal_seq"] = altered[-2]["journal_seq"]
        with patch.object(JournalStore, "read_stream", return_value=Ok(altered)):
            assert is_refusal(process.variables.restore_artifact_stage_max_bytes(process.journal))
        _assert_cap(process, 8)
    finally:
        process.close()
