"""Regression test for check_chain.py: each fixture passes, or fails on the named check.

Run: python tests/test_check_chain.py  (from standing/funnel). Exit 1 on any mismatch.
Fixtures came from the 12 November stress test of the planning funnel; each changes one
thing in v00-baseline.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE.parent / "check_chain.py"

EXPECTED = {
    "v00-baseline": None,
    "v02-after-stage4": None,  # light depth, no technical decision: stage 5 may be skipped
    "v04-indented-fact": "ground-facts",
    "v05-decision-D1a": "decision-file-name-D1a-split.md",
    "v06-digit-prefix": None,
    "v07-backtick-id": None,
    "v08-semantically-wrong": "anneal-nothing-dissolved",
    "v10-dangling-open-D": "scope-D9-has-file",
    "v11-open-fable-at-handoff": "decision-D3-fable-open",
    "v12-plan-trailing-dot": "plan-line-shape",
    "v14-pipe-in-gap": "anneal-question-row-shape",
    "v15-dup-round": "anneal-round-numbers-increase",
    "v16-ask-from-agent-note": "ask-S1-quoted-and-sourced-in-his-words",
    "v17-two-word-quote": None,
    "v18-template-placeholder-X": "scope-no-placeholders",
    "v19-mind-change-after-stage5-global-numbering": None,
    "v20-lanes-share-a-file": "lanes-tf-01-tf-02-share-no-files",
    "v21-growth-without-reason": "growth-justified",
    "v22-growth-with-reason": None,  # two checkpoints; B can be built while A is reviewed
    "v23-trace-wrong-ask": "brief-tf-01-trace-line",
}


def main() -> int:
    bad = 0
    for name, failing in EXPECTED.items():
        out = subprocess.run(
            [sys.executable, str(CHECK), str(HERE / "fixtures" / name), "--stage", "handoff"],
            capture_output=True, text=True,
        ).stdout
        fails = [ln.split(":")[0][5:] for ln in out.splitlines() if ln.startswith("FAIL ")]
        ok = (not fails) if failing is None else (failing in fails)
        bad += not ok
        print(f"{'ok  ' if ok else 'BAD '} {name}: expected {failing or 'PASS'}, got {fails[:3] or 'PASS'}")
    print(f"\n{len(EXPECTED) - bad}/{len(EXPECTED)} fixtures as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
