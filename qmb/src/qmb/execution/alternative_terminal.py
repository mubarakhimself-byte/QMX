"""Durable QMB terminal artifacts for Alternative Trading Composition runs.

Rows here are a private, versioned QMB JSONL contract. They reference the checked
CT-13 policy-decision chain and a persisted CT-07 occurrence edge to the selected
PolicyPair. They contain no Book, BMS, bot, CT-32, or R measure projections.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import cast

from qmf.core import (
    ExactRational,
    Fingerprint,
    Money,
    Ok,
    Result,
    World,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.core.chrono import WriterId
from qmf.core.exact import MONEY_STORAGE_SCALE
from qmf.data.journal import JournalEventType
from qmf.data.journal_producer import JournalReader
from qmf.data.store import JournalStore
from qmf.registry import EdgeType, LineageEdge, RegistryPersistence

from qmb._refuse import invalid, policy, storage
from qmb.execution.alternative import AlternativeMeasureDeclaration, AlternativeRunReceipt
from qmb.optimize.sampler import validate_trial_label
from qmb.orchestrator.ledger import fragment_path
from qmb.orchestrator.paths import (
    MAX_JSONL_BYTES,
    append_bytes_no_follow,
    mkdir_contained,
    read_contained_bytes,
)

__all__ = [
    "ALTERNATIVE_TERMINAL_CLASS",
    "ALTERNATIVE_TERMINAL_EDGE_STREAM",
    "AlternativeTerminalArtifact",
    "AlternativeTerminalStore",
]

ALTERNATIVE_TERMINAL_CLASS = "qmb-alternative-terminal-v1"
ALTERNATIVE_TERMINAL_EDGE_STREAM = "qmb-alternative-terminal-policy-pair"
_ROW_CLASS = "qmb-alternative-terminal-row-v1"
_INTENT_CLASS = "qmb-alternative-study-intent-v1"


def _plain(value: object) -> object:
    if isinstance(value, Mapping):
        entries = cast("Mapping[object, object]", value)
        return {str(key): _plain(item) for key, item in entries.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in cast("Sequence[object]", value)]
    return value


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        entries = cast("Mapping[object, object]", value)
        return MappingProxyType({str(key): _freeze(item) for key, item in entries.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in cast("Sequence[object]", value))
    return value


def _writer_identity(writer: WriterId) -> dict[str, object]:
    return {
        "boot_epoch_id": writer.boot_epoch_id,
        "machine": writer.machine,
        "role": writer.role,
        "stream": writer.stream,
    }


def _fp(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value)
    if is_refusal(parsed):
        return invalid(field, "terminal artifact contains an fp1 fingerprint")
    return parsed


def _receipt_identity(body: Mapping[str, object]) -> dict[str, object]:
    identity: dict[str, object] = {
        "class": "qmb-alternative-run-result-v1",
        "composition_fp1": body.get("composition_fp1"),
        "final_accounting_state_fp1": body.get("final_accounting_state_fp1"),
        "final_measures": body.get("final_measures"),
        "initial_accounting_state_fp1": body.get("initial_accounting_state_fp1"),
        "interpreter_registration_fp1": body.get("interpreter_registration_fp1"),
        "journal_refs": body.get("journal_refs"),
        "journal_stream": body.get("journal_stream"),
        "journal_writer": body.get("journal_writer"),
        "policy_pair_identity": body.get("policy_pair_identity"),
        "registry_fp1": body.get("registry_fp1"),
        "source_fp1": body.get("source_fp1"),
        "split_fp1": body.get("split_fp1"),
        "split_role": body.get("split_role"),
    }
    if "trial_label" in body:
        identity["trial_label"] = body.get("trial_label")
    return identity


@dataclass(frozen=True, slots=True)
class AlternativeTerminalArtifact:
    """One reopened ATC terminal result and the references needed to verify it."""

    body: Mapping[str, object]
    fingerprint: Fingerprint

    def identity(self) -> dict[str, object]:
        return cast("dict[str, object]", _plain(self.body))

    @property
    def run_receipt_fingerprint(self) -> Fingerprint:
        parsed = _fp(self.body.get("run_receipt_fp1"), "run_receipt_fp1")
        if is_refusal(parsed):  # pragma: no cover - construction validates this field
            raise ValueError("validated terminal artifact has a valid receipt fingerprint")
        return parsed.value

    @classmethod
    def from_run(
        cls,
        receipt: object,
        *,
        lineage_writer: object = None,
        trial_label: object = None,
    ) -> Result[AlternativeTerminalArtifact]:
        if not isinstance(receipt, AlternativeRunReceipt):
            return invalid("receipt", "terminal artifact consumes a typed AlternativeRunReceipt")
        computed_receipt = fingerprint(receipt.fp1_identity())
        if is_refusal(computed_receipt) or computed_receipt.value != receipt.fingerprint:
            return policy("receipt", "ATC run receipt reproduces its exact fp1 identity")
        state_fp = fingerprint(
            {
                "class": "qmb-atc-accounting-state-v1",
                "state": _plain(receipt.final_accounting_state),
            }
        )
        if is_refusal(state_fp) or state_fp.value != receipt.final_accounting_state_fingerprint:
            return policy("final_state", "terminal accounting state matches its fp1 reference")
        if not receipt.journal_references:
            return policy(
                "journal_refs", "a terminal ATC run cites its checked CT-13 decision chain"
            )
        label_body = receipt.trial_label
        if label_body is None and trial_label is not None:
            return policy(
                "trial_label", "optimizer labels are bound into CT-13 before terminalization"
            )
        if trial_label is not None:
            checked_label = validate_trial_label(trial_label)
            if is_refusal(checked_label):
                return checked_label
            if label_body is None:
                return policy("trial_label", "optimizer label exists on the checked run receipt")
            recorded_label = fingerprint(label_body)
            requested_label = fingerprint(checked_label.value)
            if (
                is_refusal(recorded_label)
                or is_refusal(requested_label)
                or recorded_label.value != requested_label.value
            ):
                return policy("trial_label", "terminal label matches the CT-13-bound receipt label")
        body: dict[str, object] = {
            "class": ALTERNATIVE_TERMINAL_CLASS,
            "composition_class": "alternative",
            "composition_fp1": receipt.config.composition_fp.value,
            "final_accounting_state": _plain(receipt.final_accounting_state),
            "final_accounting_state_fp1": receipt.final_accounting_state_fingerprint.value,
            "final_measures": [measure.fp1_identity() for measure in receipt.final_measures],
            "format_version": 1,
            "initial_accounting_state_fp1": receipt.initial_accounting_state_fingerprint.value,
            "interpreter_registration_fp1": receipt.interpreter_registration.fingerprint.value,
            "interpreter_registration": receipt.interpreter_registration.identity(),
            "journal_refs": [reference.identity() for reference in receipt.journal_references],
            "journal_stream": receipt.journal_stream,
            "journal_writer": _writer_identity(receipt.journal_writer),
            "policy_pair_identity": receipt.config.policy_pair.identity(),
            "registry_fp1": receipt.registry_fingerprint.value,
            "run_receipt_fp1": receipt.fingerprint.value,
            "source_fp1": receipt.source_fingerprint.value,
            "split_fp1": receipt.split_fingerprint.value,
            "split_role": receipt.split_role.value,
        }
        if lineage_writer is not None:
            if not isinstance(lineage_writer, WriterId):
                return invalid("lineage_writer", "terminal Pair lineage has a typed WriterId")
            body["lineage_writer"] = _writer_identity(lineage_writer)
        if label_body is not None:
            body["trial_label"] = _plain(label_body)
        receipt_identity = fingerprint(_receipt_identity(body))
        if is_refusal(receipt_identity) or receipt_identity.value != receipt.fingerprint:
            return policy("receipt", "terminal artifact preserves the exact run receipt chain")
        stamped = fingerprint(body)
        if is_refusal(stamped):
            return stamped
        return Ok(cls(cast("Mapping[str, object]", _freeze(body)), stamped.value))


@dataclass(frozen=True, slots=True)
class AlternativeTerminalStore:
    """Append-only per-WriterId QMB JSONL terminal store for ATC runs."""

    root: Path
    writer: WriterId

    @classmethod
    def try_create(cls, root: object, *, writer: object) -> Result[AlternativeTerminalStore]:
        if not isinstance(writer, WriterId):
            return invalid("writer", "ATC terminal JSONL is scoped to a QMB WriterId")
        if isinstance(root, Path):
            base = root
        elif isinstance(root, str) and root.strip():
            base = Path(root)
        else:
            return invalid("root", "ATC terminal storage uses a named QMB ledger directory")
        created = mkdir_contained(base, contain_within=base, field="alternative_ledger")
        if is_refusal(created):
            return created
        path = fragment_path(base, writer, world=World.REPLAY, role="alternative")
        if is_refusal(path):
            return path
        parent = mkdir_contained(path.value.parent, contain_within=base, field="alternative_ledger")
        if is_refusal(parent):
            return parent
        return Ok(cls(base, writer))

    @property
    def path(self) -> Path:
        """The contained replay-world alternative JSONL fragment."""
        resolved = fragment_path(self.root, self.writer, world=World.REPLAY, role="alternative")
        if is_refusal(resolved):  # pragma: no cover - validated by try_create
            raise ValueError("terminal store path remains valid")
        return resolved.value

    def append(
        self,
        receipt: object,
        *,
        journal_store: object,
        registry: object,
        lineage_writer: object,
        trial_label: object = None,
    ) -> Result[AlternativeTerminalArtifact]:
        if not isinstance(lineage_writer, WriterId):
            return invalid("lineage_writer", "CT-07 terminal lineage has its declared WriterId")
        artifact = AlternativeTerminalArtifact.from_run(
            receipt,
            lineage_writer=lineage_writer,
            trial_label=trial_label,
        )
        if is_refusal(artifact):
            return artifact
        if not isinstance(journal_store, JournalStore):
            return invalid("journal_store", "terminal write reopens the typed CT-13 journal")
        if not isinstance(registry, RegistryPersistence):
            return invalid("registry", "terminal write persists a typed CT-07 lineage edge")
        receipt_typed = cast(AlternativeRunReceipt, receipt)
        checked_chain = _verify_receipt_chain(receipt_typed, journal_store)
        if is_refusal(checked_chain):
            return checked_chain
        existing = self.read(journal_store=journal_store, registry=registry)
        if is_refusal(existing):
            return existing
        for prior in existing.value:
            if prior.run_receipt_fingerprint == artifact.value.run_receipt_fingerprint:
                if prior.identity() == artifact.value.identity():
                    return Ok(artifact.value)
                return policy("run_receipt", "an ATC run has one immutable terminal artifact")
        edge = LineageEdge.try_create(
            EdgeType.OCCURRENCE_OF,
            artifact.value.fingerprint,
            receipt_typed.config.policy_pair.policy_pair_hash,
            lineage_writer,
        )
        if is_refusal(edge):
            return edge
        persisted_edge = registry.persist_edge(
            edge.value, edge_stream=ALTERNATIVE_TERMINAL_EDGE_STREAM
        )
        if is_refusal(persisted_edge):
            return persisted_edge
        row_count = self._row_count()
        if is_refusal(row_count):
            return row_count
        sequence = row_count.value + 1
        row: dict[str, object] = {
            "artifact": artifact.value.identity(),
            "artifact_fp1": artifact.value.fingerprint.value,
            "class": _ROW_CLASS,
            "format_version": 1,
            "sequence": sequence,
            "writer": _writer_identity(self.writer),
        }
        encoded = canonical_bytes(row)
        if is_refusal(encoded):
            return encoded
        appended = append_bytes_no_follow(
            self.path,
            encoded.value + b"\n",
            contain_within=self.root,
            field="alternative_ledger",
        )
        if is_refusal(appended):
            return appended
        reopened = self.read(journal_store=journal_store, registry=registry)
        if is_refusal(reopened):
            return reopened
        if not any(item.fingerprint == artifact.value.fingerprint for item in reopened.value):
            return policy("alternative_terminal", "terminal JSONL append reopens exactly")
        return Ok(artifact.value)

    def reserve_trial(
        self,
        *,
        trial_label: object,
        candidate_fp: object,
        source_fp: object,
        split_fp: object,
    ) -> Result[None]:
        """Durably record evaluator invocation before allowing external effects.

        If the process stops after evaluation but before its terminal artifact, the
        reservation remains unresolved and the study refuses to execute that ask again.
        """
        from qmb.optimize.sampler import validate_trial_label  # noqa: PLC0415

        label = validate_trial_label(trial_label)
        if is_refusal(label):
            return label
        parsed_candidate = _fp(
            candidate_fp.value if isinstance(candidate_fp, Fingerprint) else candidate_fp,
            "candidate_fp",
        )
        parsed_source = _fp(
            source_fp.value if isinstance(source_fp, Fingerprint) else source_fp, "source_fp"
        )
        parsed_split = _fp(
            split_fp.value if isinstance(split_fp, Fingerprint) else split_fp, "split_fp"
        )
        if is_refusal(parsed_candidate):
            return parsed_candidate
        if is_refusal(parsed_source):
            return parsed_source
        if is_refusal(parsed_split):
            return parsed_split
        label_fp = fingerprint(label.value)
        if is_refusal(label_fp):
            return label_fp
        pending = self.pending_trials()
        if is_refusal(pending):
            return pending
        key = label_fp.value.value
        if key in pending.value:
            return policy("trial_intent", "one unresolved evaluator intent blocks retry")
        rows = self._read_raw_rows()
        if is_refusal(rows):
            return rows
        if any(
            row.get("intent_fp1") == key
            for row in rows.value
            if row.get("class") == _INTENT_CLASS
        ):
            return policy("trial_intent", "a trial label is reserved at most once")
        row: dict[str, object] = {
            "candidate_fp1": parsed_candidate.value.value,
            "class": _INTENT_CLASS,
            "format_version": 1,
            "intent_fp1": key,
            "sequence": len(rows.value) + 1,
            "source_fp1": parsed_source.value.value,
            "split_fp1": parsed_split.value.value,
            "trial_label": label.value,
            "writer": _writer_identity(self.writer),
        }
        encoded = canonical_bytes(row)
        if is_refusal(encoded):
            return encoded
        written = append_bytes_no_follow(
            self.path,
            encoded.value + b"\n",
            contain_within=self.root,
            field="alternative_ledger",
        )
        if is_refusal(written):
            return written
        reread = self._read_raw_rows()
        if is_refusal(reread):
            return reread
        if not any(
            item.get("intent_fp1") == key and item.get("sequence") == len(rows.value) + 1
            for item in reread.value
        ):
            return policy("trial_intent", "study intent append is physically read back")
        return Ok(None)

    def pending_trials(self) -> Result[Mapping[str, Mapping[str, object]]]:
        """Return durable evaluator intents without a matching terminal artifact."""
        rows = self._read_raw_rows()
        if is_refusal(rows):
            return rows
        artifacts = self._read_rows()
        if is_refusal(artifacts):
            return artifacts
        terminals = {
            label_fp.value
            for artifact in artifacts.value
            if (label_fp := _artifact_trial_label_fp(artifact)) is not None
        }
        intents: dict[str, Mapping[str, object]] = {}
        for row in rows.value:
            if row.get("class") != _INTENT_CLASS:
                continue
            key = cast("str", row["intent_fp1"])
            if key in terminals:
                continue
            if key in intents:
                return policy("trial_intent", "one trial label has one durable invocation intent")
            intents[key] = cast("Mapping[str, object]", _freeze(row))
        return Ok(MappingProxyType(intents))

    def _row_count(self) -> Result[int]:
        rows = self._read_raw_rows()
        if is_refusal(rows):
            return rows
        return Ok(len(rows.value))

    def _read_raw_rows(self) -> Result[tuple[Mapping[str, object], ...]]:
        if not self.path.exists():
            return Ok(())
        loaded = read_contained_bytes(
            self.path,
            contain_within=self.root,
            max_bytes=MAX_JSONL_BYTES,
            field="alternative_ledger",
        )
        if is_refusal(loaded):
            return loaded
        raw = loaded.value
        if raw and not raw.endswith(b"\n"):
            return storage("alternative_ledger", "terminal JSONL has no torn or partial tail")
        rows: list[Mapping[str, object]] = []
        for index, chunk in enumerate(raw[:-1].split(b"\n") if raw else ()):
            try:
                parsed: object = json.loads(chunk)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return storage(
                    "alternative_ledger", "terminal row is valid UTF-8 JSON", index=index
                )
            if not isinstance(parsed, Mapping):
                return storage("alternative_ledger", "terminal JSONL row is an object", index=index)
            row = cast("Mapping[str, object]", parsed)
            encoded = canonical_bytes(row)
            if is_refusal(encoded) or encoded.value != chunk:
                return storage(
                    "alternative_ledger", "terminal row uses canonical bytes", index=index
                )
            if (
                row.get("format_version") != 1
                or type(row.get("format_version")) is not int
                or row.get("sequence") != index + 1
                or type(row.get("sequence")) is not int
                or row.get("writer") != _writer_identity(self.writer)
            ):
                return storage(
                    "alternative_ledger", "terminal row sequence and writer are valid", index=index
                )
            row_class = row.get("class")
            if row_class == _INTENT_CLASS:
                label = row.get("trial_label")
                if not isinstance(label, Mapping):
                    return storage(
                        "alternative_ledger", "study intent carries a trial label", index=index
                    )
                label_fp = fingerprint(cast("Mapping[str, object]", label))
                if is_refusal(label_fp) or row.get("intent_fp1") != label_fp.value.value:
                    return policy(
                        "trial_intent", "study intent label matches its fingerprint", index=index
                    )
                for field in ("candidate_fp1", "source_fp1", "split_fp1"):
                    parsed_fp = _fp(row.get(field), field)
                    if is_refusal(parsed_fp):
                        return parsed_fp
            elif row_class != _ROW_CLASS:
                return storage(
                    "alternative_ledger", "terminal row uses a recognized class", index=index
                )
            rows.append(row)
        return Ok(tuple(rows))

    def read(
        self,
        *,
        journal_store: object,
        registry: object,
    ) -> Result[tuple[AlternativeTerminalArtifact, ...]]:
        if not isinstance(journal_store, JournalStore):
            return invalid("journal_store", "terminal read reopens the typed CT-13 journal")
        if not isinstance(registry, RegistryPersistence):
            return invalid("registry", "terminal read verifies typed CT-07 lineage edges")
        rows = self._read_rows()
        if is_refusal(rows):
            return rows
        checked_edges = registry.read_edges(
            ALTERNATIVE_TERMINAL_EDGE_STREAM,
            for_world=World.REPLAY,
        )
        if is_refusal(checked_edges):
            return checked_edges
        edge_fps = {edge.edge_fingerprint for edge in checked_edges.value}
        for artifact in rows.value:
            chain = _verify_terminal_body(artifact.body, journal_store)
            if is_refusal(chain):
                return chain
            pair_hash = _fp_nested(artifact.body, "policy_pair_identity", "policy_pair_hash")
            if is_refusal(pair_hash):
                return pair_hash
            lineage_body = artifact.body.get("lineage_writer")
            if not isinstance(lineage_body, Mapping):
                return invalid("lineage_writer", "terminal artifact pins its CT-07 writer")
            lineage_map = cast("Mapping[str, object]", lineage_body)
            lineage_writer = WriterId.try_create(
                lineage_map.get("machine"),
                lineage_map.get("role"),
                lineage_map.get("stream"),
                lineage_map.get("boot_epoch_id"),
            )
            if is_refusal(lineage_writer):
                return lineage_writer
            expected_edge = LineageEdge.try_create(
                EdgeType.OCCURRENCE_OF,
                artifact.fingerprint,
                pair_hash.value,
                lineage_writer.value,
            )
            if is_refusal(expected_edge) or expected_edge.value.edge_fingerprint not in edge_fps:
                return policy(
                    "ct07_lineage", "terminal artifact has its persisted occurrence-of Pair edge"
                )
        return rows

    def _read_rows(self) -> Result[tuple[AlternativeTerminalArtifact, ...]]:
        rows = self._read_raw_rows()
        if is_refusal(rows):
            return rows
        artifacts: list[AlternativeTerminalArtifact] = []
        for index, row in enumerate(rows.value):
            if row.get("class") == _INTENT_CLASS:
                continue
            body = row.get("artifact")
            if not isinstance(body, Mapping):
                return storage(
                    "alternative_ledger", "terminal row includes its artifact object", index=index
                )
            artifact_body = cast("Mapping[str, object]", body)
            stamped = fingerprint(artifact_body)
            if is_refusal(stamped) or row.get("artifact_fp1") != stamped.value.value:
                return policy(
                    "alternative_ledger",
                    "terminal row fingerprint matches its exact body",
                    index=index,
                )
            artifact = _parse_terminal_body(artifact_body, stamped.value)
            if is_refusal(artifact):
                return artifact
            artifacts.append(artifact.value)
        if len({item.run_receipt_fingerprint.value for item in artifacts}) != len(artifacts):
            return policy("alternative_ledger", "each ATC run has one terminal artifact")
        return Ok(tuple(artifacts))


def _parse_terminal_body(
    body: Mapping[str, object], stamped: Fingerprint
) -> Result[AlternativeTerminalArtifact]:
    if (
        body.get("class") != ALTERNATIVE_TERMINAL_CLASS
        or type(body.get("format_version")) is not int
        or body.get("format_version") != 1
        or body.get("composition_class") != "alternative"
    ):
        return invalid("alternative_terminal", "terminal artifact uses private ATC format v1")
    for field in (
        "composition_fp1",
        "initial_accounting_state_fp1",
        "final_accounting_state_fp1",
        "interpreter_registration_fp1",
        "registry_fp1",
        "run_receipt_fp1",
        "source_fp1",
        "split_fp1",
    ):
        parsed = _fp(body.get(field), field)
        if is_refusal(parsed):
            return parsed
    registration = body.get("interpreter_registration")
    if not isinstance(registration, Mapping):
        return invalid("interpreter_registration", "terminal row includes its exact registration")
    registration_fp = fingerprint(cast("Mapping[str, object]", registration))
    if is_refusal(registration_fp) or registration_fp.value.value != body.get(
        "interpreter_registration_fp1"
    ):
        return policy("interpreter_registration", "registration body matches its pinned fp1")
    declared_measures = cast("Mapping[str, object]", registration).get("declared_measures")
    if not isinstance(declared_measures, (tuple, list)):
        return invalid("declared_measures", "registration declares its ATC measure schema")
    declaration_ids: set[str] = set()
    for index, raw_declaration in enumerate(cast("Sequence[object]", declared_measures)):
        if not isinstance(raw_declaration, Mapping):
            return invalid(
                "declared_measures", "each declared ATC output has typed identity", index=index
            )
        declaration = cast("Mapping[str, object]", raw_declaration)
        measure_id = declaration.get("measure_identity")
        if (
            declaration.get("class") != "qmb-alternative-measure-declaration-v1"
            or not isinstance(measure_id, str)
            or not measure_id.strip()
            or measure_id in declaration_ids
            or not isinstance(declaration.get("unit_kind"), str)
        ):
            return invalid(
                "declared_measures", "registered measure declarations are unique and typed"
            )
        normalized_declaration = AlternativeMeasureDeclaration.try_create(
            measure_id,
            declaration.get("unit_kind"),
            declaration.get("currency"),
        )
        if is_refusal(
            normalized_declaration
        ) or normalized_declaration.value.fp1_identity() != dict(declaration):
            return invalid(
                "declared_measures", "registered measure declaration follows CT-01 units"
            )
        declaration_ids.add(measure_id)
    measures = body.get("final_measures")
    if not isinstance(measures, (tuple, list)):
        return invalid("final_measures", "terminal artifact carries an ordered measure sequence")
    contracts = {
        cast(str, cast("Mapping[str, object]", item)["measure_identity"]): cast(
            "Mapping[str, object]", item
        )
        for item in cast("Sequence[object]", declared_measures)
    }
    observed_ids: set[str] = set()
    for index, raw_measure in enumerate(cast("Sequence[object]", measures)):
        if not isinstance(raw_measure, Mapping):
            return invalid(
                "final_measures", "each persisted ATC measure has a typed body", index=index
            )
        measure = cast("Mapping[str, object]", raw_measure)
        measure_id = measure.get("measure_identity")
        contract = contracts.get(measure_id) if isinstance(measure_id, str) else None
        quantity = measure.get("quantity")
        if (
            measure.get("class") != "qmb-alternative-measure-v1"
            or not isinstance(measure_id, str)
            or measure_id in observed_ids
            or contract is None
            or measure.get("unit_kind") != contract.get("unit_kind")
            or not isinstance(quantity, Mapping)
        ):
            return policy(
                "final_measures", "terminal measures match unique registered output identities"
            )
        quantity_body = cast("Mapping[str, object]", quantity)
        if contract.get("currency") is not None:
            if quantity_body.get("class") != "money" or quantity_body.get(
                "currency"
            ) != contract.get("currency"):
                return policy("final_measures", "money output currency matches its registration")
            numerator = quantity_body.get("num")
            denominator = quantity_body.get("den")
            if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
                return invalid("final_measures", "money identity carries an exact rational amount")
            scaled = Fraction(numerator, denominator) * 10**MONEY_STORAGE_SCALE
            if scaled.denominator != 1:
                return invalid(
                    "final_measures", "money amount is representable at QMF storage scale"
                )
            parsed_quantity = Money.try_create(
                scaled.numerator,
                quantity_body.get("currency"),
                MONEY_STORAGE_SCALE,
            )
            if is_refusal(parsed_quantity):
                return parsed_quantity
            quantity_identity = parsed_quantity.value.fp1_identity()
        elif (
            "currency" in measure
            or quantity_body.get("class") != "exact-rational"
            or quantity_body.get("unit_kind") != contract.get("unit_kind")
        ):
            return policy("final_measures", "rational output unit-kind matches its registration")
        else:
            parsed_quantity = ExactRational.try_create(
                quantity_body.get("num"),
                quantity_body.get("den"),
                quantity_body.get("unit_kind"),
            )
            if is_refusal(parsed_quantity):
                return parsed_quantity
            quantity_identity = parsed_quantity.value.fp1_identity()
        if quantity_identity != dict(quantity_body):
            return invalid(
                "final_measures", "persisted measure quantity is a canonical QMF exact value"
            )
        observed_ids.add(measure_id)
    if not isinstance(body.get("final_accounting_state"), Mapping):
        return invalid("final_accounting_state", "terminal row includes the exact final state")
    if "trial_label" in body:
        label = validate_trial_label(body.get("trial_label"))
        if is_refusal(label):
            return label
        label_fp = fingerprint(label.value)
        body_label_fp = fingerprint(body.get("trial_label"))
        if (
            is_refusal(label_fp)
            or is_refusal(body_label_fp)
            or label_fp.value != body_label_fp.value
        ):
            return policy("trial_label", "terminal Study label is canonical validated identity")
    state_fp = fingerprint(
        {
            "class": "qmb-atc-accounting-state-v1",
            "state": _plain(body.get("final_accounting_state")),
        }
    )
    if is_refusal(state_fp) or state_fp.value.value != body.get("final_accounting_state_fp1"):
        return policy("final_accounting_state", "terminal final state reproduces its fp1")
    pair = body.get("policy_pair_identity")
    if not isinstance(pair, Mapping):
        return invalid("policy_pair_identity", "terminal row pins its selected PolicyPair")
    pair_map = cast("Mapping[str, object]", pair)
    if (
        not isinstance(pair_map.get("policy_pair_id"), str)
        or type(pair_map.get("policy_pair_version")) is not int
        or is_refusal(_fp(pair_map.get("policy_pair_hash"), "policy_pair_hash"))
    ):
        return invalid("policy_pair_identity", "PolicyPair identity carries id, version, and hash")
    lineage = body.get("lineage_writer")
    if not isinstance(lineage, Mapping):
        return invalid("lineage_writer", "terminal artifact pins the CT-07 writer")
    lineage_map = cast("Mapping[str, object]", lineage)
    if is_refusal(
        WriterId.try_create(
            lineage_map.get("machine"),
            lineage_map.get("role"),
            lineage_map.get("stream"),
            lineage_map.get("boot_epoch_id"),
        )
    ):
        return invalid("lineage_writer", "terminal CT-07 writer identity is valid")
    measures = body.get("final_measures")
    if not isinstance(measures, (tuple, list)):
        return invalid("final_measures", "terminal measure set is a sequence")
    if not isinstance(body.get("journal_refs"), (tuple, list)) or not body.get("journal_refs"):
        return invalid("journal_refs", "terminal run references its persisted CT-13 chain")
    recomputed_receipt = fingerprint(_receipt_identity(body))
    if is_refusal(recomputed_receipt) or recomputed_receipt.value.value != body.get(
        "run_receipt_fp1"
    ):
        return policy("run_receipt", "terminal row preserves the source run receipt identity")
    checked_body = cast("Mapping[str, object]", _freeze(body))
    return Ok(AlternativeTerminalArtifact(checked_body, stamped))


def _fp_nested(body: Mapping[str, object], outer: str, inner: str) -> Result[Fingerprint]:
    value = body.get(outer)
    if not isinstance(value, Mapping):
        return invalid(outer, "terminal identity contains its nested object")
    return _fp(cast("Mapping[str, object]", value).get(inner), inner)


def _artifact_trial_label_fp(
    artifact: AlternativeTerminalArtifact,
) -> Fingerprint | None:
    label = artifact.body.get("trial_label")
    if not isinstance(label, Mapping):
        return None
    stamped = fingerprint(cast("Mapping[str, object]", label))
    return None if is_refusal(stamped) else stamped.value


def _verify_receipt_chain(receipt: AlternativeRunReceipt, store: JournalStore) -> Result[None]:
    body = AlternativeTerminalArtifact.from_run(receipt)
    if is_refusal(body):
        return body
    return _verify_terminal_body(body.value.body, store)


def _verify_terminal_body(body: Mapping[str, object], store: object) -> Result[None]:
    if not isinstance(store, JournalStore) or store.world is not World.REPLAY:
        return invalid("journal_store", "ATC decision-chain recovery uses replay CT-13")
    stream = body.get("journal_stream")
    writer_body = body.get("journal_writer")
    if not isinstance(stream, str) or not isinstance(writer_body, Mapping):
        return invalid("journal_writer", "terminal row pins its CT-13 writer stream")
    writer_map = cast("Mapping[str, object]", writer_body)
    writer = WriterId.try_create(
        writer_map.get("machine"),
        writer_map.get("role"),
        writer_map.get("stream"),
        writer_map.get("boot_epoch_id"),
    )
    if is_refusal(writer):
        return writer
    if writer.value.stream != stream:
        return policy("journal_writer", "CT-13 writer owns the terminal's named stream")
    checked = JournalReader(store).read_checked(stream, for_world=World.REPLAY)
    if is_refusal(checked):
        return checked
    raw_rows = store.read_stream(stream, for_world=World.REPLAY)
    if is_refusal(raw_rows):
        return raw_rows
    refs = body.get("journal_refs")
    if not isinstance(refs, (tuple, list)) or not refs:
        return invalid("journal_refs", "terminal chain contains ordered CT-13 references")
    pair = cast("Mapping[str, object]", body.get("policy_pair_identity", {}))
    last_state_fp: str | None = None
    last_measures: object = None
    sequences: list[int] = []
    for index, raw_ref in enumerate(cast("Sequence[object]", refs)):
        if not isinstance(raw_ref, Mapping):
            return invalid("journal_refs", "each CT-13 reference is a mapping", index=index)
        ref = cast("Mapping[str, object]", raw_ref)
        seq, physical = ref.get("sequence"), ref.get("store_sequence")
        if type(seq) is not int or seq < 0 or type(physical) is not int or physical < 0:
            return invalid(
                "journal_refs", "logical and physical sequence are exact non-negative integers"
            )
        event_fp = _fp(ref.get("event_fp1"), "event_fp1")
        store_fp = _fp(ref.get("store_receipt_fp1"), "store_receipt_fp1")
        if is_refusal(event_fp):
            return event_fp
        if is_refusal(store_fp):
            return store_fp
        if physical >= len(raw_rows.value):
            return policy(
                "journal_refs", "terminal CT-13 event and physical row exist", index=index
            )
        matching_events = [
            candidate
            for candidate in checked.value
            if candidate.writer == writer.value
            and candidate.sequence == seq
            and candidate.fingerprint == event_fp.value
        ]
        if len(matching_events) != 1:
            return policy(
                "journal_refs",
                "logical reference resolves uniquely by writer, sequence, and event fingerprint",
                index=index,
            )
        event = matching_events[0]
        raw = raw_rows.value[physical]
        raw_fp = fingerprint(raw)
        if (
            event.writer != writer.value
            or event.sequence != seq
            or event.event_type is not JournalEventType.DECISION
            or event.fingerprint != event_fp.value
            or is_refusal(raw_fp)
            or raw_fp.value != store_fp.value
            or raw.get("fingerprint") != event.fingerprint.value
        ):
            return policy(
                "journal_refs",
                "terminal logical and physical CT-13 refs resolve exactly",
                index=index,
            )
        payload = event.payload
        if (
            payload.get("composition_class") != "alternative"
            or payload.get("composition_fp1") != body.get("composition_fp1")
            or payload.get("policy_pair_identity") != pair
            or payload.get("interpreter_registration_fp1")
            != body.get("interpreter_registration_fp1")
            or payload.get("recorded_source_fp1") != body.get("source_fp1")
            or payload.get("split_fp1") != body.get("split_fp1")
            or payload.get("split_role") != body.get("split_role")
            or payload.get("output_fp1") != ref.get("output_fp1")
        ):
            return policy(
                "journal_refs", "CT-13 decision matches terminal policy/source lineage", index=index
            )
        if payload.get("trial_label") != body.get("trial_label"):
            return policy("trial_label", "CT-13 decisions preserve the terminal Study ask label")
        prior = payload.get("accounting_state_before_fp1")
        after = payload.get("accounting_state_after_fp1")
        if not isinstance(prior, str) or not isinstance(after, str):
            return policy(
                "journal_refs", "CT-13 decision carries exact accounting state fingerprints"
            )
        if index == 0 and prior != body.get("initial_accounting_state_fp1"):
            return policy("journal_refs", "first decision starts at the declared initial state")
        if last_state_fp is not None and prior != last_state_fp:
            return policy("journal_refs", "decision chain preserves every accounting state edge")
        last_state_fp = after
        last_measures = payload.get("measures")
        sequences.append(seq)
    if sequences != sorted(set(sequences)):
        return policy("journal_refs", "terminal CT-13 refs are ordered and unique")
    if last_state_fp != body.get("final_accounting_state_fp1") or last_measures != body.get(
        "final_measures"
    ):
        return policy(
            "terminal_state", "last durable decision agrees with terminal state and measures"
        )
    return Ok(None)
