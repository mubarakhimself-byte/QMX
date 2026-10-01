"""Operator-owned first-start configuration for mandatory desk packs."""

from __future__ import annotations

import json
from pathlib import Path

from qma.daemon.plugins.packs import research_corpus_plugin_load_config

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
