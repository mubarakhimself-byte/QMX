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
from qma.daemon.artifacts.ticket import (
    ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA,
    ARTIFACT_TRANSFER_TICKET_FOLD_ID,
    ARTIFACT_TRANSFER_TICKET_STORE,
    ARTIFACT_TRANSFER_TICKET_TABLE,
    DAEMON_DIALS_IN,
    TRANSFER_TICKET_HEADER,
    ArtifactGetRedeem,
    DestControlHandle,
    DestControlRegistry,
    DestinationPlacement,
    InvokeTransferGate,
    TransferArtifactResult,
    TransferCompleteResult,
    TransferTicket,
    TransferTicketStore,
    gate_invoke_until_transfer_complete,
    handle_transfer_artifact,
    handle_transfer_complete,
    loopback_source_not_get_target,
    place_dest_pulled_bytes,
    source_unreachable,
)

__all__ = [
    "ARTIFACT_STAGE_PUT_EXISTED_AT_INSPECT_SHA",
    "ARTIFACT_TRANSFER_TICKET_EXISTED_AT_INSPECT_SHA",
    "ARTIFACT_TRANSFER_TICKET_FOLD_ID",
    "ARTIFACT_TRANSFER_TICKET_STORE",
    "ARTIFACT_TRANSFER_TICKET_TABLE",
    "DAEMON_DIALS_IN",
    "TRANSFER_TICKET_HEADER",
    "ArtifactGetRedeem",
    "ArtifactStore",
    "DestControlHandle",
    "DestControlRegistry",
    "DestinationPlacement",
    "InvokeTransferGate",
    "StagedArtifact",
    "TransferArtifactResult",
    "TransferCompleteResult",
    "TransferTicket",
    "TransferTicketStore",
    "claim_stage_artifact_put_existed_at_inspect_sha",
    "gate_invoke_until_transfer_complete",
    "handle_stage_artifact_put",
    "handle_transfer_artifact",
    "handle_transfer_complete",
    "loopback_source_not_get_target",
    "parse_stage_content_length",
    "place_dest_pulled_bytes",
    "refuse_interrupted_stage_put",
    "source_unreachable",
]
