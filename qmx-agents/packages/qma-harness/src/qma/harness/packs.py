"""Pack plugin views: materialise, verify and list them (engine AD-55).

A pack is a published Library object. A chat loads the core plugin plus one view per pack in its
set (AD-35), so `qma.harness.surface` asks this module which views are on disk and this module
says whether their bytes still match what was published.

A view holds `.claude-plugin/plugin.json`, `skills/`, `agents/` and `commands/` only. A pack's
own `hooks/` and `.mcp.json` are never written, so a pack can neither run a hook nor start a
server in a chat: its tools are catalog rows on the chat's one `qmx` server (AD-61).

The record of what was materialised is `<plugins>/views.json`, beside the views and never inside
one, so each view folder keeps exactly the four things the CLI reads. A view whose bytes no
longer hash to its recorded digest is not loaded and the other views still are.

`library-skills` is one more view, holding the published Library skills that belong to no pack.
Its integrity check hashes a manifest of member object ids, because it aggregates many objects
into one folder.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import shutil
import tarfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

log = logging.getLogger(__name__)

PLUGIN_JSON: Final = ".claude-plugin/plugin.json"
"""The file the CLI reads to see a plugin. Nothing else may sit at the view's top level but the
three content folders."""
CONTENT: Final = ("skills", "agents", "commands")
MANIFEST: Final = "plugin.manifest.json"
"""The core plugin's checked-in manifest, in place of the old single hash constant."""
INDEX: Final = "views.json"
LIBRARY_SKILLS: Final = "library-skills"
"""The one view that aggregates published Library skills belonging to no pack."""
NEVER_WRITTEN: Final = ("hooks", ".mcp.json")
"""What a pack may ship and a view may not: a hook runs outside every guard and an MCP server
starts its own process per chat (AD-55)."""


def digest(files: Iterable[tuple[str, bytes]]) -> str:
    """sha256 over each file's relative path and its bytes, CRLF read as LF, so a Windows
    checkout hashes as the commit does."""
    total = hashlib.sha256()
    for name, body in sorted(files):
        total.update(name.encode() + b"\0" + body.replace(b"\r\n", b"\n"))
    return total.hexdigest()


def folder_digest(folder: Path) -> str:
    """`digest` over every file under `folder`, by its posix path relative to it."""
    return digest(
        (path.relative_to(folder).as_posix(), path.read_bytes())
        for path in folder.rglob("*")
        if path.is_file()
    )


CORE: Final = "qmx"
"""The name the CLI knows QMX's own plugin by."""


def manifest(folder: Path) -> dict[str, Any]:
    """The core plugin's manifest: every file it ships with its sha256, and one digest over
    them. The manifest file cannot hash itself, so it is the one path left out."""
    files = {
        path.relative_to(folder).as_posix(): "sha256:"
        + hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for path in folder.rglob("*")
        if path.is_file() and path.relative_to(folder).as_posix() != MANIFEST
    }
    return {
        "plugin": CORE,
        "generated": (
            'uv run --no-sync python -c "from qma.harness.home import PLUGIN_DIR; '
            'from qma.harness.packs import write_manifest; write_manifest(PLUGIN_DIR)"'
        ),
        "sha256": digest((name, (folder / name).read_bytes()) for name in files),
        "files": dict(sorted(files.items())),
    }


def manifest_text(folder: Path) -> str:
    return json.dumps(manifest(folder), indent=2) + "\n"


def write_manifest(folder: Path) -> Path:
    """Write `folder`'s manifest from what it holds. The build step that keeps it current."""
    path = folder / MANIFEST
    path.write_text(manifest_text(folder), encoding="utf-8")
    return path


def manifest_refusal(folder: Path) -> str | None:
    """Why this launch may not load `folder` against its manifest, or None. Names the files that
    differ, so a change in the shipped plugin is one doctor line and one name."""
    path = folder / MANIFEST
    try:
        found = cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))
    except OSError:
        return f"the QMX plugin at {folder} has no {MANIFEST}; restore it from git"
    except ValueError as error:
        return f"the QMX plugin's {MANIFEST} does not parse ({error})"
    listed = cast("Mapping[str, str]", found.get("files") or {})
    actual = {
        item.relative_to(folder).as_posix(): (
            "sha256:" + hashlib.sha256(item.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        )
        for item in folder.rglob("*")
        if item.is_file() and item.relative_to(folder).as_posix() != MANIFEST
    }
    changed = sorted(name for name, sha in listed.items() if actual.get(name) != sha)
    added = sorted(set(actual) - set(listed))
    if changed or added:
        names = ", ".join([*changed, *(f"{name} (new)" for name in added)])
        return f"the QMX plugin at {folder} changed since it shipped ({names}); restore it from git"
    if found.get("sha256") != digest((name, (folder / name).read_bytes()) for name in listed):
        return f"the QMX plugin at {folder} does not match its own manifest digest"
    return None


@dataclass(frozen=True, slots=True)
class PackSource:
    """One pack's plugin tree, as published: the Library object ids it came from and its files by
    posix path."""

    name: str
    objects: tuple[str, ...]
    files: Mapping[str, bytes] = field(default_factory=dict[str, bytes])


@dataclass(frozen=True, slots=True)
class View:
    """One materialised plugin view: what was published, where it sits, whether it still holds."""

    name: str
    objects: tuple[str, ...]
    digest: str
    folder: Path
    skills: tuple[str, ...] = ()

    @property
    def manifest(self) -> str:
        """The hash of the member object ids, which is how an aggregating view is checked."""
        return manifest_hash(self.objects)


def kept(files: Mapping[str, bytes]) -> dict[str, bytes]:
    """The part of a pack's tree a view keeps: `plugin.json` and the three content folders.
    `hooks/` and `.mcp.json` are dropped by name, whatever folder they sit in."""
    found: dict[str, bytes] = {}
    for name, body in files.items():
        parts = Path(name).parts
        if not parts or name.startswith("/") or ".." in parts or "\\" in name:
            raise ValueError(f"a pack file name must be relative with forward slashes: {name!r}")
        if parts[0] in NEVER_WRITTEN or any(part in NEVER_WRITTEN for part in parts):
            continue
        if name == PLUGIN_JSON or parts[0] in CONTENT:
            found[name] = body
    return found


def check_tree(name: str, files: Mapping[str, bytes]) -> None:
    """Refuse a tree that is not a plugin a chat could load: no manifest, or one whose `name`
    disagrees with the pack's slug, would load under a name the pack set never names."""
    if PLUGIN_JSON not in files:
        raise ValueError(f"the pack {name!r} has no {PLUGIN_JSON}")
    try:
        found = cast("dict[str, Any]", json.loads(files[PLUGIN_JSON]))
    except ValueError as error:
        raise ValueError(f"the pack {name!r} has an unreadable {PLUGIN_JSON} ({error})") from None
    if found.get("name") != name:
        raise ValueError(
            f"the pack {name!r} publishes a plugin named {found.get('name')!r}; a view's folder "
            "name is the pack's slug, so the two must agree"
        )


def skills_of(files: Mapping[str, bytes]) -> tuple[str, ...]:
    """The skill names a view holds: one folder each, holding a `SKILL.md`."""
    found: set[str] = set()
    for name in files:
        parts = Path(name).parts
        if len(parts) == 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
            found.add(parts[1])
    return tuple(sorted(found))


def bundle_files(bundle: bytes) -> dict[str, bytes]:
    """A pack's `bundle.tar` as its files by posix path. Only regular files: a link or a device
    would let a published pack name a byte of the machine it was materialised on."""
    found: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:*") as tar:
        for member in tar.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"a pack bundle may hold regular files only ({member.name})")
            name = member.name.removeprefix("./")
            handle = tar.extractfile(member)
            if handle is None:
                raise ValueError(f"a pack bundle names a file it does not carry ({name})")
            found[name] = handle.read()
    return found


def source(object_id: str, name: str, blobs: Mapping[str, bytes]) -> PackSource:
    """One pack's `PackSource` from its published Library object: the tree comes from its
    `bundle.tar` blob, which is how a mini app publishes."""
    bundle = blobs.get("bundle.tar")
    if bundle is None:
        raise ValueError(f"the pack {name!r} publishes no bundle.tar")
    return PackSource(name=name, objects=(object_id,), files=bundle_files(bundle))


def _read_index(plugins: Path) -> list[dict[str, Any]]:
    path = plugins / INDEX
    try:
        loaded = cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))
    except OSError, ValueError:
        return []
    rows = loaded.get("views")
    return cast("list[dict[str, Any]]", rows) if isinstance(rows, list) else []


def _write_index(plugins: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path = plugins / INDEX
    staged = path.with_suffix(".json.tmp")
    staged.write_text(json.dumps({"views": list(rows)}, indent=2) + "\n", encoding="utf-8")
    staged.replace(path)


def materialise(plugins: Path, sources: Sequence[PackSource]) -> tuple[View, ...]:
    """Write one view per source under `plugins`, and record what was written. A view is
    replaced whole, so nothing of an earlier version of the same pack survives. Other packs'
    records stay, so materialising one set never drops another."""
    plugins.mkdir(parents=True, exist_ok=True)
    rows = {str(row.get("name")): row for row in _read_index(plugins)}
    written: list[View] = []
    for item in sources:
        files = kept(item.files)
        check_tree(item.name, files)
        folder = plugins / item.name
        shutil.rmtree(folder, ignore_errors=True)
        for name, body in files.items():
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        view = View(
            name=item.name,
            objects=tuple(sorted(item.objects)),
            digest=folder_digest(folder),
            folder=folder,
            skills=skills_of(files),
        )
        rows[item.name] = {
            "name": view.name,
            "objects": list(view.objects),
            "manifest": view.manifest,
            "digest": view.digest,
            "skills": list(view.skills),
        }
        written.append(view)
        log.info("materialised the pack view %s at %s", view.name, view.folder)
    _write_index(plugins, [rows[name] for name in sorted(rows)])
    return tuple(written)


@dataclass(frozen=True, slots=True)
class Survey:
    """The views a chat may load, in the order its set names them, and one `(name, reason)` per
    view left out."""

    views: tuple[View, ...]
    refusals: tuple[tuple[str, str], ...]

    def reason(self, name: str) -> str:
        return next((reason for found, reason in self.refusals if found == name), "")


def survey(plugins: Path, packs: Sequence[str]) -> Survey:
    """The views for `packs` that still hold, plus `library-skills` when it was materialised.
    A view whose folder is gone, whose bytes moved, or whose record names other objects is
    refused by name and left out; the rest load."""
    rows = {str(row.get("name")): row for row in _read_index(plugins)}
    wanted = [*packs, *([] if LIBRARY_SKILLS in packs else [LIBRARY_SKILLS])]
    kept_views: list[View] = []
    refusals: list[tuple[str, str]] = []
    for name in wanted:
        row = rows.get(name)
        if row is None:
            if name != LIBRARY_SKILLS:
                refusals.append((name, f"the pack {name} has no materialised view under {plugins}"))
            continue
        folder = plugins / name
        objects = tuple(str(item) for item in cast("list[object]", row.get("objects") or []))
        view = View(
            name=name,
            objects=objects,
            digest=str(row.get("digest")),
            folder=folder,
            skills=tuple(str(item) for item in cast("list[object]", row.get("skills") or [])),
        )
        reason = refusal(view, recorded=str(row.get("manifest")))
        if reason is not None:
            refusals.append((name, reason))
            continue
        kept_views.append(view)
    return Survey(tuple(kept_views), tuple(refusals))


def refusal(view: View, *, recorded: str | None) -> str | None:
    """Why this view may not be loaded, or None. Both records are checked: the member objects
    the view stands for, and the bytes on disk."""
    if recorded is not None and recorded != view.manifest:
        return f"the pack view {view.name} at {view.folder} no longer stands for its objects"
    if not view.folder.is_dir():
        return f"the pack view {view.name} is missing from {view.folder}"
    found = folder_digest(view.folder)
    if found != view.digest:
        return (
            f"the pack view {view.name} at {view.folder} changed since it was published "
            f"(sha256 {found}, published {view.digest}); publish the pack again"
        )
    return None


def views_in(plugins: Path, packs: Sequence[str]) -> tuple[View, ...]:
    """The verified views for a chat whose pack set is `packs`."""
    return survey(plugins, packs).views


def names(plugins: Path) -> tuple[str, ...]:
    """Every view this home has a record for, so the doctor can report each one."""
    return tuple(sorted(str(row.get("name")) for row in _read_index(plugins)))


def manifest_hash(objects: Sequence[str]) -> str:
    """The `library-skills` view's integrity record: one hash over its member object ids."""
    return hashlib.sha256("\n".join(sorted(objects)).encode()).hexdigest()
