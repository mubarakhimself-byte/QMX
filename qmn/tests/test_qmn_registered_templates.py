"""Canonical CT-22/27 registered bodies decode only through official constructors."""

from __future__ import annotations

from typing import TypeVar, cast

from qmf.core import (
    Duration,
    ExactRational,
    Instant,
    Instrument,
    Money,
    Price,
    PriceDelta,
    Quantity,
    UnitKind,
    ValueFactor,
    VenueId,
    is_ok,
    is_refusal,
)
from qmf.core.refusal import Result
from qmf.risk.control_rank import ControlActionKind
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
from qmf.risk.templates import BMS_CONTRACT_FORMAT_VERSION, BmsDefinition, BookDefinition
from qmn.host.registered_templates import decode_bms_definition, decode_book_definition

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _var(name: str, unit: UnitKind, value: object) -> TemplateVariable:
    return _ok(
        TemplateVariable.try_create(
            name,
            unit,
            value,
            UiEditability.UNEDITABLE,
            AdmissionImpact.RELINT,
        )
    )


def _sections_body(definition: BookDefinition | BmsDefinition) -> dict[str, object]:
    return {name: section.fp1_identity() for name, section in definition.sections.items()}


def test_registered_book_roundtrips_exact_qmf_values_and_evidence() -> None:
    venue = _ok(VenueId.try_create("template-venue"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    money = _ok(Money.try_create(12345, "USD", 2))
    evidence = _ok(
        VariableEvidence.try_create(
            money,
            SourceLayer.NODE_DOCS,
            AuthorityGrade.AUTHORITATIVE,
            note="fixture evidence only",
        )
    )
    values = {
        "money": _var("money", UnitKind.MONEY, money),
        "price": _var("price", UnitKind.PRICE_DELTA, _ok(Price.try_create(110023, instrument, 5))),
        "delta": _var("delta", UnitKind.PRICE_DELTA, _ok(PriceDelta.try_create(23, instrument, 5))),
        "quantity": _var("quantity", UnitKind.QUANTITY, _ok(Quantity.try_create(125, "lot", 2))),
        "ratio": _var("ratio", UnitKind.COUNT, _ok(ExactRational.try_create(3, 1, UnitKind.COUNT))),
        "factor": _var(
            "factor",
            UnitKind.VALUE_FACTOR,
            _ok(ValueFactor.try_create(25, 2, instrument, "USD")),
        ),
        "duration": _var("duration", UnitKind.DURATION, _ok(Duration.try_create(1234))),
        "instant": _var("instant", UnitKind.INSTANT, _ok(Instant.try_create(1234))),
        "blank": _var("blank", UnitKind.MONEY, _ok(NotYetRuled.try_create("GAP-TEST"))),
    }
    money_with_evidence = _ok(
        TemplateVariable.try_create(
            "money_with_evidence",
            UnitKind.MONEY,
            money,
            UiEditability.UNEDITABLE,
            AdmissionImpact.RESIGN,
            evidence=evidence,
        )
    )
    values["money_with_evidence"] = money_with_evidence
    section = _ok(TemplateSection.try_create("money_rules", values))
    book = _ok(BookDefinition.try_create(1, "USD", {"money_rules": section}))
    body = {
        "accounting_currency": book.accounting_currency,
        "sections": _sections_body(book),
    }

    reopened = _ok(decode_book_definition(1, body))

    assert _ok(reopened.fingerprint()) == _ok(book.fingerprint())
    assert set(reopened.sections["money_rules"].variables) == set(values)


def test_registered_bms_roundtrips_full_rank_table() -> None:
    rows = {
        action.value: _var(
            action.value,
            UnitKind.COUNT,
            _ok(ExactRational.try_create(index, 1, UnitKind.COUNT)),
        )
        for index, action in enumerate(ControlActionKind)
    }
    section = _ok(TemplateSection.try_create("control_rank_table", rows))
    bms = _ok(
        BmsDefinition.try_create(BMS_CONTRACT_FORMAT_VERSION, {"control_rank_table": section})
    )

    reopened = _ok(
        decode_bms_definition(
            BMS_CONTRACT_FORMAT_VERSION,
            {"sections": _sections_body(bms)},
        )
    )

    assert _ok(reopened.fingerprint()) == _ok(bms.fingerprint())


def test_unknown_sections_follow_official_ignore_identity_law() -> None:
    section = _ok(
        TemplateSection.try_create(
            "future_section",
            {
                "future_value": _var(
                    "future_value",
                    UnitKind.COUNT,
                    _ok(ExactRational.try_create(9, 1, UnitKind.COUNT)),
                )
            },
        )
    )
    baseline = _ok(BookDefinition.try_create(1, "USD", {}))
    body: dict[str, object] = {
        "accounting_currency": "USD",
        "sections": {"future_section": section.fp1_identity()},
    }

    decoded = _ok(decode_book_definition(1, body))

    assert _ok(decoded.fingerprint()) == _ok(baseline.fingerprint())
    assert decoded.sections == {}


def test_malformed_nested_format_type_refuses_after_outer_mapping_is_valid() -> None:
    section = _ok(TemplateSection.try_create("money_rules", {}))
    book = _ok(BookDefinition.try_create(1, "USD", {"money_rules": section}))
    raw_section = cast(dict[str, object], _sections_body(book)["money_rules"])
    raw_section["format_version"] = True

    refused = decode_book_definition(
        1,
        {"accounting_currency": "USD", "sections": {"money_rules": raw_section}},
    )

    assert is_refusal(refused)
