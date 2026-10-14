# HP0 findings

Each row is one question from HARNESS-PLAN HP0. Evidence logs live in `D:/QMX-worktrees/qma-ship/evidence/hp0/`.

| Question | Probe | Observed | Verdict | Feeds |
| --- | --- | --- | --- | --- |
| S1. Newest SDK with a `win_amd64` wheel and a bundled CLI at 2.1.248 or later | `p_install.py` | `claude-agent-sdk==0.2.166`, wheel `py3-none-win_amd64`, bundled CLI `2.1.299 (Claude Code)` | PASS | every later PR's pin |
| S2, OQ6. Auth method string of a Max login, and `/login` offers no Console choice | `p_login.py` | pending | PENDING | HP4 `_connect` login check |
| S19. A Bash call under `reduced_env()`, then a fake `ANTHROPIC_API_KEY` in the parent env | `p_env.py` | pending | PENDING | HP2 boot scrub |
| S20, OQ3 to OQ5. Inline settings, ConfigChange, a planted plugin, argv length, `append-system-prompt-file` | `p_settings.py` | pending | PENDING | HP4 `code_settings`, `assert_argv_fits` |
| S10. `/usage` reaches Python | `p_sdk.py usage` | pending | PENDING | HP10 usage ledger |
| S37. `/effort high` changes the next request | `p_sdk.py effort` | pending | PENDING | HP6 `classify_change` |
| S38. A PreToolUse callback sleeping past `HookMatcher.timeout` blocks Bash in bypass mode | `p_sdk.py timeout` | pending | PENDING | HP8 gate timeout |
| S25. `verbatim_prompts=True` stops `/compact` dispatch | `p_sdk.py verbatim` | pending | PENDING | HP7 untrusted input |
| S18. Working set of one idle and one busy CLI | `p_ram.py` | pending | PENDING | HP4 memory caps, OQ11 |
| Shim. A uv console-script `.exe` as `cli_path` runs a turn, App Control result | `p_shim.py` | pending | PENDING | HP4 launcher |
| OQ17. What the shim receives on the SDK version-probe start | `p_shim.py` | pending | PENDING | HP4 launcher, which path |
| OQ18. Trampoline job joins and the extra Python process size | `p_shim.py jobs` | pending | PENDING | HP4 launcher, which path |
