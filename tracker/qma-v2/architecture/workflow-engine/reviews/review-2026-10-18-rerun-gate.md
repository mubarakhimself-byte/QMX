# Reviewer gate, rerun pass (2026-10-18 evening)

Run inline by the architect: the brief allowed no sub-agents, so the reference's sequential fallback was used (write, then apply). Spines: workflow engine, Lab and Pods, Library and data. Record of the pass: `research/methodology/39-architecture-rerun.md`.

**Verdict:** pass after fixes. `lint_spine.py` reports 0 findings on all three spines after the last batch.

## Lens 1: rubric walk (good-spine checklist)

| # | Finding | Severity | Fix applied |
| --- | --- | --- | --- |
| R1 | The paradigm table's harness row listed `delegate` v2 among "provider contracts only", but HG4 asks for it as a harness behaviour change outside the pool exception | high | row rewritten: provider contracts only; `delegate` v2 and the rest are granted rounds (HG3, HG4) |
| R2 | AD-36 said comments and docstrings go through the prose matcher, while the amended prose rule gives them the secret check only (36 F) | high | AD-36's code sentence aligned |
| R3 | Deferred still said template names are out of scope, while AD-46 now binds them | medium | Deferred row reworded to point at AD-46 |
| R4 | SOLUTION-DESIGN still carried runaway-guard text in §2.1, §2.3, §3.1, §3.2, §5.1, §6.4, §10.2-10.3, §11.3, §15, §19, E18, E25, E41, and the old budgets paragraph of §7.4 | high | every occurrence rewritten to AD-16 and AD-40 |
| R5 | HARNESS-REQUESTS H7 still said the runaway guard bounds tokens and tool calls | medium | rewritten |
| R6 | `roles.live_order` had no stated default after AD-13's change | medium | §17 row added: `key, gpt, plan` |
| R7 | Every structural dimension at this altitude is decided, deferred or open: deployment and environments (AD-25, AD-30, AD-48), provider strategy (AD-12, AD-38, AD-39), operations (AD-15, AD-16, AD-40, AD-48); the desktop shell framework is Deferred with selection criteria | — | none needed |

## Lens 2: security and the money boundary

| # | Finding | Severity | Fix applied |
| --- | --- | --- | --- |
| S1 | "Bytes unchanged" on the plan lane would forward the router's own `x-qmx-grant` header to Anthropic | high | AD-38, SOLUTION-DESIGN §26.1 and 39 §2.4: the router removes only its own grant header; the body and every other header pass unchanged |
| S2 | MT5 and cTrader demo set-up must not need a change to the money gate (HG4 says the gate is untouched) | medium | checked: AD-33 keeps order tickets as money acts the gate refuses; the algo-trading toggle is permitted by the Cua manifest only after the driver matches the pinned demo account; no gate change |
| S3 | A plan lane on a central router would move plan bytes across machines | high | already excluded in AD-38 and AD-28 (same host, loopback; a central router has no plan lane) |
| S4 | The run pass lost its token cap with AD-40; a stolen pass needs another bound | medium | AD-28: a request-rate theft alarm (revoke, one `urgent` item), plus scope, TTL, placement and source binding |
| S5 | Pre-migration snapshots could read as a backup design while data is held | low | AD-48 says it is update safety, not a backup design |

## Lens 3: operator alignment (settled facts of the brief)

All settled facts checked against the amended spines: no usage caps (AD-40); pool in-house, no third-party product (AD-12); ruling 92 for copilot and workflows (AD-38, AD-41); defaults not Claude-first (AD-13, AD-34, AD-39); wire and capabilities per model (AD-39); multimodal on by default (AD-42); coding plans not interactive-only (AD-39 `use: any`); pool not fill-first and the copilot account used last (AD-12); no Fable (AD-13); tests on haiku (AD-11); MT5 and cTrader demo (AD-33, AD-44); copilot browsing as him while he watches (AD-44); data held (Deferred); plain template names and no approval on playlists (AD-46); the copilot builder as core (AD-22); a desktop app owner (AD-48); the fifth lens unbuilt (Deferred); methodology later (Deferred); D, E, F framed, not decided (OPEN-DECISIONS). No finding.

## Left open (in `methodology/39` §10 and §11)

D, E, F, G, the fifth lens and the burst-provider payment are his. The Lab and Library HLD/LLD companions were not re-projected beyond the named lines.
