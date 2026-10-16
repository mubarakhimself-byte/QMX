# Review: verification lens (was each committed fact checked against reality, not asserted from training data?)

Inline, sequential (no sub-agent available in this process).

**Verdict: pass with three flags.** Every bound technology is a brownfield pin read today from `qma/hp17`; the Hermes, n8n, CLIProxyAPI and Claude Workflow facts were read today by file 25 in a browser and are cited by section. Three claims rest on memory and must be marked or checked before a builder leans on them.

| Claim in the spine or design | Basis | Status |
| --- | --- | --- |
| Python `>=3.14,<3.15`, claude-agent-sdk 0.2.166, pydantic 2.13.4, fastapi 0.142.2, uvicorn 0.54.0, keyring 25.7.0, httpx 0.28.1 | `qma-harness/pyproject.toml` on `qma/hp17`, read 2026-10-16 | retrieved |
| `@xyflow/svelte` 1.6.6 | DEC-0469 and `stack.md:241` via file 24 | retrieved from docs, **not from the UI worktree's package.json**; check `QMX-worktrees/ui-review-repair/apps/qmx-ui/package.json` before binding (flag 1) |
| sqlite3 WAL in the stdlib | Python stdlib | remembered, uncontroversial |
| `uuid.uuid7()` available in Python 3.14 | memory of the 3.14 changelog | **remembered** (flag 2): if absent, the convention falls back to a vendored uuid7 helper; either way ids stay time-ordered strings |
| n8n `IWorkflowBase` fields, pin data development-only, Wait node offload, sub-workflow caller policy | file 25 section 2, read today | retrieved |
| Hermes credential-pool strategies, error ladder, cooldowns, leases, switch-back, quota hold, missed-occurrence contract, `no_agent`, monitors | file 25 sections 1.4-1.6, read today | retrieved |
| CLIProxyAPI strategies, session affinity, per-model cooldowns; cloaking by default | file 25 section 4, read today | retrieved; only the logic is borrowed (ruling 38) |
| Claude Workflow runtime: journal prefix replay, no usage-limit pause under the SDK, `CLAUDE_CODE_DISABLE_WORKFLOWS=1` in QMA | file 25 section 3 and `launch.py:239` | retrieved |
| Harness public names, `NewChat` fields, `Budgets`, `live()` deltas only, `ChatTableFull`, `BackgroundCap`, `agent-memory/<ws>` | `qma/harness/*.py` on `qma/hp17`, read today | retrieved |
| `qmx` tools `workflows_*`, `runs_*`, `jobs_*`, `library_*`; `ControlService.workflows_*` return 501 | `tools.py`, `service.py` on `qma/hp17`, read today | retrieved |
| `qmx_remote.RunBundle` fields; `RemoteRuns` methods | `qmx_remote/models.py`, `runs.py` on `qma/hp17` | retrieved |
| `qmx_ledger.journal.fingerprint` canonicalisation (sort_keys, compact, `allow_nan=False`) | `journal.py` on `qma/hp17` | retrieved |
| Temporal/Inngest saved-step and idempotency rules | file 13 section 3, read today by that file's author | retrieved via 13 |
| Shepherd reversibility tiers | file 13 section 1 | retrieved via 13 |
| RFC 6902 JSON Patch for variant overlays | standard | remembered, uncontroversial; the builder picks a library or hand-rolls (flag 3: name it in the implementation packet, not here) |
| OpenCode Go GLM/Kimi are chat-completions only; Ollama Cloud has an Anthropic endpoint, bearer only | file 25 section 5.4 | retrieved |
| ChatGPT sign-in refuses a second account (`siwc.py:403-404`) | file 25 section 5.1 | retrieved via 25 |

Actions: mark `uuid7` as remembered in the conventions with the fallback; add a note on the `@xyflow/svelte` pin's source; no other change.
