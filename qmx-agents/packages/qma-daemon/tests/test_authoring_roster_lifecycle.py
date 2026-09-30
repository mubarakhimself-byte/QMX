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
from qma.daemon.taskgraph.records import GraphTemplate
from qmf.core import Result, is_ok, is_refusal
from qmf.core.fingerprint import fingerprint_bytes
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
    body = json.dumps(content, sort_keys=True)
    revision = fingerprint_bytes(body.encode("utf-8")).value
    draft_id = "edraft:test"
    return {
        "contribution_id": f"authoring-contribution:{draft_id}:{revision}",
        "editor_draft_id": "edraft:test",
        "editor_revision": revision,
        "point": "graph_template",
        "qualified_id": "demo:authoring",
        "version": "1.0.0",
        "bytes": body,
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
        str(_contribution(enabled=False)["contribution_id"]),
        principal=PrincipalClass.OPERATOR,
        correlation_id="roster-rollback",
    )

    assert is_refusal(enabled)
    assert not any(
        plugin_id.startswith("research-authoring-") for plugin_id in runtime.loader.loaded_ids()
    )
    assert "demo:authoring" not in runtime.templates.ids()


def test_authoring_disable_requires_operator_and_preserves_live_state_on_persist_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roster_root = tmp_path / "authoring-pack"
    contribution = _contribution(enabled=False)
    _write_roster(roster_root, contribution)
    runtime = _runtime(tmp_path, roster_root)
    enabled = runtime.enable_published_authoring_contribution(
        str(contribution["contribution_id"]),
        principal=PrincipalClass.OPERATOR,
        correlation_id="disable-generated",
    )
    assert is_ok(enabled), enabled
    plugin_id = enabled.value.manifest.id
    assert runtime.templates.get("demo:authoring") is not None

    roster = AtomicRoster(roster_root)
    denied_disable = runtime.disable_published_authoring_contribution(
        str(contribution["contribution_id"]), principal=PrincipalClass.MACHINE
    )
    denied_uninstall = runtime.uninstall_published_authoring_contribution(
        str(contribution["contribution_id"]), principal=PrincipalClass.MACHINE
    )
    assert is_refusal(denied_disable)
    assert is_refusal(denied_uninstall)
    assert plugin_id in runtime.loader.loaded_ids()
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is not None

    original_publish = AtomicRoster.publish

    def fail_authoring_persist(self: AtomicRoster, payload: Mapping[str, object]) -> Result[Path]:
        if self.root == roster_root:
            return policy_rejection("roster", "simulated durable disable failure")
        return original_publish(self, payload)

    monkeypatch.setattr(AtomicRoster, "publish", fail_authoring_persist)
    failed_disable = runtime.disable_published_authoring_contribution(
        str(contribution["contribution_id"]), principal=PrincipalClass.OPERATOR
    )
    assert is_refusal(failed_disable)
    assert plugin_id in runtime.loader.loaded_ids()
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is not None
    before_success = roster.load()
    assert is_ok(before_success), before_success
    assert cast(list[dict[str, object]], before_success.value["published"])[0]["enabled"] is True

    monkeypatch.setattr(AtomicRoster, "publish", original_publish)
    disabled = runtime.disable_published_authoring_contribution(
        str(contribution["contribution_id"]), principal=PrincipalClass.OPERATOR
    )
    assert is_ok(disabled), disabled
    after_disable = roster.load()
    assert is_ok(after_disable), after_disable
    rows = cast(list[dict[str, object]], after_disable.value["published"])
    assert rows[0]["enabled"] is False
    assert plugin_id not in runtime.loader.loaded_ids()
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is None

    after_disable_restart = _runtime(tmp_path, roster_root)
    activated = after_disable_restart.activate()
    assert is_ok(activated), activated
    assert "demo:authoring" not in after_disable_restart.templates.ids()
    assert not any(
        item.startswith("research-authoring-") for item in after_disable_restart.loader.loaded_ids()
    )


def test_repeated_disable_does_not_remove_a_later_provider_template(tmp_path: Path) -> None:
    roster_root = tmp_path / "authoring-pack"
    contribution = _contribution(enabled=False)
    _write_roster(roster_root, contribution)
    runtime = _runtime(tmp_path, roster_root)
    contribution_id = str(contribution["contribution_id"])
    enabled = runtime.enable_published_authoring_contribution(
        contribution_id,
        principal=PrincipalClass.OPERATOR,
        correlation_id="disable-owner",
    )
    assert is_ok(enabled), enabled
    disabled = runtime.disable_published_authoring_contribution(
        contribution_id, principal=PrincipalClass.OPERATOR
    )
    assert is_ok(disabled), disabled
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is None

    later_provider_template = GraphTemplate(qualified_id="demo:authoring", version="1.0.0")
    registered = runtime.templates.register(later_provider_template)
    assert is_ok(registered), registered
    repeated = runtime.disable_published_authoring_contribution(
        contribution_id, principal=PrincipalClass.OPERATOR
    )
    assert is_ok(repeated), repeated
    assert runtime.templates.get_versioned("demo:authoring", "1.0.0") is later_provider_template
