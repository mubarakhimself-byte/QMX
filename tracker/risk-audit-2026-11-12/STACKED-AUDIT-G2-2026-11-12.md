# Stacked audit G2, 12 November: rc-09, rc-27, rc-10, rc-11, rc-12, rc-13

Read-only second-family (Claude Opus) code review and intent check of six DeepSeek-built rows, in stack order. Code was read with `git show` and `git diff` at each row's head and parent from `ledger.tsv`. Tests and probes ran in one detached copy, `D:/Temp/stacked-g2` (`git worktree add --detach`, its own `uv sync --frozen`, nothing sourced from another store, every run under `timeout`). The copy was removed with `git worktree remove` at the end. The probe scripts are in this session's scratchpad: `C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\probe_a_stop_through_step.py` to `probe_e_timer_make_raises.py`.

**Whose intent.** Only the owner's own words count as his intent, quoted from the verbatim registers `tracker/risk-core/seeds/operator-words-*.md`. Everything in PLAN, SPINE and the PR departures is labelled **agent decision** and judged on merit. On these six rows he said little and handed most of it over. On 6 Nov: "Size, exits, halts. I don't know, man. Okay, handle this" (`operator-words-2026-11-06.md:78`). Also on 6 Nov: "Breaks and accelerators. Seriously, how it configures itself. I don't think I have any opinion. I'm going to leave that part to you" (`:60`). The owner words that bear directly on these rows:

- 1 Nov: "Closing a trade is never blocked" (`operator-words-2026-11-01.md:56`). He said it while going through the agent's list and did not object to it.
- 1 Nov, on compounding: "it sizes from the current balance each time" (`:50`).
- 1 Nov, on drawdown: "the BMS doesn't allow the floor to be touched. So we give a buffer" (`:106`).
- 1 Nov: "The kill switch has survived multiple versions" (`:56`).

## Summary

Counts: 6 rows. **3 high findings, 7 medium, 9 low, 1 OWNER CALL.** No row is OK outright. Every row reaches its own named tests (all green at their heads in the copy: rc-27 2, rc-10 3, rc-11 4, rc-12 5, rc-13 5, rc-09 3). The defects sit in paths those tests do not drive.

| Row | PR | Verdict | Worst item |
|---|---|---|---|
| rc-09 | 362 | FINDING medium | A raising logic slot freezes the stop exit's instance, so the stop sent when entries return can be 66 pips off. The gate's fact script cannot fail. |
| rc-27 | 361 | FINDING medium (x2) | QMB's half of the account surface is never wired, and the row turned the conformance-tape test red. Sizing still does not read the live balance. |
| rc-10 | 363 | **FINDING high** + medium | An exit the unit minted, in a step the host then dropped, is lost for good, and the close-scope fall-through never fires for a host-phase fault. The fall-through asks once and never retries. |
| rc-11 | 364 | **FINDING high** | An exit block whose `make` raises takes every exit of the position, every bar, with no fall-through. |
| rc-12 | 365 | FINDING medium | A moved `stop_buffer` reaches the swing-stop's update but never the stop the entry is sent with. |
| rc-13 | 367 | **FINDING high** + medium + OWNER CALL | A brake whose block raises refuses entries for one step and is then gone for the rest of the run, so it fails open. |

### High findings, one line each

1. **rc-10**, `qml/src/qml/protocol/unit.py:1219` (`m.exited.add`) with `qmn/src/qmn/app/runtime.py:3301-3325` (`_drive`, `_unit_fault`). If the host raises after the unit mints an exit and before it sends it, the exit is lost for good, and close-scope is never asked. Proven at rc-10, rc-11 and the tip `8d0a9758`.
2. **rc-11**, `qml/src/qml/protocol/unit.py:1223` (`self.unit.timer(position.side)` outside the per-exit `try`). A per-bar exit whose `make` raises makes every step raise: 30 of 30 steps, zero close-scope asks, at rc-11 and the tip.
3. **rc-13**, `qml/src/qml/protocol/controls.py:123` and `:147`. A brake row that raises is skipped from then on, and `stood_down` carries only this step's new scopes. Entries resume after one step: a broken losing-day brake let 20 entries through where a working one let 0, at rc-13 and the tip.

## Per-row detail

### rc-09, "Keep a raising block from reaching the exits in its own unit" (75db7cbf, parent 81b90ecd)

**What it does.** It guards update, entries, motion and price with a plain `try`. A raise becomes a `Fault`, and the unit's entries are benched until `fault_clean_bars` (8, a placeholder) clean bars have passed. The `risk_event` kind is added, with no writer yet.

**1. Code.**

- **FINDING medium: the stop exit loses every faulted bar.** At `qml/src/qml/protocol/unit.py:1014-1034`, `_Run.update` computes both sides' logic first and feeds the STOP exit instances afterwards. A logic raise leaves `update` before the stop feed, so the swing stop never sees a faulted bar. The same order survives at the tip (`:1665-1675`). This is the fact the row is safe because of: "exit blocks hold their own instances, so a broken logic block can't corrupt them". I ran it through the real step (`probe_a`): 50 raising bars of `long.trend` on the one-market dummy, faulted against clean. On the bar entries return, the long swing stop reads 1.08702 faulted against 1.08044 clean, about 66 pips tighter. That means a larger lot count on the same risk share and a venue stop the clean strategy would not place. Money at risk stays inside the risk fraction, which is why this is medium and not high.
  - The committed fact script `evidence/rc-09/fact_exits_hold_own_instances.py` never calls `on_instant`. It calls the broken block directly and then feeds both exit instances by hand, so it only proves that they are two objects. It cannot fail on the wiring.
  - The earlier Opus review (`review/rc-09-opus-75db7cbf.md`, blocker 1) found the same.
  - Smallest fix: feed the STOP exits before the `sides = {...}` line, which uses the same evidence, and keep `probe_a`'s through-the-step comparison as a test.
- Low: the bench, its clean count, `fault_clean_bars`, `exit_faults` and `close_asked` are not in the snapshot. The builder disclosed this.
- Low: the "range one to 96 bars" on `FAULT_CLEAN_BARS` is not enforced. The door takes any value of 0 or more.
- Low: a motion fault books after that bar's entries have been proposed.
- Low: a benched bar writes no decision row, so "why didn't it trade" has only the earlier fault row to point to.
- Correction to the Opus review's blocker 2 (lint): this is not a gate red. The canonical gate, `ruff check` and `ruff format --check` over `packages extensions qml qmb qmn tools`, prints "All checks passed!" and "823 files already formatted" at `8d0a9758`. Only a single-file ruff run flags the test file.

**2. Intent.** "Closing a trade is never blocked" (1 Nov) is served for the guarded phases. Agent decisions: the bench is unit-wide, the 8-bar placeholder, and a price fault surfacing on the next answer. All are reasonable. The stop-freeze above goes against the row's own stated fact (agent).

**3. Conflicts.** None with the intent reports.

**4. Later rows.** RC-11's exit wall is built on this bench (see rc-10 and rc-11). The stop-freeze is still in the code at the tip.

### rc-27, "Give the node a live account surface" (a37eeb12, parent 75db7cbf)

**What it does.** It adds seven `account.*` facts plus a `basis` sentence in `qmf-risk`, a timed venue balance re-read on the node (`LiveAccount`, `CTraderVenue.read_balance`), a QMB `ReplayAccount`, and stamps the facts onto every node decision row.

**1. Code.**

- **FINDING medium: QMB's half is never wired, and the row went red on the conformance tape.**
  - `ReplayAccount` (`qmb/src/qmb/host/facts.py:89`) has no product caller at this head or at the tip. Only the test uses it. The plan's "QMB supplies the same names from replay" is not done.
  - Because only the node stamps `account.*` into `DecisionRow.inputs` (`qmn/src/qmn/app/runtime.py:1578`), `qmn/tests/test_conformance_tape.py::test_k9_1_and_13_same_trail_in_both_hosts` goes red. I ran it: green at the parent `75db7cbf` (3 passed), red at `a37eeb12` (1 failed, `:259`).
  - The red rode rc-10 and rc-11, both reviewed CLEAN. Lane 1's `-k app` and `test_app_runtime.py` do not collect that file.
  - rc-12 then narrowed the test to drop `account.*` from the comparison, which blesses the asymmetry instead of supplying QMB's names.
  - Smallest fix: wire `ReplayAccount.read` into the QMB handler's row stamp, so both hosts' rows carry the same keys, and restore the whole-row comparison. Also add the conformance-tape file to lane 1 for qmn rows.
- **FINDING medium (against his words): sizing does not read the live balance.** He said "it sizes from the current balance each time" (1 Nov).
  - The handler sizes on its start equity plus only its own closed trades (`qmb/src/qmb/host/unit_handler.py:427-449`). The start equity is `client.equity()` read once at start or restore (`runtime.py:1738`).
  - So between restarts, a unit never sees the other units' losses on the same account. With many units on one account, sizing reads a balance higher than the real one.
  - The PR defers this as departure 1, and DeepSeek filed it as a low. Its owners are RC-28 and RC-29, and rc-29 is parked.
  - Smallest fix, in whichever row moves the sizer: size from `account.equity` (the timed re-read) plus the open-risk basis, not from the per-handler start.
- Low: `_took` (`qmn/src/qmn/venue/ctrader_account.py:732`) turns a trader answer with no `balance` into a balance of 0 and reports it fresh. It should refuse and keep the last read.
- Low: `money_at_stake` (`packages/qmf-risk/src/qmf/risk/facts.py:125`) uses `abs(entry - stop)`, so a stop trailed past entry counts locked profit as open risk. That overstates risk, which errs on the safe side.
- Low: `_refresh_accounts` (`runtime.py:2492`) runs unguarded in `tick()` after `_drive`. A raise there heals the whole node. It runs after the exits are sent, so it cannot block one.
- Proven safe fact: the timed re-read runs at one point, after `_drive` (`runtime.py:2486`), never inside the pass, so no exit waits on a balance round trip. The named tests pass (2 passed).

**2. Intent.** The read-only venue call adds no new path from an agent to money. The status document gains `runtime.accounts`, which is read-only. Agent decisions: equity equals balance with no open P&L marked (said in `basis`), and `budget_share` is one node constant of 1, not each deployment's own share. Both are honest placeholders. The miss is the sizing point above.

**3. Conflicts.**

- Paper: the `basis` honestly names "the fake conformance double". By his definition ("paper trading is simply demo trading", 1 Nov), nothing in this row trades on paper until G-DEMO.
- Margin and liquidation read absent. This matches intent A's DESIGN CALL 9.

**4. Later rows.** rc-26 (in flight) seeds the unit's realised trades into the handler at restart. On a real venue the restart's start equity is the venue balance, which already contains those trades' money, so realised money would be counted twice: undersizing after losses, oversizing after wins. The conformance fake hides this because its `equity()` never moves. rc-26's reviewer should test a restart whose fake balance moves with the closed trades.

### rc-10, "Keep one unit's fault from stopping any other unit" (776ba8e2, parent a37eeb12)

**What it does.**

- `_drive` holds one `try` per unit. A raise or a `close_frontier` refusal becomes a host fault: entries are benched, one `risk_event` is filed per root, and the phase stays TRADING.
- The per-bar exit gets a wall, and after `exit_fault_bars` (3) bars with no exit able to run, the unit asks `HostPort.close_scope`.
- Stale reds fixed: a `promote.py` line length, the dictionary size pins, and the blocked `signal` row.

**1. Code.**

- **FINDING high: an exit the unit minted, in a step the host then dropped, is lost for good, and the fall-through never fires.**
  - The unit marks a position exited when it mints the close (`qml/src/qml/protocol/unit.py:1219`). If the host then drops the step, by a raise in pricing, in a journal write or in the send, the node's new wall files a host fault and steps the unit again. From then on `exited` holds the position, so no exit re-mints. `exit_faults` is popped, so `no_exit_ran` never counts and close-scope is never asked.
  - The node shows TRADING, and the position keeps only its venue stop and target. `exited` is also written to the snapshot, so a restart does not recover the exit.
  - Proven with `probe_b`, a held long with a five-bar time exit whose bar-4 step is dropped. The exit is minted and dropped at bar 4, never minted again over 40 bars, and close-scope is asked 0 times. Same result at rc-10, rc-11 `2324d349` and the tip `8d0a9758`.
  - This has already happened once: STACK-LIST records the rc-06 plus rc-21 malformed sizer answer that "dropped that step's exits". rc-28's fix catches that one sizer path only.
  - Smallest fix, either one:
    - In `_Run.exits`, count bars a position stays held after it was marked exited, and after `exit_fault_bars` re-mint the close, or ask `close_scope`.
    - In `Runtime._unit_fault`, count consecutive host faults per deployment with a held position, and call `close_scope` at `exit_fault_bars`.
  - Either one also covers the rc-11 high.
- **FINDING medium: the fall-through asks once and never retries.** `no_exit_ran` adds the position to `close_asked` before it calls the port (`unit.py:1236-1248`). `_ScopeClose.close_scope` discards how many positions closed (`runtime.py:1605`). `OrderPath.close` expects to be asked again and raises its `close_refused` alarm only on the Nth refusal, so one venue refusal means no retry and no alarm. This survives at the tip (`unit.py:1868-1880`). Smallest fix: let the port answer whether it closed, and add to `close_asked` only on success, or keep a standing close for the deployment scope until it is flat.
- Low: `fault_roots` is never cleared, and the root key for a host raise is `host:<ExceptionType>`, so every later RuntimeError of any cause in that deployment files no new card.
- Low: before this row, a deterministic `close_frontier` refusal turned the unit STOPPED, which is visible. Now it reads TRADING with "a fault: ..." in the detail, while the unit does nothing.
- Proven safe fact: one unit's raise no longer stops the next unit. The named tests pass (3 passed). The K9-2 drive counts are as claimed, and DeepSeek reran the fact.

**2. Intent.** "Closing a trade is never blocked" (1 Nov). The high finding is a quiet block on the unit's own exits. Agent decisions:

- `EXIT_FAULT_BARS` of 3, a placeholder.
- `close_scope` closes every position of the deployment, every market, when one position's exits fail. That is broad but defensible.
- A host fault benches entries.

**3. Conflicts.** None. `_unit_fault` raises no kill level, so the kill switch stays the only thing that escalates. That fits his "the kill switch has survived multiple versions".

**4. Later rows.** RC-42 (two passes, exits first) should send exits before any pricing and mark `exited` only after the send. That removes most of the dropped-step window. RC-67 and RC-68 must keep the partial and amend answers inside the same wall.

### rc-11, "Run every exit each bar, side-correct, with reasons and a fixed order" (2324d349, parent 776ba8e2)

**What it does.**

- An `ExitStack` per held position runs every per-bar exit on the closing side's bar.
- `PositionFacts` holds the position's facts. Exits answer typed actions, full beats partial beats amend, and a raising exit is skipped for the next one.
- Compiler format 5 to 6, and the conformance pack is remade.

**1. Code.**

- **FINDING high: a per-bar exit whose `make` raises blocks every exit of that position, every bar, with no fall-through.**
  - `_Run.exits` builds the whole stack through `self.unit.timer(position.side)` (`qml/src/qml/protocol/unit.py:1223`), outside the per-exit `try`. A raise leaves `on_instant` on every bar where the position is held.
  - The node's rc-10 wall files it as a host fault and keeps the phase TRADING. `no_exit_ran` is never reached, so close-scope is never asked.
  - `probe_e`: 30 of 30 steps raised, 0 close-scope asks, at rc-11 and at the tip.
  - DeepSeek filed this as low 6. It is the same silent exit block as the rc-10 high, made wider by the stack: one bad block takes every exit.
  - Smallest fix: build each slot in its own `try`, file `Fault(pin, EXIT)` and count the bar for `no_exit_ran`. The rc-10 `_unit_fault` counter also covers it.
- Low (from DeepSeek's lows; I confirm them by reading):
  - `PositionFacts.evidence` returns `facts | params`, so an exit parameter named `stop`, `side`, `series` or `clock` overwrites the fact.
  - `stage` is advertised in the facts and never supplied.
  - A chosen partial or amend leaves no row.
- Proven safe fact: "a second per-bar exit never changes a unit with one exit". DeepSeek's second review reran it with a held position, and the three bodies are equal. The short-side ask-bar fix is right (`test_a_short_reads_ask_bars`, 1.1002). The import test bites on a planted `fold` import. Named tests: 4 passed.

**2. Intent.** He did not rule on exit order. "Exits... handle this" (6 Nov). Agent decisions:

- Full beats partial beats amend: sound.
- Partials and amends answer but do nothing until RC-67 and RC-68: disclosed.
- A bare `Signal` keeps the old `time-exit` code: fine.
- The format bump: justified.

His own exit idea for scalpers ("first invalidation", M15) is not built here, and nothing here works against it.

**3. Conflicts.** None. The exit path imports no chain, fold or reading.

**4. Later rows.** RC-68 has to replace `test_six_exits_on_one_unit_are_each_run_or_named` (intent B). Exit blocks that read `stop` or `targets` get `None` on the node, which answers only `OwnPosition` until a row widens it.

### rc-12, "Make the shipped exit blocks read numbers from evidence" (4fa9a8df, parent 2324d349)

**What it does.** It adds `swing-stop-buffer@2`, `target-r-multiple@2` and `time-exit-bars@2`, which read their number from evidence, and points the dummy at them. It also closed rc-27's conformance-tape red by narrowing the test.

**1. Code.**

- **FINDING medium: a moved stop number never reaches the stop the entry is sent with.**
  - The entry reads the stop with empty evidence: `_answered(stop_plan.binding.pin, ..., {})` (`qml/src/qml/protocol/unit.py:1358-1368`, tip `:1950-1960`). So `swing-stop-buffer@2` falls back to its `make` seed. The moved `buffer` reaches only the update call, whose answer is thrown away.
  - The target, by contrast, is passed `self.unit.params(...)` and does move.
  - `probe_d`, with the long side's in-force `stop_buffer` set to 0.005: the entry stop sent is 1.09391, which is the seed's 1.093911. The moved stop would be 1.08866. Same at rc-12 and the tip.
  - Nothing ships a moving `stop_buffer` today, because the dummy's is `fixed`. That is why it is not high. But it is the defect this row exists to fix, and a tracked (rc-25) or derived `stop_buffer` would put one level on the receipt and send another to the venue.
  - The row's tests are block-level, so they cannot see it.
  - Smallest fix: pass `self.unit.params(stop_plan.binding, numbers)` as the stop's evidence at entry, and add a unit-level test that moves the buffer.
- Low: the conformance-tape fix narrows the test, which hides rc-27's missing QMB half (see rc-27).
- Proven safe fact: no shipped file binds the old versions besides records of past heads. DeepSeek's grep is in `evidence/rc-12/owner-fact.log`. Named tests: 5 passed.

**2. Intent.** This is agent work under "a learned number can reach an exit". He gave no ruling. The time exit's new reason word `time` is fine, and no product reader matches the old `time-exit` text.

**3. Conflicts.** None.

**4. Later rows.** rc-33 seeds per-market `stop_buffer` through `make` (`settled(market)`), so its literals are safe. Any row that moves `stop_buffer` at run time (rc-25's tracked numbers, or a derivation) will hit the finding above.

### rc-13, "Make a brake a control row that runs in the unit" (abbdd6f5, parent 4fa9a8df)

**What it does.**

- `halts` rows gain `verb` and `shadow`. A runner feeds each row its declared facts, and the unit's own statistics (`own.session_loss_r`, `loss_streak`, `losing_day_streak`, `session_fills`) are computed in QML.
- A fired live row refuses entries with "halt slot: ...". A raising row writes `link_fault`.
- Compiler format 6 to 7.

**1. Code.**

- **FINDING high: a brake whose block raises fails open after one step.**
  - `Runner.run` puts the raising row in `_down` and skips it on every later step (`qml/src/qml/protocol/controls.py:123`).
  - `ControlRun.stood_down` holds only the scopes stood down in this step (`:147`), and `refusal_reason` reads only that (`:96`). So entries are refused on the step of the raise and allowed from the next one, with the brake gone for the rest of the run.
  - The fault does not bench the unit either (departure 7).
  - `probe_c`: a live `losing-days-halt` after a losing day, every long slot holding. With the brake working, 0 entries. With the brake raising, 1 `link_fault` at step 0 and then 20 entries. Same at the tip `8d0a9758`, and no host reacts to `link_fault`.
  - The row's own words ("stands that row's scope down") and AD-9 (agent) both mean the scope stays down.
  - Smallest fix: `refusal_reason` reads the runner's persistent `_down_scopes`. Keep a separate new-only list for the risk-event row.
- **FINDING medium: a shipped halt declared `flatten` runs as `no_new_entries`, with no word said.**
  - `ControlBinding.verb` defaults to `no_new_entries` (`qml/src/qml/unit/model.py:404`, tip `:417`), and all five shipped halts' blocks answer `flatten` (PR departure 5).
  - That default made sense while flatten had no executor. rc-16 has since built flatten, and the default still overrides what the block declares at the tip.
  - A daily-loss brake meant to flatten only stops new entries.
  - This is an agent decision. He left brakes to the agents.
  - Smallest fix: default the verb from the block's `Halt.action` now that RC-16 runs it, or have the compiler print the downgrade on the receipt.
- Low: `own.session_fills` counts trades closed today (`controls.py:176`), not fills. A fill limit misses entries still open and counts yesterday's entries closed today.
- Low: `"halt slot: ..."` is not in QMB's `_REASON_WORDS`, so a suppressed row lands with no code. A `suppressed` row needs none, so nothing breaks.
- Proven safe fact: the five shipped halts bind with their `entry.json` untouched. DeepSeek ran it at the head. Named tests: 5 passed. No exit is reached by a brake: `test_a_raising_row_stops_no_exit` holds.

**2. Intent.** He handed brakes over: "Breaks and accelerators... I'm going to leave that part to you" (6 Nov). These rest on agent decisions:

- A cold row warns and skips. See the OWNER CALL.
- The session is the UTC day until RC-33.
- Brakes are unit-scope statistics.
- The verb default, above.

His only brake words are about the account floor: "the BMS doesn't allow the floor to be touched. So we give a buffer" (1 Nov). Drawdown "was meant to be set at a percentage value", not cash. The account daily-loss halt binds here but cannot fire: no host supplies `account.day_start_equity`, and rc-29, which would, is parked.

**3. Conflicts.**

- Gross against net (intent A findings 2 and 3): `own_facts` reads `ClosedTrade.r_after_costs`, which holds gross R. So every brake here, labelled "R after costs", presses on gross. On the node that stays gross after rc-28 (intent A DESIGN CALL 3).
- Kill switch: `OnFire.raise_kill` is data only, so brakes never touch the YELLOW rule at `runtime.py`.

**4. Later rows.**

- RC-14's fold reads `stood_down` per step, so it will see a raised brake for one bar only until the high finding is fixed.
- On the node, `own_journal` is the handler's in-memory closed list, so a restart resets every unit brake's statistics until rc-26 seeds them.
- The equity-drawdown halt forgets its base on restart (disclosed).

## OWNER CALLs

1. **(rc-13) A brake that cannot read its number: stop trading, or keep trading?** Today the account daily-loss brake has no "balance at the start of the day" to read, and won't until the parked rc-29 lands. A unit that names it keeps opening trades and logs one "cold" warning. Do you want a unit to stop opening new trades until each of its brakes can read what it needs? Or keep trading and just warn, which is what is built? You said the daily floor must never be touched.

The other big question that touches these rows is already waiting for you: whether rc-29 may take a third small fix (`QUESTIONS-FOR-OPERATOR.md`).

## What was run

- At `75db7cbf`: `qml/tests/test_fault_wall_unit.py`, 3 passed.
- `probe_a` (stop through the real step): stop state diverges, 1.08702 against 1.08044 when entries return.
- `qmn/tests/test_conformance_tape.py`: 3 passed at `75db7cbf`; 1 failed, 2 passed at `a37eeb12`.
- Named tests at each head:
  - `test_app_account_facts`: 2 passed.
  - `test_app_fault_wall`: 3 passed.
  - `test_exit_stack` and `test_exit_imports`: 4 passed.
  - `test_exit_blocks_v2`: 5 passed.
  - `test_control_rows`: 5 passed.
- `probe_b` (dropped exit step): exit lost for good and 0 close-scope asks, at `776ba8e2`, `2324d349` and `8d0a9758`.
- `probe_c` (raising brake): 0 entries working, 20 entries raising, at `abbdd6f5` and `8d0a9758`.
- `probe_d` (moved stop buffer): entry stop 1.09391, the seed, against 1.08866 moved, at `4fa9a8df` and `8d0a9758`.
- `probe_e` (exit `make` raises): 30 of 30 steps raise, 0 close-scope asks, at `2324d349` and `8d0a9758`.
- Root `ruff check` and `ruff format --check` over the gate paths at `8d0a9758`: both clean.
