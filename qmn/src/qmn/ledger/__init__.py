"""Virtual ledger and exact virtual positions (TN-25; Story 26.4).

Each Book binding carries an append-only exact scaled-integer virtual ledger
and a virtual-position fold joined by command identity. Venue positions remain
a separate observation-derived fold. Money never uses float on this path.
"""

from __future__ import annotations

from typing import Final

from qmn.ledger.attribution import (
    AttributionDeclaration,
    AttributionPartition,
    PositionModelKind,
    QuantityReconcileResult,
    prove_attribution_partition,
    reconcile_virtual_to_venue_quantity,
)
from qmn.ledger.binding_ledger import (
    LEDGER_RECORD_KINDS,
    BindingVirtualLedger,
    EntryReservationEvent,
    EntryReservationRecovery,
    FoldFillResult,
    LedgerRecord,
    LedgerRecordKind,
    refuse_float_money,
    seed_binding_ledger,
    sum_virtual_quantities,
)
from qmn.ledger.epoch import (
    EPOCH_STATE_CARRY_COUNTERS,
    EpochStateCarry,
    require_epoch_state_carry,
    validate_state_carry_declaration,
)
from qmn.ledger.native_position import (
    NATIVE_POSITION_ATTRIBUTION_CLASS,
    NATIVE_POSITION_ATTRIBUTION_VERSION,
    NativePositionAttribution,
    NativePositionEvidence,
    resolve_native_position_attribution,
    write_native_position_attribution,
)
from qmn.ledger.reservation_journal import QmfEntryReservationJournal
from qmn.ledger.treasury import (
    TREASURY_BOUNDARY_KINDS,
    TreasuryBoundaryAct,
    TreasuryBoundaryActKind,
    TreasuryBoundaryJournal,
    apply_treasury_boundary,
    journal_missed_rollover_correction,
    mint_treasury_boundary_act,
    refuse_boundary_rebase_of_r,
    refuse_paper_pnl_to_treasury,
)
from qmn.ledger.virtual import (
    ADMISSION_PLAN_EDGE,
    EXECUTION_QUALITY_SHORT_FILL,
    POSITION_KIND_VENUE,
    POSITION_KIND_VIRTUAL,
    AttributedFill,
    ExecutionQualityEvidence,
    PartialEntryRebase,
    PositionKind,
    VenuePosition,
    VenuePositionFold,
    VirtualPosition,
    VirtualPositionStatus,
    fold_venue_observation,
    guard_no_scale_in,
    mint_virtual_position,
    rebase_partial_entry,
    refuse_top_up_short_fill,
)
from qmn.ledger.virtual_journal import QmfVirtualLedgerJournal, VirtualLedgerRecovery

__all__ = [
    "ADMISSION_PLAN_EDGE",
    "EPOCH_STATE_CARRY_COUNTERS",
    "EXECUTION_QUALITY_SHORT_FILL",
    "LEDGER_RECORD_KINDS",
    "LEDGER_SURFACE",
    "NATIVE_POSITION_ATTRIBUTION_CLASS",
    "NATIVE_POSITION_ATTRIBUTION_VERSION",
    "POSITION_KIND_VENUE",
    "POSITION_KIND_VIRTUAL",
    "TREASURY_BOUNDARY_KINDS",
    "AttributedFill",
    "AttributionDeclaration",
    "AttributionPartition",
    "BindingVirtualLedger",
    "EntryReservationEvent",
    "EntryReservationRecovery",
    "EpochStateCarry",
    "ExecutionQualityEvidence",
    "FoldFillResult",
    "LedgerRecord",
    "LedgerRecordKind",
    "NativePositionAttribution",
    "NativePositionEvidence",
    "PartialEntryRebase",
    "PositionKind",
    "PositionModelKind",
    "QmfEntryReservationJournal",
    "QmfVirtualLedgerJournal",
    "QuantityReconcileResult",
    "TreasuryBoundaryAct",
    "TreasuryBoundaryActKind",
    "TreasuryBoundaryJournal",
    "VenuePosition",
    "VenuePositionFold",
    "VirtualLedgerRecovery",
    "VirtualPosition",
    "VirtualPositionStatus",
    "apply_treasury_boundary",
    "fold_venue_observation",
    "guard_no_scale_in",
    "journal_missed_rollover_correction",
    "mint_treasury_boundary_act",
    "mint_virtual_position",
    "prove_attribution_partition",
    "rebase_partial_entry",
    "reconcile_virtual_to_venue_quantity",
    "refuse_boundary_rebase_of_r",
    "refuse_float_money",
    "refuse_paper_pnl_to_treasury",
    "refuse_top_up_short_fill",
    "require_epoch_state_carry",
    "resolve_native_position_attribution",
    "seed_binding_ledger",
    "sum_virtual_quantities",
    "validate_state_carry_declaration",
    "write_native_position_attribution",
]

LEDGER_SURFACE: Final[str] = "qmn.ledger"
