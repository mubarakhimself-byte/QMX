"""Authoring roster serialization, recovery, and rollback coverage."""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

import pytest
from qma.core.vocabulary.enums import PrincipalClass
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.plugins.lifecycle import AtomicRoster
from qma.daemon.plugins.packs import DeskPluginRoster
from qmf.core import Result, is_ok, is_refusal
from qmf.data.store.refusals import policy_rejection


def _runtime(tmp_path: Path, roster_root: Path) -> DeskPluginRoster:
    seed = tmp_path / "seed-corpus"
    seed.mkdir(exist_ok=True)
    return DeskPluginRoster(
        plugin_load_configs=research_corpus_plugin_load_config(seed),
        authoring_roster_root=roster_root,
    )


def _contribution(*, enabled: bool) -> dict[str, object]:
    content: dict[str, object] = {
        "artifact_kind": "graph_template",
        "qualified_id": "demo:authoring",
        "version": "1.0.0",
        "nodes": [],
        "edges": [],
    }
    return {
        "contribution_id": "authoring-contribution:edraft:test:fp1:test",
        "editor_draft_id": "edraft:test",
        "editor_revision": "fp1:test",
        "point": "graph_template",
        "qualified_id": "demo:authoring",
        "version": "1.0.0",
        "bytes": json.dumps(content, sort_keys=True),
        "published": True,
        "enabled": enabled,
    }


def _write_roster(root: Path, contribution: dict[str, object]) -> AtomicRoster:
    roster = AtomicRoster(root)
    initial = roster.load()
    assert is_ok(initial), initial
    payload = dict(initial.value)
    payload["published"] = [contribution]
    saved = roster.publish(payload)
    assert is_ok(saved), saved
    return roster


def test_atomic_roster_generation_cas_serializes_concurrent_writers(tmp_path: Path) -> None:
    roster = _write_roster(tmp_path / "authoring-pack", _contribution(enabled=False))
    first_snapshot = roster.load()
    second_snapshot = roster.load()
    assert is_ok(first_snapshot) and is_ok(second_snapshot)
    barrier = threading.Barrier(2)

    def write(snapshot: Mapping[str, object], marker: str) -> Result[Path]:
        payload = dict(snapshot)
        payload["marker"] = marker
        barrier.wait()
        return AtomicRoster(roster.root).publish(payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(write, first_snapshot.value, "a")
        second = pool.submit(write, second_snapshot.value, "b")
        results: list[Result[Path]] = [first.result(), second.result()]
    assert sum(is_ok(result) for result in results) == 1
    assert sum(is_refusal(result) for result in results) == 1
    latest = roster.load()
    assert is_ok(latest)
    assert latest.value.get("marker") in {"a", "b"}
    generation = cast(int, first_snapshot.value.get("roster_generation", 0))
    assert latest.value.get("roster_generation") == generation + 1


def test_enabled_authoring_contributions_rehydrate_on_pack_startup(tmp_path: Path) -> None:
    roster_root = tmp_path / "authoring-pack"
    _write_roster(roster_root, _contribution(enabled=True))
    roster = AtomicRoster(roster_root)
    before = roster.load()
    assert is_ok(before)

    runtime = _runtime(tmp_path, roster_root)
    activated = runtime.activate()

    assert is_ok(activated), activated
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is not None
    loaded = [
        plugin_id
        for plugin_id in runtime.loader.loaded_ids()
        if plugin_id.startswith("research-authoring-")
    ]
    assert len(loaded) == 1
    after = roster.load()
    assert is_ok(after)
    assert after.value.get("roster_generation") == before.value.get("roster_generation")
    rows = cast(list[dict[str, object]], after.value["published"])
    assert rows[0]["enabled"] is True


def test_enable_rolls_back_loader_catalog_when_roster_persist_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roster_root = tmp_path / "authoring-pack"
    _write_roster(roster_root, _contribution(enabled=False))
    runtime = _runtime(tmp_path, roster_root)
    original_publish = AtomicRoster.publish

    def fail_publish(self: AtomicRoster, payload: Mapping[str, object]) -> Result[Path]:
        if self.root == roster_root:
            return policy_rejection("roster", "simulated durable roster failure")
        return original_publish(self, payload)

    monkeypatch.setattr(AtomicRoster, "publish", fail_publish)
    enabled = runtime.enable_published_authoring_contribution(
        "authoring-contribution:edraft:test:fp1:test",
        principal=PrincipalClass.OPERATOR,
        correlation_id="roster-rollback",
    )

    assert is_refusal(enabled)
    assert not any(
        plugin_id.startswith("research-authoring-") for plugin_id in runtime.loader.loaded_ids()
    )
    assert "demo:authoring" not in runtime.templates.ids()


def test_generated_authoring_disable_and_uninstall_survive_restart(tmp_path: Path) -> None:
    roster_root = tmp_path / "authoring-pack"
    contribution = _contribution(enabled=False)
    _write_roster(roster_root, contribution)
    runtime = _runtime(tmp_path, roster_root)
    enabled = runtime.enable_published_authoring_contribution(
        str(contribution["contribution_id"]), correlation_id="disable-generated"
    )
    assert is_ok(enabled), enabled
    plugin_id = enabled.value.manifest.id
    assert runtime.templates.get("demo:authoring") is not None

    disabled = runtime.loader.disable(plugin_id)
    assert is_ok(disabled), disabled
    roster = AtomicRoster(roster_root)
    after_disable = roster.load()
    assert is_ok(after_disable)
    rows = cast(list[dict[str, object]], after_disable.value["published"])
    assert rows[0]["enabled"] is False

    after_disable_restart = _runtime(tmp_path, roster_root)
    activated = after_disable_restart.activate()
    assert is_ok(activated), activated
    assert "demo:authoring" not in after_disable_restart.templates.ids()
    assert not any(
        item.startswith("research-authoring-") for item in after_disable_restart.loader.loaded_ids()
    )

    removed = after_disable_restart.uninstall_published_authoring_contribution(
        str(contribution["contribution_id"])
    )
    assert is_ok(removed), removed
    after_uninstall = roster.load()
    assert is_ok(after_uninstall)
    assert after_uninstall.value["published"] == []

    after_uninstall_restart = _runtime(tmp_path, roster_root)
    activated_again = after_uninstall_restart.activate()
    assert is_ok(activated_again), activated_again
    assert "demo:authoring" not in after_uninstall_restart.templates.ids()
