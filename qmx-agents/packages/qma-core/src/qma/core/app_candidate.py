"""MA02 v1 data-only candidate descriptors; no evaluator or publication authority."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

from qmf.core import Fingerprint, Ok, Result, is_refusal
from qmf.core.fingerprint import canonical_bytes
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal


def invalid_input(field: str, reason: str, **extra: object) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason, **extra},
    )


CONTENT_SCHEMA: Final[str] = "qma.miniapp.candidate-content.v1"
VERSION_SCHEMA: Final[str] = "qma.miniapp.candidate-version.v1"


def validate_unicode(value: object, field: str) -> Result[None]:
    """Reject lone surrogates before UTF-8 identity encoding; preserve valid text."""
    pending = [value]
    visited: set[int] = set()
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeEncodeError:
                return invalid_input(
                    field, "text must contain valid Unicode encodable as UTF-8"
                )
        elif isinstance(item, Mapping):
            body = cast(Mapping[object, object], item)
            if id(body) in visited:
                continue
            visited.add(id(body))
            pending.extend(body.keys())
            pending.extend(body.values())
        elif isinstance(item, (list, tuple)):
            sequence = cast(list[object] | tuple[object, ...], item)
            if id(sequence) in visited:
                continue
            visited.add(id(sequence))
            pending.extend(sequence)
    return Ok(None)


def json_object(content: bytes) -> Result[dict[str, object]]:
    """Decode finite JSON, rejecting duplicate keys and non-object roots."""

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant: {value}")

    def decimal(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number")
        return result

    try:
        value: object = json.loads(
            content,
            object_pairs_hook=pairs,
            parse_constant=constant,
            parse_float=decimal,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        return invalid_input("content", f"expected finite, unambiguous JSON: {exc}")
    if not isinstance(value, dict):
        return invalid_input("content", "expected a JSON object")
    body = cast(dict[str, object], value)
    unicode = validate_unicode(body, "content")
    if is_refusal(unicode):
        return unicode
    return Ok(body)


def token(field: str, value: object) -> Result[str]:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return invalid_input(
            field, "expected a non-empty string without surrounding whitespace"
        )
    unicode = validate_unicode(value, field)
    if is_refusal(unicode):
        return unicode
    return Ok(value)


def artifact_ref(value: object) -> Result[dict[str, object]]:
    """An inert complete-byte reference, never a path, URL, grant or entrypoint."""
    if not isinstance(value, Mapping):
        return invalid_input("artifact_ref", "expected fp1, byte_count and media_type")
    body = dict(cast(Mapping[str, object], value))
    if set(body) != {"fp1", "byte_count", "media_type"}:
        return invalid_input(
            "artifact_ref", "expected exactly fp1, byte_count and media_type"
        )
    parsed = Fingerprint.try_create(body["fp1"])
    if is_refusal(parsed):
        return parsed
    count = body["byte_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return invalid_input("byte_count", "expected a non-negative integer")
    media = token("media_type", body["media_type"])
    if is_refusal(media):
        return media
    return Ok(body)


@dataclass(frozen=True, slots=True)
class CandidateContent:
    """Canonical immutable descriptor bytes; nested caller containers are detached."""

    encoded: bytes

    def to_payload(self) -> dict[str, object]:
        return cast(dict[str, object], json.loads(self.encoded))

    def refs(self) -> tuple[dict[str, object], ...]:
        body = self.to_payload()
        return (
            cast(dict[str, object], body["composition_ref"]),
            *cast(list[dict[str, object]], body["source_refs"]),
            *cast(list[dict[str, object]], body["asset_refs"]),
        )


def parse_candidate_content(value: object) -> Result[CandidateContent]:
    if not isinstance(value, Mapping):
        return invalid_input(
            "content", "expected the named data-only candidate descriptor"
        )
    body = dict(cast(Mapping[str, object], value))
    if set(body) != {
        "schema",
        "kind",
        "metadata",
        "composition_ref",
        "source_refs",
        "asset_refs",
    }:
        return invalid_input(
            "content", "unknown or missing candidate descriptor fields"
        )
    if body["schema"] != CONTENT_SCHEMA or body["kind"] != "data-only":
        return invalid_input(
            "schema", "MA02 accepts only v1 data-only candidate content"
        )
    metadata = body["metadata"]
    if not isinstance(metadata, Mapping):
        return invalid_input("metadata", "expected title and description")
    meta = dict(cast(Mapping[str, object], metadata))
    if set(meta) != {"title", "description"}:
        return invalid_input("metadata", "expected exactly title and description")
    title = token("title", meta["title"])
    if is_refusal(title):
        return title
    if not isinstance(meta["description"], str):
        return invalid_input("description", "expected text")
    comp = artifact_ref(body["composition_ref"])
    if is_refusal(comp):
        return comp
    if comp.value["media_type"] != "application/json":
        return invalid_input(
            "composition_ref", "composition must name application/json bytes"
        )
    for field in ("source_refs", "asset_refs"):
        refs = body[field]
        if not isinstance(refs, list):
            return invalid_input(
                field, "expected an array of immutable artifact references"
            )
        seen: set[str] = set()
        for ref in cast(list[object], refs):
            parsed = artifact_ref(ref)
            if is_refusal(parsed):
                return parsed
            fp1 = cast(str, parsed.value["fp1"])
            if fp1 in seen:
                return invalid_input(field, "duplicate artifact reference")
            seen.add(fp1)
    unicode = validate_unicode(body, "content")
    if is_refusal(unicode):
        return unicode
    encoded = canonical_bytes(body)
    if is_refusal(encoded):
        return encoded
    return Ok(CandidateContent(encoded.value))
