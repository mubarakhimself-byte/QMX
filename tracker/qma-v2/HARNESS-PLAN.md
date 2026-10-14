# QMA v2 one-engine harness plan

This program builds QMA v2 on one engine, the Claude Agent SDK, as `research/one-engine/architect/DESIGN.md` and its `sketch/qma/` specify.
The operator gets a QMX agent he talks to like Claude Code on his one Max plan, with key providers by base URL and GPT through his ChatGPT sign-in. The next engineer inherits one package, `qma-harness`, and live check scripts that rerun.
The rule it enforces is that every invariant in DESIGN section 5 has a live check that ran green at the head of the PR that adds it.
PR ids in order are HP0, HP1 and HP2 (probes), HP3 (imports without LangChain), HP4 to HP16 (the harness), and HP17 (sign-off).
Old-code deletion is a separate program in `DELETION-PLAN.md`. It starts only after HP17 merges and the operator signs off.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-full.md`. The rule at the end of `playbooks/autopilot-stack.md` picks it, and Appendix B gives the reason. The coordinator session is the root. It dispatches one builder per PR, verifies each PR itself, and merges it into `rebuild/base` after a clean verdict. Owners stop at merge-ready and never merge, which is the project rule and replaces step 5 of autopilot-full. HP15, HP16 and HP17 are the operator's items. They stop at merge-ready for his review and his click or written go. `main` moves only by his own click. `integration` is not used.

Each PR lists ten live lanes. They are a coverage list, not ten agents. One verifier, the coordinator itself, runs them in sequence in one boot of the PR head on the operator's PC, because he has one Claude Max 5x plan. Every lane is real. It uses the bundled CLI, the plan login in the ship home, real provider keys from the OS keyring and real files. `S<n>` names a check in DESIGN section 5. "Operator check <n>" names a row of `research/one-engine/04-baseline.md` section 4.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] In the same message, list the four things only he can do, with a time for each. Log his answers in `D:/QMX-worktrees/qma-ship/decisions.tsv`.
  - [ ] Add the provider keys he wants tested to the OS keyring under `qmx/kimi`, `qmx/glm`, `qmx/deepseek`, `qmx/minimax`, `qmx/meta` and `qmx/openrouter`. The coordinator reads names only, never values.
  - [ ] Type `/login` once in HP0, so the CLI stores the plan login in the ship home.
  - [ ] Approve "QMA" on OpenAI's page once in HP2, and again in HP16 if the stored session expired.
  - [ ] Run `scripts/live/qma/s27_broker_scope.py` himself on a demo account in HP14.
- [ ] Read these from trunk at program start. Re-read them at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is not on `main` yet.
  - [ ] `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/HARNESS-PLAN.md`, then `research/one-engine/architect/DESIGN.md`, `SYNTHESIS.md` and `sketch/qma/` from the same branch. The plan branch is local only.
  - [ ] Read `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-full.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md`, `no-comments/SKILL.md`, `show-me-your-work/SKILL.md` and `principle-prove-it-works/SKILL.md`. These live in the local install, not in the repo.
- [ ] Create the store `D:/QMX-worktrees/qma-ship/` with `decisions.tsv`, `ledger.tsv`, `turns.tsv`, `evidence/`, `review/` and `home/`. Write these standing orders into `decisions.tsv` as its first rows.
  - [ ] Builders run on `opus`. Never `bulk-worker`. Fable only when the operator asks. Every brief says "do not spawn sub-agents".
  - [ ] At most two builders run at once, plus the coordinator.
  - [ ] Live lanes use the `haiku` tier on the plan unless the check names another model. Each plan turn gets a row in `turns.tsv`.
  - [ ] When the plan's five-hour window reaches 50%, the coordinator pauses live lanes until the window resets (R6).
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Spawn one owner per PR with the Agent tool, `subagent_type: "poteto-agent"`, `model: "opus"` and `run_in_background: true`. The brief holds the PR's section of this plan, the DESIGN and sketch files it names, `research/one-engine/how/HOW-one-engine.md` gotchas 1 to 16, the full lifecycle from autopilot-full step 2, and "do not spawn sub-agents".
- [ ] Follow this dependency graph. Start dependent work only after its parent merges. Sequenced work is merge-then-branch per autopilot-full step 3.
  - [ ] HP0, HP2 and HP3 are independent and first. All branch from `rebuild/base`. Run at most two at once.
  - [ ] HP1 after HP0, which fixes the SDK pin.
  - [ ] HP4 after HP3 and HP0.
  - [ ] HP5 after HP4. HP6 after HP5.
  - [ ] HP7 after HP6 and HP1.
  - [ ] HP8 after HP7. HP9 after HP8. HP10 after HP9. HP11 after HP10.
  - [ ] HP12 after HP11. HP13 after HP12. HP14 after HP13. HP15 after HP14.
  - [ ] HP16 after HP15 and HP2, and only when HP2's `FINDINGS.md` row says the route is viable. Otherwise park HP16, keep the GPT row hidden, and record that the operator decides (01 section 9 question 1).
  - [ ] HP17 after HP15, and after HP16 merged or parked.
- [ ] Hold the file boundaries.
  - [ ] Harness PRs touch only `qmx-agents/packages/qma-harness/**`, `qmx-agents/plugin/**`, `scripts/live/qma/**`, `scripts/probes/qma/**`, and the workspace files each PR names.
  - [ ] Only HP3 moves code in `qmx-agents/packages/qmx-agents`, `qmx-apps`, `qmx-remote`, `qmx-tools` and `qma-core`.
  - [ ] Only HP5 and HP8 edit `qmx-agents/packages/qmx-control`, and only the lines they name.
  - [ ] No harness PR touches `qmb/`, `qmn/`, `qmf/`, `qml/` or `apps/qmx-ui/`, and no harness PR deletes old agent code.
- [ ] Hold the review gate. HP15, HP16 and HP17 change what the operator sees. They wait for his review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that in `decisions.tsv`. Never require `gt`.
- [ ] Branch `qma/<pr-id>` from current `origin/rebuild/base` in the worktree `D:/QMX-worktrees/qma-<pr-id>`. Open the PR ready, never draft, per **Opening a PR**, with `gh pr create --base rebuild/base --head qma/<pr-id>`.
- [ ] Run `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in every workspace the PR touched, before the PR-facing push. Push with hooks on.
- [ ] Reread the full diff before each commit in place of `/deslop`, which is not installed. Run `/no-comments` before review.
- [ ] Triage every finding from the coordinator's audit lanes per `C:/Users/Mubarak/.claude/skills/poteto-mode/references/bugbot-triage.md`. No Bugbot runs on this repo.
- [ ] Rebase onto current `origin/rebuild/base` before the code-ready report and babysit. Keep that merge base in fix rounds. Rebase again only at merge prep, on a `git merge-tree` conflict with trunk, or on a CI failure that comes from a change on trunk.
- [ ] End each commit message with the attribution lines from the session's system reminder.

### Verdict and merge, for every PR

- [ ] At the code-ready head SHA and at each later push that changes the patch, the coordinator runs the swarm lanes per `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md`, inline and in sequence.
  - [ ] One gates lane runs `just ci` under the CI lock. Take the lock with `mkdir D:/QMX-worktrees/.ci-lock`, which fails while another run holds it, and remove the folder after the run.
  - [ ] The ten live lanes from the PR's **Verify, live** block.
  - [ ] The perf lane from its **Verify, perf** block.
  - [ ] Audit lane A reads the diff against DESIGN and the sketch for the modules the PR names, distrusting the PR body. It checks names, invariants and the import rules.
  - [ ] Audit lane B reads the diff for scope and safety. It checks files outside the PR's boundary, secret values, money paths, and `TestMode(` outside `scripts/live/` and tests.
- [ ] Clean only when every lane is `PASS`. Findings go back to a fresh owner with consolidated scope, including a defect that a lane filed as a note. A new head gets a fresh run, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`. Record each verdict in `ledger.tsv` with head SHA, base SHA and `git patch-id --stable`.
- [ ] Merge only from a head rebased onto current `origin/rebuild/base`, with `git merge-tree` clean and the patch-id equal to the verdict's. The root runs `gh pr merge <number> --merge --repo MubarakHimself/QMX`. HP15, HP16 and HP17 merge only after the operator's click or his written go.

### Boot recipe, for every live lane

The coordinator runs every lane of a PR on the operator's PC in one boot, not on a cloud VM. No `control-cli` or `control-ui` skill is installed. Lanes drive the HTTP doors with `scripts/live/qma/drive.py`, the check scripts directly, and from HP15 on the console through the terminal tools `run_in_terminal` and `read_terminal`, which stand in for `control-cli`.

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin qma/<pr-id>`, then check out the head SHA detached in `D:/QMX-worktrees/qma-verify`.
- [ ] In the lane shell, put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`, then run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] From HP5 on, start the host with `uv run --no-sync python -m qma.serve serve --home D:/QMX-worktrees/qma-ship/home --port 8876` and wait for `GET /api/health`. Before HP5, lanes run their scripts directly. Lanes that need `TestMode` run the harness inside the check script's own process, never through `qma.serve`.
- [ ] Deliver input only through `drive.py`, the `scripts/live/qma/` and `scripts/probes/qma/` scripts, and the console. The read-only diagnostics are `GET /api/doctor`, `GET /api/usage`, `Get-Process`, the chat records and reads of `control.db`.
- [ ] Run every check that touches `~/.claude` with a throwaway `HOME` and `USERPROFILE`, never his real folder.
- [ ] Save a text capture as `<slug>.log`, which is the CLI's screenshot. Save a console screen as `<slug>.png` with `ffmpeg -f gdigrab -i title=<window title> -frames:v 1`. Put both in `D:/QMX-worktrees/qma-ship/evidence/<pr-id>/` and return the paths with the report.
- [ ] Stop the host and confirm with `Get-Process` that no `claude` or `qma-cli-launcher` process from the lane is left.

## Settle the CLI and SDK facts on the plan (HP0)

**Depends on.** None. It branches from `rebuild/base`.

**Files.**

- [ ] Create `scripts/probes/qma/common.py`, `p_install.py`, `p_login.py`, `p_env.py`, `p_settings.py`, `p_sdk.py`, `p_ram.py`, `p_shim.py` and `test_common.py`.
- [ ] Create `scripts/probes/qma/FINDINGS.md`.

**Build.**

- [ ] In `p_install.py`, pick the newest `claude-agent-sdk` release with a `win_amd64` wheel and a bundled CLI at 2.1.248 or later, install it in a throwaway venv on `D:`, and print both versions (S1).
- [ ] In `p_login.py`, start the bundled CLI in a terminal with `CLAUDE_CONFIG_DIR=D:/QMX-worktrees/qma-ship/home/claude` and `--settings '{"forceLoginMethod": "claudeai"}'`. The operator types `/login`. Then print only the auth method field of `claude auth status` (S2, DESIGN open question 6).
- [ ] In `common.py`, write `reduced_env()`, which keeps the names in the sketch's `boot.KEEP_NAMES` plus `CLAUDE_CONFIG_DIR`. In `p_env.py`, run one plan turn with a Bash call under it, then again with a fake `ANTHROPIC_API_KEY` in the parent env (S19 prototype).
- [ ] In `p_settings.py`, connect a raw SDK client with `setting_sources=[]` and an inline `settings` JSON that carries `forceLoginMethod`, `cleanupPeriodDays` and a ConfigChange command hook. Have the agent write `settings.json` into the home mid-session. Record whether ConfigChange fired, whether a plugin planted in the home loads, and the argument length (S20 prototype, DESIGN open questions 3 to 5).
- [ ] In `p_sdk.py`, record whether `/usage` reaches Python (S10), whether `/effort high` changes the next request (S37), whether a PreToolUse callback that sleeps past `HookMatcher.timeout` blocks a Bash call in bypass mode (S38), and whether `verbatim_prompts=True` stops `/compact` from dispatching (S25).
- [ ] In `p_ram.py`, measure the working set of one idle and one busy CLI (S18).
- [ ] In `p_shim.py`, build a uv console-script `.exe` in a `D:` venv that runs the bundled CLI with the same args, pass it as `cli_path`, and run one turn. Record whether Windows App Control blocks it.
- [ ] In `FINDINGS.md`, write one row per question with the observed value, PASS or FAIL, and the later PR the value feeds.

**You see.**

- [ ] `FINDINGS.md` has a filled row for each of the nine probes, and `p_install.py` prints a `win_amd64` wheel tag and a CLI version of 2.1.248 or later.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `scripts/probes/qma/test_common.py` gains a case that `reduced_env()` keeps `CLAUDE_CODE_GIT_BASH_PATH` and drops `HTTPS_PROXY`, `ANTHROPIC_API_KEY`, `NODE_EXTRA_CA_CERTS` and `CLAUDE_CODE_USE_BEDROCK`. Run `uv run --no-sync python -m pytest scripts/probes/qma -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `claude -p "say ok"` with the trunk dev pin `claude-agent-sdk==0.2.163` and with the candidate pin at head, both in the ship home. Save `hp0-regression.log`. Pass when head replies on the plan, and trunk either replies or its failure is recorded with the error text.
- [ ] Lane 2. Run `p_install.py`. Save `hp0-install.log`. Pass when the wheel tag is `win_amd64` and the CLI version is 2.1.248 or later.
- [ ] Lane 3. Run `p_login.py` with the operator at the keyboard. Save `hp0-login.png`. Pass when the sign-in offers no Console choice and the auth method string is recorded verbatim.
- [ ] Lane 4. Run `p_env.py`. Save `hp0-env.log`. Pass when the Bash call runs under the reduced env, and the run with the fake key still shows a `RateLimitEvent` for the plan.
- [ ] Lane 5. Run `p_settings.py`. Save `hp0-settings.log`. Pass when the CLI accepts the inline settings and the log records the ConfigChange result, the planted plugin result and the argument length.
- [ ] Lane 6. Run the `/usage` case of `p_sdk.py`. Save `hp0-usage.log`. Pass when the log records what Python received, or that nothing arrived.
- [ ] Lane 7. Run the `/effort` case of `p_sdk.py`. Save `hp0-effort.log`. Pass when the log records whether the next request used the new effort.
- [ ] Lane 8. Run the timeout and verbatim cases of `p_sdk.py`. Save `hp0-timeout.log`. Pass when the sleeping callback blocks the Bash call with an error that names the timeout, and the verbatim `/compact` produces no `compact_boundary`.
- [ ] Lane 9. Run `p_ram.py`. Save `hp0-ram.log`. Pass when the idle and busy working sets are recorded in MB.
- [ ] Lane 10. Run `p_shim.py`. Save `hp0-shim.log`. Pass when the SDK runs a turn through the shim, or the App Control block is recorded with its event text.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of one `say ok` plan turn, from process start to `ResultMessage`.
- [ ] Probe. Five runs of vanilla `claude -p` at the trunk pin and five through the SDK at the candidate pin, interleaved.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Fail when the head median exceeds the trunk median by more than 50%. Trunk may lack a working Windows CLI. Then record that, and fail when the head median exceeds 15 s.

**Review gate.** None. HP0 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Settle provider compatibility on the Claude engine (HP1)

**Depends on.** HP0, for the SDK pin and `reduced_env()`.

**Files.**

- [ ] Create `scripts/probes/qma/p_providers.py`, `p_resume.py` and `p_echo.py`.
- [ ] Edit `scripts/probes/qma/FINDINGS.md` and `test_common.py`.

**Build.**

- [ ] In `p_providers.py`, run the bundled CLI against GLM, Kimi, DeepSeek, MiniMax, Meta Muse and OpenRouter. Set `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` together from keyring `qmx/<provider>`, pin all four tier models, and use `reduced_env()` and a fresh home with no login. On OpenRouter use only a model that is neither Claude nor GPT (R4).
  - [ ] Run 02b probes B1 (one Bash call), B3 (cache reads on turn three) and B4 (a two-turn tool loop with thinking), plus one WebSearch.
  - [ ] Record the init tool-search state with and without `ENABLE_TOOL_SEARCH=true`.
  - [ ] Retry Meta Muse with `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` when it rejects a request.
  - [ ] Print `NO KEY` for a row whose keyring entry is missing.
- [ ] In `p_resume.py`, start a plan chat with thinking in the ship home, then resume the same session id under the first keyed provider from a home whose `projects/` links to the plan home's, and ask a recall question. On failure, retry after `/compact` (S36).
- [ ] In `p_echo.py`, run a local http echo server. Point a profile at it with a fake key, from a throwaway home whose login file holds the canary `sk-ant-oat01-QMXCANARY`. Run once with a token and once with a base URL and no token (S9 prototype, 02a trap 7).
- [ ] In `FINDINGS.md`, write one row per provider with B1, B3, B4, WebSearch, tool search and the quirks it needed, plus the S36 and trap 7 results.

**You see.**

- [ ] `FINDINGS.md` has one row per provider that reads PASS, FAIL or NO KEY for each probe, and an S36 row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_common.py` gains a case that a provider env sets `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` together and all four tier variables. Run `uv run --no-sync python -m pytest scripts/probes/qma -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk routes providers only through `models.yaml` and the `cliproxy` URL, so record that it has no Claude-engine provider path. Gate one OpenRouter turn with a Bash call at head. Save `hp1-regression.log`. Pass when the Bash result appears in the reply and the turn has no API error.
- [ ] Lane 2. Run the GLM row. Save `hp1-glm.log`. Pass when B1, B3 and B4 each print a value, or the row prints `NO KEY`.
- [ ] Lane 3. Run the Kimi row. Save `hp1-kimi.log`. Pass when B1, B3 and B4 each print a value and the cache-marker result is recorded, or the row prints `NO KEY`.
- [ ] Lane 4. Run the DeepSeek row. Save `hp1-deepseek.log`. Pass when B1, B3 and B4 each print a value, or the row prints `NO KEY`.
- [ ] Lane 5. Run the MiniMax row. Save `hp1-minimax.log`. Pass when B1, B3 and B4 each print a value and the forced-thinking result is recorded, or the row prints `NO KEY`.
- [ ] Lane 6. Run the Meta Muse row. Save `hp1-meta.log`. Pass when B1, B3 and B4 each print a value and the log says whether experimental betas had to be off, or the row prints `NO KEY`.
- [ ] Lane 7. Run the OpenRouter row with a non-Claude, non-GPT model. Save `hp1-openrouter.log`. Pass when B1, B3 and B4 each print a value on the Anthropic endpoint, or the failure is recorded with its status code.
- [ ] Lane 8. Run `p_resume.py`. Save `hp1-resume.log`. Pass when the recall answer is right, or the failure and the after-compact result are both recorded.
- [ ] Lane 9. Run `p_echo.py`. Save `hp1-echo.log`. Pass when the echo server received only the fake key in the run with a token, and the log records whether the canary arrived in the run without one.
- [ ] Lane 10. Collect tool search and WebSearch across rows. Save `hp1-toolsearch.log`. Pass when each keyed row records tool search on with `ENABLE_TOOL_SEARCH=true` and a WebSearch result or refusal.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to the first streamed byte of a `say ok` turn, per keyed provider and on the plan.
- [ ] Probe. Three runs per keyed provider and three on the plan, interleaved.
- [ ] Baseline. Record the plan median first. Trunk has no provider path, so the plan is the reference, not a trunk ratio.
- [ ] Rule. Fail when a keyed row cannot produce the metric at all. Mark a row slow in `FINDINGS.md` when its median exceeds three times the plan median.

**Review gate.** None. HP1 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Settle the GPT route on the ChatGPT plan (HP2)

**Depends on.** None. It branches from `rebuild/base`.

**Files.**

- [ ] Create `scripts/probes/qma/p_gpt.py` and `test_gpt_body.py`.
- [ ] Edit `scripts/probes/qma/FINDINGS.md`.

**Build.**

- [ ] In `p_gpt.py`, write a throwaway Sign in with ChatGPT client per 02b section D. Use `client_id=dynamic_agent_client`, `agent_name_hint="QMA"`, PKCE S256 and a loopback callback on 127.0.0.1. Store the refresh token under keyring `qmx/chatgpt` and keep the access token in memory only.
- [ ] Run probes P0 to P5 from 02b section D in order, each only after the previous one passed. P4 failing is not fatal. Apply the stop rule. P2 `subscription_sharing_user_not_eligible`, or P3 failing in both tool shapes, ends the run.
- [ ] In `FINDINGS.md`, write a GPT row that reads viable, with the tool shape and the reasoning-replay result, or the stop rule and the step that fired it.

**You see.**

- [ ] The GPT row in `FINDINGS.md` reads viable with `tools_shape` and `reasoning_replay` values, or names the step that fired the stop rule.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_gpt_body.py` gains cases that the request body has `store` false and `stream` true, carries no `max_tokens`, `temperature` or `metadata`, and moves `system` into `instructions`. Run `uv run --no-sync python -m pytest scripts/probes/qma -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk has no GPT route on the plan, so record that. Gate probe P2 at head. Save `hp2-regression.log`. Pass when a streamed reply arrives with `store` false, or the stop rule fires and its error code is recorded.
- [ ] Lane 2. Run P0 with the operator approving "QMA". Save `hp2-p0.png`. Pass when the granted scopes include `chatgpt.tokens.use.direct`.
- [ ] Lane 3. Run P1. Save `hp2-p1.log`. Pass when `/v1/models` lists the GPT models the profile would pin.
- [ ] Lane 4. Run P2. Save `hp2-p2.log`. Pass when a hello streams to `response.completed`.
- [ ] Lane 5. Run P3 with namespace tools. Save `hp2-p3-namespace.log`. Pass when a function call comes back, or the refusal is recorded.
- [ ] Lane 6. Run P3 with plain tools. Save `hp2-p3-plain.log`. Pass when a function call comes back, or the refusal is recorded, and at least one of lanes 5 and 6 passed.
- [ ] Lane 7. Run P4. Save `hp2-p4.log`. Pass when the log records whether `reasoning.encrypted_content` came back and replayed.
- [ ] Lane 8. Run P5. Save `hp2-p5.log`. Pass when each barred field returns 400.
- [ ] Lane 9. Force a token refresh. Save `hp2-refresh.log`. Pass when the rotated refresh token is stored under `qmx/chatgpt` and no access token is on disk.
- [ ] Lane 10. Search the probe logs and `FINDINGS.md` for the access and refresh token values. Save `hp2-secrets.log`. Pass when no value is found.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to the first streamed byte of the P2 hello.
- [ ] Probe. Five P2 runs at head, spaced one minute apart.
- [ ] Baseline. Trunk lacks the route. Record that, and record the head median as the reference for HP16.
- [ ] Rule. Fail when the head median exceeds 10 s.

**Review gate.** None. HP2 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Make qmx-control import without LangChain (HP3)

**Depends on.** None. It branches from `rebuild/base`. This is DESIGN deletion step 0. It moves code and deletes nothing.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-ledger/` with `pyproject.toml` and `tests/`. Move `qmx_agents/guards/journal.py`, `experiments.py` and `parent_surfaces.py` into `src/qmx_ledger/` with `git mv`.
- [ ] Create `qmx-agents/packages/qma-core/src/qma/core/barriers/descriptors.py` with the LangChain-free `check_descriptor` from `qmx_agents/guards/money_path.py`, and `qma-core/tests/test_descriptors.py`.
- [ ] Create `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` with `domain_functions` and its helpers, moved from `registry.py`.
- [ ] Edit the callers at `qmx_apps/road/__init__.py:11`, `road/history.py:13`, `road/validation.py:12`, `qmx_apps/supervisor.py:29`, `qmx_remote/models.py:11`, `qmx_remote/runs.py:16`, `qmx_remote/worker.py:29` and `qmx_tools/servers.py`, plus every `qmx_agents` module that imported a moved name.
- [ ] Edit `qmx-apps/pyproject.toml` (drop `qmx-agents`, add `qmx-ledger` and `qma-core`), `qmx-remote/pyproject.toml` (add `qmx-ledger`), `qmx-agents/pyproject.toml` (members), the pyright paths in the root `pyproject.toml`, `tools/ci.py`, `tools/test_all.py` and both `uv.lock` files.

**Build.**

- [ ] Migrate every caller to the new module and leave no re-export shim in `qmx_agents/guards/` (principle migrate-callers-then-delete).
- [ ] Keep `check_descriptor` behaviour unchanged, including the proposal-writer exemption.

**You see.**

- [ ] After `uv pip uninstall` of every `langchain*`, `langgraph*` and `deepagents` package in the `qmx-agents` venv, `python -c "import qmx_control, qmx_apps, qmx_remote, qmx_tools.servers"` exits 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `qmx-ledger/tests/test_journal.py` gains the hash-chain and stale-lock cases from the old journal tests. `qma-core/tests/test_descriptors.py` gains cases that `place_order` is refused and `propose_order` on the proposal writer is exempt. Run the qmx-ledger, qma-core, qmx-apps, qmx-remote and qmx-tools suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the qmx-apps, qmx-remote and qmx-control suites at trunk and head. Save `hp3-suites.log`. Pass when both report the same pass and fail counts.
- [ ] Lane 2. Run the import from **You see.** in the uninstalled venv. Save `hp3-import.log`. Pass when it exits 0 and `python -X importtime` shows no `langchain_core` line.
- [ ] Lane 3. Run `uv lock --check` at the root and in `qmx-agents/`, then `uv tree`. Save `hp3-lock.log`. Pass when both locks pass and no path leads from `qmx-apps` back to `qmx-agents`.
- [ ] Lane 4. Run `python -m qmx_control start`, `status` and `stop` on a lane home at port 8876. Save `hp3-host.log`. Pass when each exits 0 and `status` names the PID.
- [ ] Lane 5. Call `runs_list` through REST on a home copied from the operator's, at trunk and head. Save `hp3-runs.log`. Pass when the run counts and costs match.
- [ ] Lane 6. Call `apps_list` through REST. Save `hp3-apps.log`. Pass when the installed apps return with no error.
- [ ] Lane 7. Install a fixture app whose manifest declares a tool named `place_order`, at trunk and head. Save `hp3-supervisor.log`. Pass when the supervisor refuses it on both sides.
- [ ] Lane 8. Run `git grep -n "qmx_agents.guards"` outside `qmx-agents/packages/qmx-agents`. Save `hp3-grep.log`. Pass when it prints nothing.
- [ ] Lane 9. Start `qmx-mcp-data` over stdio and list its tools with an MCP client, at trunk and head. Save `hp3-mcp.log`. Pass when both list the same names.
- [ ] Lane 10. Run `python -c "import qmx_agents.copilot"` at head in the full venv. Save `hp3-copilot.log`. Pass when it exits 0, which shows nothing was deleted early.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Cumulative import time of `qmx_control` from `python -X importtime`.
- [ ] Probe. Five runs at trunk and five at head, interleaved, in the full venv.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Fail when the head median is not lower than the trunk median, since LangChain no longer loads on import.

**Review gate.** None. HP3 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Start every agent CLI under the OS limits (HP4)

**Depends on.** HP3, which also edits the workspace files, and HP0, for the SDK pin and the shim result.

**Files.**

- [ ] Create `qmx-agents/packages/qma-harness/pyproject.toml`. List the modules `qma.boot`, `qma.serve`, `qma.launcher`, `qma.console`, `qma.harness` and `qma.gpt`. Declare the console script `qma-cli-launcher = "qma.launcher:main"`. Declare runtime dependencies on `claude-agent-sdk==<HP0 pin>`, `qmx-control`, `qmx-tools`, `qmx-broker`, `qma-core`, `qmx-ledger`, `keyring`, `httpx`, and `pywin32` on Windows.
- [ ] Create `src/qma/boot.py`, `src/qma/launcher.py`, `src/qma/harness/__init__.py` and `src/qma/harness/procs.py`.
- [ ] Create `tests/test_boot.py`, `test_launcher.py`, `test_procs.py` and `test_import_rules.py`.
- [ ] Create `scripts/live/qma/s01_install.py`, `s30_os_cap.py` and `s30b_orphans.py`.
- [ ] Edit `qmx-agents/pyproject.toml` (add the member, move `claude-agent-sdk` out of the dev group), the pyright paths in the root `pyproject.toml`, `tools/ci.py`, `tools/test_all.py` and both `uv.lock` files.

**Build.**

- [ ] Write `boot.KEEP_NAMES` and `scrub_process_env` as the sketch's `boot.py` states.
- [ ] Write `launcher.main` per OS as the sketch's `launcher.py` states. That covers nested Job Objects on Windows, the parent-death signal plus a `systemd-run --user --scope` under `qma-agents.slice` on Linux with a fallback, a kqueue parent watch on macOS, the pid file, and `--qma-block-config-change`, which exits 2.
- [ ] Write `AgentProcessCap` as the sketch's `procs.py` states, after the precedent in `qmx_apps/windows_job.py`.
- [ ] Write `test_import_rules.py` as an AST scan with no new dependency. It enforces the DESIGN section 2 rules. `claude_agent_sdk` is imported only in `qma.harness` and `qma.gpt.probe`. `qma.boot` and `qma.launcher` import only the standard library. `qma.console` imports nothing from `qma.harness`. `KEEP_NAMES` holds no forbidden fragment. `TestMode(` appears only under `scripts/live/` and tests, and `ProbePassed(` only in `probe.py`.

**You see.**

- [ ] `qma-cli-launcher -v` prints the bundled CLI version, and `s30_os_cap.py` prints `PASS` with `last_killed` naming one chat.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_boot.py` gains cases for idempotence, sorted removed names, case-insensitive names on Windows and the forbidden fragments. `test_launcher.py` gains cases that the block flag exits 2, that `QMA_*` inputs are stripped before the CLI starts, and that a fake CLI's exit code passes through. `test_procs.py` gains a case that a reused pid with a new start time reads as dead. Run `uv run --no-sync python -m pytest qmx-agents/packages/qma-harness/tests -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk has no launcher. Run the bundled `claude -v` at trunk and `qma-cli-launcher -v` at head. Save `hp4-version.log`. Pass when both print the same version.
- [ ] Lane 2. Run `s01_install.py` (S1). Save `hp4-s01.log`. Pass when the wheel tag is `win_amd64`, the CLI is 2.1.248 or later, and the launcher shim is an `.exe` that App Control lets run.
- [ ] Lane 3. Run `qma-cli-launcher -p "say ok"` in the ship home with the `QMA_*` inputs set. Save `hp4-passthrough.log`. Pass when the reply prints and the exit code equals the direct CLI's.
- [ ] Lane 4. Watch the pid file during the lane 3 run. Save `hp4-pidfile.log`. Pass when `procs/<chat>.json` holds the launcher pid, the CLI pid and the start time while the CLI runs, and is gone after it exits.
- [ ] Lane 5. Run `s30_os_cap.py` on Windows (S30). Save `hp4-s30.log`. Pass when only the chat that ran the memory-heavy command dies, `report().last_killed` names it, and the other two still answer.
- [ ] Lane 6. Run `s30b_orphans.py` (S30b). Save `hp4-s30b.log`. Pass when every CLI and grandchild is gone within 10 s of the hard kill, with the time recorded.
- [ ] Lane 7. Leave a live launcher tree with its pid file, start a new cap holder and call `kill_orphans`. Save `hp4-orphans.log`. Pass when the tree dies and the returned ids name its chat.
- [ ] Lane 8. Pipe a ConfigChange hook input into `qma-cli-launcher --qma-block-config-change`. Save `hp4-block.log`. Pass when it exits 2 with the reason on stderr.
- [ ] Lane 9. Plant `import claude_agent_sdk` in a copy of `qma/boot.py` and run `test_import_rules.py`, then run it on the clean tree. Save `hp4-imports.log`. Pass when the planted copy fails and the clean tree passes.
- [ ] Lane 10. Run `s30_os_cap.py` in a `python:3.13-slim` container if `docker` runs on this PC. Save `hp4-linux.log`. Pass when `os_cap` is False and the CLI still runs, or the lane records that Docker is not available.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from process start to the CLI's `-v` output.
- [ ] Probe. Ten direct `claude -v` runs at trunk and ten `qma-cli-launcher -v` runs at head, interleaved.
- [ ] Baseline. Record the direct median first.
- [ ] Rule. Fail when the launcher median exceeds the direct median by more than 300 ms.

**Review gate.** None. HP4 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Serve the harness host with settings in code (HP5)

**Depends on.** HP4, and HP0 for the auth method string.

**Files.**

- [ ] Create `src/qma/serve.py`, `src/qma/harness/home.py`, `src/qma/harness/launch.py` and `src/qma/harness/routes.py`, with `tests/test_home.py` and `tests/test_launch.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/server.py` so `create_app` takes `extra_routers`, and `service.py` so `SettingsSection` gains `claude`.
- [ ] Create `scripts/live/qma/drive.py`, `s02_login.py`, `s19_boot.py` and `s20_settings.py`.

**Build.**

- [ ] Write `qma.serve.main`. It scrubs first, then takes the same CLI as `qmx_control` (`serve`, `start`, `status`, `stop`, `--home`, `--port`, `--ui-origin`), so a later QMB retarget is one string.
- [ ] Write `home.py` as the sketch states. That covers `QmxHome`, `ensure_homes` with a junction on Windows, `parse_claude_settings`, `code_settings`, `remember_rule`, `plan_auth_method` with the HP0 string, the chat records and `doctor`.
- [ ] Write `launch.py` for plan chats as the sketch states. That covers `ChatConfig`, the chat kinds, `verbatim`, `unattended`, `PlanLaunch`, `launch_env`, `assert_scrubbed`, `instructions`, `build_options`, `TestMode`, `CONSTANT_ENV` and `GATE_TIMEOUT_S`.
- [ ] `launch.instructions` reads the QMX-wide rules from `qmx-agents/plugin/QMX.md`, then the workspace's `CLAUDE.md` and `AGENTS.md`. A missing file adds nothing.
- [ ] Write the routes `GET /api/doctor` and `GET` and `PUT /api/claude-settings`, all `async def`.
- [ ] Write `drive.py` as an HTTP client that reads the bearer from keyring `qmx/control-token` and prints PASS or FAIL with the observed value.

**You see.**

- [ ] `GET /api/doctor` lists both Claude homes, the names the boot scrub removed with no values, the plan auth method and each departure from vanilla Claude Code.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_home.py` gains cases that `parse_claude_settings` refuses `apiKeyHelper`, `forceLoginMethod`, `enabledPlugins` and `env.HTTPS_PROXY`, that the fixed values win in `code_settings`, that `ensure_homes` is idempotent and refuses a login file in the relayed home, and that records are written atomically. `test_launch.py` gains a literal expected `build_options` for a plan chat and cases for `assert_scrubbed`, `verbatim` and `unattended`. Run `uv run --no-sync python -m pytest qmx-agents/packages/qma-harness/tests -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `python -m qmx_control serve` at trunk and `python -m qma.serve serve` at head on the lane home, then `GET /api/health` and `GET /api/sessions`. Save `hp5-health.log`. Pass when both sides return the same status and session list.
- [ ] Lane 2. Start `qma.serve` with the polluted parent env from DESIGN S19 and read `/api/doctor`. Save `hp5-s19.log`. Pass when every planted name is listed with no value and the Git Bash path is kept.
- [ ] Lane 3. Read the homes in `/api/doctor`. Save `hp5-homes.log`. Pass when `claude/` and `claude-relayed/` exist, neither is `~/.claude`, and `claude-relayed/projects` resolves to `claude/projects`.
- [ ] Lane 4. Plant a canary `.credentials.json` in the relayed home and restart. Save `hp5-canary.log`. Pass when `ensure_homes` refuses and doctor names the file.
- [ ] Lane 5. Run `s20_settings.py`, which PUTs each forbidden `[claude]` key (S20 second half). Save `hp5-s20.log`. Pass when each PUT is refused with the key named and `settings.toml` is unchanged.
- [ ] Lane 6. PUT one valid allow rule. Save `hp5-put.log`. Pass when the `settings.toml` diff is exactly that rule.
- [ ] Lane 7. Run `s02_login.py` for the ship home and a throwaway empty home. Save `hp5-s02.log`. Pass when the ship home reads the subscription method and the empty home is refused.
- [ ] Lane 8. Read the inline settings line in `/api/doctor`. Save `hp5-settings.log`. Pass when it holds `forceLoginMethod` `claudeai`, `cleanupPeriodDays` 3650 and the ConfigChange hook, and the length is below 32,767.
- [ ] Lane 9. Run `qma.serve start`, `status` and `stop`. Save `hp5-lifecycle.log`. Pass when each exits 0 and `status` names the PID.
- [ ] Lane 10. Read the managed-policy lines in `/api/doctor`. Save `hp5-policy.log`. Pass when doctor names every Windows managed-settings path it checked and whether each exists.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from process start to the first 200 on `/api/health`.
- [ ] Probe. Five starts of `qmx_control serve` at trunk and five of `qma.serve serve` at head, interleaved.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Fail when the head median exceeds the trunk median by more than 1 s.

**Review gate.** None. HP5 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Run one plan chat through Harness.send (HP6)

**Depends on.** HP5.

**Files.**

- [ ] Create `src/qma/harness/chat.py`, `harness.py` and `project.py`, with `tests/test_project.py`, `tests/test_chat.py` and recorded transcripts in `tests/fixtures/`.
- [ ] Edit `routes.py` (POST `/api/chats`, POST turns, POST interrupt, GET live) and `harness/__init__.py` (the public names that exist so far).
- [ ] Create `qmx-agents/plugin/.claude-plugin/plugin.json`, `qmx-agents/plugin/QMX.md` (the QMX-wide rules, money read-only first) and `qmx-agents/plugin/skills/qmx-overview/SKILL.md`.
- [ ] Create `scripts/live/qma/s03_tools.py`, `s04_vanilla.py`, `s07_isolation.py`, `s12_interrupt.py`, `s13_compact.py`, `s14_resume.py` and `s21d_redaction.py`.

**Build.**

- [ ] Write `Chat` as the sketch states for plan chats. That covers the Cold and Live states, `_connect` steps 1 to 7, `_read` routing, the `ChatRecord` rules for `started` and `turn`, and `session_id` before the first result and `resume` after it.
- [ ] Give `can_use_tool` a floor that rejects every call that would ask, with the reason "approvals are not wired yet". HP9 replaces it.
- [ ] Write `project` as one pure function over the SDK message union, with `redact` applied first and the 14 block kinds.
- [ ] Write `Harness.open` steps 1 to 4, `start_chat`, `send`, `interrupt`, `live` and `close`.
- [ ] The post-connect check accepts exactly the QMX plugin and no MCP server, and closes the chat with a `needs_you` block otherwise.

**You see.**

- [ ] `drive.py turn <sid> "What is in this folder? Summarise the README."` streams `tool` blocks for the reads and a `text` block, and the chat record ends with `turn` "idle" and `started` true.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_project.py` gains cases over recorded transcripts with literal expected blocks for text, tool started and finished, plan, agents, compact and result, plus `redact`. `test_chat.py` gains cases with a fake client that `started` turns true only on the first `ResultMessage` and that a record left "running" yields one `needs_you` block at open. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk has no turn route, and its stdin loop in `scripts/live/copilot_build_app.py` runs on LangChain. Record that, and run operator check 2 at head through `drive.py` and with `claude -p` in the same workspace (S4 read-only part). Save `hp6-check2.log`. Pass when both read the README and the head turn ends idle with `tool` and `text` blocks.
- [ ] Lane 2. Run `s03_tools.py` (S3). Save `hp6-s03.log`. Pass when the tool list differs from vanilla by exactly the named entries in DESIGN S3, and the PowerShell result is recorded.
- [ ] Lane 3. Run `s07_isolation.py` with the throwaway home of every marker kind, then drop a plugin with a mod into each Claude home and connect (S7, S6 last part). Save `hp6-s07.log`. Pass when no marker appears, the throwaway `~/.claude` is byte-identical afterwards, and the chat with the planted plugin closes before its first prompt.
- [ ] Lane 4. Run the clean-kill case of `s14_resume.py` (S14). Save `hp6-s14a.log`. Pass when the recall question is answered right after the restart.
- [ ] Lane 5. Run the mid-turn kill, the kill between connect and first result, the deleted JSONL and the 40-day-old transcript cases of `s14_resume.py`. Save `hp6-s14b.log`. Pass when each matches DESIGN S14.
- [ ] Lane 6. Run `s12_interrupt.py` on a long reply (S12, Bash case in HP9). Save `hp6-s12.log`. Pass when `TurnEnded` arrives within 5 s of the interrupt and no CLI child is left.
- [ ] Lane 7. Run `s13_compact.py` with operator text `/compact` (S13). Save `hp6-s13.log`. Pass when a `Compacted` block arrives and a QMX rule from `append` is still followed afterwards.
- [ ] Lane 8. Send a turn with a fake `ANTHROPIC_API_KEY` in the parent env of `qma.serve` (S2). Save `hp6-s02.log`. Pass when the turn yields a plan `Limits` fact and doctor lists the name.
- [ ] Lane 9. Run `s19_boot.py` in its in-process mode, which adds `HTTPS_PROXY` to `os.environ` and sends (S19 last part). Save `hp6-s19.log`. Pass when `assert_scrubbed` refuses the send.
- [ ] Lane 10. Run `s21d_redaction.py`, then ask the chat to write a file (S21d and the floor). Save `hp6-s21d.log`. Pass when `control.db` and the live channel show `[redacted sk-ant token]`, and the write is rejected with no file created.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to the first text delta of a `say ok` turn on the `haiku` tier.
- [ ] Probe. Five vanilla `claude -p` runs and five head turns through `drive.py`, interleaved. Trunk has no harness, so vanilla is the reference.
- [ ] Baseline. Record the vanilla median first.
- [ ] Rule. Fail when the head median exceeds the vanilla median by more than 1.5 s, which bounds the connect, post-connect check and projection the diff adds.

**Review gate.** None. HP6 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Route key-provider chats through the loopback relay (HP7)

**Depends on.** HP6, and HP1 for each provider's quirks.

**Files.**

- [ ] Create `src/qma/harness/profiles.py` and `src/qma/harness/relay.py` (key lane only), with `tests/test_profiles.py` and `tests/test_relay.py`.
- [ ] Edit `launch.py` (`RelayedLaunch`, the relayed half of `launch_env`, `TestMode.loopback_http_provider`), `chat.py` (relayed connect and grant revoke) and `harness.py` (relay start and close).
- [ ] Create `scripts/live/qma/fake_model.py`, `s08_providers.py`, `s09_leak.py`, `s17_secrets.py`, `s21c_egress.py`, `s21e_relayed_home.py`, `s22_relay.py`, `s23_no_key_env.py`, `s24_usage_once.py` and `s41_model_ids.py`.

**Build.**

- [ ] Write `profiles.py` as the sketch states, with `parse_profiles` reading `settings.toml [providers]` and quirk defaults from HP1's `FINDINGS.md`.
- [ ] Write the key lane of `relay.py` as the sketch states. That covers `start`, `grant`, `revoke`, `handle`, `close`, `guard_model`, `swap_auth` and `apply_wire_quirks`. The usage sink writes one `model_call` event per upstream request to `<home>/runs/<session>/journal.jsonl` through `qmx_ledger.journal.RunJournal`.
- [ ] Write `fake_model.py`, a loopback Anthropic Messages server that replays a scripted list of content blocks, `tool_use` included, and records every request's headers and body. Later lanes use it with `TestMode(loopback_http_provider=True)` to script tool calls without spending plan turns.

**You see.**

- [ ] A chat on the OpenRouter profile answers operator check 2 through the relay, and its CLI env holds only the relay URL and the grant secret.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_profiles.py` gains a literal `resolve_model` table covering tier aliases, `[1m]` suffixes, router slugs, `auto`, the `o3` segment and Claude or GPT ids behind a key. `test_relay.py` gains cases against an in-process upstream for a 401 before the body is read, the 400 egress stop, the 404 path, the forwarded query string, literal `swap_auth` headers, literal wire-quirk bodies and the served-model abort. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk reaches providers only through `models.yaml` and `cliproxy`. Record that, and run operator check 2 on the OpenRouter profile at head. Save `hp7-check2.log`. Pass when the reads and the text arrive and each upstream request has one `model_call` row.
- [ ] Lane 2. Run `s08_providers.py` for each keyed row (S8). Save `hp7-s08.log`. Pass when each row matches its HP1 result and records tool search and quirks.
- [ ] Lane 3. Run `s09_leak.py` against `fake_model.py` (S9). Save `hp7-s09.log`. Pass when the fake model received only the fake provider key, never the plan login and never the grant secret.
- [ ] Lane 4. Run `s21c_egress.py` (S21c). Save `hp7-s21c.log`. Pass when the relay returns 400, its egress counter moves, and the fake model never receives the string.
- [ ] Lane 5. Run `s21e_relayed_home.py` (S21e). Save `hp7-s21e.log`. Pass when no login file exists in the relayed home and its `projects` resolves to the plan home's.
- [ ] Lane 6. Run `s22_relay.py` (S22). Save `hp7-s22.log`. Pass when the statuses read 401, 401, 400, 400, 400, 400, refused, 404 and forwarded with the query string, and the mismatched served model aborts the stream and moves the family counter.
- [ ] Lane 7. Run `s23_no_key_env.py`, where the fake model scripts a Bash `env` call in bypass mode (S23). Save `hp7-s23.log`. Pass when only the relay URL and grant secret appear and no key value is in the transcript or the QMX home.
- [ ] Lane 8. Run `s24_usage_once.py` with scripted usage on the fake model (S24 key half). Save `hp7-s24.log`. Pass when `RunIndex` equals the relay sum with one row per upstream request.
- [ ] Lane 9. Run `s41_model_ids.py` against the relay with a Kimi grant (S41 relay half). Save `hp7-s41.log`. Pass when an id outside the tier set gets 400 and `kimi-k3[1m]` and a tier alias pass.
- [ ] Lane 10. Run `s17_secrets.py` over the QMX home, logs, transcripts and journal for every key value lane 2 used (S17). Save `hp7-s17.log`. Pass when no value is found.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to the first streamed byte of a `say ok` turn on OpenRouter.
- [ ] Probe. Five direct runs with the base URL set to OpenRouter, as trunk has no relay, and five through the relay at head, interleaved.
- [ ] Baseline. Record the direct median first.
- [ ] Rule. Fail when the relay median exceeds the direct median by more than 150 ms.

**Review gate.** None. HP7 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA, with `/interrogate` findings on the relay triaged.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Enforce the money rule and the credential guards (HP8)

**Depends on.** HP7, for `fake_model.py` and the relayed launch.

**Files.**

- [ ] Create `src/qma/harness/money.py` (gate, adapter, deny rules, path normalizer, surface check and posture types) and `src/qma/harness/tools.py` (`Effect`, `ToolDef`, `AGENT_OPERATIONS`, `Grants`, `tool_defs`, `build_server`, `gate_rules`, `vet_mcp_servers`), with `tests/test_money.py` and `tests/test_tools.py`.
- [ ] Edit `launch.py` (hooks, `disallowed_tools`, `mcp_servers`), `chat.py` (`_connect` steps 5 and 7) and `qmx-control/src/qmx_control/service.py` (`SettingsSection` gains `agents`).
- [ ] Create `scripts/live/qma/s06_money.py`, `s06a_gate_alone.py`, `s06b_rules_alone.py`, `s21_canary.py`, `s21ab_layers.py`, `s28_effects.py`, `s35_external_mcp.py` and `s38_timeout.py`.

**Build.**

- [ ] Write `money.py` and `tools.py` as the sketch states. The gate calls `qma.core.barriers.money_path.match_money_path_act`, and the surface check calls `qma.core.barriers.descriptors.check_descriptor`.
- [ ] Fill `AGENT_OPERATIONS` as an explicit allow-list from `qmx_control.server.OPERATIONS` that leaves out `settings_put` and `backup_weekly`. Add a test that fails when an op with `destructiveHint` is declared as anything but `MANAGE`.

**You see.**

- [ ] In bypass mode, a Bash call to `keyring.get_password('QMX/ctrader', 'ctrader')` yields a deny block that names the money rule, and the broker log shows no connection.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_money.py` gains a literal verdict table of about thirty inputs, covering mixed case, relative paths, `~`, `$HOME`, `%USERPROFILE%`, `$CLAUDE_CONFIG_DIR`, Monitor commands and an exception inside `gate`, plus literal `deny_rules` strings in `//c/...` form. `test_tools.py` gains the three S28 build refusals. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Register a tool named `place_order` against trunk's `check_descriptor` and against the head `build_server`. Save `hp8-regression.log`. Pass when both refuse it.
- [ ] Lane 2. Run `s06_money.py` in bypass mode on the plan, with the mixed-case keyring read, a Monitor command naming a broker host and an Edit of `settings.toml` (S6). Save `hp8-s06-bypass.log`. Pass when each call is denied and the broker log shows no connection.
- [ ] Lane 3. Run the same calls inside a native sub-agent (S6). Save `hp8-s06-agent.log`. Pass when each is denied inside the sub-agent.
- [ ] Lane 4. Run `git status` and `ls` in his QMX repo in bypass mode (S6 negative case). Save `hp8-s06-neg.log`. Pass when both run and return output.
- [ ] Lane 5. Run `s06a_gate_alone.py` on the fake model (S6a). Save `hp8-s06a.log`. Pass when the hook denies every call.
- [ ] Lane 6. Run `s06b_rules_alone.py` (S6b). Save `hp8-s06b.log`. Pass when a rule in `//c/...` form denies every path call and the rendered rules are printed.
- [ ] Lane 7. Run `s21_canary.py` on the fake model with throwaway homes, in default mode, in bypass mode and inside a sub-agent (S21). Save `hp8-s21.log`. Pass when every read attempt is denied, the canary appears nowhere, and the relay saw no unknown bearer.
- [ ] Lane 8. Run `s21ab_layers.py` (S21a, S21b). Save `hp8-s21ab.log`. Pass when the rules alone deny every Read, Grep and Glob on a login file, and the hook alone denies every literal, `$CLAUDE_CONFIG_DIR`, `~` and relative form.
- [ ] Lane 9. Run `s28_effects.py` and `s35_external_mcp.py` (S28, S35). Save `hp8-s28-s35.log`. Pass when the three tools refuse the build, and the external `submit_order` server is refused at vetting with a `needs_you` block and is absent from `get_mcp_status()`.
- [ ] Lane 10. Run `s38_timeout.py` (S38). Save `hp8-s38.log`. Pass when the sleeping test gate blocks the Bash call and the Edit with an error naming the timeout, and the real gate's latency with three fake-model chats streaming is recorded.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Gate latency per tool call, from the hook input to its output.
- [ ] Probe. Two hundred scripted calls on the fake model with three chats streaming. Trunk has no gate on this path, so record that and measure head only.
- [ ] Baseline. Record that trunk lacks the gate, then the head p50 and p99.
- [ ] Rule. Fail when the p99 exceeds 50 ms, which is far below `GATE_TIMEOUT_S`.

**Review gate.** None. HP8 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA, with `/interrogate` findings on the gate triaged.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Answer approvals through the operator's route (HP9)

**Depends on.** HP8.

**Files.**

- [ ] Edit `chat.py` (`_can_use_tool`, `AskId`, the answer types, `Grants` recording, the bounded wait for unattended chats), `harness.py` (`answer`), `routes.py` (POST `/api/approvals/{ask_id}`) and `home.py` (`remember_rule` wired).
- [ ] Create `tests/test_answers.py` and `scripts/live/qma/s05_permissions.py`, `s15_event_wire.py`, `s20_live_edit.py`, `s29_approvals.py`, `s29a_grants_alone.py`, `s33_one_writer.py` and `op_checks_3_to_5.py`.

**Build.**

- [ ] Replace the HP6 floor with the sketch's `_can_use_tool`. It parks a future, writes the `permission` block, waits, and records a `Grant` for the exact final input on AllowOnce of an asking QMX tool.
- [ ] AllowAlways on a built-in tool calls `remember_rule` and hands the rule back with destination `session`. AllowAlways on an asking QMX tool returns `invalid`.

**You see.**

- [ ] After two AllowOnce answers through `POST /api/approvals/{ask_id}`, `hello.txt` holds "goodbye", and a second answer to the same ask returns `already_answered`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_answers.py` gains literal `AnswerStatus` cases for resolved, already_answered, expired, invalid and unknown, and a case that a grant is consumed once. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk answers asks only through the stdin of `copilot_build_app.py`. Record that, and run operator checks 3 and 4 on the plan through `op_checks_3_to_5.py`. Save `hp9-checks-3-4.log`. Pass when `hello.txt` holds "goodbye" after the allowed steps, and still exists after the rejected delete.
- [ ] Lane 2. Run `s05_permissions.py` on the fake model (S5). Save `hp9-s05.log`. Pass when push is denied, rm asks, echo runs, plan mode blocks the write, and the remembered rule takes effect in the next chat.
- [ ] Lane 3. Run `s33_one_writer.py` (S33). Save `hp9-s33.log`. Pass when the `settings.toml` diff is exactly the new rule in `[claude] permissions.allow`.
- [ ] Lane 4. Run `s15_event_wire.py` on the fake model (S15). Save `hp9-s15.log`. Pass when `text`, `tool`, `plan`, `agents` and `permission` blocks arrive in order, the second answer is `already_answered`, the answer after a restart is `expired`, and all 50 concurrent answers resolve.
- [ ] Lane 5. Run `s29_approvals.py` on the fake model (S29). Save `hp9-s29.log`. Pass when one unsigned row exists, the replay and the changed call each ask again, the `[claude]` allow rule does not let it run, AllowAlways returns `invalid`, Reject writes no row, and the broker log shows no connection.
- [ ] Lane 6. Run `s29a_grants_alone.py` (S29a). Save `hp9-s29a.log`. Pass when the replay reaches the handler and is refused for a missing grant.
- [ ] Lane 7. Run operator check 5 on the plan through `op_checks_3_to_5.py`. Save `hp9-check5.log`. Pass when positions show, both order requests are refused with the money rule named, and the broker log shows no new order.
- [ ] Lane 8. Script an AskUserQuestion call on the fake model and answer it with `Answers`. Save `hp9-question.log`. Pass when the `question` block resolves and the next request carries the chosen answer.
- [ ] Lane 9. Run `s20_live_edit.py` on the plan with `TestMode(gate_hook=False, deny_rules=False)`, so agent Bash can write the DESIGN S20 keys into `settings.json` in both homes mid-chat (S20 first half). Save `hp9-s20.log`. Pass when the next request still runs on the plan, through no proxy and with no new rule, and the ConfigChange result is recorded.
- [ ] Lane 10. Run the Bash case of `s12_interrupt.py`, a 30 s sleep that is approved and then interrupted (S12). Save `hp9-s12.log`. Pass when the turn ends and no sleep process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from the ask to its `permission` block on the SSE stream, and from the answer POST to the tool starting.
- [ ] Probe. Twenty scripted asks on the fake model at head. Trunk has no answer route.
- [ ] Baseline. Record that trunk lacks the route, then the head p50 and p95 for both legs.
- [ ] Rule. Fail when the p95 of either leg exceeds 500 ms.

**Review gate.** None. HP9 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Show plan usage and stop paid overage (HP10)

**Depends on.** HP9.

**Files.**

- [ ] Create `src/qma/harness/usage.py` (`UsageLedger`, `BackgroundCap`, `UsagePage`) and `tests/test_usage.py`.
- [ ] Edit `project.py` (`Limits`, `TurnUsage`), `chat.py` (`TurnUsage` journaled for plan chats only, `on_plan_limits`), `harness.py` (`usage`, hard-stop interrupts) and `routes.py` (GET `/api/usage`).
- [ ] Create `scripts/live/qma/s10_usage.py`, `s18_ram.py` and `s24_usage_plan.py`.

**Build.**

- [ ] Write `usage.py` as the sketch states. The hard stop covers any `overage` window that is not `rejected` and any `credits_required` fact.
- [ ] Use the HP0 `/usage` finding for the meter. If `/usage` reaches Python, a non-verbatim meter chat refreshes the reading. Otherwise the page says the cap acts on the last reading.

**You see.**

- [ ] `GET /api/usage` returns the plan windows with `as_of`, the token sums per profile, the cap 0.5, the cap note and `hard_stop`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_usage.py` gains cases for newest-wins merging, a replayed older fact, expiry on read, both hard-stop triggers and `BackgroundCap.allows` at and above the fraction. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk's `RunIndex.refresh` sums `model_call` costs. Run ten plan turns at head and refresh `RunIndex`. Save `hp10-runindex.log`. Pass when there is one row per turn and the sum equals the `ResultMessage` costs within 0.0001.
- [ ] Lane 2. Run `s10_usage.py` for the event count and the `/usage` shape (S10). Save `hp10-s10.log`. Pass when both are recorded and match HP0's finding.
- [ ] Lane 3. Feed a recorded `overage` event to the ledger in-process, then send on the plan (S10). Save `hp10-overage.log`. Pass when the send is refused and a running plan chat is interrupted.
- [ ] Lane 4. Feed a `credits_required` fact the same way. Save `hp10-credits.log`. Pass when the send is refused and a running plan chat is interrupted.
- [ ] Lane 5. Read `GET /api/usage`. Save `hp10-page.log`. Pass when it holds every field in **You see.** and the note says the cap acts on the last reading.
- [ ] Lane 6. Run `s24_usage_plan.py`, ten plan turns plus one relayed chat (S24 plan half). Save `hp10-s24.log`. Pass when the plan has one row per turn and the relayed chat is counted once.
- [ ] Lane 7. Run `s18_ram.py` on harness chats through the pid files (S18). Save `hp10-s18.log`. Pass when the idle and busy working sets are recorded and are within 25% of HP0's numbers.
- [ ] Lane 8. Record a `Limits` fact whose `resets_at` has passed, then read the page. Save `hp10-expiry.log`. Pass when the fact is gone from the page.
- [ ] Lane 9. Compare the page's five-hour utilization with the CLI's own `/usage` text in a plan chat (operator check 12, automated part). Save `hp10-check12.log`. Pass when the two are within 5 points, or the lane records that `/usage` does not reach Python.
- [ ] Lane 10. Replay an older `Limits` fact after a newer one in-process. Save `hp10-merge.log`. Pass when the newer fact stays on the page.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `GET /api/usage` with 1,000 `model_call` events in the journal.
- [ ] Probe. Twenty requests at head. Trunk has no usage route.
- [ ] Baseline. Record that trunk lacks the route, then the head p95.
- [ ] Rule. Fail when the p95 exceeds 200 ms.

**Review gate.** None. HP10 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Cap live chats and run background chats safely (HP11)

**Depends on.** HP10.

**Files.**

- [ ] Edit `chat.py` (prompt kind rules, `verbatim_prompts`, `idle_seconds`), `harness.py` (`ChatTableFull`, eviction, `_reap`, Background interrupts on the cap) and `launch.py` (limits for Background chats).
- [ ] Create `tests/test_table.py` and `scripts/live/qma/s25_untrusted.py`, `s31_chat_cap.py`, `s32_reaping.py` and `s39_unattended.py`.

**Build.**

- [ ] Read `max_live_chats` (default 4), `idle_reap_seconds`, `unattended_ask_seconds` and `background_cap` (default 0.5) from `settings.toml [budgets]`.
- [ ] Refuse `InjectedText` into an Interactive chat with `UntrustedPrompt`. Launch Background and Child chats with `verbatim_prompts=True` and the `[budgets]` turn and spend limits.
- [ ] At `max_live_chats`, close the least recently used idle chat, or raise `ChatTableFull` with a `needs_you` block that names the busy chats. Nothing queues.

**You see.**

- [ ] With the cap at 2 and two chats mid-turn, a third send returns 409 and a `needs_you` block names both busy chats.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_table.py` gains cases for eviction order, `ChatTableFull`, `idle_seconds` staying 0 while a background task runs, and the prompt-kind table. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk's background work runs on LangGraph in `qmx_agents/tasks.py`. Record that, and run a Background chat with `InjectedText` news on the plan at head. Save `hp11-background.log`. Pass when the turn ends idle and its blocks are stored.
- [ ] Lane 2. Run `s25_untrusted.py` (S25). Save `hp11-s25.log`. Pass when no compaction and no file read happen, the text reaches the model as text, and the Interactive send raises `UntrustedPrompt`.
- [ ] Lane 3. Run the idle case of `s31_chat_cap.py` (S31). Save `hp11-s31-idle.log`. Pass when the idle chat closes and later resumes with recall intact.
- [ ] Lane 4. Run the busy case of `s31_chat_cap.py` (S31). Save `hp11-s31-busy.log`. Pass when the third chat gets `ChatTableFull` with a `needs_you` block.
- [ ] Lane 5. Run `s32_reaping.py` (S32). Save `hp11-s32.log`. Pass when the chat with a running background Bash is not reaped past `idle_reap_seconds`.
- [ ] Lane 6. Run `s39_unattended.py` on the fake model (S39). Save `hp11-s39.log`. Pass when both asks reject and show expired, both chats finish their turns, and the Interactive chat connects.
- [ ] Lane 7. Set `background_cap` below the current plan use and start a Background send (S10 cap part). Save `hp11-cap.log`. Pass when the Background send is refused and an Interactive send still runs.
- [ ] Lane 8. Let an idle chat pass `idle_reap_seconds`, then send to it. Save `hp11-reap.log`. Pass when it was closed and the send resumes the same session id.
- [ ] Lane 9. Dump the options of a Background chat and an Interactive chat. Save `hp11-options.log`. Pass when only the Background chat has `verbatim_prompts`, `max_turns` and `max_budget_usd` set.
- [ ] Lane 10. Hit the plan hard stop with a Background chat running, in-process. Save `hp11-hardstop.log`. Pass when the Background chat is interrupted and shows a `needs_you` block with the reason.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to close an idle chat and connect a new one at the cap.
- [ ] Probe. Five evict-and-connect cycles at head. Trunk has no cap. Compare against five plain connects at head.
- [ ] Baseline. Record that trunk lacks the cap, then the plain connect median.
- [ ] Rule. Fail when the evict-and-connect median exceeds the plain connect median by more than 2 s.

**Review gate.** None. HP11 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Switch model, provider and effort with the warning first (HP12)

**Depends on.** HP11.

**Files.**

- [ ] Edit `chat.py` (`quote`, `apply`, `Quote`, `QuoteStale`), `launch.py` (`classify_change`, `resets_cache`), `harness.py` (`quote`, `apply`) and `routes.py` (POST quote and apply).
- [ ] Create `tests/test_change.py` and `scripts/live/qma/s34_quote_stale.py`, `s36_switch_resume.py`, `s37_effort.py`, `s40_background_relaunch.py` and `op_checks_8_9.py`.

**Build.**

- [ ] Write `classify_change` as the sketch states, with the effort path taken from HP0's S37 finding. If `/effort` works headless, effort uses it and the relaunch path for effort goes.
- [ ] Every change goes through a quote. `apply` refuses an unknown id, a stale epoch, or more background tasks than quoted. A relaunch revokes the old grant first and resumes the same session id.

**You see.**

- [ ] A provider switch from the plan to OpenRouter returns a quote whose warning names the uncached tokens, and after apply the next reply runs on OpenRouter in the same transcript.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_change.py` gains a literal `classify_change` table over profile, model, effort, mode, workspace and kind changes, and `resets_cache` cases. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk has no mid-chat switch. Record that, and run operator check 8 through `op_checks_8_9.py` at head. Save `hp12-check8.log`. Pass when the warning comes before the switch, the reply uses tools, and `/api/usage` shows OpenRouter for that reply.
- [ ] Lane 2. Run operator check 9 on one more keyed row. Save `hp12-check9.log`. Pass when check 3's file steps succeed on that provider and `/api/usage` shows it.
- [ ] Lane 3. Run `s34_quote_stale.py` (S34). Save `hp12-s34.log`. Pass when the apply after another turn returns 409.
- [ ] Lane 4. Run `s36_switch_resume.py` from a plan chat with thinking to Kimi (S36). Save `hp12-s36.log`. Pass when the recall answer is right, or the failure and the after-compact retry are recorded as in HP1.
- [ ] Lane 5. Run `s37_effort.py` (S37). Save `hp12-s37.log`. Pass when the next request uses the new effort through the path HP0 chose.
- [ ] Lane 6. Run `s40_background_relaunch.py` (S40). Save `hp12-s40.log`. Pass when the first warning names one task, the first apply raises `QuoteStale`, and the second apply relaunches.
- [ ] Lane 7. Quote SET_MODEL to an id outside the Kimi tier set, to `kimi-k3[1m]` and to a tier alias (S41 quote half). Save `hp12-s41.log`. Pass when the first quote is refused before any relaunch and the other two pass `quote` and the relay alike.
- [ ] Lane 8. Quote a permission-mode change. Save `hp12-mode.log`. Pass when the quote has no warning and the mode applies at once.
- [ ] Lane 9. Quote a model change within the plan. Save `hp12-model.log`. Pass when it uses `set_model` with no relaunch and the warning names the uncached tokens.
- [ ] Lane 10. After a provider relaunch, call the relay with the old grant secret. Save `hp12-revoke.log`. Pass when the old secret gets 401 and the transcript file is the same as before the switch.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from `apply` to the chat being Live again after a provider switch.
- [ ] Probe. Five switches between the plan and OpenRouter at head. Trunk has no switch.
- [ ] Baseline. Record that trunk lacks the switch, then the head median.
- [ ] Rule. Fail when the head median exceeds 10 s. DESIGN guesses a few seconds.

**Review gate.** None. HP12 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Delegate helper work to another provider (HP13)

**Depends on.** HP12.

**Files.**

- [ ] Edit `harness.py` (`_delegate`), `tools.py` (the `delegate` tool as `DOMAIN_WRITE`), `launch.py` (`Child` gets `Agent` in `disallowed_tools`), `money.py` (gate step 1) and `profiles.py` (`delegate_targets`).
- [ ] Create `tests/test_delegate.py` and `scripts/live/qma/s11_helpers.py` and `op_check_11.py`.

**Build.**

- [ ] Write `_delegate` as the sketch states. It refuses a profile outside the allow-list, refuses at once when no chat slot is free, starts a verbatim `Child` chat with `unattended` copied from the parent and its own grant, sends `InjectedText`, and returns the final text.

**You see.**

- [ ] `mcp__qmx__delegate({"profile": "kimi", "prompt": "..."})` returns the child's final text, and a qmx-control child session with `parent_id` exists.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_delegate.py` gains cases for the allow-list refusal, the full-table refusal and `unattended` inheritance. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk's helpers run on Deep Agents. Run operator check 11 on the plan at head through `op_check_11.py`. Save `hp13-check11.log`. Pass when an `agents` block shows the helper start and finish and the answer holds both facts.
- [ ] Lane 2. Ask a helper to start its own helper (S11). Save `hp13-nested.log`. Pass when the nested start is refused at depth 1.
- [ ] Lane 3. Start a background helper and wait (S11). Save `hp13-background.log`. Pass when it finishes with a task notification.
- [ ] Lane 4. Run a helper whose definition names a model (S11). Save `hp13-model.log`. Pass when `model_usage` shows the named model.
- [ ] Lane 5. Delegate to Kimi. Save `hp13-delegate.log`. Pass when the final text returns and the child session has `parent_id` set.
- [ ] Lane 6. Read the child's `get_server_info()` (S11 addition). Save `hp13-child-tools.log`. Pass when it lists neither `Task` nor `Agent` nor `mcp__qmx__delegate`.
- [ ] Lane 7. Script a native sub-agent calling `mcp__qmx__delegate` on the fake model (S11 addition). Save `hp13-subagent.log`. Pass when the call is denied.
- [ ] Lane 8. Fill the chat table, then delegate (S31 last part). Save `hp13-full.log`. Pass when `delegate` returns a tool error at once.
- [ ] Lane 9. Delegate to a profile outside `delegate_targets`. Save `hp13-allowlist.log`. Pass when the call is refused with the allow-list named.
- [ ] Lane 10. Delegate from a Background chat on the fake model and leave the child's ask unanswered. Save `hp13-unattended.log`. Pass when the child's ask expires after `unattended_ask_seconds` and the child launched verbatim.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from the `delegate` call to the child's first upstream request.
- [ ] Probe. Five delegations to Kimi at head. Trunk has no `delegate`.
- [ ] Baseline. Record that trunk lacks the tool, then the head median.
- [ ] Rule. Fail when the head median exceeds 5 s.

**Review gate.** None. HP13 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Measure and show the money posture (HP14)

**Depends on.** HP13.

**Files.**

- [ ] Edit `money.py` (`keyring_inventory`, `exposure_targets`, `run_exposure_probe`, `money_posture`), `harness.py` (`doctor(probe=...)`), `usage.py` (posture and exposure on the page) and `routes.py` (POST `/api/doctor/probe`).
- [ ] Create `tests/test_posture.py` and `scripts/live/qma/s26_posture.py` and `s27_broker_scope.py`.

**Build.**

- [ ] Write the posture functions as the sketch states. Unknown, unmeasured and unreachable all count as `SPEED_BUMP`.
- [ ] Write `s27_broker_scope.py` so it refuses any account id that `settings.toml [brokers]` does not mark as demo. Only the operator runs it. It stores one scope proof per credential under `<home>/state/`.

**You see.**

- [ ] `GET /api/usage` shows the posture `SPEED_BUMP` with each unproven credential named, and a list of what agent Bash can read.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_posture.py` gains a literal `money_posture` table and a case that patches `open` and proves the probe never opens a secret path. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk shows no posture. Read `GET /api/usage` at head. Save `hp14-posture.log`. Pass when it shows `SPEED_BUMP` and names each unproven entry.
- [ ] Lane 2. Add an unknown `qmx/x-test` entry, run `s26_posture.py`, then remove the entry (S26). Save `hp14-s26-unknown.log`. Pass when the posture is `SPEED_BUMP`.
- [ ] Lane 3. Add a known entry the probe cannot reach (S26). Save `hp14-s26-unreachable.log`. Pass when the posture is `SPEED_BUMP`.
- [ ] Lane 4. Run `s26_posture.py` with a scope-proof fixture that covers every entry in the live inventory (S26). Save `hp14-s26-proven.log`. Pass when the posture is `STRUCTURAL`.
- [ ] Lane 5. Load `GET /api/doctor` ten times and watch child processes (S26). Save `hp14-no-probe.log`. Pass when no probe subprocess starts.
- [ ] Lane 6. Call `POST /api/doctor/probe`. Save `hp14-probe.log`. Pass when it runs once and the page lists provider keys and `qmx/chatgpt` among what agent Bash can read.
- [ ] Lane 7. Run the probe against a throwaway home whose login file holds a canary. Save `hp14-canary.log`. Pass when the report never contains the canary text.
- [ ] Lane 8. The operator runs `s27_broker_scope.py` on a demo account (S27). Save `hp14-s27.log`. Pass when each credential has a stored result, refused for scope or not, and no live account id was accepted.
- [ ] Lane 9. Run `s17_secrets.py` over everything this PR's lanes wrote (S17). Save `hp14-s17.log`. Pass when no key value is found.
- [ ] Lane 10. Read `GET /api/doctor`. Save `hp14-doctor.log`. Pass when it holds every line the sketch's `home.doctor` docstring lists, plus the posture and the relay counters.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `POST /api/doctor/probe`.
- [ ] Probe. Five runs at head. Trunk has no probe.
- [ ] Baseline. Record that trunk lacks the probe, then the head median.
- [ ] Rule. Fail when the head median exceeds 10 s.

**Review gate.** None. HP14 is not review-gated.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The root merges with `gh pr merge <number> --merge`.

## Talk to the harness in a temporary console (HP15)

**Depends on.** HP14.

**Files.**

- [ ] Create `src/qma/console.py` and `tests/test_console.py`.
- [ ] Edit `harness.py` and `chat.py` (`export` and `rewind`, two methods beyond the sketch's eleven) and `routes.py` (POST export and rewind, GET a resume list).
- [ ] Create `scripts/live/qma/op_checks_console.py`.

**Build.**

- [ ] Write the console as the sketch's `console.py` states. It uses only the HTTP routes and the SSE streams. It scrubs its own environment first, and `/login` runs the bundled CLI's own login in the plan home with `forceLoginMethod` `claudeai`.
- [ ] Write `export` so it bundles the JSONL, the sub-agent transcripts, approvals and usage into one folder with `sk-ant-` tokens redacted, and `rewind` so it calls the SDK's file rewind for a chosen user message.

**You see.**

- [ ] In the console, "What is in this folder? Summarise the README." prints each tool step and then the answer, as Claude Code does.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_console.py` gains cases that each slash command maps to its route and that an unknown `/` text is sent as text. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk's console is the stdin loop in `copilot_build_app.py`, which needs LangChain providers. Record that, and run operator check 2 in the console at head. Save `hp15-check2.png`. Pass when the console prints the reads and then the answer.
- [ ] Lane 2. Run operator check 1. The ship home is signed in, so run `/login` in a throwaway home only to see the choices. Save `hp15-check1.png`. Pass when the console says it is signed in with the Max plan, `/usage` shows the five-hour window, and the throwaway login offers claude.ai only.
- [ ] Lane 3. Run operator checks 3 and 4. Save `hp15-checks-3-4.png`. Pass when the console asks before each write and command, `hello.txt` holds "goodbye", and the rejected delete leaves it.
- [ ] Lane 4. Run operator check 5. Save `hp15-check5.png`. Pass when positions show, both order requests are refused with the money rule named, and the broker log shows no new order.
- [ ] Lane 5. Run operator check 6. Save `hp15-check6.png`. Pass when only QMX's own skills appear and none of his, such as poteto-mode or the bmad skills.
- [ ] Lane 6. Run operator check 7 by listing his `~/.claude/skills` and `~/.claude/projects` before and after the console session. Save `hp15-check7.log`. Pass when no QMX skill or QMX chat appears in either list.
- [ ] Lane 7. Run operator checks 8 and 9 with `/provider`. Save `hp15-checks-8-9.png`. Pass when the y/N warning shows before each switch and `/usage` shows each provider for its reply.
- [ ] Lane 8. Run operator check 11. Save `hp15-check11.png`. Pass when the console shows a helper start and finish and one answer with both facts.
- [ ] Lane 9. Run operator checks 12 and 13. Save `hp15-checks-12-13.png`. Pass when `/usage` shows tokens, cache reads, the 50% cap and the five-hour percentage, and after a restart `/resume` recalls `hello.txt` without searching.
- [ ] Lane 10. Run `/export`, `/rewind`, `/mode plan`, `/effort high`, `/doctor` and Ctrl+C during a reply. Save `hp15-commands.png`. Pass when the export folder holds a redacted transcript, the rewind restores the file, each switch shows its warning or none, and Ctrl+C ends the turn.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from pressing Enter to the first printed delta.
- [ ] Probe. Five console turns and five `drive.py` turns at head, interleaved. Trunk has no console on these routes.
- [ ] Baseline. Record the `drive.py` median first.
- [ ] Rule. Fail when the console median exceeds the `drive.py` median by more than 300 ms.

**Review gate.** The operator reviews before merge.

- [ ] Copy the lane 1, 3, 4 and 7 screenshots into `D:/QMX-worktrees/qma-ship/review/HP15-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of checks 2 to 4 in the console with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/review/HP15-review.mp4`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The operator clicks merge, or the root runs `gh pr merge <number> --merge` on his written go.

## Open the GPT lane behind the probe (HP16)

**Depends on.** HP15, and HP2 with a viable GPT row. If HP2 fired the stop rule, park this PR and record that the operator decides (01 section 9 question 1).

**Files.**

- [ ] Create `src/qma/gpt/__init__.py`, `translate.py`, `siwc.py` and `probe.py`, with `tests/test_translate.py` over recorded fixtures and `tests/test_probe.py`.
- [ ] Edit `relay.py` (the GPT lane, `probe_grant`, `open_gpt_lane`, `close_gpt_lane`, the consent check in `grant`), `profiles.py` (`GptPlan`), `harness.py` (`open` step 7) and `console.py` (`/login chatgpt`).
- [ ] Create `scripts/live/qma/s16_gpt.py`.

**Build.**

- [ ] Write `qma.gpt` as the sketch states, porting the HP2 client and body rules into `siwc.py` and `translate.py`, with the tool shape and reasoning replay HP2 recorded.
- [ ] Probes P6 and P7 run through `Relay.probe_grant(ProbeRun)`. The stored pass lives under `<home>/state/` and is keyed to the translator's version hash.

**You see.**

- [ ] In the console, `/provider gpt` followed by operator check 3 makes the file steps succeed on GPT.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_translate.py` gains literal request and SSE event cases from recorded fixtures, including dropped fields, the namespace unwrap and `map_error`. `test_probe.py` gains a case that `ProbePassed` refuses construction outside `probe.py`. Run the qma-harness suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Trunk has no GPT lane. Run probe P6 at head, the bundled CLI through the translator with one Bash call. Save `hp16-p6.log`. Pass when the Bash call runs and the turn completes.
- [ ] Lane 2. Run probe P7 through `ClaudeSDKClient` with the GPT profile (S16). Save `hp16-p7.log`. Pass when the turn completes and a `ProbePassed` is stored.
- [ ] Lane 3. Remove the stored pass and call `start_chat` with the GPT profile (S16). Save `hp16-nopass.log`. Pass when it is refused.
- [ ] Lane 4. Change `translate.py` by one byte and read the stored result (S16). Save `hp16-changed.log`. Pass when it reads as None.
- [ ] Lane 5. Reuse a spent probe grant (S16). Save `hp16-spent.log`. Pass when the relay returns 401.
- [ ] Lane 6. Start a Background GPT chat without consent, then with it (S16). Save `hp16-consent.log`. Pass when the first raises `GrantRefused` and the second runs.
- [ ] Lane 7. Read the GPT CLI's init tool list. Save `hp16-toolsearch.log`. Pass when tool search is off.
- [ ] Lane 8. Run operator check 10 in the console, with the operator approving "QMA" if the stored session expired. Save `hp16-check10.png`. Pass when check 3's file steps succeed on GPT, and the operator confirms that ChatGPT's usage page lists QMA.
- [ ] Lane 9. Read `/usage` after the GPT turns. Save `hp16-usage.png`. Pass when the GPT row shows the translator's token count.
- [ ] Lane 10. Run `s17_secrets.py` for the SIWC access and refresh token values. Save `hp16-s17.log`. Pass when no value is found.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time to the first streamed byte of a hello through the GPT lane.
- [ ] Probe. Five runs at head, spaced one minute apart. Trunk has no lane, so HP2's direct P2 median is the reference.
- [ ] Baseline. Read the HP2 median from `FINDINGS.md` first.
- [ ] Rule. Fail when the head median exceeds the HP2 median by more than 500 ms.

**Review gate.** The operator reviews before merge.

- [ ] Copy the lane 8 and 9 screenshots into `D:/QMX-worktrees/qma-ship/review/HP16-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of `/provider gpt` and check 3 in the console with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/review/HP16-review.mp4`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA, with `/interrogate` findings on the translator triaged.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The operator clicks merge, or the root runs `gh pr merge <number> --merge` on his written go.

## Rerun every check and hand the console to the operator (HP17)

**Depends on.** HP15, and HP16 merged or parked.

**Files.**

- [ ] Create `scripts/live/qma/run_all.py` and `scripts/live/qma/test_run_all.py`.
- [ ] Create `qmx-agents/packages/qma-harness/docs/SIGNOFF.md`.

**Build.**

- [ ] Write `run_all.py`. It runs every `s*.py` check in DESIGN section 5 order, skips S16 when HP16 is parked and says so, and prints one PASS or FAIL table.
- [ ] Write `SIGNOFF.md` with the `run_all.py` table, the departures from vanilla Claude Code that `/doctor` lists (DESIGN open question 15), the money posture, and the open items in Appendix C.

**You see.**

- [ ] `run_all.py` prints 0 FAIL, and the operator writes in chat that the harness is signed off.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_run_all.py` gains a case that one failing check script makes `run_all.py` exit non-zero and name it. Run `uv run --no-sync python -m pytest scripts/live/qma/test_run_all.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run each `s*.py` script one by one at trunk, then `run_all.py` at head. Save `hp17-regression.log`. Pass when both give the same PASS set.
- [ ] Lane 2. Run `run_all.py` on Windows. Save `hp17-run-all.log`. Pass when it prints 0 FAIL.
- [ ] Lane 3. The operator runs operator checks 1 to 4 in the console in his default QMX home, after his own `/login` there. Save `hp17-op-1-4.png`. Pass when each row's pass column holds.
- [ ] Lane 4. The operator runs operator checks 5 to 7. Save `hp17-op-5-7.png`. Pass when each row's pass column holds.
- [ ] Lane 5. The operator runs operator checks 8 and 9. Save `hp17-op-8-9.png`. Pass when each row's pass column holds.
- [ ] Lane 6. The operator runs operator check 10 if HP16 merged. Save `hp17-op-10.png`. Pass when its pass column holds, or HP16 is parked and the GPT row is hidden.
- [ ] Lane 7. The operator runs operator checks 11 to 13. Save `hp17-op-11-13.png`. Pass when each row's pass column holds.
- [ ] Lane 8. Show the departures list from `/doctor` to the operator. Save `hp17-departures.png`. Pass when he has read it and it matches `SIGNOFF.md`.
- [ ] Lane 9. Hash every file under his real `~/.claude` before and after the sign-off session, read-only. Save `hp17-claude-home.log`. Pass when nothing QMX wrote appears and no file changed because of QMX.
- [ ] Lane 10. Run the `run_all.py` checks that need no plan login, on the fake model and key providers, in a Linux container if `docker` runs on this PC (BACKLOG B44 seed). Save `hp17-linux.log`. Pass when they pass, or the lane records that Docker is not available.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `run_all.py`.
- [ ] Probe. One run at trunk using the scripts one by one, and one run of `run_all.py` at head.
- [ ] Baseline. Record the trunk total first.
- [ ] Rule. Fail when the head run exceeds 60 minutes, so a rerun fits in one plan window, or exceeds the trunk total by more than 10%.

**Review gate.** The operator reviews before merge.

- [ ] Copy the lane 3 to 8 screenshots into `D:/QMX-worktrees/qma-ship/review/HP17-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of the operator's check 2 and check 5 in the console with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/review/HP17-review.mp4`.
- [ ] Post the screenshots, the video and `SIGNOFF.md` in chat. Stop at merge-ready. Wait for the operator's click and his sign-off message.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] The operator clicks merge, or the root runs `gh pr merge <number> --merge` on his written go. Quote his sign-off in `decisions.tsv`, because `DELETION-PLAN.md` starts from it.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report autopilot-full names. Give the queue with each PR's state and merge SHA, each verdict, what was parked and why, the open operator gates, and the trail at `D:/QMX-worktrees/qma-ship/decisions.tsv`.
- [ ] List every harness worktree and `qma/*` branch for his go. Delete none without it.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. The coding session runs HP0, HP1 and HP2 first, and each later PR reads their `FINDINGS.md`. This table maps each open question to the probe that settles it.

| Open question | Settled by | Feeds |
|---|---|---|
| SDK pin with a `win_amd64` wheel and CLI 2.1.248 or later (S1) | HP0 lane 2 | HP4 |
| Auth method string for a Max login, and whether `forceLoginMethod` hides the Console choice (DESIGN question 6) | HP0 lane 3 | HP5 |
| Does the CLI run under an allow-listed env on Windows, Git Bash included (empty or scrubbed routing env) | HP0 lane 4 | HP4, HP5 |
| Does ConfigChange fire with `setting_sources=[]`, does a plugin in a home load, how long is the inline settings argument (DESIGN questions 3 to 5) | HP0 lane 5 | HP5, HP9 |
| Does `/usage` reach Python (S10), does `/effort` work headless (S37) | HP0 lanes 6 and 7 | HP10, HP12 |
| Does a timed-out PreToolUse callback block the call (S38), does `verbatim_prompts` stop dispatch (S25) | HP0 lane 8 | HP8, HP11 |
| RAM per CLI, idle and busy (S18, DESIGN question 11) | HP0 lane 9 | HP11 default `max_live_chats` |
| Does Windows App Control let a venv console-script `.exe` run as `cli_path` | HP0 lane 10 | HP4 |
| Tool calls, caching, thinking, WebSearch and tool search on GLM, Kimi, DeepSeek, MiniMax, Meta Muse and OpenRouter (S8) | HP1 lanes 2 to 7 and 10 | HP7 quirks |
| Cross-provider resume of a plan session with thinking (S36, DESIGN question 9) | HP1 lane 8 | HP12 |
| Does a base URL without its own token send the login (02a trap 7) | HP1 lane 9, on a canary only | HP7 types |
| GPT on the ChatGPT plan, P0 to P5 (DESIGN question 10) | HP2 | HP16 or its park |

Unproven after the probes, by design. P6 and P7 need the relay, so HP16 settles them. Broker credential scope (S27) needs the operator on a demo account in HP14. macOS has no test machine, so every macOS row stays unverified. Linux runs only where Docker is available.

## Appendix B. Alternatives rejected

- **Autopilot-stack.** The rule at the end of `playbooks/autopilot-stack.md` sends sequenced work to the stack when the operator wants review before landing or withholds merge authority. Here he granted merge authority on `rebuild/base` in the project rules, he does not review code, and his gate is the console sign-off. Autopilot-full step 3 covers sequenced work by merge-then-branch, so each PR is built and verified on real trunk. A stack of eighteen PRs would rebase from the bottom on every fix and void verdicts at each rewrite. That costs plan usage he does not have.
- **One probe PR.** The three probe sets need three different credentials and two operator clicks. One PR would wait on the slowest click, and its evidence would mix three questions. Three PRs, which one agent can run back to back, keep each verdict small.
- **Money gate before the relay.** The relay PR adds `fake_model.py`, which lets the gate, approval and canary lanes script tool calls with no plan turns. Building the relay first cuts those lanes' plan usage to near zero. Until HP8 lands, the HP6 floor rejects every call that would ask, so no chat runs Bash without the operator's approval except the scripted bypass lanes on the fake model.
- **A separate `qma-gpt` distribution.** `relay.py` imports `translate.py`, and `probe.py` calls the relay, so two distributions would import each other. One `qma-harness` distribution holds every `qma.*` module DESIGN names, and the AST rules in `test_import_rules.py` keep the boundaries.
- **Re-export shims for the moved guard modules.** The 2026-10-13 plan kept `qmx_agents/guards/journal.py` as a shim. HP3 migrates every caller and leaves no shim, per the migrate-callers-then-delete principle.
- **import-linter.** It is not in the repo. An AST test enforces the same rules without a new dependency.
- **The two-engine plan of 2026-10-13.** The operator ruled one engine on 2026-10-13 at 18:32 (R1). Its OpenAI units are gone, and its other units were redesigned in DESIGN.

## Appendix C. Risks

- **App Control blocks the launcher shim (HP4).** Windows App Control already blocks `poe.exe` and `pyright` under nested venvs (comment in `qmx-agents/pyproject.toml`). HP0 lane 10 measures it first. If the shim is blocked, the HP4 owner reports it before building on it, and the coordinator brings the operator a choice with a recommendation.
- **uv_build module lists (HP4).** `qma-harness` lists six `qma.*` modules. If `uv_build` refuses a list, the owner splits the entry modules into a second distribution and records why.
- **Plan usage (all PRs).** Builder sessions draw far more of the plan than the lanes do. At most two builders run at once, lanes use the `haiku` tier, and lanes pause at 50% of the five-hour window.
- **Provider keys missing (HP1, HP7, HP12, HP13).** A missing key turns a row into `NO KEY`. Kimi stands in for "a keyed provider" in several lanes. The owner substitutes the first keyed row and records it.
- **Money is a speed bump in month one (HP8, HP14).** The trading node shares this PC (R25), so the posture stays `SPEED_BUMP`. The operator accepted that on 2026-10-13 (R21). The usage page says so.
- **S27 can place a demo order (HP14).** If a credential can trade, the scope check sends an order on the demo account. The script refuses non-demo account ids, and only the operator runs it.
- **The GPT route may fail (HP2, HP16).** The stop rule parks HP16, and the operator decides whether GPT waits.
- **Cross-provider resume may fail (HP1, HP12).** Then a switch forks with a summary, which is DESIGN question 9's fallback. The HP12 owner applies the HP1 finding.
- **Windows command-line length (HP5).** If `[claude]` grows past 32,767 characters, the only native fallback is a settings file path an agent could write. Doctor reports the length, and HP5 lane 8 records the headroom.
- **No macOS machine (all PRs).** macOS rows stay unverified. The Linux rows run only in Docker.

## Appendix D. Links and reading list

- The contract is `research/one-engine/architect/DESIGN.md`, `SYNTHESIS.md` and `sketch/qma/`. Every owner reads the sketch file for each module its PR names.
- Rulings live in `research/one-engine/01-requirements.md` section 2. Backlog ids live in `research/one-engine/03-gaps.md` and `BACKLOG.md`. Operator checks and agent checks live in `research/one-engine/04-baseline.md` sections 4 and 5.
- Code seams and import traps live in `research/one-engine/how/HOW-one-engine.md`. The code is read-only at `D:/QMX-worktrees/harness-survey`, which is `origin/rebuild/base` at `4eac8f69`.
- The interrogate verdict is `research/one-engine/interrogate/VERDICT.md`.
- `UI-NOTES.md` is for the later UI session. The console in HP15 is its reference client.
- HP3 gets `C:/Users/Mubarak/.claude/skills/how/SKILL.md` before editing, because of the import traps. HP7, HP8 and HP16 get `C:/Users/Mubarak/.claude/skills/interrogate/SKILL.md` on the diff, run by the coordinator, because the relay, the gate and the translator carry the structural stops. Reviewers run on `opus` unless the operator asks for Fable.
- The coordinator keeps its trail per `C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md` in `D:/QMX-worktrees/qma-ship/decisions.tsv`. Each owner returns its own `decisions.tsv` uncommitted.
- Never read `tracker/qma-v2/archive/` as the plan.

## Appendix E. Sizing

These numbers are estimates from the lane designs, not measurements. Effort is focused agent hours for the owner, excluding the coordinator's verification, which adds about one hour per PR. Plan turns are first-pass live turns on the Claude plan, mostly on the `haiku` tier. Key calls go to provider keys, and GPT calls go to the ChatGPT plan.

| PR | Effort (h) | Plan turns | Key calls | GPT calls | Back-to-back group |
|---|---|---|---|---|---|
| HP0 | 4 | 14 | 0 | 0 | A |
| HP1 | 3 | 4 | 60 | 0 | A |
| HP2 | 4 | 0 | 0 | 10 | A |
| HP3 | 3 | 0 | 0 | 0 | none |
| HP4 | 5 | 5 | 0 | 0 | B |
| HP5 | 4 | 0 | 0 | 0 | B |
| HP6 | 6 | 20 | 0 | 0 | none |
| HP7 | 6 | 2 | 40 | 0 | none |
| HP8 | 5 | 15 | 0 | 0 | none |
| HP9 | 5 | 15 | 0 | 0 | none |
| HP10 | 3 | 25 | 2 | 0 | C |
| HP11 | 4 | 8 | 0 | 0 | C |
| HP12 | 4 | 12 | 15 | 0 | D |
| HP13 | 3 | 8 | 10 | 0 | D |
| HP14 | 3 | 2 | 0 | 0 | none |
| HP15 | 5 | 30 | 10 | 0 | none |
| HP16 | 7 | 0 | 0 | 30 | none |
| HP17 | 3 | 60 | 30 | 10 | none |
| Total | 77 | 220 | 167 | 50 | |

- **Number of PRs.** Eighteen harness PRs, three of them probes. `DELETION-PLAN.md` adds three deletion PRs run by its own program and one QMB hand-off.
- **Effort.** About 77 owner hours plus about 18 coordinator hours. With one builder at a time and plan windows, that is roughly two working weeks of wall time (a guess).
- **Live Claude turns.** About 220 plan turns on the first pass. Fix rounds that rerun lanes add an estimated 30%, so plan for about 290. The fake model keeps the gate, approval, canary and cap lanes off the plan.
- **Back to back.** One agent can run group A (HP0, HP1, HP2), because the three probe sets share `common.py` and the CLI setup. Group B (HP4, HP5) shares the stdlib foundations and the workspace edits. Group C (HP10, HP11) shares the ledger and the chat table. Group D (HP12, HP13) shares relaunch and child-chat code. Each group still opens one PR per id and gets one verdict per PR. Every other PR gets a fresh owner.
