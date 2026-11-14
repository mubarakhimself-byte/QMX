import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ship import program as prog
from ship import state as st
from ship.layout import Program
from ship.phase import WORDS, read, set_phase
from ship.settings import Settings
from ship.tests.fixture import sign_gates, write

TOOLS = Path(__file__).resolve().parents[2]
PARENT_TIP = "a" * 40
TIP_A, TIP_B, FIX_TIP = "b" * 40, "c" * 40, "d" * 40
END_A = "e" * 40

EXAMPLE = """\
project: qmx
program: pod-scalping
kind: feature                # feature | audit | sweep | fix | wire
parent: null                 # the program this one fixes or serves, or null
area: [qml/src/qml/pod, qmn/src/qmn/app]
inputs:
  audit: null
  backlog: [B-12, B-40]
  ui_asks: []
build_branch: build/pod-scalping
parent_tip: 3ae41ffcb2b7dcaf934063f1682ed330efe969cb
core_sentence: "A scalping book with its numbers filled in can run one unit on demo."
budget:
  core: 3
  later: 2
  checkpoints: 1
  raised: []
gates:
  cut: {by: him, at: 2026-11-14, source: "dd8f4ab2:L7001", advance: no}
  plan: {by: him, at: 2026-11-14, source: "dd8f4ab2:L7240", advance: yes}
  go: null
stop_points:
  - id: A
    tier: core
    done_when: "the scalping book trades one unit on the demo account"
    handoff: ready
  - id: B
    tier: later
    done_when: "house-money sizing can be switched on"
    handoff: deferred
chains:
  - ask: S1
    verdict: core
    plan: [S1.a, S1.b]
    arch: [A1]
    interfaces: [I1]
    slices: [ps-01, ps-02, ps-03]
    edge_cases: [E1, E2]
    intent: []
    findings: []
abandoned: null
"""

SLICES_AB = """\
| id | name | stop | depends on | files | size |
|---|---|---|---|---|---|
| p-01 | One | A | - | pkg/a.py | S |
| p-02 | Two | B | - | pkg/b.py | S |
"""


def program_yaml(kind="feature", go="null", plan_advance="yes", b_handoff="ready", abandoned="null",
                 parent="null", stops=("A", "B")):
    gates = {
        "feature": f"  cut: null\n  plan: {{by: him, at: 2026-11-14, source: \"s:L1\", advance: {plan_advance}}}\n  go: {go}\n",
        "audit": f"  intent: null\n  verdicts: {{by: him, at: 2026-11-14, source: \"s:L2\", advance: {plan_advance}}}\n  go: {go}\n",
        "sweep": f"  go: {go}\n",
        "fix": f"  go: {go}\n",
    }[kind]
    stop_rows = ""
    for sid in stops:
        handoff = b_handoff if sid == "B" else "ready"
        stop_rows += f"  - id: {sid}\n    tier: core\n    done_when: \"stop {sid}\"\n    handoff: {handoff}\n"
    return (f"project: qmx\nprogram: p\nkind: {kind}\nparent: {parent}\narea: [pkg]\nbuild_branch: build/p\n"
            f"parent_tip: {PARENT_TIP}\ngates:\n{gates}stop_points:\n{stop_rows}abandoned: {abandoned}\n")


GO = '{by: him, at: 2026-11-14, source: "s:L9", advance: yes}'


class PhaseCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.plans = Path(self._tmp.name)
        self.settings = Settings()

    def tearDown(self):
        self._tmp.cleanup()

    def folder(self, name="p", yaml=None, slices=SLICES_AB, review=None, state=False, merged=(), **kw):
        p = Program(self.plans / name)
        p.dir.mkdir(parents=True, exist_ok=True)
        if yaml is not False:
            write(p.project_file, yaml if yaml is not None else program_yaml(**kw))
            try:
                sign_gates(p)  # as `ship gate` would have logged them
            except prog.ProgramError:
                pass  # a test of a broken PROGRAM.yaml
        if slices:
            write(p.slices_md, slices)
        if review:
            write(p.dir / "plan-review" / "REVIEW.md", f"# review\n\nRESULT: {review}\nEND plan-review {PARENT_TIP}\n")
        if state:
            sl = {"p-01": st.Slice("p-01", "One", [], ["pkg/a.py"], checkpoint="A"),
                  "p-02": st.Slice("p-02", "Two", [], ["pkg/b.py"], checkpoint="B")}
            st.save(p, st.State(repo="r", build_branch="build/p", remote="origin", worktree_root="w", slices=sl,
                                merged=list(merged)))
        return p

    def armed(self, name="p", merged=(), **kw):
        return self.folder(name, review="CLEAN", state=True, merged=merged, go=GO, **kw)

    def built(self, p, stop, tip):
        write(p.stop_note(stop), json.dumps({"stop": stop, "from": PARENT_TIP, "tip": tip, "landed": ["p-01"],
                                              "parked": [], "at": "2026-11-14T00:00:00+00:00"}))

    def verdict(self, p, stop, name, word, end):
        write(p.stop_review(stop) / name, f"# review\n\nVERDICT: {word}\n\nEND {end} checkpoint-{stop}-round-1\n")

    def read(self, p):
        return read(p, self.settings)

    def pick(self, got, *keys):
        return {k: got.get(k) for k in keys}


class Rules(PhaseCase):
    def test_rule_01_no_program_yaml_is_intake(self):
        got = self.read(self.folder(yaml=False, slices=None))
        self.assertEqual(self.pick(got, "next", "status", "conveyor"),
                         {"next": "intake", "status": "idle", "conveyor": "none"})

    def test_rule_02_abandoned_is_done(self):
        got = self.read(self.armed(abandoned='"he dropped it"'))
        self.assertEqual(self.pick(got, "next", "status", "why"),
                         {"next": "done", "status": "abandoned", "why": "abandoned: he dropped it"})

    def test_rule_03_no_slices_feature_is_plan_with_stage(self):
        p = self.folder(slices=None)
        set_phase(p, "ground", "running", "planner")
        self.assertEqual(self.pick(self.read(p), "next", "stage", "kind"),
                         {"next": "plan", "stage": "ground", "kind": "feature"})

    def test_rule_04_no_slices_audit_is_audit_with_stage(self):
        p = self.folder(slices=None, kind="audit")
        set_phase(p, "intent-check", "waits", "audit-intent")
        self.assertEqual(self.pick(self.read(p), "next", "stage"), {"next": "audit", "stage": "intent-check"})

    def test_rule_05_no_slices_sweep_is_sweep_handoff(self):
        self.assertEqual(self.read(self.folder(slices=None, kind="sweep"))["next"], "sweep-handoff")

    def test_rule_06_no_go_no_review_is_review(self):
        self.assertEqual(self.pick(self.read(self.folder()), "next", "status"), {"next": "review", "status": "idle"})

    def test_rule_07_review_fixes_is_planner_fix(self):
        self.assertEqual(self.read(self.folder(review="FIXES"))["next"], "planner-fix")

    def test_rule_08_clean_and_advance_yes_is_go_for_the_conveyor(self):
        got = self.read(self.folder(review="CLEAN", plan_advance="yes"))
        self.assertEqual(self.pick(got, "next", "status"), {"next": "go", "status": "idle"})

    def test_rule_09_otherwise_go_waits_on_him(self):
        for review, advance in (("CLEAN", "no"), ("QUESTIONS", "yes")):
            got = self.read(self.folder(name=f"p-{review}", review=review, plan_advance=advance))
            self.assertEqual(self.pick(got, "next", "status"), {"next": "go", "status": "waits-on-him"}, review)

    def test_rule_10_no_state_is_arm(self):
        self.assertEqual(self.read(self.folder(review="CLEAN", go=GO))["next"], "arm")

    def test_rule_11_deferred_stop_with_no_slice_is_later_handoff(self):
        only_a = "| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n| p-01 | One | A | - | pkg/a.py | S |\n"
        p = self.armed(slices=only_a, merged=["A"], b_handoff="deferred")
        self.assertEqual(self.pick(self.read(p), "next", "stop"), {"next": "later-handoff", "stop": "B"})

    def test_rule_12_not_built_is_build(self):
        got = self.read(self.armed())
        self.assertEqual(self.pick(got, "next", "stop", "status"), {"next": "build", "stop": "A", "status": "idle"})

    def test_rule_13_empty_merge_goes_on_to_the_next_stop(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        write(p.merge_note("A"), "EMPTY every slice parked\n")
        self.assertEqual(self.pick(self.read(p), "next", "stop"), {"next": "build", "stop": "B"})

    def test_rule_14_built_not_reviewed_is_checkpoint_review_round_1(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.assertEqual(self.pick(self.read(p), "next", "stop", "round", "from", "tip"),
                         {"next": "checkpoint-review", "stop": "A", "round": "1", "from": PARENT_TIP, "tip": TIP_A})

    def test_rule_15_blocked_and_fix_not_built_is_build_in_the_fix_folder(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "BLOCKED", TIP_A)
        got = self.read(p)
        fix = (self.plans / "p-fix-A").as_posix()
        self.assertEqual(self.pick(got, "next", "stop", "build_folder"),
                         {"next": "build", "stop": "A", "build_folder": fix})

    def test_rule_16_fix_built_is_checkpoint_review_round_2(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "BLOCKED", TIP_A)
        self.built(Program(self.plans / "p-fix-A"), "A", FIX_TIP)
        got = self.read(p)
        self.assertEqual(self.pick(got, "next", "round", "tip", "fix_program", "from"),
                         {"next": "checkpoint-review", "round": "2", "tip": FIX_TIP,
                          "fix_program": (self.plans / "p-fix-A").as_posix(), "from": PARENT_TIP})

    def test_rule_17_blocked_after_round_2_waits(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "BLOCKED", TIP_A)
        self.built(Program(self.plans / "p-fix-A"), "A", FIX_TIP)
        self.verdict(p, "A", "REVIEW-2.md", "BLOCKED", FIX_TIP)
        self.assertEqual(self.pick(self.read(p), "next", "status"), {"next": "waits", "status": "waits-on-him"})

    def test_rule_18_clean_is_merge(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "CLEAN", END_A)
        self.assertEqual(self.pick(self.read(p), "next", "stop", "reviewed_tip"),
                         {"next": "merge", "stop": "A", "reviewed_tip": END_A})
        self.verdict(p, "A", "REVIEW.md", "BLOCKED", TIP_A)
        self.built(Program(self.plans / "p-fix-A"), "A", FIX_TIP)
        self.verdict(p, "A", "REVIEW-2.md", "CLEAN", FIX_TIP)
        self.assertEqual(self.pick(self.read(p), "next", "reviewed_tip"), {"next": "merge", "reviewed_tip": FIX_TIP})

    def test_rule_19_merged_without_docs_is_docs(self):
        p = self.armed(merged=["A", "B"])
        write(p.dir / "docs" / "A.json", "{}\n")
        self.assertEqual(self.pick(self.read(p), "next", "stop"), {"next": "docs", "stop": "B"})

    def test_rule_20_every_stop_merged_is_done(self):
        p = self.armed(merged=["A", "B"])
        for sid in ("A", "B"):
            write(p.dir / "docs" / f"{sid}.json", "{}\n")
        self.assertEqual(self.pick(self.read(p), "next", "status"), {"next": "done", "status": "done"})


class Cases(PhaseCase):
    def test_fix_folder_with_no_go_gate_routes_to_build_never_review(self):
        self.armed()
        fix = self.folder("p-fix-A", yaml=program_yaml(kind="fix", parent="p", stops=("A",)), state=True)
        got = self.read(fix)
        self.assertEqual(self.pick(got, "next", "stop", "kind", "parent"),
                         {"next": "build", "stop": "A", "kind": "fix", "parent": (self.plans / "p").as_posix()})

    def test_built_fix_folder_reads_its_parents_round_2(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "BLOCKED", TIP_A)
        fix = self.folder("p-fix-A", yaml=program_yaml(kind="fix", parent="p", stops=("A",)), state=True)
        self.built(fix, "A", FIX_TIP)
        self.assertEqual(self.pick(self.read(fix), "next", "round", "tip"),
                         {"next": "checkpoint-review", "round": "2", "tip": FIX_TIP})

    def test_live_chain_lock_reads_running(self):
        p = self.armed()
        self.built(p, "A", TIP_A)
        write(p.chain_lock, json.dumps({"pid": os.getpid(), "started": "x", "program": "p", "step": "checkpoint",
                                        "children": []}))
        got = self.read(p)
        self.assertEqual(self.pick(got, "next", "status", "conveyor"),
                         {"next": "checkpoint-review", "status": "running", "conveyor": f"alive {os.getpid()}"})

    def test_dead_chain_lock_reads_idle(self):
        p = self.armed()
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        write(p.chain_lock, json.dumps({"pid": dead.pid}))
        self.assertEqual(self.pick(self.read(p), "status", "conveyor"),
                         {"status": "idle", "conveyor": f"dead {dead.pid}"})

    def test_unanswered_question_waits_and_an_answered_one_does_not(self):
        p = self.armed()
        write(p.waits, "# Waits\n\n- [ ] Which account?\n")
        got = self.read(p)
        self.assertEqual(self.pick(got, "next", "status", "waits"),
                         {"next": "build", "status": "waits-on-him", "waits": p.waits.as_posix()})
        write(p.waits, "# Waits\n\n- [x] Which account? :: \"the demo one\" (dd8f4ab2:L9)\n")
        self.assertEqual(self.pick(self.read(p), "status", "waits"), {"status": "idle", "waits": None})

    def test_from_for_stop_b_is_stop_a_reviewed_tip_not_the_target(self):
        p = self.armed(merged=["A"])
        self.built(p, "A", TIP_A)
        self.verdict(p, "A", "REVIEW.md", "CLEAN", END_A)
        write(p.merge_note("A"), f"MERGED {'f' * 40}\n")
        self.built(p, "B", TIP_B)
        self.assertEqual(self.pick(self.read(p), "next", "stop", "from", "tip"),
                         {"next": "checkpoint-review", "stop": "B", "from": END_A, "tip": TIP_B})

    def test_a_file_outside_the_subset_waits_with_its_line(self):
        got = self.read(self.folder(yaml="project: qmx\nkind: feature\ncore_sentence: |\n  two\n"))
        self.assertEqual(self.pick(got, "next", "status"), {"next": "waits", "status": "waits-on-him"})
        self.assertTrue(got["why"].startswith("PROGRAM.yaml line 3: multi-line strings"), got["why"])

    def test_version_1_fixture_loads_through_legacy(self):
        v1 = (f"program: old\nrepo: C:/x\nbuild_branch: build/old\nparent_tip: {PARENT_TIP}\n"
              "target_branch: engine/base\nscope_gate: {by: him, at: 2026-11-10, where: s1}   # PLAN-REVIEW\n\n"
              "stop_points:\n  - id: A\n    done_when: <one line>\n    merged: null\n\nfiles:\n"
              "  - path: SCOPE.md\n    serves: [planner]\n")
        index = prog.legacy(v1)
        self.assertEqual((index.version, index.kind, index.program, index.parent_tip),
                         (1, "feature", "old", PARENT_TIP))
        self.assertEqual(index.gate("go"), {"by": "him", "at": "2026-11-10", "where": "s1"})
        self.assertEqual([(s.id, s.merged) for s in index.stops], [("A", None)])
        p = self.folder("old-fix-A", yaml=v1.replace("scope_gate: {by: him, at: 2026-11-10, where: s1}", "scope_gate: null"),
                        state=True)
        loaded = prog.load(p)
        self.assertEqual((loaded.kind, loaded.parent, loaded.gate("go")), ("fix", "old", None))
        self.assertEqual(self.pick(self.read(p), "next", "stop"), {"next": "build", "stop": "A"})


class Parser(PhaseCase):
    def test_parse_reads_the_example(self):
        raw = prog.parse(EXAMPLE)
        self.assertEqual(raw["area"], ["qml/src/qml/pod", "qmn/src/qmn/app"])
        self.assertEqual(raw["inputs"], {"audit": None, "backlog": ["B-12", "B-40"], "ui_asks": []})
        self.assertEqual(raw["budget"], {"core": 3, "later": 2, "checkpoints": 1, "raised": []})
        self.assertEqual(raw["gates"]["cut"], {"by": "him", "at": "2026-11-14", "source": "dd8f4ab2:L7001", "advance": False})
        self.assertIsNone(raw["gates"]["go"])
        self.assertEqual(raw["core_sentence"], "A scalping book with its numbers filled in can run one unit on demo.")
        self.assertEqual(raw["chains"][0]["slices"], ["ps-01", "ps-02", "ps-03"])
        index = prog.from_dict(raw)
        self.assertEqual([(s.id, s.handoff) for s in index.stops], [("A", "ready"), ("B", "deferred")])
        self.assertEqual((index.kind, index.last_gate_before_go(), index.gate("plan")["advance"]), ("feature", "plan", True))

    def test_parse_rejects_a_tab_and_a_multi_line_string_with_the_line_number(self):
        with self.assertRaises(prog.ProgramError) as tab:
            prog.parse("project: qmx\nbudget:\n\tcore: 3\n")
        self.assertEqual(tab.exception.line_no, 3)
        for text, line in (("project: qmx\ncore_sentence: |\n  two\n  lines\n", 2),
                           ("project: qmx\nkind: feature\ncore_sentence: \"open\n  still open\"\n", 3),
                           ("a: 1\nb: &anchor x\n", 2), ("a: 1\n   b: 2\n", 2)):
            with self.assertRaises(prog.ProgramError) as bad:
                prog.parse(text)
            self.assertEqual(bad.exception.line_no, line, text)

    def test_set_gate_changes_only_the_gates_block(self):
        p = self.folder(yaml=EXAMPLE)
        line = prog.set_gate(p, "go", "him", "dd8f4ab2:L9000", True, at="2026-11-15")
        self.assertEqual(line, 'go: {by: him, at: 2026-11-15, source: "dd8f4ab2:L9000", advance: yes}')
        after = p.project_file.read_text("utf-8")
        self.assertEqual(after, EXAMPLE.replace(
            "  go: null\n", '  go: {by: him, at: 2026-11-15, source: "dd8f4ab2:L9000", advance: yes}\n'))
        self.assertEqual(prog.load(p).gate("go")["source"], "dd8f4ab2:L9000")
        with self.assertRaisesRegex(prog.ProgramError, "kind feature has no gate 'verdicts'"):
            prog.set_gate(p, "verdicts", "him", "x", False)
        self.assertEqual(p.project_file.read_text("utf-8"), after)
        crlf = self.folder("crlf", yaml="")
        crlf.project_file.write_bytes(EXAMPLE.replace("\n", "\r\n").encode("utf-8"))
        prog.set_gate(crlf, "go", "him", "s:L1", False, at="2026-11-15")
        self.assertEqual(crlf.project_file.read_bytes(), EXAMPLE.replace(
            "  go: null\n", '  go: {by: him, at: 2026-11-15, source: "s:L1", advance: no}\n').replace("\n", "\r\n").encode())

    def test_set_gate_adds_a_missing_gate_and_expands_an_inline_block(self):
        p = self.folder(yaml="kind: sweep\ngates: {go: null}\nabandoned: null\n")
        prog.set_gate(p, "go", "stop-review", "stop-review/A/REVIEW.md", True, at="2026-11-15")
        self.assertEqual(p.project_file.read_text("utf-8"),
                         'kind: sweep\ngates:\n'
                         '  go: {by: stop-review, at: 2026-11-15, source: "stop-review/A/REVIEW.md", advance: yes}\n'
                         'abandoned: null\n')
        q = self.folder("q", yaml="kind: audit\ngates:\n  intent: null\n# note\nabandoned: null\n")
        prog.set_gate(q, "verdicts", "him", "s", False, at="2026-11-15")
        self.assertEqual(q.project_file.read_text("utf-8"),
                         'kind: audit\ngates:\n  intent: null\n'
                         '  verdicts: {by: him, at: 2026-11-15, source: "s", advance: no}\n# note\nabandoned: null\n')


class Cli(PhaseCase):
    def ship(self, *args):
        done = subprocess.run([sys.executable, "-m", "ship", *args], cwd=TOOLS, capture_output=True, text=True)
        return done.returncode, done.stdout

    def test_words_all_set_and_gate(self):
        rc, out = self.ship("phase", "--words")
        self.assertEqual((rc, out.split()), (0, list(WORDS)))
        self.armed()
        self.folder("q", slices=None)
        rc, out = self.ship("phase", "--all", "--plans", str(self.plans))
        blocks = [dict(line.split(": ", 1) for line in b.splitlines()) for b in out.strip().split("\n\n")]
        self.assertEqual([(b["folder"], b["next"]) for b in blocks],
                         [((self.plans / "p").as_posix(), "build"), ((self.plans / "q").as_posix(), "plan")])
        rc, out = self.ship("phase", "--program", str(self.plans / "q"), "--set", "expand", "--status", "running",
                            "--by", "planner")
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads((self.plans / "q" / "phase.json").read_text("utf-8"))["phase"], "expand")
        rc, out = self.ship("phase", "--program", str(self.plans / "q"))
        self.assertIn("stage: expand\n", out)
        rc, out = self.ship("gate", "--program", str(self.plans / "q"), "go", "--by", "him", "--source", "s:L1",
                            "--advance")
        self.assertEqual(rc, 0)
        self.assertTrue(prog.load(Program(self.plans / "q")).gate("go")["advance"])
        rc, out = self.ship("gate", "--program", str(self.plans / "q"), "intent", "--by", "him", "--source", "s")
        self.assertEqual((rc, out), (1, "REFUSED PROGRAM.yaml: kind feature has no gate 'intent'; its gates are ['cut', 'plan', 'go']\n"))


if __name__ == "__main__":
    unittest.main()
