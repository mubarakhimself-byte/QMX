"""MA03 versioned output states use the existing wire schema engine."""

from __future__ import annotations

from typing import Any

import pytest
from qma.wire.schemas import validate_instance
from qmf.core import is_ok, is_refusal


@pytest.mark.parametrize("state", ["ready", "empty", "stale", "unavailable", "failed"])
def test_read_state_contract(state: str) -> None:
    body: dict[str, Any] = {
        "schema": "qma.miniapp.read-state.v1",
        "state": state,
        "op_id": "qmb.analysis.project",
        "op_version": 1,
        "descriptor_fp1": "fp1:sha256:" + "1" * 64,
        "input_hash": "fp1:sha256:" + "2" * 64,
    }
    if state in {"ready", "stale"}:
        body["data"] = {"fp1": "fp1:sha256:" + "3" * 64, "kind": "saved-view", "body": {}}
    if state in {"stale", "unavailable", "failed"}:
        body["reason"] = "Owner data unavailable"
    assert is_ok(validate_instance(body, "miniapp_read_state"))
    if "data" in body:
        del body["data"]
    else:
        body["data"] = {"fp1": "fp1:sha256:" + "3" * 64, "kind": "saved-view", "body": {}}
    assert is_refusal(validate_instance(body, "miniapp_read_state"))


@pytest.mark.parametrize(
    "key,value",
    [("op_version", True), ("op_version", 0), ("grant_id", "forged"), ("state", "fabricated")],
)
def test_read_state_rejects_spoofed_fields(key: str, value: object) -> None:
    body = {
        "schema": "qma.miniapp.read-state.v1",
        "state": "empty",
        "op_id": "qmb.analysis.project",
        "op_version": 1,
        "descriptor_fp1": "pin",
        "input_hash": "pin",
        key: value,
    }
    assert is_refusal(validate_instance(body, "miniapp_read_state"))
