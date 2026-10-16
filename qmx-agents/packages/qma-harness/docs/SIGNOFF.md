# QMA harness sign-off

This page is the hand-over for the QMA v2 harness, HP0 to HP17. It holds the result of every live check, the full CI run, the money posture, the ways QMA departs from vanilla Claude Code, the open risks, and the checks only the operator can do. The harness is signed off when the operator has done those checks and writes in chat that it is signed off.

Status on 2026-10-16: **waiting for the operator.** The checks that need him are listed under "What the operator still does". Every other check ran on his PC at night.

## Live checks: `run_all.py`

`scripts/live/qma/run_all.py` runs every `s*.py` check in DESIGN section 5 order and prints one table. It ran at HP17 head 26e61f94, on Windows, on the ship home's plan login on haiku, with a fresh scratch folder (`--scratch D:/Temp/qma-live-hp17`). OpenRouter turns shared one spend ledger capped at $0.045. The logs are in `D:/QMX-worktrees/qma-ship/evidence/hp17/`, and each check's raw output is in `run_all/<check>.out` there. Every path below that starts with `evidence/` is under `D:/QMX-worktrees/qma-ship/`.

Run 2:

| Check | Script | Verdict | Seconds | Note |
|---|---|---|---|---|
| S1 | s01_install.py | PASS | 4 |  |
| S2 | s02_login.py | PASS | 7 |  |
| S3 | s03_tools.py | PASS | 15 |  |
| S4 check2 | s04_vanilla.py | PASS | 10 |  |
| S5 | s05_permissions.py | PASS | 17 |  |
| S6 bypass | s06_money.py | PASS | 25 |  |
| S6 agent | s06_money.py | FAIL | 35 | exit 1: 01:48:20 FAIL |
| S6 neg | s06_money.py | PASS | 18 |  |
| S6a | s06a_gate_alone.py | PASS | 9 |  |
| S6b | s06b_rules_alone.py | PASS | 9 |  |
| S7 | s07_isolation.py | PASS | 12 |  |
| S8 rows | s08_providers.py | FAIL | 92 | exit 1: 01:50:40 FAIL |
| S9 | s09_leak.py | PASS | 8 |  |
| S10 meter | s10_usage.py | PASS | 15 |  |
| S10 overage | s10_usage.py | PASS | 66 |  |
| S10 credits | s10_usage.py | PASS | 29 |  |
| S10 merge | s10_usage.py | PASS | 6 |  |
| S10 expiry | s10_usage.py | PASS | 9 |  |
| S10 restart | s10_usage.py | PASS | 6 |  |
| S11 nested | s11_helpers.py | PASS | 8 |  |
| S11 background | s11_helpers.py | PASS | 9 |  |
| S11 model | s11_helpers.py | PASS | 8 |  |
| S11 kimi | s11_helpers.py | PASS | 14 |  |
| S11 tools | s11_helpers.py | PASS | 10 |  |
| S11 subagent | s11_helpers.py | PASS | 9 |  |
| S11 full | s11_helpers.py | PASS | 9 |  |
| S11 allowlist | s11_helpers.py | PASS | 9 |  |
| S11 unattended | s11_helpers.py | PASS | 15 |  |
| S12 | s12_interrupt.py | PASS | 34 |  |
| S12 bash | s12_interrupt.py | PASS | 15 |  |
| S13 | s13_compact.py | PASS | 19 |  |
| S14 all | s14_resume.py | PASS | 112 |  |
| S15 wire | s15_event_wire.py | PASS | 11 |  |
| S15 restart | s15_event_wire.py | PASS | 14 |  |
| S15 concurrent | s15_event_wire.py | PASS | 18 |  |
| S15 question | s15_event_wire.py | PASS | 9 |  |
| S16 lanes | s16_gpt.py | PASS | 45 |  |
| S17 | s17_secrets.py | PASS | 4 |  |
| S18 | s18_ram.py | PASS | 24 |  |
| S19 | s19_boot.py | PASS | 8 |  |
| S20 live | s20_live_edit.py | PASS | 15 |  |
| S20 settings | s20_settings.py | PASS | 9 |  |
| S21 | s21_canary.py | FAIL | 15 | exit 1: 02:00:23 FAIL |
| S21ab | s21ab_layers.py | PASS | 11 |  |
| S21c | s21c_egress.py | PASS | 10 |  |
| S21d | s21d_redaction.py | PASS | 21 |  |
| S21e | s21e_relayed_home.py | PASS | 10 |  |
| S22 | s22_relay.py | PASS | 8 |  |
| S23 | s23_no_key_env.py | PASS | 10 |  |
| S24 key | s24_usage_once.py | PASS | 10 |  |
| S24 plan | s24_usage_plan.py | PASS | 25 |  |
| S25 | s25_untrusted.py | PASS | 14 |  |
| S26 unknown | s26_posture.py | PASS | 6 |  |
| S26 unreachable | s26_posture.py | PASS | 6 |  |
| S26 proven | s26_posture.py | PASS | 6 |  |
| S27 | s27_broker_scope.py | SKIP |  | only the operator runs it |
| S28 | s28_effects.py | PASS | 6 |  |
| S29 | s29_approvals.py | PASS | 11 |  |
| S29a | s29a_grants_alone.py | PASS | 11 |  |
| S30 | s30_os_cap.py | PASS | 17 |  |
| S30b | s30b_orphans.py | PASS | 20 |  |
| S31 idle | s31_chat_cap.py | PASS | 13 |  |
| S31 busy | s31_chat_cap.py | PASS | 38 |  |
| S32 | s32_reaping.py | PASS | 56 |  |
| S33 | s33_one_writer.py | PASS | 10 |  |
| S34 | s34_quote_stale.py | PASS | 9 |  |
| S35 | s35_external_mcp.py | PASS | 50 |  |
| S35u | s35u_unattended_external.py | PASS | 31 |  |
| S36 | s36_switch_resume.py | SKIP |  | skipped on the command line |
| S37 | s37_effort.py | PASS | 9 |  |
| S38 | s38_timeout.py | PASS | 53 |  |
| S39 | s39_unattended.py | PASS | 17 |  |
| S40 | s40_background_relaunch.py | PASS | 24 |  |
| S41 | s41_model_ids.py | PASS | 6 |  |

69 PASS, 3 FAIL, 2 SKIP in 22.5 min
FAIL: S6 agent, S8 rows, S21

How to rerun it, from the repo root:

```
cd qmx-agents
uv run --no-sync python ../scripts/live/qma/run_all.py --evidence <evidence folder> --scratch <empty folder> --skip S36
```

Add `--gpt-parked` if the GPT lane is parked, and `--no-login` for a machine with no plan login, keys or keyring (the Linux container lane).

### Rows that are not PASS

Run 2 above gave 69 PASS, 3 FAIL and 2 SKIP in 22.5 minutes, inside the 60-minute rule. Trunk has no `scripts/live/qma`, so there is no trunk total to compare. The three failed rows were run once more (`evidence/hp17-retry/hp17-retry.log`):

- **S8 rows: PASS on retry.** In run 2, deepseek wrote no thinking block on the B4 turn. That is the model's choice. Every other S8 step passed both times.
- **S21: PASS on retry.** Run 2 failed only because two earlier runs' S21c and S21d logs, which print the fake canary by design, sat inside the evidence folder S21 searches. They are now in `evidence/hp17-earlier`.
- **S6 agent: FAIL in run 2 and in the retry. It is now an observation.** Haiku declined, in plain text, to start the sub-agent's keyring read, so the call never reached the gate. A model's refusal should not decide a money row. After the check round, a fake-model row, **S6a agent**, decides it. A fake parent starts a real native sub-agent, and the sub-agent makes the keyring read, the broker-host command and the Edit of settings.toml. All three were denied inside the sub-agent. With the gate alone, the hook denied each one. With the full launch, the hook denied the two Bash calls and a deny rule denied the Edit. settings.toml was unchanged (`evidence/hp17/fix1/hp8-s06a-agent.log`: 7 PASS). The fake profile's CLI offers no Monitor tool, so the broker host is named in Bash. The plan-model S6 agent row now logs a call the model declined as RECORDED, neither PASS nor FAIL. Any call the model does make must still be denied. Its rerun passed: two calls were recorded as declined, and the hook denied the broker command inside the sub-agent (`evidence/hp17/fix1/hp8-s06-agent.log`). Run 2's table is older than both changes.
- **S27: SKIP.** Only the operator runs it (item 10 below).
- **S36: SKIP.** It needs a sonnet plan turn at effort `max`, and its spend guard prices the one Kimi turn at $0.0502, over tonight's $0.05 OpenRouter cap. HP12 measured it (`evidence/hp12/owner-hp12-s36.log`: PASS). Rerun it with a higher `QMA_SPEND_BUDGET` when that spend is fine.

Two passing rows need a note:

- **S12 bash** is flaky. It passed in run 2 and failed in run 1. Sometimes Git Bash's `sleep.exe` outlives an interrupt by more than 5 s, until the chat closes. HP9 logged it as a low.
- **S10 meter** passes because DESIGN S10 only asks to record whether `/usage` reaches Python. Tonight it did not. The CLI's `/usage` reply no longer holds a "Current session: N% used" line, so `Harness.meter` gets no reading from it. Plan rate-limit events still give the five-hour reading, so the usage page and the background cap keep working.

Seven scripts were updated so they match what later PRs built. S3 now asks for a `claude-` model id and names WebFetch. S4 seeds its README. S8 expects tool search off on OpenRouter. S10 reads `/doctor` lines. S21d and S35u answer their asks through the approvals route. S24 counts only its own rows. After run 2, S35u's check was narrowed to the weather tool's own ask, and it passed again (`evidence/hp17-retry/hp17-retry-s35u.log`). Lane 1 (`evidence/hp17/hp17-regression.log`) compares each check's last verdict in the stack's own evidence with run 2. 74 of 84 logs agree, and the log explains each of the other ten.

### Linux container lane

Not run. The `docker` command is installed, but no Docker engine runs on this PC. Starting Docker Desktop was not tried while the operator was away, because it can ask him to accept terms. `evidence/hp17/hp17-linux.log` records it. `run_all.py --no-login` lists the 40 rows that would run there.

## Full CI

Full `just ci` ran once at b2234415, under the CI lock, with every `ANTHROPIC_*` and `CLAUDE*` name unset. Log: `evidence/hp17/full-ci-b2234415.log`.

- Every static gate passed. That needed two fixes first. Six qma-harness test files were not formatted. The package's own lint and strict pyright, which `tools/ci.py` runs with the package config and the workspace tasks skip, had 24 lint and 46 type errors from HP4 to HP16. Each fix is an import order, a wrapped line, an annotation, a cast or a pyright ignore. No behaviour changed, and the 861 qma-harness tests pass.
- The suite table matches clean trunk (`evidence/trunk-4eac8f69-gates-clean.log`) except one row. qmx-apps 6 failures (rclone missing) and qmx-control 1 failure (the long-path test) are the known environment failures. qmx-apps serial had 1 failure trunk did not have: `test_producer_to_consumer_artifact_and_screen_state`. In that run, `uv sync` could not install an example app's lock. The failure is intermittent and did not come back. At head it passed 3 of 3 times in the check round, with a temp folder as long as CI's, with the default one and with a short one. The probable cause is `uv sync` under CI load. HP17 changes nothing in qmx-apps.

## Money posture

The posture is **SPEED_BUMP**. The operator accepted that for the first month on 2026-10-13 (R21), because the trading node shares this PC.

- What holds: agents cannot place, change or close an order. The money gate denies every broker call in every mode, sub-agents included (S6, S6a, and S6a agent, which runs a real native sub-agent on the fake model). The deny rules block reads and writes of QMX settings and the login files (S6b, S21a). `propose_order` asks every time, and an approval is bound to its arguments (S29, S29a). An external MCP server that offers an order tool never launches (S35).
- Why it is still a speed bump: agent Bash can read every `qmx/*` keyring entry, including `qmx/ctrader-client-id` and `qmx/ctrader-client-secret` (HP14). Nothing yet proves those credentials cannot trade. S27 is that proof, and only the operator can run it.
- It becomes STRUCTURAL when every broker credential in the keyring has a stored "refused for scope" proof from S27 (S26 shows the switch).
- **His Claude account has extra usage switched on.** The usage page and `/doctor` both say "extra usage is on for this account". Today it cannot bill, because the account is out of credits (`overage_disabled_reason: out_of_credits`), and the harness stops plan use the moment an overage reading arrives (S10). He should switch extra usage off at claude.ai so the plan can never bill. HP10 found this first.

## Departures from vanilla Claude Code

The console's `/doctor` prints these 19 lines (`DEPARTURES` in `qma/harness/home.py`, DESIGN section 3 and open question 15). Lane 8 checks that the operator has read them and that they match this list.

1. Only the workspace root's CLAUDE.md and AGENTS.md are read, once, into the system prompt append. Parent and subfolder CLAUDE.md files are not loaded.
2. `.claude/rules/` and CLAUDE.local.md are not loaded. `@import` lines stay raw text.
3. `/memory`, `#` quick memory and `/init` edit files that apply only at the next launch, and only at the workspace root.
4. Project settings, project hooks and `.mcp.json` are off.
5. Project skills, commands and agents are off. Only the QMX plugin's load.
6. Auto memory lives in `<qmx_home>/agent-memory/<workspace>/`, one per workspace, shared by every provider.
7. Plan mode may fail to write its plan file, which defaults to a protected Claude home.
8. Always allow is saved to `[claude.remembered."<workspace>"]`, not to the project's local settings file.
9. User settings: only `permissions`, six `env` names, `hooks`, `outputStyle`, `attribution`, `includeCoAuthoredBy`, `alwaysThinkingEnabled`, `language` and `respectGitignore` can be set.
10. Settings edits apply at the next launch, never mid-session.
11. Skills and plugins do not hot-reload. The ConfigChange guard blocks reloads.
12. His personal `~/.claude`, plugins, mods and claude.ai connectors never load.
13. Agent Bash sees an allow-listed environment. Other names need the UI keep list and a restart.
14. No proxy and no corporate CA for plan traffic.
15. Background and Child chats are verbatim: no slash commands, no `@file` reads.
16. Nonessential traffic is off, TodoWrite is on, Workflow is off.
17. `/rewind` file checkpoints do not cross a provider switch (inferred).
18. In the QMX repo, edits under `qmx-agents/plugin/` and Bash naming that folder are denied.
19. Asking QMX tools have no always allow.

What S3 measured tonight under item 16: with nonessential traffic off, QMA chats have no Monitor, DesignSync, PushNotification or Workflow, and they have TaskCreate, TaskGet, TaskList and TaskUpdate. QMA chats also have WebFetch, which vanilla Claude Code on this PC no longer shows. Vanilla's tool list follows the feature flags it downloads, and WebFetch left it between HP6 and HP17 with no QMA change.

## Open items (HARNESS-PLAN Appendix C)

| Risk | Where it stands |
|---|---|
| SDK version probe or trampoline job breaks the launcher (HP4) | Closed. S1 and S30 pass through `qma-cli-launcher.exe`. |
| App Control blocks the launcher shim (HP4) | Closed on this PC. S1 runs the shim. |
| `uv_build` module lists (HP4) | Closed. One `qma-harness` distribution builds. |
| Plan usage | Open, by design. Builders draw most of the plan. Tonight's checks ran on haiku. |
| Provider keys missing | Open. OpenRouter is the only keyed row, so S8 and operator check 9 cover one provider. Every other row reads NO KEY. |
| Money is a speed bump in month one | Open, accepted (R21). See "Money posture". |
| S27 can place a demo order | Open. Only the operator runs S27. It refuses an account not marked demo before it reads any credential. |
| The GPT route may fail (HP2, HP16) | Closed for now. HP16 is in the stack and S16 passes. The ChatGPT usage page check is the operator's (HP16 lane 8). |
| Cross-provider resume may fail (S36) | Not rerun tonight (see "Rows that are not PASS"). HP12 measured it. |
| Windows command-line length (HP5) | Closed. `assert_argv_fits` refuses past 30,000 characters, and S20 records the length. |
| No macOS machine | Open. macOS paths are checked by review only. |

## What the operator still does

Each item says what to run and what passing looks like. Save each screenshot in `D:\QMX-worktrees\qma-ship\evidence\hp17\` under the name given. To capture the console window, set its title first, then grab it with ffmpeg from a second PowerShell window:

```
$Host.UI.RawUI.WindowTitle = 'QMA sign-off'
ffmpeg -f gdigrab -i "title=QMA sign-off" -frames:v 1 D:\QMX-worktrees\qma-ship\evidence\hp17\<name>.png
```

Start the console in his default QMX home (`~/.qmx`). Until the stack merges, run it from the `D:\QMX-worktrees\qma-hp17` worktree. After it merges into `rebuild/base`, run it from a checkout of `rebuild/base`. `C:\Users\Mubarak\Desktop\QMX` is on `main`, which does not have the harness yet. Put the folder the agent works in after `--workspace`:

```
uv run --project qmx-agents --no-sync python -m qma.console --workspace D:\path\to\a\test\folder
```

1. **HP17 lane 9, before anything else.** Hash his real `~/.claude`, read-only, so lane 9 can show QMX wrote nothing there:

   ```
   Get-ChildItem -Recurse -File -Force $HOME\.claude | Get-FileHash -Algorithm SHA256 | Select-Object Hash, Path | Export-Csv D:\QMX-worktrees\qma-ship\evidence\hp17\claude-home-before.csv -NoTypeInformation
   ```

2. **HP17 lane 3, operator checks 1 to 4.** Type `/login` and sign in with his Max plan. Then run checks 1 to 4 from `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/one-engine/04-baseline.md` section 4 (local branch plan/agent-system) (sign-in and `/usage`; "What is in this folder? Summarise the README."; make, show and change hello.txt; delete hello.txt and answer no). Pass: each row's pass column holds. Save `hp17-op-1-4.png`.
3. **HP17 lane 4, operator checks 5 to 7**, from `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/one-engine/04-baseline.md` section 4 (local branch plan/agent-system). Check 5: ask for open positions, ask for a buy order, then ask for the order through the terminal. Both order requests are refused and name the money rule, and cTrader shows no new order. Check 6: "List your skills and slash commands." Only QMX's skills appear. Check 7: close the console, open his normal Claude Code, and type `/skills` then `/resume`. No QMX skill or chat appears. Save `hp17-op-5-7.png`.
4. **HP17 lane 5, operator checks 8 and 9.** `/provider openrouter`, then the check 2 question again. A cost and cache warning shows first, and `/usage` names OpenRouter. Check 9 needs a second keyed provider. OpenRouter is the only one today, so it stays SKIPPED unless he adds a key. Save `hp17-op-8-9.png`.
5. **Revoke QMA in ChatGPT before the GPT check.** Open ChatGPT Settings, Connected apps, and revoke QMA. While HP16 was built, ChatGPT tokens were written to two logs. They were redacted and the stored refresh token has rotated since, but an older token may still be accepted. `/login chatgpt` reuses the stored sign-in, so revoke first. Then the next step's `/login chatgpt` signs in fresh on OpenAI's page.
6. **HP17 lane 6, operator check 10, together with HP16 lane 8.** `/login chatgpt` and approve "QMA" on OpenAI's page. `/provider gpt`, then check 3 with a new file name. Then open ChatGPT Settings, Usage. Pass: the same result as check 3, and **ChatGPT's usage page lists QMA**. Save `hp17-op-10.png`.
7. **HP17 lane 7, operator checks 11 to 13**, from `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/one-engine/04-baseline.md` section 4 (local branch plan/agent-system). A helper counts files while the agent gives the date. `/usage` matches claude.ai Settings, Usage. Close and reopen the console, `/resume`, and ask "What file did we make first?". Save `hp17-op-11-13.png`.
8. **HP17 lane 8.** Type `/doctor` and read the 19 departure lines. Pass: he has read them and they match the list above. Save `hp17-departures.png`.
9. **HP17 lane 9, after the session.** Close the console, hash again into `claude-home-after.csv`, and compare:

   ```
   Get-ChildItem -Recurse -File -Force $HOME\.claude | Get-FileHash -Algorithm SHA256 | Select-Object Hash, Path | Export-Csv D:\QMX-worktrees\qma-ship\evidence\hp17\claude-home-after.csv -NoTypeInformation
   Compare-Object (Import-Csv D:\QMX-worktrees\qma-ship\evidence\hp17\claude-home-before.csv) (Import-Csv D:\QMX-worktrees\qma-ship\evidence\hp17\claude-home-after.csv) -Property Hash, Path | Out-File D:\QMX-worktrees\qma-ship\evidence\hp17\hp17-claude-home.log
   ```

   His own Claude Code sessions change files under `~/.claude/projects` and similar folders while they run. Pass: no changed or new path names QMA, QMX's home, the ship home or a QMA chat, and nothing else changed that his own sessions would not.
10. **HP14 lane 8, the S27 broker scope check.** Only he runs it, because it reads a broker credential. It needs a `[brokers]` cTrader connection in the ship home marked `environment = "demo"`, and a keyring entry holding the `clientId`, `clientSecret` and `accessToken` bundle. The command is in PR #87's body:

   ```
   cd D:/QMX-worktrees/qma-hp14/qmx-agents
   $env:QMA_EVIDENCE_DIR = 'D:/QMX-worktrees/qma-ship/evidence/hp14'
   uv run --no-sync python ../scripts/live/qma/s27_broker_scope.py --account <demo ctidTraderAccountId> --home D:/QMX-worktrees/qma-ship/home
   ```

   If the broker accepts the order, he closes the demo position by hand.
11. **Switch off extra usage** at claude.ai Settings, Usage (see "Money posture").
12. **Review gate.** Copy the lane 3 to 8 screenshots to `D:\QMX-worktrees\qma-ship\review\HP17-review-<slug>.png`. Record 30 to 60 seconds of checks 2 and 5:

    ```
    ffmpeg -f gdigrab -framerate 15 -t 60 -i "title=QMA sign-off" -pix_fmt yuv420p D:\QMX-worktrees\qma-ship\review\HP17-review.mp4
    ```

    Then write in chat that the harness is signed off. `decisions.tsv` quotes that message, because `DELETION-PLAN.md` starts from it.

## Low findings

Every low finding from HP8 to HP17 is in `D:/QMX-worktrees/qma-ship/lows.md`. None blocks the sign-off.
