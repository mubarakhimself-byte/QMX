"""A publish lands the pack in the Library and materialises its view at once, so the next chat
loads its skills with no restart."""

from __future__ import annotations

import io
import json
import tarfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from qma.harness import QmxHome, packs
from qmx_engine.ledger import redact
from qmx_library.port import LibraryRefused
from qmx_library.store import Store

from qmx_host.sessions import PackLanding

PLUGIN: dict[str, object] = {"name": "macro-bias", "version": "1.2.0", "operations": {"bias": {}}}
SKILL = "---\nname: brief\ndescription: Read the morning bias\n---\nRead it.\n"


def bundle(files: dict[str, str]) -> bytes:
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


@pytest.mark.xfail(
    raises=LibraryRefused,
    strict=True,
    reason="the engine principal may not put on refs/apps/<id>, nor land a definition on main "
    "(qmx_library.principal.may_advance, Store.merge); the landing's authority is open",
)
def test_a_published_pack_is_a_loadable_view_before_any_restart(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    published = Pack(
        "macro-bias",
        "1.2.0",
        "sha256:aa",
        ("bias",),
        bundle({".claude-plugin/plugin.json": json.dumps(PLUGIN), "skills/brief/SKILL.md": SKILL}),
    )
    with Store.open(tmp_path / "library", redactor=redact) as store:
        before = packs.survey(home.packs_dir, ["macro-bias"])
        landed = PackLanding(store, home)(published)
    after = packs.survey(home.packs_dir, ["macro-bias"])
    assert before.views == ()
    assert [(view.name, view.skills, view.objects) for view in after.views] == [
        ("macro-bias", ("brief",), (landed,))
    ]
