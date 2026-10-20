"""APP2a: an ask is a pinned operation call, a leave is a Library artifact with a freshness."""

from __future__ import annotations

import shutil
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue

from qmx_apps.artifacts import Artifacts, Landing, contract_problems
from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.road.check import check, wire_name
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Stage
from qmx_apps.supervisor import Instance, Pin, Supervisor
from qmx_apps.volume import Volume, VolumeLease

EXAMPLES = Path(__file__).resolve().parents[4] / "examples/apps"
PRODUCER = "exchange-status"
CONSUMER = "weekend-watcher"


class RuntimeFixture(Supervisor):
    """Activation only is faked: a publish never starts a real app process here."""

    running: str | None = None

    def start(
        self,
        app_id: str,
        *,
        definition_hash: str | None = None,
        profile: str | None = None,
    ) -> Document:
        self.running = definition_hash
        return self.status(app_id)

    def stop(self, app_id: str) -> Document:
        self.running = None
        return self.status(app_id)

    def status(self, app_id: str) -> Document:
        return {"status": "running" if self.running else "stopped", "definition_hash": self.running}


def manifest_text(source: Path) -> str:
    return (source / "app.toml").read_text(encoding="utf-8")


def register(
    owner: Supervisor,
    source: Path,
    expected: str | None,
    *,
    version: str | None = None,
    edit: Callable[[str], str] | None = None,
) -> Definition:
    """The immutable image the road holds: a copy under the app's own definitions folder."""
    table = manifest_text(source)
    if version is not None:
        table = table.replace('version = "1.0.0"', f'version = "{version}"', 1)
    if edit is not None:
        table = edit(table)
    (source / "app.toml").write_text(table, encoding="utf-8")
    image = Definition.load(source)
    target = owner.home / "definitions" / image.hash
    shutil.copytree(source, target)
    owner.road.register(Definition.load(target), "first_party", expected)
    return image


def copied(root: Path, name: str, version: str) -> Path:
    source = root / f"{name}-{version}"
    shutil.copytree(EXAMPLES / name, source)
    return source


def shadow(owner: Supervisor, image: Definition) -> None:
    for stage in ("tests", "sandbox", "shadow"):
        with history(owner.home, image.manifest.id) as state:
            state.append(
                Evidence(
                    definition_hash=image.hash,
                    version=image.manifest.version,
                    stage=cast(Stage, stage),
                    passed=True,
                    inputs={"fixture": True},
                    versions={"definition": image.hash},
                    results={"passed": True},
                    duration_seconds=0.0,
                )
            )


def test_an_app_declares_operations_contracts_and_its_trigger(tmp_path: Path) -> None:
    source = tmp_path / "app"
    shutil.copytree(EXAMPLES / "macro-daily-bias", source)
    definition = Definition.load(source)
    manifest = definition.manifest
    assert list(manifest.operations) == ["bias"]
    assert (manifest.operations["bias"].returns, manifest.operations["bias"].approval) == (
        "artifact",
        "read",
    )
    assert manifest.provides["bias"].stale_after == 129600
    assert manifest.suggested_trigger is not None
    assert manifest.suggested_trigger.seconds == 86400
    assert (manifest.isolation.memory_mb, manifest.isolation.cpu_percent) == (None, None)

    table = manifest_text(source).replace(
        "[capabilities]", '[profiles]\nschema = { type = "object" }\n\n[capabilities]'
    )
    (source / "app.toml").write_text(table, encoding="utf-8")
    assert Definition.load(source).manifest.profiles is not None

    retired = table + '\n[emits.bias]\ntype = "object"\n'
    (source / "app.toml").write_text(retired, encoding="utf-8")
    with pytest.raises(AppError, match="emits is retired"):
        Definition.load(source)


def test_an_output_lands_as_an_artifact_and_reads_stale_past_its_share(tmp_path: Path) -> None:
    landings: list[Landing] = []
    artifacts = Artifacts(tmp_path / "home", lambda landing: landings.append(landing) or "fp1:x")
    definition = Definition.load(EXAMPLES / "macro-daily-bias")
    bias: dict[str, JsonValue] = {
        "bias": "bullish",
        "rationale": "recorded fixture",
        "as_of": "2026-10-20T00:00:00Z",
        "source": "fixture",
    }
    ref = artifacts.save(definition, "bias", bias)

    assert [(landing.output, landing.fields["type"], landing.version) for landing in landings] == [
        ("bias", "bias", "1.0.0")
    ]
    assert cast(Document, landings[0].fields["metadata"])["producer_app"] == "macro-daily-bias"
    fresh = artifacts.read(ref)
    assert (fresh["stale"], fresh["stale_after"], fresh["data"]) == (False, 129600, bias)
    assert fresh["library_id"] == "fp1:x"
    assert artifacts.latest("macro-daily-bias", "summary") is None

    with closing(sqlite3.connect(artifacts.index)) as db, db:
        db.execute("UPDATE artifacts SET landed_at = ?", ("2026-10-01T00:00:00+00:00",))
    stale = artifacts.read(ref)
    assert (stale["stale"], stale["stale_after"]) == (True, 129600)
    assert cast(float, stale["age_seconds"]) > 129600

    with pytest.raises(AppError) as undeclared:
        artifacts.save(definition, "summary", bias)
    assert undeclared.value.code == "undeclared_output"


def test_a_changed_provides_schema_is_refused_while_a_consumer_cannot_read_it(
    tmp_path: Path,
) -> None:
    owner = RuntimeFixture(tmp_path / "home")
    save = copied(owner.home, PRODUCER, "1.0.0")
    producer = register(owner, save, None)
    shadow(owner, producer)
    owner.road.publish(PRODUCER, producer.hash)

    register(owner, copied(owner.home, CONSUMER, "1.0.0"), None)
    narrowed = register(
        owner,
        copied(owner.home, PRODUCER, "1.1.0"),
        producer.hash,
        version="1.1.0",
        edit=lambda table: table.replace(
            '[provides.snapshot.properties.observations]\ntype = "array"',
            '[provides.snapshot.properties.observations]\ntype = "string"',
            1,
        ),
    )
    shadow(owner, narrowed)
    with pytest.raises(AppError) as refused:
        owner.road.publish(PRODUCER, narrowed.hash, owner.road.active_revision(PRODUCER))
    assert refused.value.code == "contract_changed"
    assert "snapshot breaks weekend-watcher: observations: the producer gives string" in str(
        refused.value
    )


def test_a_moved_pin_and_a_ring_past_the_host_setting_are_refused(tmp_path: Path) -> None:
    definition = Definition.load(EXAMPLES / "macro-daily-bias")
    lease = VolumeLease(tmp_path, definition.manifest.id)
    instance = Instance(definition, Volume(tmp_path, definition.manifest.id), lease)
    try:
        owner = Supervisor(tmp_path, call_depth=2)
        owner.revalidate(instance, Pin.parse({"pack": "macro-daily-bias", "version": "1.0.0"}))
        with pytest.raises(AppError) as moved:
            owner.revalidate(instance, Pin.parse({"pack": "macro-daily-bias", "version": "0.9.0"}))
        assert (moved.value.code, str(moved.value)) == (
            "pin_stale",
            "pinned macro-daily-bias 0.9.0; macro-daily-bias 1.0.0 is what runs",
        )
        owner.bounded(2)
        with pytest.raises(AppError) as ring:
            owner.bounded(3)
        assert ring.value.code == "call_depth_exceeded"
        Supervisor(tmp_path).bounded(9)
        with pytest.raises(AppError) as bad:
            Pin.parse({"pack": "macro-daily-bias"})
        assert bad.value.code == "invalid_pin"
        assert Pin.parse(None) is None
    finally:
        lease.close()


def test_profiles_partition_data_and_are_never_invented(tmp_path: Path) -> None:
    source = copied(tmp_path, "weekend-watcher", "1.0.0")
    table = manifest_text(source).replace(
        "[capabilities]", '[profiles]\nschema = { type = "object" }\n\n[capabilities]'
    )
    (source / "app.toml").write_text(table, encoding="utf-8")
    definition = Definition.load(source)
    owner = Supervisor(tmp_path / "home")
    lease = VolumeLease(owner.home, definition.manifest.id)
    instance = Instance(
        definition, Volume(owner.home, definition.manifest.id), lease, profile="research"
    )
    try:
        environment = owner.environment(instance)
        assert instance.data == instance.volume.root / "data/profiles/research"
        assert environment["QMX_DATA_DIR"] == str(instance.data)
        assert (environment["QMX_PROFILE"], environment["TMP"]) == (
            "research",
            str(instance.data / "tmp"),
        )
        assert instance.document()["data"] == "data/profiles/research"
        owner.check_profile(definition, "research")
        with pytest.raises(AppError) as named:
            owner.check_profile(definition, "Research")
        assert named.value.code == "invalid_profile"
        plain = Instance(definition, instance.volume, lease)
        assert (plain.data.name, plain.document()["profile"]) == ("data", None)
        without = Definition.load(EXAMPLES / "macro-daily-bias")
        with pytest.raises(AppError) as undeclared:
            owner.check_profile(without, "research")
        assert undeclared.value.code == "undeclared_profile"
    finally:
        lease.close()


def test_app_check_refuses_an_order_act_a_long_wire_name_and_served_extras(
    tmp_path: Path,
) -> None:
    view = tmp_path / "pack"
    (view / ".claude-plugin").mkdir(parents=True)
    (view / ".claude-plugin" / "plugin.json").write_text('{"name": "pack-alpha"}')
    assert wire_name("app:macro-daily-bias", "bias") == "mcp__qmx__app_macro-daily-bias_bias"

    order = check(view, declared=["place_order"], served=["place_order"], toolset="app:x")
    assert order.refusals == (
        "order_act: place_order names the order act submit_order; agents have no path to money "
        "(ruling 116)",
    )
    assert not check(view, declared=["bias"], served=["bias"]).refusals
    long = "b" * 40
    past = check(view, declared=[long], served=[long], toolset="app:" + "a" * 30)
    assert past.refusals[0].startswith(f"wire_name: mcp__qmx__app_{'a' * 30}_{long}")
    differ = check(view, declared=["bias"], served=["bias", "view"])
    assert differ.refusals == (
        "tools_differ: the server's tools differ from the declared rows (declared and not served: "
        "none; served and not declared: view)",
    )


def test_contract_problems_names_only_a_consumer_that_cannot_read_the_change(
    tmp_path: Path,
) -> None:
    published = Definition.load(EXAMPLES / "weekend-watcher")
    reader = Definition.load(EXAMPLES / "exchange-status")
    assert contract_problems(published, [reader], None) == {}
    broken = published.manifest.provides["summary"].model_copy(
        update={"schema_": {"type": "string"}}
    )
    narrowed = Definition(
        published.root,
        published.manifest.model_copy(update={"provides": {"summary": broken}}),
        published.hash,
    )
    feed = reader.manifest.model_copy(
        update={
            "feeds": {
                "summary": published.manifest.provides["summary"].model_copy(
                    update={"schema_": {"type": "object"}}
                )
            }
        }
    )
    wants = Definition(reader.root, feed, reader.hash)
    assert contract_problems(narrowed, [wants], published) == {
        "summary": ["exchange-status: the producer gives string, the consumer needs object"]
    }
