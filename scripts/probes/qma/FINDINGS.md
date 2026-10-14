# HP0 findings

Each row is one question from HARNESS-PLAN HP0. Evidence logs live in `D:/QMX-worktrees/qma-ship/evidence/hp0/`.

Run every probe with the probe venv's Python, `D:/QMX-worktrees/qma-ship/probe-venv/Scripts/python.exe`, which `p_install.py` builds. A probe that needs a plan turn stops with `BLOCKED` until `p_login.py` has signed the ship home in.

| Question | Probe | Observed | Verdict | Feeds |
| --- | --- | --- | --- | --- |
| S1. Newest SDK with a `win_amd64` wheel and a bundled CLI at 2.1.248 or later | `p_install.py` | `claude-agent-sdk==0.2.166`, wheel `py3-none-win_amd64`, bundled CLI `2.1.299 (Claude Code)` | PASS | every later PR's pin |
| S2, OQ6. Auth method string of a Max login, and `/login` offers no Console choice | `p_login.py` | not run: the ship home has no plan login yet | BLOCKED | HP4 `_connect` login check |
| S19. A Bash call under `reduced_env()`, then a fake `ANTHROPIC_API_KEY` in the parent env | `p_env.py` | not run: the ship home has no plan login yet | BLOCKED | HP2 boot scrub |
| S20, OQ3 to OQ5. Inline settings, ConfigChange, a planted plugin, argv length, `append-system-prompt-file` | `p_settings.py` | not run: the ship home has no plan login yet | BLOCKED | HP4 `code_settings`, `assert_argv_fits` |
| S10. `/usage` reaches Python | `p_sdk.py usage` | not run: the ship home has no plan login yet | BLOCKED | HP10 usage ledger |
| S37. `/effort high` changes the next request | `p_sdk.py effort` | not run: the ship home has no plan login yet | BLOCKED | HP6 `classify_change` |
| S38. A PreToolUse callback sleeping past `HookMatcher.timeout` blocks Bash in bypass mode | `p_sdk.py timeout` | not run: the ship home has no plan login yet | BLOCKED | HP8 gate timeout |
| S25. `verbatim_prompts=True` stops `/compact` dispatch | `p_sdk.py verbatim` | not run: the ship home has no plan login yet | BLOCKED | HP7 untrusted input |
| S18. Working set of one idle and one busy CLI | `p_ram.py` | not run: the ship home has no plan login yet | BLOCKED | HP4 memory caps, OQ11 |
| Shim. A uv console-script `.exe` as `cli_path` runs a turn, App Control result | `p_shim.py turn` | The turn is not run: the ship home has no plan login yet. Without a turn, the SDK started the uv `.exe` as `cli_path` and connected through it, and App Control blocked nothing (`p_shim.py version`). | BLOCKED | HP4 launcher |
| OQ17. What the shim receives on the SDK version-probe start | `p_shim.py version` | SDK 0.2.166 starts the shim as `[shim, "-v"]` with the process env only: no `QMA_*` name, so the shim cannot find the CLI (cold and warm runs agree). The SDK swallows the failure and connects anyway. A no-input mode that finds the bundled CLI with `find_spec` answered `-v` in 0.89 s to 1.13 s, inside the SDK's 2 s budget but with little margin. In 1 of 4 connects the `-v` start left no record, so the 2 s budget can end a cold start before the shim logs. | PASS | HP4 takes the no-input mode |
| OQ18. Trampoline job joins and the extra Python process size | `p_shim.py jobs` | The shim's Python child always starts inside the uv trampoline's job (`IsProcessInJob` true). Two shims joining one parent job: the first joins, the second fails with error 5 (access denied), in 4 of 4 runs with one record file per start. Both nest their own job. With the first fallback (CLI started with breakaway, suspended, assigned to the parent job and then a nested job), both shims succeed in 4 of 4 runs. The shim's Python process is 24.5 MB to 25.8 MB. | FAIL for the sketch path, PASS for the fallback | HP4 takes breakaway, suspended, assign to nested jobs |
