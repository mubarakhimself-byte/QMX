"""Closed-and-addable wire packet vocabulary (CT-40; AD-5; DEC-0304; FR-Q21).

Ownership of every command, query, and event family name sits in ``qma-wire``.
New families are added only by editing this registry — never coined locally by a
client, worker, plugin, or daemon module.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

__all__ = [
    "ADDABLE_COMMAND_COUNT",
    "ADDABLE_QUERY_COUNT",
    "SEED_COMMAND_COUNT",
    "SEED_EVENT_COUNT",
    "SEED_QUERY_COUNT",
    "SEED_VOCABULARY_COUNT",
    "WIRE_COMMANDS",
    "WIRE_EVENTS",
    "WIRE_QUERIES",
    "WIRE_VOCABULARY_OWNER",
    "MessageFamily",
    "WireCommand",
    "WireEvent",
    "WireQuery",
    "WireVocabularyError",
    "family_of",
    "parse_wire_type",
]


WIRE_VOCABULARY_OWNER: Final[str] = "qma-wire"

SEED_COMMAND_COUNT: Final[int] = 9
SEED_QUERY_COUNT: Final[int] = 7
SEED_EVENT_COUNT: Final[int] = 10
SEED_VOCABULARY_COUNT: Final[int] = SEED_COMMAND_COUNT + SEED_QUERY_COUNT + SEED_EVENT_COUNT
# Closed-and-addable extensions beyond the packet seed:
# list_mission_hooks (FR-Q35; AD-11), plugin_install_preflight (FR-Q69; AD-21),
# facade_search / facade_get for federated discovery (FR-RES-18; DEC-0449),
# get_diagnosis for kit failure_class (Story 61.2; DEC-0456),
# get_instance_health for pack-instance typed-report (Story 64.2; DEC-0112),
# and list_mailbox for product-session mailbox snapshots (Story 69.2; AM-08),
# and get_editor_draft_head for durable editor-head snapshots (Story 71.2; AM-03),
# and get_pack_ui_request for recorded pack chrome (Epic 72), get_product_session
# for exact grant recovery, and get_job for originating-session job reattachment.
# MA02 adds candidate/history reads; MA03 adds catalog/exact-validation reads.
ADDABLE_QUERY_COUNT: Final[int] = 16
# transfer_artifact (Story 70.2; AM-09), transfer_complete (Story 70.3),
# save/publish_editor_draft (Story 71; AM-09), cancel_job (Epic 73; AM-09),
# and ProductSession open/grant (DEC-0421 / DEC-0442).
# MA02 adds save_app_candidate; MA03 adds validate_app_candidate.
# Seed 9/7/10 stay the seed.
ADDABLE_COMMAND_COUNT: Final[int] = 12


class MessageFamily(StrEnum):
    """The three wire message families (DEC-0304)."""

    COMMAND = "command"
    QUERY = "query"
    EVENT = "event"


class WireCommand(StrEnum):
    """Closed-and-addable commands (packet seed plus approved amendments).

    The nine packet-seed commands (DEC-0304) plus addable ``transfer_artifact``
    (Story 70.2; AM-09), dest-authored ``transfer_complete`` (Story 70.3),
    editor draft save/publish (Story 71; AM-09), ``cancel_job`` (Epic 73;
    AM-09), and operator ProductSession open/grant (DEC-0421 / DEC-0442).
    Seed count stays 9. Wire ``type`` values are snake_case identifiers
    derived from the packet's English labels
    (``install/enable plugin`` → ``install_enable_plugin``).
    """

    START_MISSION = "start_mission"
    SEND_MESSAGE = "send_message"
    STEER_AGENT = "steer_agent"
    STOP_RUN = "stop_run"
    APPROVE_HOOK_ACTION = "approve_hook_action"
    INSTALL_ENABLE_PLUGIN = "install_enable_plugin"
    UPDATE_CONFIGURATION = "update_configuration"
    LAUNCH_TASK = "launch_task"
    RETRY_TASK = "retry_task"
    TRANSFER_ARTIFACT = "transfer_artifact"
    TRANSFER_COMPLETE = "transfer_complete"
    VALIDATE_APP_CANDIDATE = "validate_app_candidate"
    SAVE_APP_CANDIDATE = "save_app_candidate"
    SAVE_EDITOR_DRAFT = "save_editor_draft"
    PUBLISH_EDITOR_DRAFT = "publish_editor_draft"
    CANCEL_JOB = "cancel_job"
    OPEN_PRODUCT_SESSION = "open_product_session"
    GRANT_PRODUCT_SESSION = "grant_product_session"
    SUBMIT_AGENT_REQUEST = "submit_agent_request"
    CANCEL_AGENT_REQUEST = "cancel_agent_request"
    RESUME_AGENT_REQUEST = "resume_agent_request"


class WireQuery(StrEnum):
    """Closed-and-addable queries (packet seed plus AD extensions).

    The seven packet-seed queries (DEC-0304, DEC-0331) plus ``list_mission_hooks``
    (FR-Q35; AD-11), ``plugin_install_preflight`` returning rollback mode
    (FR-Q69; AD-21), ``facade_search`` / ``facade_get`` for the federated
    discovery DTO KnowledgeHit | ArtifactHit | ContributionHit (FR-RES-18;
    DEC-0449; Story 53.1), ``get_diagnosis`` for kit ``failure_class``
    (Story 61.2; DEC-0456), ``get_instance_health`` for pack-instance
    ``health()`` (Story 64.2; DEC-0112), and ``list_mailbox`` for the
    product-session mailbox snapshot (Story 69.2; AM-08; DEC-0500), and
    get_editor_draft_head for durable editor state (Story 71.2; AM-03), and
    get_product_session to recover durable grant records after reconnect, and
    get_job to reattach an originating-session JobHandle. Distinct
    from ``get_provider_health``. The packet seed ``get bot`` reads
    ``get_quant`` under the Bot-to-Quant rule.
    """

    GET_QUANT = "get_quant"
    LIST_MISSIONS = "list_missions"
    GET_GRAPH_STATE = "get_graph_state"
    INSPECT_LEDGER = "inspect_ledger"
    INSPECT_TRACE = "inspect_trace"
    LIST_INSTALLED_PLUGINS = "list_installed_plugins"
    GET_PROVIDER_HEALTH = "get_provider_health"
    LIST_MISSION_HOOKS = "list_mission_hooks"
    PLUGIN_INSTALL_PREFLIGHT = "plugin_install_preflight"
    FACADE_SEARCH = "facade_search"
    FACADE_GET = "facade_get"
    GET_DIAGNOSIS = "get_diagnosis"
    GET_INSTANCE_HEALTH = "get_instance_health"
    LIST_MAILBOX = "list_mailbox"
    GET_APP_UI_CATALOG = "get_app_ui_catalog"
    GET_APP_CANDIDATE_VALIDATION = "get_app_candidate_validation"
    GET_APP_CANDIDATE = "get_app_candidate"
    GET_APP_CANDIDATE_HISTORY = "get_app_candidate_history"
    GET_EDITOR_DRAFT_HEAD = "get_editor_draft_head"
    GET_PACK_UI_REQUEST = "get_pack_ui_request"
    GET_PRODUCT_SESSION = "get_product_session"
    GET_JOB = "get_job"
    GET_AGENT_REQUEST = "get_agent_request"


class WireEvent(StrEnum):
    """The ten seed ``noun.verb`` events (DEC-0304).

    Hook control names (``before_<verb>`` / ``after_<verb>``) are not members.
    """

    AGENT_STARTED = "agent.started"
    MESSAGE_DELTA = "message.delta"
    TOOL_STARTED = "tool.started"
    TASK_COMPLETED = "task.completed"
    HOOK_BLOCKED = "hook.blocked"
    LEDGER_UPDATED = "ledger.updated"
    MISSION_UPDATED = "mission.updated"
    WORKER_DETACHED = "worker.detached"
    PROVIDER_COOLDOWN = "provider.cooldown"
    ARTIFACT_CREATED = "artifact.created"


WIRE_COMMANDS: Final[frozenset[str]] = frozenset(member.value for member in WireCommand)
WIRE_QUERIES: Final[frozenset[str]] = frozenset(member.value for member in WireQuery)
WIRE_EVENTS: Final[frozenset[str]] = frozenset(member.value for member in WireEvent)

_TYPE_TO_FAMILY: Final[dict[str, MessageFamily]] = {
    **dict.fromkeys(WIRE_COMMANDS, MessageFamily.COMMAND),
    **dict.fromkeys(WIRE_QUERIES, MessageFamily.QUERY),
    **dict.fromkeys(WIRE_EVENTS, MessageFamily.EVENT),
}


class WireVocabularyError(ValueError):
    """Raised when a wire type is not a member of the closed packet vocabulary."""


def _host_request_family(wire_type: str) -> MessageFamily | None:
    """Lazy lookup so host_request verbs ride as command/query types (AD-14)."""
    # Lazy: host_request → envelope → vocabulary; top-level import would cycle.
    from qma.wire.host_request import host_request_type_family  # noqa: PLC0415

    return host_request_type_family(wire_type)


def family_of(wire_type: str) -> MessageFamily:
    """Return the message family for a closed vocabulary member."""
    try:
        return _TYPE_TO_FAMILY[wire_type]
    except KeyError:
        host_family = _host_request_family(wire_type)
        if host_family is not None:
            return host_family
        raise WireVocabularyError(
            f"{wire_type!r} is not a member of the closed qma-wire vocabulary "
            f"(owner={WIRE_VOCABULARY_OWNER})"
        ) from None


def parse_wire_type(value: object) -> str:
    """Accept only a type declared in the closed-and-addable packet vocabulary.

    The packet seed (26 nouns) plus closed-and-addable ``host_request`` verbs
    (AD-14) are accepted; host_request verbs ride as command or query types.
    """
    if not isinstance(value, str) or not value:
        raise WireVocabularyError(f"{value!r} is not a wire message type")
    if value in _TYPE_TO_FAMILY:
        return value
    if _host_request_family(value) is not None:
        return value
    raise WireVocabularyError(
        f"{value!r} is not a member of the closed qma-wire vocabulary "
        f"(owner={WIRE_VOCABULARY_OWNER})"
    )
