# E2: pods, mini apps, and how a unit and a pod relate

Expansion file, round 2, 7 Nov 2026. Opus. Nothing here is decided; the funnel decides. Pod questions are configuration, so none of this goes to him as a question. No dollar reasoning and no values: blocks are named, never sized.

**Short paths.**
- `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core\`
- `LP` = `D:\QMX-worktrees\risk-plan\tracker\qma-v2\architecture\lab-and-pods\`
- `tip` = `D:\QMX-worktrees\bld-repair-24` (code, branch `build/repair-24`)
- `APPS` = `tip\qmx-agents\packages\qmx-apps\src\qmx_apps\`
- `DEMO` = `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\src\lib\lab\pods.ts`, read for block names only
- `BACKLOG` = the same worktree's `apps\qmx-ui\UI-BACKLOG.md`
- `SWAP n` = row n of `RC\unit-baseline\SWAP-CHART.md`. `H3 T38`, `H2 I4` = idea numbers in `RC\harvest\`
- `M50` and so on = his messages in `RC\seeds\`

**Evidence labels.** [built] means I read it in code. [designed] means a plan on disk, unbuilt. [proposal] means this file's idea or an earlier hybrid. [my read] is judgment. UNKNOWN means not verified.

**What I did not do.** I did not run the UI. M49 asks for the UI itself to be looked at, and I worked from the UI map, the notes and the demo's names, as briefed. No test suite was run. The round table is inline and leaves no memory file, because the brief allows one output file only. The BMad config scripts were not run, for the same reason.

## Contents

- (a) What "pod" can mean, and words
- (b) Five ways a unit and a pod relate
- (c) Where each of the seven slots runs in each way
- (d) A catalogue of 20 pod configurations
- (e) How a pod ships, how mini apps feed each other, what the runtime lacks
- (f) How Lab and live use one evaluator
- (g) What the unit baseline must carry
- Round table, as it happened
- UNKNOWN list

---

## (a) What "pod" can mean

### His two senses, kept apart

| | Sense 1: the stack | Sense 2: the department |
|---|---|---|
| **His words** | "templatize what now, should I call it a pod under a unit" (`operator-words-2026-11-01.md:84`). "the risk management [and position] sizing system as a pod and templatizing it inside the unit" (`:98`). "a scalping based pod or scalping based system" (`operator-words-2026-11-03.md:13`). "question number five is really more of a pod life question" (M49) | "you are looking at a mini app that is optimized for futures... I think in a hedge fund, that's called what? A pod" (M50). "you're having agents that are specialized" and "think of them like departments" (M50). BMS as "the pod manager in a hedge fund. I don't know if that's right" (`operator-words-2026-11-01.md:84`) |
| **What it is** | A recipe: how a trade gets its size and when trading stops | A team: agents, workflows and mini apps specialised in a market or a job |
| **Runs at trade time?** | Yes, or its compiled form does | Never. A mini app cannot sit in the money path: only `trading-node` may name the trading secrets (`APPS\manifest.py:61-63`, `:401-411`) [built] |
| **If it stops** | Trading is affected, by design | Units keep trading. The MIS relay states this rule: "a stopped MIS stops nothing" (`tip\qmx-agents\packages\qmx-host\src\qmx_host\feed_relay.py:10-12`) |
| **Status of the word** | On his screens already | "I think" (M51). He said "a mini app is different also" (M51) |

### Two more meanings hide inside those

Each is a different question, and the word "pod" has been answering all of them.

1. **Who shares money?** "Books are now Pods (each with a live side and a paper side)" (`BACKLOG:8`). Portfolio's pod card shows money, room above the kill line, bots and weights (`LP\UI-TO-BACKEND-MAP.md:122`). So the screen pod is a stack **plus** its members, its money and its place. Sense 1 alone can't explain that card.
2. **How does it arrive?** "pods are meant to be mini apps" (`operator-words-2026-11-03.md:13`) and "how do we ship pods?" (same line). That is packaging. A stack can arrive by copy, by template or inside a mini app.

He also said a hedge-fund pod is "more like the book" (`:13`), and that sits between the two senses. On the record the book word itself "came from a session where I was curious on how hedge funds actually handled this" (`operator-words-2026-11-01.md:50`).

A real hedge-fund pod is all three at once: an allocation of capital with limits, a stack of rules from the risk desk, and a team (`RC\research\R2-trader-practice-windows-drift-isolation-breadth.md:102-105`). So his instinct is fair; the single word just carries too much for a builder.

### Recommendation for words [my read; a default, not a question]

| Word | Means | Where |
|---|---|---|
| **Pod** | The stack: a versioned document with seven slots. Sense 1. It keeps his screen word | Lab, Library, Portfolio, code kind `pod` |
| **Pod deployment** | A pod version plus its members, its share of money, its place and its live or paper side. This is what the Portfolio card shows. The screen can keep saying "pod", as a screen says "unit" for a unit's deployment | Code and docs |
| **Desk** | Sense 2: a mini app or several, with agents and workflows, specialised in a market or job. "Department" is his word and equally fine on screen; "desk" is the trading-floor word and is short in code | Mini apps page, agents session |
| **Mini app** | Stays what it is: the package. No new word for "a mini app that carries pods" | Runtime |
| **Book, BMS** | Retire as words on screen. "Classic Book" survives as a template name (`DEMO:5`, `:335-337`). He already renamed them (`BACKLOG:396`), and "Pod vocabulary may change" (`BACKLOG:37`) | Docs only |

**One sentence joining his senses:** a desk ships and tunes pods; pods trade without the desk.

Avoid two words: "pack" is taken three times (`APPS\road\__init__.py:40`, MIS packs, `X1-H17` packs), and "bundle" is taken by `bundle.tar`. Say "a mini app that carries pods".

---

## (b) Five ways a unit and a pod relate

**What exists today, so the ways can be read against it.** The unit document `qmx.unit/1` already holds `sizer`, `exit_set`, `halts`, `reads` and `numbers` (`tip\qml\src\qml\unit\model.py:470-492`). There is no pod reference. The sizer is called at entry inside the hosted unit (`SWAP 1`). Halts and reads are refused at compile (`tip\qml\src\qml\compile\compiler.py:900-903`). The cross-unit hook is a stub on the node and absent in QMB (`SWAP 6`). Pods are shells: `pod.schema.json` has a bare `slots` object (`SWAP 31`). A compiled-fingerprint change makes the node refuse until a new record exists (`SWAP` 2.3, `qmn\app\runtime.py:559-565,2756`). That last fact weighs on several ways below.

Unit origins come from his M49: "I can have a unit made through the lab... a different type of workflow, or a unit come from a mini app... All of them can trade."

### Way 1. Pod compiled into the unit's own blocks

The pod is a design-time recipe. Compile expands it into the unit's `sizer`, `halts`, `reads`, `numbers`, and the pod disappears. This is his first form: "templatizing it inside the unit" (`:98`), and placeholder 31's own question (`H3` section 4, row 4c).

| Case | What happens at trade time |
|---|---|
| **One unit** | Unit logic, then the compiled sizer and modifiers, then venue fit, all inside the unit's call. The cleanest possible path |
| **200 units** | 200 compiled copies. One pod edit recompiles 200 units, and each compiled fingerprint moves, so the node refuses each until it has a fresh record. No unit can see another's open risk. "One pod" exists only as a source link |
| **Unit from the Lab** | Lab emits a finished unit. Its Lab stack must compile fully or be refused |
| **Unit from a mini app** | Same, if the app can land a `unit` and its blocks. It can't today (e) |

- **Buys:** the unit stands alone, which the rulings want (`RC\grounding\G8-unit-chassis-and-extensibility.md` 6.3). Backtest and node run the same thing. No new stage. Nothing above the unit can fail.
- **Costs:** cross-unit slots have no home (`H3` section 4, row 4c), and his Q5, a portfolio day stop, can't be expressed. Pod edits become mass re-proving. A stage change makes a new unit and wipes the record (`H2` section 4, row "Cross-unit hook").

### Way 2. Pod as a group document above units

The pod is a live document on the node, one per group. Units propose; the host's evaluator answers. This is the Book and BMS shape reborn: "Bots trade; books control bots" (`RC\grounding\G4-current-book-bms.md:50`). It is close to candidates 1 and 2's "one guard above every unit" (`H3` section 2), with their `risk-group` document.

| Case | What happens at trade time |
|---|---|
| **One unit** | Unit proposes, then a group of one sizes it. The machinery is heavier than the job, though it is the same code path |
| **200 units** | One document, one evaluator per place, shared caps native, one edit reaches all at its anchor. A fault in the evaluator stops every entry, never an exit (`H3` T71, `SPINE` AD-4 wrapper) |
| **Unit from the Lab** | Lab pods fit natively. The Lab's unit needs only a reference |
| **Unit from a mini app** | A unit carrying its own sizer collides with the group's. A precedence rule is needed |

- **Buys:** one place for everything, one rank table, one edit, and agents watch pods instead of units.
- **Costs:** the unit's own sizer socket and five shipped halt blocks go unused (`SWAP 5`). A unit no longer stands alone. A scalper's brake sits in a shared stage, away from the unit it serves (`candidate-3` argument, `H3` T6). A QMB host call must be built (`SWAP 6`).

### Way 3. Pod as a mini app

The pod is a mini app. Two different things hide in this phrase, and they must stay apart.

- **3a, the mini app as package.** It lands documents and runs nothing at trade time. This isn't a relation at all: it sits on top of any other way. See (e).
- **3b, the mini app as controller.** The app's agents and jobs watch off-path and publish rulings: shares, stand-downs, factors, number moves. The node reads the last published ruling with its age and applies it. The MIS board is the working example: a feed file that can only hold back entries, and a stale board falls back to trading (`H3` T43, `tip\qmx-agents\packages\qmx-host\src\qmx_host\feed_relay.py:10-14`).

| Case (3b) | What happens at trade time |
|---|---|
| **One unit** | Unit uses its own sizer, reading the last ruling as a fact |
| **200 units** | One app rules for all. Agents carry the load, as he asked: "Why not just have an agentic workflow... As a mini app" (M49). But each brake is as late as the last ruling |
| **Unit from the Lab** | Runs as a unit; the app adds rulings if pointed at it |
| **Unit from a mini app** | Natural: the app that made it keeps watching it |

- **Buys:** it matches his "pods are meant to be mini apps" and his department picture. Rich logic and agents, no node change per idea, and no signature per idea.
- **Costs:** an app is `shows` or `runs` and can't be atomic with an order. A shared cap needs the order and the count together, and a fast brake can't wait for a relay pass (`feed_relay.py:37` defaults to a 5 second pass). The app's ledger is a late copy of the journals. It can't be what a floor trusts. A scalper gains nothing here. The relay is written and has no production importer: a search of `tip` outside tests finds none [built].

### Way 4. No pod at all

A unit carries its own parts. Presets give starting points. Grouping is a tag, and one portfolio config holds what's left (`X1-H40`, `H3` T36). "Pod" is a saved view on a screen, computed from the units it filters.

| Case | What happens at trade time |
|---|---|
| **One unit** | As Way 1, with no compile step for a pod |
| **200 units** | 200 profiles with tag drop-ins and one config. Rules apply across tags, overlapping, strictest wins (`X1-H34`). "Isolate crypto" is one rule. No object exists to test head to head, version or promote |
| **Unit from the Lab** | The Lab has nothing to design. Its Pods bench becomes a preset editor |
| **Unit from a mini app** | Simplest: a unit is a unit |

- **Buys:** fewest words and fewest documents, closest to "design for complexity, never a complex system". No level to invent.
- **Costs:** it contradicts screens he treats as real. The Pods bench, Pods shelf and Portfolio pods all lose their object (`LP\UI-TO-BACKEND-MAP.md` F to I). Comparing two whole configurations needs a new idea anyway, and that new idea is a pod. A tag has no persisted record (`X1` gap 5). Strictest-wins stacks caution, which risks his "sitting duck" (`X1-H34` weakest link).

### Way 5. One pod document, split by scope

There is one pod document. Each block says where it may run (`H3` T6 made this point for rows). At deploy, unit-scope blocks run in the unit's call, cross-unit blocks run in one group stage on the node, and slow blocks run off the order path at anchors and publish a fact. **An empty slot means "use the unit's own block".** So "no pod" is not a special case: it is the empty pod.

Order of events on the node [proposal]:
1. Unit logic gives an entry and a stop, as today (`SWAP 2`).
2. Sizer, then throttles, then unit-scope caps. The pod's block if the slot is filled, the unit's own if empty. Answer: dollars at risk, with a trail.
3. Group stage: shared caps and group guards. They may only cut or refuse (a raise is decided at step 2 from a published fact).
4. Venue fit turns dollars into whatever the instrument takes.
5. Fill goes to the ledger. Exits never enter steps 2 and 3 (`CHECK` B3, `H3` section 2 "One wrapper").

| Case | What happens at trade time |
|---|---|
| **One unit** | Group stage has nothing to do: it is one call that returns "no cut". In effect Way 1 |
| **200 units** | One document, 200 references, one shared stage per place. An edit rolls out by a deployment's pin, so 10 members can try the new version first (`H3` T51). A unit's logic fingerprint stays still when only its pod changes, if the pod has its own fingerprint (g, row 3) |
| **Unit from the Lab** | The Lab's stack is this document, and the unit holds a reference (`LP\ARCHITECTURE-SPINE.md` AD-10) |
| **Unit from a mini app** | It trades alone with its own blocks in an empty pod, or joins a pod that fills only some slots |

- **Buys:** all four origins work with no special case. Pod-life questions become fields. The two-stage cost is small: candidate 3's property test showed two cut-only stages equal one table over 20,000 random states (`H3` T6, a model test).
- **Costs:** the most new contract of any way. Block rows need a placement field, composition rules per slot, a pod reference on the deployment and a separate fingerprint. "Where did this size come from?" must be answered by a trail that crosses two stages.
- **Limit:** a pod's home is one place (`LP\ARCHITECTURE-SPINE.md` AD-8). A cap can't be atomic across two machines, so a pod spanning places is a mix of pods with shares (Pod 14).

### The ways side by side

| | Way 1 compiled in | Way 2 group doc | Way 3b controller app | Way 4 no pod | Way 5 split |
|---|---|---|---|---|---|
| Unit stands alone | Yes | No | Yes | Yes | Yes when alone; shared stage when grouped |
| Shared caps | No | Yes | Late only | At the config | Yes |
| One edit for 200 units | No, mass re-proof | Yes | Yes | Tags only | Yes, by pin |
| Compare two whole setups | Awkward | Yes | Awkward | No object | Yes |
| Agents have a thing to watch | Unit | Pod | App | Tag | Pod |
| New core work | Least | Medium | Relay plus rulings | Least | Most |
| Seam has two adapters today | Unit host in node and QMB | Node only | Board only | As Way 1 | Same core, node and replay |

**My read.** Way 5 as the relation; Way 3a as the way it ships; Way 3b for slow rulings only (allocator, slow inputs). Way 1 and Way 4 survive inside it, as one unit and as the empty pod. That keeps every origin he named and leaves room without forcing a pod on anyone. It also costs the most contract, and the funnel should weigh that against "too much machine". If the funnel wants less, the honest fallback is Way 1 plus a thin group document with only caps and a ledger.

**Deep-module check on Way 5** (codebase-design vocabulary). The core is one module with a small interface:

```
decide(stack, state, facts, intent) -> Answer{ dollars | refuse, trail, state' }
on_fill(stack, state, fill) -> state'
at_anchor(stack, state, facts) -> published_facts, state'
```

- **Deletion test:** delete it and size logic reappears in `unit.py`, `runtime.py`, `unit_handler.py`, the Lab simulator and `paper.step`. It earns its keep.
- **Two adapters:** node and replay, so the seam is real.
- **Way 3b's seam** has one adapter (the board), so a general ruling relay is still a hypothetical seam. Build it when a second reader arrives (`T43` needs one).

---

## (c) Where each of the seven slots runs in each way

The slots come from `LP\ARCHITECTURE-SPINE.md` AD-10 and `DEMO:10-18`. Venue fit is not a slot and always runs last; today it is `qml\numbers\convert.py:88`, re-applied by the hosts (`SWAP 12`).

**A finding from building this table:** the slots don't share one clock, and that matters more than where they sit.

| Slot | Natural clock | Must it be atomic with the order? |
|---|---|---|
| Inputs | Fed continuously, read at decision | No |
| Guards | Per bar and per order | Yes for a stop on new entries |
| Allocator | At an anchor | **No.** It publishes a share; a trade reads the share as a fact |
| Sizer | Per entry | Yes, same call |
| Throttles | Per entry | Same call, reading facts |
| Caps | Per order | **Yes for shared caps** |
| Ledger | Per fill | Written after, read before |

So the allocator is off the order path in every way, including Way 2. That also answers "facts move live, numbers at anchors" (`H3` T25).

| Slot | Way 1 | Way 2 | Way 3b | Way 4 | Way 5 |
|---|---|---|---|---|---|
| **Inputs** | Unit's `reads` and bindings, refused today (`compiler.py:900-901`, `930-936`) | Fact kernel beside the group evaluator | App computes off-path; relay copies to node; read with age | Each unit's `reads` | Each block declares needs; compile compares with what the place provides (`H3` T18). Published readings arrive by relay |
| **Guards** | Unit `halts`, three scopes, refused today (`SWAP 5`). Its "account" scope sees only itself | Group evaluator at the order hook (`SWAP 6`) | App publishes a stand-down; node applies at next read. Slow brakes only | Unit halts plus tag rows in the config | Unit-scope in the unit's call; cross-unit in the group stage |
| **Allocator** | No home. A share frozen on the deployment, refreshed from outside | At anchor; writes shares to status | Natural home: an agent or job proposes shares | Named split rule in the config (`H3` T5) | Off the order path at anchor; result is a fact. On PC or node by its place |
| **Sizer** | Unit socket (`unit.py:785-793`) | Host sizes; unit's socket unused | Stays in the unit. App may only feed parameters | Unit socket | Pod's if filled, else unit's, called from the same position. A dollars rule, then the converter (`H3` T4) |
| **Throttles** | Chain in the unit. `sizing_modifier` must stop refusing (`compiler.py:107-117,438-443`; `SWAP` E2) | Chain in the group evaluator | Published factor read at entry | Unit chain, tag drop-ins | One chain, in the unit's call. A group-signal throttle reads the group's ledger as a fact |
| **Caps** | Own-unit limits only. **A shared cap can't be expressed** | Native | **Can't be atomic.** App sets a limit, node must enforce it, so the slot's real home is the node | Config, at the guard | Own-unit caps in the unit's call; shared caps in the group stage |
| **Ledger** | Unit status file. Group view is a later report | Group ledger on the node, one fold (`H3` T59) | App's own `app.db`, a late copy. A brake can't trust it | One per unit, one for the config | One fold keyed by scope id, including pod. PC gets a copy |

**The exit gap.** The seven slots have no exit slot, yet "the Book owns the exit" (`G4:61`) and a scalper's risk management largely is fast invalidation (`SEEDS` A9). Under all five ways I keep ordinary exits on the unit, since an exit changes what a trade's R means (`H3` section 4, rows 8 and 8b). Forced closes live in guards with a `flatten` verb. A pod can name the exit abilities it needs, and a **unit template** can carry exits, a pod reference and presets together. His "scalping based system" (`operator-words-2026-11-03.md:13`) is that template, not the pod alone. The round table disagrees (see the end).

---

## (d) A catalogue of 20 pod configurations

Blocks only. **Plain name** = in the demo's list (`DEMO:33-260`). **`s:`** = ships in QML stdlib at `tip\qml\src\qml\blocks\stdlib\`. **`n:`** = new block, which is content someone writes. "Empty" means the unit's own block applies. None of these has run, and all are ingredients.

### From the old relentless system

**Pod 1. Relentless.** April's vault system, `G3` section 2. Half-Kelly, many multipliers, lowest cap wins.
- Inputs: `n:session-window-clock`, `n:rvol`, `n:chaos-measures`, `n:spread-depth-score`, `n:own-paper-record`
- Guards: `kill`, `news-kill`, `n:warm-up`, `n:net-payoff-gate`, `s:account-daily-loss-halt`
- Allocator: `n:family-slots`
- Sizer: `kelly`
- Throttles: `n:bot-rating`, `n:session-multiplier`, `n:house-money-step`, `n:rvol-scale`, `n:chaos-scale`, `n:correlation-penalty`, `n:drawdown-pressure`, `n:micro-scale`, `n:streak-attenuator`
- Caps: `n:family-slot-cap`, `n:equity-band-cap`, `n:open-risk-ceiling`, `n:family-budget`, `n:day-loss-left`
- Ledger: `n:equity-at-each-trade`, `n:equity-band-daily`
- **Variant, "as it was coded":** drop `n:family-slot-cap`. `G3` section 3 found that the per-trade cap never reached the final minimum in old code, and that this may explain what he remembers as "that thing can't lose". One block out makes a different animal, which is the whole argument for a stack.
- Asks of the baseline: a multiply combiner, a lowest-wins combiner, per-family shared state, live equity (`SWAP 17`).

**Pod 2. Session relay.** One pot passing through the day's sessions; the "seven total sessions" picture (`G3` 4.1).
- Inputs: `n:session-window-clock`, `n:window-record`
- Guards: `kill`
- Allocator: `n:dominant-family-by-window`
- Sizer: empty
- Throttles: `n:measured-window-lift` (`H2` I24)
- Caps: `caps`
- Ledger: `n:session-chain-ledger`; deliberately no per-session cap (`G3` section 2)
- Asks: `sessions` must stop refusing (`SWAP` E6), and a record split by session (`H2` section 4).

### From the Book

**Pod 3. Classic Book.** The docs' ladder from `G4` 3.4. The baseline in every comparison, as the demo says (`DEMO:337`).
- Inputs: none
- Guards: `kill`, `streak`, `brakes`, `n:protection-windows`, `n:sqs-gate`
- Allocator: empty
- Sizer: `n:cushion-runway` (reads capital at period open, floor, periods, loss-run allowance; one floor read by sizing and by the kill line)
- Throttles: none
- Caps: `caps`, `n:account-constraints`
- Ledger: `n:period-open-equity`, `n:virtual-ledger`, `n:sweep`
- Asks: kill line's verb (`SWAP 20`), bench to paper (`SWAP 23`, `24`), control rank table as data.

### House money and reverse house money

**Pod 4. Cushion pair.** One rule, one ledger; the anchor decides what it is. Fixed anchor presses and cuts; running-peak anchor only brakes (`R9` 0.4, `H2` I4).
- Inputs: none
- Guards: `kill`
- Allocator: empty
- Sizer: empty
- Throttles: `n:cushion-rule` (shape swappable)
- Caps: `n:press-share-of-profit`
- Ledger: `n:cushion-ledger` with anchor type, clock and scope
- Asks: anchor and scope as rows (`H2` section 4). This answers Q4: the "rule I approve" is simply a block with its own gate, `n:press-gate`.

**Pod 5. The old pair, as it really was.** Not mirror images: money from a day anchor, count of losses in a session (`R9` 0.4).
- Inputs: `n:session-window-clock`
- Guards: `kill`
- Allocator: `n:family-slots`
- Sizer: empty
- Throttles: `n:house-money-step`, `n:streak-attenuator` gated to `n:orb-led-windows`, combined by product
- Caps: `caps`
- Ledger: `n:slot-day-ledger`, where a unit entering a slot inherits it, to stop cash-out by rotation
- Asks: a slot identity apart from the unit.

### From his scalper-first plan

**Pod 6. Scalper first.** "we are starting with scalpers" (M49). Costs observed and acted on (M51). Fast invalidation counted properly (`SEEDS` A9, `H2` I6, I16).
- Inputs: `n:cost-cell`, `n:spread-reading`, `n:news-calendar`, `n:realised-loss-spread`
- Guards: `kill`, `n:skip-own-news-day`, `n:sqs-gate`, `cooldown`, `s:session-fill-limit-halt`, `s:session-loss-limit-halt`
- Allocator: empty
- Sizer: `n:dollars-from-real-loss`
- Throttles: `n:cost-taper`, `thin-hours`, `n:money-streak` (a cut costs its size, a breakeven costs its fees)
- Caps: `liq-cap`, `n:same-bet-cap`, `n:tail-budget` (`H2` I29)
- Ledger: `n:money-ledger`, `n:event-ledger`
- Asks: exit stack with all three verbs (`SWAP 3`, `4`, `9`), the cost cell written from fills (`H2` section 4), several positions (`SWAP` E4). This pod stress-tests the baseline hardest.

**Pod 7. Human mimic.** A unit trading like a person reading flow, in chosen windows (M50). The order-flow reading itself belongs elsewhere (M51).
- Inputs: `n:order-flow-reading`, `n:sniping-window`, `regime-input`
- Guards: `kill`, `n:window-only`
- Allocator: empty
- Sizer: `n:conviction-step` (`H2` I41)
- Throttles: `n:measured-window-lift`
- Caps: `n:burst-cap`
- Ledger: `n:window-record`
- Asks: unit passes a conviction number to its sizer by a binding (`compiler.py:930-936`).

**Pod 8. Best basket.** "Why not look for the best basket" (M50). Few units until capital allows volume (`H2` I17).
- Inputs: `n:instrument-feasibility`
- Guards: `kill`
- Allocator: `n:few-best-by-feasibility`, `n:open-next-slot-on-pot`
- Sizer: `n:cushion-runway`
- Throttles: none
- Caps: `n:same-bet-cap`
- Ledger: `ledger-usd`
- Warning kept: ranking by recent results chases noise (A1-103, `H2` I17).

**Pod 9. Stage switcher.** "at 5,000, the math changes drastically" (M51). A declared stage line swaps the sizing rows at an anchor (`H2` I27).
- Inputs: none
- Guards: `kill`
- Allocator: `n:stage-selects-member` (members are other pods)
- Sizer, throttles, caps: from the selected member
- Ledger: `n:stage-line`, `n:banker-acts`
- Asks: a pod changes a unit's rows at an anchor **without a new unit identity** (`H2` section 4). The seat that matters most on this list.

### From prop firms

He set prop firms aside for himself (`G1:65`, `BACKLOG:8`) and called buffers "only explaining" (`SEEDS` T11). These are content for other users, and a good test of the canvas.

**Pod 10. Prop rider.** Rule sheet as data (`R9` 4.4, `X5-H22`).
- Inputs: `n:firm-rule-sheet`
- Guards: `n:daily-loss-marked-equity` on the firm's own reset clock, `n:total-loss` (static or trailing), `n:best-day-consistency`, `n:news-lockout`, `n:profit-lock-wind-down` (A2-058)
- Allocator: empty
- Sizer: `n:largest-size-keeping-floor-odds` (`H2` I20)
- Throttles: `n:goal-taper` (`H2` I25), `n:buffer-taper`
- Caps: `n:firm-max-contracts`
- Ledger: `n:firm-anchor-ledger`
- Asks: marked equity (`SWAP 17`), a named clock per rule.

**Pod 11. Earned tiers.** Strongest live pair found: one signal both ways (`R9:35`, `H2` I22).
- Inputs: none
- Guards: `n:day-loss-tied-to-tier`
- Allocator: empty
- Sizer: empty
- Throttles: none
- Caps: `n:tier-ladder` (rise only after dwell, fall the same day, counter resets on drop-out, no skipping, no rise mid-session)
- Ledger: `n:tier-record`
- Asks: dwell and direction fields on the row (`H3` T27).

### From hedge-fund pods

**Pod 12. Multi-manager.** Soft stop cuts capital, hard stop ends it; the firm re-sizes later; none restores by itself (`R9:465-469`, `R2:102-104`). The BMS as "pod manager" (M7).
- Inputs: `n:driver-tags`
- Guards: `n:soft-stop-step-down`, `n:hard-stop-out`
- Allocator: `parity`, `n:firm-re-sizes-by-card`
- Sizer: empty, each member's own
- Throttles: `n:de-gross-before-stop`
- Caps: `corr-cap`, `n:factor-cap`, `n:parent-limit`
- Ledger: `n:high-water-mark`
- Asks: `pod:` scope key, a brake that benches a whole pod, restore by rule or hand as a field.

**Pod 13. Own size, capped total.** Direct answer to "the more units I have, the less I can trade" (M49). Each unit keeps its own size; only the total on losing together is capped (`X1-H38`, `H2` I3, `H3` T5). **Variant, lending:** guaranteed share plus burst from idle slack (`H2` I39).
- Inputs: `n:losing-together-stat`
- Guards: `kill`
- Allocator: `n:no-split`
- Sizer: empty
- Throttles: none
- Caps: `n:parent-limit`
- Ledger: `ledger-usd`
- Asks: allocation mode as a named row. The spine has no row for this mode today (`H3` T5).

**Pod 14. Run together.** A pod of pods (`LP\OPEN-DECISIONS.md` OPEN-4). Also how a group spans two places.
- Inputs: none
- Guards: `n:top-level-stop`
- Allocator: `n:split-across-pods`
- Sizer, throttles: from members
- Caps: `n:parent-limit`
- Ledger: `ledger-usd`
- Asks: `members` and `parent` (`H3` section 4, row 5c).

### Instruments, models, agents, starters, and the reckless one

**Pod 15. Futures desk pod.** His week-long example (M50). Mini and micro as separate rows.
- Inputs: `n:roll-calendar`, `n:exchange-session-clock`, `n:margin-facts`
- Guards: `n:roll-stand-down`, `n:spec-change-stand-down`, `s:equity-drawdown-halt`
- Allocator: `n:opening-range-priority`
- Sizer: `vol-target`
- Throttles: `n:gap-factor`
- Caps: `n:worst-step-reserve` (`H2` I21), `n:margin-headroom` (`H2` I30), `n:contract-tier`
- Ledger: `n:per-contract-record`
- Asks: instrument rows and roll as a version event (`X1` gap 4), leverage change wiring (`SWAP 15`).

**Pod 16. Model-sized hybrid.** From the demo's gallery (`DEMO:375-378`).
- Inputs: `regime-input`, `vol-input`
- Guards: `kill`, `brakes`
- Allocator: empty
- Sizer: `model-sizer` under a rule ceiling
- Throttles: `regime`, `ladder`
- Caps: `caps`
- Ledger: `ledger-usd`
- Asks: where a model runs at trade time; a needs row that says the place can run it (`H3` T40).

**Pod 17. Watched by agents.** "Why would I have to be there monitoring units?" and "a unit whose edge was never real" (M49).
- Inputs: `n:paper-twin-gap`, `n:random-entry-twin`, `n:decay-reading`, `n:agent-fact-with-expiry`
- Guards: `n:edge-doubt-card`
- Allocator: `n:bounded-share-moves`
- Sizer: empty
- Throttles: `n:read-agent-fact`
- Caps: `caps`
- Ledger: `n:would-have-rows`
- Asks: would-have writer (`SWAP 29`), proposal door (`H3` T56). A pod rule reads a published fact; an agent's power is a field. **Open tension:** "agents never touch money" against a cut that applies itself. Default: a card. UNKNOWN whether an automatic cut inside bounds crosses his line.

**Pod 18. Volatility core.** Demo template (`DEMO:310-325`).
- Inputs: `vol-input`
- Guards: `kill`, `brakes`
- Allocator: `parity`
- Sizer: `vol-target`
- Throttles: `ladder`, `thin-hours`
- Caps: `caps`, `corr-cap`
- Ledger: `ledger-usd`
- Note: volatility scaling double-counts for stop-sized units (`H2` I33). Blocks can warn about each other.

**Pod 19. Canary.** Smallest possible, for a newcomer's first run (`DEMO:370-373`).
- Inputs: none
- Guards: `kill`
- Allocator: empty
- Sizer: `fixed-usd`
- Throttles: none
- Caps: `n:one-position`
- Ledger: `ledger-usd`
- Asks: nothing. This is the out-of-the-box default.

**Pod 20. Full press.** The brief says a reckless setup must be expressible.
- Inputs: none
- Guards: none
- Allocator: empty
- Sizer: `kelly` at its full setting, or `n:martingale-sizing` (`H3` T23 names it)
- Throttles: none
- Caps: none
- Ledger: `ledger-usd`
- Asks: the demo's `required: true` on `kill` (`DEMO:168`) and "Send to paper requires kill line set" (`LP\ARCHITECTURE-SPINE.md` AD-10) become **preset warnings, not refusals**. The hidden-ruin audit grades it and says so plainly (`H2` I28). Fixed lines still hold: exits never blocked, the kill switch stays his to lower.

### Which way can express which pod [my read, nothing tested]

Y = yes. P = partly. N = no. In brackets, why.

| Pod | Way 1 | Way 2 | Way 3b | Way 4 | Way 5 |
|---|---|---|---|---|---|
| 1 Relentless | P (no family budgets) | Y | N (caps) | P | Y |
| 2 Session relay | P | Y | P | Y | Y |
| 3 Classic Book | P (one Book per unit) | Y | N | P | Y |
| 4 Cushion pair | Y at unit scope | Y | N (per trade) | Y | Y |
| 5 Old pair | P (no slot) | Y | N | P | Y |
| 6 Scalper first | Y | Y (slower to read) | N | Y | Y |
| 7 Human mimic | Y | P (conviction crosses a stage) | N | Y | Y |
| 8 Best basket | N | Y | P (slow, proposes) | P | Y |
| 9 Stage switcher | N (new identity) | Y | P | N (new version) | Y |
| 10 Prop rider | Y for one account | Y | N | Y | Y |
| 11 Earned tiers | Y | Y | P | Y | Y |
| 12 Multi-manager | N | Y | P | P (no pod ledger) | Y |
| 13 Capped total | N | Y | N | Y | Y |
| 14 Run together | N | P (`parent`) | P | N | Y |
| 15 Futures desk pod | P | Y | N | P | Y |
| 16 Model hybrid | P (model on node) | P | P | P | P |
| 17 Watched by agents | P | Y | Y | P | Y |
| 18 Volatility core | P (no parity) | Y | P | P | Y |
| 19 Canary | Y | Y | Y | Y | Y |
| 20 Full press | Y | Y | Y | Y | Y |

### Pod-life answers as fields (his Q1, Q4, Q5)

| What the old page asked him | As configuration |
|---|---|
| Q5: may a portfolio day stop raise the kill switch? | Guard row field `on_fire`: stand down at a scope, raise a kill level, or send a card. Each pod chooses. Lowering stays his hand (`H2` I11) |
| Q1: may a rule close a position? | A guard verb (`none`, `no_new_entries`, `reduce`, `flatten`), and the dictionary's exits (`H3` T13) |
| Q4: press after a record passes a rule | `n:press-gate` as a block in Pod 4 |
| Stand down, come back | Attack, release, restore on the row (`H2` I5) |

---

## (e) How a pod ships, and how mini apps feed each other

### Four ways to ship, smallest first

| Level | What ships | How | Needs |
|---|---|---|---|
| 1. A pod | One `pod` document, referring to pinned blocks | Library item, copied. Also one file, for "a file extension for it" (M50): a `.qmxpod` or `.qmxunit` zip with the document and its pins [proposal] | `pod` kind gets a real schema (`SWAP 31`) |
| 2. A pod plus its new blocks | Above, plus `component` items | Lands by a door that saves blocks. That door doesn't exist (`SWAP` 2.2) | `blocks_save`, contract test on Library blocks (`SWAP` E11) |
| 3. A mini app carrying pods | Manifest listing pods, blocks, presets, scenarios, workflows, skills, self-test card (`X1-H30`) | Install, then items land as drafts. "an install card that shows what the app asks for; new or agent-built apps install disabled until he approves" (`RC\..\qma-v2\UI-NOTES.md:89`) | The gaps below |
| 4. A desk | Level 3, plus agents, workflows, screens and feeds to other apps | Runs as an app: `kind = "both"`, `risk = "runs"` | The gaps below, plus methodology and agents sessions |

The rule from n8n carries over directly: a saved thing stores **only what differs from its preset, and each block's version** (`R1` 4.2 to 4.5, `H3` T9). Blocks declare their fields beside their code, so forms come free (`H3` T8). Packages are installed from inside the product. VS Code's lesson, which he named for mini apps (`M31`), is the same: a manifest declares what it contributes, and the host loads it.

**The money rule, unchanged.** Nothing a mini app lands reaches a node except what the host compiles from landed, checked items, with his promote click (`X1-H30`, brief's fixed lines).

### Three roads between mini apps, one to a unit

"mini apps can provide output and input for other mini apps" (M50).

| Road | What it does | Status |
|---|---|---|
| **A. Artifact feed** | App A's job returns an output under `[provides.x]`. Host validates and stores it, returns a ref. A caller passes the ref under B's declared `[feeds.x]`. B gets an immutable copy; no shared database (`README.md:57-64`, `APPS\artifacts.py:260`) | [built]. `stale_after` is built. A publish that breaks a consumer's schema is refused and names the consumer (`artifacts.py:16-18`, `:406`). Someone must carry the ref: there is no subscription |
| **B. Library landing as event** | A output lands in the Library. An `event` trigger on the Library ref log fires B's workflow (`tip\qmx-agents\packages\qmx-engine\src\qmx_engine\triggers\event.py:1`). `emits` and `accepts` are retired for this reason (`APPS\manifest.py:94-95`) | [built] for what lands. Only `qmb-run` lands today |
| **C. Proposal to a pod** | A desk proposes a new pod version or a moved number as a card | Partly. Cards exist; the door to a pod doesn't (`H3` T56) |
| **D. Reading to a unit** | A published reading reaches a unit's `reads`, on the node, with its age and a fallback | **Not built.** `reads_not_built` (`compiler.py:900-901`). The only road is the MIS board, can only hold back entries, and its relay has no production caller (`H3` T43) |

### His futures week, walked through [proposal]

1. A `futures-desk` mini app, `risk = "runs"`, installs. `[profiles]` gives one partition per contract family, `mini` and `micro` (`APPS\supervisor.py:852-865`) [built].
2. Copilot and agents work through a week (M50). Its jobs land research notes, a `pod` draft (Pod 15) and new blocks. These land through a lander.
3. An `event` trigger fires an `fx-desk` workflow on a macro-structure note, by road B. Road A works too.
4. A hill-climb job re-sizes the recorded trades under each pod draft (`H2` I1, I37), counts each try, and lands the survivors.
5. A unit template lands as a draft: exits, pod ref, presets. Unit drafts go through `unit_check` and compile. A paper run starts on his yes (`LP\OPEN-DECISIONS.md` closed OPEN-3).
6. He promotes. The node gets a compiled unit and a compiled pod. **Stop the desk and the units keep trading.** The desk's next reading just ages (road D).

Three unit origins, one door: a copilot-written unit needs no mini app at all. It uses `pods.patch` and `unit_new`.

### What is missing in the runtime

All [built] facts at `tip`; the "kind" column applies the brief's test.

| # | Gap | Evidence | Kind | If left out |
|---|---|---|---|---|
| 1 | An app names at most one lander, and only `qmb-run` is registered | `APPS\manifest.py:251-261`; `qmx_host\host.py:1912`, `:2607-2653` | **Seat:** a core `library-items` lander | Pods can't ship by app. Core rework later |
| 2 | Landers are run-shaped: opened per job (`lander.open(app, version, job, inputs, principal)`) | `host.py:2161`; `APPS\supervisor.py:1450-1467` | **Seat:** static content lands at publish, produced content through a job | A pod bundled in an app has no moment to land |
| 3 | A published pack holds `plugin.json` and `skills/` only | `APPS\road\__init__.py:33-36`, `:56-70` | **Seat:** declared `library/` folder in the pack | Same |
| 4 | `pod`, `pod-block` are shells; `template` is `retired: true`, though the Lab expects `template` items with `instantiates = pod` | `kinds\pod.schema.json`, `pod-block.schema.json`, `template.schema.json`; `LP\UI-TO-BACKEND-MAP.md:92` | **Seat:** real schemas, un-retire template | Nothing to land, no gallery, no out-of-the-box |
| 5 | No row saves a block; `blocks_check` only checks | `SWAP` 2.2 | **Seat** | Agents draft and he hand-saves. "The unit is what ideas become" stops short |
| 6 | Two block worlds: `pod-block` (form, graph, code, model) and QML `component` | `H3` T39; `kinds\pod-block.schema.json` | **Seat:** one catalogue; a form or graph compiles to a block | Two loaders, two contract tests |
| 7 | `reads` refused; relay is MIS-only and unwired | `compiler.py:900-901`; `feed_relay.py:40`; no non-test importer | **Seat:** declared feed to a node, with age and fallback | Desks can't reach units. Rework of node feeds later |
| 8 | No app-level `requires`: an app can't state it needs another app or a feed | `APPS\manifest.py:228-245` has no such field | **Content now,** a small field. The needs list can cover pods | Install gives a working app with a dead feed, unexplained |
| 9 | No subscription: a caller must pass the artifact ref | `README.md:60`; `supervisor.py:1279-1281` | Content: a workflow does it through road B | Each desk writes wiring |
| 10 | No way to pin or upgrade a landed item across units: no forwarding map, no offer | `H3` T49, T52; `SWAP` E16 (identity table unwired) | **Seat** | Upgrading 200 units means 200 hand moves |
| 11 | Agent-written code installs only at T2 (Docker) or after review; T1 is a convention, not a sandbox | `README.md:14-15`, `:38-41`, `:74-75` | Not this session (agents and harness). A pod as **data** needs no sandbox; a block with **code** does | Agent-made blocks wait on review |
| 12 | `build-mini-app` skill is a placeholder; no `build-pod` skill | `tip\qmx-agents\plugin\skills\build-mini-app\SKILL.md` | Content | Copilot can't do his week |
| 13 | A Library block reaching a node: `gather` reads Library `component`s, but the node path for one is unknown | `SWAP` 2.2. UNKNOWN beyond that | **Check first** | A landed block might work in QMB and not live |
| 14 | A new stdlib block bumps the money app's version and needs his signature | `SWAP` 2.2, Call 11 | Note | A pod core inside QML is a signature per change. Blocks should live outside it |

**Good news on the same runtime.** Hash-locked immutable images, refused rewrites, `shows`/`runs`/`money` classes, breakers, volumes, `[profiles]`, schema gates at publish, event triggers, MCP operations, agent and workflow entry points, `DockerSupervisor` for T2 (`README.md`). The mini-app runtime is much closer to shipping pods than the unit is to receiving them.

---

## (f) How Lab and live use one evaluator

**The conflict.** `LP` AD-10 makes `qmx_lab.pods.simulator` "the one evaluator" behind every pod screen and paper. The fold says the Lab runs "the same package on a replay port" (`H3` T38). The Lab's AD-11 then compiles a pod to Book and BMS fragments, with blocks the node can't run named as `unsupported_blocks`, running in the Lab only. So on paper a size shown in the Lab can differ from a size live, which is what AD-10 set out to prevent ("five screens computing five different sizes").

**The shape that removes it** [proposal].

1. **One core, in a library both sides import.** The three functions from (b). The node can't import the Lab (`LP` AD-11), so it can't be `qmx_lab`. The simulator becomes a driver. QML is the obvious home, and `SWAP` 2.2 warns QML sits in the node's lock, so the core stays small and blocks stay in the Library.
2. **Pure and stateful are both true.** AD-10 says a block is pure; guard rows keep `block_state` (`H3` T38). Reconcile: state goes in and comes back. "Same inputs, same answer" still holds, with state as an input.
3. **Four drivers, one core.** Node live (real facts), QMB (bars, with fills), paper (`paper.step`), Lab replay (recorded intents).
4. **Size trail equals the decision row.** The Lab's bars (`LP\UI-TO-BACKEND-MAP.md:91`) and the node's receipt are one record: sizer, each throttle, caps, venue fit (`H3` T61). Fan, stress board and head to head are many calls above the same core.
5. **Merge order is declared.** Replaying 200 units needs one rule for ties, by time then rank. The live node's arrival order needs the same rule. UNKNOWN whether the node processes units one at a time; check at the spine.
6. **`unsupported_blocks` becomes the needs list.** A block says what it reads; a place says what it provides (`H3` T18). "Ready for live?" shows a named row per unmet need, with a fallback or a refusal. A block is no longer "Lab-only" by nature, only unmet at this place. A model that this node can't run is a needs row (Pod 16).
7. **A conformance tape.** One recorded set of intents and facts through every driver, identical trail required, in CI (`candidate-3`, `candidate-2`, `H3` section 2). This is what proves it, and a mechanism test is all a simulation may do here.

**What may legitimately differ, stated.** Fills, costs and latency, because facts differ. Never the arithmetic. If facts match, trails match.

**Three things this forces.**
- **Workflows at trade time.** Portfolio offers sizing methods including "Workflow" (`LP\UI-TO-BACKEND-MAP.md:122`), and `news-kill` is a "graph" block (`DEMO:183`). An engine workflow is a finite run (`LP` AD-12), so it can't answer an order. A graph block must compile to a block, or its result must arrive as a published fact. The chip stays; its meaning narrows.
- **Replay honesty.** `LP` AD-8 says a change of size "needs a rerun", and a resize replay is a labelled projection. `H2` I1 wants resize replay as the everyday tool. Both can hold: replay for exploring, a QMB rerun for evidence. Replay can't see what larger fills do (`H2` I1). Hand-off to the methodology session.
- **Compile target.** AD-11's CT-22 and CT-27 target predates units (`H3` section 4, row 4). OPEN-1 said "when the risk session settles the unit, only the adapter changes". That day is now. The port stays; the target becomes the pod document plus `qmx.unit/1`.

---

## (g) What the unit baseline must carry

Only what pods and mini apps add to `H2` section 4 and `H3` section 5, which stand. The test: if left out, does the core get reworked later?

| # | Must carry | Kind | Why (pod or case that needs it) | Rework if left out |
|---|---|---|---|---|
| 1 | Pod reference on the deployment, optional. Empty pod is the default | Input | All origins; Way 5 or thin group | New field on every unit and journal |
| 2 | Deployment key includes the pod and live or paper side. Today a second deployment of a unit version is refused (`G9:126`, `promote.py:422-447`) | Input | "every pod should have a live mode and a paper mode" (`BACKLOG:397`), head to head, canary of a pod | Deployment identity migration |
| 3 | **Two fingerprints:** logic and pod. Today one compiled fingerprint gates the node (`SWAP` 2.3) | Record | Pods 9, 12. One pod edit must not re-prove 200 units | **The largest rework risk here** |
| 4 | Would-have rows under any pod | Record | A guard filters which trades happen, so "logic in R" (`H3` T48) needs them. Sizing alone leaves R alone; guards don't (round table) | The logic record quietly depends on the pod |
| 5 | Slot composition rules, as data: sizer picks one; throttles multiply or a declared combiner; caps lowest; guards worst state; inputs union. `CombinerKind` already exists for logic (`unit\model.py:112-118`) | Socket | Pods 1, 5 | Each mix is code |
| 6 | Placement on each block row: unit, group, off-path, or where its needs are met | Socket | Way 5; `H3` T6 | A later move rewrites rows |
| 7 | Sizer socket as dollars rule plus converter | Socket | All pods; "why lots?" (`H3` T4) | Socket changes per idea |
| 8 | Throttles run: `sizing_modifier` stops refusing (22 blocks claim the role, `H3` overhauls) | Socket | Pods 1, 4, 5, 6, 18 | No pod works |
| 9 | Halts bind (`SWAP 5`), with verbs beyond stop, including reduce (`H2` section 4) | Socket | Most pods | Pods can only stop |
| 10 | Group stage: real host call on node **and** in QMB, passing intent and open risk across members (`SWAP 6`) | Hook | Pods 8, 12, 13, 14 | Pods stay paper |
| 11 | Scope keys including `pod:`, `tag:`, `class:`, `driver:` | Input | Pods 12, 15 and "isolate crypto" | Vocabulary rewrite |
| 12 | One ledger fold keyed by scope; anchor type, clock and scope as rows (`H2` I4) | Record | Pods 3, 4, 5, 9, 10, 11 | Each pair has its own ledger |
| 13 | `on_fire` action field; only his hand lowers a kill level | Socket | His Q5 | Questions return to him |
| 14 | `required` and "kill line set" as preset warnings; compile doesn't demand a kill line | Rule | Pod 20 | Reckless can't be painted |
| 15 | Exits stay on the unit; exit stack with all verbs; unit template holds exits, pod ref and presets | Socket | Pod 6 | "Scalping based system" has no home |
| 16 | No dependence on a QMB card, or on a mini app being up | Rule | Four origins (`H3` T7), stopped desk | Lab and app units misread |
| 17 | Published-reading path with age and fallback, even if one reader at first | Hook | Roads D, Pods 2, 7, 15, 17 | Node feed rewrite |
| 18 | Core landers, block save, real pod and template kinds | Runtime | (e) rows 1 to 5 | "Ship pods" stays a sentence |
| 19 | Pin plus diff plus lineage on each unit and pod | Record | 200 units; upgrades (`H3` T9, T52) | Can't be retrofitted cheaply |
| 20 | Pod-scope read rows and proposal rows | Hook | Pod 17. Agents watch a dozen pods instead of 200 units | Monitoring stays per unit |

**Content, not baseline:** all 20 pods above, every `n:` block, gallery order, each allocator, each shape of cushion rule, the file extension, desks themselves.

**Belongs to another session:** readiness and proof (methodology), agent jobs and who may self-apply (agents), Portfolio and Home screens (UI), values (numbers talk), MIS internals (`E1`).

---

## Round table, as it happened

Four voices, inline, headless. Nobody could be asked anything, so they argued it out and left the fights standing. Renata runs risk at a multi-manager fund. Tariq scalps gold from his flat. Ines builds platforms. Marek shipped node-editor products.

**Renata:** A pod that sits inside a unit isn't a pod. It's a settings file. A pod is where capital gets cut. Who cuts it, if every unit has its own copy?

**Tariq:** And I don't want a committee between me and my entry. My size is decided before I hit the button. Your risk desk can read about it after.

**Ines:** It's the same process on the same node, Tariq. Reading shared state costs nothing next to a venue round trip. UNKNOWN until measured, but it won't be your problem.

**Tariq:** Two nodes, though?

**Ines:** Then no, not atomic. Which is fine. A pod lives on one place. Two places means two pods and a share between them.

**Marek:** You're all arguing about plumbing. A newcomer opens a gallery, clicks "Scalper", gets a working thing. If they ever see the word "stage", we lost.

**Renata:** And when they've got 200?

**Marek:** Then they edit one pod and 200 follow. Which is why Way 1 is dead.

**Ines:** Dead for a different reason. Node refuses a changed compiled fingerprint. Edit the recipe, every unit needs a new record. I can show you the line.

**Renata:** Good. It *should* need one. You changed the risk.

**Ines:** Changed the size. R stays the same. Logic record survives a size change.

**Renata:** Size, yes. Put a guard in that skips thin hours and now a different set of trades happens. Your precious logic record is a record of logic-under-that-guard.

*(Ines stops typing.)*

**Ines:** Fair. So the logic record only survives if we keep what the unit would have done. Would-have rows.

**Tariq:** Which nobody writes.

**Ines:** Kind declared, no writer. Yes. It goes on the list. *(This is row 4 of (g), and it came from here.)*

**Tariq:** Now the real one. Your seven slots have no exit. Fast invalidation is my risk management. Cut losers early, that's why I can size up. If a "risk and sizing pod" can't hold my exit, it isn't my pod.

**Renata:** An exit changes what R means. Swap exits in a stack and you can't compare anything. Exits stay with the strategy.

**Tariq:** Then your pod's a calculator.

**Marek:** Neither of you. He said "scalping based system". Give that a home: a template with exits, a pod reference, presets. A person starts from the template and gets all of it.

**Tariq:** And when my stage changes and I want tighter cuts?

**Marek:** New version of the unit.

**Tariq:** That's my complaint.

*(Left open: can a pod swap exit rows at an anchor? (g) row 15 says no. Tariq doesn't accept it.)*

**Renata:** The demo marks the kill line required. Good.

**Marek:** It says paint anything. His brief says a reckless setup must be expressible.

**Renata:** He said kill switch only comes down by his hand. He didn't say a pod with no floor is a good idea.

**Tariq:** He didn't ask if it's a good idea.

**Renata:** Then it says so in the largest type the screen has.

**Marek:** Yes. A warning and a grade. Not a wall.

*(Renata lets it pass, unhappily. Row 14.)*

**Ines:** "Pods are meant to be mini apps." I need to say this plainly. Only one app can hold trading keys, and it's the node. A mini app in the order path is impossible by construction.

**Renata:** Real pods aren't software. They've got analysts, a PM, capital and limits from the risk desk. He's describing the analysts in one breath and the limits in the next.

**Marek:** So the mini app is the team and the delivery van. The pod is what it delivers.

**Tariq:** Stop the team and my unit keeps trading?

**Ines:** Yes. Same rule as the MIS board.

**Renata:** Allocation can sit with the team. No one allocates per order anyway.

**Tariq:** At my size I'd rebalance by session.

**Renata:** Still an anchor. Still off the order path. *(This became the clock table in (c).)*

**Marek:** Who watches 200 units?

**Renata:** Nobody. You watch twelve pods. That's what a pod is *for*.

**Tariq:** And agents cutting me down every time I have a bad hour? I've seen that ratchet. You end up a sitting duck.

**Renata:** Cuts need a way back. A restore rule on the row.

**Ines:** He also has a fixed line: agents never touch money. A cut that applies itself. Is that touching?

*(Nobody settles it. Default is a card. Flagged under Pod 17.)*

**What the collision produced that no single voice brought:**
- Guards change a unit's record, so would-have rows are a baseline item, not an extra.
- The allocator isn't a trade-time slot at all.
- Empty slot means "unit's own block", so "no pod" needs no special case.
- A pod lives on one place; spanning is a mix.
- Team and pod are separable, which is the join between his two senses.

**Left open on purpose:** pod swapping exits at an anchor; a kill line as warning or wall (Renata's dissent); whether an automatic cut crosses "agents never touch money"; how much contract Way 5 is worth against a thin group document.

---

## UNKNOWN list

1. How the running UI looks. Notes only.
2. Whether a shared group stage adds real delay on a node at scalper rates. Not measured.
3. Whether the node handles units one at a time, which decides merge order (f.5).
4. How a Library-only block reaches a live node (e, row 13).
5. Whether a graph block can compile to a form the node accepts. No path exists today.
6. Speed of a Decimal-based core over a fan of resampled paths.
7. Whether Windows' `os.replace` problem (`CHECK`) affects a general feed relay. The current relay uses whole-file replace.
8. Whether Way 5's two-stage equality holds with raises. The property test covers cuts only (`H3` T6).
9. Pod definitions in `X0`, `X2`, `X3`, `X4`, `X5`, `X7`: I read `X1`'s pod hybrids, and `H2` and `H3`'s harvest of the rest, not each file. Other agents in this round cover some.
10. Everything in the catalogue is unrun, and nothing here says any pod performs.
