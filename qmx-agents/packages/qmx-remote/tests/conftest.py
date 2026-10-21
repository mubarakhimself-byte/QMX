from collections.abc import Iterator
from pathlib import Path

import pytest

QMX_HOME = Path.home() / ".qmx"


def snapshot() -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(QMX_HOME)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in QMX_HOME.rglob("*")
        if path.is_file()
    }


@pytest.fixture(autouse=True)
def isolated_home(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    before = snapshot()
    home = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    for name in ("QMX_HOME", "QMX_TOOLS_ROOT", "QMX_TOOLS_FACTORY"):
        monkeypatch.delenv(name, raising=False)
    yield
    after = snapshot()
    changed = sorted(
        name for name in before.keys() | after.keys() if before.get(name) != after.get(name)
    )
    assert not changed, f"the user's real {QMX_HOME} changed during this test: {changed}"
