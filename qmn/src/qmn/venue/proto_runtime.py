"""Pinned protocol descriptor compiler at the sanctioned venue boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import qmf.venue as venue_package
from qmf.core import RefusalCategory, Result, Retryability, TypedRefusal, is_refusal
from qmf.venue.proto import CompiledProto, compile_descriptor_set

__all__ = ["DEFINITIONS", "PINNED_PROTO_RUNTIME_SURFACE", "compile_pinned_descriptor"]

PINNED_PROTO_RUNTIME_SURFACE: Final[str] = "qmn.venue.proto_runtime"


DEFINITIONS: Final = Path(venue_package.__file__).resolve().parent / "protocol" / "openapi-91.pb"
"""The pinned Spotware definitions (release 91), beside the venue package this layer imports, so a
checkout and an installed env read the same file."""


def compile_pinned_descriptor(
    descriptor_set_bytes: object,
    *,
    package_name: object,
    release_tag: object,
    expected_digest: object,
) -> Result[CompiledProto]:
    """Compile exact operator-pinned bytes and refuse any digest movement."""
    if not isinstance(expected_digest, str) or not expected_digest.startswith("sha256:"):
        return _invalid("descriptor_digest", "the compiled descriptor digest is pinned sha256 data")
    compiled = compile_descriptor_set(
        descriptor_set_bytes,
        package_name=package_name,
        release_tag=release_tag,
    )
    if is_refusal(compiled):
        return compiled
    if compiled.value.artifact.descriptor_set_digest != expected_digest:
        return _policy(
            "proto_descriptor_digest",
            "descriptor bytes match the operator-pinned digest; no demonstration digest "
            "is accepted",
            failure_id="configured_runtime.proto_digest_mismatch",
        )
    return compiled


def _invalid(field: str, reason: str) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason},
    )


def _policy(field: str, reason: str, *, failure_id: str) -> TypedRefusal:
    return TypedRefusal(
        category=RefusalCategory.POLICY_REJECTION,
        retryability=Retryability.NO,
        context={"field": field, "reason": reason, "failure_id": failure_id},
    )
