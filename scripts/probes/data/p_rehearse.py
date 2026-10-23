"""P-REHEARSE (W3, acceptance): the whole switch-over runs on a copy of his home, and his home
does not change.

The probe copies `~/.qmx` into a scratch root under `TMP` (221 KB on 2026-10-22), hashes every file
of the real home before and after, and runs the same steps `switch_library.py` runs on a copy:

1. Step 0's counts are recorded, then Library B imports into `<copy>/library/` with the known test
   junk filtered by id (fix-check 58, N18).
2. Every count per kind, version chain, link, memo row, blob hash and blob byte equals step 0's
   numbers minus the filtered ids, listed by id.
3. `<copy>/migration/retired/library.db` exists read-only, the copy's own `library.db` is gone, and
   a copilot read of the store answers from `<copy>/library/`.
4. The real home's tree hash is the same before and after.

    uv run --no-sync --project qmx-agents python scripts/probes/data/p_rehearse.py
    uv run --no-sync --project qmx-agents python scripts/probes/data/p_rehearse.py --keep

`--keep` leaves the rehearsed copy for the copilot and app lanes; the coordinator removes it.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
from pathlib import Path

from qmx_control.library import Library
from qmx_engine.ledger import redact
from qmx_library.migrate.from_library_b import switch_over

HOME = Path.home() / ".qmx"


def tree_hash(root: Path) -> str:
    """Every file's relative path, size and bytes, in one hash: the proof the home never moved."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        body = path.read_bytes()
        digest.update(f":{len(body)}:".encode())
        digest.update(hashlib.sha256(body).digest())
    return digest.hexdigest()


def copilot_reads(copy: Path, expected: int) -> list[str]:
    """A read through the door the copilot uses, from the store alone."""
    problems: list[str] = []
    library = Library(copy)
    try:
        found = library.search("", limit=1000)
        if len(found) != expected:
            problems.append(f"the copilot reads {len(found)} items, expected {expected}")
        if found and not str(found[0]["id"]).startswith("fp1:sha256:"):
            problems.append(f"the copilot read {found[0]['id']!r}, not a store object id")
        if any(str(item["ref"]).startswith("artifacts/") is False for item in found):
            problems.append("an item has no artifacts/<sha> ref")
    finally:
        library.close()
    return problems


def rehearse(copy: Path) -> tuple[list[str], dict[str, object]]:
    problems: list[str] = []
    switched = switch_over(copy, redactor=redact)
    report = switched.report()
    if not switched.ok:
        wrong = [row for row in report["verification"] if row["step0"] != row["store"]]
        problems.extend(f"verification: {row}" for row in wrong)
        problems.extend(f"bad blob {b}" for b in switched.verification.bad_blobs)
        problems.extend(f"bad chain {c}" for c in switched.verification.bad_chains)
    if not (copy / "library").is_dir():
        problems.append("no <home>/library/ after the switch-over")
    retired = copy / "migration" / "retired" / "library.db"
    if not retired.is_file():
        problems.append("migration/retired/library.db is missing")
    elif retired.stat().st_mode & 0o222:
        problems.append("migration/retired/library.db is still writable")
    if (copy / "library.db").exists():
        problems.append("library.db is still in the home")
    if sorted(switched.imported.junk) != sorted(report["junk"]):
        problems.append("the report's filtered ids are not the importer's")
    imported = [row for row in report["verification"] if str(row["what"]).startswith("library-b ")]
    problems.extend(copilot_reads(copy, sum(int(row["store"]) for row in imported)))
    return problems, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=HOME, help="the real home, read only")
    parser.add_argument("--scratch", type=Path, default=None, help="where the copy goes")
    parser.add_argument(
        "--keep", action="store_true", help="leave the rehearsed copy for the lanes"
    )
    arguments = parser.parse_args(argv)
    home = arguments.home.expanduser().resolve()
    if not home.is_dir():
        print(f"no home at {home}")
        return 1
    scratch = arguments.scratch or Path(tempfile.mkdtemp(prefix="dr1b-rehearse-", dir=None))
    copy = scratch if scratch.name == "home" else scratch / "home"
    if copy.resolve() == home:
        print("refused: the probe rehearses on a copy, never on the real home")
        return 2
    if copy.exists():
        shutil.rmtree(copy)
    copy.parent.mkdir(parents=True, exist_ok=True)
    before = tree_hash(home)
    shutil.copytree(home, copy)
    problems, report = rehearse(copy)
    after = tree_hash(home)
    if before != after:
        problems.append("his real home changed while the rehearsal ran")
    print(f"home {home} sha256 {before}")
    print(f"copy {copy}")
    print(f"step 0 kinds: {report['step0']['kinds']}")
    print(f"filtered junk ids ({len(report['junk'])}): {', '.join(report['junk'])}")
    for row in report["verification"]:
        print(f"  {row['what']}: step0 {row['step0']} store {row['store']}")
    print(f"retired: {report['retired']}")
    for problem in problems:
        print(f"  {problem}")
    if not arguments.keep:
        shutil.rmtree(copy, ignore_errors=True)
        if copy.parent != home and not any(copy.parent.iterdir()):
            copy.parent.rmdir()
    if problems:
        print("P-REHEARSE FAIL")
        return 1
    print("P-REHEARSE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
