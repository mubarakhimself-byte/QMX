"""Private AD-32 evidence envelope over typed admission pages and CT-06 lineage.

The envelope records which checked CT-22/27/28/33 records were assessed and
keeps incomplete admission state explicit. It does not upgrade a decoded CT-28
capability result into a fresh CT-18 check or treat an unverified SQS input as a
baseline.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from qmf.core import (
    ExactRational,
    Fingerprint,
    Ok,
    Result,
    UnitKind,
    World,
    WriteOutcome,
    canonical_bytes,
    fingerprint,
    is_refusal,
)
from qmf.data.store import EvidenceStore, StoreReceipt, WorldStore
from qmf.data.store.rooms import RoomRole
from qmf.registry import LoadedRecord
from qmf.risk.binding import (
    BookBindingRecord,
    ControlActionKind,
    ControlRankTable,
)
from qmf.risk.control_rank import ControlRankRow
from qmf.risk.grammar import TemplateVariable
from qmf.risk.templates import BmsDefinition, BookDefinition
from qml.declaration import BotDefinition, mint_bot_definition

from qmn.host._refuse import invalid, policy, unavailable
from qmn.host.configured_runtime import (
    CONFIGURED_REGISTRY_REFERENCE_KINDS,
    ConfiguredRuntimeAssessment,
    configured_registry_as_of_fingerprint,
    resolve_registered_binding,
)
from qmn.host.registered_templates import decode_bms_definition, decode_book_definition
from qmn.host.shakedown import ShakedownEvidence, ShakedownSignaturePage
from qmn.mis.signal_snapshot import SqsBaselineKey

__all__ = [
    "ADMISSION_EVIDENCE_FORMAT_VERSION",
    "AdmissionEvidenceRef",
    "derive_bms_control_rank_table",
    "persist_admission_evidence",
    "read_admission_evidence",
]

ADMISSION_EVIDENCE_FORMAT_VERSION: Final[int] = 1
_ROW_CLASS: Final[str] = "qmn-admission-evidence-row-v1"
_ROW_KIND: Final[str] = "ad32-admission-evidence"
_Lineage = tuple[
    Fingerprint,
    Mapping[str, object],
    Fingerprint,
    Mapping[str, object],
    Fingerprint,
    Mapping[str, object],
]


@dataclass(frozen=True, slots=True)
class AdmissionEvidenceRef:
    """Checked CT-11 location and full private-envelope identity."""

    envelope_fp1: Fingerprint
    archive_fp1: Fingerprint


def derive_bms_control_rank_table(value: object) -> Result[ControlRankTable]:
    """Decode the declared CT-27 control-rank section without supplying ranks.

    The template section is keyed by each CT-30 action kind and each variable's
    exact count value is its declared rank. All four actions are mandatory by the
    CT-27 contract; no missing action is synthesized.
    """
    if type(value) is not BmsDefinition:
        return invalid("bms_definition", "rank conversion receives a typed CT-27 BMS")
    section = value.sections.get("control_rank_table")
    if section is None:
        return unavailable(
            "control_rank_table",
            "the CT-27 definition does not contain its mandatory control-rank table",
            failure_id="configured_runtime.admission_rank_table_missing",
        )
    rows: list[ControlRankRow] = []
    for key, raw_variable in section.variables.items():
        if type(raw_variable) is not TemplateVariable or raw_variable.name != key:
            return invalid(
                "control_rank_table",
                "rank entries are matching typed template variables",
            )
        try:
            action = ControlActionKind(key)
        except ValueError:
            return invalid("control_rank_table", "rank entry names a CT-30 control action")
        value = raw_variable.value
        if (
            getattr(raw_variable.unit_kind, "value", None) != "count"
            or type(value) is not ExactRational
            or value.unit_kind is not UnitKind.COUNT
            or value.denominator != 1
        ):
            return invalid("control_rank_table", "each declared rank is an exact integer count")
        row = ControlRankRow.try_create(action, value.numerator)
        if is_refusal(row):
            return row
        rows.append(row.value)
    if {row.control_action_kind for row in rows} != set(ControlActionKind):
        return unavailable(
            "control_rank_table",
            "the declared CT-27 table must rank every CT-30 control action",
            failure_id="configured_runtime.admission_rank_table_incomplete",
        )
    return ControlRankTable.try_create(rows)


def persist_admission_evidence(
    store: object,
    assessment: object,
    page: object,
) -> Result[AdmissionEvidenceRef]:
    """Persist an identity-checked page wrapper, marked incomplete pending proof.

    This records real loaded registry identities and the existing typed page. The
    current CT-22/27 containers do not expose all admission requirements through
    typed projections, and the assessment has no fresh per-account CT-18
    verification or derived SQS/rung evidence. Those joins remain explicit
    blockers in this envelope.
    """
    lineage = _checked_lineage(assessment, page)
    if is_refusal(lineage):
        return lineage
    live_store = _live_store(store)
    if is_refusal(live_store):
        return live_store
    body = {
        "class": "qmn-admission-evidence-envelope-v1",
        "format_version": ADMISSION_EVIDENCE_FORMAT_VERSION,
        "status": "incomplete",
        "registry_as_of_fp1": lineage.value[0].value,
        "registered_records": lineage.value[1],
        "binding_fp1": lineage.value[2].value,
        "page": lineage.value[3],
        "page_fp1": lineage.value[4].value,
        "bms_control_rank_table": lineage.value[5],
        "missing_evidence": [
            "ct22_typed_required_venue_capabilities",
            "ct28_fresh_ct18_capability_check",
            "derived_live_sqs_baselines_for_book_sensors",
            "deployment_live_path_rung_baseline",
            "shakedown_source_binding_join",
            "operator_signature_occurrence",
            *(
                ["ct27_complete_control_rank_table"]
                if lineage.value[5].get("status") != "derived"
                else []
            ),
        ],
    }
    return _append_envelope(live_store.value, body)


def read_admission_evidence(
    store: object,
    reference: object,
) -> Result[Mapping[str, object]]:
    """Reopen and recompute the exact persisted private AD-32 envelope."""
    if type(reference) is not AdmissionEvidenceRef:
        return invalid("reference", "reader takes the exact admission evidence receipt")
    envelope_fp = _fp(reference.envelope_fp1, "envelope_fp1")
    archive_fp = _fp(reference.archive_fp1, "archive_fp1")
    if is_refusal(envelope_fp):
        return envelope_fp
    if is_refusal(archive_fp):
        return archive_fp
    live_store = _live_store(store)
    if is_refusal(live_store):
        return live_store
    rows = live_store.value.append_store.read_raw(archive_fp.value, for_world=World.LIVE)
    if is_refusal(rows):
        return rows
    raw_row: object = rows.value[0] if len(rows.value) == 1 else None
    if not isinstance(raw_row, Mapping):
        return policy("admission_evidence_row", "one checked CT-11 row reopens")
    row = cast(Mapping[str, object], raw_row)
    if (
        row.get("class") != _ROW_CLASS
        or type(row.get("format_version")) is not int
        or row.get("format_version") != ADMISSION_EVIDENCE_FORMAT_VERSION
        or row.get("artifact_class") != _ROW_KIND
        or type(row.get("body_json")) is not str
    ):
        return invalid("admission_evidence_row", "row has the exact private class and version")
    raw_body = cast(str, row["body_json"])
    try:
        parsed_body = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeError):
        return invalid("admission_evidence_body", "envelope body is canonical JSON")
    if not isinstance(parsed_body, Mapping):
        return invalid("admission_evidence_body", "envelope body is an object")
    body = cast(Mapping[str, object], parsed_body)
    if set(body) != {
        "class",
        "format_version",
        "status",
        "registry_as_of_fp1",
        "registered_records",
        "binding_fp1",
        "page",
        "page_fp1",
        "bms_control_rank_table",
        "missing_evidence",
    }:
        return invalid("admission_evidence_body", "envelope has its exact private fields")
    canonical = canonical_bytes(dict(body))
    body_fp = fingerprint(dict(body))
    raw_fp = _fp(row.get("artifact_fp1"), "artifact_fp1")
    if is_refusal(canonical):
        return canonical
    if is_refusal(body_fp):
        return body_fp
    if is_refusal(raw_fp):
        return raw_fp
    if (
        canonical.value.decode("utf-8") != raw_body
        or body_fp.value != envelope_fp.value
        or raw_fp.value != envelope_fp.value
        or body.get("class") != "qmn-admission-evidence-envelope-v1"
        or type(body.get("format_version")) is not int
        or body.get("format_version") != ADMISSION_EVIDENCE_FORMAT_VERSION
        or body.get("status") != "incomplete"
    ):
        return policy(
            "admission_evidence_identity",
            "body and receipt match the incomplete envelope",
        )
    page = body.get("page")
    if not isinstance(page, Mapping):
        return invalid("page", "persisted AD-32 page is a canonical mapping")
    page_fp = _fp(body.get("page_fp1"), "page_fp1")
    if is_refusal(page_fp):
        return page_fp
    actual_page_fp = fingerprint(dict(cast(Mapping[str, object], page)))
    if is_refusal(actual_page_fp):
        return actual_page_fp
    if actual_page_fp.value != page_fp.value:
        return policy("page_fp1", "stored page identity recomputes from the complete page body")
    records_raw = body.get("registered_records")
    if not isinstance(records_raw, Mapping):
        return invalid(
            "registered_records", "envelope retains its four typed registry record bodies"
        )
    records = cast(Mapping[str, object], records_raw)
    checked_records = _validate_registered_record_bodies(records)
    if is_refusal(checked_records):
        return checked_records
    as_of = _fp(body.get("registry_as_of_fp1"), "registry_as_of_fp1")
    binding = _fp(body.get("binding_fp1"), "binding_fp1")
    if is_refusal(as_of):
        return as_of
    if is_refusal(binding):
        return binding
    identities = {
        name: cast(Mapping[str, object], records[name])["stable_id"]
        for name in sorted(CONFIGURED_REGISTRY_REFERENCE_KINDS)
    }
    recomputed_as_of = fingerprint(
        {"class": "qmn-configured-registry-as-of-v1", "records": identities}
    )
    if is_refusal(recomputed_as_of):
        return recomputed_as_of
    if recomputed_as_of.value != as_of.value:
        return policy(
            "registered_records",
            "registry-as-of identity matches the retained checked CT-06 bodies",
        )
    binding_check = _decode_registered_binding(records)
    if is_refusal(binding_check):
        return binding_check
    if binding_check.value != binding.value:
        return policy("binding_fp1", "CT-28 full body decodes to the retained binding identity")
    rank_table_raw = body.get("bms_control_rank_table")
    if not isinstance(rank_table_raw, Mapping):
        return invalid("bms_control_rank_table", "rank status is a typed private mapping")
    rank_table = cast(Mapping[str, object], rank_table_raw)
    status = rank_table.get("status")
    if status == "unavailable":
        if dict(rank_table) != {
            "status": "unavailable",
            "reason": "typed-rank-table-unavailable",
        }:
            return invalid("bms_control_rank_table", "unavailable rank status has exact fields")
    elif status == "derived":
        if set(rank_table) != {"status", "identity"} or not isinstance(
            rank_table.get("identity"), Mapping
        ):
            return invalid("bms_control_rank_table", "derived rank table carries typed identity")
        rank_identity = cast(Mapping[str, object], rank_table["identity"])
        body_bms = cast(Mapping[str, object], records["ct27_fp1"])["body"]
        decoded_bms = _decode_registered_bms_rank_identity(body_bms)
        if is_refusal(decoded_bms):
            return decoded_bms
        if not _canonical_equal(rank_identity, decoded_bms.value):
            return policy(
                "bms_control_rank_table", "rank table recomputes from retained CT-27 body"
            )
    else:
        return invalid("bms_control_rank_table", "rank status is derived or explicitly unavailable")
    missing = body.get("missing_evidence")
    if (
        not isinstance(missing, list)
        or any(type(item) is not str or not item for item in cast(list[object], missing))
        or len(set(cast(list[str], missing))) != len(cast(list[str], missing))
    ):
        return invalid("missing_evidence", "incomplete status lists unique named missing evidence")
    return Ok(MappingProxyType(dict(body)))


def _validate_registered_record_bodies(
    records: Mapping[str, object],
) -> Result[None]:
    if set(records) != set(CONFIGURED_REGISTRY_REFERENCE_KINDS):
        return invalid("registered_records", "exactly CT-22/27/28/33 records are retained")
    identities: dict[str, str] = {}
    for name, expected_kind in CONFIGURED_REGISTRY_REFERENCE_KINDS.items():
        raw = records.get(name)
        if not isinstance(raw, Mapping):
            return invalid(name, "registered record retains its canonical mapping")
        record = cast(Mapping[str, object], raw)
        if set(record) != {
            "kind",
            "stable_id",
            "contract_format_version",
            "at_birth_parent_refs",
            "body",
            "format_version",
        }:
            return invalid(name, "registered record has its exact retained identity fields")
        if (
            record.get("kind") != expected_kind
            or type(record.get("contract_format_version")) is not int
            or cast(int, record.get("contract_format_version")) <= 0
            or type(record.get("format_version")) is not int
            or cast(int, record.get("format_version")) <= 0
            or not isinstance(record.get("body"), Mapping)
            or not isinstance(record.get("at_birth_parent_refs"), list)
        ):
            return invalid(name, "registered record has typed kind, version, refs, and body")
        stable = _fp(record.get("stable_id"), f"{name}.stable_id")
        if is_refusal(stable):
            return stable
        parent_refs: list[Fingerprint] = []
        for value in cast(list[object], record["at_birth_parent_refs"]):
            parent = _fp(value, f"{name}.at_birth_parent_refs")
            if is_refusal(parent):
                return parent
            parent_refs.append(parent.value)
        computed = fingerprint(
            {
                "class": "registration-record",
                "kind": expected_kind,
                "contract_format_version": record["contract_format_version"],
                "at_birth_parent_refs": [ref.value for ref in parent_refs],
                "body": dict(cast(Mapping[str, object], record["body"])),
                "format_version": record["format_version"],
            }
        )
        if is_refusal(computed):
            return computed
        if stable.value != computed.value:
            return policy(name, "retained registration body recomputes its full CT-06 identity")
        identities[name] = stable.value.value
    return Ok(None)


def _decode_registered_binding(
    records: Mapping[str, object],
) -> Result[Fingerprint]:
    book_record = cast(Mapping[str, object], records["ct22_fp1"])
    bms_record = cast(Mapping[str, object], records["ct27_fp1"])
    book = decode_book_definition(book_record["contract_format_version"], book_record["body"])
    if is_refusal(book):
        return book
    bms = decode_bms_definition(bms_record["contract_format_version"], bms_record["body"])
    if is_refusal(bms):
        return bms
    book_fp = book.value.fingerprint()
    bms_fp = bms.value.fingerprint()
    if is_refusal(book_fp):
        return book_fp
    if is_refusal(bms_fp):
        return bms_fp
    ct28 = cast(Mapping[str, object], records["ct28_fp1"])
    binding = resolve_registered_binding(
        ct28["body"],
        expected_book_fp=book_fp.value,
        expected_bms_fp=bms_fp.value,
    )
    if is_refusal(binding):
        return binding
    return binding.value.fingerprint()


def _decode_registered_bms_rank_identity(value: object) -> Result[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return invalid("ct27_body", "rank adapter reads a typed CT-27 body")
    ct27_body = cast(Mapping[str, object], value)
    raw_sections_value = ct27_body.get("sections")
    if not isinstance(raw_sections_value, Mapping):
        return invalid("ct27_body.sections", "CT-27 sections are a mapping")
    raw_sections = cast(Mapping[str, object], raw_sections_value)
    raw_section = raw_sections.get("control_rank_table")
    if not isinstance(raw_section, Mapping):
        return unavailable(
            "control_rank_table",
            "retained CT-27 body lacks the control-rank table",
            failure_id="configured_runtime.admission_rank_table_missing",
        )
    section = cast(Mapping[str, object], raw_section)
    variables_raw = section.get("variables")
    if not isinstance(variables_raw, Mapping):
        return invalid("ct27_body.control_rank_table.variables", "declared rank rows are mappings")
    rows: list[ControlRankRow] = []
    for name, raw_variable in cast(Mapping[str, object], variables_raw).items():
        if type(name) is not str or not isinstance(raw_variable, Mapping):
            return invalid("ct27_body.control_rank_table", "rank rows have named mappings")
        variable = cast(Mapping[str, object], raw_variable)
        required = {
            "class",
            "name",
            "unit_kind",
            "value",
            "ui_editable",
            "admission_impact",
            "format_version",
        }
        if (
            not required.issubset(variable)
            or set(variable) - (required | {"evidence"})
            or variable.get("class") != "template-variable"
            or variable.get("name") != name
            or variable.get("unit_kind") != UnitKind.COUNT.value
            or type(variable.get("format_version")) is not int
            or variable.get("format_version") != 1
        ):
            return invalid(
                "ct27_body.control_rank_table",
                "rank variable matches official typed identity",
            )
        value = variable.get("value")
        if not isinstance(value, Mapping):
            return invalid("ct27_body.control_rank_table.value", "rank is an exact value identity")
        exact = cast(Mapping[str, object], value)
        if (
            exact.get("class") != "exact-rational"
            or exact.get("unit_kind") != UnitKind.COUNT.value
            or type(exact.get("format_version")) is not int
            or exact.get("format_version") != 1
        ):
            return invalid(
                "ct27_body.control_rank_table.value",
                "rank value is exact-rational count",
            )
        denominator = exact.get("den")
        numerator = exact.get("num")
        if type(denominator) is not int or denominator != 1 or type(numerator) is not int:
            return invalid("ct27_body.control_rank_table.value", "control rank is an exact integer")
        try:
            action = ControlActionKind(name)
        except ValueError:
            return invalid("ct27_body.control_rank_table", "rank names a registered CT-30 action")
        row = ControlRankRow.try_create(action, numerator)
        if is_refusal(row):
            return row
        rows.append(row.value)
    if {row.control_action_kind for row in rows} != set(ControlActionKind):
        return unavailable(
            "control_rank_table",
            "retained CT-27 body ranks every CT-30 action",
            failure_id="configured_runtime.admission_rank_table_incomplete",
        )
    table = ControlRankTable.try_create(rows)
    if is_refusal(table):
        return table
    return Ok(table.value.fp1_identity())


def _checked_lineage(
    assessment: object,
    page: object,
) -> Result[_Lineage]:
    if type(assessment) is not ConfiguredRuntimeAssessment:
        return invalid("assessment", "lineage is derived from the configured-runtime assessment")
    if type(page) is not ShakedownSignaturePage or type(page.shakedown) is not ShakedownEvidence:
        return invalid("page", "AD-32 wrapper carries the exact typed signature page")
    if (
        type(assessment.book_definition) is not BookDefinition
        or type(assessment.bms_definition) is not BmsDefinition
        or type(assessment.bot_definition) is not BotDefinition
        or type(assessment.binding_record) is not BookBindingRecord
    ):
        return invalid("assessment", "assessment retains the exact official typed definitions")
    records = assessment.registered_records
    if set(records) != set(CONFIGURED_REGISTRY_REFERENCE_KINDS):
        return invalid("registered_records", "assessment resolves exactly CT-22/27/28/33")
    as_of = configured_registry_as_of_fingerprint(records)
    if is_refusal(as_of):
        return as_of
    if as_of.value != assessment.registry_as_of:
        return policy("registry_as_of", "assessment identity matches its exact loaded records")
    encoded_records: dict[str, object] = {}
    for key, expected_kind in CONFIGURED_REGISTRY_REFERENCE_KINDS.items():
        record = records[key]
        if type(record) is not LoadedRecord or record.kind != expected_kind:
            return invalid(key, "registry reference reopens as its expected CT-06 kind")
        record_body = cast(object, record.body)
        if (
            type(record.contract_format_version) is not int
            or record.contract_format_version <= 0
            or type(record.format_version) is not int
            or record.format_version <= 0
            or type(record.at_birth_parent_refs) is not tuple
            or not isinstance(record_body, Mapping)
            or any(type(field) is not str for field in cast(Mapping[object, object], record_body))
        ):
            return invalid(key, "loaded CT-06 fields have exact identity-bearing types")
        stable_id = _fp(record.stable_id, f"{key}.stable_id")
        persisted_id = _fp(record.persisted_fingerprint, f"{key}.persisted_fingerprint")
        if is_refusal(stable_id):
            return stable_id
        if is_refusal(persisted_id):
            return persisted_id
        parent_refs: list[Fingerprint] = []
        for parent in cast(tuple[object, ...], record.at_birth_parent_refs):
            parsed_parent = _fp(parent, f"{key}.at_birth_parent_refs")
            if is_refusal(parsed_parent):
                return parsed_parent
            parent_refs.append(parsed_parent.value)
        computed = fingerprint(
            {
                "class": "registration-record",
                "kind": record.kind,
                "contract_format_version": record.contract_format_version,
                "at_birth_parent_refs": [ref.value for ref in parent_refs],
                "body": dict(record.body),
                "format_version": record.format_version,
            }
        )
        if is_refusal(computed):
            return computed
        if computed.value != stable_id.value or persisted_id.value != stable_id.value:
            return policy(key, "loaded CT-06 full body recomputes its persisted stable identity")
        encoded_records[key] = {
            "kind": record.kind,
            "stable_id": stable_id.value.value,
            "contract_format_version": record.contract_format_version,
            "at_birth_parent_refs": [ref.value for ref in parent_refs],
            "body": dict(record.body),
            "format_version": record.format_version,
        }
    book_fp = assessment.book_definition.fingerprint()
    bms_fp = assessment.bms_definition.fingerprint()
    if is_refusal(book_fp):
        return book_fp
    if is_refusal(bms_fp):
        return bms_fp
    loaded_book = records["ct22_fp1"]
    loaded_bms = records["ct27_fp1"]
    decoded_book = decode_book_definition(
        loaded_book.contract_format_version,
        loaded_book.body,
    )
    decoded_bms = decode_bms_definition(
        loaded_bms.contract_format_version,
        loaded_bms.body,
    )
    if is_refusal(decoded_book):
        return decoded_book
    if is_refusal(decoded_bms):
        return decoded_bms
    decoded_book_fp = decoded_book.value.fingerprint()
    decoded_bms_fp = decoded_bms.value.fingerprint()
    if is_refusal(decoded_book_fp):
        return decoded_book_fp
    if is_refusal(decoded_bms_fp):
        return decoded_bms_fp
    if decoded_book_fp.value != book_fp.value or decoded_bms_fp.value != bms_fp.value:
        return policy(
            "definitions",
            "assessment and checked CT-06 records decode to the same typed definitions",
        )
    bot = mint_bot_definition(
        records["ct33_fp1"].body,
        format_version=records["ct33_fp1"].contract_format_version,
        at_birth_parent_refs=records["ct33_fp1"].at_birth_parent_refs,
    )
    if is_refusal(bot):
        return bot
    bot_fp = bot.value.fingerprint_content()
    assessment_bot_fp = assessment.bot_definition.fingerprint_content()
    if is_refusal(bot_fp):
        return bot_fp
    if is_refusal(assessment_bot_fp):
        return assessment_bot_fp
    if (
        not _canonical_equal(records["ct33_fp1"].body, bot.value.body())
        or bot.value.identity_payload() != assessment.bot_definition.identity_payload()
        or assessment_bot_fp.value != bot_fp.value
    ):
        return policy("ct33_fp1", "typed CT-33 matches the checked registered body")
    binding = resolve_registered_binding(
        records["ct28_fp1"].body,
        expected_book_fp=book_fp.value,
        expected_bms_fp=bms_fp.value,
    )
    if is_refusal(binding):
        return binding
    binding_fp = binding.value.fingerprint()
    assessed_binding_fp = assessment.binding_record.fingerprint()
    if is_refusal(binding_fp):
        return binding_fp
    if is_refusal(assessed_binding_fp):
        return assessed_binding_fp
    if type(page.shakedown.sqs_baseline) is not SqsBaselineKey:
        return invalid("page.shakedown.sqs_baseline", "page carries its typed SQS key")
    if (
        not _canonical_equal(records["ct28_fp1"].body, binding.value.fp1_identity())
        or assessed_binding_fp.value != binding_fp.value
        or assessment.binding_fingerprint != binding_fp.value
        or binding.value.world is not World.LIVE
        or binding.value.venue_id != page.shakedown.sqs_baseline.venue
    ):
        return policy("ct28_fp1", "page scope matches exact live binding and definition lineage")
    try:
        page_body = dict(page.as_mapping())
    except (AttributeError, TypeError, ValueError):
        return invalid("page", "signature page's nested evidence is well-formed")
    page_fp = fingerprint(page_body)
    if is_refusal(page_fp):
        return page_fp
    rank_table = derive_bms_control_rank_table(assessment.bms_definition)
    rank_identity: Mapping[str, object]
    if is_refusal(rank_table):
        rank_identity = MappingProxyType(
            {"status": "unavailable", "reason": "typed-rank-table-unavailable"}
        )
    else:
        rank_identity = MappingProxyType(
            {"status": "derived", "identity": rank_table.value.fp1_identity()}
        )
    return Ok(
        (
            as_of.value,
            MappingProxyType(encoded_records),
            binding_fp.value,
            MappingProxyType(page_body),
            page_fp.value,
            rank_identity,
        )
    )


def _append_envelope(store: WorldStore, body: Mapping[str, object]) -> Result[AdmissionEvidenceRef]:
    body_fp = fingerprint(dict(body))
    encoded = canonical_bytes(dict(body))
    if is_refusal(body_fp):
        return body_fp
    if is_refusal(encoded):
        return encoded
    row: dict[str, object] = {
        "class": _ROW_CLASS,
        "format_version": ADMISSION_EVIDENCE_FORMAT_VERSION,
        "artifact_class": _ROW_KIND,
        "artifact_fp1": body_fp.value.value,
        "body_json": encoded.value.decode("utf-8"),
    }
    expected_row_fp = fingerprint([row])
    if is_refusal(expected_row_fp):
        return expected_row_fp
    receipt = store.append_store.append_raw([row])
    if is_refusal(receipt):
        return receipt
    actual_receipt = receipt.value
    if not _valid_receipt(actual_receipt, expected_row_fp.value):
        return policy("store_receipt", "CT-11 receipt identifies the retained LIVE envelope")
    readback = store.append_store.read_raw(actual_receipt.fingerprint, for_world=World.LIVE)
    if is_refusal(readback):
        return readback
    if len(readback.value) != 1 or readback.value[0] != row:
        return policy("readback", "the exact CT-11 envelope row is checked before success")
    return Ok(AdmissionEvidenceRef(body_fp.value, actual_receipt.fingerprint))


def _live_store(store: object) -> Result[WorldStore]:
    if type(store) is not EvidenceStore:
        return invalid("store", "AD-32 wrapper uses the exact QMF EvidenceStore")
    return store.for_world(World.LIVE)


def _valid_receipt(value: object, expected: Fingerprint) -> bool:
    return (
        type(value) is StoreReceipt
        and value.fingerprint == expected
        and value.world is World.LIVE
        and value.room_role is RoomRole.IMMUTABLE_RAW_ARCHIVE
        and value.engine == "parquet"
        and value.is_evidence_bearing is True
        and value.retained_forever is True
        and type(value.format_version) is int
        and value.format_version == 1
        and type(value.outcome) is WriteOutcome
        and value.sequence is None
        and value.engine_major is None
        and value.rebuild_calendar_identity is None
        and value.rebuild_tzdata_version is None
    )


def _fp(value: object, field: str) -> Result[Fingerprint]:
    parsed = Fingerprint.try_create(value.value if type(value) is Fingerprint else value)
    if is_refusal(parsed):
        return invalid(field, "identity is an exact fp1 fingerprint")
    return parsed


def _canonical_equal(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    left_bytes = canonical_bytes(dict(left))
    right_bytes = canonical_bytes(dict(right))
    return (
        not is_refusal(left_bytes)
        and not is_refusal(right_bytes)
        and left_bytes.value == right_bytes.value
    )
