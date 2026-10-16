> STATUS 2026-10-16 (rubric walk): SUPERSEDED. See 27-rubric-walk.md. Rulings in 26 win.

# 20 — Review A: operator fit and simplicity

Reviewer: adversarial review of `19-centralized-design.md`, written 2026-10-16. The test was Mubarak's own words and rulings. File:line references point to this worktree (`tracker/qma-v2/...`) unless a memory note is named.

Verdict: 19 is a thorough reference for the agents who will build QMX. It is not yet fit for Mubarak himself. It invents at least one number and calls it his. It bends three of today's rulings: the Lab is THE core, total creative freedom, and the node is premature. It contradicts itself on the account guard. It asks him ten bundled technical questions when only about six are his to answer. It also builds the Lab late and the mini apps last.

---

## Findings, ranked

### High

**1. The "$20 his number" is made up.**
- Where: 19:18 (decision 2), 19:5 (the rule that "his number" marks his numbers).
- Problem: by 19's own rule at line 5, "his number" means Mubarak set it. He never did. Nothing in `tracker/qma-v2` mentions $20 as an ask-above limit. The inputs use "his number" as a blank to fill: `15-templates-researcher.md:180`, `17-templates-dev-pm-lab.md:14`, `17:213`, `17:523`. 19 turned the blank into a figure and credited it to him. The same thing happened earlier with "(his number)" at `17:186` (12 variants) and `15:146` (5 dead ends). Those numbers are Claude's too.
- Fix: delete "$20 ... (his number)". Make it a question with an empty slot: "Ask me before one run spends more than $___." Change "his number" in 15 and 17 to "default, his to change".

**2. The Lab is THE core feature, yet the build order puts it fifth and the mini apps last.**
- Where: 19:362-372 (wave 2 order), 19:382 (mini apps D7-D9 in wave 4).
- Problem: wave 2 starts with P2 (a Portfolio report), then T1 and RK1 (trader and risk), then RS1, then A. The Lab and Board pilot (L1) comes fifth. Mini apps wait until wave 4. Yet his correction 2 says "plugins are the contract to mini apps, before any general Lab or Portfolio plugins" (`wayfinder/tickets/plugin-unit-and-loading.md:17`). Today he said the Lab is the core.
- Fix: reorder wave 2. (1) L1 and L2, the Board on one real idea, ending in a scorecard; this also proves the renderer. (2) One mini app loaded as a plugin, reading one Lab output, then archived. (3) RS1 paper scout. P2, T1 and RK1 move to wave 3. They mostly read live accounts, and the node work that feeds them is premature.

**3. "Total creative freedom" is bent by rules that also bind him.**
- Where: 19:258 (the builder lint), 19:144 (C8: "variants may tighten ... never loosen"), 19:256 (gates on every Board run), 19:21 (deflated Sharpe at least 0.95 over every trial in the family).
- Problem: the lint stops anyone, him included, from removing a grader or calibration, or loosening a gate, in a workflow they build. The Board runs gates on every `scope-run`. The family ledger counts every Board tweak as a trial, and the deflated Sharpe gate punishes each extra trial. A vibe-coding board that grades and penalises every try is not total creative freedom. His correction 4: "the Lab is QMX's core feature with total creative freedom" (`wayfinder/tickets/autonomy-policy.md:17`).
- Fix: these rules bind agents, not him. Inside the Lab, a draft runs with only cheap sanity checks: costs on, lookahead flag, minimum trades. The full overfit gates and the trial count apply only when something leaves the Lab, on promotion to Strats or to demo. He may drop any check in a workflow he builds, and the output carries a "check removed" badge.

**4. Goes deep on the trading node, which he called premature, and invents risk numbers.**
- Where: 19:22 (decision 6: six sub-rules on unit upload, live tightening, auto-revert, override badge and same-family review), 19:140 (C7: `unit.tighten` actions and a direction table "shared by the node"), 19:144 (RK1 amber/red thresholds: 30% / 3R, 10% / 1R), 19:21 (demo trade counts).
- Problem: today he said the unit lives in the node and that this is "premature, so don't go deep". `wayfinder/MAP.md:46` agrees. Memory `qmx-operator-standing-rules` rule 2 says risk and sizing authority is the GitBook and node docs. Rule 4 says not to re-discuss node internals with him. 19 designs the node's write path and asks him to approve kill-line thresholds that no GitBook source backs. 16 cites no GitBook for them either.
- Fix: delete decision 6. Shrink C7 to "templates ask for named facts; a missing fact returns `unknown` and renders 'could not check'". Move `unit.tighten`, the direction table and auto-revert to the risk-sizing session. Mark every risk threshold "from GitBook, or to be set" instead of shipping Claude's numbers.

**5. 19 contradicts itself on the account guard.**
- Where: 19:336 (wave 0: "agents cannot read or write the guard"), 19:25 (decision 9: "agents are locked out of the account guard now"). Against: 19:140 (C7: a guard reader serves "guard state, the guard config hash"), 19:366 (pilot 1 proves "the account-guard reader"), and RK1 throughout.
- Evidence: `16-templates-trader-risk.md:15` says "A template may read the guard and propose a change to it."
- Problem: a builder cannot follow both rules. Either the lock-out canary test breaks P2 and RK1, or the reader breaks the lock-out.
- Fix: one sentence in C7. "Zero-token scripts may read guard state through the read-only reader. Model and agent steps never see the guard, and the canary test checks exactly that." Or make it a yes/no for him.

**6. The ten decisions are mostly not his, mostly bundled, and partly already settled.**
- Where: 19:15-28.
- Problem: memory `mubarak-operator-profile` asks for short numbered yes/no questions. `dont-reask-settled-decisions` says to ask only about money, vocabulary he cares about and irreversible scope. `qmx-operator-standing-rules` rule 9 says not to frame design observations as his decisions. Against those:
  - Purely technical, so Claude's call: 1 (step kinds, reversibility tiers), 3 (semver, SHA lock, registry), 7 (JSON schemas, grader) and 8 (role table, floor tier).
  - Already his words, so asking again is re-asking: 4 (home, packs), 9 (Portfolio human-driven, unit in the node) and the Strats name (19:28; `BACKLOG.md:91` already has "strats S T R A T").
  - Bundled: 2 is four decisions, 5 is five numbers plus a WF1/WF2 ruling he already made, 6 is six decisions, and 10 is three (Board, builder, variant rule).
- Fix: see "Rewritten decisions" below. That leaves seven yes/no questions and one blank number.

**7. The deliverable is a 52 KB wall of text. He asked for animated explainer documents.**
- Where: all of 19. For example, C2 at 19:120 is one paragraph of about 600 words.
- Problem: today he said output should be animated explainer documents, not text blocks. Memory `mubarak-operator-profile` adds that he "will not read a markdown report". 19 is fine as input for agents but will not reach him.
- Fix: keep 19 as the agents' reference. Give him a separate explainer page: the one-page system diagram (19 section 2) animated step by step, the wave plan as a timeline, and the rewritten decisions at the end. Give him time to read before asking anything.

### Medium

**8. "Two iterations" is presented as his target. His word was "fewest".**
- Where: 19:26 (decision 10), 19:256, 19:298 (L1 title).
- Evidence: `12-design-synthesis.md:20` quotes him, "in the fewest iterations". `wayfinder/tickets/experimentation-board-vibe-coding.md:17` says "fewer round trips".
- Fix: "Fewest iterations. The Board shows a counter. Two is Claude's starting goal, not his." Rename L1 to "Idea to first result".

**9. Promotion to the Library is declared "inside the Lab" without asking him.**
- Where: 19:18, 19:414.
- Problem: correction 4 says publishing outside the Lab asks. 19's own diagram draws the Library (Strats) as a separate room (19:76-77), and Strats v2 is its own session (`BACKLOG.md:91`). Calling promotion "inside the Lab" so that it needs no ask is a quiet bend.
- Fix: make it its own yes/no (rewritten decision 2).

**10. "Methodology is the umbrella" is missing.**
- Where: 19:1 (title) and 19:258 are the only places the word appears.
- Problem: today he said methodology is the umbrella over the organogram and the workflows, and that he and the copilot can create new methodologies. 19 never says what a methodology is. It also dropped 12's "Methodology version" builder row (`12:292`). 19's builder makes agents, workflows, skills and packs, but not methodologies.
- Fix: add a short "C0 Methodology" section. A methodology is a pack that sets the autonomy rows, gates, role tiers, organogram and starter templates. QMX ships one default. He or the copilot copies it and edits it with the builder, and old versions are kept.

**11. The builder he asked for today waits until wave 3.**
- Where: 19:378.
- Problem: making new workflows by talking is the heart of the Lego vision (memory `qmx-lego-vision`) and of today's words. Wave 3 is far away.
- Fix: put a minimal workflow builder in wave 2. He describes the workflow, the copilot writes the folder, a fake-model dry run follows, and the workflow installs disabled until he says yes. The agent, skill and pack builders stay in wave 3.

**12. No pilot proves a combined session.**
- Where: C3 at 19:124 describes packs composing, but no wave 2 row (19:364-372) tests it.
- Evidence: `12:88` says the same session can hold Lab, Portfolio, a workflow and an app at once. He repeated this today.
- Fix: add a pilot. A Lab-born session loads a workflow pack and the pilot mini app's pack, is opened in the hub, keeps its Lab home, and shows a Portfolio proposal as a card only.

**13. Waves 1 and 2 are too big to prove the idea.**
- Where: 19:350-374.
- Problem: wave 1 builds all 11 contracts, the browser and a large UI list in three parallel tracks. Wave 2 then touches about 16 templates (P2, T1, RK1, RS1, RS7, A, RS5, L1, D2, L2, B, D3, RK4, T5, T9, RS0). Memory `light-verification-per-pr` and `builders-sequential` say heavy rigor already cost him about 20 hours, so builders run one at a time.
- Fix: see the cut list. The smallest version that still proves the idea: a thin engine, a folder loader, a renderer, the Board pilot, one mini-app plugin, one scheduled scout and the minimal workflow builder.

**14. Usage on Max 5x: several templates would burn the cap, and nothing plans the night.**
- Where: 19:128 (budget classes), 19:395-397 (L4, D3), 19:374 (exit gate "three nights unmanaged inside the cap").
- The heavy ones:
  - D3: 3 generations × 4 children × 20 builder turns is about 240 strong-model turns per card.
  - L4: 200 trials and 6 revolutions every night.
  - L1 arena: 3 readings × 30 turns × 2 repair rounds (`17:63`).
  - D7: 3 prototypes × 40 turns.
  - D4: up to 12 variants.
  - T4: 6 analysts × 10-20 calls (`16:170`).
  - RS4: a multi-agent harness at about 15 times a chat (`15:119`).
  - A: nightly, with an `audit-other-family` pass on every item.
  - `calibrate` (RS7) is the hidden multiplier. It runs K readers plus a validator on every headline, and 12 templates use it (19:172).
- Problem: one Claude Max, 50% of each 5-hour window for background work, plus a weekly limit. A, L4 and T4 all want the same nights. "Another model family" means a paid key (OpenRouter), so every family-rule check costs money or falls back to Claude anyway.
- Fix: a night plan with at most one heavy job per night, the rest queued and shown in the job panel. Run calibrate only on headlines he will see, and only when attended. Same-family fresh context is the default on Max, and another family is opt-in per workflow. Make the wave 2 exit gate "one night", then measure before promising three.

**15. The letter "B" means four different things.**
- Where: 19:128 (budget classes B0-B4), 19:136 (browser levels B0-B4), 19:268-269 (templates A and B), 19:368 ("B1 fallback"), and backlog items B17a and B44 throughout.
- Fix: use words. Cost tiers: free, tiny, small, fan-out, heavy. Browser levels: none, read web, act web, read as me, act as me. Keep "B" for the funnel only.

**16. Settings would hold 27 model roles and the renderer 20 output kinds.**
- Where: 19:241-246 (roles), 19:132 (output kinds).
- Problem: he configures models in Settings himself. A 27-row table is not "simple".
- Fix: Settings shows four tiers (cheap, mid, strong, reviewer). Roles map to a tier and can be overridden in an "advanced" fold. Use the six formats from `12:237-244` (dashboard card, explainer, scroll story, scorecard, alert, decision card), with the other kinds as variants.

**17. Journeys are situational, but 19 locks one mode per template and leans on a file it says it supersedes.**
- Where: 19:264-316 (a fixed Mode column), 19:106 ("journey mixes in `12` section (a) still hold") against 19:3 ("supersedes 06, 07 and 12").
- Fix: rename the column to "Default mode" and say the hub picks the mode by situation. Either copy the journey table into 19 or stop calling 12 superseded.

### Low

**18. The browser hold is lifted quietly.**
- Where: 19:28 ("smaller items"), 19:358 (the browser starts "beside" wave 1), 19:369 (pilot 4 uses B3, "read as me", logged in).
- Problem: his hold B17a (`BACKLOG.md:76`) is a real ruling. The first pilot then uses the riskiest read level.
- Fix: make it a main yes/no (rewritten decision 4). Start with the watch pane and public reads, and add logged-in reads after he has watched a run.

**19. "Money" means two things.**
- Where: 19:18. "Nothing asks except money" means account money, which is read-only. "Compute spend asks above one number" means key spend.
- Fix: write "account money (never)" and "key spend (ask above $___)".

**20. Small errors.**
- 19:18 points to "section 8" for the conflict. The conflicts are in section 10.
- `wayfinder/MAP.md:13` says 49 templates. 19:317 says 48, and 48 is the right count.
- 19:374 says "RS1 or L4's predecessor B". B is not L4's predecessor, so say which template.
- 19:21 shows 0.95 as if settled, but `08-strategy-funnel-lineage.md:292` recommended "above 0", and `08:298` recommended 30 trades. Both 08 and 19 are Claude's proposals, not his. 19:419-420 notes the change from 08 but still asks him to approve the numbers.

---

## Cut list

The target is waves 1-2. The rest of 19 stays as reference for the later build-out.

**Contracts: keep the shape, cut the weight for wave 1.**

| Piece | Keep in wave 1 | Defer |
|---|---|---|
| C1 folders | `plugin.json` + `qmx.toml` + `README` required; every other slot optional; archive, never delete | variant overlays, `SOUL.md`, `pending/`, `evals/` as required slots |
| C2 engine | step kinds script, model, agent, human, grader; saved step results; retry, then escalate to one inbox item; a watchdog for stuck runs; one trace per run | the `rlm` kind, the doctor's local repair, CRO fork-and-replay of logic edits, `runs_on` (after B44), four-layer monitoring |
| C3 homes and packs | home stored and never changed; packs compose; the stricter row wins | per-pack memory scopes |
| C4 settings | four tiers, per-workflow model override, the 50% governor, one per-run spend cap | five budget classes, reserve-then-refund, the family-rule lint |
| C5 output | six formats, schema check, numbers trace to a source | headless render plus screenshot grader, 20 kinds |
| C6 browser | QMX profile, watch pane, one job at a time | leases B2-B4, Stagehand, Steel, the queue UI |
| C7 unit adapter | read named facts, `unknown` renders "could not check" | `unit.tighten`, the direction table, auto-revert (risk session) |
| C8 gates | a store in Settings, hash-bound verdicts, 3-4 default gates (costs on, out-of-sample, minimum trades, deflated Sharpe) | the other six tests until B runs for real |
| C9 ledger | the trial ledger; holdout touched once | the live cost model from T9 |
| C10 memory | `run` and `operator` scopes | auto-proposed checks after three lessons |
| C11 app I/O | `feeds`/`provides` by artifact for one mini app | webhooks, external out, the full 12-line `app check` |

**Templates: merge overlaps, and stop counting subflows as templates.**

| Merge or move | Why |
|---|---|
| T1 morning brief + T2 pre-session + T10 end-of-day become one "desk brief" with three schedules | Same inputs, same output card |
| P2 daily portfolio report + T10 wrap | Both are the end-of-day read of the book |
| RK3 decay + P3 decay and limit report | 19:401 already gives them one default |
| RS2 paper to card + RS5 understand and extract | Both turn a source into a card |
| RS3 replicate a paper + T8 video to demo trial | Both are "source to a Lab test" |
| D1 card to build + D5 indicator authoring | Same build loop |
| D7 + D8 mini app create and maintain | One lifecycle |
| L3 promote to Library | It is A stage 7 / `library-write` |
| RS9 + D10 weekly reviews | One weekly review |
| RS5, RS7, RK4, RK7, D2, L2 | These are blocks in 5.1, not templates he picks |

That takes the list from 48 to about 30 user-facing templates. Wave 2 needs only five: L1 (with B-lite inside), RS1, one mini app (D7-lite), the minimal workflow builder, and P2 script-only as the cheap renderer proof.

---

## Invented defaults

None of these are Mubarak's. Each is fine as an editable default in Settings, as long as it is labelled as Claude's.

**Wrongly labelled his, or near his words:**
- $20 ask-above per run (19:18).
- "Two iterations" per idea. His word was "fewest" (19:26, 19:256).
- 12 variants per run, labelled "his number" at `17:186`.
- 5 dead ends to wake, labelled "his number" at `15:146`.

**Gates (19:21, 19:144):**
- Deflated Sharpe probability at least 0.95.
- Walk-forward efficiency at least 0.5 over 6 folds.
- PBO at most 0.25.
- Noise test: 200 runs with 70% still profitable.
- Monte Carlo p at most 0.05.
- Beats the 95th percentile of 1,000 random-entry runs.
- 60% of parameter neighbours profitable.
- Profitable at 1.5x costs.
- 200 in-sample and 100 out-of-sample trades.
- Demo: 2 weeks, 100 trades for scalpers, 30 for swing units.
- Improve loop: 3 generations × 4 children, stop after 2 with no gain, 20 builder turns.

**Risk. These need a GitBook source, not Claude:**
- RK1 amber below 30% / 3R, red below 10% / 1R, black on a missing heartbeat.
- RK1 tick every 30 s; RK3 daily and every 10 trades; RK2 hourly.
- Decay: amber outside the 90% Monte Carlo band for 10 trades.
- RK8 slippage over 0.5R; watchdog outage over 2 minutes.
- Black alert pushed every 10 minutes.

**Cost and usage:**
- Budget classes: 8k, 3 calls / 40k, 6 × 10 / 300k.
- Calibration: 5 headlines × 3 samples.
- Readers: 3 per tick at 10 calls.
- Searchers: 5-15 calls, hard stop at 20 calls or 100 sources.
- L4: 200 trials, 6 revolutions, 3 restarts, plateau after 30, top 3, deadline 07:00.
- D4: 4 builder-made variants.
- D10: 10 backtests, 5 fix drafts.

**Method:**
- Grill: at most 5 questions. Arena: 2-3 readings. Research harness: 3-5 searchers.
- 7 starter sub-agent roles, 27 model roles.
- Significance: n under 20. Lookahead flag at Sharpe above 2 (or above 3 on minute data). Sentiment only above 5 sd.
- A lesson seen 3 times proposes a check. Memory files under 200 lines.
- T7: at least 20 trades, at most 3 lessons.
- Dead-end mining: at most 10 clusters, short list of 5.
- Watchlist: FX majors plus XAUUSD.

**Actually his:** the 50% background cap, one Claude Max account, money read-only, USD.

---

## Rewritten decisions

Seven questions, each answerable with a yes or a no, plus one blank number. Everything else in 19's list becomes Claude's call, recorded as an assumption he can overrule. That covers the engine, folders, output format, model settings and gate defaults.

| # | Question for Mubarak | Recommended |
|---|---|---|
| 1 | Inside the Lab, may agents start and schedule their own jobs without asking you, as long as background use stays under your 50% cap? (This changes your 10-13 rule that scheduling always asks.) | Yes |
| 2 | When something proven in the Lab goes into Strats, should QMX just tell you instead of asking first? | Yes |
| 3 | Agents must ask you before one run spends more than $___ on paid keys such as OpenRouter. What number? (Or say "always ask".) | Always ask, until you pick a number |
| 4 | Lift the browser hold for one first step: a separate QMX browser you log into once and can watch live, which agents use to read pages, one job at a time, with no clicking? | Yes |
| 5 | Rules like "a run may not skip a check" bind agents only. You can drop any check in your own workflows, and the result shows a badge. Agree? | Yes |
| 6 | May the Experimentation Board be saved on the backend, so a board survives restarts and workflows can run it? (This changes two docs that say the Board lives only in the browser.) | Yes |
| 7 | Build order: the Lab and Board first, then one mini app as a plugin, then the paper scout. The morning brief and Portfolio reports come later. Agree? | Yes |

Removed from 19's list:
- Decision 6 goes to the risk session.
- Decisions 4 and 9 and the Strats name are already his words.
- Decisions 1, 3, 7 and 8 and the gate numbers are Claude's to set as editable defaults.
