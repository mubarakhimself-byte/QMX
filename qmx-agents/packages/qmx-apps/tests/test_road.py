"""Adapt the surviving MA02–MA04 rules; the old daemon suites remain intact."""

from __future__ import annotations

import secrets
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import cast

import pytest
from qmx_ledger.journal import RunJournal, encoded, fingerprint

from qmx_apps.errors import AppError, Document
from qmx_apps.manifest import Definition
from qmx_apps.road.history import history
from qmx_apps.road.models import Evidence, Proof, Stage, json_document
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import VolumeLease

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"


class RuntimeFixture(Supervisor):
    """Only activation is faked here; separate integration tests use P12 processes."""

    running: str | None = None
    refuse: str | None = None

    def start(
        self,
        app_id: str,
        *,
        definition_hash: str | None = None,
        profile: str | None = None,
    ) -> Document:
        if self.refuse == definition_hash:
            raise AppError("start_failed", "Fixture activation failure", 503)
        self.running = definition_hash
        return self.status(app_id)

    def stop(self, app_id: str) -> Document:
        self.running = None
        return self.status(app_id)

    def status(self, app_id: str) -> Document:
        return {"status": "running" if self.running else "stopped", "definition_hash": self.running}


def save(
    owner: Supervisor, version: str, expected: str | None, *, risk: str = "money"
) -> Definition:
    source = owner.home / f"source-{version}"
    shutil.copytree(EXAMPLE, source)
    manifest = source / "app.toml"
    manifest.write_text(
        manifest.read_text()
        .replace('version = "1.0.0"', f'version = "{version}"')
        .replace('risk = "shows"', f'risk = "{risk}"')
    )
    image = Definition.load(source)
    target = owner.home / "definitions" / image.hash
    shutil.copytree(source, target)
    image = Definition.load(target)
    owner.road.register(image, "first_party", expected)
    return image


def proof(owner: Supervisor, image: Definition, stage: Stage, *, passed: bool = True) -> None:
    with history(owner.home, image.manifest.id) as state:
        state.append(
            Evidence(
                definition_hash=image.hash,
                version=image.manifest.version,
                stage=stage,
                passed=passed,
                inputs={"fixture": True},
                versions={"definition": image.hash},
                results={"passed": passed},
                duration_seconds=0.1,
            )
        )


def shadow(owner: Supervisor, image: Definition) -> None:
    for stage in ("tests", "sandbox", "shadow"):
        proof(owner, image, cast(Stage, stage))


@pytest.fixture
def owner(tmp_path: Path) -> RuntimeFixture:
    return RuntimeFixture(tmp_path / "home")


def test_restart_exact_versions_receipts_and_projection_rebuild(owner: RuntimeFixture) -> None:
    first = save(owner, "1.0.0", None)
    second = save(owner, "1.1.0", first.hash)
    records = owner.road.evidence("exchange-status")
    assert records[1]["parent"] == first.hash
    with closing(sqlite3.connect(owner.catalog)) as db, db:
        db.execute("DELETE FROM definitions")
        db.execute("DELETE FROM selected")
    reopened = RuntimeFixture(owner.home)
    assert reopened.road.evidence("exchange-status") == records
    assert reopened.get("exchange-status")["definition_hash"] == second.hash


def test_competing_same_base_serializes_without_lost_data(owner: RuntimeFixture) -> None:
    first = save(owner, "1.0.0", None)
    second = save(owner, "1.1.0", first.hash)
    with pytest.raises(AppError, match="head changed"):
        save(owner, "1.2.0", first.hash)
    assert owner.get("exchange-status")["definition_hash"] == second.hash


def test_immutable_version_rule_survives_projection_loss(owner: RuntimeFixture) -> None:
    first = save(owner, "1.0.0", None)
    source = owner.home / "changed"
    shutil.copytree(first.root, source)
    (source / "server.py").write_text("changed content")
    changed = Definition.load(source)
    target = owner.home / "definitions" / changed.hash
    shutil.copytree(source, target)
    with closing(sqlite3.connect(owner.catalog)) as db, db:
        db.execute("DELETE FROM definitions")
    with pytest.raises(AppError, match="new version"):
        owner.road.register(Definition.load(target), "first_party", first.hash)
    assert owner.get("exchange-status")["definition_hash"] == first.hash


def test_road_writer_lock_cannot_collide_with_another_app_id(owner: RuntimeFixture) -> None:
    image = save(owner, "1.0.0", None)
    lease = VolumeLease(owner.home, "exchange-status-road")
    try:
        assert owner.road.evidence("exchange-status")[0]["definition_hash"] == image.hash
    finally:
        lease.close()


@pytest.mark.parametrize("stage", ["sandbox", "shadow", "live"])
def test_skipping_stages_refuses_without_evidence(owner: RuntimeFixture, stage: Stage) -> None:
    image = save(owner, "1.0.0", None)
    with pytest.raises((AppError, ValueError)):
        if stage == "live":
            owner.road.publish("exchange-status", image.hash)
        else:
            owner.road.advance("exchange-status", image.hash, stage)
    assert len(owner.road.evidence("exchange-status")) == 1


def test_failed_step_keeps_stage_and_currentness_is_rechecked(owner: RuntimeFixture) -> None:
    image = save(owner, "1.0.0", None)
    proof(owner, image, "tests", passed=False)
    with history(owner.home, "exchange-status") as state:
        assert state.stages[image.hash] == "build"
    shadow(owner, image)
    save(owner, "1.1.0", image.hash)
    with pytest.raises(AppError) as refused:
        owner.road.publish("exchange-status", image.hash)
    assert refused.value.code == "head_conflict"


@pytest.mark.parametrize("risk", ["shows", "runs", "money"])
def test_risk_rules_signature_and_fixed_budget(owner: RuntimeFixture, risk: str) -> None:
    image = save(owner, "1.0.0", None, risk=risk)
    shadow(owner, image)
    owner.road.signing_key(secrets.token_urlsafe(32))
    if risk == "money":
        with pytest.raises(AppError) as denied:
            owner.road.publish("exchange-status", image.hash)
        assert denied.value.code == "signature_required"
    signature = owner.road.sign("exchange-status", image.hash, None)
    record = owner.road.publish("exchange-status", image.hash, signature=signature)
    assert record["stage"] == "live"
    results = cast(Document, record["results"])
    assert results["proposal_only"] == (risk == "money")
    assert results["budget"] == image.manifest.budget.model_dump(mode="json")
    with pytest.raises(AppError) as stale:
        owner.road.publish("exchange-status", image.hash, signature=signature)
    assert stale.value.code == "publication_conflict"


def test_create_publish_replace_undo_and_restart(owner: RuntimeFixture) -> None:
    first = save(owner, "1.0.0", None, risk="shows")
    shadow(owner, first)
    published = owner.road.publish("exchange-status", first.hash)
    second = save(owner, "1.1.0", first.hash, risk="shows")
    assert owner.running == first.hash
    shadow(owner, second)
    replaced = owner.road.publish("exchange-status", second.hash, str(published["revision"]))
    rolled = owner.road.publish(
        "exchange-status", second.hash, str(replaced["revision"]), rollback=True
    )
    assert rolled["action"] == "rollback" and rolled["definition_hash"] == first.hash
    assert rolled["revision"] not in {str(published["revision"]), str(replaced["revision"])}
    assert owner.get("exchange-status")["definition_hash"] == second.hash
    assert owner.running == first.hash
    assert RuntimeFixture(owner.home).road.evidence("exchange-status")[-1] == rolled


def test_runtime_staging_failure_preserves_last_good(owner: RuntimeFixture) -> None:
    first = save(owner, "1.0.0", None, risk="shows")
    shadow(owner, first)
    active = owner.road.publish("exchange-status", first.hash)
    second = save(owner, "1.1.0", first.hash, risk="shows")
    shadow(owner, second)
    owner.refuse = second.hash
    with pytest.raises(AppError, match="activation failure"):
        owner.road.publish("exchange-status", second.hash, str(active["revision"]))
    assert owner.running == first.hash
    assert owner.road.active_revision("exchange-status") == active["revision"]


def test_competing_active_revision_cas(owner: RuntimeFixture) -> None:
    image = save(owner, "1.0.0", None, risk="shows")
    shadow(owner, image)

    def publish(_: int) -> str:
        try:
            return str(owner.road.publish("exchange-status", image.hash)["revision"])
        except AppError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, range(2)))
    assert len([result for result in results if len(result) == 64]) == 1
    assert results.count("publication_conflict") == 1
    assert (
        len(
            [
                record
                for record in owner.road.evidence("exchange-status")
                if record["stage"] == "live"
            ]
        )
        == 1
    )


@pytest.mark.parametrize("mutation", ["blob", "journal", "image"])
def test_corrupted_history_refuses_before_projection_rebuild(
    owner: RuntimeFixture, mutation: str
) -> None:
    image = save(owner, "1.0.0", None)
    folder = owner.home / "apps/exchange-status/road"
    if mutation == "blob":
        next((folder / "steps.jsonl.results").iterdir()).write_bytes(b"changed")
    elif mutation == "journal":
        with (folder / "steps.jsonl").open("ab") as stream:
            stream.write(b"incomplete")
    else:
        (image.root / "server.py").write_text("changed")
    with pytest.raises(AppError):
        owner.road.evidence("exchange-status")
    with closing(sqlite3.connect(owner.catalog)) as db:
        assert db.execute("SELECT hash FROM selected").fetchone()[0] == image.hash


@pytest.mark.parametrize(
    "data", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'{"x":"\\ud800"}', b"[]"]
)
def test_finite_unambiguous_unicode_json(data: bytes) -> None:
    with pytest.raises(AppError):
        json_document(data)


@pytest.mark.parametrize(
    "body",
    [
        {"source": "live", "cases": []},
        {"source": "live", "cases": [{"tool": "x", "expected": None}], "passed": True},
        {"source": "live", "cases": [{"tool": "x", "expected": None, "code": "execute"}]},
    ],
)
def test_closed_proof_inputs(body: Document) -> None:
    with pytest.raises(ValueError):
        Proof.model_validate(body)


@pytest.mark.parametrize("mutation", ["parent", "version", "unknown", "passed"])
def test_self_consistent_forged_version_refuses_replay(
    owner: RuntimeFixture, mutation: str
) -> None:
    image = save(owner, "1.0.0", None)
    folder = owner.home / "apps/exchange-status/road"
    path = folder / "steps.jsonl"
    envelope = json_document(path.read_bytes())
    payload = cast(Document, envelope["payload"])
    body = json_document((folder / str(payload["result_ref"])).read_bytes())
    body[mutation] = {"parent": "wrong", "version": "2.0.0", "unknown": True, "passed": False}[
        mutation
    ]
    data = encoded(body)
    from hashlib import sha256

    digest = sha256(data).hexdigest()
    (folder / "steps.jsonl.results" / digest).write_bytes(data)
    payload.update({"result_ref": f"steps.jsonl.results/{digest}", "byte_count": len(data)})
    envelope.pop("fingerprint")
    envelope["fingerprint"] = fingerprint(envelope)
    path.write_bytes(encoded(envelope) + b"\n")
    with pytest.raises(AppError):
        owner.road.evidence("exchange-status")
    with closing(sqlite3.connect(owner.catalog)) as db:
        assert db.execute("SELECT hash FROM selected").fetchone()[0] == image.hash


def test_precommit_failure_then_retry_preserves_runtime(
    owner: RuntimeFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = save(owner, "1.0.0", None, risk="shows")
    shadow(owner, image)
    original = RunJournal.append

    def fail(self: RunJournal, event: str, payload: object) -> dict[str, object]:
        raise OSError("write failed")

    monkeypatch.setattr(RunJournal, "append", fail)
    with pytest.raises(AppError):
        owner.road.publish("exchange-status", image.hash)
    assert owner.running is None
    monkeypatch.setattr(RunJournal, "append", original)
    assert owner.road.publish("exchange-status", image.hash)["stage"] == "live"


def test_postcommit_projection_failure_reports_committed_and_repairs(
    owner: RuntimeFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qmx_apps import road

    image = save(owner, "1.0.0", None, risk="shows")
    shadow(owner, image)

    def fail(*args: object) -> None:
        raise OSError("projection failed")

    monkeypatch.setattr(road, "project", fail)
    with pytest.raises(AppError) as committed:
        owner.road.publish("exchange-status", image.hash)
    assert committed.value.code == "publication_committed"
    assert owner.running == image.hash
    monkeypatch.undo()
    record = owner.road.evidence("exchange-status")[-1]
    assert record["stage"] == "live" and record["passed"] is True
    with closing(sqlite3.connect(owner.catalog)) as db:
        assert db.execute("SELECT revision FROM active").fetchone()[0] == record["revision"]
