# Last independent check of the fold

7 Nov 2026. Checked `SPINE.md`, `SOLUTION.md`, `WALKS.md` and `OPEN.md` in full against `D:\QMX-worktrees\bld-repair-24` at `351e7521`. Lenses: adversarial, edge-case, verification-gap, structure, plus blast radius. Code paths below are relative to that worktree. The worktree is unchanged (`git status` shows 0 lines). All running was in a throw-away copy under `D:\Temp`, removed afterwards.

## Verdict

**The shape is sound, and it is not ready for builders as written.** There are 9 blockers. Each has a small fix, and most are a few lines of spine text. None needs a different architecture or a question to him. Three of them break a fixed line or put money at risk: a faulty block stops exits, an entry goes out twice, and a size is wrong by currency. Two more mean the walk he asked for most, from zero to a trading unit, doesn't reach paper today.

No fix touches the fork he still has to decide (a recipe or a governing pod).

## How sure each result is

| Claim | Result | How far it got |
|---|---|---|
| One faulty logic block stops the other units' bar steps, so their exits don't run | True | **Ran** on the real `Runtime`, fake cTrader, 12 bars |
| A parked entry crossing a bar sends twice | True | **Ran** on the real order path, with AD-17's fix applied literally |
| A size in a JPY-quoted market is wrong | True | **Ran** the shipped sizer |
| A stopless entry survives once it passes AD-22's six places | **False** | **Ran** the real tick |
| A unit can go from draft to paper on his click | **False** | **Ran** the real lifecycle fold; judge gate read |
| A node can host a 1-minute and a 15-minute unit on one account | **False** | **Ran** the real `_host`, both ways |
| A long bell can't trip the 30 s watchdog (`WALKS.md` walk 8) | **False** | **Ran** the real path on a virtual clock: 26 s for one entry |
| A size-only edit changes the compiled fingerprint today (the fact AD-3 rests on) | True | **Ran** the real compiler |
| A number moves in the built engine | True for logic numbers | **Ran** |
| A sizing or exit number can reach the engine today | **False, by named refusal** | **Ran** |
| AD-14's widening is enough to change a size | **Not alone** | **Ran** on a patched scratch copy |
| `run_budgeted` answers a hang at about its budget | True, and it leaves a thread behind | **Ran** a toy, standard library only, not the real blocks |

## Blockers

### B1. One faulty block stops exits, in that unit and in every unit after it

- **Fixed line:** "Exits are never blocked."
- **Evidence:** I made one logic block raise on `dep-1`, with `dep-2` hosted behind it. Over 12 bars, `_drive_one` ran for `dep-1` 11 times and for `dep-2` **zero** times, with 11 heals. Both units still read `trading`. So `dep-2`'s per-bar exits and its node-closed targets (`runtime.py:1849-1857`) never run. Only stops resting at the venue protect it.
- **Why:** `_drive` has no guard per unit (`runtime.py:3013-3018`). The raise reaches `step()`, which heals and starts again from the first unit (`runtime.py:2193-2200`).
- **Inside one unit:** `_Run.step` runs logic blocks before exits (`unit.py:530-536`), so a raising logic block also ends that unit's own exits. "Pass 1" is the same call.
- **What the spine has:** AD-9 wraps chain links and control rows. It wraps the bar step "once tested", with no slice. AD-13 covers a raising exit block only. Walk 11 covers a hang, never a raise in a logic slot. K9 test 2 doesn't list this case.
- **Smallest fix, in slice 3:**
  - Put a plain `try` around each unit in `_drive`. A raise moves that unit to entries-off, writes a row, and the next unit runs.
  - In `_Run.step`, catch logic and entry faults so `exits()` still runs and its intents survive.
  - Add a faulty logic slot and a faulty sizer to K9 test 2.
  - No threads are needed for this.

### B2. A parked entry that crosses a bar sends twice

- **Evidence:** I implemented AD-17's fix as written, returning `Ok(False)` from `execute_resting`, and let pass 2 reach the queue late. The real order path sent 2 `ProtoOANewOrderReq` for one market. The venue held 2 positions and the handler held 1. The second position has no unit exits.
- **Why:** while an entry is parked, `own_position` reads `None`, so `_Run.entries` mints a new intent on the next signal (`unit.py:746-749`). This can't happen today, because placing is immediate. The fix creates it.
- **Also wrong:** "until its `not_before` expires". `not_before` is the bar's own time, an earliest time, and I confirmed it equals the frontier on the wire (`unit.py:832`). It never expires, so a parked entry has no lifetime at all.
- **Smallest fix:**
  - Add a parked entry to the facts `_Run.entries` reads, so the market reads as `suppressed_limit`.
  - Give it an explicit `expires_at`, the next bar of its market by default, labelled as a placeholder, then write `Skip` with `budget_expired`.
  - Add "no second mint while parked" to K9 test 11.

### B3. From zero, nothing reaches paper

- **Evidence:** a his-click `DRAFT -> PAPER` event comes back from the real `fold` as rejected, `not_in_table` (`qml/lifecycle/machine.py:106-108`). `TESTED` comes only from a judge verdict of `pass` (`qmx_host/lifecycle.py:39`). `too_thin` moves nothing, and the judge's default needs 100 trades (`qmx_judge/presets.py:45`).
- **Consequence:** `SPINE.md` section 6 goes from step 3 (backtest) to step 4 (promote click) with no judge step. Yet every card says "a shape, not an edge", so a pass is not what the template is for. K7 would fail at its first promote. His M49 is direct: "All of them can trade. No one is refusing them." He also rules out validity as this session's question, so this can't wait on the methodology session.
- **Smallest fix:** add one lifecycle row, `DRAFT -> PAPER` by his click, requiring a passing G safety record. Paper touches no money. `PAPER -> LIVE` stays his click. Name the row in slice 5 and in K7.

### B4. One account's feed builds one bar size, and the templates need several

- **Evidence:** with a 1-minute feed, the real `_host` refuses the m15 unit: "the unit reads m15 bars and this account's feed builds 1-minute bars". With a 15-minute feed it trades (`runtime.py:2774`). The default feed is 15 minutes (`ctrader_account.py:115`). Stream ids are market ids throughout the handler (`unit_handler.py:261`), and `_bars` is keyed by market and then time.
- **Consequence:** `scalper-mr` (1m and 5m) and `intraday-trend` (15m) can't both run on one account, and `scalper-mr` can't run on the default at all. Slice 9 says "Templates A and B compile"; they then refuse at the node. "Second stream" appears nowhere in section 3's contracts. Walk 2's "On 1m bars the cut acts once a minute" assumes a feed that isn't there.
- **Smallest fix:** write a slice 9 contract: the feed builds one base bar, each unit's streams roll up from it, and the handler keys by `(stream, market)`. Split the slice (see S9).

### B5. Size is wrong by currency, and the contract gives no way to fix it

- **Evidence, from the shipped sizer at 100,000 equity and 0.5 %:**

| Market | Quote currency | Loss at the stop | Intended |
|---|---|---|---|
| EURUSD | USD | 500 USD | 500 USD |
| XAUUSD | USD | 500 USD | 500 USD |
| USDJPY | JPY | **500 JPY** | 500 USD |

- **Why it stays open:** `to_quantity(amount, entry, stop_or_basis, record, rule)` has no rate input, and the record has no rate field (script over its fields: none). A cross such as EURJPY needs a market the unit doesn't trade, and `context_needs` arrives in slice 14. Slice 2 promises the "USDJPY fix", so two builders would solve it differently, and a stale rate has no stated behaviour.
- **Smallest fix:**
  - Add `rate: Fact` to `to_quantity`.
  - Add `conversion_market` to the record, subscribed by the host.
  - A stale or absent rate gives a named skip on entries. Exits never read it.
  - QMB reads the same fact from replay.

### B6. AD-21's diagram breaks a package rule

- **Evidence:** the diagram draws `qmf-data --> qml`. `tools/workspace_meta.py:72` allows `qml` only `qmf-core`, `qmf-registry` and `qmf-risk`, and `tools/tests/test_workspace_structure.py:138` asserts it. `DEPENDENCIES.md` says the same (DEC-0180). `qmf-data` also brings `pyarrow` and `duckdb`. Section 3 puts `DecisionRow` in `qmf-data`, while `HostedUnit` builds it in `qml` today (`unit.py:153`).
- **Smallest fix:** remove the arrow. Row shapes live in `qml` or `qmf-risk`. `fold` takes plain mappings. Hosts own journal kinds and reading.

### B7. Slice 4 depends on slice 6

- **Evidence:** slice 4 ends with "words from the fold" and "restart keeps a bench from rows". Slice 6 is where "fold at unit scope" lands. AD-12 makes the fold the only source of control words.
- **Smallest fix:** move `fold.py` at unit scope into slice 4.

### B8. AD-1 and AD-17 disagree on when the size is computed

- **Evidence:** AD-1 says `price` is called "right after `on_instant` on the same tick". Section 12 confirms that reading ("instead of right after"). AD-9, AD-17, section 3's comment ("pass 2") and the section 1 figure put the sizer in pass 2.
- **Consequence:** a builder following AD-1 sizes in pass 1, which brings account facts into the exit pass and sizes parked entries on stale facts.
- **Smallest fix:** make AD-1 say pass 2. Then section 12's slice 11 row (the "half a PR: move one call") is already done, so remove that cost from the switch price.

### B9. AD-22's "six places" is wrong; a stopless entry is still closed

- **Evidence:** I gave a held position the state a declared no-stop entry has (no stop at the venue, none on its send row). After one real tick it was closed, with `protection_escalation` raised. The closer is `_restore_stops` (`runtime.py:2358-2386`) calling `restore_stop` with `None`.
- **Further places, read and not run:**
  - `ctrader_account.py:1454-1456` rejects with `no-stop`.
  - `NodeUnit.adopt` reads `send["stop"]` (`runtime.py:1636`).
  - `reconciler.py:390` alarms on a held position with no stop.
  - `safe_to_restart` lists it (`runtime.py:2288-2289`).
  - `_money` and `_close` (`unit_handler.py:578, 669-673`) work out risk from the stop.
- **Consequence:** walk 2's verdict is FAILS as written, not STRAINS. UNKNOWN: whether cTrader accepts a no-stop market order at all.
- **Smallest fix:** list these places in AD-22. Make K9 test 12 "a stopless entry held for N bars on the fake broker, then through a restart". Add one demo probe (does the venue accept it?) to R24's list.

## Should-fix

| # | Finding | Evidence | Smallest fix |
|---|---|---|---|
| S1 | The time budget doesn't cover what takes the time | **Ran:** one entry on a venue answering at its 5 s wait with no stop shown takes **26 s** in one tick (4 sends, 3 confirm waits). A budget check then one entry can pass 30 s. Pass 1 has no budget: 6 closes at the 5 s wait use the whole 30 s, then `os._exit`. Stops at the venue hold through the restart. Walk 8's "cannot trip" is false | Start no entry unless elapsed plus worst case is under the limit. Reset `watch.began` as a progress beat between exits. Correct walk 8 |
| S2 | Core rows with no slice and no contract | Script over section 10: I17 feasibility, K5 protected list and channel isolation, R8 run stamp and arms, I7 `knows_at`, I9 provenance, claim and generation stamp. Section 4 says each "lands" | Name a slice for each, or mark it as additive with a reason |
| S3 | The placement test contradicts walk 3 | AD-9: a link reading the account goes in the node chain. Walk 3 has "the unit chain's own cap reads `account.open_risk_by_bet_key`" | Move walk 3's check to the node chain, or narrow the test |
| S4 | The partition has holes | Script: 9 `Unit` fields are in neither section (`baseline`, `claim_card`, `context_needs`, `family_id`, `lineage`, `plain_python`, `routes`, `title`, `unit_id`). `reads` is risk, yet walk 7 says a reading used by a logic slot is a logic edit. A risk-section `stages` selector can move exit numbers with no G run | Rule: anything not named as risk is logic. A `reads` row bound by a logic slot is logic. An exit's `stage_values` make the selector logic |
| S5 | "Once" against "on each changed decision" | AD-19 bumps only on a changed decision; section 3 and section 7 say 5 "once, in slice 1". Slice 3 changes decisions (side-correct time exit) with the fingerprint unchanged, so a G record goes stale silently | Say: free bumps until the first live deploy, one per changed decision |
| S6 | A test that can't be built | K9 test 13 runs a tape through four drivers. No Lab package exists, and no slice adds one | Three drivers now; Lab joins when it exists |
| S7 | "Only five things refuse" is false | Still refused: `routes`, `plain_python`, `roll`, a stop past entry, a recipe touching an exit (AD-4), a stop past liquidation (PH 14), and margin, order-rate and size-band vetoes with no stated off switch. AD-20 says everything else warns | Give each veto a row with an off switch, except what a venue can't do. Correct the sentence |
| S8 | "Paper on the fake broker on day one" isn't a product path | `ConformanceAccount` has no production builder (grep). Paper needs a bound venue and its live prices (`paper_lane.py:1-9`; `runtime.py:2763`). Release's G1 to G3 have no plan or owner | Ship a practice venue kind, or state plainly that day one ends at backtest. Give release an owner, since M49 asked for this directly |
| S9 | Slice 9 is two PRs for six things | Sessions, second stream, per-market settings, `position_limit`, roles and window card. `_held` is one per market (`unit_handler.py:286`), as is `open_positions.get(market)` (`runtime.py:1802`). No contract covers multi-position | Add the contract. Split into about 4 PRs |
| S10 | `_close_scope` is out of reach from QML | AD-13's last fall-through is node code; `qml` can't import it, and QMB has none | Add a `Fault` answer on the step, acted on by a host port |
| S11 | The module map puts node links in `qml` | `chain/node_chain.py` "links" would need `qmn` kill-effects and `qmn/order/protection.py`, which `qml` can't import | Runner and protocol in `qml`; node links injected from `qmn` |
| S12 | Self-configuration has three gaps | See "Does a number really move" below | Three rows there |
| S13 | Contract words diverge | Gate `block` against verdict `refuse`; `wait` undefined; sticker `flatten` has no executor; `logic_touch` has no stated handling; a stage-up `card` doesn't say what trades while it waits | One line each |
| S14 | A hung block leaves a burning thread | **Toy:** answered in 83 ms at a 50 ms budget, and the thread lives on. Main-thread work ran 3.8 times slower with 5 such threads. A healthy call cost 0.2 ms, about 128 ms per bar for 200 units at 3 rows each | After `link_hung`, mark the node for restart when flat, and reuse one pool |
| S15 | Short stops read bid bars | `unit.py:574-576` feeds bid bars to both sides, so a short's stop ignores the spread | Say which side's bars in AD-13 |
| S16 | The fleet watch isn't a mini app | His words: "As a mini app also" (M49). `fleet-fold` is an engine template | Package it through the mini-app manifest |
| S17 | His signature has no column | `SWAP` 2.2 says QML in the node's lock bumps the money app and needs his signature. Section 10 tracks demo sign-in only. UNKNOWN: I found no gate in `release_gate.py` or `build_release.py` | State one signed release per stop point |

## Can a builder build it?

- **File:line claims:** 44 distinct citations were extracted by script and read against the source, and all 44 point at what they claim. 8 further path and line claims also hold. So **52 of 52 hold on location.**
- **Where meaning failed, despite the right lines:** "six places" (B9), "cannot trip the watchdog" (S1), and the `qmf-data` arrow (B6).
- **Slice arithmetic:** PR counts add up (14, 29, 42, 44).
- **Order:** one hard forward dependency (B7). One soft: slice 4's account halts need slice 8's live account facts to mean anything across units.
- **Divergence:** B8, S3, S4, S5, S13.

## Coverage

Scripted where it could be.

| List | Landed | Did not land |
|---|---|---|
| SWAP placeholders, 31 | 31 of 31 in section 5 | None missing |
| SWAP sockets, E1 to E18 | 18 of 18 | None missing |
| FUNNEL section 3, 51 live rows | 51 of 51 named in section 4 | Named, no slice or contract: S2's list |
| Part C, H-01 to H-136 | 26 are named in the fold; the rest rely on one range statement in `SOLUTION.md` and on FUNNEL section 7's table, which has rows for the 11 I spot-checked | See below |
| FUNNEL 3.8 refusals | Blanket sentence | "A second deployment of one version" (`promote.py`) is placed on S14's deployment key, which section 4 strikes without a replacement, so paper twins lose their seat |

**Part C items that don't hold today:**
- H-01, H-06, H-08, H-17 and H-43: blocked by B3 and B4, and by S8.
- H-21 and H-33: B4 and S9.
- H-30 and H-31: B5.
- H-50: B1.
- H-98: S16.

**Named as "not held" by the fold and fair:** H-78, H-90, H-92, H-122. **Older list:** breakeven (16), System 1 (20), multiple Books (29) and N8N or white label (2) don't appear in the fold; FUNNEL section 7 places 16 as a block, off. I did not check the others on that table.

## His words, M49 to M56

| He asked | Delivered as designed? |
|---|---|
| "can actually trade" | Yes, after B1 to B4 |
| "size itself", "Why lots?" | Yes, after B5. The answer on lots is good |
| "can self-configure" | Mechanism yes. See below |
| "has a template" | Yes, after B4 |
| "Someone who hasn't been part of developing KMX can use tomorrow" | **Not yet:** B3, S8, and the release lane has no owner |
| "baseline with a customizability layer", "canvas" | Yes; stop point B is a real baseline |
| "it's maintainable" | Yes: one explain function, generated guide, census |
| "Why would I have to be there monitoring" | Yes for the script. Agents have doors only, by hand-off. S16 |
| "you're setting stuff in a rigid manner" | Mostly met. Rigid: a recipe can't touch an exit (a real cost, named in AD-4); compiled exit order; "cuts stand, raises wait" compiled in; the vetoes in S7 |
| "If the pod thing makes no sense, you can propose something new" (M56) | Yes: OPEN row 1 and section 12 are honest. Section 12's price changes slightly with B8 |
| "The UI is a proposal" (M55) | Yes; nothing binds |

**Could a reckless setup be expressed?** Yes for size, brakes and the kill line, on the design. No-stop can't be expressed until B9 is fixed, and the vetoes in S7 can still refuse it.

## Does a number really move?

Mechanism only, on synthetic trades; no gain claimed.

1. **A logic number moves at the tip.** `min_trend_strength` went from 0 to 0.0001 after 20 trades, through the real engine.
2. **No sizing or exit number can reach the engine at the tip.** `risk_fraction`, `stop_buffer`, `target_r` and `time_out_bars` each refuse with `motion_not_built`.
3. **On a scratch copy with AD-14's stamp widening, the number is compiled and does not move** until the trades carry a stamp for the sizer. `_stamps` reads logic slots, so `engine.py:122` skips every trade. AD-14's "may run with no logic stamp" names this.
4. **With a stamp, it moved** from 0.005 to 0.0049, and the moved value reached the sizer's evidence.
5. **The shipped sizer ignores it.** Evidence said 0.0049; the block used 0.005 from `make` (`block.py:24`). Section 5 covers this through the grown sizer. Slice 7's test must use an evidence-reading sizer, or it will prove nothing.

**Gaps for S12:**
- No shipped rule block is written for a risk number; the only one I ran is the trend-floor rule. Ship one, or slice 7 has nothing real to run.
- `flat` means all markets flat (`unit.py:543`), so a many-market scalper can starve its cadence.
- After a restart, `SlowState.read` is lost unless a value moved (`runtime.py:2926-2927`), and `own_journal` starts empty. Seed it from trade rows.

## The walks, again from zero

| Walk | `WALKS.md` says | My re-walk |
|---|---|---|
| 1 Zero to a filled paper entry | HOLDS | **FAILS** at the promote (B3), at bar size for anything but 15m (B4), and at the venue for a stranger (S8) |
| 2 Gold scalper, no stop | STRAINS | **FAILS** as written (B9), and needs a 1-minute feed (B4) |
| 3 ORB, one bet | HOLDS | Holds, with S3's contradiction to settle. Not run |
| 8 200 units | STRAINS less | Strains more than stated: S1. A compile pool in the same process also shares the interpreter lock with the node thread during a roll. Not measured |
| 9 Swap with an open trade | Sizer holds | Holds on read. Fact proven: a size-only edit moves today's fingerprint, so AD-3's split is what's needed |
| 11 Fault, hang, restart | HOLDS; hang strains | **FAILS** on a raising logic block (B1). Restart holds on read; tests owed, as it says |

## Too much machine

Each can go without losing anything he asked for.

- **The group `order` block** beyond a `rank` field. "Best of those firing" is nobody's ask yet. Keep the field and add the slot when content needs it.
- **Reservations as a type.** On one thread, a place answers at once. All that's needed is "an unknown outcome keeps its room".
- **Proposal tape.** It serves size search, which is methodology's. Hand it off with the row shape reserved.
- **The Lab driver** until a Lab exists (S6).
- **`run_budgeted` on every row.** B1's plain `try` handles raises, which are the common fault. Consider it only for Library links, or defer it with the worker process. This one needs a call from the lead, because FUNNEL S6 asks that a hung link refuse entries only.
- **`SOLUTION.md`'s "The pieces" section** repeats section 10 and section 3. Cut it to a pointer, or keep it only for his reading.

## Dollar reasoning

None decides anything. A grep of all four files finds only "5,000 lots" (a size fault), his own M51 words, "USD at the seam", and "it does not set a dollar value". E5's tables are cited as mechanism only.

## What I ran, read, and did not read

**Ran in the throw-away copy:** the rows marked "Ran" in the first table, the coverage scripts, and the citation script.

**Read, not run:**
- `unit.py`, and large parts of `runtime.py`, `unit_handler.py` and `promote.py`
- `engine.py`, `loop.py` in part, `healing.py` in part
- `workspace_meta.py`, `DEPENDENCIES.md` in part
- `paper_lane.py` header, `ctrader_account.py` in part, the cited line of `reconciler.py`
- M49 to M56, `SEEDS-2.md` Part C
- FUNNEL section 3 and 4, and section 7 by grep
- SWAP sections 1 and 2.1 to 2.4
- `.memlog.md` tail, `RUN.md` head

**Did not read:**
- `COMPARE.md`, except by grep; V1 to V4
- `harvest/H1` to `H5`, `E1` to `E4`; `E5` by grep only
- `QUESTIONS.md`, `UI-LOOK.md`, `TIMELINE.md`, `system-map.md`
- `operator-words-2026-11-03.md` and `2026-11-01.md`, which `BRIEF-COMMON.md` names; I used their lines as `SEEDS-2.md` quotes them
- FUNNEL sections 1, 2, 5, 6, 8
- SWAP after 2.5
- The repair plan's Call 11 text

**Not tested:** real cTrader, any 200-unit run, any full suite, and the customization resolver for `bmad-review`. I used the shipped lens list. The brief's blocker and should-fix split replaces that skill's rule of no ranking.
