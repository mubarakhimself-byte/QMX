"""In-memory local-complete artifact store for authenticated PUT /artifacts/stage.

Story 70.1 reuses the inspect ``_artifacts`` map pattern and
``before_artifact_register``. No new sqlite class.
"""

from __future__ import annotations

from qma.daemon.artifacts.stage import (
    handle_stage_artifact_put,
    parse_stage_content_length,
    refuse_interrupted_stage_put,
)
from qma.daemon.artifacts.store import (
    ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA,
    ArtifactStore,
    StagedArtifact,
    claim_stage_artifact_put_existed_at_inspect_sha,
)

__all__ = [
    "ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA",
    "ArtifactStore",
    "StagedArtifact",
    "claim_stage_artifact_put_existed_at_inspect_sha",
    "handle_stage_artifact_put",
    "parse_stage_content_length",
    "refuse_interrupted_stage_put",
]
