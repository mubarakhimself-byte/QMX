"""Story 47.3 — stage and apply verified RefinementProposals (FR-Q66; CT-50)."""

from __future__ import annotations

from typing import cast

from qma.core.ports.refinement import (
    STAGING_STORE_RECORD_TYPE,
)
from qma.core.vocabulary.enums import RefinementEditKind
from qma.daemon.staging import ProposalGate
from qmf.core import is_ok


def test_staging_store_accepts_only_refinement_proposal() -> None:
    gate = ProposalGate()
    assert gate.record_type == STAGING_STORE_RECORD_TYPE
    accepted = gate.accept(
        summary="narrow toolset",
        rationale="mission needs fewer tools",
        edits=[
            {
                "kind": "toolset",
                "operation": "create",
                "id": "research.readonly",
                "content": {"tools": ["market.read"]},
            }
        ],
        expected_outcome="toolset available",
        proposal_id="p-store",
    )
    assert is_ok(accepted)
    payload = accepted.value.to_payload()
    assert payload["type"] == STAGING_STORE_RECORD_TYPE
    assert payload["summary"]
    assert payload["rationale"]
    assert payload["expected_outcome"]
    assert accepted.value.edits[0].kind is RefinementEditKind.TOOLSET
    edits = cast("list[dict[str, object]]", payload["edits"])
    operations = {str(edit["operation"]) for edit in edits}
    kinds = {str(edit["kind"]) for edit in edits}
    assert operations <= {"create", "update", "delete"}
    assert kinds <= {
        "prompt",
        "memory",
        "skill",
        "toolset",
        "worker_template",
        "hook",
        "graph_template",
        "loop",
        "role",
    }
