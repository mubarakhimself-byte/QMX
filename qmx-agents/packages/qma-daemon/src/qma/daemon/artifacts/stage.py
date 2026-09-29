"""Library handler for authenticated PUT /artifacts/stage (Story 70.1; AM-05).

The live daemon listener must call this after pairing Bearer auth. Helpers
alone with the listener discarding bytes fail the story.
"""

from __future__ import annotations

from qma.core.vocabulary.enums import ArtifactCompleteness
from qma.daemon.artifacts.store import ArtifactStore, StagedArtifact
from qma.daemon.journal.variables import (
    ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
    resolve_artifact_stage_max_bytes,
)
from qma.wire.stage_artifact import (
    STAGE_ARTIFACT_AMENDMENT,
    STAGE_ARTIFACT_HTTP_PATH,
    require_stage_artifact_capability,
)
from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import TypedRefusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "handle_stage_artifact_put",
    "parse_stage_content_length",
    "refuse_interrupted_stage_put",
]


def parse_stage_content_length(value: object) -> Result[int]:
    """Required Content-Length. Missing or unparsable refuses with no object."""
    if value is None:
        return invalid_input(
            "content_length",
            "PUT /artifacts/stage requires Content-Length; no RFC 9110 partial PUT",
            wrote_object=False,
            http_put=STAGE_ARTIFACT_HTTP_PATH,
            named_amendment=STAGE_ARTIFACT_AMENDMENT,
        )
    if isinstance(value, bool):
        return invalid_input(
            "content_length",
            "Content-Length must be a non-negative integer",
            given=repr(value),
            wrote_object=False,
        )
    if isinstance(value, int):
        length = value
    elif isinstance(value, str) and value.strip() != "":
        raw = value.strip()
        if not raw.isdigit():
            return invalid_input(
                "content_length",
                "Content-Length must be a non-negative integer",
                given=repr(value),
                wrote_object=False,
            )
        length = int(raw)
    else:
        return invalid_input(
            "content_length",
            "PUT /artifacts/stage requires Content-Length; no RFC 9110 partial PUT",
            given=repr(value),
            wrote_object=False,
            http_put=STAGE_ARTIFACT_HTTP_PATH,
        )
    if length < 0:
        return invalid_input(
            "content_length",
            "Content-Length must be a non-negative integer",
            given=length,
            wrote_object=False,
        )
    return Ok(length)


def refuse_interrupted_stage_put() -> TypedRefusal:
    """Interrupted v1 PUT: refuse, delete incomplete bytes, mint no fp1."""
    return policy_rejection(
        "content_length",
        "interrupted PUT is refused; incomplete bytes are deleted; no partial fp1",
        completeness=ArtifactCompleteness.PARTIAL.value,
        wrote_object=False,
        http_put=STAGE_ARTIFACT_HTTP_PATH,
        named_amendment=STAGE_ARTIFACT_AMENDMENT,
    )


def handle_stage_artifact_put(
    store: ArtifactStore,
    body: bytes,
    *,
    content_length: object,
    max_bytes: object,
    capabilities: object,
) -> Result[StagedArtifact]:
    """Admit PUT bytes as local-complete possession.

    ``max_bytes`` is the injected ``registry:artifact.stage_max_bytes`` value
    (None means missing — refuse, mint no number).
    """
    gated = require_stage_artifact_capability(capabilities)
    if is_refusal(gated):
        return gated
    cap = resolve_artifact_stage_max_bytes(max_bytes)
    if is_refusal(cap):
        return cap
    length = parse_stage_content_length(content_length)
    if is_refusal(length):
        return length
    if length.value > cap.value:
        return policy_rejection(
            "content_length",
            "Content-Length exceeds registry:artifact.stage_max_bytes",
            content_length=length.value,
            registry_key=ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
            wrote_object=False,
            http_put=STAGE_ARTIFACT_HTTP_PATH,
        )
    if len(body) != length.value:
        store.abandon_incomplete()
        return refuse_interrupted_stage_put()
    return store.stage_complete_bytes(body)
