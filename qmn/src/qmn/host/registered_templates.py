"""Rehydrate CT-22/27 templates from their canonical CT-06 JSON identities.

QMF's public template constructors intentionally take typed children. Registry
records, however, reopen from canonical identity maps. This adapter decodes those
maps only through official QMF constructors and requires a byte-canonical identity
round trip before returning a typed definition.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast

from qmf.core import (
    Duration,
    ExactRational,
    Instant,
    Instrument,
    Money,
    Ok,
    Price,
    PriceDelta,
    Quantity,
    Result,
    UnitKind,
    ValueFactor,
    VenueId,
    canonical_bytes,
    is_refusal,
)
from qmf.core.exact import MAX_SCALE
from qmf.risk.grammar import (
    AdmissionImpact,
    AuthorityGrade,
    NotYetRuled,
    SourceLayer,
    TemplateSection,
    TemplateVariable,
    UiEditability,
    VariableEvidence,
)
from qmf.risk.templates import (
    BMS_SECTIONS,
    BOOK_SECTIONS,
    BmsDefinition,
    BookDefinition,
)

from qmn.host._refuse import invalid, policy, unavailable

__all__ = ["decode_bms_definition", "decode_book_definition"]

_GRAMMAR_FORMAT_VERSION = 1
_Decoded = TypeVar("_Decoded")


def decode_book_definition(contract_format_version: object, body: object) -> Result[BookDefinition]:
    """Decode a CT-22 body from a loaded, fingerprint-checked CT-06 record."""
    if not isinstance(body, Mapping):
        return invalid("ct22.body", "registered Book body is a canonical mapping")
    value = cast(Mapping[str, object], body)
    if set(value) != {"accounting_currency", "sections"}:
        return invalid("ct22.body", "registered Book body has its exact canonical fields")
    sections = _decode_sections(value.get("sections"))
    if is_refusal(sections):
        return sections
    decoded = BookDefinition.try_create(
        contract_format_version,
        value.get("accounting_currency"),
        sections.value,
    )
    if is_refusal(decoded):
        return decoded
    normalized_sections = _known_section_body(value, decoded.value.sections, BOOK_SECTIONS)
    if is_refusal(normalized_sections):
        return normalized_sections
    normalized = {
        "accounting_currency": value.get("accounting_currency"),
        "sections": normalized_sections.value,
    }
    if not _same_identity(normalized, _book_body_identity(decoded.value)):
        return policy("ct22.body", "typed Book re-encodes to the exact persisted body")
    return decoded


def decode_bms_definition(contract_format_version: object, body: object) -> Result[BmsDefinition]:
    """Decode a CT-27 body from a loaded, fingerprint-checked CT-06 record."""
    if not isinstance(body, Mapping):
        return invalid("ct27.body", "registered BMS body is a canonical mapping")
    value = cast(Mapping[str, object], body)
    if set(value) != {"sections"}:
        return invalid("ct27.body", "registered BMS body has its exact canonical fields")
    sections = _decode_sections(value.get("sections"))
    if is_refusal(sections):
        return sections
    decoded = BmsDefinition.try_create(contract_format_version, sections.value)
    if is_refusal(decoded):
        return decoded
    normalized_sections = _known_section_body(value, decoded.value.sections, BMS_SECTIONS)
    if is_refusal(normalized_sections):
        return normalized_sections
    normalized = {"sections": normalized_sections.value}
    if not _same_identity(normalized, _bms_body_identity(decoded.value)):
        return policy("ct27.body", "typed BMS re-encodes to the exact persisted body")
    return decoded


def _decode_sections(value: object) -> Result[dict[str, TemplateSection]]:
    if not isinstance(value, Mapping):
        return invalid("sections", "registered template sections are a canonical mapping")
    sections: dict[str, TemplateSection] = {}
    for raw_name, raw_section in cast(Mapping[object, object], value).items():
        if type(raw_name) is not str or not isinstance(raw_section, Mapping):
            return invalid("sections", "section names and canonical bodies are typed")
        section_body = cast(Mapping[str, object], raw_section)
        if set(section_body) != {"class", "name", "variables", "format_version"}:
            return invalid("section", "TemplateSection identity has its exact fields")
        if (
            section_body.get("class") != "template-section"
            or section_body.get("name") != raw_name
            or type(section_body.get("format_version")) is not int
            or section_body.get("format_version") != _GRAMMAR_FORMAT_VERSION
        ):
            return invalid("section", "section identity matches the official format and map key")
        variables_raw = section_body.get("variables")
        if not isinstance(variables_raw, Mapping):
            return invalid("section.variables", "TemplateSection variables are a mapping")
        variables: dict[str, TemplateVariable] = {}
        for raw_name_in_section, raw_variable in cast(
            Mapping[object, object], variables_raw
        ).items():
            if type(raw_name_in_section) is not str or not isinstance(raw_variable, Mapping):
                return invalid("variable", "variable names and canonical bodies are typed")
            variable = _decode_variable(cast(Mapping[str, object], raw_variable))
            if is_refusal(variable):
                return variable
            if variable.value.name != raw_name_in_section:
                return policy("variable.name", "variable identity matches its declared mapping key")
            variables[raw_name_in_section] = variable.value
        section = TemplateSection.try_create(raw_name, variables)
        if is_refusal(section):
            return section
        if not _same_identity(section_body, section.value.fp1_identity()):
            return policy("section", "typed TemplateSection exactly reproduces its identity")
        sections[raw_name] = section.value
    return Ok(sections)


def _decode_variable(value: Mapping[str, object]) -> Result[TemplateVariable]:
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
        not required.issubset(value)
        or set(value) - (required | {"evidence"})
        or value.get("class") != "template-variable"
        or type(value.get("format_version")) is not int
        or value.get("format_version") != _GRAMMAR_FORMAT_VERSION
    ):
        return invalid("template_variable", "TemplateVariable identity has exact official fields")
    name = value.get("name")
    if type(name) is not str:
        return invalid("template_variable.name", "variable name is a string")
    try:
        unit = UnitKind(cast(str, value.get("unit_kind")))
        editability = UiEditability(cast(str, value.get("ui_editable")))
        impact = AdmissionImpact(cast(str, value.get("admission_impact")))
    except (TypeError, ValueError):
        return invalid("template_variable", "declared enums are official QMF values")
    typed_value = _decode_value(value.get("value"))
    if is_refusal(typed_value):
        return typed_value
    evidence: VariableEvidence | None = None
    if "evidence" in value:
        decoded_evidence = _decode_evidence(value.get("evidence"))
        if is_refusal(decoded_evidence):
            return decoded_evidence
        evidence = decoded_evidence.value
    variable = TemplateVariable.try_create(
        name,
        unit,
        typed_value.value,
        editability,
        impact,
        evidence=evidence,
    )
    if is_refusal(variable):
        return variable
    if not _same_identity(value, variable.value.fp1_identity()):
        return policy("template_variable", "typed TemplateVariable exactly reproduces identity")
    return variable


def _decode_evidence(value: object) -> Result[VariableEvidence]:
    if not isinstance(value, Mapping):
        return invalid("variable_evidence", "recorded evidence is a canonical mapping")
    body = cast(Mapping[str, object], value)
    required = {
        "class",
        "recorded_value",
        "source_layer",
        "authority_grade",
        "is_ratified_constant",
        "format_version",
    }
    if (
        not required.issubset(body)
        or set(body) - (required | {"note"})
        or body.get("class") != "variable-evidence"
        or body.get("is_ratified_constant") is not False
        or type(body.get("format_version")) is not int
        or body.get("format_version") != _GRAMMAR_FORMAT_VERSION
    ):
        return invalid("variable_evidence", "evidence identity has exact official fields")
    try:
        layer = SourceLayer(cast(str, body.get("source_layer")))
        grade = AuthorityGrade(cast(str, body.get("authority_grade")))
    except (TypeError, ValueError):
        return invalid("variable_evidence", "evidence source and grade are official values")
    recorded = _decode_value(body.get("recorded_value"))
    if is_refusal(recorded):
        return recorded
    evidence = VariableEvidence.try_create(
        recorded.value,
        layer,
        grade,
        note=body.get("note"),
    )
    if is_refusal(evidence):
        return evidence
    if not _same_identity(body, evidence.value.fp1_identity()):
        return policy("variable_evidence", "typed evidence exactly reproduces its identity")
    return evidence


def _decode_value(value: object) -> Result[object]:
    if not isinstance(value, Mapping):
        return invalid("template_value", "declared template value is a canonical QMF mapping")
    body = cast(Mapping[str, object], value)
    kind = body.get("class")
    if kind == "not-yet-ruled":
        if set(body) != {"class", "gap_ref", "format_version"}:
            return invalid("not_yet_ruled", "blank identity has exact official fields")
        if (
            type(body.get("format_version")) is not int
            or body.get("format_version") != _GRAMMAR_FORMAT_VERSION
        ):
            return invalid("not_yet_ruled", "blank identity uses the supported grammar version")
        result = NotYetRuled.try_create(body.get("gap_ref"))
        return _identity_checked(result, body, "not_yet_ruled")
    if kind == "duration":
        if set(body) != {"class", "value_ns", "format_version"}:
            return invalid("duration", "Duration identity has exact official fields")
        result = Duration.try_create(body.get("value_ns"))
        return _identity_checked(result, body, "duration")
    if kind == "instant":
        if set(body) != {"class", "value_ns", "format_version"}:
            return invalid("instant", "Instant identity has exact official fields")
        result = Instant.try_create(body.get("value_ns"))
        return _identity_checked(result, body, "instant")
    if kind == "exact-rational":
        if set(body) != {"class", "unit_kind", "num", "den", "format_version"}:
            return invalid("exact_rational", "ExactRational identity has exact official fields")
        try:
            unit_kind = UnitKind(cast(str, body.get("unit_kind")))
        except (TypeError, ValueError):
            return invalid("exact_rational.unit_kind", "unit kind is an official QMF value")
        result = ExactRational.try_create(body.get("num"), body.get("den"), unit_kind)
        return _identity_checked(result, body, "exact_rational")
    if kind == "value-factor":
        if set(body) != {
            "class",
            "unit_kind",
            "instrument",
            "currency",
            "num",
            "den",
            "format_version",
        }:
            return invalid("value_factor", "ValueFactor identity has exact official fields")
        if body.get("unit_kind") != UnitKind.VALUE_FACTOR.value:
            return invalid("value_factor.unit_kind", "value factor uses its official unit kind")
        instrument = _decode_instrument(body.get("instrument"))
        if is_refusal(instrument):
            return instrument
        result = ValueFactor.try_create(
            body.get("num"), body.get("den"), instrument.value, body.get("currency")
        )
        return _identity_checked(result, body, "value_factor")
    if kind in {"money", "price", "price-delta", "quantity"}:
        return _decode_scaled_value(body, cast(str, kind))
    return unavailable("template_value", "value class is not in the official CT-01/02 vocabulary")


def _decode_scaled_value(body: Mapping[str, object], kind: str) -> Result[object]:
    expected = {
        "money": {
            "class",
            "unit_kind",
            "currency",
            "num",
            "den",
            "storage_scale",
            "format_version",
        },
        "price": {
            "class",
            "unit_kind",
            "instrument",
            "num",
            "den",
            "storage_scale",
            "format_version",
        },
        "price-delta": {
            "class",
            "unit_kind",
            "instrument",
            "num",
            "den",
            "storage_scale",
            "format_version",
        },
        "quantity": {"class", "unit_kind", "unit", "num", "den", "storage_scale", "format_version"},
    }[kind]
    if set(body) != expected:
        return invalid(kind, "scaled exact identity has its exact official fields")
    if type(body.get("storage_scale")) is not int or body.get("format_version") != 1:
        return invalid(kind, "scaled identity has exact storage and contract versions")
    value = body.get("num")
    denominator = body.get("den")
    if type(value) is not int or type(denominator) is not int or denominator <= 0:
        return invalid(kind, "scaled identity is a signed numerator over positive denominator")
    scale_value = _exact_decimal_scale(value, denominator)
    if is_refusal(scale_value):
        return scale_value
    if kind == "money":
        unit = UnitKind.MONEY.value
        if body.get("unit_kind") != unit:
            return invalid(kind, "money value carries its official unit kind")
        result = Money.try_create(scale_value.value[0], body.get("currency"), scale_value.value[1])
        return _identity_checked(result, body, kind)
    elif kind == "quantity":
        if body.get("unit_kind") != UnitKind.QUANTITY.value:
            return invalid(kind, "quantity value carries its official unit kind")
        result = Quantity.try_create(scale_value.value[0], body.get("unit"), scale_value.value[1])
        return _identity_checked(result, body, kind)
    else:
        instrument = _decode_instrument(body.get("instrument"))
        if is_refusal(instrument):
            return instrument
        expected_unit = UnitKind.PRICE_DELTA.value
        if body.get("unit_kind") != expected_unit:
            return invalid(kind, "price value carries its official instrument-scoped unit kind")
        if kind == "price":
            result = Price.try_create(scale_value.value[0], instrument.value, scale_value.value[1])
            return _identity_checked(result, body, kind)
        delta = PriceDelta.try_create(scale_value.value[0], instrument.value, scale_value.value[1])
        return _identity_checked(delta, body, kind)


def _decode_instrument(value: object) -> Result[Instrument]:
    if not isinstance(value, Mapping):
        return invalid("instrument", "instrument identity is a canonical mapping")
    body = cast(Mapping[str, object], value)
    if set(body) != {"venue", "symbol"}:
        return invalid("instrument", "instrument identity has exact official fields")
    venue = VenueId.try_create(body.get("venue"))
    if is_refusal(venue):
        return venue
    result = Instrument.try_create(venue.value, body.get("symbol"))
    if is_refusal(result):
        return result
    if not _same_identity(body, {"venue": result.value.venue.value, "symbol": result.value.symbol}):
        return policy("instrument", "official Instrument constructor reproduces its tag")
    return result


def _exact_decimal_scale(numerator: int, denominator: int) -> Result[tuple[int, int]]:
    for scale in range(MAX_SCALE + 1):
        scaled_numerator = numerator * (10**scale)
        if scaled_numerator % denominator == 0:
            return Ok((scaled_numerator // denominator, scale))
    return unavailable(
        "template_value", "exact rational is not representable at qmf-core MAX_SCALE"
    )


def _identity_checked(
    result: Result[_Decoded],
    expected: Mapping[str, object],
    field: str,
) -> Result[object]:
    if is_refusal(result):
        return result
    actual = getattr(result.value, "fp1_identity", None)
    if not callable(actual):
        return invalid(field, "official decoded value exposes its canonical identity")
    actual_identity = actual()
    if not isinstance(actual_identity, Mapping):
        return invalid(field, "official decoded value exposes a mapping identity")
    if not _same_identity(expected, cast(Mapping[str, object], actual_identity)):
        return policy(field, "official constructor reproduces the exact canonical identity")
    return Ok(result.value)


def _book_body_identity(value: BookDefinition) -> Mapping[str, object]:
    identity = value.fp1_identity()
    return {
        "accounting_currency": identity["accounting_currency"],
        "sections": identity["sections"],
    }


def _bms_body_identity(value: BmsDefinition) -> Mapping[str, object]:
    return {"sections": value.fp1_identity()["sections"]}


def _known_section_body(
    raw_body: Mapping[str, object],
    decoded_sections: Mapping[str, TemplateSection],
    known_names: tuple[str, ...],
) -> Result[Mapping[str, object]]:
    raw_sections = raw_body.get("sections")
    if not isinstance(raw_sections, Mapping):
        return invalid("sections", "registered definition has canonical sections")
    known = frozenset(known_names)
    return Ok(
        {
            key: value
            for key, value in cast(Mapping[str, object], raw_sections).items()
            if key in known and key in decoded_sections
        }
    )


def _same_identity(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    left_bytes = canonical_bytes(dict(left))
    right_bytes = canonical_bytes(dict(right))
    return (
        not is_refusal(left_bytes)
        and not is_refusal(right_bytes)
        and left_bytes.value == right_bytes.value
    )
