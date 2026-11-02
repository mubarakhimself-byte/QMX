"""Application-layer profile pins and closed resolver stay separate from CT configs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar, cast

from google.protobuf import descriptor_pb2
from qmb.host.replay import PinnedInstrumentPriceMetadata
from qmb.host.replay_request import ReplayInputRequest, persist_replay_request
from qmf.core import (
    CalendarIdentity,
    Instrument,
    Result,
    VenueId,
    World,
    fingerprint,
    is_ok,
    is_refusal,
)
from qmf.core.chrono import Instant, WriterId
from qmf.data.observation import ForeignMoney, MarketDataContext, SourceObservation
from qmf.data.seal import HoldoutSeal
from qmf.data.source_boundary import SourceObservationBoundary
from qmf.data.splits import SegmentRole, SplitBoundary, SplitManifest
from qmf.data.store import EvidenceStore
from qmf.venue.proto import descriptor_set_digest
from qml.protocol import mint_state_scope
from qmn.host.configured_composition import (
    HOST_PROFILE_CLASS,
    HOST_PROFILE_FORMAT_VERSION,
    OFFLINE_CONFORMANCE_PROFILE_ID,
    ResolvedHostResourceProfile,
    build_registered_factory,
    registered_callback_fp1,
    resolve_host_resource_profile,
)
from qmn.host.configured_runtime import (
    ConfiguredRuntimeAssessment,
    assess_configured_runtime,
)
from test_qmn_configured_runtime import fixture_deployment

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


_OFFLINE_SOURCE = {
    "bot.py": "def on_instant(self, evidence):\n    return ()\n",
    "factory.py": (
        "from qml.protocol import FunctionFactory\n"
        "factory = FunctionFactory(logic=lambda evidence: ())\n"
    ),
}


def _recorded_request(assessment: ConfiguredRuntimeAssessment, root: Path) -> dict[str, object]:
    raw_root = root / "raw-archive"
    request_root = root / "replay-requests"
    calendar = _ok(CalendarIdentity.try_create("offline-profile-calendar", "v1", "2025a"))
    epoch_ns = 1_700_000_000_000_000_000
    split_instants = tuple(
        _ok(Instant.try_create(epoch_ns + offset))
        for offset in (72 * 3_600_000_000_000, 144 * 3_600_000_000_000, 216 * 3_600_000_000_000)
    )
    segments = _ok(SplitManifest.default_split_segments(split_instants))
    split = _ok(
        SplitManifest.try_create(
            calendar_identity=calendar,
            segments=segments,
            seal_boundary=_ok(SplitBoundary.try_create(split_instants[-1])),
            purge_width=0,
            embargo_width=0,
            world=World.REPLAY,
        )
    )
    seal = _ok(HoldoutSeal.from_manifest(split, 18))
    boundary = SourceObservationBoundary(EvidenceStore(raw_root, seal=seal))
    source_writer = _ok(WriterId.try_create("offline-profile", "fixture", "ct10", "source"))
    refs: list[str] = []
    venue = _ok(VenueId.try_create("replay-venue"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    for frontier, event_ns in enumerate((epoch_ns, epoch_ns + 1)):
        instant = _ok(Instant.try_create(event_ns))
        for side, price in (("bid", 1_234_500), ("ask", 1_234_520)):
            sequence = frontier * 2 + (side == "ask")
            observation = _ok(
                SourceObservation.try_create(
                    event_time=instant,
                    known_at=instant,
                    source="offline-profile-recorded-fixture",
                    source_native_id=f"{frontier}-{side}",
                    revision="1",
                    receive_wall_time=instant,
                    writer=source_writer,
                    sequence=sequence,
                    world=World.REPLAY,
                    foreign_money=_ok(ForeignMoney.try_create(price, 5)),
                    market_data=_ok(
                        MarketDataContext.try_create(
                            venue="replay-venue",
                            symbol="EURUSD",
                            resolution="tick",
                            side=side,
                            license_tag="local-fixture",
                            provenance={"source_kind": "persisted-offline-conformance"},
                        )
                    ),
                )
            )
            refs.append(_ok(boundary.admit(observation)).archive.fingerprint.value)
    price_metadata_identity = {
        "instrument": instrument.fp1_identity(),
        "metadata_version": "offline-profile-fixture-v1",
        "price_scale": 5,
        "source_policy": {"kind": "persisted-local-fixture"},
    }
    price_metadata = _ok(
        PinnedInstrumentPriceMetadata.try_create(
            instrument=instrument,
            price_scale=5,
            metadata_identity=price_metadata_identity,
            metadata_fp1=_ok(fingerprint(price_metadata_identity)),
        )
    )
    scope = _ok(
        mint_state_scope(
            os="fixture-os",
            logic_identity=assessment.bot_definition.logic_reference.as_logic_reference(),
            protocol_format_version=1,
            arithmetic_reference_build="offline-conformance-fixture",
        )
    )
    request = _ok(
        ReplayInputRequest.try_create(
            split=split,
            split_role=SegmentRole.TRAIN,
            archive_fingerprints=refs,
            stream_id="primary",
            price_metadata=price_metadata,
            bot_identity=assessment.bot_definition.identity_payload(),
            source_tree=_OFFLINE_SOURCE,
            assignment={},
            state_scope=scope.to_mapping(),
            state_bound=256,
            conformance_timeout_seconds=30,
        )
    )
    request_ref = _ok(persist_replay_request(request_root=request_root, request=request))
    return {
        "request_root": str(request_root),
        "request_ref": request_ref.value,
        "raw_store_root": str(raw_root),
        "split_fp1": split.fingerprint.value,
        "holdout_months": 18,
    }


def _offline_profile(assessment: ConfiguredRuntimeAssessment, root: Path) -> dict[str, object]:
    records = assessment.registered_records
    bot = assessment.bot_definition
    callback = _ok(registered_callback_fp1())
    logic_fp = _ok(bot.logic_reference.fingerprint_content())
    producers: list[dict[str, object]] = [{"producer_id": "sqs", "version": "v1", "parameters": {}}]
    mis_identity: dict[str, object] = {
        "class": "qmn-profile-mis-catalog-v1",
        "catalog_id": "fixture-mis-catalog",
        "producers": producers,
    }
    return {
        "class": HOST_PROFILE_CLASS,
        "format_version": HOST_PROFILE_FORMAT_VERSION,
        "profile_id": OFFLINE_CONFORMANCE_PROFILE_ID,
        "composition_class": "book",
        "ct22_fp1": records["ct22_fp1"].persisted_fingerprint.value,
        "ct27_fp1": records["ct27_fp1"].persisted_fingerprint.value,
        "ct28_fp1": assessment.binding_fingerprint.value,
        "ct33_fp1": records["ct33_fp1"].persisted_fingerprint.value,
        "ct24_event_fp1": assessment.activation_evidence_ref,
        "logic_fp1": logic_fp.value,
        "logic_source": _OFFLINE_SOURCE,
        "callback": {"id": "qmn.book.offline-entry-once.v1", "fp1": callback.value},
        "recorded_source": {
            **_recorded_request(assessment, root),
        },
        "mis_catalog": {
            "id": "fixture-mis-catalog",
            "fp1": _ok(fingerprint(mis_identity)).value,
            "producers": producers,
        },
    }


def _valid_deployment(root: Path) -> Path:
    descriptor_set = descriptor_pb2.FileDescriptorSet()
    proto = descriptor_set.file.add()
    proto.name = "fixture.proto"
    proto.package = "fixture"
    proto.syntax = "proto3"
    raw = descriptor_set.SerializeToString()
    digest = _ok(descriptor_set_digest(raw))
    descriptor_path = root / "pinned-proto.pb"
    descriptor_path.write_bytes(raw)
    return fixture_deployment(root, descriptor_path, digest)


def _write_v2_deployment(root: Path, profile: dict[str, object]) -> Path:
    deployment = _valid_deployment(root)
    payload = json.loads(deployment.read_text(encoding="utf-8"))
    profile_path = root / "host-resource-profile.json"
    profile_path.write_text(json.dumps(profile, sort_keys=True), encoding="utf-8")
    payload["format_version"] = 2
    payload["host_resource_profile"] = {
        "descriptor_path": str(profile_path),
        "descriptor_fp1": _ok(fingerprint(profile)).value,
    }
    deployment.write_text(json.dumps(payload), encoding="utf-8")
    return deployment


def valid_deployment(root: Path) -> Path:
    """Public shared fixture builder for configured-runtime integration tests."""
    return _valid_deployment(root)


def offline_profile(assessment: ConfiguredRuntimeAssessment, root: Path) -> dict[str, object]:
    """Public shared fixture builder for the registered replay-only profile."""
    return _offline_profile(assessment, root)


def write_v2_deployment(root: Path, profile: dict[str, object]) -> Path:
    """Write a pinned v2 fixture using the canonical profile helper."""
    return _write_v2_deployment(root, profile)


def test_v2_profile_is_independently_pinned_and_resolves_only_closed_identity(
    tmp_path: Path,
) -> None:
    v1_path = _valid_deployment(tmp_path)
    v1 = _ok(assess_configured_runtime(v1_path, qmx_root=tmp_path))
    assert v1.host_resource_profile is None
    assert is_refusal(resolve_host_resource_profile(v1))

    v2_path = _write_v2_deployment(tmp_path, _offline_profile(v1, tmp_path))
    v2 = _ok(assess_configured_runtime(v2_path, qmx_root=tmp_path))
    selected = resolve_host_resource_profile(v2)
    assert is_ok(selected), selected
    assert isinstance(selected.value, ResolvedHostResourceProfile)
    assert selected.value.profile_id == OFFLINE_CONFORMANCE_PROFILE_ID
    assert len(selected.value.replay_request.source.observations) == 4
    assert selected.value.stream_id == "primary"
    assert is_ok(build_registered_factory(selected.value))


def test_resolved_profile_freezes_nested_mis_parameters(tmp_path: Path) -> None:
    assessment = _ok(assess_configured_runtime(_valid_deployment(tmp_path), qmx_root=tmp_path))
    profile = _offline_profile(assessment, tmp_path)
    mis_catalog = cast("dict[str, object]", profile["mis_catalog"])
    producers = cast("list[dict[str, object]]", mis_catalog["producers"])
    producers[0]["parameters"] = {"changed": 1}
    mis_catalog["fp1"] = _ok(
        fingerprint(
            {
                "class": "qmn-profile-mis-catalog-v1",
                "catalog_id": mis_catalog["id"],
                "producers": producers,
            }
        )
    ).value
    path = _write_v2_deployment(tmp_path, profile)
    assessed = _ok(assess_configured_runtime(path, qmx_root=tmp_path))
    resolved = _ok(resolve_host_resource_profile(assessed))
    before = resolved.mis_catalog_fp1
    try:
        params = cast("Mapping[str, object]", resolved.mis_producers[0]["parameters"])
        cast("dict[str, object]", params)["changed"] = 2
    except TypeError:
        pass
    else:
        raise AssertionError("nested resolved MIS configuration must be immutable")
    assert resolved.mis_catalog_fp1 == before


def test_v2_refuses_descriptor_mutation_and_unregistered_callback_before_selection(
    tmp_path: Path,
) -> None:
    assessment = _ok(assess_configured_runtime(_valid_deployment(tmp_path), qmx_root=tmp_path))
    profile = _offline_profile(assessment, tmp_path)
    path = _write_v2_deployment(tmp_path, profile)
    payload = json.loads(path.read_text(encoding="utf-8"))
    descriptor = tmp_path / "host-resource-profile.json"
    changed = dict(profile)
    changed["composition_class"] = "alternative"
    descriptor.write_text(json.dumps(changed), encoding="utf-8")
    refused_digest = assess_configured_runtime(path, qmx_root=tmp_path)
    assert is_refusal(refused_digest)
    assert (
        refused_digest.context.get("failure_id")
        == "configured_runtime.host_profile_identity_mismatch"
    )

    payload["host_resource_profile"]["descriptor_fp1"] = _ok(fingerprint(changed)).value
    path.write_text(json.dumps(payload), encoding="utf-8")
    changed_body = _ok(assess_configured_runtime(path, qmx_root=tmp_path))
    refused_profile = resolve_host_resource_profile(changed_body)
    assert is_refusal(refused_profile)
    assert refused_profile.context.get("field") == "composition_class"

    unregistered = dict(profile)
    unregistered["callback"] = {"id": "user.module:callable", "fp1": "fp1:sha256:" + "0" * 64}
    unregistered["logic_fp1"] = _ok(
        assessment.bot_definition.logic_reference.fingerprint_content()
    ).value
    unregistered_path = _write_v2_deployment(tmp_path, unregistered)
    unresolved = _ok(assess_configured_runtime(unregistered_path, qmx_root=tmp_path))
    refused_callback = resolve_host_resource_profile(unresolved)
    assert is_refusal(refused_callback)
    assert refused_callback.context.get("failure_id") == "configured_runtime.callback_unregistered"


def test_v2_source_bytes_must_reproduce_admitted_logic_manifest(tmp_path: Path) -> None:
    assessment = _ok(assess_configured_runtime(_valid_deployment(tmp_path), qmx_root=tmp_path))
    profile = _offline_profile(assessment, tmp_path)
    profile["logic_source"] = {"bot.py": "def on_instant(self, evidence):\n    return (1,)\n"}
    deployment = _write_v2_deployment(tmp_path, profile)
    resolved_assessment = _ok(assess_configured_runtime(deployment, qmx_root=tmp_path))

    resolved = resolve_host_resource_profile(resolved_assessment)

    assert is_refusal(resolved)
    assert resolved.context.get("failure_id") == "configured_runtime.host_profile_logic_mismatch"
