"""Closed, bounded proof inputs and immutable stage records."""

from __future__ import annotations

import json
import math
from typing import Literal, cast

from pydantic import ConfigDict, Field, JsonValue

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import StrictModel

type Stage = Literal["build", "tests", "sandbox", "shadow", "live"]
STAGES: tuple[Stage, ...] = ("build", "tests", "sandbox", "shadow", "live")


def json_document(data: bytes) -> Document:
    """The old candidate parser's finite, unambiguous UTF-8 rule survives."""

    def pairs(items: list[tuple[str, JsonValue]]) -> Document:
        result: Document = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def constant(value: str) -> JsonValue:
        raise ValueError(f"Non-finite JSON: {value}")

    def decimal(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite JSON number")
        return number

    try:
        body: JsonValue = json.loads(
            data, object_pairs_hook=pairs, parse_constant=constant, parse_float=decimal
        )
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object")
        # Also catches escaped lone surrogates before identity encoding.
        json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
        return body
    except (ValueError, UnicodeError, RecursionError) as error:
        raise AppError("invalid_proof", "Use finite, unambiguous UTF-8 JSON.") from error


class Probe(StrictModel):
    tool: str = Field(min_length=1, max_length=200)
    arguments: Document = Field(default_factory=dict)
    expected: JsonValue


class Proof(StrictModel):
    source: Literal["recorded", "live"]
    cases: list[Probe] = Field(min_length=1, max_length=100)


class Evidence(StrictModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    definition_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    version: str
    stage: Stage
    passed: bool
    inputs: Document
    versions: Document
    results: Document
    duration_seconds: float = Field(ge=0)
    parent: str | None = None
    trust: Literal["first_party", "operator", "reviewed", "agent"] = "first_party"
    expected_active: str | None = None
    action: Literal["advance", "publish", "rollback"] = "advance"

    def document(self) -> Document:
        return cast(Document, self.model_dump(mode="json"))
