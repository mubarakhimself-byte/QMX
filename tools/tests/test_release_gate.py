"""Independent negative controls for same-candidate release acceptance."""

from copy import deepcopy

import pytest
import release_gate as gate


def evidence() -> dict:
    artifacts = {f"{name}-0.1.0-py3-none-any.whl": "b" * 64 for name in gate.DISTRIBUTIONS}
    artifacts.update(
        dict.fromkeys(
            ("ui.tar.gz", "launcher.py", "requirements.lock", "pack-resources.json"), "b" * 64
        )
    )
    return {
        "candidate": "a" * 40,
        "artifacts": artifacts,
        "checks": {
            name: {
                "status": "PASS",
                "candidate": "a" * 40,
                "artifacts": artifacts,
                "command": "actual command",
                "trace": "trace.log",
            }
            for name in gate.REQUIRED
        },
    }


def test_complete_evidence_positive_control() -> None:
    assert gate.evaluate(evidence()) == []


@pytest.mark.parametrize("status", ["FAIL", "BLOCKED", "NOT RUN", "skipped", None])
@pytest.mark.parametrize("name", gate.REQUIRED)
def test_every_required_lane_must_pass(name: str, status: object) -> None:
    record = evidence()
    record["checks"][name]["status"] = status
    assert gate.evaluate(record)


@pytest.mark.parametrize("name", gate.REQUIRED)
def test_missing_lane_refuses(name: str) -> None:
    record = evidence()
    del record["checks"][name]
    assert gate.evaluate(record)


def test_stale_commit_and_artifact_refuse() -> None:
    for field, value in (("candidate", "c" * 40), ("artifacts", {"product.whl": "c" * 64})):
        record = deepcopy(evidence())
        record["checks"]["installed_launch"][field] = value
        assert gate.evaluate(record)


@pytest.mark.parametrize("record", [None, [], {}, {"candidate": "a" * 40}])
def test_malformed_evidence_refuses(record: object) -> None:
    assert gate.evaluate(record)


def test_arbitrary_inventory_is_not_product() -> None:
    record = evidence()
    record["artifacts"] = {"empty.txt": "b" * 64}
    for check in record["checks"].values():
        check["artifacts"] = record["artifacts"]
    assert gate.evaluate(record)


def test_untyped_command_and_trace_refuse() -> None:
    record = evidence()
    record["checks"]["factory"]["command"] = True
    record["checks"]["factory"]["trace"] = 1
    assert gate.evaluate(record)


def test_missing_actual_artifacts_refuse(tmp_path) -> None:
    assert gate.evaluate(evidence(), evidence_root=tmp_path)


def test_empty_evidence_file_is_not_a_trace(tmp_path) -> None:
    (tmp_path / "trace.log").write_text("")
    assert gate._local_file(tmp_path, "trace.log") is None


def test_plain_text_cannot_impersonate_wheel(tmp_path) -> None:
    path = tmp_path / "qmb-0.1.0-py3-none-any.whl"
    path.write_text("not a wheel")
    assert gate._artifact_errors(path)
