"""tools/ci/backlog.py: CI's findings as backlog rows, from fixture baselines and run summaries."""

from __future__ import annotations

import json
from pathlib import Path

import backlog

BASELINES = {
    "vulture.txt": (
        "# header\n"
        "packages/qmf-core/src/qmf/core/exact.py|vulture|unused import 'Sized'\n"
        "qmn/src/qmn/data/run.py|vulture|unused import 'X'\n"
        "qmn/src/qmn/data/run.py|vulture|unused import 'X'\n"
        "qmn/src/qmn/data/run.py|vulture|unused variable 'y'\n"
    ),
    "skylos.txt": "tools/a.py|unused_imports:unused_imports|os\ntools/a.py|danger:SKY-D1|eval\n",
    "mutmut.txt": "packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived\n",
    "pyright.txt": 'qmn/src/qmn/x.py|reportAttributeAccessIssue|"WinDLL" is not a known attribute\n',
    "known-reds.txt": "# reds\nlinux|qmn|qmn.tests.test_a::test_b\n",
    "flaky.txt": "",
    "mutmut-modules.txt": "# fixed\nqmf.core.exact\nqmf.risk.sizing\n",
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
        {"tool": "vulture", "key": "qmn/gone.py|vulture|x", "kind": "gone"}
        | {"file": "qmn/gone.py", "blocks": False},
    ],
}

WALK = {
    "reds": [],
    "quality": [
        {"tool": "mutmut", "key": "packages/qmf-core|mutmut|qmf.core.exact.add survived"}
        | {"kind": "new", "file": "packages/qmf-core", "blocks": False},
        {"tool": "mutmut", "key": "packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived"}
        | {"kind": "new", "file": "packages/qmf-risk", "blocks": False},
    ],
}

EXPECTED = [
    "key\tsource\twhat\twhere\tfirst_seen\tprogram\ttouches\tdoor",
    "vulture|packages/qmf-core/src/qmf/core/exact.py|vulture|unused import 'Sized'\tci-vulture\t"
    "Vulture: unused import 'Sized'\tpackages/qmf-core/src/qmf/core/exact.py\t2026-11-14\t\t"
    "qmf.core.exact\ttriage",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused import 'X'\tci-vulture\t"
    "Vulture: unused import 'X'\tqmn/src/qmn/data/run.py\t2026-11-14\t\tnone\tmechanical",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused import 'X'#2\tci-vulture\t"
    "Vulture: unused import 'X'\tqmn/src/qmn/data/run.py\t2026-11-14\t\tnone\tmechanical",
    "vulture|qmn/src/qmn/data/run.py|vulture|unused variable 'y'\tci-vulture\t"
    "Vulture: unused variable 'y'\tqmn/src/qmn/data/run.py\t2026-11-14\t\tnone\ttriage",
    "skylos|tools/a.py|unused_imports:unused_imports|os\tci-skylos\t"
    "Skylos unused_imports:unused_imports: os\ttools/a.py\t2026-11-14\t\tnone\tmechanical",
    "skylos|tools/a.py|danger:SKY-D1|eval\tci-skylos\tSkylos danger:SKY-D1: eval\ttools/a.py\t"
    "2026-11-14\t\tnone\ttriage",
    "mutmut|packages/qmf-risk|mutmut|qmf.risk.sizing.size_of survived\tci-mutmut\t"
    "mutant survived in qmf.risk.sizing.size_of\tpackages/qmf-risk\t2026-11-14\t\t"
    "qmf.risk.sizing\ttriage",
    'pyright|qmn/src/qmn/x.py|reportAttributeAccessIssue|"WinDLL" is not a known attribute\t'
    'ci-types\tpyright reportAttributeAccessIssue: "WinDLL" is not a known attribute\t'
    "qmn/src/qmn/x.py\t2026-11-14\t\tnone\ttriage",
    "known-red|linux|qmn|qmn.tests.test_a::test_b\tknown-red\t"
    "red test on linux: qmn.tests.test_a::test_b\tqmn\t2026-11-14\t\tnone\ttriage",
    "flaky|linux|qmx-agents/packages/qmx-host|tests.test_f::test_g\tflaky\t"
    "flaky test on linux: tests.test_f::test_g\tqmx-agents/packages/qmx-host\t2026-11-14\t\t"
    "none\tmechanical",
    "skylos|qml/src/qml/q.py|quality:SKY-Q1|long\tci-skylos\tSkylos quality:SKY-Q1: long\t"
    "qml/src/qml/q.py\t2026-11-14\t\tnone\ttriage",
    "mutmut|packages/qmf-core|mutmut|qmf.core.exact.add survived\tci-mutmut\t"
    "mutant survived in qmf.core.exact.add\tpackages/qmf-core\t2026-11-14\t\tqmf.core.exact\ttriage",
]


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    baselines = tmp_path / "baselines"
    baselines.mkdir()
    for name, text in BASELINES.items():
        (baselines / name).write_text(text, "utf-8")
    deep, walk = tmp_path / "deep.json", tmp_path / "walk.json"
    deep.write_text(json.dumps(DEEP), "utf-8")
    walk.write_text(json.dumps(WALK), "utf-8")
    return baselines, deep, walk


def test_fixture_baselines_and_summaries_become_the_expected_rows(tmp_path: Path) -> None:
    baselines, deep, walk = _fixture(tmp_path)
    out = tmp_path / "rows.tsv"
    argv = ["--baselines", str(baselines), "--summary", str(deep), "--summary", str(walk)]
    assert backlog.main([*argv, "--date", "2026-11-14", "--out", str(out)]) == 0
    assert out.read_text("utf-8").splitlines() == EXPECTED


def test_the_same_inputs_give_the_same_keys_twice(tmp_path: Path) -> None:
    baselines, deep, walk = _fixture(tmp_path)
    first, second = tmp_path / "1.tsv", tmp_path / "2.tsv"
    argv = ["--baselines", str(baselines), "--summary", str(deep), "--summary", str(walk)]
    backlog.main([*argv, "--date", "2026-11-14", "--out", str(first)])
    backlog.main([*argv, "--date", "2026-11-15", "--out", str(second)])
    keys = [
        [line.split("\t", 1)[0] for line in p.read_text("utf-8").splitlines()]
        for p in (first, second)
    ]
    assert keys[0] == keys[1]
    assert len(set(keys[0])) == len(keys[0])


def test_a_known_red_in_both_the_baseline_and_the_run_is_one_row(tmp_path: Path) -> None:
    baselines, deep, _ = _fixture(tmp_path)
    out = tmp_path / "rows.tsv"
    backlog.main(
        ["--baselines", str(baselines), "--summary", str(deep), "--date", "d", "--out", str(out)]
    )
    keys = [line.split("\t", 1)[0] for line in out.read_text("utf-8").splitlines()]
    assert keys.count("known-red|linux|qmn|qmn.tests.test_a::test_b") == 1
    assert not any("test_n::test_m" in k or "shard" in k or "unused import 'z'" in k for k in keys)
