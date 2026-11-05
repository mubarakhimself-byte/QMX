"""Red proof for tools/tests/test_first_real_start.py. The script came before its tests in this PR,
so each test is shown red against a copy of the script with one behaviour taken out, and all of them
against an empty module. Run from the worktree root with its root env."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
SCRIPT = (ROOT / "tools" / "first_real_start.py").read_text("utf-8")
MUTATIONS = {
    "the landed check always passes": (
        'def landed_refusal(source: Path) -> str | None:\n',
        'def landed_refusal(source: Path) -> str | None:\n    return None\n',
    ),
    "the deploy trusts the promote answer": (
        "    if row is None:\n        return False, f\"the node holds no deployment",
        "    if row is None:\n        return True, \"\"\n    if row is None:\n        return False, f\"the node holds no deployment",
    ),
    "the passport's checks are not read": (
        "    if wrong:\n        return False, f\"the passport landed",
        "    if False:\n        return False, f\"the passport landed",
    ),
    "the rows are not looked for": (
        "        rows, month = _rows(world, \"order\")\n        if rows > world.rows_before and month:",
        "        rows, month = 1, \"x\"\n        if rows > world.rows_before and month:",
    ),
    "a rehearsal takes any folder": (
        "    if store.resolve().parent not in home.resolve().parents:",
        "    if False:",
    ),
    "the app's secret skips the key route": (
        "stored = world.host.rest(\"PUT\", f\"/api/keys/{APP_SECRET_KEY}\", body={\"value\": app[1]})",
        "stored = world.host.rest(\"GET\", \"/api/health\")",
    ),
    "the session is never waited for": (
        "        if row.get(\"session\") == \"ready\":\n            world.session = True",
        "        if row.get(\"session\") == \"never\":\n            world.session = True",
    ),
    "a held grant signs in again": (
        "    if row.get(\"session\") in SIGNED_OUT:\n        found = _sign_in(world)",
        "    if True:\n        found = _sign_in(world)",
    ),
    "the bearer is read before the landed check": (
        "        refused = landed_refusal(cast(Path, args.source))\n",
        "        bearer()\n        refused = landed_refusal(cast(Path, args.source))\n",
    ),
}


def run(label: str, text: str) -> int:
    with tempfile.TemporaryDirectory(dir="D:/Temp", prefix="c14-red-") as folder:
        (Path(folder) / "first_real_start.py").write_text(text, "utf-8")
        done = subprocess.run(
            [
                sys.executable, "-m", "pytest", "tools/tests/test_first_real_start.py", "-q", "-n", "0",
                "-p", "no:cacheprovider", "-o", f"pythonpath={folder}", f"--basetemp={folder}/t", "--no-header",
                "--tb=no",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    failed = [line.split("::")[1].split(" ")[0] for line in done.stdout.splitlines() if line.startswith(("FAILED", "ERROR")) and "::" in line]
    last = (done.stdout.strip().splitlines() or [""])[-1]
    print(f"{'RED ' if done.returncode else 'GREEN'} {label}: {last}", flush=True)
    for name in failed:
        print(f"      {name}", flush=True)
    return done.returncode


def main() -> int:
    bad = 0
    for label, (old, new) in MUTATIONS.items():
        if old not in SCRIPT:
            print(f"FAIL the script no longer holds the text for: {label}", flush=True)
            bad += 1
            continue
        bad += run(label, SCRIPT.replace(old, new, 1)) == 0
    bad += run("an empty module", "") == 0
    bad += run("the script as it stands, which must pass", SCRIPT) != 0
    print(f"{'FAIL' if bad else 'PASS'} red proof", flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    shutil.which("git")
    sys.exit(main())
