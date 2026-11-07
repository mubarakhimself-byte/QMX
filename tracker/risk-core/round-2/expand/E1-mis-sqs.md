# E1: designs for the SQS and the MIS

No agent was ever asked to design these two (`harvest/H1-market-side.md:11-16`). This file does that job. It gives four SQS designs, four MIS designs, how isolation, news and sniping sit across them, how a unit widens its markets, how mini apps publish readings, new physics with a null test each, and what the unit baseline must carry.

**Short version**

- **SQS (spread sensor and gate).** Split the sensor from what it does. One sensor on the node. The default gate becomes a per-trade cost check, so a scalper and an ORB get different answers on the same instrument in the same second. The old rule stays as a floor for broken markets. Shrink, wait and the five-gate bank are shipped as blocks a user can switch on.
- **MIS (market reader).** The app that shipped stays. Two changes shape the core: any app may publish a reading in the same record, and "usual level" curves become one artifact the SQS and the MIS share, so a dead MIS leaves yesterday's curves working. His router becomes the first app on top: it writes a reading called "active markets".
- **Hazard found in the code.** If a unit lists many markets, today's board rule trades all of them when the board dies (`qmn/src/qmn/app/runtime.py:367-369`). His router needs a "home markets" fallback before anyone widens a list.
- **Isolation, news, opens and windows can be one mechanism:** a sticker on a market scope, and each unit says which stickers it ignores. An ORB ignores the "open" sticker, a scalper doesn't. A news unit ignores the news sticker.

**Words used**

| Word | Meaning here |
|---|---|
| R | The loss if the planned stop is hit. Cost in R means cost as a share of that loss |
| Reading | One stamped measurement of a market, in the record the MIS publishes |
| Pack | A list of readings for an instrument class (`packs.json`) |
| Curve | A market's usual level of something for each slot of its week: spread, tick rate, range |
| Sensor / verb | The sensor measures. The verb is what a unit does about it: block, shrink, wait, warn, nothing |
| Sticker | A typed, expiring notice on a market scope. It borrows Kubernetes "taints": a unit's "toleration" says it ignores that sticker. Named here for plain reading; the Kubernetes link is from my memory, and R7 doesn't cover it |
| Allowed / home / active | Markets a unit may ever trade; markets it trades with no list; markets it trades now |

**Tags from the round's test** (`round-2/BRIEF-COMMON.md:31-36`): **[config]** a block, pack or pod setting. **[socket]** the core must leave room now or be reworked later. **[content]** someone adds it later. **[other]** another session's job.

**Method.** `bmad-brainstorming` ran headless: 109 ideas across five technique groups (Appendix A; log at `D:\Temp\E1-brainstorm\.memlog.md`, scratch). `bmad-party-mode` ran in session mode with a trader, quant, execution and systems voice, all voiced by this one agent, with no independent minds (Appendix B). The skill's HTML artifact was skipped, because the brief allows one output file. Code was read at `D:\QMX-worktrees\bld-repair-24`, tip `351e7521` (H1 read `255f3bbf`; the tip moved while this ran). Paths under `qmn/`, `qml/`, `qmx-agents/`, `packages/` are at that tip. `UP/` is `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`. No test or simulation was run.

---

## 1. What shipped, checked first

Another session built the MIS. It is enhanced here, not re-planned. Every row is a read of the code, and I ran nothing.

**Keep as is:** the app form, reading records in a journal that the host's records job harvests, one writer per market, restart without double publishing, holdout sealing, shadow rows, packs as lists of ids, and readings that are QML blocks or `qmf-readings` labelers with no second copy (`qmx-agents/apps/mis/mis_core.py:1-17`).

| What the code does | Where | What the plan said (`UP/architecture/MIS-PAGE-CONTENT.md`) | What it costs | Enhancement |
|---|---|---|---|---|
| One bar size per MIS, default H1 | `mis_core.py:85-89`, `:442` | Each reading states its clock | His router wants 1m and 5m. A 5m run moves every reading to 5m, including Hurst | The card's clock sets the bar **[socket, in the app]** |
| Blocks are fed closes only | `:247-248` `{"series": price}`; `:490` | Volatility from bar ranges, the fastest reading found (about 8 bars against 27 from closes, section 3 item 1, simulated) | The fastest volatility reading has no input here. `garman-klass`, `parkinson` and `rogers-satchell` have reading cards, but a block needing highs and lows gets none (my reading, not run) | Full bar port **[content]** |
| Each round rebuilds each reading from the first bar of its window | `:245-248`, `:486` | Silent | Fine on H1. On 1m across many markets, every round replays months. Cost UNKNOWN, not measured | Keep reading state between rounds **[content]** |
| A pack can't set a block's parameters | `:426-429`: parameters reach labelers only | "Every default is a starting value he can change" | Configurable only by shipping a new block version | Pack parameters reach blocks **[config]** |
| One value and one word, with fixed cuts on the card (`variance-ratio`: 0.9, 1.1, `origin: inferred`) | `:253-254`, block `entry.json` | Three forms: value, where it sits against usual, word | No "against usual" exists. Nothing in the record says where a value sits against its own history | Curves (section 3, MIS-4) plus a third form **[socket]** |
| All nine classes run the same five readings | `packs.json` | Each class adds its own: fix windows, funding, roll, cash open | "Per class" exists as a name only | Pack contents **[content]**. 17 stdlib blocks have reading cards, only 4 are in use. Clock blocks exist for EIA, LBMA and funding, with no cards |
| `spread_state` uses fixed point cuts, the same in every pack | `packs.json`; `labelers.py:224-229` | "Spread against usual" | The same cut on EURUSD, gold and an index means different things. A third spread measure beside SQS and any cost table | Retire it when curves arrive **[content]** |
| A tick-tier reading is read from the store once per round, with a 2-second freshness | `:264-276`, `:927-928`, `packs.json` | "The node itself runs the readings that need every tick" | It will read stale on most rounds (my reading, not run). The plan's split is right and this row is a stand-in | Move to the node when the node sensor exists **[socket]** |
| The record's source is `node` or `mis` | `packages/qmf-readings/.../record.py:32-36` | Silent | No other app can publish in this shape | Open the source (section 3, MIS-2) **[socket]** |
| The MIS is the only app declaring `data_reads`, with `["market"]`. No app declares reading readings | `apps/*/app.toml` | His mini apps feed each other (M50) | UNKNOWN whether the supervisor has a capability for it | Hand-off to the mini app contract **[socket]** |
| Clock facts don't reach the app: `clock_ok=False` | `:857-858` | Stamped history | As-of questions rest on an unproven clock | Repair's C-01 (comment at `:857`) **[other]** |

**The node side.**
- `Runtime.guard` runs after sizing, sees only a market name, and has no spread or news check (`runtime.py:2623`, called at `:1757` after `lots()` at `:1745`). `_entry` holds the stop and quote (`:1043-1075`).
- Its scopes name instruments only (`:1675-1678`), so no class or region can be stopped.
- `Placement` is a narrow-only read that holds back a market when a fresh board disfavours it, and trades every listed market when the board is stale or missing (`:333-369`). R18 leaves the relay off (`unit-baseline/SWAP-CHART.md:290`).

**The unit side.** `reads`, `sessions` and `context_needs` exist in the model (`qml/src/qml/unit/model.py:391-396, 445-449, 481-488`), and the compiler refuses all three by name (`qml/src/qml/compile/compiler.py`, `_shape_problems`). `Read` holds reading, market, fallback and staleness, with no publisher. `Fallback` has three values (`model.py:157-160`).

**The SQS.** The rule survives outside the deletion in `packages/qmf-readings/.../labelers.py:331-440, 625-650`. The gate that calls it is in the old node, and C-20 deletes that (`grounding/G12-audit-and-repair-for-risk.md:151-222`). The new node has none. No caller builds a baseline. The reason code `spread_wide` exists and nothing writes it.

---

## 2. SQS designs

Today's rule in plain words: live spread is compared with a baseline, an entry is refused when the score falls below a line, it clears with a band so it doesn't flap, and it needs a baseline earned in this same environment (`G12:178`, `:193-207`). His ruling: "Kill switch and SQS stay" (`G12:423`). He also opened it to redesign (M52). All four designs below keep exits unchecked.

### SQS-1. The same gate, moved and made swappable

**What it is.** The old rule on the new node, as one block in an entry-gate slot, reading a per-instrument curve. It answers: "is this spread unusual for this instrument right now?"

| | |
|---|---|
| **Buys** | Keeps his ruling at the lowest build cost. A clear fact with no hidden size change. Rule text already written and tested in the old path |
| **Costs** | First live entry waits hours for a live baseline (`architecture/SPINE.md:475`). Eight settings to fill, each blocking live when blank (`G12:214`). It knows nothing about the trade: a spread can be usual and still eat a tight scalper's edge, or be unusual and not matter to a wide-stop trade |
| **Scalper, several instruments** | Blocks one instrument during its own blowout while the others carry on, which matches his news-day picture in M51. It misses the slow killer: spreads that stay usual but too costly for this unit's stop |
| **ORB, several opens** | Opens are wide. Against a whole-day baseline the gate blocks exactly when ORB wants in. A same-minute baseline fixes most of it, but a usual-for-the-open spread that is still high passes, which is the right answer only by luck |
| **Needs from the unit** | Nothing beyond its instrument. Needs an entry-gate slot on the host, plus the curve |
| **Configurable** | Block in a slot; the settings live in a pack or pod. A user can swap the percentile gate in (A3-070) |
| **When something is down** | Doesn't touch the MIS, because it is on the node. Curve factory down: the last curve stands with an age word, then the pod's choice applies. Sensor can't read: refuses entries on that instrument only, as the old rule does (`labelers.py:400-406`) |

### SQS-2. The cost hurdle

**What it is.** Stop asking about the spread and ask about the trade: "at this quote, with this stop, does this entry still clear what this unit allows for costs?" Live spread, commission and expected slippage come out in R for this one trade, then compare with the unit's stated allowance. Sources: `research/R4-alphaxiv/chat-27-E-microstructure.md:26-28` (cost hurdle, gate on executable conditions); A3-070's example of a 5-pip edge keeping 4 at 1 pip of spread; his M51 line that QMX observes costs and acts on them.

| | |
|---|---|
| **Buys** | Style handled with no style code. Same instrument, same second, two right answers. **No warm-up:** live spread and stop are known at the first tick, so the first entry doesn't wait hours. Works per trade, so it also tells which instruments a given stop width can trade at all. It reads as data analysis, the way he framed it |
| **Costs** | Blind to a broken market whose spread looks small against a wide stop, so it needs a floor. Needs a commission record and slippage estimate, and costs are synthetic until fills exist (H1 idea 11). Needs the stop before the gate, so the host's order changes. It isn't a market state, so it doesn't feed isolation by itself; the sensor underneath does |
| **Scalper, several instruments** | The main gain. In a costly minute a tight-stop scalper stays out on the costly instrument and trades the cheap ones. With forward cost added it can also see an exit landing in rollover hour (Appendix A idea 12) |
| **ORB, several opens** | Passes at a wide open because its stop is wide. Each open gets its own answer. A narrow opening range gives a tight stop, and the same trade is refused, which is what a trader would do |
| **Needs from the unit** | A stop at the gate, and one declared allowance. A unit with no price stop is refused today anyway (`SWAP-CHART` row 11). Python units state an estimate |
| **Configurable** | Allowance is a template default, a pack value, or a pod override. Cost table cell or live quote is a setting. A reckless unit sets its allowance wide open |
| **When something is down** | No MIS or curve involved. Cost table missing: live spread alone with a flag, or refuse, per pod. No quote: `_entry` already blocks (`runtime.py:1066-1072`) |
| **Replay** | QMB uses recorded quotes where they exist and the cost table cell where only bars exist, labelled on the row. R19's minute rows carry spread (`SWAP-CHART.md:291`, chart only, not read in code) |

### SQS-3. The fillability bank

**What it is.** A small bank of fast sensors asking "can the market fill an order now?": spread against usual, tick rate, quote gaps, micro range, recent slippage. Own fills feed back through short markouts: where the mid went after a fill. Sources: A3-073, A3-074, X0-18, B008, chat-27 section 1. "The EA does not predict direction" (MQL5 22772 via A3-073).

| | |
|---|---|
| **Buys** | Catches liquidity leaving before the spread shows it. Learns one broker's habits. Its parts are also isolation evidence and the restore check (H1 ideas 13, 14). Closest to what a human scalper feels as a bad tape |
| **Costs** | Most machine of the four. Each sensor adds settings. "Safety filters can also screen out winners", and the papers give no count of how many (`chat-27:130-140`). Needs tick data and own fills. Tick rate means quote updates on retail feeds (A3-073 class note). Noisy gates should start as shadow labels (`chat-27:144`) |
| **Scalper, several instruments** | Real benefit in thin hours and around quote gaps. Real risk of sitting out too much. Needs a refused-share reading so an agent sees strangling |
| **ORB, several opens** | Little use on entry: an open is fast and gappy by nature, so most sensors would refuse it. ORB would ignore most of the bank |
| **Needs from the unit** | A per-sensor pass or refuse list. Markout on the trade row |
| **Configurable** | Each sensor is a block. The bank is a pack. Default state: shadow |
| **When something is down** | Node-side, so no MIS dependency. One sensor dead reads as `unknown`: that sensor's chosen fail mode applies, not the bank's |

### SQS-4. The cost dial

**What it is.** No yes or no until very late. As live cost climbs against the unit's proven band, size steps down, and only past a hard line does the entry stop. Sources: X2-H42, A3-071 (602 NQ sessions, author backtest), A3-076 (the old multiplier that never ran).

| | |
|---|---|
| **Buys** | Keeps trading in costly minutes, which answers "sitting duck". Graded response. Natural pair for his brakes and accelerators |
| **Costs** | Conflicts with "never shrink" (X3-H63). His stated fear: stacked multipliers were the old handbrake (A3-185). Any cut looks good on a losing unit unless tested against a random cut (H1 idea 17). Near the smallest tradable size a shrink rounds to a refusal, so at small accounts this behaves like a blocking gate. It cannot live in the guard, because the guard runs after sizing (`runtime.py:1745, :1757`) |
| **Scalper, several instruments** | Stays active everywhere at varying size. Good if its edge survives the cost, bad if the costly minutes are simply negative after costs, where smaller is still a loss |
| **ORB, several opens** | Smaller at wide opens, which may cut size on the very trades that carry its result. Needs its own band per open |
| **Needs from the unit** | A sizer that takes a cost input and a named modifier with its reason on the receipt |
| **Configurable** | A modifier block on the sizer socket; a preset can stack it or not |
| **When something is down** | Missing cost means the modifier reads absent and says so on the receipt. The old default of 1.0 hid this (`G3:71-87` via A3-185) |

### Comparison

| | SQS-1 same gate | SQS-2 cost hurdle | SQS-3 bank | SQS-4 dial |
|---|---|---|---|---|
| Question asked | Unusual? | Worth it for this trade? | Fillable? | How much? |
| Knows the trade | No | Yes | No | Partly |
| Waits for a baseline | Yes | No | Yes | Yes |
| Treats scalper and ORB differently by itself | No | Yes | No | Only with bands per style |
| Catches a broken market | Yes | No | Yes | Late |
| Can also feed isolation | Yes | No | Yes | No |
| Settings to carry | Eight | One allowance plus cost record | Many | Several |
| Risk of a handbrake | Medium | Low | High | High |

### Recommendation

Build one sensor and an open slot, and ship this template default: **SQS-2 as the gate, SQS-1 as the floor for broken markets.** SQS-3's parts and SQS-4 ship as blocks, in shadow or off. Also offer a "wait" verb as a block later (Appendix A idea 9).

Why:
1. SQS-2 alone gives the scalper and ORB the right different answers with no style code, which is what he asked of the canvas.
2. It removes the hours-long wait for the first live entry, a defect the old design accepted (`SPINE.md:475`).
3. It fits his M51 model.
4. SQS-1 as a floor honours "SQS stays" and covers SQS-2's blind spot. It also gives isolation its fast tell.
5. SQS-3 and SQS-4 carry real risk of a handbrake, and neither has evidence on net returns. Shadow labels will tell (`chat-27:142-144`).

What would change this: if shadow runs show the bank catches costly fills that the hurdle lets through, more of SQS-3 moves to default. That is a test, and it sets no number here.

What must not wait: the sensor, the slot and the facts passed to it are **[socket]**. Allowances and floor lines are **[config]** and belong to the numbers talk.

---

## 3. MIS designs

All four keep his three rules (`MIS-PAGE-CONTENT.md` groups A, B): it reads and publishes, it never switches a unit on or off, and no unit needs it. Fast-reading limits apply to all: volatility shows in minutes, while trend or mean reversion on 1m and 5m takes about 4 to 5 hours to show (section 3 items 1-2, simulated on made-up bars). Only a label known at entry is honest (item 3).

### MIS-1. The deeper board (the unit plan's design, finished)

**What it is.** One MIS with tiers. Fill the packs the plan lists, give each reading its own clock, publish value, against-usual and word. Units read through `reads` with a fallback. Reading organisation stays option H: tier and data level on each reading, class as a pack (`UP/research/23-mis-organisation.md:60`).

| | |
|---|---|
| **Buys** | Least new thinking, since most of it is designed. One vocabulary. His groups A to M are already mapped. It is what the MIS page already told him |
| **Costs** | Everything is central, so everything waits on one app and one owner. Many readings to build before any is proven useful. Sprawl (`mis-field.md` P7, B124). His department picture has no seat. SQS and the MIS keep separate baselines unless someone joins them |
| **Scalper** | Gets fast "now against usual" words from the node and a session list of reverting markets. Binds what it wants |
| **ORB on several opens** | Gets cash-open readings, opening drive and overnight range per open, if the packs carry them. Needs a calendar reading per class |
| **Needs from the unit** | `reads` compiled; `context_needs` compiled |
| **Configurable** | Pack lists; reading cards; shadow to live |
| **When it is down** | Readings go stale, the unit's named fallback applies, the unit trades (`MIS-PAGE-CONTENT.md` "How units use it") |

### MIS-2. The open bus (the MIS as one publisher among many)

**What it is.** The important thing becomes the **record and its rules**. The shipped MIS stays as the default publisher of the default pack. Any mini app, pod or agent workflow can publish readings in the same shape, under its own name. A unit pins publisher, reading and version. This is his "mini apps can provide output and input for other mini apps" and "departments" (M50), and `AGENT-DEPARTMENT-SEEDS.md:59-61`.

| | |
|---|---|
| **Buys** | The canvas. A futures mini app, a macro workflow or a user's paper reading can all reach a unit with no change to the MIS. Trained models fit the same slot. Lowers what must be right first time: a poor default gets replaced, not rebuilt. Adds no service, since the record and journal shipped |
| **Costs** | Quality isn't guaranteed by construction. One word may mean different things across publishers, so it needs the same-meaning check (`mis-field.md` P5-c). Silent meaning changes (P10-a: "a wrong MIS is worse than a dark one"). Possible cycles between apps. More herding to count |
| **Scalper** | Same as MIS-1 by default; a gold mini app could add its own fast readings computed at the node |
| **ORB on several opens** | An index mini app publishes "opens in play today" with its own method. A different user swaps in another |
| **Needs from the unit** | Publisher on `Read`; a fallback per read; the decision row records publisher, version, age |
| **Configurable** | This is the customization layer: a pod or template pins publishers |
| **When it is down** | One publisher down makes only its readings stale. Nothing else notices. A publisher can't take the node down, because reads are files and records, not calls |

### MIS-3. The finder (his router as the main product)

**What it is.** Flip the output. Instead of a board per market, the core answer is per unit: "here is where your claim is true now." A unit writes its context claim in the MIS's words ("reverting, quiet, costs fine"), and the finder returns an active market list for the next session or day, re-run at each session open. His M5 words (`seeds/SEEDS.md:616`), B023, B030, B081, B121.

| | |
|---|---|
| **Buys** | His idea, directly. It gives the MIS a job that a unit can't do alone: a view across markets. The output is easy to score: run router, agent and all-allowed lists side by side (B035). Answers "How do we change sessions?": re-run at handover |
| **Costs** | Works as a session or day list, never per trade (`MIS-PAGE-CONTENT.md` section 3). The ranking is itself a tuned thing, so it counts as a try. It can route into a market with no record for that unit. Can herd all mean reverters into a few markets. He found the old router machinery over-built on 28 Oct (`mis-field.md` section 5), so this must stay a list, without offers, expiry auctions or planners. Weak claims give weak lists |
| **Scalper** | The design's best case: the mean-reversion scalper moves between gold and some FX pairs by session |
| **ORB on several opens** | A pre-open shortlist: which opens look in play today by tick rate, overnight range and calendar. Then each open trades as one family |
| **Needs from the unit** | Allowed, home, active. A claim in words. Records per market. A same-bet key |
| **Configurable** | Finder method is a publisher, so it's replaceable. Whether a unit obeys is a read with a fallback. Pod sets who may route |
| **When it is down** | The list ages out and the unit returns to **home** markets. This needs the change in section 5, because today's fallback is every listed market |

### MIS-4. Two products: the curve factory and the node stream

**What it is.** Stop treating fast and slow as one thing (QF01, B054, B055, B082, B085, B086). Nearly everything a scalper needs is "now against usual for this minute of the week", and SQS is one case of that (`H1` idea 19).

- **Slow product, the shipped app grown a little:** overnight it builds each market's curves for the next session, plus the session and day words and an almanac. Curves land as a fingerprinted Library artifact.
- **Fast product, on the node:** it divides live by curve, and that is nearly all it does. Spread, tick rate, range, quote gaps. No model on the fast path.

| | |
|---|---|
| **Buys** | **One baseline, shared by SQS, MIS and QMB,** ending three spread measures drifting apart (`H1` section 3). A dead MIS is safe by structure, not by promise, because yesterday's curves are on the node. A market added today gets curves from history with no live wait (B059). Weeks of tick work on the node become simple division. Fits "you are not going to put an HMM inside a scalper's MIS". The same-minute baseline is already specified (A3-181) |
| **Costs** | Curves go stale across a real change in the market, so they carry an age word. Holidays and clock shifts distort them (B065, A3-181 known failures). Thin markets give thin curves. Needs tick code on the node, and that file is repair's today, so it waits for the seat. Demo curves aren't live curves (DEC-0230), so cold start needs a flagged borrowed curve or a wait, chosen per pod |
| **Scalper** | Fast words with little compute across many instruments. Same numbers in test and live |
| **ORB on several opens** | "Against usual for this open" is exactly what it wants, per open, since each open has its own slot in the curve. It reads activity at the open against that open's past |
| **Needs from the unit** | Nothing new beyond reads; node-side readings arrive with source `node` |
| **Configurable** | Curve shape (same minute, hourly, percentile), history length and refit are artifact settings. A user can publish their own curves |
| **When it is down** | Factory down: curves age, words carry the age, and each unit's fallback applies past its limit. Node stream down means the feed is down, and entries already stop on that node (`runtime.py:2649-2652`) |

### Other poles, kept for the funnel

`mis-field.md` holds further shapes I folded in rather than listing: slow-only (B106, largely MIS-4's slow product with fast work in units), no central MIS (B105, loses cross-market readings), cross-sectional only (B107), per-reading placement rule (B126, the August rule, worth keeping as a card field). Reading-from-units (B103, B104) is in section 7 as a test.

### Comparison

| | MIS-1 deeper board | MIS-2 open bus | MIS-3 finder | MIS-4 two products |
|---|---|---|---|---|
| Main output | Words per market | Records from many | List per unit | Curves, and now against usual |
| Fits his M50 departments | Weakly | Strongly | Through a publisher | Weakly |
| Fits his router | With an extra job | As an app | Directly | Supplies inputs |
| Safe when dead | By fallback | Per publisher | With home markets | By structure |
| Ends the three spread measures | No | No | No | Yes |
| Change to the core if left out now | Low | **High** (record, read) | **High** (allowed, active) | **High** (one baseline) |
| Adds to what shipped | Readings | A field and rules | A job | A nightly job and a node reader |

### Recommendation

They are not rivals on one axis. MIS-2 settles who publishes, MIS-3 what the output is for, MIS-4 where things run, MIS-1 what gets read.

**Take MIS-2 and MIS-4 as the shape; build MIS-3 as the first app on top; treat MIS-1's list as pack content filled over time.**

Why:
1. By the round's test, MIS-2 and MIS-4 are expensive to retrofit. The record's source, the read's publisher and the one baseline touch every later reading. Pack contents don't.
2. MIS-3 needs no new service if its answer is a reading (section 5), so it can be replaced like any other. That keeps it from turning into the machinery he called over-built.
3. MIS-4 makes "a unit keeps trading without the MIS" true in the simplest way.
4. This leaves the shipped app's core untouched. It gains a per-card clock, a curve job and an open source field.

**Cost to be honest about:** MIS-2 hands out rope. A wrong third-party reading can hurt the unit that pinned it. The defence is pinning, shadow rows, a dark-run comparison (B061) and meaning-flip replay (B064). No central approval stands in the way, because "a reckless setup must be expressible". Agent-written readings are the exception (section 6).

---

## 4. Market isolation, news and sniping across the designs

### One mechanism for three of them: stickers and tolerations

Isolation, news and caution windows look like three features. All three say "this scope is special until this time, here is how strong, here is why". So: one **sticker** record, stored in the stand-down table that exists (`runtime.py:2664-2673`).

| Field | Why |
|---|---|
| Scope | Instrument today; class, region, currency, underlying, session as well. "It can isolate crypto" (C27) needs it. `instrument_scopes` gives two keys only (`runtime.py:1675-1678`) |
| Kind | `news`, `open`, `fix`, `isolation`, `unknown`, or any name a publisher adds |
| Strength | Prefer not, no new entries, flatten. These are his graded modes (H1 idea 23). Strength "prefer not" means the sizer or a read may use it; it blocks nothing |
| Expiry and resume rule | Every isolation has an end (H1 idea 23); resume on spreads and depth, not the clock (H1 idea 32) |
| Why, and who | Evidence ids; publisher; so accuracy can be scored afterwards |

Each unit (or its pod or template) lists **tolerations**: sticker kinds it ignores. Default templates: a scalper tolerates none; an ORB tolerates `open`; a news unit tolerates `news`.

**This settles several open collisions without a global rule:**
- ORB allowed where a scalper is blocked (X0-30).
- News units against a global news window (QO11, H1 idea 33).
- "Is this a pod question?": yes. Tolerations and strengths are pod settings (M49).
- A fix-reversal unit against a caution window (H1 idea 36).

**Fixed lines hold:**
- The kill switch is not a sticker and can't be tolerated.
- Only his hand lowers the kill switch.
- Stickers act on entries, except `flatten`, which closes and so can't block an exit.
- An agent-placed sticker can only reduce risk and must expire.

**How a sticker fails:** a sticker table the node can't read counts as `unknown` for that scope, and its strength is a pod setting. This is the fail-closed-for-one-scope from X3-H36 without touching the board's fail-open, which answers `H1` section 3's "compatible only if an isolation is a stand-down and not just a word on the board".

### Market isolation

His question: "how does the MIS adjust?" (C27). **Answer: the MIS doesn't. It keeps publishing what it sees. The sticker refuses entries, and the finder doesn't list a stickered market.**

| Part | Where | Tag |
|---|---|---|
| Who may place: a rule on two different tells, an agent card, a person | Rule is a pod block (H1 idea 23); agent card is de-risk only with expiry (H1 idea 27) | [config] |
| Evidence | SQS blocks across a class; volatility against usual; liquidity commonality (section 7); slow tells on the day tier (H1 idea 26) | [content] |
| Accuracy record | Each isolation writes whether a loss followed, with blocked trades as would-have rows (Appendix A idea 16) | [socket] |

**Across the designs:** with SQS-1 or SQS-3 the fast tell is built in. With SQS-2 alone there is no tell, which is another reason for the floor. MIS-4 gives every market an against-usual reading on the same scale, so "many instruments unusual at once" can be counted cheaply. MIS-2 lets a macro app supply the slow evidence. MIS-3 is a user of stickers only. "No public source on a fund switching off one class by rule" (`R2:185`), so this is a design without live precedent: exchanges do it per product and market-wide (`R2:140`).

### News

| Layer | What | Tag |
|---|---|---|
| Calendar to sticker | Event carries driver tags: both FX legs, home exchange, region, commodity. US CPI stickers indices, gold and USD pairs, not just "USD" (H1 idea 30) | Tags on the instrument record [socket]; tag lists [content] |
| Strength | Measured impact replaces the colours as data arrives (`R2:177-179`) | [content] |
| Who decides | Pod setting; kill switch keeps the hard kill (H1 idea 31) | [config] |
| Trading news | A news unit tolerates the sticker and reads event-clock readings: minutes since release, reaction, spread recovery (B010, B108). No surprise reading on today's free feed, which lacks actuals (`R2:178`) | [content]; event clock [socket] |
| Before the event | Pre-event liquidity state predicted the post-event state better than event labels in BTC and ETH futures (arXiv 2607.09230, abstract; `H1` idea 18) | [content] |
| Missed releases | A velocity tell backstops the calendar (H1 idea 32) | [content] |
| News agents | Typed, expiring, de-risk only, provenance, one-item effect limited (`chat-28:125-148`). Fabricated news worked better on agents than prompt injection (`chat-28:207`) | [other] agent session; door [socket] |

His M51 picture is met directly: a sticker on one instrument on its news day, others trade on. SQS-1's floor catches the same day if the calendar missed it.

### Sniping windows and opens

**His question "is ORB the sniping period?"** (`H1` gap 6) gets a plain answer: **No, they're different kinds of thing.** ORB is a logic. An open is a window. A sniping window is a record that says one unit family on one instrument does better in one slice. ORB could have a sniping window, and a scalper's sniping window could be an open.

A **window card** is a Library artifact: slice, family, how found, try count, expiry, status. Status can be `hand-written`, `shadow` or `proven`.

| Path | How | Note |
|---|---|---|
| Deterministic | Slices where the curve shows low cost and high activity (`X0` P5a) | Misses flow windows such as fixes |
| Agent | Nominated from papers, videos and the almanac, proven by QMB, each a counted try (`X0` P5b, X7-H25). His week-with-the-copilot picture (M50) | Too many tries inflate false windows, so count them |
| Hand-written | A user types "gold, this hour" | Allowed. The card says unproven. **This is the canvas: his belief about gold (M50) can trade without anyone proving it first**, and the record then speaks |

**Effect, by the same two mechanisms:** a window raises size through the named sizer socket with a receipt, or a unit restricts itself to windows through `sessions`. The opposite of a sticker: a sticker says "careful here", a window says "this one earns".

**Evidence, stated once:** research says a window lowers cost or raises activity and does not hand out edge (`R2:24`, `:67-69`). Picking hours from a unit's own backtest is look-ahead (`R2:69`). He disagrees from what he has seen in gold. That argument is in the numbers talk (`PARKED-FOR-NUMBERS-TALK.md`), and the design doesn't settle it.

**Caution widths at opens.** "No generation derived a caution-window width" (`H1` idea 36). MIS-4 can derive one: minutes until spread and activity return to usual for that open. That is a measurement per instrument, and no number is set here.

### How each design treats the three

| | Isolation | News | Sniping and opens |
|---|---|---|---|
| **SQS-1** | Block counts across a class are a tell | Catches a blowout the calendar missed | A same-minute curve stops false blocks at opens |
| **SQS-2** | No tell | Handles cost, not events; a tight stop stays out by itself | Hands ORB its pass with no window logic |
| **SQS-3** | Several tells | Quote gaps show withdrawal before the print | Most sensors refuse opens, so ORB tolerates them |
| **SQS-4** | No tell | Size falls before the block; unclear if that's wanted | A low-cost slice can't raise size; that's the window's job |
| **MIS-1** | Class words on a board | Calendar readings in packs | Almanac; window readings (B012) |
| **MIS-2** | A department app may place de-risk cards | A news app publishes event readings | Window cards from any app |
| **MIS-3** | Doesn't list stickered markets | Doesn't list a market with a news sticker in the session | Lists "where this unit's windows are open today" |
| **MIS-4** | Against-usual counts, cheap | Aftershock clock from curves | Windows derived from curves; widths measured |

---

## 5. How a unit reads and widens markets (his router)

**His words:** the scalper "changes its scope, which means it's now focusing on those" (`seeds/SEEDS.md:616`). **The plan's rule:** the MIS can only narrow, and widening is a new version and his click (A3-184). **Not settled** (`H1` section 3).

### A simple shape: the active list is a reading

No router service, no planner and no new transport. A finder publishes a reading whose value is a list of markets.

```
markets:  allowed   gold, EURUSD, GBPUSD, USDJPY, NAS, ...
home:     gold, EURUSD
reads:    active-markets from <finder>, fallback: home, stale after: <setting>
```

- **Narrowing already works this way.** `Placement` holds back listed markets by a word on the board (`runtime.py:336-369`). A wide `markets` list plus a list reading **is** widening, from the unit's view, with no change to the "only he promotes" line: he approved the allowed list.
- **The hazard.** Today a stale board means trade every listed market (`runtime.py:367-369`). That was safe when lists were short. On a wide unit, a dead MIS would turn on its whole universe. **Fallback must be home markets.** `Placement` must gain this, or the wide list must be refused until it does. **[socket]**
- **Locking.** The list is read at session open and held until the next open, or by setting. A persistence reading takes hours to show (`MIS-PAGE-CONTENT.md` section 3), so a per-trade route would be noise. Open positions in a dropped market keep their exits.

### The ladder, each a setting

| Rung | What it does | Who clicks | Good for |
|---|---|---|---|
| 0. Fixed | Unit trades its list | Promotion | A market-specific unit (his System 2) |
| 1. Narrow | Board holds some back (shipped, unwired) | Promotion | "Only where favoured" |
| 2. Active list | Reading picks from allowed, home as fallback | Promotion covers allowed; a pod can ask for a card per newly active market | His router |
| 3. Card adds to allowed | Readings resemble proven markets, agent lands a card, new version, counted try (B121, B100) | Him or rule, per methodology | Finding new ground |
| 4. Free | Allowed is a whole class | Promotion | A reckless setup, expressible |

### What a router needs that isn't a router

| Need | Why | Tag |
|---|---|---|
| Records per unit and market, and per session | "The router can be wrong; records must be per unit and market" (A3-187). Plan splits per market only (G7 5.3 via H1) | [socket] |
| Newly active market marked on the trade row | So a probation size setting can apply, and so results can be read | [socket]; the size is [config] |
| Same-bet key, and a cap per cluster by unit rule | All mean reverters on three markets is one bet (B045, B048) | Key [socket]; rule [content] |
| Lists kept and scored | Router, agent, all allowed, side by side (B035). If the router doesn't beat all-allowed, it says so | [content] |
| Spread and cost in the finder | "At small size, costs and minimum sizes choose the markets before the MIS does" (H1 idea 51). His "best basket" (M50) is this | [content]; talk parked |
| Honest labels only | Backtest uses as-of readings (B090); a hindsight label claimed a 76% better edge per trade, in simulation on made-up bars (`MIS-PAGE-CONTENT.md` section 3 item 3) | [socket] |

**Other routing methods, swappable as publishers:** reading match (default), twin search (B100), "is today like my good days" (Appendix A idea 54), scouts or pheromone (Appendix A ideas 52, 53), an agent's morning brief (B033), a person typing a list. All write the same reading.

**How sessions change (his question).** Tokyo to London: the finder re-runs at handover, the reading changes, and units trade the new list. Words like `reverting` are keyed per market, so nothing in the unit is named London. Positions overlapping the handover are linked only by the same-bet key (H1 idea 3).

---

## 6. Mini apps publishing readings

### The contract

Everything an app publishes uses the shipped record with these changes:

| Change | Why | Tag |
|---|---|---|
| `source` becomes publisher identity (`node`, `mis`, or `app:<id>`, `agent:<id>`) | The enum closes the door today (`record.py:32-36`) | [socket] |
| A declared capability to read other apps' readings, and one to publish | His "output and input for other mini apps" | [socket]; mini app contract, shared with `round-2/expand/E2-pods-miniapps.md` |
| Inputs named on each record | Lineage, and refusing cycles at configure time | [socket] |
| `valid_until` beside `stale_after_s` | Agent and event readings expire by meaning, not by age (`chat-28:125`) | [socket] |
| Reading card published with it | Tier, clock, data level, lag, minimum sample: the card shape already exists on blocks | [config] |

### Rules

1. **Reading isn't controlling.** A publisher can't place, size or close. A unit chooses to read, by pin, with a fallback.
2. **Shadow first by default.** A new publisher writes `health: shadow`; a unit going live on it is a promotion matter.
3. **Tier follows speed.** LLMs and slow workflows may not publish on tick or fast bar tiers (`chat-28:125`; latency in `chat-28:187`).
4. **Agents never touch money.** A reading written by an agent may only reduce risk through any verb: block, shrink, or sticker. A human-pinned template may use an agent's reading as an input to a selection list, since choosing among allowed markets is not sizing. Whether that holds is for the agent session to test. **[other]**
5. **No look-ahead by tool.** An agent's read tool returns only data stamped before its own timestamp (B041).
6. **Scored like sensors.** Agent, MIS and all-markets lists compared (B034, B035). `chat-28:150`: safety improvement counts as safety; call it alpha only if net results repeat out of sample.
7. **Same word, same meaning.** A shared word needs a test across classes before a unit may match on it across classes (P5-c).
8. **Retire what nobody reads** (B124).

### Example walk: his departments

1. A **macro mini app** (a workflow, day tier) publishes `usd-state`, with sources, valid until the next release.
2. An **FX mini app** reads it with its own microstructure readings and publishes `fx-carry-stress`, plus a card asking for a de-risk sticker on JPY for three days.
3. A **futures mini app** works a week with the copilot (M50). It publishes an ORB shortlist, its own curves and two window cards.
4. A **finder** reads all that and writes `active-markets`.
5. A **unit** pins the finder, falls back to home, and never knows how many departments sit behind the reading.

If all of them die, the unit trades home markets. Each step was a record. The trade row shows which readings it saw, with source, age and version.

**Not designed here:** which agents, how they run, and the methodology for each (`handoff/AGENT-DEPARTMENT-SEEDS.md`) **[other]**. Screens for the MIS tab, market card, weather report **[other: UI session]**.

---

## 7. New physics worth testing

He invited it: "Whether there is new market physics... no problem" (`seeds/operator-words-2026-11-03.md:176`). Nothing on disk offers new physics beyond a quarry note (`H1` idea 42). "Ising-type measures have no trading evidence found" (via H1). The on-disk OHLCV record is cautionary: fourteen intraday momentum signal families on MNQ, 947 days, none cleared five tests after costs (arXiv 2605.04004, abstract read).

**Evidence tags.** *Disk*: read on disk this session. *Snippet*: alphaXiv search abstract only, from this session. *Memory*: from my memory, not checked; treat as a lead. *Mine*: my construction, with no source.

### Every reading passes the same three floors

No values here; those belong to the test plan.

1. **Null floor.** The statistic differs from what the same statistic gives on data with the claimed structure destroyed (each row's null).
2. **Bounce floor.** Run on mids and on a price with synthetic bid-ask bounce, since bounce fakes mean reversion 10 to 130 times more often than designed (`MIS-PAGE-CONTENT.md` section 3 item 4).
3. **Use floor.** A unit with the reading against the same unit with shuffled labels at the same rate (B096), as-of stamped, net of costs. Every run counts as a try. "Differs from the null" alone is not a reason to ship.

All of these enter as blocks with reading cards in shadow **[content]**. None changes the core, given sections 3 to 6. Quote-based ones need a tick or activity port to QML blocks, since cards support `time_base: ticks` (`record.py:49-52`) but the MIS feeds closes only.

| # | Reading, plain words | What it might tell a unit | Data | Null test | Standing |
|---|---|---|---|---|---|
| P1 | **Activity-price split ("market temperature").** Price move per quote update, against usual. Splits "busy" into busy and moving, busy and churning, quiet and jumpy | High move per update means thin or informed: scalper steps back. Low move per update means churn: reverters like it. Answers "Busy can mean deep, wide, fast, or all three" (H1 idea 11) | Quotes (rung 2), so cTrader works | Shuffle tick times within the same minute-of-week bin, keeping seasonality; the split's day-to-day persistence should vanish | Mine, built on trading-time ideas (Clark, Ané-Geman, memory). Tick count tracks volume hourly, one vendor study (`MIS-PAGE-CONTENT.md` section 3 item 6) |
| P2 | **Quote self-excitement (Hawkes branching ratio).** How much of the quote flow is reacting to itself rather than to outside news | Rising self-excitement may warn of a cascade; a reflexivity reading he would recognise from physics | Quote or trade timestamps | Same-seasonality surrogate with a time-varying rate and no self-excitation. Must also survive a different event definition | Snippet, with warnings: 1302.1405 finds near-critical on E-mini; 2610.36317 says large-tick clustering is partly a feed artefact; 2610.19428 says common signals fake cross-excitation; 2610.35159 on apparent criticality. **Expect failure unless it clears these** |
| P3 | **Liquidity commonality.** Share of spread changes in a class explained by one factor, moment to moment | Fast class-wide tell for isolation, with no price move required. Catches a provider pulling quotes | Spreads across a class | Shuffle each instrument's time index independently; share should fall to the noise level from random-matrix theory | Strongest here. FX liquidity moves in common, Mancini et al. via `R2:166`; rises in stress, `R2:167`; this reading form is mine |
| P4 | **Aftershock clock.** After a shock, spread and range decay on a power-law clock (seismology's Omori law) | How long after news to wait, by event class, instead of a fixed window. Gives his re-entry on spreads | Spreads, quotes | Same event times moved to placebo slots of the same minute of week; no decay should appear | Omori in markets: memory (Lillo, Mantegna; Petersen). Application to spread is mine |
| P5 | **Directional-change clock (intrinsic time).** Count reversals of a set size rather than minutes; read how far moves overshoot | A clock that stretches in busy hours. Suits a scalper's own move size. Would use `time_base` as an event clock | Quotes or M1 | Simulate a random walk with the same volatility curve and fat tails. Overshoot laws also appear there, so only the gap counts | Memory (Glattfelder, Olsen). Two on-disk hits for the words are unrelated uses. **Strong risk the null absorbs it** |
| P6 | **Class alignment (Ising, retested).** Share of a class's markets moving the same way, and how much that swings | Old system blocked on it (`G3:81` via H1 idea 42). Possible risk-off tell and same-bet warning | Bars across a class | Independently permute each instrument's moves; keep its own autocorrelation with block shuffling | "No trading evidence found". Retest, don't restore (B123) |
| P7 | **Time irreversibility.** Does a price path look different played backward at short scales? | A cheap measure of order against noise, for the "is this tradable" question | Bars or ticks | Time-reversed series and phase-randomised surrogates | Snippet: 2604.14962 on fluctuation-theorem-like asymmetry; 2602.00383 on null-validated topological signatures as a sibling |
| P8 | **Critical slowing.** Recovery from small shocks slows before a state change: autocorrelation and variance creep up | Warns before a state changes (B119), the thing lag readings can't do | Bars; class-wide variant with network markers | Kendall trend test against phase surrogates; test on many events, not one | **Disk warns:** 2607.27070: crash signatures differ from event to event, across seven perp cascades. Snippet: 2604.21297 on network markers |
| P9 | **Information flow between related markets** (transfer entropy, lead-lag). COMEX to gold CFD, futures to index CFD, BTC to alts | Which market leads now, not just historically. A borrowed reading with a stated dependency (P4-b) | Two feeds; asynchronous | Surrogate p-values, per snippet 2206.10173; shift the source by placebo lags | COMEX leads gold (`MIS-PAGE-CONTENT.md` section 3 item 8). Snippets: 1906.10388, 2206.10173. QR12 still open after costs |
| P10 | **Mini and micro residue.** Same underlying, two contract sizes: the gap between their mids, their depth and their fill costs | His M50 belief that inefficiencies exist across sizes (`H1` gap 2). Cost per R differs by contract anyway | Two futures feeds; **futures have no route in this build** (G7 4.1 via H1), so recorded data first | Compare with the gap between two random samples of one contract's quotes at the same times; residue must exceed tick noise and fees | Mine; nothing on disk studies this. Honest prior: any gap is likely under one tick and closed fast, but cost-per-risk differences are real facts worth having |
| P11 | **Level gravity.** Does price behave differently near round numbers, prior-day high and low, session extremes? | Human traders read this (M50). `session-running-high` blocks exist | Bars or ticks | **Placebo grid:** move the levels by a random offset and repeat. The clean null of this list | Memory (Osler, stop clusters at round numbers). On-disk "round number" hits are unrelated |
| P12 | **Scalpability and tick constraint.** Bar range over spread; share of time the spread sits at one tick | "Is there enough movement to pay for trading?", plain and history-free. Sets which markets suit a scalper. Tick-size tiers (H1 idea 49) | Quotes | Mostly arithmetic. Use floor applies; no statistical claim to null | Mine. Fact-based, low risk, likely first to earn a place |
| P13 | **Species survey.** Tiny fixed scout logics in shadow on each market: which is paying here now, after real costs | Direct answer to "is mean reversion paying here today". No proxy statistic. Could feed the finder | Paper fills at the node's quotes | Random-entry scout with the same hold and cost. Skill is the gap between them | B103, B104, B049 ideas; none run. Feedback risk when units crowd (B094). Paper costs flatter (X0 P6c) |
| P14 | **Disorder and compression.** Permutation entropy (block exists with a card) with a complexity measure beside it | Noise against structure, per day | Bars | Surrogates with the same distribution | A3-188: "mostly negative results", 23714 against a random null. Keep the null beside it always |
| P15 | **Trend age hazard.** Chance a move reverses, by how long it has run | State age and taper (B118, H1 idea 45) | Bars | Random walk with same volatility; shuffle of move lengths | Snippet: 2006.07847, 30 years of data. A3-061 to 065 |

**Where I'd start.** P12 and P3: cheap and useful even if the physics disappoints. Then P1 and P4. P2 has the most appeal and the most warnings. The rest stay on the shelf until a unit asks.

**Old quarry.** Chaos and Ising readings from the old sentinel get cards and the same floors (B102, B123). Whether their code still runs is UNKNOWN; I didn't open it.

---

## 8. What the unit baseline must carry

By the round's test: left out now, the core gets reworked later. Values are absent on purpose. "Status" is what the tip does.

| # | The unit or host must carry | Why here | Status at tip | If missing |
|---|---|---|---|---|
| 1 | `reads` compiled, with fallback and stale limit | Every MIS idea | Model has it; compiler refuses | No reading reaches a unit, except by embedding a block |
| 2 | **Publisher** on a read | MIS-2, mini apps | Absent from `Read` | Rework every unit document later |
| 3 | Record `source` open; `valid_until`; inputs named | MIS-2, agents | Enum of two | Departments can't publish |
| 4 | **Allowed, home, active** | His router | One `markets` list | Widening stays a new version each time |
| 5 | Board or list fallback is home markets, not all listed | Hazard in section 5 | Fails open to all (`runtime.py:367-369`) | A dead MIS turns on a wide unit's whole universe |
| 6 | An **entry-gate slot** with a verb list, per unit | All SQS designs | `guard` has no spread check (`SWAP-CHART` E7) | SQS gets hard-wired, the old shape he objected to |
| 7 | Gate receives the facts: market, side, quote, stop, unit's cost allowance, cost cells | SQS-2 | `check(market)` only; stop known later in `_entry` | Per-trade cost check can't exist |
| 8 | **Cost input** to the sizer; commission key; per instrument, hour, venue, world | M51, SQS-2, SQS-4 | Sizer has none (H1 idea 11) | Size blind to cost |
| 9 | Named **size modifier** socket: reading, range, reason on receipt | SQS-4, windows, his reasons to reduce | Absent | Back to hidden multipliers |
| 10 | **Node-side sensor** for spread, tick rate, gaps, with source `node` | SQS, MIS-4 | Nothing. `sqs_baseline_producer.py` must move before C-20 (`G12:220`, `:425`) | C-20 deletes the only gate, and the sensor has no home |
| 11 | **One curve artifact** read by SQS, node, MIS, QMB; per world; age word; flagged borrowed cold start | MIS-4 | Three spread measures | They drift; first entry waits |
| 12 | **Sticker** record: scope, kind, strength, expiry, why, who; `unknown` as a state | Section 4 | Stand-down table with instrument scopes | All or nothing; rigid news rule |
| 13 | **Tolerations** per unit, pod overridable | ORB, news units, M49 | Absent | One rule for every style at opens and news |
| 14 | Scope keys: class, region, currency, underlying, session | Isolation, news | Two instrument keys | "It can isolate crypto" can't be said |
| 15 | Exits bypass every gate and sticker, by contract test | Fixed line | Exits unchecked in old gate; close path never blocked (`runtime.py:1277`) | The one thing everyone ruled out |
| 16 | `sessions` compiled, with **window cards** readable | Windows, ORB per open | Compiler refuses | Windows can't bind |
| 17 | Instrument record: book-or-quote flag, underlying, bucket, driver tags, tick tier, calendars, roll, commission | Venue rule, news tags, futures, mini and micro | Partly (H1 section 4) | Order-flow logic on a CFD; CPI stickers "USD" only |
| 18 | Trade row: session, slice, cost cell, gross and net, split costs, readings seen with source, age and version, markout, newly-active mark, gate verdicts | Windows, MIS lift, router | Largely absent (`SWAP-CHART` row 29) | Nothing can be proved or scored |
| 19 | **Would-have rows** for entries refused by any gate or sticker | Blocked winners (`chat-27:142`) | `would_have` not written (`SWAP-CHART` row 29) | Gates can't be judged; handbrake stays hidden |
| 20 | Records split by unit, market, session, slice | Router, windows, ORB per open | Per market only | "A sniping window gets more money because the record shows" has no record |
| 21 | Family tag and same-bet key | ORB family, router herding | Bet key planned | Five opens count as five bets |
| 22 | As-of question shared by QMB and live, with backfill flagged | Honest tests | Stamped records exist; query doesn't, UNKNOWN beyond that | Backtest flatters the MIS |
| 23 | Bars with full range, volume or tick count, time of day; event time as a clock | Volatility, RVOL, news units, P1 | MIS feeds closes; RVOL blocked (A3-077) | Fastest readings stay out |
| 24 | Declared **fail mode** per input and per gate | "Unknown is not calm" (H1 idea 24) | Partly | A stale feed reads as calm |
| 25 | A door for typed, scoped, expiring **de-risk cards** with evidence | Agents, 200 units, M49 | Tighten-only cards exist in a template (`SWAP-CHART` row 28), nothing applies them | He monitors by hand, which he rejected |
| 26 | Replay path through gates, stickers and reads | Scenarios, QMB parity | "No sizing-only or brake-path replay" (H1 idea 54) | SQS proven in live only |

**Template defaults worth carrying as presets [config], without values:**

| Preset | Gate | Tolerates | Reads | Routing rung |
|---|---|---|---|---|
| Scalper | Cost hurdle, floor | None | Fast against-usual, scalpability | 1 or 2 |
| ORB | Cost hurdle, floor per open | `open` | Open shortlist, activity at the open | 0 or 2, one family |
| Intraday | Cost hurdle, floor | Per pod | Session words | 0 or 2 |
| News | Cost hurdle, floor off or per pod | `news` | Event clock | 0 |
| Reckless | Off | All but the kill switch | None | 4 |

**Hand-offs (no action here):**
- **Repair session:** rows 5 and 10 touch files it owns; the claim list before C-20 must include the SQS producer and rule (`funnel/FUNNEL.md:212`).
- **Methodology:** how much proof a market, window or reading needs; what a newly active market must show; rules for trying many readings.
- **Agents:** workflows behind section 6; rule 4 there.
- **Numbers talk:** allowances, floors, strengths, probation sizes, whether gold's windows hold.
- **UI:** MIS tab, market card, sticker display, why-didn't-it-trade.
- **Pods and mini apps:** `round-2/expand/E2-pods-miniapps.md` should check the contract in section 6 and tolerations as pod settings; I didn't read E2, which was being written.

**Not verified.**
- No run of anything; the "my reading, not run" rows above are code reading only.
- Cost of per-card clocks at scale: UNKNOWN.
- The Kubernetes analogy and P-row "Memory" tags: my memory.
- "Snippet" papers: search abstracts only.
- R19's spread rows: chart only.
- A3 rows 1-30 and 146-180 and full chat-26 turns 1-2 not read row by row; `R2` read in sections 1 and 3 and the short answer; `14-design-idea-studies.md` read to section 0 and its contents list; `23-mis-organisation.md` to section 4.
- His original request for these designs couldn't be found word for word (`review-2026-11-07/TIMELINE.md`, Appendix A).

---

## Appendix A. Brainstorm ideas (109, by technique, unranked)

Ids elsewhere in this file ("Appendix A idea n") count down the whole list.

**Assumption Reversal**
1. Flip "is the spread unusual?" to "does this trade still clear its cost?"
2. No baseline: cost in R from live quote, stop, commission
3. One sensor per instrument, one verb per unit
4. Verb list: block, shrink, wait, warn, shadow, none
5. Fillability bank: spread, tick rate, gaps, micro range, slippage
6. Effective spread and markout from own fills
7. One curve factory feeds SQS and MIS
8. Cold start from a borrowed curve, flagged borrowed
9. Patience verb: hold the intent briefly, enter if spread recovers and signal stands
10. Wide spread changes order type to resting (node takes market entries only today)
11. Spread recovery after a spike as a signal seed
12. Forward cost: price the exit from the curve at the expected exit hour
13. Dealer skew: ask or bid widening alone
14. Two venues quoted, routes pick the cheaper
15. SQS block counts published as a reading
16. Would-have row for every refused entry
17. Refused-share reading per unit; agent card when gates strangle it
18. Control gate firing at the same rate at random moments
19. Gate can't change size; only the sizer socket can, with a receipt
20. Same-minute curves where data allows, coarser where thin

**Reverse Brainstorming**
21. Meaning-flip replay before a version moves
22. Isolation is a stand-down row, never a board word
23. Dark runs in every record, stop-the-MIS test
24. Keep reading state between rounds
25. The card's clock sets its bar
26. Full bar port
27. Packs differ, empty rows visible
28. Words from own percentile, cuts as settings
29. As-of query only
30. Herding count by reading
31. Retire card for unread or duplicate readings
32. News records expire, de-risk only, provenance, one-item effect limit
33. Allowed and active lists, probation setting per newly active market
34. List locked at session open
35. One per cluster by unit rule, same-bet key
36. Three lists scored side by side
37. Fallback is home markets, not all allowed
38. Tick readings only where the feed lands
39. Clock fact reaches the app volume
40. Yesterday's curves usable with an age word

**Cross-Pollination**
41. Forecast and nowcast products, different issue times
42. NOTAM: typed expiring notice on a market scope
43. Taints and tolerations: stickers on scopes, units ignore some
44. Sticker strengths: prefer not, no new entries, flatten
45. Node affinity: preferred markets by reading words
46. Triage: vital signs always on, slow tests only when vitals look unusual
47. Markets you may like, explore slots on paper
48. Aftershock decay as a spread recovery clock
49. Yield management: a slice earns its size from its record
50. Readings as pinned packages, lockfile in the unit
51. Word plus outlook
52. Bee scouts: tiny shadow units sample and recruit
53. Ant pheromone: market score rises when units win, decays; no statistic
54. Immune matching: is today like this unit's good days?
55. Outlier ejection applied to markets
56. Feature flags: gates per pod without a new unit version
57. Correction is a new record linked to the old
58. Actuarial almanac per slot
59. Niches with no unit steer agents
60. No router: each unit applies a local rule to shared readings

**Trader and instrument lens**
61. ORB shortlist: which opens are in play today
62. Same window: caution for a scalper, opportunity for ORB
63. Opening-range quality: width against usual, gap, pre-open tick rate
64. One ORB family, a cost and activity cell per open
65. Scalpability: bar range over spread, no history
66. Tape speed: tick rate against usual
67. Level map published
68. Context sentence across tiers
69. Gold CFD reads COMEX, MIS holds the dependency
70. Mini and micro residue
71. Cost per risk across contract sizes
72. Instrument dossier mini app
73. Window card in the Library
74. Sniping lift: a proven slice raises size by name
75. News sticker from calendar plus driver tags
76. Pre-event liquidity state as first predictor
77. Re-entry on spreads and depth, not the clock
78. News units tolerate the news sticker
79. Velocity tell backstops the calendar
80. Is London active today, from participation
81. Handover re-runs the finder
82. Spread-to-stop check names what a stop width can trade

**Systems and developer lens**
83. Same-meaning test on shared words
84. Replay parity digit check per reading
85. Admission from the card: `lag_bars` against typical hold
86. Reading price tag
87. Publisher pin on a read
88. Three output forms on the record
89. New fallback: last good until an age limit
90. Active markets is itself a reading
91. Router as a workflow writing that reading
92. Curves as a fingerprinted Library artifact
93. Node starts from the curve artifact
94. Scope keys beyond instrument

**New physics**
95. Hawkes branching ratio on quote arrivals
96. Move per quote update against usual
97. Directional-change intrinsic time
98. Liquidity commonality
99. Class alignment (Ising-style)
100. Time irreversibility
101. Critical slowing
102. Transfer entropy lead-lag
103. Aftershock exponent on spread
104. Round-number and prior-level gravity
105. Species survey of scout logics
106. Tick constraint share
107. Complexity-entropy plane
108. Dynamical network markers
109. Reversal hazard by trend age

## Appendix B. The party's clashes that changed the design

Session mode, one mind voicing four people, so these are positions and not independent review. Clashes left open on purpose.

**Trader:** Your cost hurdle makes me smile, because it's how I actually think. I don't care if the spread is "unusual". I care if I'm paying a third of my stop to get in.

**Execution:** And you'll happily buy into a market where the quotes have frozen, because your stop's wide and the spread looks fine. Stale quote, tight spread, no fill. You need a floor.

**Quant:** Whichever floor you pick, show me blocked trades against a random gate at the same rate. Otherwise you've only proved that skipping trades feels nice.

*(So: SQS-2 plus SQS-1 floor, would-have rows, and a control gate.)*

**Systems:** Three spread measures in three places is the actual bug. I don't mind which rule wins, as long as there's one curve.

**Trader:** Curves are yesterday. On a shock day yesterday's "usual" is a joke.

**Systems:** Then the reading says "far from usual", which is the true thing to say. And if the factory dies you still have yesterday's.

**Quant:** Same-minute curves break on holidays and clock changes. Flag those days or your "unusual" alarm rings every Thanksgiving.

*(So: MIS-4, with an age word and calendar flags. Open: the trader still doesn't trust curves after a real shift.)*

**Trader:** The router is the reason I'd run any of this. Gold's reverting, go to gold.

**Quant:** By the time you've proved it's reverting on one-minute bars, four or five hours have gone. It's a morning list. Say it's a morning list.

**Trader:** Fine. A morning list is how I trade anyway.

**Systems:** Hold on. If the unit's market list goes wide and the board dies, line 369 says trade them all.

**Execution:** That's how you lose money with the system switched off.

*(So: home markets, list locked at session open.)*

**Systems:** Why are isolation, news and open windows three features? They're the same row.

**Trader:** Because my ORB wants the open and my scalper doesn't.

**Systems:** That's why it's a toleration on the unit, not a rule on the market.

**Quant:** And then I'll want to know who lifted the sticker and whether a loss followed.

*(So: stickers with an accuracy record.)*

**Quant:** Half your physics list is a random walk in a costume. Directional-change laws show up on simulated walks. Hawkes says near-critical partly because of how the feed is cut.

**Trader:** He invited it, and he wants a machine that can try things.

**Quant:** Fine, try them. With the null beside each one, and every try counted.

*(Open: whether any of it earns a place. Scalpability and commonality went first because they pay off even if the physics doesn't.)*
