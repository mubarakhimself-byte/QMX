"""A publish lands the pack on `main` as the operator's act and materialises its view at once, so
the next chat's surface holds the pack's skills with no restart."""

from __future__ import annotations

import io
import json
import tarfile
from dataclasses import dataclass
from pathlib import Path

from qma.harness import QmxHome
from qma.harness.launch import Home, Interactive
from qma.harness.surface import Declaration, HomeSlots, Supply, build
from qmx_engine.ledger import redact
from qmx_library.principal import MAIN
from qmx_library.store import Store

from qmx_host.sessions import PackLanding

SKILL = "---\nname: {name}\ndescription: Read the morning bias\n---\nRead it.\n"


def bundle(version: str, skill: str) -> bytes:
    plugin: dict[str, object] = {
        "name": "macro-bias",
        "version": version,
        "operations": {"bias": {}},
    }
    files = {
        ".claude-plugin/plugin.json": json.dumps(plugin),
        f"skills/{skill}/SKILL.md": SKILL.format(name=skill),
    }
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, text in files.items():
            body = text.encode()
            member = tarfile.TarInfo(name)
            member.size = len(body)
            tar.addfile(member, io.BytesIO(body))
    return buffer.getvalue()


@dataclass(frozen=True)
class Pack:
    app_id: str
    version: str
    definition_hash: str
    operations: tuple[str, ...]
    bundle: bytes


def chat_skills(home: QmxHome) -> tuple[str, ...]:
    """The pack skills a new chat in the `macro-bias` pack set launches with."""
    supply = Supply((), HomeSlots(home), {}, (home.plugin_dir,), home.root / "spill")
    found = build(
        Interactive(), Home(), ("macro-bias",), Declaration(), supply, workspace=home.root / "ws"
    )
    return tuple(name for name in found.skills if name.startswith("macro-bias:"))


def test_a_published_pack_reaches_the_next_chat_before_any_restart(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    first = Pack("macro-bias", "1.2.0", "sha256:aa", ("bias",), bundle("1.2.0", "brief"))
    second = Pack("macro-bias", "1.3.0", "sha256:bb", ("bias",), bundle("1.3.0", "outlook"))
    with Store.open(tmp_path / "library", redactor=redact) as store:
        before = chat_skills(home)
        land = PackLanding(store, home)
        landed = land(first)
        after_first = chat_skills(home)
        republished = land(second)
        after_second = chat_skills(home)
        head = store.head("macro-bias", MAIN)
    assert before == ()
    assert after_first == ("macro-bias:brief",)
    assert after_second == ("macro-bias:outlook",)
    assert head is not None
    assert head[0] == republished != landed
