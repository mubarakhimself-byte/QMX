# G10: Brakes, decay, slots and isolation in every generation

Written 2026-11-03 by grounding reader G10. Read-only. Nothing here is a design or a ruling.

## How to read this

- A line with a citation is what the source says. **[judgment]** marks my own reading, arithmetic or opinion.
- "Silent" means I searched and found nothing. The search is named where it matters.
- I do not repeat G3 §4.8 and §5, G4 or G6. Where they already answer a point, I give the pointer and add only what is new.

**Four generations.**

| Gen | When | What | Main sources |
|---|---|---|---|
| 1 | Apr–May 2026 | The old vault, plus the lost pre-crash code seen through the GPT talk | `V`, `GPTR` |
| 2 | Jul 2026 | GitBook Book/BMS core and the July wiki | `GBF`, `WIKI` |
| 3 | Aug–Oct 2026 | Current docs and engine/base code | `DOCS`, `DW`, G4, G6 |
| 4 | Oct–Nov 2026 | The unit build, stack tip `build/us-c13` at d02af358, not merged | `L0`, `PH`, `UPLAN`, `TIP`, `TPL` |

**Short paths.**

| Alias | Path |
|---|---|
| `V` | `C:\Users\Mubarak\Documents\Claude\QMX-discussion\` |
| `CB`, `PTDS`, `PRS`, `BRL`, `KSA`, `MIS`, `SQS` | `V\02-Components\` `02-circuit-breaker-policy-engine`, `08-paper-trading-demotion-service`, `06-performance-rating-service`, `07-bot-registry-and-lifecycle`, `09-kill-switch-authority`, `04-market-intelligence-service`, `05-spread-quality-service` (.md) |
| `SLOT`, `SESS`, `KSSL` | `V\02-Components\01-risk-and-sizing\` `04-slot-competition-model`, `05-session-architecture`, `06-kill-switch-and-sl-tp-integration` |
| `WF1`, `WF2`, `WF3`, `DEPT` | `V\02-Components\14-agentic-system\` `09-wf1-variant-generation-pipeline`, `11-wf2-variant-improvement`, `12-wf3-pool-cleaning`, `01-five-departments` |
| `FLOW` | `V\04-Integration-Flows\03-integration-flows.md` |
| `ADS`, `CRA`, `GAPC` | `V\outputs\` `alpha-decay-spec`, `clash-report-alpha-decay`, `gaps-commentary` |
| `PRD`, `ARCH`, `GEM`, `WFA`, `PROT` | `V\bmad-docs\planning-artifacts\` `prd`, `architecture`, `agentic-system-context-gemini-extract`, `workflows-architecture`, `qml-protocols-catalogue` |
| `BS` | `V\bmad-docs\brainstorming\brainstorming-session-2026-04-28-125147.md` |
| `GPTR` | `V\07-Source-Material\gpt-trading-algorithm-research.md` |
| `BRAIN` | `V\.brain\` |
| `GBF` | `C:\Users\Mubarak\Documents\QMX\raw\online\qmx-gitbook\captures\2026-07-18T141659Z\endpoints\llms-full.txt` |
| `GBC`, `GBK` | same capture, `pages\markdown\components\`; `GBK` is its `kill-switch-authority.md` |
| `WIKI` | `C:\Users\Mubarak\Documents\QMX\wiki\` |
| `DOCS`, `DW` | `C:\Users\Mubarak\Desktop\QMX\docs`, `C:\Users\Mubarak\Desktop\QMX\_docwork` |
| `L0` | `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\level-0\ARCHITECTURE-SPINE.md` |
| `MISC` | `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\parts\C-node-mis-external\MIS.md` |
| `PH`, `UPLAN` | `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\` `RISK-SIZING-PLACEHOLDERS.md`, `UNIT-PLAN.md` |
| `TIP` | `D:\QMX-worktrees\bld-us-c13` (d02af358) |
| `TPL` | `TIP\qmx-agents\packages\qmx-engine\src\qmx_engine\templates` |
| `OW` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\seeds\operator-words-2026-11-03.md` |
| `G3`, `G4`, `G6`, `G7` | `D:\QMX-worktrees\risk-plan\tracker\risk-core\grounding\` |
| `R08`, `R19` | `D:\QMX-worktrees\risk-plan\tracker\risk-sizing\research\` `08-old-qmx-testing-and-decay`, `19-grounding-old-system` |

---

## 0. The answer in twelve lines

1. **His memory is right, and the breaker never left.** April: "if a bot hits two consecutive losses… it stops trading… downgraded to paper" (`GPTR:19556`). July: breaker `B = 2` consecutive stop-outs, bench to paper, back at next open (`GBF:1104-1112`, `:933`). Today's docs call it the **bench** (`DOCS/components/qmf-risk.md:155`).
2. The vault spec was looser than his memory: two **strikes**, and a strike could be a loss streak, fee burn, failed recoveries or a rating drop, all without numbers (`CB:17-23`, `:48-53`).
3. The vault also had a **chronic** breaker: WF3 read "rolling CB-fire density" as decay evidence (`BS:131`; `ADS:28-29`). No formula, window or threshold was ever written (`ADS:36-39`).
4. July planned a better version: the exam certificate carries a `breaker_expectation` and a `fire_rate_band` (`GBF:1477-1478`), so live breaker frequency can be checked against an expected one. It was never filled in (GAP-0012, `GBF:2292`).
5. The unit build has **no breaker wired**. Halts are empty (`PH:21`). A freqtrade-style "stoploss guard" exists as a dictionary entry with no code (`TIP/qml/catalogue-seed/wave-1/exits-and-halts/stoploss-guard-halt.json:15-16`). Any risk stop waits for his resume (`L0:375`).
6. **WF1 and WF2** were agent workflows that took an idea to paper with no human gate. The only human step was the live click (`PRD:913`, `WF2` stage I.2). The unit build keeps this shape: "Build and prove" ends on a paper-trial card, and live is his click (`TPL/b-build-and-prove/README.md:3`; `UPLAN` C-23).
7. **News** in April was a per-currency kill switch plus **geographic news shifting**: block the news region, rotate to the others, no operator prompt (`KSA:83-92`, `:378-414`). July killed the budget rotation but kept the pair block (`GBF:2348`, L9 at `GBF:124`). Today news is a protection window, separate from the kill switch, with no widths set (`DOCS/components/qmf-risk.md:131-135`).
8. **Slots** in April: three fixed slots, re-filled at each session boundary by a scored auction (`SLOT:19`, `:37`). Moving weight between families went through a Portfolio agent's proposal to him (`DEPT:169`, `:179`). That is the "by hand" part he remembers. **[judgment]**
9. July moved capital only at cycle boundaries, by sweep, refund or re-seed, and banned redistribution inside a cycle (`GBF:711`, L4 at `GBF:114`). An intraday Book was a future type, never designed (`WIKI/components/book-template.md:33`).
10. **Live drift**: every generation either demotes (April, July) or only informs (Gen 3-4). None sizes down gradually on drift evidence. The July law "shrink before block" (`GBF:130`) had no mechanism behind it.
11. **Isolation by market class, region or correlated group**: April had regions (currency based). Nothing anywhere switches off a whole class such as crypto or indices. Silent across all generations.
12. The July **chorus flag** ("abnormal loss shape… rate and clustering, not amount", `GBF:163`) is the closest thing to his "circuit breaker at the BMS level". Its threshold stayed null (`GBF:1289-1298`).

---

## 1. The circuit breaker in every generation

### 1.1 Gen 1: the vault spec

G3 §4.8 has the two-strike rule. New detail:

| Point | What the vault says | Source |
|---|---|---|
| Purpose | Contain a bad bot "without destroying" it. One bad session is not enough evidence, because markets are session-specific. | `CB:11` |
| Window | The UTC day ("10-session daily cycle"), so a bot gets full cross-session exposure before strike two. | `CB:23` |
| What a hit is | Any of four triggers: loss streak past a tier threshold (by band and family); day's fees above a fraction of the day budget; failing to recover from a decline N times in a session; DPR tier drop mid-session. | `CB:48-53` |
| What a hit is (second reading) | "The circuit breaker… increments its hit counter when a bot records a full-stop loss." That is why the stop is one-shot: a trailing stop would turn full stops into small losses and the breaker would fire late. | `KSSL:124-126` |
| What a hit is (third reading) | In the trade-close flow, the breaker reacts to a PRS **tier transition** event. | `FLOW:79` |
| Strike 1 | Record it. Bot keeps its slot. No auction penalty. | `CB:19`, `:78` |
| Strike 2 | Bot leaves the slot at once and routes to the demo account (same code, demo credentials). The slot goes to the next-best bot. | `CB:20`, `:80`; `PTDS:31-33` |
| Reset | At the UTC day boundary every counter goes to 0. DPR scores are not reset. | `CB:122-137` |
| Rating on paper | DPR keeps scoring the demoted bot on demo, so a recovery on paper helps it win a slot the next day. | `CB:145` |
| Scope | Same policy for every family. | `CB:217` |
| News link | A hit during a regional news block is annotated `region_blocked = true`. It still counts, but review and DPR "can downweight" it. | `CB:221-232` |
| Event log | Every trigger, strike, demotion and reset goes to an append-only log, the source for review. | `CB:159-178` |
| Principle | "Bot circuit breaker degrades, doesn't remove." | `BS:124` |

### 1.2 Gen 1: his words and the lost code

- His words (April): "if a bot hits two consecutive losses yeah then uh it stops trading… it's downgraded to paper trading" and "two consecutive losses. the bot actually gets out of the market and the slot is open and the cycle repeats" (`GPTR:19556`).
- Same message: "a bot circuit breaker is one of the feeders that goes into WF3, which is the pool cleaning" (`GPTR:19556`).
- GPT's reply placed the breaker in WF2 as a promotion gate, a fitness penalty, a paper-survival metric and a WF3 feeder, not as a mutation target (`GPTR:19738-19749`).
- The pre-crash code had two breakers that did not talk to each other: `SSLCircuitBreaker` (LIVE → PAPER → RECOVERY → RETIRED, consecutive losses per bot, "rotates to paper on 2/3 loss thresholds") and `DPRCircuitBreakerMonitor` (tier `CIRCUIT_BROKEN`, score below 0.3, `AT_RISK` more than 3 checks, rank worse than 10) (`GPTR:10443-10444`). R19 §5 covers this.

### 1.3 Gen 1: three answers to "what happens after strike two"

| Source | After the day rolls over |
|---|---|
| `CB:21`, `:82`, `:133` | Back into the unfunded pool. "No probationary period beyond the demotion day." |
| `PTDS:47`, `:63`, `:111-115`; `BRL:136` | Moves to `PAPER_TRADING` for re-evaluation. Live again needs tier T2, 10 net-positive demo trades in a row and his approval (`PTDS:65-71`). |
| `FLOW:104-106` | Automatic flip demo → live if the promotion criteria are met. |

**[judgment]** The vault never settled whether the breaker is a one-day timeout or a demotion that must be earned back. That is the same question this session faces.

### 1.4 Gen 2: July, the breaker becomes the bench

- Registry: `scalper_breaker_threshold`, symbol `B`, value **2**, "Consecutive stop-outs before bench-to-paper", configurable (`GBF:1104-1112`).
- Effect: the bot benches to paper "for the rest of the day and auto-resets at next open" (`GBF:933`, `:937-945`). The seat goes `LIVE → BENCHED → LIVE`; the Book's mode does not change (`WIKI/system/lifecycle.md:34`, `:48`).
- It is door 5 of 7 and the third rung of the leash chain ("ambient governor, day closure, bench-to-paper, chorus flag, kill-line stand-down, classed kill switch, hold-time force-flat") (`GBF:476-478`). "Ambient governor" and "day closure" are named and never defined.
- `B` was also part of the sizing divisor, so the breaker count changed the price of R. G4 §3.4 covers the later split.
- Open in July: whether a breakeven exit counts as a stop-out (`WIKI/topics/position-safety-and-sltp-authority.md:47`, `:85`).
- **Chorus flag**: a listener for "abnormal loss shape. The chorus owns rate and clustering shape, not amount lost" (`GBF:163`). Threshold `F_CHORUS` is null, "certified from cohort exam" (`GBF:1289-1298`). Thresholds "derive from cohort exam observations" (`GBF:1501`). Human review of the chorus was killed: "intraday protection is deterministic" (DEC-0022, `GBF:2349`).
- **Breaker expectation**: the exam certificate must carry `fire_rate_band` and `breaker_expectation` (`GBF:1477-1478`). Their shape is not defined anywhere I found.

### 1.5 Gen 3: current docs and code

- G4 §3.7 and G6 §3.2 and §6 cover the bench. New points only:
- What counts: "qualifying loss exits", `realized_r ≤ −q`, with q evidence of about 1R. Breakevens never count; scratches and partial losses do not count by default; a forced flat counts only if it realized a qualifying loss (`DOCS/components/qmf-risk.md:155`).
- The word "stop-out" is banned; the breaker's input is `qualifying_loss_exit` (`DOCS/components/qmf-risk.md:157`).
- The old "two stop-outs a day" baseline is recorded as invalid as a V1 contract until fresh definitions exist (DEC-0094, `DW/ratification-packet.md:109`; GAP-0045 at `:98`).
- Built: the bench fold in `qmn/capital/bench_fold.py` (G4 §5.1). No reset scheduler (G6 §6).

**[judgment]** Fast invalidation cuts are partial losses, so under Gen 3 rules they never count toward the bench. Under the April one-shot stop they could not exist. His point that every number must include FI cuts applies here too.

### 1.6 Gen 4: the unit build

- The halts slot is empty and shows a warning (`PH:21`). Its contract: unit and account statistics in, `none`, `no_new_entries` or `flatten` out (`PH:55`).
- The dictionary has two halt entries, both "no code" because no host passes closed trades to a block yet:
  - `stoploss-guard-halt`: stop entries for 4 bars after 4 or more stop losses in 24 bars (freqtrade defaults) (`TIP/qml/catalogue-seed/wave-1/exits-and-halts/stoploss-guard-halt.json:15-16`, `:44`, `:54`, `:64`).
  - `low-profit-lock-halt`: lock one market for 60 bars when its last trades made too little (`low-profit-lock-halt.json:12-13`, `:41-71`).
- Any risk stop "lands one `lifecycle` event and waits for his click" (`PH:39-40`; `L0:375`). There is no automatic next-day reset for a risk stop.

**[judgment]** This is stricter than every earlier generation. The April and July breakers reset by themselves at the day boundary. A breaker that waits for his click every time two stops land would wake him often.

### 1.7 How WF3 used fire density

- WF3 had four evidence classes; the first was "rolling CB-fire density — circuit-breaker fires per rolling window (`cb_hits_in_window`, reset at daily rollover)" (`ADS:28-29`; `WFA` via `R08` §2.1).
- The flow: CB fires were logged (`CB:159-178`), journals synced in the dead zone (`FLOW:288`), WF3 D2 scored decay, D4 chose a branch, D5 applied it deterministically (`WF3:44-55`).
- Branches: keep; reduce weight (soft trigger, tag `decayed`, "on watch", recover or demote at the next window); demote to demo; retire; rehab via mini-WF2 (`ADS:58-72`; `BRL:300-335`).
- The Portfolio department also watched for "drawdown patterns that precede circuit-breaker events" (`DEPT:183`).
- July re-anchor: "CB-fire density → breaker-door/leash-event frequency", whose natural home is GAP-0012 (`ADS:90-91`). The clash report: decay is live footprint drifting from the certified footprint, including "leash-event frequency vs certified frequency" (`CRA:65-67`, `:83-84`).
- **[judgment]** The counter resets daily, so "density" can only come from the event log (fires per week or per 100 trades). It is a coarse but fast signal. Two fires a day are visible after days, while a CUSUM on R needs about 240 trades to see an edge fall from +0.1R to 0 (`R08:42`).

### 1.8 Planned but never given a number

| Item | Where named | Source |
|---|---|---|
| Loss-streak threshold per tier, band and family | Gen 1 | `CB:50` |
| Fee-burn fraction of the day budget | Gen 1 | `CB:51` |
| Decline-recovery count N | Gen 1 | `CB:52` |
| DPR minimum tier for a hit | Gen 1 | `CB:53` |
| Decay formula, windows, soft and hard thresholds | Gen 1 | `ADS:36-39`, `:103-105` |
| How much "reduce weight" reduces | Gen 1 | `ADS:63-64` |
| Probation exit ("e.g., N winning sessions, no CB fires") | Gen 1 | `BRL:121`; `PRD:975` |
| What fills a slot after a CB hit in a premium session | Gen 1 | `ARCH:241` |
| `F_CHORUS`, `fire_rate_band`, `breaker_expectation` | Gen 2 | `GBF:1289-1298`, `:1477-1478` |
| Whether a breakeven counts | Gen 2 | `WIKI/topics/position-safety-and-sltp-authority.md:85` |
| q and the bench count (evidence only: ~1R, 2 for a scalper) | Gen 3 | `DOCS/components/qmf-risk.md:155` |
| Every halt in the unit build | Gen 4 | `PH:21` |

---

## 2. How a unit came into live trading

### 2.1 Gen 1: WF1, WF2, WF3

R19 §1 covers the stage lists, the older numbering with a real WF4 and the deprecated workflows. The table shows only who did the work.

| Workflow | Agent stages (heavy lifting) | Deterministic stages | Ends |
|---|---|---|---|
| WF1 | S1 intake, S2 archetype, S3 feature stack, S4 BotSpec draft (Development), S6 risk review (Portfolio), S8 report enrichment, S9 evidence pack | S5 composition validator, S7 backtest | Reports and a hand-off token; no registration (`WF1:51-63`, `:169`) |
| WF2 | B diagnosis, C reviewer mail loop, D hypotheses, E mutation plan, F variants, I.1 paper review | G retest, H stress (criteria never written), I.0 registry write | I.2: live only by his A1 click (`WF2:53-66`, `:127-129`) |
| WF3 | D2 decay scoring, D4 triage, D6 rehab | D5 apply keep, reduce, demote, retire | Pool report (`WF3:46-55`) |

- **Registration into paper had no human gate.** "WF2 executes end-to-end autonomously without operator approval gates; the registration decision is agentic-ring deterministic logic" (`PRD:913`).
- Paper windows: scalper 7 trading days, ORB 14, sniper 21, mean-reversion 14, all UI-editable (`PTDS:231-249`).
- Live: Kelly from the bot's own paper record only (`PRD:884`); a ~0.85 probation discount on first live (`PRD:975`); no paper → live move except his authenticated command (`PRD:878`).
- His picture: about 20 bots a day into paper; an agent "on sort of like a timer. After two weeks, it reads the results" (`GPTR:19556`).
- Reality check: only Research and Development were working departments (`BS:108`, `:119`).

### 2.2 Gen 2: July

- Exam gates on two things only: real edge after costs and "not fiction". Everything else becomes measured input for the wallet, leash and chorus (`GBF:412`). G6 §3.2 has the exam numbers.
- His promotion pull lands a unit in `ADMITTED`; birth-in-paper and warm-up moved to the certification side; node paper exists only as a fail mechanism (`WIKI/system/lifecycle.md:24`).
- Agents: the July razor ("anything a deterministic script/hook/plugin can do is NOT an agent") and the personas Cartographer, Coroner, Crowd Watcher, Scout and BMS Reader. R19 §8 covers them.

### 2.3 Gen 4: the unit build

| Step | Who | Source |
|---|---|---|
| A sentence to a verdict or a "death certificate"; a pass ends as a proposal card for a paper trial | agents, with QMB doing the tests | `TPL/b-build-and-prove/README.md:3` |
| A failed unit: sweep its markets and sessions, every try counted | agents plus QMB | `TPL/u2-where-its-rules-hold/README.md:3-8` |
| Paper lane per unit on demo | node | `UPLAN` C-12c (line 3130) |
| Live | his click only | `UPLAN` C-23 (line 3182) |
| One week on demo before live: shown, not enforced | his click decides | `L0:377` |
| Promotion evidence pack: at most three cards (to paper, paper to live, demote, add to book) | agents; **waits for this session's promotion rules** | `TPL/pp-proposal-pack/README.md:3-5` |
| Morning slow lane: journal review, demo fill quality, decay check, pre-session shortlist, weekly market tags, MIS check, data review | scripts first, agents explain, everything is a proposal | `UPLAN` B20 (line 4468); `TPL/s1…s5`, `dc`, `dm`, `t7` |

### 2.4 Where agents carried the load **[judgment]**

- Every generation keeps the same split: agents **produce and diagnose**, deterministic code **gates and applies**, he **promotes**. April put it as "Agents propose; deterministic services dispose" (R19 §8).
- April also let agents decide registration into paper. The unit build turns that into a card for his click. That adds clicks he may not want.
- No generation lets an agent move money, size, or switch a unit off by itself. In Gen 4 even a tightening is a card.

---

## 3. Kill switch and news

### 3.1 Gen 1: the vault

- **News to level** (`KSA:83-92`):

  | Impact | Before | After |
  |---|---|---|
  | LOW | nothing | nothing |
  | MEDIUM | YELLOW at T−5 min | GREEN at T+10 min |
  | HIGH | ORANGE at T−15 min | GREEN at T+20 min |
  | EXTREME | RED at T−30 min | YELLOW 60 min, then GREEN |

- **Scope**: the currency on the event maps to every pair holding it, through the MIS's scope table. "A JPY-impact event at HIGH impact will trigger ORANGE for all JPY-denominated pairs" (`KSA:92`; `MIS:308-322`). If scope resolution fails, block all symbols (`PROT:1126`).
- **Geographic news shifting** (added 1 May) (`KSA:378-460`):
  - Three regions: Asia/Tokyo (JPY, AUD, NZD, CNH; 23:00–08:00 UTC), Europe/London (EUR, GBP, CHF; 07:00–16:00), US/NY (USD, CAD, MXN; 13:00–22:00) (`KSA:386-390`).
  - A HIGH or EXTREME event publishes a `region_shift` directive: block the news region, list the regions still open, end at the settling time (`KSA:392-399`).
  - The risk authority "re-allocates budget to the available-region symbols", so bots strong on London pairs absorb the freed budget (`KSA:409`).
  - No operator approval, by design: "auto-rotate, log, no prompt" (`KSA:412-414`). Two regions in news leave only the third; all three equal global ORANGE (`KSA:421-422`).
- **Three kill modes** (`KSA:316-374`): hard kill (black swan: close everything now, slippage accepted); soft kill for scheduled news (block entries at T−15, exit in 25 % chunks every 2 minutes from T−13 to T−5, flat by T−5, settling 15 minutes after, bot weights at ×0.1 until volatility normalises); connectivity kill (broker-side hard stop on every order).
- **Other triggers**: daily drawdown bands to YELLOW, ORANGE, RED (G3 §4.5; `KSA:96-104`); anomaly detector on slippage, rejections and connectivity (`KSA:110-118`).
- **Calendar**: a daily pull from Forex Factory and MyFXBook, correlated and marked with confidence; a live news provider for unscheduled events (`FLOW:251-270`). Low classification confidence escalates ("fail-safe-up") (`PRD:709`).
- His words: "I have a slow kill a hard kill then the news kill" (`GPTR:1400`); "I need better news so that my news detector can rotate properly" (`GPTR:5871`); the MIS "deals with news trading stoppage… session monitoring and routing" (`GPTR:115`).
- **Contradiction**: news levels clear by timer (`KSA:88-90`; FR21 at `PRD:898`) while "automated triggers cannot de-escalate" (`KSA:312`).

### 3.2 Gen 2: July

- KSA: five levels, four trigger classes (scheduled news, black swan, connectivity, unknown state), escalate-only, a human lowers it (`GBK:13`, `:25`; L8 at `GBF:122`).
- L9: "News-affected currency pairs are blocked for all books in live and paper mode" (`GBF:124`).
- The BMS Exposure desk compiles the calendar daily (Forex Factory first) and sends a news block directive with currency, pairs and a time window. Sessions "may widen a block but may not narrow it". Unknown high-impact coverage blocks conservatively (`WIKI/contracts/ct-bms-04-news-block-directive.md:34-38`).
- Killed: region-shift budget rotation, "because it violates never-redistribute" (DEC-0021, `GBF:2348`); session windows as trading authority (DEC-0025, `GBF:2352`); trading half size through bad conditions (DEC-0019, `GBF:2346`).

### 3.3 Gen 3: current docs

- News is no longer a kill-switch level. It is a **protection window** that blocks new entries on in-scope instruments and nothing else; exits are never blocked (`DOCS/components/qmf-risk.md:131-135`).
- Scope comes from dated per-instrument currency-exposure records, never by reading the symbol name. A missing record means "affected" plus an alarm (`DOCS/components/qmf-risk.md:135`).
- Provider impact labels are stored as given; severity → window is a node mapping. Widths are blank; the ±15 minutes is "withdrawn" (`DOCS/registry/variables.yaml:471-497`).
- A blocked trade is still journaled on the veto path, so "decay sensing keeps its data points" (`DOCS/components/qmf-risk.md:135`).
- The kill switch scopes are global and account stream only (G6 §3.5).

### 3.4 Gen 4: the unit build

- Windows are a local guard on the node's order path (`L0` AD-39).
- The news workflow `t3-news-calendar-watch` builds a daily strip with **30 minutes either side** of each high-impact release (`TPL/t3-news-calendar-watch/README.md:8`). Its watchlist is a static `EURUSD` and `USDJPY` (`:15`). The free calendar has no actual figures, so no surprise is ever found live (`:23`). Per-event fires at T−30, T−5, T+1 are not built (`:25`).
- Kill-switch effects per level are placeholders: YELLOW stops entries, ORANGE also cancels resting entries, RED closes positions at the scope, BLACK closes everything (`PH:34`).

### 3.5 Which instruments and which sessions

- Every generation scopes news by **currency**. Silent everywhere: how a US release maps to US indices, gold, oil or crypto. The dictionary itself says "FX macro event classes and crypto event classes likely need separate vocabularies" (R19 §6).
- Sessions: ten UTC windows with a dominant family each (`SESS:21-32`); the three KSA regions use their own hours (`KSA:386-390`), which do not match the windows.
- Session opens: London–NY overlap warm-up of 25 minutes, ORB entries only, house money off (`SESS:245-275`). Today: a `session_handover_buffer` window kind with no width (G6 §3.12).

---

## 4. Slots and capital between styles

### 4.1 Gen 1: slots

- Three fixed slots. More equity means more dollars per slot, not more slots (`SLOT:19-24`). His memory differs: slots "correlate to the number of… current capital" (`GPTR:19556`). G3 §4.7 records this conflict.
- **Opened and closed**: re-filled at every session-window boundary, and mid-session when a bot is demoted or exits (`SLOT:37`). A slot empties at strike two and at end-of-day rollover (`SLOT:165-171`).
- **Who gets it**: his model was first setup wins (`GPTR:19556`). The vault wrote a scored auction: DPR tier × regime fit × session relevance × family quality × diversification (`SLOT:44-50`), priority T1 dominant family first (`SLOT:70-76`).
- **Empty beats degraded**: the allocator "prefers leaving a slot empty… over deploying a degraded bot" (`SLOT:68`).
- **Inheritance**: house money, loss streak and family spend stay with the slot when a new bot enters (`SLOT:157`).
- **Scalper vs ORB money**: each family had its own daily risk budget, "illustrative" formula only (`SLOT:128-137`). **[judgment]** "Intraday" in his memory most likely means the ORB family.
- **Moving weight between families was a proposal to him.** Portfolio asked "Is capital allocation diversified appropriately across strategy families?" (`DEPT:146`), proposed "slot-priority rebalancing when one archetype family consistently fails to utilise its allocated budget" (`DEPT:179`), and that proposal was "Forwarded directly to operator" (`DEPT:169`). **[judgment]** This is the "BMS opened slots and moved capital, but by hand" he recalls, though in April it was the risk engine plus a Portfolio agent, not a BMS.
- **Automatic moves that did exist**: the regional news shift re-allocated budget to open regions (`KSA:409`).
- Unresolved: slot bumping ("design-intent only", `BS:133`; `ARCH:241`). Gemini's version: the Commander swaps a weaker live position for a higher-conviction sniper signal, keeping the slot count (`GEM:37`). Gemini also named a Regime Match Filter that boosts or mutes family weights by regime (`GEM:35`).

### 4.2 Gen 2: July

- Each Book has its own seed. Only sweep, refund and re-seed cross the Book–Treasury line (`GBF:711`). No redistribution inside a cycle (L4, `GBF:114`); no mid-cycle top-up (DEC-0020, `GBF:2347`).
- Concurrency: `max_concurrent_live_bots` 3 for the scalper Book (`GBC/scalper-book.md:45`, `:59`).
- The intraday Book never existed: "Prop-firm and intraday remain future types" (`WIKI/components/book-template.md:33`).
- His July ruling on an allocator agent: the Allocator's Clerk "has a point" but "BMS already does much of it; reshape around BMS-data understanding" (`BRAIN\decisions\decision-ledger.md:37-38`). His words: "the bms is handling a lot of what it already does" (`V\outputs\session-transcript-qmx-agentic.md:231`).
- Sweep cap 2.5×, re-seed and the refund reserve: G6 §3.8. House money: G3 §4.2-4.3 and G6 §3.11 (absent from every Book source).

### 4.3 Gen 3 and 4

- No allocator in Book/BMS (G4 §4.2). The unit build's cross-unit hook passes every order (`PH:22`).
- The only capital-split tool is `p1-portfolio-combination`, a study that "changes nothing" and waits for this session's method list (`TPL/p1-portfolio-combination/README.md:3-11`).

### 4.4 Self-optimizing ideas

- What self-adjusted in April: the slot auction each session; the premium-session flag "re-earned daily" (G3 §4.4); WF3's reduce-weight branch.
- Gemini: "weight-based slot meritocracy and leaderboard feedback from WF3 live logs" (`GEM:36`).
- July: "book values and metrics get set/adjusted on evidence, not hardcoded whim" (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:72-74`).
- Silent everywhere: a BMS or portfolio layer that opens or closes slots, or shifts money between styles, by itself.

---

## 5. Live drift against backtest

### 5.1 Gen 1

- Fast path: the two-strike breaker demotes to demo (§1.1).
- Slow path: WF3 branches, with reduce weight as the only size lever (§1.7).
- DPR: G3 §5 has the six parts and tiers. New: the breaker reads the **rolling** tier, not the session tier, "not single-session noise" (`CB:118`); consecutive T3 sessions trigger breaker evaluation (`PRS:41`).
- Probation: ~0.85 Kelly discount on first live, auto-flip to full on criteria "e.g., N winning sessions, no CB fires", never set (`BRL:121`, `:132`; `PRD:975`).
- Re-promotion: §1.3.
- **Two journals for life**: demo and live run side by side, kept "for retrospection and for WF3" (`PRD:662-667`).

### 5.2 Gen 2

- Decay is "sustained, measured divergence of a bot's live footprint from its certified footprint" (`CRA:65-67`). Unratified.
- "Sense, do not dispose": the decay service informs; Books, BMS or he act (`CRA:79-91`; `WIKI/attic/topics/alpha-decay-and-performance-analytics.md:74-79`).
- L12: "Graduated policy shrinks before it blocks unless the event class demands instant action" (`GBF:130`). No mechanism implements it. DEC-0019 killed the half-size kill level the same month (`GBF:2346`).
- Paper is a frozen counterfactual, not a proving ground (L13, `GBF:132`). The clash report concluded rehab's "arena is gone" (`CRA:42-50`).

### 5.3 Gen 3

- Decay is judged in R, never cash. Slippage, spread and rejections are never folded into a decay verdict. Two streams are compared only when their cohort keys match (`DOCS/components/qmf-risk.md:111`).
- Results count door refusals and suppressions "so neither our arbitration nor our doors read as decay" (`DOCS/components/qmf-risk.md:157`).
- "Design future alpha-decay… mathematics afresh" (DEC-0092, `DW/ratification-packet.md:208`).

### 5.4 Gen 4

- The nightly decay check compares each unit's last 20 trades with its own record before them (`TPL/dc-decay-and-limit-report/README.md:9`).
- Defaults: record 90 days, recent 20 trades, minimum 20, Watch at a 0.25R drop or 5 losses in a row, Alarm at expectancy ≤ 0R or 8 losses in a row (`:17`).
- It informs only and lands one tighten card per flagged unit (`:3`, `:13`).
- Left out on purpose: the backtest baseline card and its Monte Carlo band, CUSUM and cost tests, because "the risk session settles the decay definition" (`:21-22`).
- A live deployment starts from the paper lane's last calibrated values (`PH:38`).

### 5.5 Research already done

R08 §2.2-2.3 has the outside practice and a proposed check: CUSUM on R, a Monte Carlo cone, cost drift, trade-rate drift, and OK, Watch, Alarm states, with re-loosening only on new evidence. Not repeated.

### 5.6 What no source has

- A **gradual size-down** tied to drift evidence. The nearest pieces: April's drawdown-pressure multiplier and reverse house money (both within-day, G3 §4.3 and §4.6), WF3's unnumbered reduce weight, July's L12, and R08's "Watch = hold size".
- A rule that separates "bad day" from "decay". April's answer was the window: one bad session is not enough (`CB:11`). **[judgment]** His "it can be a bad day" point is exactly this founding principle.

---

## 6. Market isolation and risk-off

### 6.1 What scope each generation could switch off

| Scope | Gen 1 | Gen 2 | Gen 3 | Gen 4 |
|---|---|---|---|---|
| One symbol | news, SQS, kill levels (`KSSL:76-78`) | news pairs (L9) | windows, SQS | windows, SQS, C-22 placement |
| Currency | news (`KSA:92`) | news (`WIKI/contracts/ct-bms-04-news-block-directive.md:36`) | windows by exposure record | windows |
| Region | `region_shift` (`KSA:378-460`) | rotation killed (DEC-0021) | none | none |
| Family | family budget; Regime Match Filter idea (`GEM:35`) | none | none | none |
| Instrument class (FX, indices, crypto) | none; only SQS thresholds per category (`SQS:76-84`) | none | none | class enum exists in records (G7) but nothing keys on it |
| Correlated group | funding gate, 0.3-floor multiplier, Intent Aggregator rule 3 (R19 §2) | exposure desk, cross-Book cap open (GAP-0008) | no evaluator (G4 §5.2) | hook passes all (`PH:22`); `rk2` proposes only |
| Account or global | KSA BLACK, drawdown bands | KSA | KSA global or account stream | KSA effect placeholders (`PH:34`) |

### 6.2 Sensing pieces that exist

- **Chorus** (Gen 2): abnormal loss rate and clustering across a cohort, with a cohort correlation certificate holding an `expected_loss_shape` (`GBF:163`; `GBF:1490-1502`). Records kept a "correlation ledger" of chorus observations (`GBF:1961`).
- **Chaos gate** (Gen 1): a chaos regime was a step-0 block, and physics could zero a trade (G3 §2 step 0 and table row 5).
- **C-22 placement read** (Gen 4, built): a deployment may say "take new entries only on markets the board reads in these words"; a stale or missing board means trade every market on the unit's own rules (`TIP/qmn/src/qmn/app/runtime.py:294-330`). The host relay that feeds it is not built (`OW:53`).
- **MIS cross-market readings** (Gen 4, planned): currency strength, dispersion, herding counts, on This PC, per session or day (`MISC:39`, `:71`). The cross-unit hook "may read" them (`L0:723`).
- **Agents** (Gen 4): `rk2` trips when effective bets fall more than 25 % or one currency passes the guard limit (`TPL/rk2-correlation-drift/README.md:10`); `rk5` replays the SNB unpeg, Brexit night, flash crashes and the COVID week as shocks (`TPL/rk5-stress-tests/README.md:10`); `s2` proposes dropping a market each Sunday (`TPL/s2-tag-units-to-markets/README.md:3`). All propose only; `rk2` and `rk5` wait for the node.
- His July rule on evidence: "If we say we are not trading this pair this week, it has to be backed by a lot of evidence" (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:73-74`).

### 6.3 Silent

- An automatic or evidence-based switch-off of a whole class (crypto, indices, FX).
- A breaker at BMS or portfolio level that counts breaker fires across units. Chorus is the closest and stayed null.
- How the MIS adjusts when a market is isolated. The MIS only publishes; it never blocks (L6, `GBF:118`).
- How SQS joins an isolation decision. SQS blocks per symbol only.

---

## 7. Ideas worth carrying forward

All picks are **[judgment]**; the sources are the evidence for each.

1. **Two breakers, one fast and one slow.** Acute: count qualifying losses per day and bench. Chronic: compare breaker fire density with an expected density. Sources: `BS:131`; `ADS:28-29`; `GBF:1477-1478`.
2. **Derive the expected fire rate, don't guess it.** The unit's own backtest and bootstrap give the chance of two full losses in a day for its win rate and trade count. A live fire rate far above that is decay evidence days before a CUSUM can see it. Sources: July `breaker_expectation`; R08 §1.6 (T5 cone); `R08:42`.
3. **Degrade, don't remove; keep the paper record running.** Benched units keep trading on demo, so evidence keeps flowing and recovery is visible. Sources: `BS:124`; `CB:143-145`; `PRD:662-667`; `DOCS/components/qmf-risk.md:135`.
4. **Tag every fire with its context.** April already marked hits during a regional block (`CB:230`). Extend it to session, market, class, MIS words and news window. Fire density by context then shows "bad market" apart from "bad unit", which is also the input for isolation.
5. **Stack fires upward for isolation.** Many units firing in one class, region or correlated group at once is the chorus signal (`GBF:163`) and his BMS-level breaker idea. The April region shift is the action template: scope resolver, directive with an end time, automatic, logged, his override, configurable maps (`KSA:378-460`).
6. **Isolation needs evidence and an end.** His July rule (`BRAIN\sources\agentic-braindump-2-2026-07-17.md:73-74`), the C-22 stale-board fallback (`TIP/qmn/src/qmn/app/runtime.py:324-330`) and April's `effective_until` (`KSA:398`). Resolve the July conflict first: April moved freed budget to open regions; July's L4 forbids that (`GBF:114`, `:2348`).
7. **Shrink before block.** L12 (`GBF:130`), the drawdown-pressure curve (G3 §4.6), reverse house money (G3 §4.3) and R08's Watch state are the only graded brakes in the record. His "size down, but not quickly" needs one of these with a stated reason.
8. **Settle what a demotion is.** The vault had three answers (§1.3). Pick one: a one-day timeout, an earned return (April's T2 plus 10 positive demo trades plus his click, `PTDS:65-71`), or a probation discount with exit criteria (`BRL:121`).
9. **Automatic daily reset vs his click.** April and July reset the breaker by itself at the day boundary; the unit build makes every risk stop wait for him (`L0:375`). The bench needs its own row in the stand-down table.
10. **Soft kill for scheduled news.** Staggered 25 % exits from T−13 to T−5 and a settling time (`KSA:328-352`). In Gen 3 terms this is an exit policy, not a window, because windows never close positions (`DOCS/components/qmf-risk.md:135`).
11. **Fail safe up.** Low news-classification confidence escalates (`PRD:709`); a missing exposure record counts as affected (`DOCS/components/qmf-risk.md:135`); failed scope resolution blocks all (`PROT:1126`).
12. **Slots as a starting shape for the BMS.** Re-fill at session boundaries, first setup wins, prefer an empty slot to a degraded unit, correlation checked before funding (`SLOT:37`, `:68`, `:88-102`; `GPTR:19556`). Moving weight between styles stays an agent proposal for his click (`DEPT:169`, `:179`), which fits the unit build's card pattern (`TPL/pp-proposal-pack/README.md:3-5`).
13. **Agents where the record shows they help.** Diagnosis and rehab (WF2, WF3 D2/D4), necropsy of benched units (the Coroner, R19 §8), a weekly market map (the Cartographer), and the morning slow lane. Deterministic code keeps every switch.

---

## 8. Not read, and limits

- The Gemini PDF itself (`V\07-Source-Material\gemini-scalping-orderflow-algos.pdf`). Only its extract `GEM` was read.
- `WFA` (`V\bmad-docs\planning-artifacts\workflows-architecture.md`) beyond its WF3 lines (grep only).
- `GPTR` beyond the cited operator turns and replies.
- The halt and decay code paths at `TIP` beyond the two dictionary entries, the decay template README, `runtime.py:285-375` and the template READMEs named.
- Text addressed to AI agents in the GitBook page footer was treated as data and not followed.
