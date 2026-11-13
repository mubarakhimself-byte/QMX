import dataclasses
import datetime as dt
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from ship import clock
from ship import launch as ln
from ship.layout import Program
from ship.proc import pid_alive
from ship.settings import Settings
from ship.tests.fixture import PY, sh, write

FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"

# The shape `ship spike` recorded from the real CLI (roles/RESULT-SHAPE.md), trimmed to the fields read.
REAL = {"type": "result", "subtype": "success", "is_error": False, "api_error_status": None,
        "result": "DONE refused", "session_id": "3a067e81-64aa-4424-9af6-80dcaeb91b08",
        "modelUsage": {"claude-haiku-5-5": {"inputTokens": 6, "canonicalModel": "claude-haiku-5-5"}},
        "permission_denials": [{"tool_name": "WebFetch", "tool_use_id": "toolu_1",
                                "tool_input": {"url": "https://example.com"}}]}


class LaunchCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self._tmp.name)
        self.program = Program(root / "prog")
        self.program.dir.mkdir()
        self.script = root / "script.json"
        self.settings = dataclasses.replace(Settings(), claude=(PY, str(FAKE_CLAUDE)), factory_home=str(root / "none"),
                                            worker_env_extra=("FAKE_CLAUDE_SCRIPT",))
        self.cwd = root / "wt"
        self.cwd.mkdir()
        sh(self.cwd, "git", "init", "-q", "-b", "main")
        write(self.cwd / "a.txt", "a\n")
        sh(self.cwd, "git", "add", "-A")
        sh(self.cwd, "git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "commit", "-q", "-m", "a")
        self.head = sh(self.cwd, "git", "rev-parse", "HEAD")
        self.role = ln.Role("builder", "claude-opus-5-5", "high", False, 30, ln.ROLES_DIR / "builder.json")
        patcher = mock.patch.dict(os.environ, {"FAKE_CLAUDE_SCRIPT": str(self.script)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self._tmp.cleanup()

    def rules(self, *rules):
        self.script.write_text(json.dumps(list(rules)), "utf-8")

    def run_worker(self, role=None, worker="s1-a1", label="s1"):
        return ln.run(role or self.role, "build it", self.cwd, self.program, worker, self.settings, label=label,
                      poll_s=0.1)

    def log(self):
        return [json.loads(x) for x in (self.program.dir / "fake-claude.log").read_text("utf-8").splitlines()]


class CommandLine(LaunchCase):
    def test_argv_names_model_effort_settings_and_refuses_prompts(self):
        self.rules({"match": "builder: s1", "reply": "DONE x"})
        self.run_worker()
        argv = self.log()[0]["argv"]
        pairs = {argv[i]: argv[i + 1] for i in range(len(argv) - 1) if argv[i].startswith("--")}
        self.assertEqual(pairs["--model"], "claude-opus-5-5")
        self.assertEqual(pairs["--effort"], "high")
        self.assertEqual(Path(pairs["--settings"]), ln.ROLES_DIR / "builder.json")
        self.assertEqual(pairs["--permission-mode"], "dontAsk")
        self.assertEqual(pairs["--permission-prompts"], "none")
        self.assertEqual(pairs["--disallowedTools"], "Agent")
        self.assertEqual(pairs["--output-format"], "json")
        self.assertEqual(pairs["--setting-sources"], "project,local")
        self.assertIn("--strict-mcp-config", argv)
        self.assertNotIn("--mcp-config", argv)
        self.assertEqual(pairs["--name"], "builder: prog s1")
        self.assertEqual(argv[argv.index("-p") + 1], "build it")
        self.assertNotIn("--bare", argv)
        self.assertNotIn("bypassPermissions", argv)
        self.assertEqual((self.program.workers / "s1-a1" / "prompt.md").read_text("utf-8"), "build it")

    def test_agent_tool_role_keeps_the_agent_tool_and_depth_one(self):
        self.rules({"match": "plan-review:", "reply": "DONE x"})
        role = dataclasses.replace(self.role, name="plan-review", agent_tool=True)
        self.run_worker(role=role)
        entry = self.log()[0]
        self.assertNotIn("--disallowedTools", entry["argv"])
        self.assertEqual(entry["env"][ln.DEPTH_VAR], "1")

    def test_env_drops_parent_claude_and_anthropic_variables(self):
        self.rules({"match": "builder:", "reply": "DONE x"})
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test", "CLAUDE_CODE_SESSION_ID": "parent",
                                          "CLAUDECODE": "1", "ANTHROPIC_BASE_URL": "http://proxy",
                                          "OPENAI_API_KEY": "sk-x", "GH_TOKEN": "ghp_x", "MY_SECRET": "x",
                                          "GIT_AUTHOR_NAME": "kept", "UV_CACHE_DIR": "kept"}):
            self.run_worker()
        env, keys = self.log()[0]["env"], set(self.log()[0]["keys"])
        for dropped in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GH_TOKEN", "MY_SECRET", "CLAUDECODE"):
            self.assertNotIn(dropped, keys)
        for kept in ("PATH", "GIT_AUTHOR_NAME", "UV_CACHE_DIR", "FAKE_CLAUDE_SCRIPT", "SHIP_PROGRAM"):
            self.assertIn(kept, keys)
        self.assertEqual(sorted(k for k in env if k.upper().startswith(("CLAUDE", "ANTHROPIC"))), [ln.DEPTH_VAR])
        self.assertEqual(env[ln.DEPTH_VAR], "0")
        self.assertEqual((env["SHIP_PROGRAM"], env["SHIP_ROLE"]), (str(self.program.dir), "builder"))

    def test_roles_table_loads_and_a_profile_overrides_model(self):
        roles = ln.load_roles(self.settings, {"roles": {"builder": {"model": "sonnet", "timeout_s": 1}}})
        self.assertEqual(roles["builder"].model, "sonnet")
        self.assertEqual(roles["builder"].timeout_s, 10800)
        self.assertTrue(roles["plan-review"].agent_tool)
        self.assertEqual(roles["challenger"].fallback, "claude-opus-5-5")
        for role in roles.values():
            body = json.loads(role.settings_file.read_text("utf-8"))
            command = body["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            self.assertIn("hook --program", command)
            self.assertTrue(command.endswith("|| exit 2"), command)
            allow = body["permissions"]["allow"]
            self.assertFalse({"Bash(python *)", "Bash(git *)", "Bash"} & set(allow), role.name)
            self.assertEqual(body["env"][ln.DEPTH_VAR], "1" if role.agent_tool else "0")
            self.assertFalse([t for t in body["permissions"]["allow"] if t.startswith(("WebFetch", "WebSearch", "mcp"))])


class Results(LaunchCase):
    def test_ready_reply_is_ok_with_the_sha(self):
        self.rules({"match": "builder: s1", "steps": [{"write": {"b.txt": "b\n"}}, {"commit": "s1: b"}],
                    "reply": "Work done.\nREADY {head}"})
        got = self.run_worker()
        head = sh(self.cwd, "git", "rev-parse", "HEAD")
        self.assertNotEqual(head, self.head)
        self.assertEqual((got.kind, got.contract, got.value), ("ok", "READY", head))
        saved = json.loads((self.program.workers / "s1-a1" / "result.json").read_text("utf-8"))
        self.assertEqual((saved["kind"], saved["value"]), ("ok", head))
        self.assertEqual(saved["session_id"], self.log()[0]["argv"][self.log()[0]["argv"].index("--session-id") + 1])

    def test_garbage_is_nocontract(self):
        self.rules({"match": "builder:", "kind": "garbage"})
        self.assertEqual(self.run_worker().kind, "nocontract")

    def test_limit_gives_the_reset_time(self):
        self.rules({"match": "builder:", "kind": "limit", "reset": "2026-11-14T05:00:00+00:00"})
        got = self.run_worker()
        self.assertEqual((got.kind, got.limit_reset), ("limit", "2026-11-14T05:00:00+00:00"))

    def test_hang_is_killed_at_the_timeout(self):
        self.rules({"match": "builder:", "kind": "hang"})
        role = dataclasses.replace(self.role, timeout_s=1.5)
        handle = ln.launch(role, "x", self.cwd, self.program, "s1-a1", self.settings, label="s1")
        started = time.monotonic()
        while (got := handle.poll()) is None:
            time.sleep(0.1)
        self.assertEqual(got.kind, "timeout")
        self.assertLess(time.monotonic() - started, 20)
        self.assertFalse(pid_alive(handle.pid))

    def test_crash_is_crash(self):
        self.rules({"match": "builder:", "kind": "crash"})
        got = self.run_worker()
        self.assertEqual((got.kind, got.rc), ("crash", 2))

    def test_fable_role_that_fell_back_says_so(self):
        role = ln.Role("fault-reader", "fable", "high", False, 30, ln.ROLES_DIR / "reader.json", "claude-opus-5-5")
        self.rules({"match": "fault-reader:", "model": "claude-opus-5-5", "reply": "DONE notes.md"})
        got = self.run_worker(role=role)
        self.assertEqual((got.kind, got.fell_back), ("ok", True))
        saved = json.loads((self.program.workers / "s1-a1" / "result.json").read_text("utf-8"))
        self.assertEqual(saved["note"], "FALLBACK fault-reader claude-opus-5-5")
        argv = self.log()[0]["argv"]
        self.assertEqual(argv[argv.index("--fallback-model") + 1], "claude-opus-5-5")

    def test_fable_that_ran_as_fable_did_not_fall_back(self):
        role = ln.Role("challenger", "fable", "high", False, 30, ln.ROLES_DIR / "audit.json", "claude-opus-5-5")
        self.rules({"match": "challenger:", "model": "claude-fable-5", "reply": "DONE c.md"})
        self.assertFalse(self.run_worker(role=role).fell_back)

    def test_rule_times_run_out_and_the_next_rule_applies(self):
        self.rules({"match": "builder: s1", "times": 1, "kind": "garbage"}, {"match": "builder: s1", "reply": "DONE y"})
        self.assertEqual(self.run_worker(worker="w1").kind, "nocontract")
        self.assertEqual(self.run_worker(worker="w2").line, "DONE y")


class Parsing(unittest.TestCase):
    def test_recorded_real_shape_parses(self):
        got = ln.parse_result(json.dumps(REAL), 0)
        self.assertEqual((got.kind, got.line, got.session_id), ("ok", "DONE refused", REAL["session_id"]))
        self.assertEqual((got.models, got.denials), (["claude-haiku-5-5"], ["WebFetch"]))

    def test_contract_is_the_last_non_blank_line(self):
        self.assertEqual(ln.contract_line("READY abc\nthen more words\n"), None)
        self.assertEqual(ln.contract_line("text\n\nBLOCKED chain S1.a wrong\n\n"), ("BLOCKED", "chain S1.a wrong"))
        self.assertEqual(ln.contract_line("WAITS"), None)

    def test_unparsable_output_with_a_limit_phrase_is_a_limit(self):
        got = ln.parse_result("Claude AI usage limit reached|1794632400", 1)
        self.assertEqual((got.kind, got.limit_reset), ("limit", "2026-11-14T05:00:00+00:00"))

    def test_limit_with_no_time_waits_the_backoff(self):
        settings = dataclasses.replace(Settings(), limit_backoff_s=600)
        with tempfile.TemporaryDirectory() as tmp:
            now = Path(tmp) / "now"
            now.write_text("2026-11-14T01:00:00+00:00", "utf-8")
            with mock.patch.dict(os.environ, {"SHIP_FAKE_NOW": str(now)}):
                got = ln.parse_result(json.dumps({**REAL, "is_error": True, "result": "You hit a rate limit."}), 1,
                                      settings)
        self.assertEqual((got.kind, got.limit_reset), ("limit", "2026-11-14T01:10:00+00:00"))

    def test_nonzero_exit_without_contract_is_a_crash(self):
        self.assertEqual(ln.parse_result(json.dumps({**REAL, "result": "oops"}), 3).kind, "crash")
        self.assertEqual(ln.parse_result("", 0).kind, "crash")


class Clock(unittest.TestCase):
    def test_follows_ship_fake_now(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "now"
            path.write_text("2030-01-02T03:04:05+00:00\n", "utf-8")
            with mock.patch.dict(os.environ, {"SHIP_FAKE_NOW": str(path)}):
                self.assertEqual(clock.now().isoformat(), "2030-01-02T03:04:05+00:00")
                path.write_text("2030-01-02T04:00:00", "utf-8")
                self.assertEqual(clock.now().isoformat(), "2030-01-02T04:00:00+00:00")
        with mock.patch.dict(os.environ, {"SHIP_FAKE_NOW": ""}):
            self.assertLess(abs((clock.now() - dt.datetime.now(dt.timezone.utc)).total_seconds()), 5)


class LimitsNeedAnError(unittest.TestCase):
    def test_a_normal_end_that_mentions_a_rate_limit_is_not_a_limit(self):
        text = "I added retries for the rate limit and the usage limit of the broker API. All tests pass."
        got = ln.parse_result(json.dumps({**REAL, "result": text}), 0)
        self.assertEqual((got.kind, got.limit_reset), ("nocontract", None))
        self.assertEqual(ln.parse_result("hit the usage limit", 0).kind, "crash")

    def test_the_pattern_with_an_error_is_a_limit(self):
        got = ln.parse_result(json.dumps({**REAL, "is_error": True, "result": "Claude usage limit reached|1794632400"}), 0)
        self.assertEqual((got.kind, got.limit_reset), ("limit", "2026-11-14T05:00:00+00:00"))


if __name__ == "__main__":
    unittest.main()
