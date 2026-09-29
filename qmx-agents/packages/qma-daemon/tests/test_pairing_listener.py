"""Pairing HTTP/WS production wiring on the bound CT-40 listener."""

from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import cast

from qma.daemon.pairing import CT40_WS_SUBPROTOCOL, PairingWsHandle
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.auth import format_pairing_authorization
from qmf.core import is_ok

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
