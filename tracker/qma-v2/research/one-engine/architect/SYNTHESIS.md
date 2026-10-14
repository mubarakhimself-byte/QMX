# Arena synthesis note: one-engine QMA v2 harness

2026-10-14. The design is `DESIGN.md`, the types are in `sketch/qma/`. Candidates: A = `candidate-1-thin-native/`, B = `candidate-2-gateway/`, C = `candidate-3-boundary/`.

## Judge's verdict

`JUDGE.md` scored A 24, C 19, B 18 (of 30) and recommended A as the base. A is the only candidate that passes every hard rule as designed. B loses on the policy rule, because its plan relay sits in the row 02b A calls clearly barred. C loses on operator cost and on scope against 03 GB-7, not on safety. The judge noted A's money score (2) is no better than B's. A's honesty makes it a speed bump the operator accepted, not a proof, so the base ships with a measured posture and a named path to the zone upgrade.

## Base: A, thin native

Kept: its shape, the `Harness` class and its eleven methods, `Profile`, `ChatConfig`, `classify_change`, `ChatRecord`, `AskId`, `Answer`, `Quote`, `Verdict`, `Fact`, the `delegate` tool, the deletion order, and the import-linter rules. Callers still never see an SDK type, a CLI flag or an env variable.

## Grafts

| # | Graft | From | Where it landed |
|---|---|---|---|
| 1 | Boot scrub of inherited `ANTHROPIC_*`, `CLAUDE_CODE_*`, `OPENAI_*` (plus `CLAUDE_CONFIG_DIR`, `AWS_BEARER_TOKEN_BEDROCK`, `ENABLE_TOOL_SEARCH`, `ENABLE_CLAUDEAI_MCP_SERVERS`) before the SDK loads. A's total routing env kept, plus `assert_scrubbed` at every launch. | B | `qma/boot.py`, `qma/serve.py`, `launch.assert_scrubbed`. New entry point `python -m qma.serve`. Check S19. |
| 2 | Canary leak check: throwaway config home with a fake plan token, a key profile at an echo server, grep everything. | B | Check S21. |
| 3 | Untrusted-content marking. SDK-native: `verbatim_prompts=True` (02a sections 6 and 15) stops slash dispatch, `/skill` invocations and `@path` reads. It is per client, so Background and Child chats are always verbatim and Interactive chats refuse `InjectedText`. | B (A had it for Child only) | `chat.OperatorText`, `InjectedText`, `UntrustedPrompt`, `launch.verbatim`. Check S25. |
| 4 | One loopback relay for non-plan traffic: per-launch grant secret as `ANTHROPIC_AUTH_TOKEN`, family guard per request, real key from the keyring, wire quirks, unchanged streaming, authoritative key usage. GPT is a lane in it, still gated by `ProbePassed`. A's separate translator server folded in. Plan CLIs get no base URL. | B and C converged | `harness/relay.py`, `launch.PlanLaunch` and `launch.RelayedLaunch`, `profiles.Quirks`. `gpt/server.py` deleted. Checks S9, S21 to S24. |
| 5 | Inside-out exposure probe run by `doctor`, which sets `MoneyPosture` with the broker scope proofs. Shown on the usage page. | C | `money.run_exposure_probe`, `money_posture`, `usage.UsagePage`. Checks S26, S27. |
| 6 | Closed `Effect` enum with no money-act member; every tool declares one. | C | `tools.Effect`, `ToolDef.effect`. Check S28. |
| 7 | Approvals bound to a digest of the exact arguments, consumed once, enforced in the tool handler. | C | `tools.Grants`, `args_digest`, `AnswerStatus "invalid"`. Check S29. |
| 8 | One OS memory cap over all agent CLI trees: Windows Job Object (with kill-on-close), Linux delegated cgroup, macOS live-chat cap only. A's `max_live_chats` and reaping kept. | C | `harness/procs.py`. Check S30. |
| 9 | Named seam for the later OS-account zone (U10), not built. | C | `Harness` docstring, `relay.py`, `tools.py`, DESIGN "The seam for a later agent account". |

## Convergence

B and C reached the same structural gain from opposite directions: no provider key in any CLI env. B did it with a gateway that also carried the plan, C with a door relay that did not. The synthesis takes C's plan-free placement and B's per-request family guard and quirks, and puts the relay inside qmx-control with no second process. That agreement between two independent candidates is the strongest signal in the arena.

## Judge corrections applied to A

1. Settings hooks claim against `setting_sources=[]`. Now `["user"]` from the start, since settings move with `CLAUDE_CONFIG_DIR` (02a section 6). S7 tests only the unconfirmed part (skills, agents, commands), read-only, and on `LEAKS` the rules from `settings.json` are passed in code so UI edits still hold. `home.UserTier`, `launch.build_options`.
2. Broker scope stated as fact. `money.py` layer 1 is now conditional on S27 (was M1), and says the scope names come from the runner's own knowledge.
3. "Unrepresentable" overclaim. `ProbePassed` now has a module-private mint guard plus the CI grep, and both DESIGN and `probe.py` say "guarded, not unrepresentable".
4. Background cap staleness. `usage.BackgroundCap.allows` and DESIGN now say the cap acts on the last `RateLimitEvent`, which fires only on transitions, so it is best effort and can overshoot (03 GB-9).

## Rejected

| Idea | From | Reason |
|---|---|---|
| Plan traffic through a QMX gateway, sealed or not | B | 02b A lists relaying the Claude OAuth token as clearly barred. 01 section 7 requirement 1 says QMX never holds or passes the token. B's sealing starts after the HTTP parse, so the process does read it. |
| Wire gate that rewrites `tool_use` in model responses | B | It edits Anthropic responses, risks a 400 on the next turn, and breaks "do not buffer" (02b C item 5). The PreToolUse hook already covers sub-agents and every mode. |
| Cross-provider sub-agents in one CLI | B | Anthropic does not support routing Claude Code to non-Claude models through any gateway (02b C item 2). `delegate` is the documented safe floor (03 GB-4). |
| Mandatory OS-account zone in v1 | C | Elevated setup on every OS, unproven sign-in from a service session and on macOS, daily friction (Git ownership, credentials, shares), and close to his no-sandbox ruling (R28). 03 GB-7 already filed it as U10. Kept as the named seam. |
| User-tier mirror pushed into the zone | C | Only needed with a zone. A second copy of the user tier is split ownership. |
| Removing every in-process money check | C | Defence in depth is cheap and the operator ruled "hooks, not prompts". Operator-added MCP servers and loopback services slip past a boundary. |
| Deny entries on every non-system volume root | C | Invasive on his own drives and slow over a whole drive. |
| QMA-held keychain password on macOS | C | Too close to "store" in 02b A item 4. |

## Accepted tradeoff, not a question

In month one the trading node runs on this same PC (R25). A trading-capable credential is then reachable from agent Bash, so the measured posture is SPEED_BUMP. The operator accepted the speed bump on 10-13 (R21). The usage page states it from the probe result. The U10 zone, or moving the trading credential to the node, is what turns it STRUCTURAL.
