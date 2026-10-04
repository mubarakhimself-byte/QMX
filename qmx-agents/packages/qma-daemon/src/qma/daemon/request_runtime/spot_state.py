"""Read a host-pinned retained QMN projection, with no node execution imports.

The QMN writer publishes this projection atomically with its snapshot/audit.
Only OS-owned operator configuration supplies a path. Callers supply scope data,
never a database path, account writer, credential, model adapter or callback.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.bootstrap_config import CONFIG_NAME
from qma.daemon.journal.authoritative import AuthoritativeJournal
from qma.daemon.journal.variables import HOST_RETRY_ATTEMPT_CEILING_KEY, GovernedVariableRegistry
from qmf.core import Ok, Result, is_refusal
from qmf.data.store.refusals import invalid_input, policy_rejection, storage_failure

SPOT_CONTRIBUTION = "trading-readonly:positions"


@dataclass(frozen=True, slots=True)
class SpotQueryValue:
    body: Mapping[str, object]

    def to_payload(self) -> Mapping[str, object]:
        return self.body


@dataclass(frozen=True, slots=True)
class SpotStateBinding:
    instance_id: str
    config_revision: int
    package_version: str
    provider_connection_id: str
    venue_id: str
    account_id: str
    policy_ref: str
    state_db_path: Path

    @property
    def scope(self) -> dict[str, str]:
        return {
            "provider_connection_id": self.provider_connection_id,
            "venue_id": self.venue_id,
            "account_id": self.account_id,
        }

    @property
    def authority_scope(self) -> str:
        """Opaque session account-scope token, not a QMF evidence fingerprint."""
        identity = {
            "scope": self.scope,
            "policy_ref": self.policy_ref,
            "state_db_path": str(self.state_db_path),
        }
        return (
            "spot-paper:"
            + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        )

    def validate_target(
        self, *, contribution: str, package_version: str, config_revision: int
    ) -> Result[None]:
        if (contribution, package_version, config_revision) != (
            SPOT_CONTRIBUTION,
            self.package_version,
            self.config_revision,
        ):
            return policy_rejection("spot_binding", "host contribution/config binding changed")
        return Ok(None)

    def query(self, payload: Mapping[str, object]) -> Result[SpotQueryValue]:
        if dict(payload) != self.scope:
            return policy_rejection("account_scope", "query cannot retarget its host-owned account")
        try:
            # mode=ro refuses nonexistent files; query_only protects this reader.
            with closing(sqlite3.connect(self.state_db_path.as_uri() + "?mode=ro", uri=True)) as db:
                db.execute("PRAGMA query_only=ON")
                row = db.execute("SELECT body FROM query_view WHERE id=1").fetchone()
            if row is None or not isinstance(row[0], str) or len(row[0]) > 2_000_000:
                return storage_failure("retained spot view is missing or oversized")
            raw: object = json.loads(row[0])
            if not isinstance(raw, dict):
                return storage_failure("retained spot view is not an object")
            view = cast("dict[str, object]", raw)
            raw_scope = view.get("scope")
            scope = cast("dict[str, object]", raw_scope) if isinstance(raw_scope, dict) else {}
            if (
                type(view.get("format_version")) is not int
                or type(view.get("paper_state_version")) is not int
                or type(view.get("audit_seq")) is not int
                or view.get("format_version") != 1
                or view.get("paper_state_version") != 2
                or view.get("simulation") is not True
                or view.get("retained") is not True
                or view.get("behavior") != "recorded-spot-limit-fills"
                or view.get("policy_ref") != self.policy_ref
                or not isinstance(raw_scope, dict)
                or any(scope.get(key) != value for key, value in self.scope.items())
            ):
                return policy_rejection(
                    "spot_view", "retained view violates host scope/policy/version"
                )
            return Ok(SpotQueryValue(MappingProxyType(view)))
        except (OSError, sqlite3.Error, ValueError) as exc:
            return storage_failure("retained spot view unavailable", context={"error": str(exc)})


def load_spot_state_bindings(root: Path) -> Result[Mapping[str, SpotStateBinding]]:
    """Optional startup binding; no automatic grant or writer creation."""
    path = root / CONFIG_NAME
    if not path.exists():
        return Ok(MappingProxyType({}))
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("operator config requires an object")
        rows_raw = cast("dict[str, object]", raw).get("spot_paper_queries", {})
        if not isinstance(rows_raw, dict):
            raise ValueError("spot_paper_queries requires a bounded instance mapping")
        rows = cast("dict[object, object]", rows_raw)
        if len(rows) > 64:
            raise ValueError("spot_paper_queries requires a bounded instance mapping")
        bindings: dict[str, SpotStateBinding] = {}
        fields = {
            "config_revision",
            "package_version",
            "provider_connection_id",
            "venue_id",
            "account_id",
            "policy_ref",
            "state_db_path",
        }
        for instance_id, raw_row in rows.items():
            if (
                not isinstance(instance_id, str)
                or not instance_id.strip()
                or not isinstance(raw_row, dict)
            ):
                raise ValueError("spot instance and binding must be explicit")
            row = cast("dict[str, object]", raw_row)
            if set(row) != fields:
                raise ValueError("spot binding fields must match the supported read-only shape")
            revision = row["config_revision"]
            if type(revision) is not int or revision < 0:
                raise ValueError("spot config revision must be a nonnegative integer")
            for key in fields - {"config_revision"}:
                value = row[key]
                if not isinstance(value, str) or not value.strip() or len(value) > 4096:
                    raise ValueError("spot binding values must be bounded nonempty strings")
            state_path = Path(cast("str", row["state_db_path"]))
            if not state_path.is_absolute():
                raise ValueError("spot state_db_path must be an operator-owned absolute path")
            binding = SpotStateBinding(
                instance_id,
                revision,
                cast("str", row["package_version"]),
                cast("str", row["provider_connection_id"]),
                cast("str", row["venue_id"]),
                cast("str", row["account_id"]),
                cast("str", row["policy_ref"]),
                state_path.resolve(),
            )
            bindings[instance_id] = binding
        return Ok(MappingProxyType(bindings))
    except (OSError, UnicodeError, ValueError) as exc:
        return invalid_input("spot_paper_queries", str(exc))


def configure_spot_host_retry(
    root: Path, variables: GovernedVariableRegistry, journal: AuthoritativeJournal
) -> Result[None]:
    """Bind an explicit OS-owned host ceiling through the existing registry."""
    try:
        raw = cast(
            "dict[str, object]", json.loads((root / CONFIG_NAME).read_text(encoding="utf-8"))
        )
        value = raw.get("host_retry_attempt_ceiling")
        if value is None:
            return Ok(None)  # Existing query admission remains fail-closed.
        if type(value) is not int or not 1 <= value <= 32:
            return invalid_input(
                "host_retry_attempt_ceiling", "explicit count from 1 to 32 required"
            )
        configured = variables.variable_set(
            HOST_RETRY_ATTEMPT_CEILING_KEY,
            value,
            principal_class=PrincipalClass.OPERATOR,
            journal=journal,
        )
        if is_refusal(configured):
            return configured
        return Ok(None)
    except (OSError, UnicodeError, ValueError) as exc:
        return invalid_input("host_retry_attempt_ceiling", str(exc))
