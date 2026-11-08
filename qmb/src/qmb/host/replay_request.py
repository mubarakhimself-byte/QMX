"""Durable, content-addressed CT-12 and CT-10 replay request adapter.

The request fp1 is a separate QMB evidence reference. It names an exact CT-12
manifest plus explicit CT-10 archive receipts and the selected CT-33 source. The
registered ExperimentSpec data_ref remains the CT-12 fingerprint.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from qmf.core.chrono import CalendarIdentity, CivilDate, Instant, TradingDate
from qmf.core.fingerprint import Fingerprint, World, canonical_bytes, fingerprint
from qmf.core.identity import Instrument, VenueId
from qmf.core.refusal import Ok, Result, is_refusal
from qmf.data.seal import HoldoutSeal
from qmf.data.splits import (
    ProducerHorizon,
    SegmentRole,
    SplitBoundary,
    SplitManifest,
    SplitSegment,
)
from qml.conformance.layer2 import Layer2Verdict
from qml.declaration import BotDefinition
from qml.logic import fingerprint_source_manifest
from qml.protocol import MappingReadSurface

from qmb._refuse import invalid, policy, unavailable
from qmb.execution.binder import execution_keys_from_request
from qmb.host.adapter import HostedBot, construct_conformant_bot
from qmb.host.replay import (
    PinnedInstrumentPriceMetadata,
    RecordedReplaySource,
    TypedPartitionRef,
    read_recorded_replay_source,
    read_typed_replay_source,
)
from qmb.host.runner import FACTORY_KIND_SOURCE, FactorySpec, load_factory, run_sandbox

__all__ = [
    "REPLAY_REQUEST_FORMAT_VERSION",
    "TYPED_REQUEST_CLASS",
    "ReplayInputRequest",
    "ResolvedReplayRequest",
    "TypedReplayRequest",
    "load_typed_replay_request",
    "parse_typed_replay_request",
    "persist_replay_request",
    "resolve_replay_request",
    "resolve_typed_replay_request",
]

REPLAY_REQUEST_FORMAT_VERSION: Final[int] = 1
_REQUEST_CLASS: Final[str] = "qmb-recorded-replay-request-v1"
TYPED_REQUEST_CLASS: Final[str] = "qmb-typed-replay-request-v1"


@dataclass(frozen=True, slots=True)
class ReplayInputRequest:
    """Validated request pins; source files and all nested mappings are immutable."""

    split: SplitManifest
    split_role: SegmentRole
    archive_fingerprints: tuple[Fingerprint, ...]
    stream_id: str
    price_metadata: PinnedInstrumentPriceMetadata
    bot_identity: Mapping[str, object]
    source_tree: Mapping[str, str]
    assignment: Mapping[str, object]
    state_scope: Mapping[str, object]
    state_bound: int
    conformance_timeout_seconds: int
    fingerprint: Fingerprint

    @classmethod
    def try_create(
        cls,
        *,
        split: object,
        split_role: object,
        archive_fingerprints: object,
        stream_id: object,
        price_metadata: object,
        bot_identity: object,
        source_tree: object,
        assignment: object,
        state_scope: object,
        state_bound: object,
        conformance_timeout_seconds: object,
    ) -> Result[ReplayInputRequest]:
        if not isinstance(split, SplitManifest) or split.world is not World.REPLAY:
            return invalid("split", "a replay request pins a typed world=replay CT-12 manifest")
        split_stamp = fingerprint(split.fp1_identity())
        if is_refusal(split_stamp):
            return split_stamp
        if split_stamp.value != split.fingerprint:
            return policy("split", "CT-12 manifest fields match the cited fingerprint")
        try:
            role = split_role if isinstance(split_role, SegmentRole) else SegmentRole(split_role)
        except (TypeError, ValueError):
            return invalid("split_role", "a replay request names one CT-12 segment role")
        if not isinstance(archive_fingerprints, Sequence) or isinstance(
            archive_fingerprints, (str, bytes)
        ):
            return invalid("archive_fingerprints", "a request pins an ordered receipt-ref sequence")
        refs: list[Fingerprint] = []
        for raw in cast("Sequence[object]", archive_fingerprints):
            parsed = Ok(raw) if isinstance(raw, Fingerprint) else Fingerprint.try_create(raw)
            if is_refusal(parsed):
                return parsed
            if parsed.value in refs:
                return invalid("archive_fingerprints", "each CT-10 receipt is cited once")
            refs.append(parsed.value)
        if not refs:
            return invalid("archive_fingerprints", "a replay request cites CT-10 archive receipts")
        if not isinstance(stream_id, str) or not stream_id.strip():
            return invalid("stream_id", "a replay request names a source stream")
        if not isinstance(price_metadata, PinnedInstrumentPriceMetadata):
            return invalid("price_metadata", "execution pins exact CT-03 instrument metadata")
        if not all(
            isinstance(value, Mapping)
            for value in (bot_identity, source_tree, assignment, state_scope)
        ):
            return invalid("request", "CT-33, source, assignment, and state scope are mappings")
        raw_tree = cast("Mapping[object, object]", source_tree)
        files: dict[str, str] = {}
        for raw_path, raw_source in raw_tree.items():
            if not isinstance(raw_path, str) or not isinstance(raw_source, str):
                return invalid("source_tree", "source paths and file contents are strings")
            files[raw_path] = raw_source
        if not files:
            return invalid("source_tree", "a selected logic source manifest is non-empty")
        if isinstance(state_bound, bool) or not isinstance(state_bound, int) or state_bound < 1:
            return invalid("state_bound", "QML state bound is an explicit positive integer")
        if (
            isinstance(conformance_timeout_seconds, bool)
            or not isinstance(conformance_timeout_seconds, int)
            or conformance_timeout_seconds < 1
        ):
            return invalid(
                "conformance_timeout_seconds",
                "isolated conformance timeout is explicit positive seconds",
            )
        typed_bot = cast("Mapping[str, object]", bot_identity)
        typed_assignment = cast("Mapping[str, object]", assignment)
        typed_scope = cast("Mapping[str, object]", state_scope)
        definition = BotDefinition.try_from_mapping(typed_bot)
        if is_refusal(definition):
            return definition
        source_fp = fingerprint_source_manifest(files)
        if is_refusal(source_fp):
            return source_fp
        if source_fp.value != definition.value.logic_reference.source_manifest:
            return policy("source_tree", "selected source files match the CT-33 logic identity")
        body = _identity(
            split=split,
            split_role=role,
            archive_fingerprints=tuple(refs),
            stream_id=stream_id,
            price_metadata=price_metadata,
            bot_identity=typed_bot,
            source_tree=files,
            assignment=typed_assignment,
            state_scope=typed_scope,
            state_bound=state_bound,
            timeout=conformance_timeout_seconds,
        )
        stamped = fingerprint(body)
        if is_refusal(stamped):
            return stamped
        return Ok(
            cls(
                split=split,
                split_role=role,
                archive_fingerprints=tuple(refs),
                stream_id=stream_id,
                price_metadata=price_metadata,
                bot_identity=_freeze_mapping(typed_bot),
                source_tree=MappingProxyType(files),
                assignment=_freeze_mapping(typed_assignment),
                state_scope=_freeze_mapping(typed_scope),
                state_bound=state_bound,
                conformance_timeout_seconds=conformance_timeout_seconds,
                fingerprint=stamped.value,
            )
        )

    def fp1_identity(self) -> dict[str, object]:
        return _identity(
            split=self.split,
            split_role=self.split_role,
            archive_fingerprints=self.archive_fingerprints,
            stream_id=self.stream_id,
            price_metadata=self.price_metadata,
            bot_identity=self.bot_identity,
            source_tree=self.source_tree,
            assignment=self.assignment,
            state_scope=self.state_scope,
            state_bound=self.state_bound,
            timeout=self.conformance_timeout_seconds,
        )


@dataclass(frozen=True, slots=True)
class ResolvedReplayRequest:
    request_ref: Fingerprint
    split_fp1: Fingerprint
    source: RecordedReplaySource
    hosted: HostedBot
    conformance_verdict: Layer2Verdict


def persist_replay_request(*, request_root: object, request: object) -> Result[Fingerprint]:
    """Persist canonical request bytes, refusing any conflicting file at the same ref."""
    if not isinstance(request, ReplayInputRequest):
        return invalid("request", "only a validated ReplayInputRequest is persisted")
    stamped = fingerprint(request.fp1_identity())
    if is_refusal(stamped):
        return stamped
    if stamped.value != request.fingerprint:
        return policy("request", "persisted request fields match its immutable content ref")
    root = _request_root(request_root)
    if is_refusal(root):
        return root
    encoded = canonical_bytes(request.fp1_identity())
    if is_refusal(encoded):
        return encoded
    path = root.value / request.fingerprint.value.replace(":", "-")
    try:
        root.value.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        with os.fdopen(descriptor, "wb") as output:
            output.write(encoded.value)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError:
        previous = _read_bytes(path)
        if is_refusal(previous):
            return previous
        if previous.value != encoded.value:
            return policy("request_ref", "a stored request ref contains identical canonical bytes")
    except OSError as exc:
        return unavailable(
            "request_root", "QMB could not persist the replay request", given=type(exc).__name__
        )
    return Ok(request.fingerprint)


def resolve_replay_request(
    *,
    request_root: object,
    request_ref: object,
    split: object = None,
    expected_split_fp1: object,
    raw_store_root: object,
    holdout_months: object,
) -> Result[ResolvedReplayRequest]:
    """Resolve a QMB request against the already-registered CT-12 identity and read CT-10."""
    root = _request_root(request_root)
    if is_refusal(root):
        return root
    ref_result = (
        Ok(request_ref)
        if isinstance(request_ref, Fingerprint)
        else Fingerprint.try_create(request_ref)
    )
    if is_refusal(ref_result):
        return ref_result
    ref = ref_result.value
    raw = _read_bytes(root.value / ref.value.replace(":", "-"))
    if is_refusal(raw):
        return raw
    try:
        decoded = json.loads(raw.value)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return invalid("request", "stored request is canonical UTF-8 JSON")
    if not isinstance(decoded, Mapping):
        return invalid("request", "stored request is a mapping envelope")
    body = cast("Mapping[str, object]", decoded)
    check = fingerprint(body)
    if is_refusal(check):
        return check
    if check.value != ref:
        return policy("request_ref", "stored request content matches its fp1 path")
    if (
        body.get("class") != _REQUEST_CLASS
        or body.get("format_version") != REPLAY_REQUEST_FORMAT_VERSION
    ):
        return invalid("request", "stored request uses the supported QMB format")
    expected_result = (
        Ok(expected_split_fp1)
        if isinstance(expected_split_fp1, Fingerprint)
        else Fingerprint.try_create(expected_split_fp1)
    )
    if is_refusal(expected_result):
        return expected_result
    if split is None:
        stored_identity = _mapping(body.get("split_identity"), "split_identity")
        if is_refusal(stored_identity):
            return stored_identity
        reconstructed = _decode_split_manifest(stored_identity.value)
        if is_refusal(reconstructed):
            return reconstructed
        split = reconstructed.value
    if not isinstance(split, SplitManifest) or split.world is not World.REPLAY:
        return invalid("split", "resolver receives a typed replay CT-12 manifest identity")
    stored_split = Fingerprint.try_create(body.get("split_fp1"))
    if is_refusal(stored_split):
        return stored_split
    if stored_split.value != expected_result.value or split.fingerprint != expected_result.value:
        return policy(
            "split_fp1", "request and resolved CT-12 refs equal registered ExperimentSpec data_ref"
        )
    if body.get("split_identity") != split.fp1_identity():
        return policy(
            "split_identity", "request CT-12 identity equals the registry-resolved manifest"
        )
    role_raw = body.get("split_role")
    try:
        role = SegmentRole(role_raw)
    except (TypeError, ValueError):
        return invalid("split_role", "request names a supported CT-12 segment role")
    data = _mapping(body.get("price_metadata_identity"), "price_metadata_identity")
    if is_refusal(data):
        return data
    instrument_body = _mapping(data.value.get("instrument"), "instrument")
    if is_refusal(instrument_body):
        return instrument_body
    instrument = _instrument(instrument_body.value)
    if is_refusal(instrument):
        return instrument
    metadata = PinnedInstrumentPriceMetadata.try_create(
        instrument=instrument.value,
        price_scale=data.value.get("price_scale"),
        metadata_identity=data.value,
        metadata_fp1=body.get("price_metadata_fp1"),
    )
    if is_refusal(metadata):
        return metadata
    refs = body.get("archive_fingerprints")
    stream = body.get("stream_id")
    if not isinstance(refs, list) or not isinstance(stream, str):
        return invalid("archive_fingerprints", "request pins CT-10 receipt refs and stream")
    seal = HoldoutSeal.from_manifest(split, holdout_months)
    if is_refusal(seal):
        return seal
    source = read_recorded_replay_source(
        store_root=raw_store_root,
        archive_fingerprints=cast("Sequence[object]", refs),
        stream_id=stream,
        instrument_metadata=metadata.value,
        split_manifest=split,
        split_role=role,
        holdout_seal=seal.value,
        world=World.REPLAY,
    )
    if is_refusal(source):
        return source
    request = _request_context(body, split, role, metadata.value)
    if is_refusal(request):
        return request
    return _host_selected_bot(ref, split, source.value, request.value)


def _host_selected_bot(
    ref: Fingerprint,
    split: SplitManifest,
    source: RecordedReplaySource,
    request: Mapping[str, object],
) -> Result[ResolvedReplayRequest]:
    """Run the selected CT-33 source's Layer 2 check, then host it over the source's surfaces."""
    declaration = BotDefinition.try_from_mapping(request["bot_identity"])
    if is_refusal(declaration):
        return declaration
    conformance = run_sandbox(
        declaration=declaration.value,
        source_tree=request["source_tree"],
        assignment=request["assignment"],
        state_scope=request["state_scope"],
        state_bound=request["state_bound"],
        timeout_seconds=request["timeout"],
    )
    if is_refusal(conformance):
        return conformance
    tree = cast("Mapping[str, str]", request["source_tree"])
    candidates = [
        (path, text) for path, text in tree.items() if path.rsplit("/", 1)[-1] == "factory.py"
    ]
    if len(candidates) != 1:
        return policy("source_tree", "the selected source contains one conventional factory.py")
    path, source_text = candidates[0]
    module = path[:-3].replace("/", ".")
    if module.endswith(".__init__"):
        module = module[: -len(".__init__")]
    factory = load_factory(
        FactorySpec(FACTORY_KIND_SOURCE, source_text, f"{module}:factory"),
        source_tree=tree,
    )
    if is_refusal(factory):
        return factory
    hosted = construct_conformant_bot(
        factory.value,
        declaration=declaration.value,
        assignment=request["assignment"],
        read_surfaces=source.read_surfaces,
    )
    if is_refusal(hosted):
        return hosted
    return Ok(
        ResolvedReplayRequest(ref, split.fingerprint, source, hosted.value, conformance.value)
    )


_TYPED_REQUEST_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "class",
        "format_version",
        "stream_id",
        "split_identity",
        "split_role",
        "price_metadata_identity",
        "partitions",
        "bot_identity",
        "source_tree",
        "assignment",
        "state_scope",
        "state_bound",
        "conformance_timeout_seconds",
        "execution",
    }
)


@dataclass(frozen=True, slots=True)
class TypedReplayRequest:
    """A replay request written as data: typed partitions, the bot and its execution inputs.

    Every field is parsed from one JSON body and ``fingerprint`` is that body's fp1, so the
    file in the run's input folder is the request's whole identity. Partition files are
    named relative to that folder and must exist inside it.
    """

    split: SplitManifest
    split_role: SegmentRole
    stream_id: str
    price_metadata: PinnedInstrumentPriceMetadata
    partitions: tuple[TypedPartitionRef, ...]
    bot: Mapping[str, object]
    execution: Mapping[str, object]
    fingerprint: Fingerprint


def load_typed_replay_request(
    *, request_path: object, input_dir: object
) -> Result[TypedReplayRequest]:
    """Read a typed replay request's JSON file and parse it against its input folder."""
    if not isinstance(request_path, (str, Path)) or not str(request_path).strip():
        return invalid("request_path", "a typed replay request is a named JSON file")
    raw = _read_bytes(Path(request_path))
    if is_refusal(raw):
        return raw
    try:
        decoded: object = json.loads(raw.value)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return invalid("request", "a typed replay request is UTF-8 JSON")
    return parse_typed_replay_request(decoded, input_dir=input_dir)


def parse_typed_replay_request(body: object, *, input_dir: object) -> Result[TypedReplayRequest]:
    """Validate a typed replay request body; every refusal comes before any data is read."""
    if not isinstance(body, Mapping):
        return invalid("request", "a typed replay request is a JSON object")
    fields = cast("Mapping[str, object]", body)
    unknown = sorted(str(key) for key in fields if key not in _TYPED_REQUEST_FIELDS)
    if unknown:
        return invalid("request", "unknown typed replay request field", given=unknown)
    if (
        fields.get("class") != TYPED_REQUEST_CLASS
        or fields.get("format_version") != REPLAY_REQUEST_FORMAT_VERSION
    ):
        return invalid(
            "request",
            "a typed replay request names its class and format version",
            expected_class=TYPED_REQUEST_CLASS,
            expected_format_version=REPLAY_REQUEST_FORMAT_VERSION,
        )
    stream_id = fields.get("stream_id")
    if not isinstance(stream_id, str) or not stream_id.strip():
        return invalid("stream_id", "a typed replay request names its run stream")
    split_identity = _mapping(fields.get("split_identity"), "split_identity")
    if is_refusal(split_identity):
        return split_identity
    split = _decode_split_manifest(split_identity.value)
    if is_refusal(split):
        return split
    if split.value.world is not World.REPLAY:
        return policy("split", "a typed replay request pins a world=replay CT-12 manifest")
    try:
        role = SegmentRole(fields.get("split_role"))
    except (TypeError, ValueError):
        return invalid("split_role", "a typed replay request names one CT-12 segment role")
    metadata = _typed_price_metadata(fields.get("price_metadata_identity"))
    if is_refusal(metadata):
        return metadata
    partitions = _typed_partitions(fields.get("partitions"), input_dir)
    if is_refusal(partitions):
        return partitions
    bot = _bot_context(fields)
    if is_refusal(bot):
        return bot
    execution = _mapping(fields.get("execution"), "execution")
    if is_refusal(execution):
        return execution
    checked_execution = execution_keys_from_request(execution.value)
    if is_refusal(checked_execution):
        return checked_execution
    stamped = fingerprint(fields)
    if is_refusal(stamped):
        return stamped
    return Ok(
        TypedReplayRequest(
            split=split.value,
            split_role=role,
            stream_id=stream_id,
            price_metadata=metadata.value,
            partitions=partitions.value,
            bot=bot.value,
            execution=_freeze_mapping(execution.value),
            fingerprint=stamped.value,
        )
    )


def resolve_typed_replay_request(
    *, request: object, holdout_months: object
) -> Result[ResolvedReplayRequest]:
    """Read a typed request's partitions month by month, then host its bot over them.

    Each month is read and its fingerprint re-derived by ``read_typed_replay_source``; the
    months are joined into one source whose read surface keeps every sample so far, as a
    single read does, so a bot sees two months exactly as it would see one.
    """
    if not isinstance(request, TypedReplayRequest):
        return invalid("request", "resolution consumes a parsed TypedReplayRequest")
    seal = HoldoutSeal.from_manifest(request.split, holdout_months)
    if is_refusal(seal):
        return seal
    months = sorted({ref.month for ref in request.partitions})
    sources: list[RecordedReplaySource] = []
    for month in months:
        read = read_typed_replay_source(
            partitions=[ref for ref in request.partitions if ref.month == month],
            stream_id=request.stream_id,
            instrument_metadata=request.price_metadata,
            split_manifest=request.split,
            split_role=request.split_role,
            holdout_seal=seal.value,
            world=World.REPLAY,
        )
        if is_refusal(read):
            return read
        sources.append(read.value)
    joined = _join_months(sources)
    if is_refusal(joined):
        return joined
    return _host_selected_bot(request.fingerprint, request.split, joined.value, request.bot)


def _typed_price_metadata(raw: object) -> Result[PinnedInstrumentPriceMetadata]:
    identity = _mapping(raw, "price_metadata_identity")
    if is_refusal(identity):
        return identity
    instrument_body = _mapping(identity.value.get("instrument"), "instrument")
    if is_refusal(instrument_body):
        return instrument_body
    instrument = _instrument(instrument_body.value)
    if is_refusal(instrument):
        return instrument
    stamped = fingerprint(identity.value)
    if is_refusal(stamped):
        return stamped
    return PinnedInstrumentPriceMetadata.try_create(
        instrument=instrument.value,
        price_scale=identity.value.get("price_scale"),
        metadata_identity=identity.value,
        metadata_fp1=stamped.value,
    )


def _typed_partitions(raw: object, input_dir: object) -> Result[tuple[TypedPartitionRef, ...]]:
    """Resolve each named partition file inside the run's input folder, refusing by name."""
    if not isinstance(input_dir, (str, Path)) or not str(input_dir).strip():
        return invalid("input_dir", "a typed replay request is read against its input folder")
    root = Path(input_dir).resolve()
    if not isinstance(raw, list) or not raw:
        return invalid("partitions", "a typed replay request names at least one partition")
    refs: list[TypedPartitionRef] = []
    for index, item in enumerate(cast("list[object]", raw)):
        entry = _mapping(item, "partitions")
        if is_refusal(entry):
            return entry
        series = entry.value.get("series")
        month = entry.value.get("month")
        file = entry.value.get("file")
        if not isinstance(file, str) or not file.strip():
            return invalid("partitions", "a partition names its file", index=index)
        path = (root / file).resolve()
        if not path.is_relative_to(root):
            return policy(
                "partitions", "a partition file lies inside the run's input folder", file=file
            )
        if not path.is_file():
            return invalid(
                "partitions",
                "a named partition file exists in the run's input folder",
                series=series,
                month=month,
                file=file,
            )
        ref = TypedPartitionRef.try_create(
            path=path, series=series, month=month, fingerprint=entry.value.get("fingerprint")
        )
        if is_refusal(ref):
            return ref
        if any(
            (known.series, known.month) == (ref.value.series, ref.value.month) for known in refs
        ):
            return invalid("partitions", "each partition is named once", series=series, month=month)
        refs.append(ref.value)
    return Ok(tuple(refs))


def _bot_context(fields: Mapping[str, object]) -> Result[dict[str, object]]:
    """Validate the selected CT-33 bot a typed request names, as ``ReplayInputRequest`` does."""
    bot = _mapping(fields.get("bot_identity"), "bot_identity")
    tree = _mapping(fields.get("source_tree"), "source_tree")
    assignment = _mapping(fields.get("assignment"), "assignment")
    scope = _mapping(fields.get("state_scope"), "state_scope")
    if is_refusal(bot):
        return bot
    if is_refusal(tree):
        return tree
    if is_refusal(assignment):
        return assignment
    if is_refusal(scope):
        return scope
    files: dict[str, str] = {}
    for raw_path, raw_source in tree.value.items():
        if not isinstance(raw_source, str):
            return invalid("source_tree", "source paths and file contents are strings")
        files[raw_path] = raw_source
    if not files:
        return invalid("source_tree", "a selected logic source manifest is non-empty")
    state_bound = fields.get("state_bound")
    timeout = fields.get("conformance_timeout_seconds")
    if isinstance(state_bound, bool) or not isinstance(state_bound, int) or state_bound < 1:
        return invalid("state_bound", "QML state bound is an explicit positive integer")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        return invalid(
            "conformance_timeout_seconds",
            "isolated conformance timeout is explicit positive seconds",
        )
    definition = BotDefinition.try_from_mapping(bot.value)
    if is_refusal(definition):
        return definition
    source_fp = fingerprint_source_manifest(files)
    if is_refusal(source_fp):
        return source_fp
    if source_fp.value != definition.value.logic_reference.source_manifest:
        return policy("source_tree", "selected source files match the CT-33 logic identity")
    context: dict[str, object] = {
        "bot_identity": _freeze_mapping(bot.value),
        "source_tree": MappingProxyType(files),
        "assignment": _freeze_mapping(assignment.value),
        "state_scope": _freeze_mapping(scope.value),
        "state_bound": state_bound,
        "timeout": timeout,
    }
    return Ok(context)


def _join_months(sources: Sequence[RecordedReplaySource]) -> Result[RecordedReplaySource]:
    """Join month sources into one, each frame keeping every earlier month's samples."""
    if len(sources) == 1:
        return Ok(sources[0])
    first = sources[0]
    stream = first.stream_id
    frames: dict[int, object] = {}
    carried: tuple[object, ...] = ()
    previous: int | None = None
    for source in sources:
        latest = carried
        for frontier_ns, payload in source.read_surfaces[stream].frames.items():
            if previous is not None and frontier_ns <= previous:
                return invalid(
                    "partitions",
                    "joined months replay in strictly increasing frontiers",
                    frontier_ns=frontier_ns,
                )
            samples = cast("Mapping[str, Sequence[object]]", payload)["samples"]
            latest = carried + tuple(samples)
            frames[frontier_ns] = {"kind": "series", "samples": latest}
            previous = frontier_ns
        carried = latest
    surface = MappingReadSurface.try_create(frames)
    if is_refusal(surface):
        return surface
    joined = replace(
        first,
        slices=tuple(item for source in sources for item in source.slices),
        read_surfaces=MappingProxyType({stream: surface.value}),
        execution_paths=tuple(item for source in sources for item in source.execution_paths),
        partitions=tuple(item for source in sources for item in source.partitions),
    )
    stamped = fingerprint(joined.fp1_identity())
    if is_refusal(stamped):
        return stamped
    return Ok(replace(joined, fingerprint=stamped.value))


def _identity(
    *,
    split: SplitManifest,
    split_role: SegmentRole,
    archive_fingerprints: tuple[Fingerprint, ...],
    stream_id: str,
    price_metadata: PinnedInstrumentPriceMetadata,
    bot_identity: Mapping[str, object],
    source_tree: Mapping[str, str],
    assignment: Mapping[str, object],
    state_scope: Mapping[str, object],
    state_bound: int,
    timeout: int,
) -> dict[str, object]:
    return {
        "class": _REQUEST_CLASS,
        "format_version": REPLAY_REQUEST_FORMAT_VERSION,
        "split_fp1": split.fingerprint.value,
        "split_identity": split.fp1_identity(),
        "split_role": split_role.value,
        "archive_fingerprints": [item.value for item in archive_fingerprints],
        "stream_id": stream_id,
        "price_metadata_identity": dict(price_metadata.metadata_identity),
        "price_metadata_fp1": price_metadata.fingerprint.value,
        "bot_identity": dict(bot_identity),
        "source_tree": dict(source_tree),
        "assignment": dict(assignment),
        "state_scope": dict(state_scope),
        "state_bound": state_bound,
        "conformance_timeout_seconds": timeout,
    }


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _freeze_mapping(cast("Mapping[str, object]", value))
    if isinstance(value, (tuple, list)):
        return tuple(_freeze_value(item) for item in cast("Sequence[object]", value))
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})


def _request_context(
    body: Mapping[str, object],
    split: SplitManifest,
    role: SegmentRole,
    metadata: PinnedInstrumentPriceMetadata,
) -> Result[dict[str, object]]:
    bot = _mapping(body.get("bot_identity"), "bot_identity")
    tree = _mapping(body.get("source_tree"), "source_tree")
    assignment = _mapping(body.get("assignment"), "assignment")
    scope = _mapping(body.get("state_scope"), "state_scope")
    if is_refusal(bot):
        return bot
    if is_refusal(tree):
        return tree
    if is_refusal(assignment):
        return assignment
    if is_refusal(scope):
        return scope
    typed_tree = tree.value
    if any(not isinstance(value, str) for value in typed_tree.values()):
        return invalid("source_tree", "stored selected source contains text paths and files")
    state_bound = body.get("state_bound")
    timeout = body.get("conformance_timeout_seconds")
    if (
        isinstance(state_bound, bool)
        or not isinstance(state_bound, int)
        or isinstance(timeout, bool)
        or not isinstance(timeout, int)
    ):
        return invalid("state_bound", "stored QML scope and timeout are explicit integers")
    rebuilt = ReplayInputRequest.try_create(
        split=split,
        split_role=role,
        archive_fingerprints=cast("Sequence[object]", body.get("archive_fingerprints", ())),
        stream_id=body.get("stream_id"),
        price_metadata=metadata,
        bot_identity=bot.value,
        source_tree=typed_tree,
        assignment=assignment.value,
        state_scope=scope.value,
        state_bound=state_bound,
        conformance_timeout_seconds=timeout,
    )
    if is_refusal(rebuilt):
        return rebuilt
    context: dict[str, object] = {
        "bot_identity": rebuilt.value.bot_identity,
        "source_tree": rebuilt.value.source_tree,
        "assignment": rebuilt.value.assignment,
        "state_scope": rebuilt.value.state_scope,
        "state_bound": state_bound,
        "timeout": timeout,
    }
    return Ok(context)


def _instrument(identity: Mapping[str, object]) -> Result[Instrument]:
    venue = VenueId.try_create(identity.get("venue"))
    if is_refusal(venue):
        return venue
    return Instrument.try_create(venue.value, identity.get("symbol"))


def _decode_split_manifest(identity: Mapping[str, object]) -> Result[SplitManifest]:
    """Rebuild typed CT-12 from the content-addressed request's canonical identity."""
    if identity.get("class") != "dataset-split-manifest":
        return invalid("split_identity", "request embeds canonical CT-12 manifest identity")
    calendar_raw = _mapping(identity.get("calendar_identity"), "calendar_identity")
    if is_refusal(calendar_raw):
        return calendar_raw
    calendar_body = calendar_raw.value
    calendar = CalendarIdentity.try_create(
        calendar_body.get("rule_set"),
        calendar_body.get("rule_set_version"),
        calendar_body.get("tzdata_version"),
    )
    if is_refusal(calendar):
        return calendar
    raw_segments = identity.get("segments")
    if not isinstance(raw_segments, list) or not raw_segments:
        return invalid("segments", "CT-12 request contains ordered split segments")
    segments: list[SplitSegment] = []
    for raw_segment in cast("Sequence[object]", raw_segments):
        segment_body = _mapping(raw_segment, "segment")
        if is_refusal(segment_body):
            return segment_body
        boundary_body = _mapping(segment_body.value.get("boundary"), "boundary")
        if is_refusal(boundary_body):
            return boundary_body
        boundary = _decode_split_boundary(boundary_body.value, calendar.value)
        if is_refusal(boundary):
            return boundary
        segment = SplitSegment.try_create(segment_body.value.get("role"), boundary.value)
        if is_refusal(segment):
            return segment
        segments.append(segment.value)
    seal_body = _mapping(identity.get("seal_boundary"), "seal_boundary")
    if is_refusal(seal_body):
        return seal_body
    seal_boundary = _decode_split_boundary(seal_body.value, calendar.value)
    if is_refusal(seal_boundary):
        return seal_boundary
    purge = _mapping(identity.get("purge_width"), "purge_width")
    embargo = _mapping(identity.get("embargo_width"), "embargo_width")
    if is_refusal(purge):
        return purge
    if is_refusal(embargo):
        return embargo
    raw_producers = identity.get("cited_producers")
    if not isinstance(raw_producers, list):
        return invalid("cited_producers", "CT-12 producer horizons are explicitly listed")
    producers: list[ProducerHorizon] = []
    for raw_producer in cast("Sequence[object]", raw_producers):
        producer_body = _mapping(raw_producer, "cited_producer")
        if is_refusal(producer_body):
            return producer_body
        horizon_body = _mapping(
            producer_body.value.get("warmup_plus_confirmation"), "warmup_plus_confirmation"
        )
        if is_refusal(horizon_body):
            return horizon_body
        horizon = ProducerHorizon.try_create(
            producer_body.value.get("producer"),
            horizon_body.value.get("value_ns"),
        )
        if is_refusal(horizon):
            return horizon
        producers.append(horizon.value)
    manifest = SplitManifest.try_create(
        calendar_identity=calendar.value,
        segments=tuple(segments),
        seal_boundary=seal_boundary.value,
        purge_width=purge.value.get("value_ns"),
        embargo_width=embargo.value.get("value_ns"),
        world=identity.get("world"),
        cited_producers=tuple(producers),
    )
    if is_refusal(manifest):
        return manifest
    if manifest.value.fp1_identity() != dict(identity):
        return policy("split_identity", "reconstructed CT-12 retains exact canonical identity")
    return manifest


def _decode_split_boundary(
    identity: Mapping[str, object], calendar: CalendarIdentity
) -> Result[SplitBoundary]:
    kind = identity.get("kind")
    if kind == "instant":
        instant_body = _mapping(identity.get("instant"), "instant")
        if is_refusal(instant_body):
            return instant_body
        instant = Instant.try_create(instant_body.value.get("value_ns"))
        if is_refusal(instant):
            return instant
        return SplitBoundary.try_create(instant.value)
    if kind == "trading-date":
        trading_body = _mapping(identity.get("trading_date"), "trading_date")
        if is_refusal(trading_body):
            return trading_body
        if trading_body.value.get("calendar") != calendar.fp1_identity():
            return policy("calendar_identity", "CT-12 trading boundary matches manifest calendar")
        raw_date = trading_body.value.get("date_value")
        if not isinstance(raw_date, str):
            return invalid("date_value", "CT-12 trading-date identity contains ISO date text")
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError:
            return invalid("date_value", "CT-12 trading-date identity contains valid ISO date")
        civil = CivilDate.try_create(parsed_date.year, parsed_date.month, parsed_date.day)
        if is_refusal(civil):
            return civil
        trading = TradingDate.try_create(calendar, civil.value)
        if is_refusal(trading):
            return trading
        return SplitBoundary.try_create(trading.value)
    return invalid("boundary", "CT-12 boundary kind is instant or trading-date")


def _mapping(value: object, field: str) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid(field, "request identity field is a mapping")
    return Ok(cast("Mapping[str, object]", value))


def _request_root(value: object) -> Result[Path]:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        return invalid("request_root", "QMB request root is an explicit configured path")
    root = Path(value)
    if root.is_symlink():
        return policy("request_root", "QMB request root is not a symlink")
    return Ok(root)


def _read_bytes(path: Path) -> Result[bytes]:
    try:
        if path.is_symlink() or not path.is_file():
            return invalid("request_ref", "no durable replay request exists at this ref")
        return Ok(path.read_bytes())
    except OSError as exc:
        return unavailable(
            "request_root", "QMB could not read its replay request", given=type(exc).__name__
        )
