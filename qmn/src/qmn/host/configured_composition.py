"""Closed resolver for independently pinned hosted resource profiles.

The descriptor is an application-layer object. It does not extend CT-22/27/28/33
or the 71-row node configuration, and it cannot name an import path. Only
compiled-in profile and callback identities may be resolved here.
"""

from __future__ import annotations

import hashlib
import inspect
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qmb.host.replay_request import ResolvedReplayRequest, resolve_replay_request
from qmf.core import Fingerprint, Ok, Result, fingerprint, is_refusal
from qml.declaration import BotDefinition
from qml.logic import fingerprint_source_manifest
from qml.protocol import FunctionFactory

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.configured_runtime import ConfiguredRuntimeAssessment

__all__ = [
    "HOST_PROFILE_CLASS",
    "HOST_PROFILE_FORMAT_VERSION",
    "OFFLINE_CONFORMANCE_PROFILE_ID",
    "ResolvedHostResourceProfile",
    "build_registered_factory",
    "registered_callback_fp1",
    "resolve_host_resource_profile",
]

HOST_PROFILE_CLASS: Final[str] = "qmn-host-resource-profile"
HOST_PROFILE_FORMAT_VERSION: Final[int] = 1
OFFLINE_CONFORMANCE_PROFILE_ID: Final[str] = "qmn.book.offline-conformance.v1"
_CALLBACK_CLASS: Final[str] = "qmn-host-callback-registration-v1"
_CALLBACK_ID: Final[str] = "qmn.book.offline-entry-once.v1"
_OFFLINE_LOGIC_SOURCE: Final[Mapping[str, str]] = MappingProxyType(
    {
        "bot.py": "def on_instant(self, evidence):\n    return ()\n",
        "factory.py": (
            "from qml.protocol import FunctionFactory\n"
            "factory = FunctionFactory(logic=lambda evidence: ())\n"
        ),
    }
)
_PROFILE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "class",
        "format_version",
        "profile_id",
        "composition_class",
        "ct22_fp1",
        "ct27_fp1",
        "ct28_fp1",
        "ct33_fp1",
        "ct24_event_fp1",
        "logic_fp1",
        "logic_source",
        "callback",
        "recorded_source",
        "mis_catalog",
    }
)


@dataclass(frozen=True, slots=True)
class ResolvedHostResourceProfile:
    """Identity-checked descriptor selected by the trusted application resolver."""

    profile_id: str
    profile_fp1: Fingerprint
    composition_class: str
    callback_id: str
    callback_fp1: Fingerprint
    logic_source: Mapping[str, str]
    replay_request: ResolvedReplayRequest
    source_fp1: Fingerprint
    stream_id: str
    mis_catalog_id: str
    mis_catalog_fp1: Fingerprint
    mis_producers: tuple[Mapping[str, object], ...]


def registered_callback_fp1(callback_id: str = _CALLBACK_ID) -> Result[Fingerprint]:
    """Fingerprint the installed closed QML factory implementation bytes.

    The profile selects a registry key only. Its identity follows the exact
    installed FunctionFactory source artifact, so a package update cannot keep
    the old callback identity by retaining a descriptive version string.
    """
    if callback_id != _CALLBACK_ID:
        return unavailable(
            "callback_id",
            "callback identity is not present in the compiled QMN callback registry",
            failure_id="configured_runtime.callback_unregistered",
        )
    try:
        factory_path = inspect.getsourcefile(FunctionFactory)
        composition_path = inspect.getsourcefile(build_registered_factory)
        if factory_path is None or composition_path is None:
            raise OSError("registered callback source artifact is unavailable")
        implementation_digest = hashlib.sha256(
            Path(factory_path).read_bytes() + b"\x00" + Path(composition_path).read_bytes()
        ).hexdigest()
    except OSError:
        return unavailable(
            "callback_implementation",
            "the installed QML FunctionFactory source bytes are available for identity",
            failure_id="configured_runtime.callback_implementation_missing",
        )
    return fingerprint(
        {
            "class": _CALLBACK_CLASS,
            "callback_id": _CALLBACK_ID,
            "implementation_distribution": "qml.protocol.factory.FunctionFactory",
            "implementation_sha256": implementation_digest,
        }
    )


def build_registered_factory(profile: object) -> Result[FunctionFactory]:
    """Return the closed offline callback after checking its exact CT-33 source.

    This conformance-only no-intent bot cannot derive venue commands from
    recorded data and is not a production execution policy.
    """
    if not isinstance(profile, ResolvedHostResourceProfile):
        return invalid("profile", "registered factories require a resolved profile")
    expected = registered_callback_fp1(profile.callback_id)
    if is_refusal(expected):
        return expected
    if profile.callback_fp1 != expected.value:
        return policy("callback_fp1", "profile pins the installed closed callback bytes")
    if dict(profile.logic_source) != dict(_OFFLINE_LOGIC_SOURCE):
        return unavailable(
            "logic_source",
            "the registered offline callback only implements its exact no-intent logic",
            failure_id="configured_runtime.callback_logic_unregistered",
        )
    return Ok(FunctionFactory(logic=_offline_no_intents))


def _offline_no_intents(_evidence: object) -> tuple[object, ...]:
    """Closed conformance callback; provider-free and deliberately emits no actions."""
    return ()


def resolve_host_resource_profile(assessment: object) -> Result[ResolvedHostResourceProfile]:
    """Resolve the sole built-in offline profile against actual checked authority."""
    if not isinstance(assessment, ConfiguredRuntimeAssessment):
        return invalid("assessment", "profile resolution consumes checked runtime assessment")
    descriptor = assessment.host_resource_profile
    if descriptor is None:
        return unavailable(
            "host_resource_profile",
            "version 1 has no hosted resource profile and remains stand-down",
            failure_id="configured_runtime.host_profile_missing",
        )
    if frozenset(descriptor) != _PROFILE_KEYS:
        return invalid(
            "host_resource_profile",
            "profile descriptor has the exact application-layer identity fields",
            missing=sorted(_PROFILE_KEYS - set(descriptor)),
            unknown=sorted(set(descriptor) - _PROFILE_KEYS),
        )
    if (
        descriptor.get("class") != HOST_PROFILE_CLASS
        or type(descriptor.get("format_version")) is not int
        or descriptor.get("format_version") != HOST_PROFILE_FORMAT_VERSION
    ):
        return invalid("host_resource_profile", "profile class and version are recognized")
    profile_id = descriptor.get("profile_id")
    if profile_id != OFFLINE_CONFORMANCE_PROFILE_ID:
        return unavailable(
            "profile_id",
            "profile id is absent from the closed host resource profile registry",
            failure_id="configured_runtime.host_profile_unregistered",
        )
    if descriptor.get("composition_class") != "book":
        return invalid("composition_class", "this registered profile is the Book composition")
    authority_refs = {
        "ct22_fp1": assessment.registered_records["ct22_fp1"].persisted_fingerprint.value,
        "ct27_fp1": assessment.registered_records["ct27_fp1"].persisted_fingerprint.value,
        "ct28_fp1": assessment.binding_fingerprint.value,
        "ct33_fp1": assessment.registered_records["ct33_fp1"].persisted_fingerprint.value,
        "ct24_event_fp1": assessment.activation_evidence_ref,
    }
    for key, expected in authority_refs.items():
        offered = Fingerprint.try_create(descriptor.get(key))
        if is_refusal(offered):
            return offered
        if offered.value.value != expected:
            return policy(
                key,
                "profile identity cites the exact assessed registered or activation authority",
                failure_id="configured_runtime.host_profile_authority_mismatch",
            )
    callback = _mapping(descriptor.get("callback"), "callback")
    if is_refusal(callback):
        return callback
    if frozenset(callback.value) != frozenset({"id", "fp1"}):
        return invalid("callback", "callback pins only its closed-registry id and fp1")
    callback_id = callback.value.get("id")
    if not isinstance(callback_id, str):
        return invalid("callback.id", "registered callback id is a string token")
    expected_callback = registered_callback_fp1(callback_id)
    if is_refusal(expected_callback):
        return expected_callback
    callback_fp = Fingerprint.try_create(callback.value.get("fp1"))
    if is_refusal(callback_fp):
        return callback_fp
    if callback_fp.value != expected_callback.value:
        return policy("callback.fp1", "callback identity matches its compiled implementation")
    source = _mapping(descriptor.get("recorded_source"), "recorded_source")
    if is_refusal(source):
        return source
    source_fields = {
        "request_root",
        "request_ref",
        "raw_store_root",
        "split_fp1",
        "holdout_months",
    }
    if frozenset(source.value) != frozenset(source_fields):
        return invalid(
            "recorded_source",
            "source pins QMB's content-addressed request, CT-10 root, CT-12 ref and holdout",
        )
    request_root = _absolute_root(source.value.get("request_root"), "recorded_source.request_root")
    raw_store_root = _absolute_root(
        source.value.get("raw_store_root"), "recorded_source.raw_store_root"
    )
    if is_refusal(request_root):
        return request_root
    if is_refusal(raw_store_root):
        return raw_store_root
    split_fp = Fingerprint.try_create(source.value.get("split_fp1"))
    request_fp = Fingerprint.try_create(source.value.get("request_ref"))
    if is_refusal(split_fp):
        return split_fp
    if is_refusal(request_fp):
        return request_fp
    holdout_months = source.value.get("holdout_months")
    if (
        isinstance(holdout_months, bool)
        or not isinstance(holdout_months, int)
        or holdout_months < 1
    ):
        return invalid("recorded_source.holdout_months", "holdout is a positive pinned integer")
    replay_request = resolve_replay_request(
        request_root=request_root.value,
        request_ref=request_fp.value,
        split=None,
        expected_split_fp1=split_fp.value,
        raw_store_root=raw_store_root.value,
        holdout_months=holdout_months,
    )
    if is_refusal(replay_request):
        return replay_request
    if replay_request.value.source.world.value != "replay":
        return policy("recorded_source.world", "QMB request materializes the replay world")
    request_bot = replay_request.value.hosted.declaration
    request_bot_fp = _bot_fingerprint(request_bot)
    assessment_bot_fp = _bot_fingerprint(assessment.bot_definition)
    if is_refusal(request_bot_fp):
        return request_bot_fp
    if is_refusal(assessment_bot_fp):
        return assessment_bot_fp
    if request_bot_fp.value != assessment_bot_fp.value:
        return policy(
            "recorded_source.bot_identity",
            "recorded request CT-33 declaration matches the checked registered bot",
        )
    if replay_request.value.source.stream_id == "":
        return invalid("recorded_source.stream_id", "materialized source has a stream identity")
    source_fp = replay_request.value.source.fingerprint
    stream_id = replay_request.value.source.stream_id
    mis = _mapping(descriptor.get("mis_catalog"), "mis_catalog")
    if is_refusal(mis):
        return mis
    if frozenset(mis.value) != frozenset({"id", "fp1", "producers"}):
        return invalid("mis_catalog", "MIS catalog pins its identity and producer declarations")
    mis_id = _token(mis.value.get("id"), "mis_catalog.id")
    if is_refusal(mis_id):
        return mis_id
    producers = _mapping_rows(mis.value.get("producers"), "mis_catalog.producers")
    if is_refusal(producers):
        return producers
    mis_identity = {
        "class": "qmn-profile-mis-catalog-v1",
        "catalog_id": mis_id.value,
        "producers": [dict(row) for row in producers.value],
    }
    mis_fp = _pinned_identity(mis.value.get("fp1"), mis_identity, "mis_catalog.fp1")
    if is_refusal(mis_fp):
        return mis_fp
    if not any(row.get("producer_id") == "sqs" for row in producers.value):
        return invalid("mis_catalog.producers", "governed Book profile registers SQS")
    bot: BotDefinition = assessment.bot_definition
    logic_fp = bot.logic_reference.fingerprint_content()
    if is_refusal(logic_fp):
        return logic_fp
    offered_logic_fp = Fingerprint.try_create(descriptor.get("logic_fp1"))
    if is_refusal(offered_logic_fp):
        return offered_logic_fp
    if offered_logic_fp.value != logic_fp.value:
        return policy(
            "logic_fp1",
            "host profile callback binds the exact CT-33 logic identity",
            failure_id="configured_runtime.host_profile_logic_mismatch",
        )
    source_tree_value = _mapping(descriptor.get("logic_source"), "logic_source")
    if is_refusal(source_tree_value):
        return source_tree_value
    source_tree: dict[str, str] = {}
    for path, source_text in source_tree_value.value.items():
        if not isinstance(source_text, str):
            return invalid("logic_source", "compiled source bytes are strings")
        source_tree[path] = source_text
    source_manifest = fingerprint_source_manifest(source_tree)
    if is_refusal(source_manifest):
        return source_manifest
    if source_manifest.value != bot.logic_reference.source_manifest:
        return policy(
            "logic_source",
            "the registered callback source bytes reproduce the exact CT-33 logic manifest",
            failure_id="configured_runtime.host_profile_logic_mismatch",
        )
    if dict(source_tree) != dict(_OFFLINE_LOGIC_SOURCE):
        return unavailable(
            "logic_source",
            "the closed offline profile only registers its exact no-intent conformance source",
            failure_id="configured_runtime.callback_logic_unregistered",
        )
    profile_fp = fingerprint(dict(descriptor))
    if is_refusal(profile_fp):
        return profile_fp
    return Ok(
        ResolvedHostResourceProfile(
            profile_id=OFFLINE_CONFORMANCE_PROFILE_ID,
            profile_fp1=profile_fp.value,
            composition_class="book",
            callback_id=callback_id,
            callback_fp1=callback_fp.value,
            logic_source=MappingProxyType(source_tree),
            source_fp1=source_fp,
            stream_id=stream_id,
            replay_request=replay_request.value,
            mis_catalog_id=mis_id.value,
            mis_catalog_fp1=mis_fp.value,
            mis_producers=producers.value,
        )
    )


def _mapping(value: object, field: str) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid(field, "profile field is a mapping")
    frozen = _freeze_profile_value(cast("Mapping[object, object]", value), field)
    if is_refusal(frozen):
        return frozen
    return Ok(cast("Mapping[str, object]", frozen.value))


def _mapping_rows(value: object, field: str) -> Result[tuple[Mapping[str, object], ...]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return invalid(field, "profile rows are a sequence of mappings")
    rows: list[Mapping[str, object]] = []
    for row in cast(Sequence[object], value):
        parsed = _mapping(row, field)
        if is_refusal(parsed):
            return parsed
        rows.append(parsed.value)
    if not rows:
        return invalid(field, "profile requires at least one declared row")
    return Ok(tuple(rows))


def _freeze_profile_value(value: object, field: str) -> Result[object]:
    if value is None or type(value) in {str, int, bool}:
        return Ok(value)
    if type(value) is float:
        return (
            Ok(value)
            if math.isfinite(value)
            else invalid(field, "profile numbers are finite JSON values")
        )
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, child_value in cast("Mapping[object, object]", value).items():
            if type(key) is not str:
                return invalid(field, "profile object keys are strings")
            child = _freeze_profile_value(child_value, field)
            if is_refusal(child):
                return child
            frozen[key] = child.value
        return Ok(MappingProxyType(frozen))
    if isinstance(value, (list, tuple)):
        frozen_values: list[object] = []
        for item in cast("Sequence[object]", value):
            child = _freeze_profile_value(item, field)
            if is_refusal(child):
                return child
            frozen_values.append(child.value)
        return Ok(tuple(frozen_values))
    return invalid(field, "profile descriptor contains only JSON values")


def _token(value: object, field: str) -> Result[str]:
    if not isinstance(value, str) or not value.strip():
        return invalid(field, "profile identity is a nonblank string")
    return Ok(value.strip())


def _absolute_root(value: object, field: str) -> Result[Path]:
    if not isinstance(value, str) or not Path(value).is_absolute():
        return invalid(field, "runtime artifact root is an absolute operator-pinned path")
    root = Path(value)
    if not root.is_dir():
        return unavailable(field, "pinned runtime artifact root exists as a directory")
    return Ok(root)


def _bot_fingerprint(value: object) -> Result[Fingerprint]:
    if not isinstance(value, BotDefinition):
        return invalid("bot_definition", "replay request resolves an admitted CT-33 bot")
    return value.fingerprint_content()


def _pinned_identity(
    value: object,
    identity: Mapping[str, object],
    field: str,
) -> Result[Fingerprint]:
    expected = fingerprint(identity)
    if is_refusal(expected):
        return expected
    offered = Fingerprint.try_create(value)
    if is_refusal(offered):
        return offered
    if offered.value != expected.value:
        return policy(field, "pinned identity matches canonical profile content")
    return expected
