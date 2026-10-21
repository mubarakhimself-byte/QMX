"""A pinned app bundle, fetched by hash and started lazily on the machine that calls it.

AD-64 runs a `state: none` operation on the caller's machine, so a machine holding no copy of the
app starts it there from the bundle its pin names. An app's image is addressed by its content hash
and kept at `<home>/definitions/<hash>` on every machine, which makes a fetch a verified copy from
another store's `definitions/` folder and a second fetch of the same hash a no-op.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from qmx_apps.errors import AppError
from qmx_apps.manifest import Trust, image_hash

if TYPE_CHECKING:
    from qmx_apps.errors import Document
    from qmx_apps.supervisor import Supervisor


def image(home: Path, definition_hash: str) -> Path:
    """Where one definition's immutable image lives on this machine."""
    return home.resolve() / "definitions" / definition_hash


def present(home: Path, definition_hash: str) -> bool:
    """Whether this machine already holds `definition_hash`, checked against its content now."""
    root = image(home, definition_hash)
    return root.is_dir() and image_hash(root) == definition_hash


def installed(supervisor: Supervisor, app_id: str) -> set[str]:
    """Every definition hash this machine has installed for `app_id`."""
    try:
        return {str(row["definition_hash"]) for row in supervisor.versions(app_id)}
    except AppError:
        return set()


def fetch(home: Path, definition_hash: str, sources: Iterable[Path]) -> Path:
    """The verified image for `definition_hash`, copied here from the first source that holds it.
    A source is a `definitions/` folder or one image folder inside one. The copy is staged and
    re-hashed, so a truncated or edited bundle is refused rather than installed."""
    target = image(home, definition_hash)
    if present(home, definition_hash):
        return target
    for source in sources:
        root = Path(source)
        folder = root if root.name == definition_hash else root / definition_hash
        if not folder.is_dir():
            continue
        if image_hash(folder) != definition_hash:
            raise AppError("bundle_corrupt", f"{folder} is not the bundle {definition_hash}.", 409)
        staged = target.with_name(f"{definition_hash}.fetch")
        shutil.rmtree(staged, ignore_errors=True)
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(folder, staged)
        if image_hash(staged) != definition_hash:
            shutil.rmtree(staged, ignore_errors=True)
            raise AppError("bundle_corrupt", f"the copy of {definition_hash} did not verify.", 409)
        shutil.rmtree(target, ignore_errors=True)
        staged.replace(target)
        return target
    raise AppError(
        "bundle_missing",
        f"No source holds the bundle {definition_hash}; give it a store's definitions folder.",
        404,
    )


def start(
    supervisor: Supervisor,
    app_id: str,
    *,
    definition_hash: str,
    sources: Iterable[Path] = (),
    profile: str | None = None,
    trust: Trust = "reviewed",
) -> Document:
    """Start `app_id` on this machine from the bundle `definition_hash` pins, or answer the
    instance that is already running. This is the `state: none` path: the call brings the app's
    server up on whichever machine made it, and a bundle fetched from another store is installed
    under its own hash before it runs, so the pin is what executes."""
    known = installed(supervisor, app_id)
    if definition_hash in known:
        status = supervisor.status(app_id)
        if status.get("status") == "running":
            return status
    folder = fetch(supervisor.home, definition_hash, sources)
    if definition_hash not in known:
        supervisor.install(folder, trust=trust, expected_id=app_id, expected_hash=definition_hash)
    return supervisor.start(app_id, definition_hash=definition_hash, profile=profile)
