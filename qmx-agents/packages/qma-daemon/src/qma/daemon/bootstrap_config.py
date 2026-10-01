"""Operator-owned first-start configuration for mandatory desk packs."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from qma.core.ontology import ActorId
from qma.daemon.plugins.packs import research_corpus_plugin_load_config
from qmf.core import Ok, RefusalCategory, Result, Retryability, TypedRefusal, is_refusal

CONFIG_NAME = "operator-config.json"


class BootstrapConfigError(ValueError):
    """The operator's startup configuration is missing or invalid."""


def load_plugin_load_configs(daemon_root: Path | str) -> dict[str, dict[str, object]]:
    """Read the filesystem-valued corpus root from the OS-owned daemon root."""
    config_path = Path(daemon_root) / CONFIG_NAME
    if not config_path.is_file():
        raise BootstrapConfigError(
            f"operator configuration is required; create {config_path} with "
            'JSON field "research_corpus_root_path" set to an existing corpus directory'
        )
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BootstrapConfigError(f"cannot read {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise BootstrapConfigError(f"{config_path} must contain a JSON object")
    corpus_root = raw.get("research_corpus_root_path")
    if not isinstance(corpus_root, str) or not corpus_root.strip():
        raise BootstrapConfigError(
            f'{config_path} requires non-empty string "research_corpus_root_path"'
        )
    return research_corpus_plugin_load_config(Path(corpus_root))


def backtest_binding(
    daemon_root: Path | str, instance_id: str, config_revision: int
) -> Result[tuple[ActorId, str]]:
    """Resolve an operator-owned QMB actor/environment mapping for an exact instance revision."""
    resolved = backtest_binding_for_instance(daemon_root, instance_id)
    if is_refusal(resolved):
        return resolved
    owner, environment_ref, bound_revision = resolved.value
    if bound_revision != config_revision:
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=Retryability.AFTER_CONDITION,
            context={
                "reason": "operator QMB binding does not match exact config revision",
                "instance_id": instance_id,
            },
        )
    return Ok((owner, environment_ref))


def backtest_binding_for_instance(
    daemon_root: Path | str, instance_id: str
) -> Result[tuple[ActorId, str, int]]:
    """Resolve the operator-owned binding and its current revision for session opening."""
    path = Path(daemon_root) / CONFIG_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=Retryability.AFTER_CONDITION,
            context={
                "reason": "operator QMB binding configuration is unavailable",
                "error": str(exc),
            },
        )
    rows = raw.get("qmb_bindings") if isinstance(raw, dict) else None
    row = rows.get(instance_id) if isinstance(rows, dict) else None
    if not isinstance(row, Mapping):
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=Retryability.AFTER_CONDITION,
            context={
                "reason": "no operator QMB binding exists for enabled instance",
                "instance_id": instance_id,
            },
        )
    revision = row.get("config_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=Retryability.AFTER_CONDITION,
            context={
                "reason": "operator QMB binding has no valid nonnegative config revision",
                "instance_id": instance_id,
            },
        )
    actor = ActorId.try_create(row.get("owner_actor_id"))
    if is_refusal(actor):
        return actor
    environment_ref = row.get("environment_ref")
    if not isinstance(environment_ref, str) or not environment_ref.strip():
        return TypedRefusal(
            category=RefusalCategory.UNAVAILABLE_DEPENDENCY,
            retryability=Retryability.AFTER_CONDITION,
            context={
                "reason": "operator QMB binding has no declared environment_ref",
                "instance_id": instance_id,
            },
        )
    return Ok((actor.value, environment_ref.strip(), revision))
