"""Configured supervisor preflight never manufactures runtime authority."""

from __future__ import annotations

import json
from pathlib import Path

from google.protobuf import descriptor_pb2
from qmf.core import fingerprint, is_ok, is_refusal
from qmf.venue.proto import descriptor_set_digest
from qmn.host.configured_runtime import assess_configured_runtime


def _deployment(root: Path, descriptor_path: Path | None, digest: str) -> Path:
    registry = root / "registry"
    registry.mkdir(exist_ok=True)
    as_of = fingerprint({"fixture": "registry-as-of"})
    assert is_ok(as_of)
    payload = {
        "format_version": 1,
        "machine": "fixture-machine",
        "registry_root": str(registry),
        "registry_as_of_fp1": as_of.value.value,
        "config_layers": {"roster_identity": {"roster_fp1": "fixture-roster"}},
        "roster": {
            "account_bindings": [],
            "sensing_only": [
                {
                    "venue_id": "fixture-venue",
                    "environment": "demo",
                    "account_id": "fixture-account",
                    "credential_reference": "secret://fixture",
                    "opaque_metric_id": "fixture-metric",
                    "world": "replay",
                }
            ],
            "protective_reserve_capacity": 1,
        },
        "proto": {
            "package_name": "openapi-proto-messages",
            "release_tag": 91,
            "descriptor_digest": digest,
            "descriptor_path": None if descriptor_path is None else str(descriptor_path),
        },
        "required_references": {
            "active_ct28": "ct28:fixture",
            "activation_evidence": "activation:fixture",
        },
    }
    path = root / "deployment.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_pinned_protocol_bytes_refuse_as_typed_stand_down(tmp_path: Path) -> None:
    path = _deployment(tmp_path, None, "sha256:" + "b" * 64)

    refused = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_refusal(refused)
    assert refused.context.get("failure_id") == "configured_runtime.proto_missing"


def test_valid_local_pins_remain_stand_down_without_admission(tmp_path: Path) -> None:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = descriptor_set_digest(raw)
    assert is_ok(digest)
    descriptor_path = tmp_path / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    path = _deployment(tmp_path, descriptor_path, digest.value)

    assessed = assess_configured_runtime(path, qmx_root=tmp_path)

    assert is_ok(assessed)
    assert assessed.value.stand_down
    assert assessed.value.stand_down_reason is not None
    assert assessed.value.activation_authorized is False
    assert assessed.value.provider_ready is False


def test_deployment_file_outside_operator_root_is_refused(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-deployment.json"
    outside.write_text("{}", encoding="utf-8")

    refused = assess_configured_runtime(outside, qmx_root=tmp_path)

    assert is_refusal(refused)
