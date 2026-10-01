"""Pure QML host-side DTO and lineage helpers.

QML returns fingerprintable content and conformance verdicts. CT-06
registration receipts are stamped by the QMB composition root in
``qmb.host.bot_registration`` (CT-33 §44; AD-25; OR-06).
"""

from __future__ import annotations

from qml.host.graduation import (
    MILL_PROMOTED_FROM_IS_GOVERNED_EVIDENCE,
    MILL_PROMOTED_FROM_IS_LINEAGE,
    refuse_research_ref_as_governed_evidence,
    stamp_promoted_from_edge,
)
from qml.host.seed_cite import (
    CANDIDATE_ORIGIN,
    QMA_INVENTS_SEED_CITE,
    SEED_CITE_FIELDS,
    SEED_CITE_IN_FP1,
    HostCandidate,
    SeedCite,
    admit_candidate_origin,
    admit_seed_cite,
    attach_seed_cite,
    mint_host_candidate,
    refuse_ct07_to_knowledge_citation,
    refuse_qma_invented_seed_cite,
)

__all__ = [
    "CANDIDATE_ORIGIN",
    "MILL_PROMOTED_FROM_IS_GOVERNED_EVIDENCE",
    "MILL_PROMOTED_FROM_IS_LINEAGE",
    "QMA_INVENTS_SEED_CITE",
    "SEED_CITE_FIELDS",
    "SEED_CITE_IN_FP1",
    "HostCandidate",
    "SeedCite",
    "admit_candidate_origin",
    "admit_seed_cite",
    "attach_seed_cite",
    "mint_host_candidate",
    "refuse_ct07_to_knowledge_citation",
    "refuse_qma_invented_seed_cite",
    "refuse_research_ref_as_governed_evidence",
    "stamp_promoted_from_edge",
]
