"""AD-26 governed configurable-variable registry (FR-Q36; DEC-0325).

Every number any QMA subsystem mints is a registry row declaring name, owning
subsystem, scope, type, units, default, editability, and home. Registry-homed
values change only via an ``operator``-principal ``variable.set`` that records a
``variable.set`` journal event. Uneditable and record-homed values are refused.
There is no ``variable`` edit kind — agents, hooks, Roles and Missions never set
one. Store-lifecycle cadences are cited by ``registry:`` key and never copied.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, cast

from qma.core.refusals import OperatorPrincipalRequired
from qma.core.vocabulary import (
    PrincipalClass,
    VariableEditability,
    VariableScope,
    VocabularyError,
    parse_closed,
)
from qma.daemon.journal.authoritative import AuthoritativeJournal, JournalAppendReceipt
from qma.wire.principals import authorize_wire_command
from qmf.core import Duration, Instant, Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "ARTIFACT_STAGE_MAX_BYTES_KEY",
    "ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY",
    "HOST_CONFIGURE_PAIRING_TTL_SOURCE",
    "HOST_NESTED_MISSION_CALL_DEPTH_CEILING_KEY",
    "HOST_NESTED_MISSION_CALL_DEPTH_CEILING_REGISTRY_KEY",
    "HOST_RETRY_ATTEMPT_CEILING_KEY",
    "HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY",
    "PAIRING_SESSION_TTL_KEY",
    "PAIRING_SESSION_TTL_META_KEY",
    "PAIRING_SESSION_TTL_REGISTRY_KEY",
    "PAIRING_TTL_CONFIGURED_EVENT",
    "REGISTRY_HOME",
    "STORE_BACKUP_CADENCE_KEY",
    "STORE_FULL_RESTORE_REHEARSAL_CADENCE_KEY",
    "STORE_LIFECYCLE_KEYS",
    "STORE_SAMPLE_RESTORE_TEST_CADENCE_KEY",
    "VARIABLE_SET_COMMAND",
    "VARIABLE_SET_EVENT",
    "GovernedVariableRegistry",
    "VariableRow",
    "VariableSetReceipt",
    "builtin_qma_variable_rows",
    "cite_store_lifecycle_key",
    "claim_pairing_ttl_ct40_writable_at_inspect_sha",
    "expires_at_from_pairing_ttl",
    "fold_pairing_ttl_from_journal",
    "has_variable_edit_kind",
    "pairing_session_ttl_is_set",
    "pairing_ttl_duration_ns",
    "parse_operator_pairing_ttl_duration",
    "refuse_pair_issue_without_ttl",
    "registry_key",
    "resolve_artifact_stage_max_bytes",
]


VARIABLE_SET_COMMAND: Final[str] = "variable.set"
VARIABLE_SET_EVENT: Final[str] = "variable.set"
REGISTRY_HOME: Final[str] = "registry"
PAIRING_SESSION_TTL_KEY: Final[str] = "pairing.session_ttl"
PAIRING_SESSION_TTL_REGISTRY_KEY: Final[str] = "registry:pairing.session_ttl"
PAIRING_SESSION_TTL_META_KEY: Final[str] = "registry:pairing.session_ttl"
PAIRING_TTL_CONFIGURED_EVENT: Final[str] = "pairing.ttl_configured"
HOST_CONFIGURE_PAIRING_TTL_SOURCE: Final[str] = "host.configure.pairing-ttl"
PAIRING_TTL_CT40_WRITABLE_AT_INSPECT_SHA: Final[bool] = False
PAIRING_TTL_INSPECT_SHA: Final[str] = "34c148be"
_ISO8601_DURATION: Final[re.Pattern[str]] = re.compile(
    r"^P(?=[WT0-9])(?:(\d+)W)?(?:(\d+)D)?"
    r"(?:T(?=[0-9])(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$"
)
_NS_PER_SECOND: Final[int] = 1_000_000_000
_NS_PER_MINUTE: Final[int] = 60 * _NS_PER_SECOND
_NS_PER_HOUR: Final[int] = 60 * _NS_PER_MINUTE
_NS_PER_DAY: Final[int] = 24 * _NS_PER_HOUR
_NS_PER_WEEK: Final[int] = 7 * _NS_PER_DAY
ARTIFACT_STAGE_MAX_BYTES_KEY: Final[str] = "artifact.stage_max_bytes"
ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY: Final[str] = "registry:artifact.stage_max_bytes"
HOST_RETRY_ATTEMPT_CEILING_KEY: Final[str] = "host.retry_attempt_ceiling"
HOST_RETRY_ATTEMPT_CEILING_REGISTRY_KEY: Final[str] = "registry:host.retry_attempt_ceiling"
# Story 63.2 / FR-PG-32: nested Mission call_depth ceiling. Not GAP-0108.
HOST_NESTED_MISSION_CALL_DEPTH_CEILING_KEY: Final[str] = "host.nested_mission_call_depth_ceiling"
HOST_NESTED_MISSION_CALL_DEPTH_CEILING_REGISTRY_KEY: Final[str] = (
    "registry:host.nested_mission_call_depth_ceiling"
)

# Cite by key — never copy a registry value into code (FR-Q36; AD-26).
STORE_BACKUP_CADENCE_KEY: Final[str] = "registry:store.backup_cadence"
STORE_SAMPLE_RESTORE_TEST_CADENCE_KEY: Final[str] = "registry:store.sample_restore_test_cadence"
STORE_FULL_RESTORE_REHEARSAL_CADENCE_KEY: Final[str] = (
    "registry:store.full_restore_rehearsal_cadence"
)
STORE_LIFECYCLE_KEYS: Final[frozenset[str]] = frozenset(
    {
        STORE_BACKUP_CADENCE_KEY,
        STORE_SAMPLE_RESTORE_TEST_CADENCE_KEY,
        STORE_FULL_RESTORE_REHEARSAL_CADENCE_KEY,
    }
)


def registry_key(name: str) -> str:
    """Return the ``registry:<name>`` citation form."""
    if name.startswith("registry:"):
        return name
    return f"registry:{name}"


def resolve_artifact_stage_max_bytes(value: object) -> Result[int]:
    """Require an injected ``registry:artifact.stage_max_bytes``. Mint no number."""
    if value is None:
        return policy_rejection(
            "stage_max_bytes",
            "registry:artifact.stage_max_bytes is missing; PUT /artifacts/stage "
            "is refused and writes no object (GAP-0110; DEC-0510 A11); this "
            "increment mints no number",
            registry_key=ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
            wrote_object=False,
        )
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return invalid_input(
            "stage_max_bytes",
            "registry:artifact.stage_max_bytes must be a non-negative int when set",
            given=repr(value),
            registry_key=ARTIFACT_STAGE_MAX_BYTES_REGISTRY_KEY,
            wrote_object=False,
        )
    return Ok(value)


def cite_store_lifecycle_key(name: object) -> Result[str]:
    """Resolve a store-lifecycle citation to its ``registry:`` key.

    Refuses unknown names and never returns a copied cadence value.
    """
    if not isinstance(name, str) or name.strip() == "":
        return invalid_input(
            "store_lifecycle_key",
            "cite registry:store.backup_cadence, "
            "registry:store.sample_restore_test_cadence, or "
            "registry:store.full_restore_rehearsal_cadence by key (FR-Q36; AD-26)",
            given=repr(name),
        )
    key = registry_key(name.removeprefix("registry:"))
    if key not in STORE_LIFECYCLE_KEYS:
        return policy_rejection(
            "store_lifecycle_key",
            "store-lifecycle citations name one of the three AD-26 cadence keys "
            "and never copy a registry value (FR-Q36; AD-26)",
            given=name,
            allowed=sorted(STORE_LIFECYCLE_KEYS),
        )
    return Ok(key)


def parse_operator_pairing_ttl_duration(value: object) -> Result[str]:
    """Accept an operator-supplied duration. Mint no sitting default (GAP-0109)."""
    if not isinstance(value, str) or value.strip() == "":
        return invalid_input(
            "duration",
            "qmb host configure pairing-ttl requires an operator-supplied "
            "duration; this increment mints no duration (GAP-0109)",
            given=repr(value),
        )
    return Ok(value.strip())


def pairing_ttl_duration_ns(value: object) -> Result[int]:
    """Parse an operator ISO-8601 duration to nanoseconds. Mint no default."""
    parsed = parse_operator_pairing_ttl_duration(value)
    if is_refusal(parsed):
        return parsed
    matched = _ISO8601_DURATION.fullmatch(parsed.value.upper())
    if matched is None:
        return invalid_input(
            "duration",
            "registry:pairing.session_ttl must be an ISO-8601 duration "
            "(PnW / PnD / PTnHnMnS); this epic mints no duration (GAP-0109)",
            given=parsed.value,
            registry_key=PAIRING_SESSION_TTL_REGISTRY_KEY,
        )
    weeks, days, hours, minutes, seconds = matched.groups()
    total = 0
    if weeks is not None:
        total += int(weeks) * _NS_PER_WEEK
    if days is not None:
        total += int(days) * _NS_PER_DAY
    if hours is not None:
        total += int(hours) * _NS_PER_HOUR
    if minutes is not None:
        total += int(minutes) * _NS_PER_MINUTE
    if seconds is not None:
        total += int(seconds) * _NS_PER_SECOND
    if total <= 0:
        return invalid_input(
            "duration",
            "registry:pairing.session_ttl must be a positive ISO-8601 duration",
            given=parsed.value,
            registry_key=PAIRING_SESSION_TTL_REGISTRY_KEY,
        )
    created = Duration.try_create(total)
    if is_refusal(created):
        return created
    return Ok(created.value.value_ns)


def expires_at_from_pairing_ttl(*, now_ns: object, ttl: object) -> Result[int]:
    """``expires_at`` = now + configured TTL. Mint no duration (GAP-0109)."""
    start = Instant.try_create(now_ns)
    if is_refusal(start):
        return invalid_input(
            "now_ns",
            "now_ns is a signed int64 nanosecond instant",
            given=repr(now_ns),
        )
    span = pairing_ttl_duration_ns(ttl)
    if is_refusal(span):
        return span
    duration = Duration.try_create(span.value)
    if is_refusal(duration):
        return duration
    added = start.value.add_duration(duration.value)
    if is_refusal(added):
        return added
    return Ok(added.value.value_ns)


def pairing_session_ttl_is_set(value: object) -> bool:
    """True when ``registry:pairing.session_ttl`` holds an operator duration."""
    if value is None:
        return False
    if not isinstance(value, str):
        return True
    return value.strip() != ""


def refuse_pair_issue_without_ttl(value: object) -> Result[None]:
    """Missing TTL refuses ``/pair/start`` or ``/pair/confirm`` issue (FR-UI-20).

    Lands the refuse gate only. Does not implement pair HTTP.
    """
    if pairing_session_ttl_is_set(value):
        return Ok(None)
    return policy_rejection(
        PAIRING_SESSION_TTL_KEY,
        "missing registry:pairing.session_ttl refuses /pair/start and "
        "/pair/confirm issue (FR-UI-20; GAP-0109)",
        registry_key=PAIRING_SESSION_TTL_REGISTRY_KEY,
        ttl="unset",
        pair_http=False,
    )


def claim_pairing_ttl_ct40_writable_at_inspect_sha(writable: object) -> Result[bool]:
    """The write path at inspect SHA was not CT-40 ``variable.set`` (DEC-0507)."""
    if writable is True or writable == "true":
        return policy_rejection(
            PAIRING_SESSION_TTL_KEY,
            "registry:pairing.session_ttl was not a CT-40 variable.set write "
            "path at inspect SHA 34c148be; only host-control configure "
            "pairing-ttl writes it (AM-10)",
            ct40_writable_at_inspect_sha=False,
            inspect_sha=PAIRING_TTL_INSPECT_SHA,
            registry_key=PAIRING_SESSION_TTL_REGISTRY_KEY,
        )
    if writable is not False:
        return invalid_input(
            "ct40_writable_at_inspect_sha",
            "inspect-SHA CT-40 writable claim is a boolean",
            given=repr(writable),
        )
    return Ok(False)


def fold_pairing_ttl_from_journal(journal: AuthoritativeJournal) -> str | None:
    """Latest host-control TTL write: ``as_of`` recorded_at, then journal_seq."""
    rows = journal.read_all()
    if is_refusal(rows):
        return None
    chosen_key: tuple[int, int] | None = None
    chosen: str | None = None
    for row in rows.value:
        if row.get("event") != PAIRING_TTL_CONFIGURED_EVENT:
            continue
        recorded_at = row.get("recorded_at")
        journal_seq = row.get("journal_seq")
        payload = row.get("payload")
        if not isinstance(recorded_at, int) or isinstance(recorded_at, bool):
            continue
        if not isinstance(journal_seq, int) or isinstance(journal_seq, bool):
            continue
        if not isinstance(payload, dict):
            continue
        duration = cast("dict[str, object]", payload).get("duration")
        if not isinstance(duration, str) or duration.strip() == "":
            continue
        key = (recorded_at, journal_seq)
        if chosen_key is None or key >= chosen_key:
            chosen_key = key
            chosen = duration.strip()
    return chosen


def has_variable_edit_kind() -> bool:
    """False — AD-22 mints no ``variable`` edit kind (FR-Q36; AD-26)."""
    return False


@dataclass(frozen=True, slots=True)
class VariableRow:
    """One machine-readable AD-26 registry row."""

    name: str
    owning_subsystem: str
    scope: VariableScope
    value_type: str
    units: str | None
    default: object
    editability: VariableEditability
    home: str

    @property
    def registry_key(self) -> str:
        """``registry:<name>`` citation form."""
        return registry_key(self.name)

    @property
    def is_registry_homed(self) -> bool:
        """True when ``home`` is the registry itself."""
        return self.home == REGISTRY_HOME

    @property
    def is_record_homed(self) -> bool:
        """True when ``home`` is a named owning record type."""
        return not self.is_registry_homed

    def to_dict(self) -> Mapping[str, object]:
        """JSON-native row shape."""
        return MappingProxyType(
            {
                "name": self.name,
                "owning_subsystem": self.owning_subsystem,
                "scope": self.scope.value,
                "type": self.value_type,
                "units": self.units,
                "default": self.default,
                "editability": self.editability.value,
                "home": self.home,
                "registry_key": self.registry_key,
            }
        )


def _row(
    name: str,
    *,
    owning_subsystem: str,
    scope: VariableScope,
    value_type: str,
    units: str | None,
    default: object,
    editability: VariableEditability = VariableEditability.UI_EDITABLE,
    home: str = REGISTRY_HOME,
) -> VariableRow:
    return VariableRow(
        name=name,
        owning_subsystem=owning_subsystem,
        scope=scope,
        value_type=value_type,
        units=units,
        default=default,
        editability=editability,
        home=home,
    )


def builtin_qma_variable_rows() -> tuple[VariableRow, ...]:
    """QMA AD-26 rows shipped in v1 (DEC-0325).

    Defaults cite declarations, not copies of unresolved values where the spine
    left none.
    """
    daemon = "COMP-QMA-DAEMON"
    wire = "COMP-QMA-WIRE"
    g = VariableScope.GLOBAL
    return (
        _row(
            "quant.quiet_hours",
            owning_subsystem=daemon,
            scope=VariableScope.QUANT,
            value_type="declaration",
            units="schedule",
            default="declared-per-quant",
            home="quant_record.WakePolicy",
        ),
        _row(
            "quant.max_wakes_per_window",
            owning_subsystem=daemon,
            scope=VariableScope.QUANT,
            value_type="count",
            units="count",
            default="declared-per-quant",
            home="quant_record.WakePolicy",
        ),
        _row(
            "hook.timeout_before",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "hook.timeout_after",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "hook.timeout_control",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "mission.ask_timeout",
            owning_subsystem=daemon,
            scope=VariableScope.MISSION,
            value_type="duration",
            units="duration",
            default="declared-per-mission",
            home="mission.approval_route",
        ),
        _row(
            "mission.on_timeout",
            owning_subsystem=daemon,
            scope=VariableScope.MISSION,
            value_type="enum",
            units="enum",
            default="declared-per-mission",
            home="mission.approval_route",
        ),
        _row(
            "wire.deprecation_minors",
            owning_subsystem=wire,
            scope=g,
            value_type="count",
            units="count",
            default=2,
        ),
        _row(
            "wire.dedup_window",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "rlm.depth_cap",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default=2,
        ),
        _row(
            HOST_RETRY_ATTEMPT_CEILING_KEY,
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            # GAP-0108 / cheap-veto A9: registry row exists; this story mints no number.
            default=None,
        ),
        _row(
            HOST_NESTED_MISSION_CALL_DEPTH_CEILING_KEY,
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            # FR-PG-32: host-registered recursion ceiling; this story mints no
            # number. Distinct from GAP-0108 retry-attempt ceiling.
            default=None,
        ),
        _row(
            "rlm.fanout_cost_ceiling_usd",
            owning_subsystem=daemon,
            scope=VariableScope.DESK,
            value_type="money",
            units="money(numeraire)",
            default="declared-per-installation",
        ),
        _row(
            "telemetry.retention_window",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "telemetry.trim_event_count",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default="declared-per-installation",
        ),
        _row(
            "telemetry.trim_disk_bytes",
            owning_subsystem=daemon,
            scope=g,
            value_type="quantity",
            units="bytes",
            default="declared-per-installation",
        ),
        _row(
            "mailbox.delivery_trim_event_count",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default="declared-per-installation",
        ),
        _row(
            "mailbox.delivery_trim_disk_bytes",
            owning_subsystem=daemon,
            scope=g,
            value_type="quantity",
            units="bytes",
            default="declared-per-installation",
        ),
        _row(
            "mailbox.delivery_retention_window",
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            default="declared-per-installation",
        ),
        _row(
            "environment.max_in_flight",
            owning_subsystem=daemon,
            scope=VariableScope.EXECUTION_ENVIRONMENT,
            value_type="count",
            units="count",
            default=1,
            home="execution_environment_declaration",
        ),
        _row(
            "routine.max_concurrent",
            owning_subsystem=daemon,
            scope=VariableScope.ROUTINE,
            value_type="count",
            units="count",
            default="declared-per-routine",
            home="routine_record",
        ),
        _row(
            "continuation.max_consecutive",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default="declared-per-installation",
        ),
        _row(
            "continuation.budget",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default="declared-per-installation",
        ),
        _row(
            "continuation.escalation_target",
            owning_subsystem=daemon,
            scope=g,
            value_type="string",
            units="string",
            default="declared-per-installation",
        ),
        _row(
            "continuation.laptop_off_promised",
            owning_subsystem=daemon,
            scope=g,
            value_type="boolean",
            units="boolean",
            default=False,
        ),
        _row(
            "store.backup_cadence",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units="schedule",
            # Value lives in docs/registry/variables.yaml — code cites the key only.
            default=None,
        ),
        _row(
            "store.sample_restore_test_cadence",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units="schedule",
            default=None,
        ),
        _row(
            "store.full_restore_rehearsal_cadence",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units="schedule",
            default=None,
        ),
        _row(
            "proxy.allow_unauthenticated_loopback",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units=None,
            default=True,
        ),
        _row(
            "deployment.model_family",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units="enum",
            default="declared-per-installation",
        ),
        _row(
            "review_policy.families",
            owning_subsystem=daemon,
            scope=g,
            value_type="enum",
            units="enum",
            default="declared-per-installation",
        ),
        _row(
            "wire.remote_outbox_depth",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default="declared-per-installation",
        ),
        _row(
            "wire.remote_spool_bytes",
            owning_subsystem=daemon,
            scope=g,
            value_type="quantity",
            units="bytes",
            default="declared-per-installation",
        ),
        _row(
            "deferred.finished_mission_trajectory_count",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default=50,
        ),
        _row(
            "deferred.sandbox_refusal_count",
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="count",
            default=3,
        ),
        _row(
            PAIRING_SESSION_TTL_KEY,
            owning_subsystem=daemon,
            scope=g,
            value_type="duration",
            units="duration",
            # GAP-0109 / DEC-0510 A10: row exists; this increment mints no duration.
            default=None,
        ),
        _row(
            ARTIFACT_STAGE_MAX_BYTES_KEY,
            owning_subsystem=daemon,
            scope=g,
            value_type="count",
            units="bytes",
            # GAP-0110 / DEC-0510 A11: row exists; this increment mints no number.
            default=None,
        ),
    )


@dataclass(frozen=True, slots=True)
class VariableSetReceipt:
    """Outcome of an accepted ``variable.set``."""

    name: str
    value: object
    previous: object
    journal: JournalAppendReceipt


@dataclass
class GovernedVariableRegistry:
    """In-memory AD-26 registry with operator-only ``variable.set`` write path."""

    _rows: dict[str, VariableRow] = field(default_factory=dict[str, VariableRow])
    _values: dict[str, object] = field(default_factory=dict[str, object])

    @classmethod
    def with_builtins(cls) -> GovernedVariableRegistry:
        """Load the shipped QMA AD-26 rows."""
        registry = cls()
        for row in builtin_qma_variable_rows():
            registered = registry.register(row)
            if is_refusal(registered):
                msg = f"builtin variable row refused: {row.name}"
                raise RuntimeError(msg)
        return registry

    def rows(self) -> Mapping[str, VariableRow]:
        """Snapshot of registered rows (metadata only for record-homed)."""
        return MappingProxyType(dict(self._rows))

    def values(self) -> Mapping[str, object]:
        """Snapshot of registry-homed runtime values."""
        return MappingProxyType(dict(self._values))

    def register(self, row: VariableRow | Mapping[str, object]) -> Result[VariableRow]:
        """Register one machine-readable variable row (FR-Q36)."""
        parsed = self._coerce_row(row) if not isinstance(row, VariableRow) else Ok(row)
        if is_refusal(parsed):
            return parsed
        item = parsed.value
        if item.name in self._rows:
            return policy_rejection(
                "variable_registry",
                "a variable name may be registered once (FR-Q36; AD-26)",
                name=item.name,
            )
        self._rows[item.name] = item
        if item.is_registry_homed:
            self._values[item.name] = item.default
        return Ok(item)

    def get(self, name: object) -> Result[VariableRow]:
        """Look up a registered row by bare name or ``registry:`` key."""
        resolved = self._resolve_name(name)
        if is_refusal(resolved):
            return resolved
        row = self._rows.get(resolved.value)
        if row is None:
            return policy_rejection(
                "variable_registry",
                "unknown registered variable (FR-Q36; AD-26)",
                name=resolved.value,
            )
        return Ok(row)

    def get_value(self, name: object) -> Result[object]:
        """Return the current registry-homed value; refuse record-homed reads here."""
        row_result = self.get(name)
        if is_refusal(row_result):
            return row_result
        row = row_result.value
        if row.is_record_homed:
            return policy_rejection(
                "variable_value",
                "a record-homed variable's value lives on its owning record, not "
                "in the registry (FR-Q36; AD-26)",
                name=row.name,
                home=row.home,
            )
        return Ok(self._values[row.name])

    def variable_set(
        self,
        name: object,
        value: object,
        *,
        principal_class: object,
        journal: AuthoritativeJournal,
        scope_path: object = (),
        source: object = "operator",
    ) -> Result[VariableSetReceipt]:
        """Set a registry-homed value via operator-principal ``variable.set``.

        Records a ``variable.set`` journal event. Refuses uneditable rows,
        record-homed rows, non-operator principals, and any Agent/hook/Role/
        Mission route (no ``variable`` edit kind).
        """
        if source not in {None, "operator", VARIABLE_SET_COMMAND}:
            return policy_rejection(
                "variable_set",
                "no Agent, hook, Role or Mission may alter a registered value; "
                "there is no variable edit kind and no non-operator configuration "
                "write path (FR-Q36; AD-26)",
                source=repr(source),
            )

        authorized = authorize_wire_command(VARIABLE_SET_COMMAND, principal_class)
        if is_refusal(authorized):
            return authorized
        if authorized.value.principal_class is not PrincipalClass.OPERATOR:
            return OperatorPrincipalRequired.of(
                command=VARIABLE_SET_COMMAND,
                principal_class=str(principal_class),
            )

        row_result = self.get(name)
        if is_refusal(row_result):
            return row_result
        row = row_result.value

        if row.name == PAIRING_SESSION_TTL_KEY:
            return policy_rejection(
                "variable_set",
                "CT-40 variable.set naming registry:pairing.session_ttl is "
                "refused for any principal; only qmb host configure pairing-ttl "
                "over host-control may write it (AM-10; DEC-0492)",
                name=row.name,
                registry_key=row.registry_key,
                writer=HOST_CONFIGURE_PAIRING_TTL_SOURCE,
            )

        if row.editability is VariableEditability.UNEDITABLE:
            return policy_rejection(
                "variable_set",
                "a variable.set naming an uneditable variable is refused (FR-Q36; AD-26)",
                name=row.name,
                editability=row.editability.value,
            )
        if row.is_record_homed:
            return policy_rejection(
                "variable_set",
                "a variable.set naming a record-homed variable is refused; "
                "change it only through that record's operator-principal write "
                "command (FR-Q36; AD-24, AD-26)",
                name=row.name,
                home=row.home,
            )

        previous = self._values.get(row.name, row.default)
        payload: dict[str, object] = {
            "name": row.name,
            "registry_key": row.registry_key,
            "value": value,
            "home": row.home,
            "scope": row.scope.value,
        }
        if previous is not None:
            payload["previous"] = previous
        append = journal.append_event(
            VARIABLE_SET_EVENT,
            scope_path=scope_path,
            payload=payload,
        )
        if is_refusal(append):
            return append
        self._values[row.name] = value
        return Ok(
            VariableSetReceipt(
                name=row.name,
                value=value,
                previous=previous,
                journal=append.value,
            )
        )

    def artifact_stage_max_bytes(self) -> Result[int]:
        """Read injected ``registry:artifact.stage_max_bytes``. Missing refuses PUT."""
        got = self.get_value(ARTIFACT_STAGE_MAX_BYTES_KEY)
        if is_refusal(got):
            return got
        return resolve_artifact_stage_max_bytes(got.value)

    def pairing_ttl_is_set(self) -> bool:
        """True when host-control has written ``registry:pairing.session_ttl``."""
        return pairing_session_ttl_is_set(self._values.get(PAIRING_SESSION_TTL_KEY))

    def pairing_ttl_status(self) -> str:
        """Status surface: ``set`` or ``unset``. Never the duration secret-or-default."""
        return "set" if self.pairing_ttl_is_set() else "unset"

    def refuse_pair_issue(self) -> Result[None]:
        """Missing-TTL refuse gate for ``/pair/start`` and ``/pair/confirm`` issue."""
        return refuse_pair_issue_without_ttl(self._values.get(PAIRING_SESSION_TTL_KEY))

    def pairing_ttl_duration(self) -> Result[str]:
        """Configured TTL string. Missing TTL refuses issue (GAP-0109)."""
        value = self._values.get(PAIRING_SESSION_TTL_KEY)
        refused = refuse_pair_issue_without_ttl(value)
        if is_refusal(refused):
            return refused
        if not isinstance(value, str):
            return invalid_input(
                PAIRING_SESSION_TTL_KEY,
                "registry:pairing.session_ttl is an operator-supplied duration string",
                given=repr(value),
            )
        return Ok(value.strip())

    def configure_pairing_session_ttl(
        self,
        duration: object,
        *,
        journal: AuthoritativeJournal,
        source: object = HOST_CONFIGURE_PAIRING_TTL_SOURCE,
    ) -> Result[str]:
        """Sole writer of ``registry:pairing.session_ttl`` (AM-10; GAP-0109)."""
        if source != HOST_CONFIGURE_PAIRING_TTL_SOURCE:
            return policy_rejection(
                PAIRING_SESSION_TTL_KEY,
                "only qmb host configure pairing-ttl over host-control may write "
                "registry:pairing.session_ttl (AM-10; DEC-0492)",
                source=repr(source),
                writer=HOST_CONFIGURE_PAIRING_TTL_SOURCE,
            )
        parsed = parse_operator_pairing_ttl_duration(duration)
        if is_refusal(parsed):
            return parsed
        append = journal.append_event(
            PAIRING_TTL_CONFIGURED_EVENT,
            payload={
                "name": PAIRING_SESSION_TTL_KEY,
                "registry_key": PAIRING_SESSION_TTL_REGISTRY_KEY,
                "duration": parsed.value,
                "writer": HOST_CONFIGURE_PAIRING_TTL_SOURCE,
            },
        )
        if is_refusal(append):
            return append
        self._values[PAIRING_SESSION_TTL_KEY] = parsed.value
        return Ok(parsed.value)

    def load_pairing_session_ttl(self, duration: object) -> Result[str]:
        """Restore a previously journaled host-control TTL. Not a writer."""
        parsed = parse_operator_pairing_ttl_duration(duration)
        if is_refusal(parsed):
            return parsed
        self._values[PAIRING_SESSION_TTL_KEY] = parsed.value
        return Ok(parsed.value)

    def refuse_non_operator_route(
        self,
        name: object,
        value: object,
        *,
        principal_class: object = "machine",
        via: object = "agent",
    ) -> Result[None]:
        """Refuse Agent / hook / Role / Mission configuration-write attempts."""
        _ = (name, value)
        return policy_rejection(
            "variable_set",
            "no Agent, hook, Role or Mission may alter a registered value; "
            "there is no variable edit kind and no non-operator configuration "
            "write path (FR-Q36; AD-26)",
            via=repr(via),
            principal_class=repr(principal_class),
        )

    def _resolve_name(self, name: object) -> Result[str]:
        if not isinstance(name, str) or name.strip() == "":
            return invalid_input(
                "name",
                "a variable name is a non-empty string (FR-Q36; AD-26)",
                given=repr(name),
            )
        return Ok(name.removeprefix("registry:"))

    def _coerce_row(self, raw: Mapping[str, object]) -> Result[VariableRow]:
        name = raw.get("name")
        if not isinstance(name, str) or name.strip() == "":
            return invalid_input("name", "variable row requires a non-empty name")
        owning = raw.get("owning_subsystem")
        if not isinstance(owning, str) or owning.strip() == "":
            return invalid_input(
                "owning_subsystem",
                "variable row declares its owning subsystem (FR-Q36; AD-26)",
            )
        try:
            scope = parse_closed(VariableScope, raw.get("scope"))
        except VocabularyError as exc:
            return policy_rejection(
                "variable_scope",
                "scope is one of the eight closed AD-26 values (FR-Q36; AD-26)",
                detail=str(exc),
                given=repr(raw.get("scope")),
            )
        value_type = raw.get("type")
        if not isinstance(value_type, str) or value_type.strip() == "":
            return invalid_input("type", "variable row declares its type")
        units = raw.get("units")
        if units is not None and not isinstance(units, str):
            return invalid_input("units", "units is a string or null")
        try:
            editability = parse_closed(VariableEditability, raw.get("editability"))
        except VocabularyError as exc:
            return policy_rejection(
                "variable_editability",
                "editability is ui-editable or uneditable (FR-Q36; AD-26)",
                detail=str(exc),
                given=repr(raw.get("editability")),
            )
        home = raw.get("home", REGISTRY_HOME)
        if not isinstance(home, str) or home.strip() == "":
            return invalid_input(
                "home",
                "home is registry or a named owning record type (FR-Q36; AD-26)",
            )
        if "default" not in raw:
            return invalid_input("default", "variable row declares its default")
        return Ok(
            VariableRow(
                name=name,
                owning_subsystem=owning,
                scope=scope,
                value_type=value_type,
                units=units,
                default=raw.get("default"),
                editability=editability,
                home=home,
            )
        )
