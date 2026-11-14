"""tools/ci/backlog.py: CI's findings as backlog rows, from fixture baselines and run summaries."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import backlog
import pytest
import qci
import ratchet

SIZING = "packages/qmf-risk/src/qmf/risk/sizing.py"
BASELINES = {
    "vulture.txt": (
        "# header\n"
        "packages/qmf-core/src/qmf/core/exact.py|vulture|unused import 'Sized'\n"
        "qmn/src/qmn/data/run.py|vulture|unused import 'X'\n"
        "qmn/src/qmn/data/run.py|vulture|unused import 'X'\n"
        "qmn/src/qmn/data/run.py|vulture|unused variable 'y'\n"
        "qmn/src/qmn/data/cast.py|vulture|unused import 'Mapping'\n"
    ),
    "skylos.txt": "tools/a.py|unused_imports:unused_imports|os\ntools/a.py|danger:SKY-D1|eval\n",
    "mutmut.txt": "packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived\n",
    "pyright.txt": f"{SIZING}|reportAttributeAccessIssue|bad\n",
    "known-reds.txt": "# reds\nlinux|qmn|qmn.tests.test_a::test_b\n",
    "flaky.txt": "",
    "mutmut-modules.txt": "# fixed\nqmf.core.exact\nqmf.risk.sizing\n",
}
SOURCES = {
    "qmn/src/qmn/data/run.py": "import X\n",
    "qmn/src/qmn/data/cast.py": (
        "from collections.abc import Mapping\nfrom typing import cast\n\n"
        'x = cast("Mapping[str, int]", {})\n'
    ),
}

DEEP = {
    "reds": [
        {"id": "qmn|qmn.tests.test_a::test_b", "system": "linux", "kind": "known", "blocks": False},
        {"id": "tools|t.test_n::test_m", "system": "windows", "kind": "new", "blocks": True},
        {"id": "qmx-agents/packages/qmx-host|tests.test_f::test_g", "system": "linux"}
        | {"kind": "flaky", "blocks": False},
        {"id": "shard linux-2", "system": "linux", "kind": "unfinished", "blocks": True},
    ],
    "quality": [
        {"tool": "skylos", "key": "qml/src/qml/q.py|quality:SKY-Q1|long", "kind": "new"}
        | {"file": "qml/src/qml/q.py", "blocks": False},
        {"tool": "vulture", "key": "qmb/b.py|vulture|unused import 'z'", "kind": "new"}
        | {"file": "qmb/b.py", "blocks": True},
        {"tool": "vulture", "key": "qmb/c.py|vulture|unused import 'w'", "kind": "new"}
        | {"file": "qmb/c.py"},
        {"tool": "vulture", "key": "qmn/gone.py|vulture|x", "kind": "gone"}
        | {"file": "qmn/gone.py", "blocks": False},
    ],
}

WALK = {
    "level": "walk",
    "reds": [],
    "quality": [
        {"tool": "mutmut", "key": "packages/qmf-core|mutmut|qmf.core.exact.add survived"}
        | {"kind": "new", "file": "packages/qmf-core", "blocks": False},
        {"tool": "mutmut", "key": "packages/qmf-core|mutmut|qmf.core.exact.add no tests"}
        | {"kind": "new", "file": "packages/qmf-core", "blocks": False},
        {"tool": "mutmut", "key": "packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived"}
        | {"kind": "new", "file": "packages/qmf-risk", "blocks": False},
    ],
}

D = "2026-11-14"
EXPECTED = [
    "key\tsource\twhat\twhere\tfirst_seen\tprogram\ttouches\tdoor",
    "vulture|packages/qmf-core/src/qmf/core/exact.py|vulture|unused import 'Sized'\tci-vulture\t"
    f"Vulture: unused import 'Sized'\tpackages/qmf-core/src/qmf/core/exact.py\t{D}\t\t"
    "qmf.core.exact\ttriage",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused import 'X'\tci-vulture\t"
    f"Vulture: unused import 'X'\tqmn/src/qmn/data/run.py\t{D}\t\tnone\tmechanical",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused import 'X'#2\tci-vulture\t"
    f"Vulture: unused import 'X'\tqmn/src/qmn/data/run.py\t{D}\t\tnone\tmechanical",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused variable 'y'\tci-vulture\t"
    f"Vulture: unused variable 'y'\tqmn/src/qmn/data/run.py\t{D}\t\tnone\ttriage",
    "vulture|qmn/src/qmn/data/cast.py|vulture|unused import 'Mapping'\tci-vulture\t"
    f"Vulture: unused import 'Mapping'\tqmn/src/qmn/data/cast.py\t{D}\t\tnone\ttriage",
    "skylos|tools/a.py|unused_imports:unused_imports|os\tci-skylos\t"
    f"Skylos unused_imports:unused_imports: os\ttools/a.py\t{D}\t\tnone\tmechanical",
    "skylos|tools/a.py|danger:SKY-D1|eval\tci-skylos\tSkylos danger:SKY-D1: eval\ttools/a.py\t"
    f"{D}\t\tnone\ttriage",
    "mutmut|packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived\tci-mutmut\t"
    f"mutant survived in qmf.risk.sizing.size_of\tpackages/qmf-risk\t{D}\t\t"
    "qmf.risk.sizing\ttriage",
    f"pyright|{SIZING}|reportAttributeAccessIssue|bad\tci-types\t"
    f"pyright reportAttributeAccessIssue: bad\t{SIZING}\t{D}\t\tqmf.risk.sizing\ttriage",
    "known-red|linux|qmn|qmn.tests.test_a::test_b\tknown-red\t"
    f"red test on linux: qmn.tests.test_a::test_b\tqmn\t{D}\t\tnone\ttriage",
    "flaky|linux|qmx-agents/packages/qmx-host|tests.test_f::test_g\tflaky\t"
    f"flaky test on linux: tests.test_f::test_g\tqmx-agents/packages/qmx-host\t{D}\t\t"
    "none\tmechanical",
    "skylos|qml/src/qml/q.py|quality:SKY-Q1|long\tci-skylos\tSkylos quality:SKY-Q1: long\t"
    f"qml/src/qml/q.py\t{D}\t\tnone\ttriage",
    "mutmut-walk|packages/qmf-core|qmf.core.exact.add\tci-mutmut\t"
    f"2 surviving mutants in qmf.core.exact.add (nightly walk)\tpackages/qmf-core\t{D}\t\t"
    "qmf.core.exact\ttriage",
    "mutmut-walk|packages/qmf-risk|qmf.risk.sizing.size_of\tci-mutmut\t"
    "1 surviving mutant in qmf.risk.sizing.size_of (nightly walk)\tpackages/qmf-risk\t"
    f"{D}\t\tqmf.risk.sizing\ttriage",
]


def _fixture(tmp_path: Path) -> tuple[list[str], Path]:
    baselines, root = tmp_path / "baselines", tmp_path / "repo"
    baselines.mkdir()
    for name, text in BASELINES.items():
        (baselines / name).write_text(text, "utf-8")
    for rel, text in SOURCES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, "utf-8")
    deep, walk = tmp_path / "deep.json", tmp_path / "walk.json"
    deep.write_text(json.dumps(DEEP), "utf-8")
    walk.write_text(json.dumps(WALK), "utf-8")
    argv = ["--baselines", str(baselines), "--root", str(root), "--summary", str(deep)]
    return argv, walk


def _const[T](value: T) -> Callable[..., T]:
    """A stand-in for a function: whatever it is called with, it returns `value`."""

    def answer(*_args: object, **_kwargs: object) -> T:
        return value

    return answer


def _keys(path: Path) -> list[str]:
    return [line.split("\t", 1)[0] for line in path.read_text("utf-8").splitlines()]


def test_fixture_baselines_and_summaries_become_the_expected_rows(tmp_path: Path) -> None:
    argv, walk = _fixture(tmp_path)
    out = tmp_path / "rows.tsv"
    assert backlog.main([*argv, "--summary", str(walk), "--date", D, "--out", str(out)]) == 0
    assert out.read_text("utf-8").splitlines() == EXPECTED


def test_walk_survivors_add_to_the_baselines_rows_for_the_same_function(tmp_path: Path) -> None:
    argv, walk = _fixture(tmp_path)
    alone, both = tmp_path / "alone.tsv", tmp_path / "both.tsv"
    backlog.main([*argv, "--date", D, "--out", str(alone)])
    backlog.main([*argv, "--summary", str(walk), "--date", D, "--out", str(both)])
    added = sorted(set(_keys(both)) - set(_keys(alone)))
    assert added == [
        "mutmut-walk|packages/qmf-core|qmf.core.exact.add",
        "mutmut-walk|packages/qmf-risk|qmf.risk.sizing.size_of",
    ]
    assert "mutmut|packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived" in _keys(both)


def test_the_same_inputs_give_the_same_keys_twice(tmp_path: Path) -> None:
    argv, walk = _fixture(tmp_path)
    first, second = tmp_path / "1.tsv", tmp_path / "2.tsv"
    backlog.main([*argv, "--summary", str(walk), "--date", D, "--out", str(first)])
    backlog.main([*argv, "--summary", str(walk), "--date", "2026-11-15", "--out", str(second)])
    assert _keys(first) == _keys(second)
    assert len(set(_keys(first))) == len(_keys(first))


def test_a_known_red_in_both_the_baseline_and_the_run_is_one_row(tmp_path: Path) -> None:
    argv, _ = _fixture(tmp_path)
    out = tmp_path / "rows.tsv"
    backlog.main([*argv, "--date", "d", "--out", str(out)])
    keys = _keys(out)
    assert keys.count("known-red|linux|qmn|qmn.tests.test_a::test_b") == 1
    blocking = ("test_n::test_m", "shard", "unused import 'z'", "unused import 'w'")
    assert not any(b in k for k in keys for b in blocking)


def test_with_only_a_summary_the_date_must_be_named(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv, _ = _fixture(tmp_path)
    with pytest.raises(SystemExit):
        backlog.main([*argv, "--out", str(tmp_path / "rows.tsv")])
    assert "--date is needed" in capsys.readouterr().err


# ---- the walk, end to end: job_mutmut -> summary.json -> rows -----------------------------------


def test_the_walk_job_records_its_survivors_as_notes_the_backlog_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out, baselines = tmp_path / "ci-out-mutmut-walk-1", tmp_path / "baselines"
    out.mkdir()
    baselines.mkdir()
    (baselines / "mutmut.txt").write_text(
        "packages/qmf-core|mutmut|qmf.core.exact.a survived\n", "utf-8"
    )
    package = tmp_path / "packages" / "qmf-core"
    package.mkdir(parents=True)
    targets = [
        qci.ci_mutate.Target("packages/qmf-core", "qmf.core.exact", name) for name in ("a", "b")
    ]
    results = (
        "    qmf.core.exact.x_a__mutmut_1: survived\n"
        "    qmf.core.exact.x_b__mutmut_1: survived\n"
        "    qmf.core.exact.x_b__mutmut_2: killed\n"
    )

    def fake_run(argv: list[str], cwd: Path, **kwargs: object) -> int:
        out_file = kwargs.get("stdout_to")
        if isinstance(out_file, Path):
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(results if "results" in argv else "", "utf-8")
        return 0

    monkeypatch.setenv("QMX_LEVEL", "walk")
    monkeypatch.setattr(qci, "OUT", out)
    monkeypatch.setattr(qci, "REPO", tmp_path)
    monkeypatch.setattr(qci, "BASELINES", baselines)
    monkeypatch.setattr(qci, "head", _const("a" * 40))
    monkeypatch.setattr(qci, "tree_of", _const("t1"))
    monkeypatch.setattr(qci, "mutate_targets", _const(targets))
    monkeypatch.setattr(qci, "sync", _const(None))
    monkeypatch.setattr(qci, "stage_mutmut", _const(None))
    monkeypatch.setattr(qci, "git", _const(""))
    monkeypatch.setattr(qci, "uv", _const("uv"))
    monkeypatch.setattr(qci, "run", fake_run)
    assert qci.job_mutmut() == 0
    summary = qci.build_summary(
        sha="a" * 40,
        ref="engine/base",
        run_id="5",
        url="u",
        lvl=qci.Level.WALK,
        jobs_of_level=["mutmut-walk"],
        needs={"mutmut-walk": {"result": "success"}},
        api_jobs=None,
        artifacts=tmp_path,
        known_reds=[],
    )
    assert summary["quality"] == [
        {
            "tool": "mutmut",
            "key": "packages/qmf-core|mutmut|qmf.core.exact.b survived",
            "file": "packages/qmf-core",
            "kind": "new",
            "blocks": False,
        }
    ]
    rows = backlog.summary_rows(summary, D, ratchet.read_baseline(baselines / "none.txt"))
    assert [(r.key, r.what) for r in rows] == [
        (
            "mutmut-walk|packages/qmf-core|qmf.core.exact.b",
            "1 surviving mutant in qmf.core.exact.b (nightly walk)",
        )
    ]
