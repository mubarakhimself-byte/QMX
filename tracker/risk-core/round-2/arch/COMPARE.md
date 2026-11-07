# Comparing the four architecture versions

Independent judge, 7 Nov 2026. I read all four versions in full (SPINE, WALKS, RATIONALE), `round-2/funnel/FUNNEL.md` sections 3, 4, 6 and Appendix E, `QUESTIONS.md`, and your messages M49 to M56 word for word. I checked 24 code claims at `D:\QMX-worktrees\bld-repair-24` (tip `351e7521`); the table is at the end. Two small mechanism checks ran under `D:\Temp\judge`. No test suite ran. Nobody else judged, so there is no second opinion here.

**The short answer.** Start from version 1 and take about a dozen named parts from the others. Version 1 against version 4 is close, because they are one family. Version 1 against version 2 is a real choice about what a pod is, and it is yours if you want it. Version 3 is not close as a base.

## Words used

| Word | Meaning |
|---|---|
| Unit | One trading algorithm, as one document plus its blocks |
| Block | One small QML piece: a sizer, an exit, a brake |
| Pod | On your screens: blocks plus money plus members. Each version redraws it |
| Group | A shared object above units that holds caps and money |
| Node | The live program that holds the broker connection. Today it runs every unit on one thread (`runtime.py:2157`) |
| Fingerprint | A hash of the compiled unit. The node only runs a unit whose fingerprint has a test record |
| G record | That test record, from QMB's layer G |
| Venue stop | A stop held at the broker, which survives if the node dies |
| Bell | One bar close where many units want to enter at once |
| Sticker | An expiring notice on a market or scope that holds entries back; a unit can list kinds it ignores |
| Fold | One function that reads the journals and gives the risk state at any level |
| R | The loss if the planned stop is hit |

**How to read the references.** `AD-3` is decision 3 in that version's `SPINE.md`. `W8` is walk 8 in its `WALKS.md`. `RAT` is its `RATIONALE.md`. `Q6` is a row in `funnel/QUESTIONS.md`. `M49` is your message. `S14`, `I6` are rows in the funnel's core list. `E5` and `E2` are files in `round-2/expand/`. Bare code names: `runtime.py` is `qmn/src/qmn/app/runtime.py`, `unit.py` is `qml/src/qml/protocol/unit.py`, `compiler.py` is `qml/src/qml/compile/compiler.py`.

PR counts are each author's estimate. Nobody measured them.

---

## 1. Each version in five lines

### Version 1: the unit owns it (`V1-unit-owns`)
- **The idea:** a unit carries every rule it obeys in its own document. A pod is a recipe stamped into each member before it runs. Above the units sits one thin group that holds shared caps and a ledger and can only cut.
- **What you would see:** a pod card that looks like one thing, with two things behind it: a recipe for the method, a group for the money. One pod edit shows a plan of all members, and you click once.
- **What a builder does:** mostly lifts refusals the compiler already names. Splits the document into a logic part and a risk part with a hash each, so a size edit keeps the logic's test record.
- **PR count:** about 37.
- **Cost in one line:** a pod edit is bulk work behind the click: 200 new versions and about 2.5 minutes of compile, twice.

### Version 2: one pod document, split by scope (`V2-pod-by-scope`)
- **The idea:** a pod is one live document of blocks. Each block says where it runs: in the unit, in a group stage on the node, or off to the side at set times. An empty slot means the unit's own block.
- **What you would see:** the closest match to the proposal screens: one pod, one method, one size trail walking every block. One edit, one document, one click.
- **What a builder does:** builds one chain, a group stage, two passes per bar, a time budget around block code, and one small field (`runs_at`) that places every block.
- **PR count:** 51, and it says it could reach 58.
- **Cost in one line:** the most contract. Its own words: it can be kept from being too much machine, and "it can't be made small".

### Version 3: a live pod above the units (`V3-group-above`)
- **The idea:** units say what and when. The pod says how much and whether. One evaluator per pod, in its own process with no keys, answers for every member. It is drawn like a fund's risk desk.
- **What you would see:** pods first, units on drill-down. A unit alone gets a "pod of one" generated for it, without you seeing the word.
- **What a builder does:** takes the sizer and brakes out of the unit document, builds the evaluator, a worker process, and a pipe to it.
- **PR count:** about 50.
- **Cost in one line:** a unit cannot open a trade by itself (its own section 2), and one bug in a pod's evaluator stops entries for every member.

### Version 4: the flat unit (`V4-premise`)
- **The idea:** drop the second object altogether. Risk is more QML inside the unit. Shared numbers are facts the host computes. Rules reach each other only by stickers. Nothing else runs.
- **What you would see:** "pod" stays as a screen word for a group plus the preset its members were painted with. A group limit edit reaches 200 units at their next decision, with no recompile. A structural edit is a plan with a batch re-test and one click.
- **What a builder does:** the shortest list of nouns (seven). One fingerprint. Retires the Lab's seven-slot pod design.
- **PR count:** 32 (its band is 30 to 38). I think this is low: see section 2, last row.
- **Cost in one line:** it leaves out the fix for entries delaying other units' exits, and it refuses a truly stopless live unit.

---

## 2. Side by side

Each cell gives my reading, then its evidence in brackets.

| What you asked for | V1 unit owns | V2 pod by scope | V3 live pod | V4 flat unit |
|---|---|---|---|---|
| **Canvas freedom:** can someone express something unusual or reckless? | **Strong.** Warns, never refuses, outside the fixed lines. Stopless is expressible, warned. Weak spot: "take the best of those firing this bar" can't be said (AD-20, W2, W8) | **Strong.** Same rule. A group can only cut, so a press goes in the unit stage; a reckless pod still can (AD-5, AD-21) | **Mixed.** Reckless pods run. But a unit can't place with no evaluator, an account-wide user brake can't be atomic, and a new fast sensor needs a signed package (section 2, AD-8, AD-16) | **Strong, one hole.** Anything can be painted, and a unit may drop its group cap. But it keeps the node's venue-stop rule, so a truly stopless live unit is out (W2). That rule is not one of your fixed lines |
| **A newcomer out of the box** | **Strong.** One complete document; never meets a pod. Installer is the release lane's in every version (W1, `E5` G1 to G3) | **Good.** House pod and empty pod stay hidden, but the walk can't pass until slice 10 (W1) | **Good.** Pod of one hides it; a newcomer who opens Portfolio finds a pod they didn't make (W1) | **Strong.** One document, and it ships instrument records. Whether those stand in for a broker's is unverified (W1, `E5` G8) |
| **A unit from anywhere** (Lab, workflow, mini app, copilot) | **Strong.** All land the same document. A mini-app sizer stays, with `risk_locks` (W6) | **Strong.** Empty pod means no special case. Lab replay only matches live late, at slice 14 (W6) | **Mixed.** Cleanest for the Lab. A mini app's own sizer has to become an "ask", and one that insists on placing alone is not expressible (AD-14, W6) | **Strong.** One path, no pod reference to resolve (W6) |
| **Pods and mini apps** | **Works, less direct.** Stamped recipe plus group; "12 of 14 follow the recipe" can happen. Agents can compare recipes, but no live pod exists to point at (AD-4, RAT) | **Closest to your screens.** Methods side by side, one document, a pod of pods by `parent` (AD-1, section 4.1) | **Strong for a shared pod.** Pod-pool cushion and same-bet caps are natural; heavy for a lone unit (W3, W12) | **Weakest on the word.** A pod is a group plus a preset; a member can drift from its preset and only a report catches it (RAT, W8) |
| **200 units** | **Works, strains.** QML step about 55 to 60 ms (their probe, I reran it). Compile about 2.3 to 2.5 minutes per 200 on one worker. Sends in series (W8) | **Works, best answer on the bell.** Exits first, time budget, leftovers carry over. Serial sends remain (AD-7, W8) | **Mixed.** Evaluation scales across processes (pipe 2 ms per 200, stand-in chain). Unit stepping stays on one thread and it says that is the likeliest surprise (W8) | **Works for values, weak at the bell.** Group edit is cheap. A structural edit is 200 G runs, about 17 minutes on one core for the dummy on 2,000 bars (my check). No fix for entries delaying exits (section 5) |
| **Agents carrying load** | **Good.** Scripted fleet read, drafts and plans only; decay card off (section 6) | **Good.** Same, plus plain-row meters; learners give agents a clean place to publish a target (AD-13) | **Best for reading.** About a dozen pod rows, then drill down (W8) | **Good, one mismatch.** Lets an agent's de-risk sticker apply by itself and calls that Q4's default (AD-4). Q4's default is a card |
| **Self-configuration** | **Good, least new.** Replay finds, facts track, the built engine corrects, each with an off switch. Size herding untested (AD-14, W8) | **More parts.** Learner and applier; its own rationale says to drop this first if anything goes (AD-13, RAT) | **Slower.** Pod numbers move at anchors only; raises wait. One decision, easy to read. A recovering day can't re-press until the anchor (AD-10, W12) | **Good, least new.** Same engine, plus `state_table` numbers keyed on a fact (AD-8) |
| **Backtest equal to live** | **Arithmetic same.** Group caps need a multi-unit run, at slice 13 (W13) | **Arithmetic same.** Largest gap is the group; the merge lane arrives last, slice 14 (W13) | **Arithmetic same, soonest group run**, slice 9. A unit's money result means nothing apart from its pod, so methodology gets two proof objects (W13) | **Arithmetic same.** Group and account rules can't be proved in QMB; multi-unit replay is deferred (W13, section 11) |
| **Failure safety for exits** | **Good.** Frontier outbox: exits first. Wrapped chains. One hung block stops all 200 until the process restarts (AD-17, W11) | **Strongest.** Exit code can't reach the chain, by an import test. Hung link answered in 57 ms in a toy. Costs: abandoned threads leak; a hung logic block closes that unit's positions (AD-7 to AD-9, W11) | **Strong.** Exits run with the worker hung or dead. Pod-level flatten is only as live as its worker. Every entry in the pod stops on one fault (AD-5, W11) | **Weakest.** Its exits skip the gates, but no pass separates them from other units' entries. Its "hung stage" answer is "there is no stage" (W11); the whole node restarts, and cuts and time exits don't run in that gap |
| **Maintainability and adding a part** | **Good.** New brake is one folder and one row. Two chains to keep joined. Bulk versions in the Library (section 7) | **Good once built.** About 21 public types, one reader of `runs_at`, `EXTENDING.md` generated (section 13) | **Good inside, a process seam outside.** After format 5, new brakes never bump the compiler. Three fact providers (AD-12, section 8) | **Best on paper.** Seven nouns, one fingerprint. Halts run twice (at mint and at place), which is one thing to keep equal (AD-5) |
| **Reuse of what's built** | **High.** Seats exist (`model.py:470-492`); most PRs lift a refusal | **Medium.** Same seats, plus a new `risk` map, and sizing moves out of `_Run.enter` | **Lowest for the unit.** Removes `/sizer`, keeps `/halts` refused. The block API stays (AD-1, section 6) | **Highest.** Roles, halts, stand-down table, `template` kind. Retires small shells |
| **"Too much machine"** | **Moderate.** Slices 1 to 11 are a whole single-unit baseline with no group or pod. The rest is opt-in (RAT) | **Most.** About nine PRs a lone unit never feels (section 13) | **Heavy.** Worker, relay, reservations, mandatory pod. Its own words call the charge fair (RAT) | **Least to learn.** The machine moves to bulk versions, re-tests and old versions draining beside new ones |
| **PRs, and earliest paper trade** | 37. First filled paper entry after about PR 11 (canary), all three templates at about PR 23 | 51 to 58. First filled entry at slice 10, which is PR 38 by its table | About 50. First filled entry at slice 3, PR 10, on today's narrow exits; all templates pass at slice 14, about PR 46 | 32 by its count. Rehearsal at slice 4, about PR 24. It packs eight roles or all of motion into one PR each, where V1 spends more. With the missing fixes added I expect about 36 to 42 |

---

## 3. The 13 walks

**Holds:** works. **Strains:** works at a stated cost. **Fails:** can't do it. A star (\*) marks where my verdict is harsher than the author's.

| # | Walk | V1 | V2 | V3 | V4 |
|---|---|---|---|---|---|
| 1 | Newcomer to paper | Holds | Strains: passes late | Holds; a pod they didn't make | Holds, if shipped records work |
| 2 | Gold scalper, fast cut, no stop | Strains | Strains; seconds-fast fails | Strains in four places | **Fails\*** for truly stopless: it keeps the rule |
| 3 | ORB across opens, one bet | Holds; first in rank takes the room | Strains; same | **Holds best**, within a pod | Strains; cross-unit count is live only |
| 4 | Futures week to units with own sizing | **Holds best** | Strains; gaps are mostly elsewhere | Strains\*: "own sizing" means an ask or a pod of its own | Holds |
| 5 | Very aggressive setup, then a stage change | Holds; undeclared stage is an edit | Strains | **Holds best** | Holds for numbers; a block change is a plan |
| 6 | Lab, workflow, mini app | Holds | Strains on Lab | Strains on own-sizer; insisting on placing alone fails | Holds; lander missing, as in all |
| 7 | App feeds app; desk publishes a reading | Holds; new reading for 200 is a plan | Strains: relay work | Holds; copilot must choose reader | Holds; capability to read another app unknown |
| 8 | 200: edit, watch, herding, limits | Strains: serial sends, first-come caps | Strains least at the bell | Strains: stepping still on one thread | **Strains hard\***: entries delay exits, and it doesn't say so |
| 9 | Swap a placeholder with a record and an open trade | Sizer holds, in place; exit strains | Same | **Sizer trivial**; exit strains | Strains\*: every sizer swap is a new deployment that restarts cold beside the old one |
| 10 | New brake, class, sizing base | Holds | Holds | Holds; atomic account brake **fails** the one-folder promise | Holds |
| 11 | MIS down, chain fault, hang, restart | Holds except hang: strains hard | **Holds best**; leaks threads | Holds; fault stops all pod entries | **Strains hard\*** on hang |
| 12 | House money and press, per pod | Holds; flip is a plan | Holds; one row | Holds; re-press waits for anchor | **Holds best**: one live fact flips it |
| 13 | Backtest against live | Strains on group caps, wicks | Strains: largest gap, late fix | Strains: peers; two proof objects | Strains most: deferred |

**What every version shares.** A "fast" cut acts at most once per closed bar, because units step on closed bars (`compiler.py:976-981`). V1, V2 and V3 say so. V4 doesn't mention it. The futures walk needs a route, `roll`, a methodology and a copilot that can take video, in all four. No version got past "UNKNOWN" on real send times; those wait for the demo probes.

---

## 4. My recommendation

**Base: version 1.** Reasons, in order:

1. **It is what you asked for, most literally.** "Just make sure that the unit can actually trade, it can self-configure, it has a template" (M49). The brief adds "can size itself". In V1 the document says all of it, with nothing else required.
2. **It extends most easily without breaking the lines.** Slices 1 to 11 are a complete single-unit system. Group and pods come after, and a unit that ignores them loses nothing. If "too much machine" turns out true, you can stop there and still have a working baseline. No other version has that stopping point so early.
3. **Its weak spots can be fixed by grafts.** V2's and V4's weak spots sit in their shapes.

### What to take into it

| # | Take | From | Why |
|---|---|---|---|
| 1 | A time budget on the entries pass; leftovers carry to the next tick and re-check caps | V2 AD-7 | V1's outbox puts exits first, but a long bell can still trip the 30-second watchdog |
| 2 | One wrapper with a time limit around block code; a fault never returns a refusal to the frontier | V2 AD-9 | V1's weakest walk. A refused frontier ends that unit's exits today. Chain links first; unit step once tested on Windows |
| 3 | An import test: exit code can't reach the chain | V2 AD-8 | Turns a promise into a test, at almost no cost |
| 4 | One decision row, written before the send, with every input stored so it replays alone | V2 AD-6 | V1 joins two chains on one id; this fixes when and what |
| 5 | Reservations: room is held from send to outcome, and an unknown outcome keeps it | V2 AD-11, V3 AD-9 | V1 names no in-flight count, so a shared cap can overrun |
| 6 | Group limits as live facts: one edit reaches every member at the next decision | V4 AD-10, 3.8 | Cuts V1's biggest cost for the most common edit |
| 7 | The three tiers as the builders' rule: a fact changes live, a number moves in its range, structure is a version | V4 AD-2 | One sentence that stops builders disagreeing |
| 8 | Group membership by tag as well as by name | V4 3.8 | At 200 units, joining a group shouldn't touch each member |
| 9 | Brake states read from the fold, with the snapshot only a cache | V4 3.4, V2 AD-16 | Restart and pod edits then need no state copied. Today's snapshot writes only when a calibrated number moves |
| 10 | A drift report: members whose risk part differs from their recipe | V4 W8 | V1 doesn't address hand edits made after stamping |
| 11 | Record each unit's proposals as a tape, so size searches replay cheaply; exploring only | V3 RAT, W4 | Fits your "hill climb"; V3 states the limit honestly |
| 12 | Restart rules: an anchor's id comes from clock and time alone; cuts stand, earned raises wait one anchor | V3 AD-11 | Stops a restart acting as a hidden accelerator |
| 13 | Let the group's `order` be a block, field now, content later | V3 phase 2, V2 chain | The outbox already holds every entry of a bar, so "best of those firing" becomes sayable. That removes V1's own stated reason to abandon |

**My estimate with these:** about 40 to 44 PRs, first filled paper entry around PR 12 or 13. Unmeasured.

**Rejected.** V2's learner and applier: more parts, and its author ranks it first to go. V2's `runs_at` and V3's mandatory pod: they don't fit this base. V3's worker process: kept as the named next step if hung blocks prove real. V4's retest-everything rule: keep it as an option on a plan, since it costs machine time and no attention. V4's keep-the-venue-stop rule: against the brief.

### What you lose by not picking each

- **V2:** one pod as one live document. In V1 a pod edit writes up to 200 versions where V2 writes one. Comparing two whole setups is plainer in V2, and a pod on screen matches one thing on disk. This is the real loss.
- **V3:** the fund picture: one place sets size for everyone, one rank table, block code away from the keys, a compiler that almost never bumps, pod-pool cushions with no extra work. You can move toward this later only with a large rework.
- **V4:** the smallest vocabulary, no split in the document, and a re-test on every structural change. You keep most of its best idea through graft 6.

### How close

- **V1 over V4: close.** V4's own rationale says it is V1's family (fork F1 shape A). V1 wins because V4 has no answer for exits at the bell, and its risk edits restart units cold. Fix those and the PR gap mostly closes.
- **V1 over V2: a real choice.** V2 is the better system at 200 units with shared pods. V1 is the better baseline, about a quarter shorter, trading much sooner. **If you picture the pod as a live thing that governs its members, choose V2 and keep V1's slices as its order.**
- **V3: not close as a base.** Its grafts are good.

### What would change my mind

| If this turned out true | Then |
|---|---|
| You want a pod to govern, with members unable to step out | V2 |
| Pod edits become daily across hundreds of units | V2 |
| A pod must decide jointly per order, beyond ordering them | V2, or V3 |
| You rule that every pod edit needs a full test per member (Q6) | V4: the fingerprint split stops paying for itself |
| Moving risk in place (V1 AD-6) proves hard in slice 14 | V4's drain path, which is mostly built |
| Demo probes show sends so slow they hurt fills, even with the outbox | Sends off the thread, or V3's separate processes |
| Hung blocks happen in practice | V3's worker process |

---

## 5. What any final design must take, whatever its shape

**All four already agree on these,** so I treat them as settled: a sizer answers a typed amount and one converter spells the venue's quantity ("why lots?" gets its answer here). Exits run on their own path with a rank. One fold. One `explain_size`. One handler across hosts. Every number has a derivation, range and reason. Readings carry publisher, age and fallback. Agents write drafts only.

**Found by one version or by this check, and owed by all:**

| # | Finding | Evidence | Who has it |
|---|---|---|---|
| 1 | **Entries delay other units' exits today.** Each unit places its entries as it mints them, and units run one at a time. One entry can hold the thread for the venue's answer (up to 5 s) plus up to 3 tries of 2 s waiting for the stop | `runtime.py:1727-1733`, `:3013-3016`, `:179-182`, `:1182-1190`; `ctrader_account.py:110,679` | V1, V2, V3. **V4 lacks it.** V4 listed the order as UNKNOWN; I read it: mint, then place, per unit |
| 2 | **A long bell can kill the node.** The 30 s watchdog times the whole pass and exits the process | `healing.py:64`, `:403-420`; `runtime.py:2192` | Only V2 budgets for it |
| 3 | **A refused frontier stops that unit's exits.** The phase goes to STOPPED and the driver skips STOPPED units. The venue stop stays | `runtime.py:3014-3015`, `:3040-3046` | V2 by name; V1 and V3 by wrappers; all must prove it |
| 4 | **A new fingerprint over a held trade silences its per-bar exits.** I reran it: 0 exit intents in 60 bars against 1 in the control. **It's narrower than "orphans exits":** the venue stop holds and the node still closes targets. After a restart under the same deployment, adoption re-stamps the trade. The built withdraw path keeps an old version running exits till flat | `unit.py:672-679`; `compiler.py:1072-1079`; `runtime.py:1637-1652`, `:2640-2641`, `:2746-2748`; `D:\Temp\judge\v1-probe-rerun.txt` | Rule for all: never host a different fingerprint over a held trade without a logic-only stamp (V1, V2) or a drain (V3 exit swaps, V4) |
| 5 | **A new version starts cold.** A snapshot from another fingerprint is refused, so a design with one fingerprint re-warms logic on each risk edit. V4 names a carry in one table row and gives no contract | `unit.py:990-991`; V4 AD-12, PH 22 | V1 and V2 avoid it by the split; V3 by construction; V4 owes it |
| 6 | **Stopless needs more places than the versions list.** They name compile, `enter`, handler, node entry, gate. Also: after the send the node waits to see the stop, and if it never shows, it closes the trade and raises the alarm. Without a branch, a stopless entry gets closed at once. The gate also sits on other order paths; whether a unit's route reaches them is UNKNOWN | `runtime.py:1182-1190`; `qmn/order/path.py:561`, `venue/live.py:1012` | Nobody. **New.** Add it to every version's no-stop row |
| 7 | **A parked entry reads as "warming up".** Only a known-unknown outcome makes the next bar wait. An entry not yet placed gets a Skip row and is marked done. V2 assumes it waits. One small change, needed by any version that parks entries past a bar | `runtime.py:1703-1713` | **New.** Corrects V2 section 4.4 |
| 8 | **Block-running code can't live in `qmf-risk`.** That package depends only on `qmf-core`, and `qml` depends on it. V3 saw this. V1's map puts the chain and group there | `packages/qmf-risk/pyproject.toml:7-9`; `qml/pyproject.toml:8-12`; V3 AD-3 | Fix V1's module map: types may stay, the runner goes in `qml` |
| 9 | **Brake state won't survive a restart by accident.** Today's snapshot writes only when a calibrated number moves | `runtime.py` `_saved_snapshot`, about `:2920-2927` | V1 names it; grafts fix it |
| 10 | **Exits are serial too.** Exits first doesn't help when 200 positions close one venue call at a time, and a slow account delays the next one | V2 W8; `runtime.py:3013` | Keep the meter; reopen if measured |
| 11 | **A logic record under a changed risk part isn't the same trades.** A new gate skips an entry, and the unit's next trades differ. V1, V2 and V3 all keep the logic record across a pod edit | V3 W13 says this of tapes; V1 assumption on Q6 | Hand to the methodology session, with would-have rows as the evidence |
| 12 | **Fast cuts wait on the bar.** Shape the exit answer so a quote clock can feed it later with no rework | `compiler.py:976-981`; V2 section 14 | All defer. Test 2 of the brief says leave room |

---

## 6. What is truly open, and whose call

Everything else is configuration, or belongs to a named session. Every row below has a default, and nothing waits.

| # | Question | Kind | Whose | Default the work runs on |
|---|---|---|---|---|
| 1 | **What a pod is.** A recipe stamped into units plus a group (V1), or one live document that governs (V2). You said you'd go through every overhaul (M56). This is the biggest one | Your words, scope | You | V1 with the grafts |
| 2 | **One click per pod edit** (Q6), and **does that click also cover a stage move up, later, by rule?** V1, V2 and V3 assume yes; V4 treats it as a number moving by its own rule; V1 ships going-up stages as a card by default | Your click, fixed line | You | One click per edit; moving up lands a card |
| 3 | **An agent's de-risk reading** (Q4): does a cut inside declared bounds cross your line? V4 assumes it doesn't; the others land a card | Fixed line | You | A card |
| 4 | **Demo sign-in, and may the probes run on your demo account** (Q1). Send time, whether a fill carries the stop, and how an amend behaves all wait here. They settle findings 1, 2 and 10, plus trailing stops and partials | Your account | You | Fake broker; those parts land after |
| 5 | **Data you'd own or pay for** (Q2): volume on bars, order flow, a futures route. Your futures week needs the route | Money, scope | You | FX and gold through cTrader, tick count from quotes |
| 6 | **Landing branch** (Q5) | Your click | You | On `engine/base` after repair's stack |
| 7 | **The word "desk"** (Q3) | Your words | You | "desk" in code, "department" on screen |

---

## Code claims checked

| # | Claim | Whose | Result |
|---|---|---|---|
| 1 | A risk-only edit moves today's fingerprint | V1 | True: the document is hashed in (`compiler.py:1072-1079`); rerun gave True |
| 2 | Per-bar exits stop after that recompile | V1 | True at the unit level, 0 against 1. Narrower in practice: finding 4 |
| 3 | Entries wait on the runtime thread, and units run in series | V2 | True (finding 1) |
| 4 | 30 s watchdog exits the process | V2 | True (`healing.py:64`, `StuckWatch.check`) |
| 5 | Refused frontier sets STOPPED, and exits end | V2 | True (finding 3) |
| 6 | The venue-stop gate is on the unit's entry path, and the entry path needs a stop | V4, all | True (`runtime.py:1065`, `:1074-1076`, `:1102-1106`). It's node code, no fixed line. V4 could change it with one row |
| 7 | `none_declared` already exists on the wire | V1, V2 | True (`unit_intent.py:69-73,131`), though it "leaves R undefined" |
| 8 | Node mints then places per unit | V3 true; V4 UNKNOWN | True (`runtime.py:1727-1733`) |
| 9 | `client.send` holds a lock, with a 5 s answer wait | V1 | True (`ctrader_account.py:110,679`) |
| 10 | A parked entry waits on the next bar | V2 | **Partly false** (finding 7) |
| 11 | 0.5 s slice latency "limit" | V3 | Partly: it is set (`runtime.py:189`) and reported as `latency_breached` (`qmn/loop/driver.py:136`). I saw nothing that stops on it, and did not read the whole driver |
| 12 | The document's seats, role list and refusals exist | V1, V4 | True (`model.py:89-109,470-492`; `compiler.py:896-912`) |
| 13 | `state_table` enum exists | V4 | True (`model.py:189-196`) |
| 14 | Pod kinds are shells; `template` is retired | V4 | True, 772 and 997 bytes (V4 says about 700); `retired: true` |
| 15 | A second live deployment is refused | V3, V4 | Partly: only the same unit and version (`promote.py:424-447`). A new version isn't caught there |
| 16 | Old version can run exit-only till flat | V4 proposes it as new | Mostly built: `withdrawn` blocks entries, and the unit stops when flat (`runtime.py:2640-2641,2746-2748`) |
| 17 | Netting account refuses a second unit on a symbol | V1, V2 | True (`runtime.py:2888-2906`) |
| 18 | Node's G gate reads the compiled fingerprint | All | True (`runtime.py:2756`) |
| 19 | `qml` depends on `qmf-risk`, not the reverse | V3 | True; V1's map misses it (finding 8) |
| 20 | Snapshot written only on a calibrated move | V1 | True |
| 21 | One compile worker; one runtime thread | V1 | True (`runtime.py:2098,2157`) |
| 22 | Relay has no production importer | V1, V2, V4 | True within `qmx-agents/packages`: only tests name it |
| 23 | Apps can only read market data | V1 | True at `supervisor.py:891`; I didn't read the full capability code |
| 24 | About 12 sites read the sizer | V3 | Fair: 15 lines across 6 files by my grep. `identity/diff.py:247` wasn't matched by it and I didn't confirm it |

**Mechanism checks, not evidence for any choice.**
- V1's probe, rerun: compile 679 ms per unit, 200-unit step 55 ms, in `D:\Temp\judge\v1-probe-rerun.txt`.
- Layer G on the dummy, 2 markets of synthetic bars: 1.34 s at 500 bars, 5.01 s at 2,000, so about 17 minutes per 200 on one core. Real blocks and longer slices will cost more.
- A third run at 8,000 bars raised an error from a stop on the wrong side on my synthetic bars. I did not look into it. Script: `D:\Temp\judge\g_time.py`.

**Not verified.** Real send times. Real throughput with journals at 200 units. Whether a Library block reaches a live node (all four say UNKNOWN). The grafted design as a whole, which is the fold stage's to check.
