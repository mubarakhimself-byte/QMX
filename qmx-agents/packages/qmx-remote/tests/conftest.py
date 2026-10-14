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
def untouched_user_home() -> Iterator[None]:
    before = snapshot()
    yield
    after = snapshot()
    changed = sorted(
        name for name in before.keys() | after.keys() if before.get(name) != after.get(name)
    )
    assert not changed, f"test wrote under the user's real {QMX_HOME}: {changed}"
