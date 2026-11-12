import datetime as dt
import unittest

from ship import state as st
from ship.run_report import build
from ship.settings import Settings
from ship.state import Status
from ship.tests.fixture import RepoCase, write

DAY = "2026-11-12T"


def ev(hhmm, kind, sid=None, **detail):
    return {"at": f"{DAY}{hhmm}:00+00:00", "kind": kind, "slice": sid, **detail}


def move(hhmm, sid, a, b, **detail):
    return ev(hhmm, "status", sid, **{"from": a, "to": b, "reason": ""}, **detail)


class RunReport(RepoCase):
    def night(self):
        with st.locked(self.program) as state:
            state.slices["s3"].depends_on = ["s2"]
            state.events = [
                ev("00:00", "init"),
                move("00:00", "s1", "pending", "held"),
                move("00:30", "s1", "held", "ready"),
                move("00:40", "s1", "ready", "checked"),
                move("00:50", "s1", "checked", "landed"),
                move("01:00", "s2", "pending", "held"),
                ev("01:10", "hold", reason="battery"),
                move("01:20", "s2", "held", "dead"),
                ev("01:50", "clear"),
                move("02:00", "s2", "dead", "held"),
                move("02:30", "s2", "held", "parked", cause="rounds"),
                move("02:30", "s3", "pending", "blocked-by"),
                move("02:30", "s4", "pending", "blocked-by"),
            ]
            for sid, status in (("s1", Status.LANDED), ("s2", Status.PARKED), ("s3", Status.BLOCKED_BY),
                                ("s4", Status.BLOCKED_BY)):
                state.slices[sid].status = status
            state.slices["s1"].landed_sha = "1234567890" * 4
        checks = self.program.checks("s1", "abcdef1234")
        write(checks / "summary.txt", "PASS test-root s1 abcdef12\nFAIL diff-check s1 abcdef12\n"
                                      "NOTRUN linux s1 abcdef12 later\n")
        write(checks / "diff-check.log", "pkg/a.py:1: trailing whitespace.\nFAIL diff-check s1 abcdef12\n")

    def test_report_from_state_and_checks(self):
        self.night()
        ok, text = build(self.program, Settings(), now=dt.datetime.fromisoformat(f"{DAY}03:00:00+00:00"))
        self.assertTrue(ok)
        self.assertIn("- total: 4 slices; the counts add up", text)
        self.assertIn("| s2 | Subtract | parked |", text)
        self.assertIn("## FAIL lines (1)\n\n- `FAIL diff-check s1 abcdef12` (checks", text)
        self.assertIn("- `NOTRUN linux s1 abcdef12 later`", text)
        self.assertIn("- slice_checks never ran for s2", text)
        self.assertIn(
            "## Idle time: 1.2 hours (no seat held while work remained)\n\n"
            f"- {DAY}00:30+00:00 to {DAY}01:00+00:00 (30 min): no dispatch while ['s2'] could start\n"
            f"- {DAY}01:20+00:00 to {DAY}01:50+00:00 (30 min): power hold\n"
            f"- {DAY}01:50+00:00 to {DAY}02:00+00:00 (10 min): no seat held; slices between build and landing: ['s2']\n",
            text)

    def test_status_without_its_event_does_not_add_up(self):
        self.night()
        with st.locked(self.program) as state:
            state.slices["s1"].status = Status.CHECKED
        ok, text = build(self.program, Settings())
        self.assertFalse(ok)
        self.assertIn("the counts DO NOT add up", text)


if __name__ == "__main__":
    unittest.main()
