# PRB-R findings: router probes P0, P1 and P1k

Each row is one probe of SOLUTION-DESIGN section 26.14, run on 2026-10-18 at `engine/base` (`132169c7`) plus this branch. The probes drive a raw `claude_agent_sdk` 0.2.166 client (bundled CLI 2.1.299) from the `qmx-agents` venv, never the harness. Plan turns ran on `haiku` (served as `claude-haiku-5-5`) under the ship home's plan login. Logs are in `D:/QMX-worktrees/qma-ship/build/evidence/prb-r/` as `owner-prb-r-<slug>.log`.

Run each from `qmx-agents/` with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA` unset, for example `uv run --no-sync python ../scripts/probes/router/p0_parity.py`. P0 and P1 take the lane lock themselves.

## Read this first: P0 failed, so the plan lane does not ship

P0 is the build gate for the plan lane. A plan launch behind a base URL does not send the request it sends to `api.anthropic.com` directly, and no env value found restores every difference. The closest launch, `ENABLE_TOOL_SEARCH=true` plus the private `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL=1`, still drops one beta, `mid-conversation-system-clear-at-2026-08-21`, on every request.

The fallback the plan names applies. RTR7 (the plan lane) is not built. RTR6 gives plan mains no third-party sub-agent definitions. A Claude plan copilot reaches Kimi, Qwen and the rest through `delegate` v2 only. Key and GPT mains are not affected, and P1k passed for the Kimi main.

P1 passed, so the CLI itself does run a `kimi/k3` sub-agent under the plan login. The block is P0's parity line, not P1.

## Rows

| Probe | Observed | Verdict | Fallback it triggers |
| --- | --- | --- | --- |
| P0 `p0_parity.py` | Four rounds of three repeats. Each repeat is the same haiku turn with one `mcp__qmx__ping` call, run A with no base URL and run B through `router.py` with the grant in `ANTHROPIC_CUSTOM_HEADERS`. All 24 turns succeeded (`PONG-PARITY`, one tool call). Both runs went through the same recording HTTPS proxy, so run A's direct requests were recorded too. Round 0 (no env on B), per request: B lacks the headers `x-claude-code-prompt-id`, `x-claude-code-request-class`, `x-client-request-id` and, on the second request, `x-claude-code-prev-tool-durations`. B lacks the betas `mid-conversation-system-clear-at-2026-08-21`, `thinking-binding-controls-2026-08-01` and `cache-diagnosis-2026-04-07`. B lacks the body field `diagnostics`, the tool `DeferredToolPlaceholder` and one `safeguards[0].classifier_context.rules.deny` rule (76 against 75). B's billing line in `system[0]` carries only `cc_version` and `cc_entrypoint`; A's also carries `cch`, `cc_prompt_id`, `cc_prev_req`, `cc_turn_origin`, `cc_prompt_index` and `cc_turn_index`. Round 1 (`ENABLE_TOOL_SEARCH=true`) restored the tool and the deny rule. Round 2 (plus `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL=1`) restored the headers, two betas, `diagnostics` and the billing line. Round 3 (plus `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`) changed nothing more. In rounds 2 and 3, all 12 pairs still lack `mid-conversation-system-clear-at-2026-08-21` in B. The `authorization` value was the same in A and B on every pair (compared in memory), and it is an OAuth bearer. | FAIL. One difference that no tried env value restores: the beta `mid-conversation-system-clear-at-2026-08-21` | The plan lane does not ship. RTR7 is not built. RTR6 gives plan mains no third-party definitions |
| P1 `p1_definitions.py` | A haiku main under the plan login, base URL on `router.py`, grant header, and the round 2 env. `agents={"kimi-reviewer": AgentDefinition(model="kimi/k3", tools=[])}`. The main called `Agent` with `subagent_type: kimi-reviewer`. One request with `model: kimi/k3` reached the router with `x-claude-code-agent-id: a70bfec3ebaf7ccc4` and went to the Kimi echo. The echo's answer came back through the sub-agent's `SubagentHandback` call in the `task_notification`, and the main's final reply was the echo text, word for word. Every method and path the CLI used: `POST /v1/messages?beta=true` five times, with models `claude-haiku-5-5` (3), `kimi/k3` (1) and `claude-sonnet-5` (1). Every main request went to `api.anthropic.com` with the OAuth bearer and got 200. The raw sub-agent request is kept with secret values withheld as `owner-prb-r-p1-subagent-request-0.http` for RTR7's P4. | PASS | None. P1's line holds. P1 alone does not open the plan lane, because P0 failed |
| P1 canary (lane 5) | `p1_definitions.py --runs 2`: the echo form twice in a row. Both runs passed every P1 check. | PASS, the same verdict twice | None. It can serve as RTR7's boot canary if RTR7 is ever built |
| P1k `p1k_key_mains.py`, Kimi main | A main on the OpenRouter Kimi row (`moonshotai/kimi-k2.5`) from a throwaway home, base URL on `router.py`, the grant as `ANTHROPIC_AUTH_TOKEN`, `ENABLE_TOOL_SEARCH=false`, `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1`. Definitions `deepseek-reviewer` (`deepseek/deepseek-v4-pro`) and `qwen-reviewer` (`qwen/qwen3.6-plus`). The router sent the Kimi id to OpenRouter with the key it read by keyring name `qmx/openrouter`, and each sub-agent id to its own echo. Both sub-agents spawned. Each request reached the router with its model id unchanged and `x-claude-code-agent-type: custom`. Both echo answers came back in the task notifications, and the main reported them word for word. Nothing that reached an echo held an `authorization`, `x-api-key` or grant header or an `sk-ant-` value. The CLI printed `unrecognized_model` for all three ids and sent them anyway. | PASS | None |
| P1k GPT main | Not run. | not run, no GPT sign-in | Until it runs, GPT mains have no P1k result; RTR6 decides from that |

## Values the probes found

- The plan-lane launch env that comes closest to parity is `ENABLE_TOOL_SEARCH=true` plus `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL=1`. The second name is private (leading underscore) in CLI 2.1.299. Its code path is `isFirstPartyBaseUrl()`, which returns true when the name is set. A private name can change or go in any CLI release.
- The kept-reminders beta `mid-conversation-system-clear-at-2026-08-21` is added only when a per-model, per-conversation delivery check in the CLI says so. That check stays off behind a base URL even with the first-party name set. No public env name controls it in 2.1.299. This search was four env rounds plus a read of the CLI's source strings. It does not prove that no value exists.
- With a base URL set, the CLI still sends `GET /v1/mcp_servers?limit=1000&include_additional_installs=true` straight to `api.anthropic.com`. The router never sees it.
- Under a plan main, the sub-agent's `kimi/k3` request reaches the base URL carrying the plan's OAuth bearer. The probe router dropped it before the echo. A real router must drop it on every third-party lane, which is P4's egress line.
- CLI 2.1.299 runs `Agent` calls in the background. A sub-agent's run ends only when it calls the tool `SubagentHandback` with its report. Until then the CLI re-asks with `[handback-send-enforce]`. A third-party sub-agent model must make that tool call.

## Perf

Not gated (Override 4). Metric: the time the pass-through router itself adds per plan request, from request read to upstream send (minus the upstream connect) plus upstream first byte to client first byte.

- Router overhead: median 14.98 ms over six requests in round 0 (13.21 to 22.60), and 14.8 to 15.7 ms in the other rounds. That is below the 50 ms risk line, so it is not a risk for RTR7.
- Upstream connect and TLS per request: median 160 to 192 ms per round. The probe router opens a fresh connection per request; a pooled router would not pay this.
- Request wall time, median per round (6 requests each): A 1505 / 1542 / 1595 / 1588 ms, B 1483 / 1969 / 1788 / 1578 ms. The spread between requests (about 1 to 3 s) is larger than the A-B gap, so the wall times show no router cost beyond noise.

## Method notes and departures

- P0 run A is recorded through `InterceptProxy`, an HTTPS proxy that serves `api.anthropic.com` with a probe-made certificate. The CLI trusts it only through `NODE_EXTRA_CA_CERTS` in that process's env. The CA and its key are deleted at the end of the run. Run B goes through the same proxy for its other hosts, so the only launch difference is the base URL, the grant header and the round's env.
- P0's exclusions follow the plan, plus values the model or the clock decides: tool-use and message ids, the billing line's `cch`, `cc_prompt_id` and `cc_prev_req` values, the `<total_tokens>` counter in a reminder, and the model's own words in earlier assistant turns. Presence is still compared for all of them. Three pairs differed in `messages[2].content` length, in both directions (A 2 and B 1, then A 1 and B 2). That is the model's output, and it is not counted against parity.
- P0 compares `/v1/messages` pairs. The other path, `GET /v1/mcp_servers`, is listed in the log and not judged.
- Env candidates are set on run B only, because "a launch env value restores it" means the plan-lane launch.
- P1 and the canary launched with the round 2 env (`PLAN_LANE_ENV` in `common.py`), as a plan-lane launch would.
- The DeepSeek and Qwen ids are Claude's default. Only an echo answers them.
- P4's other egress lines (betas, `defer_loading`, `metadata.user_id`) are not judged here. They belong to P4 against the normaliser, which is not built.
