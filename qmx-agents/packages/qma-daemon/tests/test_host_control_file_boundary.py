"""OS-owned local-control files must not turn a public call into token egress."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
from qma.daemon.host_control import (
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_FILE,
    ensure_host_control_token,
    host_control_call,
    read_host_control_bind,
    read_host_control_token,
    write_host_control_bind,
)
from qmf.core import RefusalCategory, TypedRefusal, is_ok, is_refusal


@pytest.mark.parametrize(
    ("host", "port"),
    [
        ("203.0.113.4", 23456),
        ("example.invalid", 23456),
        ("::", 23456),
        ("127.0.0.1", 65536),
        ("127.0.0.1", True),
        ("127.0.0.1", 8765),
    ],
)
def test_invalid_bind_refuses_before_opening_socket_or_transmitting_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    host: str,
    port: int,
) -> None:
    held = ensure_host_control_token(tmp_path)
    assert is_ok(held)
    bind = tmp_path / HOST_CONTROL_BIND_NAME
    bind.write_text(json.dumps({"host": host, "port": port}), encoding="utf-8")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    calls: list[object] = []

    def unexpected_connection(*args: object, **kwargs: object) -> socket.socket:
        calls.append((args, kwargs))
        raise AssertionError("invalid bind reached network boundary")

    monkeypatch.setattr(socket, "create_connection", unexpected_connection)
    result = host_control_call(tmp_path, "status")
    assert is_refusal(result), result
    assert result.category in {RefusalCategory.POLICY_REJECTION, RefusalCategory.INVALID_INPUT}
    assert held.value not in str(result)
    assert calls == []
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


@pytest.mark.parametrize(("host", "port"), [("203.0.113.4", 12), ("127.0.0.1", 65536)])
def test_invalid_bind_writer_preserves_last_valid_address(
    tmp_path: Path, host: str, port: int
) -> None:
    assert is_ok(write_host_control_bind(tmp_path, host="127.0.0.1", port=23456))
    before = (tmp_path / HOST_CONTROL_BIND_NAME).read_bytes()
    result = write_host_control_bind(tmp_path, host=host, port=port)
    assert is_refusal(result), result
    assert (tmp_path / HOST_CONTROL_BIND_NAME).read_bytes() == before
    readback = read_host_control_bind(tmp_path)
    assert is_ok(readback) and readback.value == ("127.0.0.1", 23456)


@pytest.mark.parametrize("name", [HOST_CONTROL_FILE, HOST_CONTROL_BIND_NAME])
def test_corrupt_utf8_control_file_is_typed_storage_refusal(tmp_path: Path, name: str) -> None:
    path = tmp_path / name
    path.write_bytes(b"\xff")
    before = path.read_bytes()
    result = (
        read_host_control_token(tmp_path)
        if name == HOST_CONTROL_FILE
        else read_host_control_bind(tmp_path)
    )
    assert isinstance(result, TypedRefusal), result
    assert result.category is RefusalCategory.STORAGE_FAILURE
    assert result.context["field"] == name
    assert path.read_bytes() == before
    if name == HOST_CONTROL_FILE:
        minted = ensure_host_control_token(tmp_path)
        assert is_refusal(minted), minted
        assert path.read_bytes() == before


@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_legal_loopback_addresses_roundtrip_without_authority_expansion(
    tmp_path: Path, host: str
) -> None:
    assert is_ok(write_host_control_bind(tmp_path, host=host, port=23456))
    actual = read_host_control_bind(tmp_path)
    assert is_ok(actual) and actual.value == (host, 23456)
