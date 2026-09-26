"""qma.daemon — sole QMA runtime and sole writer.

The persistence substrate (FR-Q22) is the sole durable-write boundary for the
event journal, SQLite store, and artifact store through qmf-data sinks. The
authoritative journal (FR-Q23–FR-Q25) allocates global ``journal_seq``, enforces
the closed store list, announcement law, durable-clock stamps, and v1 fold
contracts. Store-class ownership (FR-Q26) and the governed variable registry
(FR-Q36) bind write paths and configurable numbers. Store lifecycle (FR-Q37)
covers versioned migration, encrypted backup, and controlled restoration.
SemVer is display-only provenance in lockstep with the QMF workspace (AR-Q11).
"""

from __future__ import annotations

from qma.daemon.capabilities import (
    AGENT_PATH_ENFORCEMENT_EVENTS,
    AgentCapabilityStore,
    PermissionPolicyEnforcer,
    spawn_agent,
)
from qma.daemon.diagnosis import (
    DIAGNOSIS_EXISTED_AT_INSPECT_SHA,
    DIAGNOSIS_OWNER,
    DIAGNOSIS_QUERY_NAME,
    Diagnosis,
    DiagnosisQueryService,
    claim_diagnosis_query_at_inspect_sha,
    classify_failure_class,
)
from qma.daemon.discovery import (
    CONTRIBUTION_LISTING_OCCUPANCY,
    FEDERATED_SEARCH_OCCUPANCY,
    INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA,
    INSTANCE_HEALTH_OWNER,
    INSTANCE_HEALTH_QUERY_NAME,
    ContributionListingService,
    FederatedDiscoveryService,
    FederatedSearch,
    InstanceHealthService,
    claim_qmn_qmf_health_is_instance_report,
    query_instance_health,
)
from qma.daemon.hooks import (
    AGENT_REACHABLE_WRITE_VERBS,
    BYPASS_WRITE_PATHS,
    HookRegistry,
)
from qma.daemon.journal import (
    AuthoritativeJournal,
    DaemonClock,
    FoldContract,
    FoldContractRegistry,
    FoldMetadata,
    GovernedVariableRegistry,
    StoreOwnershipRegistry,
    StoreRegistry,
    order_by_announcement_journal_seq,
)
from qma.daemon.kit_journey import (
    COPILOT_REQUIRED_TO_SHIP,
    J_KIT_01,
    KIT_JOURNEY_01_E2E_AT_INSPECT_SHA,
    KIT_JOURNEY_01_INSPECT_SHA,
    HeadlessPackInvokeReport,
    JKit01Fixture,
    claim_j_kit_01_e2e_at_inspect_sha,
    refuse_copilot_required_to_ship,
    refuse_headless_in_app_panel,
)
from qma.daemon.knowledge import KnowledgeService, KnowledgeSourceRegistry
from qma.daemon.memory import MemoryAdmissionGate, MemoryProviderRegistry
from qma.daemon.observability_boundary import (
    QMB_LOGSINK_MAY_REMAIN,
    THIRD_LOGGER_MINTED,
    emit_telemetry_from_hook,
    mint_third_logger,
    place_typed_failure,
)
from qma.daemon.operator_log import (
    FOURTH_OBSERVABILITY_COMP_MINTED,
    LOGS_ARE_NOT_EVIDENCE,
    LOGS_ARE_NOT_JOURNALS,
    OPERATOR_LOG_REQUIRED_FIELDS,
    OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA,
    JsonLineFormatter,
    claim_operator_logger_at_inspect_sha,
    configure_daemon_logging,
    emit_operator_event,
)
from qma.daemon.persistence import (
    PersistenceStartupEvidence,
    PersistenceSubstrate,
)
from qma.daemon.persistence.lifecycle import DaemonStoreLifecycle
from qma.daemon.plugins import (
    ExportScanReport,
    PackLifecycleFixture,
    PackTransition,
    claim_gap_0098_closed,
)
from qma.daemon.process import DaemonProcess
from qma.daemon.retry import (
    EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA,
    HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA,
    RECONCILE_POLICY_TYPES_EXISTED_AT_INSPECT_SHA,
    HostRetryLoop,
    HostRetryResult,
    claim_effect_class_or_reconcile_policy_absent_at_inspect_sha,
    claim_host_retry_loop_at_inspect_sha,
)
from qma.daemon.sessions import (
    PRODUCT_SESSION_EXISTED_AT_INSPECT_SHA,
    PRODUCT_SESSION_OCCUPANCY,
    PRODUCT_SESSION_OWNER,
    ProductSession,
    ProductSessionContext,
    ProductSessionService,
)
from qma.daemon.staging import (
    AdmissionPipeline,
    ChangeRequest,
    ChangeRequestFixture,
    ProposalGate,
)
from qma.daemon.taskgraph import (
    NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA,
    CompileRequest,
    MissionCompiler,
    NestedMissionHost,
    TaskGraphDispatcher,
    TaskGraphStateService,
    claim_durable_edges_at_inspect_sha,
    claim_nested_connect_surface_absent_at_inspect_sha,
    claim_nested_mission_occupancy_at_inspect_sha,
    include_subgraph_at_author,
    refuse_live_graph_splice,
    refuse_live_task_graph_merge,
    refuse_merge_remote_worker_outbox,
    refuse_qmb_occupancy_write,
    refuse_second_scheduler,
)
from qma.daemon.taskgraph.restart_fixture import (
    OutboxRestartFixture,
    refuse_second_logical_b,
)
from qma.daemon.telemetry import RetentionJob, TelemetryStore

__all__ = [
    "AGENT_PATH_ENFORCEMENT_EVENTS",
    "AGENT_REACHABLE_WRITE_VERBS",
    "BYPASS_WRITE_PATHS",
    "CONTRIBUTION_LISTING_OCCUPANCY",
    "COPILOT_REQUIRED_TO_SHIP",
    "DIAGNOSIS_EXISTED_AT_INSPECT_SHA",
    "DIAGNOSIS_OWNER",
    "DIAGNOSIS_QUERY_NAME",
    "EFFECT_CLASS_TYPES_EXISTED_AT_INSPECT_SHA",
    "FEDERATED_SEARCH_OCCUPANCY",
    "FOURTH_OBSERVABILITY_COMP_MINTED",
    "HOST_RETRY_LOOP_EXISTED_AT_INSPECT_SHA",
    "INSTANCE_HEALTH_EXISTED_AT_INSPECT_SHA",
    "INSTANCE_HEALTH_OWNER",
    "INSTANCE_HEALTH_QUERY_NAME",
    "J_KIT_01",
    "KIT_JOURNEY_01_E2E_AT_INSPECT_SHA",
    "KIT_JOURNEY_01_INSPECT_SHA",
    "LOGS_ARE_NOT_EVIDENCE",
    "LOGS_ARE_NOT_JOURNALS",
    "NESTED_MISSION_OCCUPANCY_EXISTED_AT_INSPECT_SHA",
    "OPERATOR_LOGGER_EXISTED_AT_INSPECT_SHA",
    "OPERATOR_LOG_REQUIRED_FIELDS",
    "PRODUCT_SESSION_EXISTED_AT_INSPECT_SHA",
    "PRODUCT_SESSION_OCCUPANCY",
    "PRODUCT_SESSION_OWNER",
    "QMB_LOGSINK_MAY_REMAIN",
    "RECONCILE_POLICY_TYPES_EXISTED_AT_INSPECT_SHA",
    "THIRD_LOGGER_MINTED",
    "AdmissionPipeline",
    "AgentCapabilityStore",
    "AuthoritativeJournal",
    "ChangeRequest",
    "ChangeRequestFixture",
    "CompileRequest",
    "ContributionListingService",
    "DaemonClock",
    "DaemonProcess",
    "DaemonStoreLifecycle",
    "Diagnosis",
    "DiagnosisQueryService",
    "ExportScanReport",
    "FederatedDiscoveryService",
    "FederatedSearch",
    "FoldContract",
    "FoldContractRegistry",
    "FoldMetadata",
    "GovernedVariableRegistry",
    "HeadlessPackInvokeReport",
    "HookRegistry",
    "HostRetryLoop",
    "HostRetryResult",
    "InstanceHealthService",
    "JKit01Fixture",
    "JsonLineFormatter",
    "KnowledgeService",
    "KnowledgeSourceRegistry",
    "MemoryAdmissionGate",
    "MemoryProviderRegistry",
    "MissionCompiler",
    "NestedMissionHost",
    "OutboxRestartFixture",
    "PackLifecycleFixture",
    "PackTransition",
    "PermissionPolicyEnforcer",
    "PersistenceStartupEvidence",
    "PersistenceSubstrate",
    "ProductSession",
    "ProductSessionContext",
    "ProductSessionService",
    "ProposalGate",
    "RetentionJob",
    "StoreOwnershipRegistry",
    "StoreRegistry",
    "TaskGraphDispatcher",
    "TaskGraphStateService",
    "TelemetryStore",
    "__version__",
    "claim_diagnosis_query_at_inspect_sha",
    "claim_durable_edges_at_inspect_sha",
    "claim_effect_class_or_reconcile_policy_absent_at_inspect_sha",
    "claim_gap_0098_closed",
    "claim_host_retry_loop_at_inspect_sha",
    "claim_j_kit_01_e2e_at_inspect_sha",
    "claim_nested_connect_surface_absent_at_inspect_sha",
    "claim_nested_mission_occupancy_at_inspect_sha",
    "claim_operator_logger_at_inspect_sha",
    "claim_qmn_qmf_health_is_instance_report",
    "classify_failure_class",
    "configure_daemon_logging",
    "emit_operator_event",
    "emit_telemetry_from_hook",
    "include_subgraph_at_author",
    "mint_third_logger",
    "order_by_announcement_journal_seq",
    "place_typed_failure",
    "query_instance_health",
    "refuse_copilot_required_to_ship",
    "refuse_headless_in_app_panel",
    "refuse_live_graph_splice",
    "refuse_live_task_graph_merge",
    "refuse_merge_remote_worker_outbox",
    "refuse_qmb_occupancy_write",
    "refuse_second_logical_b",
    "refuse_second_scheduler",
    "spawn_agent",
]

# Display-only provenance — never identity content (AR-Q11; DEC-0335).
__version__ = "0.1.0"
