"""C-27a: a job result may carry `outputs`, each landed as its own artifact, and a ref the Library
already holds is never landed twice.

The app is a real supervised process whose job answers what the test asks it to, so every case
below is a real job result crossing the host's job queue.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from pydantic import JsonValue
from qmx_engine.ledger import redact
from qmx_host.host import landers  # pyright: ignore[reportMissingTypeStubs]
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_apps.artifacts import Landing
from qmx_apps.errors import AppError, Document
from qmx_apps.supervisor import Supervisor

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
OPERATOR = Principal("operator")
APP = "outputs"
NOTE = '\n[provides.note]\ntype = "object"\nrequired = ["n"]\nproperties = { n = { type = "integer" } }\n'
TESTER = '\n[provides.backtest-result]\nlander = "qmb-run"\nschema = { type = "object" }\n'

JOB = """\
import hashlib
import json
from pathlib import Path


def result(inputs):
    report = json.dumps({"trades": 2}).encode()
    (Path(inputs["run_folder"]) / "report.json").write_bytes(report)
    return {
        "run_id": inputs["run_id"],
        "status": "finished",
        "tester": {"app": "outputs"},
        "measures": {"trades": 2},
        "consumed": [],
        "files": [
            {
                "slot": "report",
                "path": "report.json",
                "fp": "fp1:sha256:" + hashlib.sha256(report).hexdigest(),
            }
        ],
    }


def run(inputs):
    answer = inputs["answer"]
    listed = answer.get("outputs") if isinstance(answer, dict) else None
    for item in listed if isinstance(listed, list) else []:
        if isinstance(item, dict) and item.get("data") == "RESULT":
            item["data"] = result(inputs)
    return answer
"""


def note(n: int) -> Document:
    return {"output": "note", "data": {"n": n}}


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


class Plain:
    """A sink that keeps every landing it is handed and never deduplicates, so the count it holds
    is what the host's own duplicate rule leaves. It fails the landings `failing` names once."""

    def __init__(self) -> None:
        self.landed: list[Landing] = []
        self.calls = 0
        self.failing: set[int] = set()

    def __call__(self, landing: Landing) -> str:
        self.calls += 1
        if self.calls in self.failing:
            raise RuntimeError("the sink died mid-batch")
        self.landed.append(landing)
        return f"plain-{len(self.landed)}"

    def data(self) -> list[JsonValue]:
        return [it.data for it in self.landed]


@pytest.fixture
def store(tmp_path: Path) -> Generator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as opened:
        yield opened


@pytest.fixture
def plain() -> Plain:
    return Plain()


@pytest.fixture
def supervisor(tmp_path: Path, store: Store, plain: Plain) -> Generator[Supervisor]:
    owner = Supervisor(tmp_path / "home", library=plain)
    owner.attach_landers(landers(store, owner, "pc"))
    try:
        yield owner
    finally:
        owner.close()


def started(tmp_path: Path, supervisor: Supervisor, extra: str) -> None:
    target = tmp_path / "source"
    shutil.copytree(EXAMPLE, target, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    shutil.copyfile(Path(__file__).with_name("fixture_server.py"), target / "server.py")
    manifest = target / "app.toml"
    text = (
        manifest.read_text()
        .replace('id = "exchange-status"', f'id = "{APP}"')
        .replace('mcp = "server.py"', 'mcp = "server.py"\njobs = ["job.py"]')
    )
    manifest.write_text(text + NOTE + extra)
    (target / "job.py").write_text(JOB)
    supervisor.install(target, trust="first_party")
    supervisor.start(APP)


def answer(supervisor: Supervisor, value: JsonValue, **kwargs: object) -> Document:
    inputs = cast(Document, {**cast(Document, kwargs.pop("inputs", {})), "answer": value})
    return supervisor.run_job(APP, "job.py", inputs=inputs, **kwargs)  # pyright: ignore[reportArgumentType]


def outputs_of(ran: Document) -> list[str]:
    return [str(cast(Document, ref)["output"]) for ref in cast(list[JsonValue], ran["artifact_refs"])]


def test_three_outputs_land_three_artifacts_and_a_result_without_outputs_lands_as_before(
    tmp_path: Path, supervisor: Supervisor, plain: Plain
) -> None:
    started(tmp_path, supervisor, "")

    many = answer(supervisor, {"outputs": [note(1), note(2), note(3)], "seen": 3})
    one = answer(supervisor, note(4))
    none = answer(supervisor, {"seen": 0})
    empty = answer(supervisor, {"outputs": []})

    assert (outputs_of(many), many["result"]) == (["note", "note", "note"], {"seen": 3})
    assert sorted(one) == ["app_id", "artifact_ref", "instance_id", "job", "profile", "result", "version"]
    assert (one["result"], cast(Document, one["artifact_ref"])["output"]) == (note(4), "note")
    assert sorted(none) == ["app_id", "instance_id", "job", "profile", "result", "version"]
    assert (empty["artifact_refs"], empty["result"]) == ([], {})
    assert plain.data() == [{"n": 1}, {"n": 2}, {"n": 3}, {"n": 4}]
    assert supervisor.read_output(APP, "note")["data"] == {"n": 4}


def test_the_same_output_sent_twice_leaves_one_library_item(
    tmp_path: Path, supervisor: Supervisor, plain: Plain
) -> None:
    started(tmp_path, supervisor, "")

    first = answer(supervisor, {"outputs": [note(1), note(1)]})
    again = answer(supervisor, {"outputs": [note(1), note(2)]})
    single = answer(supervisor, note(2))

    refs = cast(list[JsonValue], first["artifact_refs"])
    assert refs[0] == refs[1] == cast(list[JsonValue], again["artifact_refs"])[0]
    assert single["artifact_ref"] == cast(list[JsonValue], again["artifact_refs"])[1]
    assert plain.data() == [{"n": 1}, {"n": 2}]


def test_a_refused_output_lands_none_of_its_batch(
    tmp_path: Path, supervisor: Supervisor, plain: Plain
) -> None:
    started(tmp_path, supervisor, "")

    codes: list[tuple[str, str]] = []
    for bad in (
        {"outputs": [note(1), {"output": "note", "data": {"n": "two"}}]},
        {"outputs": [note(1), {"output": "nowhere", "data": {}}]},
        {"outputs": [note(1), {"output": "note"}]},
        {"outputs": note(1)},
        {"outputs": [note(1)], **note(2)},
    ):
        with pytest.raises(AppError) as refused:
            answer(supervisor, cast(JsonValue, bad))
        codes.append((refused.value.code, str(refused.value)))

    assert codes == [
        ("invalid_output", "Output does not match the declared provides schema."),
        ("undeclared_output", "The app did not declare this output."),
        ("invalid_output", "Each of outputs is one {output, data}."),
        ("invalid_output", "outputs is a list of {output, data}."),
        ("invalid_output", "A job answers output and data, or outputs, not both."),
    ]
    assert plain.landed == []
    assert supervisor.status(APP)["status"] == "running"


def test_a_batch_cut_between_two_landings_lands_each_output_once_when_sent_again(
    tmp_path: Path, supervisor: Supervisor, plain: Plain
) -> None:
    started(tmp_path, supervisor, "")
    plain.failing = {2}
    batch: JsonValue = {"outputs": [note(1), note(2), note(3)]}

    with pytest.raises(RuntimeError, match="the sink died mid-batch"):
        answer(supervisor, batch)
    resent = answer(supervisor, batch)

    assert outputs_of(resent) == ["note", "note", "note"]
    assert plain.data() == [{"n": 1}, {"n": 2}, {"n": 3}]


def unit(store: Store) -> str:
    draft = Draft("note", "unit-1", "unit-1", fields={})
    return store.put(OPERATOR, draft, on="main", expected_head=None).object_id


def test_a_lander_output_among_outputs_still_lands_once_per_run(
    tmp_path: Path, supervisor: Supervisor, plain: Plain, store: Store
) -> None:
    started(tmp_path, supervisor, TESTER)
    pinned = unit(store)
    lands = {"outputs": [{"output": "backtest-result", "data": "RESULT"}, note(7)]}
    twice = {"outputs": [{"output": "backtest-result", "data": "RESULT"}] * 2}

    ran = answer(supervisor, lands, inputs={"unit": pinned}, principal="operator")
    with pytest.raises(AppError) as refused:
        answer(supervisor, twice, inputs={"unit": pinned}, principal="operator")
    with pytest.raises(AppError) as missing:
        answer(supervisor, {"outputs": [note(8)]}, inputs={"unit": pinned}, principal="operator")

    run_id = str(ran["run_id"])
    head = store.head(run_id, "main")
    assert head is not None
    assert store.get(OPERATOR, head[0]).fields["status"] == "finished"
    assert outputs_of(ran) == ["backtest-result", "note"]
    assert (refused.value.code, str(refused.value)) == (
        "lander_once",
        "Job job.py answered 2 results its lander lands; a run lands one.",
    )
    assert missing.value.code == "result_missing"
    assert plain.data() == [{"n": 7}]
