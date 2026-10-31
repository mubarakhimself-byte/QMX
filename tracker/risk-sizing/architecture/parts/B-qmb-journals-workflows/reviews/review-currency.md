# Review: was every committed decision reality-checked?

The first configured reviewer of `bmad-architecture`'s gate, run in sequence by part B's agent against `ARCHITECTURE-SPINE.md`.

**Verdict.** Every code fact the spine rests on was read at a cited line on `c93407ca` or run; one external fact was checked on the vendor's page today; one behaviour of the Claude CLI stays INFERRED and has a named recheck in its slice.

| Claim | How it was checked | Status |
| --- | --- | --- |
| Library pins (Python 3.14.6, pyarrow 25.0.1, jsonschema 4.26.0, optuna 4.9.0, FastAPI 0.142.2, claude-agent-sdk 0.2.166, cronsim 2.7, tzdata 2025.2) | Level 0's stack table, CHECKED against the lockfiles and vendors on 31 Oct (`level-0/reviews/review-currency.md`); part B adds no dependency | current |
| The prompt cache's default life is five minutes (the reason for `[qmb] agent_wait_s` = 240) | context7, Anthropic's page `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`: the default TTL is 5 minutes, refreshed on use, with an optional 1-hour TTL | CHECKED 31 Oct; other providers differ, so the number is a setting |
| An operation call stops the app after 30 s | `qmx_apps/supervisor.py:957-963`, read | CHECKED |
| A job waits as long as it runs; a request is `{"job": job}`; `run()` takes no argument | `supervisor.py:986-1043`, `:1022`; `bootstrap.py:195-228`, read | CHECKED |
| One running instance per app id | `supervisor.py:570`, `:951` | CHECKED |
| The manifest refuses `both` without a `ui` folder and an `instance` operation declared `read` | `qmx_apps/manifest.py:309-310`, `:325-327` | CHECKED |
| The artifact store hands each leave to the host's sink | `qmx_apps/artifacts.py:109-151` | CHECKED |
| The typed store reads `t` in milliseconds and holds numeric columns only | `qmf-data/src/qmf/data/series.py:690`; `store/engines/typed.py:56-92` | CHECKED |
| The CT-13 store is one-writer JSONL per world; its worlds are `live`, `replay`, `simulated` | `store/journal.py:1-60`; `qmf-core/src/qmf/core/fingerprint.py:412-424` | CHECKED |
| Jobs with inputs keep every shipped test green | ran the shipped app and `app_op` tests plus a new test on an overlay copy: 36 passed | CHECKED by running |
| The journal column and rule keep every price kind as it is | ran the whole `qmf-data` suite on an overlay copy: 584 passed, 3 skipped; the round-trip test passed | CHECKED by running |
| A refused row on Windows raises `PermissionError` in the shipped store | `scratchpad/l1b/refused_row_windows.py` on the unpatched code | CHECKED by running (a finding) |
| A workflow agent step is offered only its declared built-ins | `scratchpad/l1b/agw_offered_tools.py` runs the harness's selection and launch filter | CHECKED by running |
| The Claude CLI never runs a built-in absent from `tools` | not run | INFERRED; slice B17 reruns probe P-PERM on the real launch path |
| Hard links from the store into an app volume work on his drives | not run | INFERRED; slice B6 checks it and copies when it cannot link |

No finding needs his decision.
