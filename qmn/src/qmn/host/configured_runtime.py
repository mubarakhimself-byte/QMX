"""Operator-pinned configured-runtime preflight for the supervised QMN process.

This loader reads only deployment references and configuration.  It does not
mint activation authority, open provider connections, or make a roster eligible.
Missing or mismatched pinned protocol artifacts are ordinary typed stand-down
conditions.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qmf.core import Fingerprint, Ok, Result, is_refusal
from qmf.venue.proto import compile_descriptor_set

from qmn.config.compiler import ResolvedNodeConfig, compile_node_config
from qmn.config.roster import RosterRuntimeComposition, compose_roster_runtime
from qmn.host._refuse import clean_token, invalid, policy, unavailable

__all__ = [
    "CONFIGURED_RUNTIME_FORMAT_VERSION",
    "ConfiguredRuntimeAssessment",
    "assess_configured_runtime",
]

CONFIGURED_RUNTIME_FORMAT_VERSION: Final[int] = 1
_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "format_version",
        "machine",
        "registry_root",
        "registry_as_of_fp1",
        "config_layers",
        "roster",
        "proto",
        "required_references",
    }
)
_LAYER_KEYS: Final[frozenset[str]] = frozenset(
    {"roster", "bms", "book", "node_defaults", "roster_identity", "config_version"}
)
_ROSTER_KEYS: Final[frozenset[str]] = frozenset(
    {"account_bindings", "sensing_only", "protective_reserve_capacity"}
)
_PROTO_KEYS: Final[frozenset[str]] = frozenset(
    {"package_name", "release_tag", "descriptor_digest", "descriptor_path"}
)


@dataclass(frozen=True, slots=True)
class ConfiguredRuntimeAssessment:
    """Validated operator configuration and the current fail-closed verdict."""

    machine: str
    registry_as_of: Fingerprint
    node_config: ResolvedNodeConfig
    roster: RosterRuntimeComposition
    descriptor_digest: str
    stand_down_reason: str | None
    activation_authorized: bool = False
    provider_ready: bool = False

    @property
    def stand_down(self) -> bool:
        return self.stand_down_reason is not None


def assess_configured_runtime(
    deployment_path: object,
    *,
    qmx_root: object,
) -> Result[ConfiguredRuntimeAssessment]:
    """Load, type-check and preflight one operator-pinned deployment document.

    Successful assessment only means its local declarations were parsed and
    compiled.  A missing protocol artifact returns an assessment that explicitly
    remains stand-down; an artifact on disk is compiled and digest checked, but
    this function never performs admission, activation or provider readiness.
    """
    path = _absolute_path(deployment_path, "deployment_path")
    if is_refusal(path):
        return path
    root = _absolute_path(qmx_root, "qmx_root")
    if is_refusal(root):
        return root
    try:
        resolved_root = root.value.resolve(strict=True)
        resolved_path = path.value.resolve(strict=True)
        resolved_path.relative_to(resolved_root)
        raw_bytes = resolved_path.read_bytes()
    except (OSError, ValueError):
        return unavailable(
            "deployment_file",
            "the operator-pinned deployment file is readable beneath QMX_ROOT",
        )
    try:
        payload = json.loads(raw_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return invalid("deployment_file", "the configured deployment is valid UTF-8 JSON")
    if not isinstance(payload, Mapping):
        return invalid("deployment_file", "the configured deployment is a JSON object")
    body = cast("Mapping[str, object]", payload)
    keys = frozenset(body.keys())
    if keys != _TOP_LEVEL_KEYS:
        return invalid(
            "deployment_file",
            "the deployment has exactly the versioned configured-runtime fields",
            missing=sorted(_TOP_LEVEL_KEYS - keys),
            unknown=sorted(keys - _TOP_LEVEL_KEYS),
        )
    version = body.get("format_version")
    if type(version) is not int or version != CONFIGURED_RUNTIME_FORMAT_VERSION:
        return invalid("format_version", "configured-runtime format version is 1")

    machine = clean_token(body.get("machine"))
    if machine is None:
        return invalid("machine", "machine is the exact operator-pinned machine identity")
    as_of = Fingerprint.try_create(body.get("registry_as_of_fp1"))
    if is_refusal(as_of):
        return as_of
    if not isinstance(body.get("registry_root"), str):
        return invalid("registry_root", "registry_root is an operator-pinned path reference")
    registry_root = Path(cast("str", body["registry_root"]))
    if not registry_root.is_absolute():
        return invalid("registry_root", "registry_root is an absolute evidence-root reference")
    if not registry_root.is_dir():
        return unavailable(
            "registry_root",
            "the pinned registry evidence root is present and readable",
        )

    layers = _mapping(body.get("config_layers"), "config_layers", _LAYER_KEYS)
    if is_refusal(layers):
        return layers
    config_version = layers.value.get("config_version", 1)
    if type(config_version) is not int:
        return invalid("config_version", "config_version is a positive integer")
    compiled = compile_node_config(
        roster=layers.value.get("roster"),
        bms=layers.value.get("bms"),
        book=layers.value.get("book"),
        node_defaults=layers.value.get("node_defaults"),
        roster_identity=layers.value.get("roster_identity"),
        config_version=config_version,
    )
    if is_refusal(compiled):
        return compiled

    roster_decl = _mapping(body.get("roster"), "roster", _ROSTER_KEYS)
    if is_refusal(roster_decl):
        return roster_decl
    roster = compose_roster_runtime(
        account_bindings=roster_decl.value.get("account_bindings"),
        sensing_only=roster_decl.value.get("sensing_only"),
        protective_reserve_capacity=roster_decl.value.get("protective_reserve_capacity"),
    )
    if is_refusal(roster):
        return roster

    references = body.get("required_references")
    if not isinstance(references, Mapping) or not references:
        return invalid(
            "required_references",
            "deployment references name exact registered CT-28 and activation evidence",
        )
    reference_body = cast("Mapping[object, object]", references)
    for key, value in reference_body.items():
        if clean_token(key) is None or clean_token(value) is None:
            return invalid(
                "required_references",
                "each required artifact and activation cite is a non-blank reference",
            )

    proto = _mapping(body.get("proto"), "proto", _PROTO_KEYS)
    if is_refusal(proto):
        return proto
    package_name = clean_token(proto.value.get("package_name"))
    digest = clean_token(proto.value.get("descriptor_digest"))
    release_tag = proto.value.get("release_tag")
    descriptor_path = proto.value.get("descriptor_path")
    if package_name is None or digest is None:
        return invalid("proto", "the protocol package and descriptor digest are pinned")
    if type(release_tag) is not int or release_tag <= 0:
        return invalid("proto.release_tag", "the protocol release tag is a positive integer")
    if not isinstance(descriptor_path, str) or not descriptor_path:
        return unavailable(
            "proto_descriptor",
            "pinned protocol descriptor bytes are absent; configured runtime remains stand-down",
            failure_id="configured_runtime.proto_missing",
        )
    descriptor = Path(descriptor_path)
    if not descriptor.is_absolute():
        return invalid("proto.descriptor_path", "protocol descriptor path is absolute")
    try:
        descriptor_bytes = descriptor.read_bytes()
    except OSError:
        return unavailable(
            "proto_descriptor",
            "pinned protocol descriptor bytes are absent; configured runtime remains stand-down",
            failure_id="configured_runtime.proto_missing",
        )
    compiled_proto = compile_descriptor_set(
        descriptor_bytes,
        package_name=package_name,
        release_tag=release_tag,
    )
    if is_refusal(compiled_proto):
        return compiled_proto
    if compiled_proto.value.artifact.descriptor_set_digest != digest:
        return policy(
            "proto_descriptor_digest",
            "descriptor bytes match the operator-pinned digest; no demonstration digest "
            "is accepted",
            failure_id="configured_runtime.proto_digest_mismatch",
        )

    # Local config + descriptor validity cannot substitute for CT-28 admission,
    # an activation boundary or the rest of the sealed host composition.
    return Ok(
        ConfiguredRuntimeAssessment(
            machine=machine,
            registry_as_of=as_of.value,
            node_config=compiled.value,
            roster=roster.value,
            descriptor_digest=digest,
            stand_down_reason=(
                "configured deployment declarations validated; authoritative registered "
                "seat resolution, activation, and boot ceremony have not been admitted"
            ),
        )
    )


def _absolute_path(value: object, field: str) -> Result[Path]:
    if not isinstance(value, (str, Path)):
        return invalid(field, f"{field} is an absolute filesystem path")
    path = Path(value)
    if not path.is_absolute():
        return invalid(field, f"{field} is an absolute filesystem path")
    return Ok(path)


def _mapping(
    value: object,
    field: str,
    allowed: frozenset[str],
) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid(field, f"{field} is an object with pinned fields")
    body = cast("Mapping[str, object]", value)
    unknown = set(body) - allowed
    if unknown:
        return invalid(field, f"{field} has no unknown fields", unknown=sorted(unknown))
    return Ok(MappingProxyType(dict(body)))
