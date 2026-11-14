# Stacked audit G3, 12 November: rc-14 to rc-20 (stop point A)

Read-only second-family review (Claude Opus) of seven rows that DeepSeek built and reviewed. Code was read with `git show` and `git diff` on parent..head. Probes ran in a detached copy at `baf7c9fa` (rc-20 head, which holds all seven rows), at `D:/Temp/stacked-g3`, each under a time limit. The copy was removed afterwards. Nothing in any worktree or branch was edited.

Owner intent is quoted from user turns in the planning transcript (`2928e6ee...jsonl`, grepped, never read whole) and from `seeds/SEEDS.md`. Everything in SPINE, FUNNEL, PLAN and the PR bodies is labelled **agent decision**.

## Summary

| Row | PR | Head | Verdict | One line |
|---|---|---|---|---|
| rc-14 | 368 | `4e9d0f57` | FINDING (medium) | Only a `restore` row lowers the fold's word. Nothing writes one for his resume, and none is journaled, so a resumed brake reads BENCHED for good, including after a restart. |
| rc-15 | 370 | `550e1aa6` | FINDING (medium) | One `risk_event` row per brake for the handler's whole life. A second fire after a release writes nothing (proved). |
| rc-16 | 371 | `14065fc6` | FINDING (high), FINDING (medium), OWNER CALL | A `flatten` brake never refuses entries, so the unit keeps opening trades while the fold says HALTED (proved). A `reduce` factor of 2 doubles size (proved). He said a rule should not close positions. |
| rc-17 | 372 | `d4f8855d` | OK (lows) | The canary and the shipped month work. The shipped records lose their `source: shipped` label on `main`. |
| rc-18 | 373 | `69af00e7` | FINDING (medium), OWNER CALL | The G record, now the only evidence for draft to paper, is read from any ref, an agent's own included (proved at the store). A never-judged unit can reach live on two of his clicks. |
| rc-19 | 374 | `0f63ef1b` | OWNER CALL (plus a low) | K7 ends on the fake broker, whose account is landed as world `demo`. Practice has no production binding, and "paper" is not his demo. |
| rc-20 | 375 | `baf7c9fa` | FINDING (low) | The line he is asked to sign claims more than the shortfalls section allows. Two other sentences in the note are false. |

**Counts:** 7 rows. OK: 1. FINDING: 5 rows, made of 1 high, 5 medium and 7 low. OWNER CALL: 3.

**Stop A's claim does not hold as written.** The claim: "One unit trades on paper from zero, with no broker and no judge". It holds only inside a test rig:
- K7 (`qmx-host/tests/k7_rehearsal.py`) ends on `FakeCTrader`, whose account is landed as world `demo`.
- The practice venue cannot land in the Library, because the account kind takes only `demo` or `live`.
- No production code binds the practice venue. The node binds only through the cTrader door.
- By his own definition, paper is demo trading (D14, M7). No demo account is involved anywhere.

The note's shortfalls section says the first two of these honestly. The sentence he signs does not.

## Per-row detail

### rc-14: read every brake's state from one fold

**Code.**
- `qml/fold.py` is pure. It imports only `qmf.core` and `qmf.risk`, so the blast-radius fact holds.
- The rank guard is correct: a weaker fire cannot clear a stronger word. DeepSeek's fix round proved it.
- **Finding (medium): only a `restore` row lowers a word, and nothing produces one for his resume.**
  - At `qml/src/qml/protocol/unit.py:1247-1256` (rc-20 head), the runner adds `restore` rows only for rule rows.
  - Every compiled row is `hand`, because a document cannot state `restore` (PR 371, "What this leaves out").
  - His resume (node `operations.py`) clears the stand-down but writes no fold row.
  - `Runtime._risk_rows` (`qmn/src/qmn/app/runtime.py:3267`) rebuilds only from `risk_event` rows.
  - Result: after his resume, `risk_state()` and the cached snapshot read BENCHED forever, and a restart rebuilds BENCHED.
  - Today nothing gates on the fold. Its only reader is the snapshot-write check (`runtime.py:3332`). So the harm is a wrong word, not a wrong trade.
  - The plan rows that read the fold later will inherit the false BENCHED: RC-22's cushion, RC-50 group, RC-62 fleet watch, and the copilot's `risk_state(scope)`.
  - DeepSeek's rc-16 review saw half of this as low 3 ("Unreachable while no document can state restore"). It is reachable today through the hand row, which is every row.
  - **Smallest fix:** when his resume clears a `RISK_STOP`, write a `restore` row for that deployment's unit scope into the unit journal, and have `_risk_rows` read `restore` rows too.
- Low: `_risk_rows` dates rows by the journal line's `t` (`runtime.py:3310`), while the unit dates its own rows by bar instant. Across a practice replay that restarts from an earlier bar, the fold's `(at, id)` cursor skips new fires. This is cosmetic while nothing gates on the fold.

**Intent.**
- No owner words on the fold itself. The five words come from SPINE AD-12 and AD-18 (agent decision).
- The fold is sound in design. The defect is that his hand is the one thing that cannot lower it.

### rc-15: write risk events and would-have rows in both hosts

**Code.**
- **Finding (medium): one `risk_event` per brake row for the handler's lifetime.**
  - `qmb/src/qmb/host/unit_handler.py:519` dedupes on `risk:{scope}.{row}` in `_noted`, which is never cleared.
  - Proved by a probe that drives the shared handler with a fire at T0, a quiet T1 and a fire at T2: it gives `risk_event rows = 1`.
  - In a QMB month a session-loss brake that fires on ten days leaves one row. On the node, a brake that fires again after his resume, in the same process, leaves no card. The lifecycle stop row still lands.
  - `event_id` is `code:row` (`journal.py`, `_fire_body`), so every fire of a row is one "incident" forever.
  - The plan says "Every control that fires writes a `risk_event`". The docstring says "one per root cause, so a brake that holds for an hour lands one card". The code does neither for a second episode.
  - **Smallest fix:** clear `risk:{row}` from `_noted` when the row stops firing (no `fired` event this step), and put the first fire's instant into `event_id`.
- Low: the E501 over-long line at `qmb/tests/test_risk_event_rows.py:362` was added by this row. It is the QA static red that the rc-20 note says "belongs" to no slice.

**Intent.** Agent decision (AD-12, R4). It is fine on merit, apart from the defect above.

### rc-16: let a brake flatten, stop and send to paper

**Code.**
- **Finding (high): a `flatten` brake does not stop entries, so the brake releases at once while its word says HALTED.**
  - `refuses_entries` (`packages/qmf-risk/src/qmf/risk/controls.py:174`) is true only for `no_new_entries`.
  - `_Run.controls` (`qml/src/qml/protocol/unit.py:1226`) flattens, but `ControlRun.refusal_reason` stays None.
  - `OnFire.stand_down`, the spine's way to add a stop, is never executed anywhere.
  - Probe: a unit-scope `flatten` row firing two steps in a row gives `refusal_reason None` both steps, while `fold` answers `HALTED`.
  - Consequence: on any document with `verb: flatten`, the unit closes everything, then reopens on the next signal, and closes again on the next bar while the brake still fires. That churns spread and commission under a brake that says halted.
  - No shipped template carries a flatten row today (canary has no halts; the shipped halts default to `no_new_entries`). Any document may, though, since this row removed `verb_not_built`.
  - **Smallest fix:** make `refuses_entries` true for `FLATTEN` at entry scopes, or refuse `flatten` at compile until `on_fire.stand_down` runs.
- **Finding (medium): the `reduce` factor is not validated.**
  - `qml/src/qml/protocol/controls.py:168` takes the block's factor, and `unit.py:1230` multiplies by it.
  - Probe: `Halt(REDUCE, ..., Decimal("2"))` answers factor 2, so a "brake" doubles the next entry. A negative or zero factor reaches the converter.
  - DeepSeek logged this as low 6. It belongs higher because it is a size raise wearing a brake's name, the shape rc-14's fix round already closed for the fold.
  - **Smallest fix:** treat a factor outside (0, 1] as the row's `link_fault`.
- Low (latent): this row adds `Transition(STOPPED, PAPER, RISK_RULE)` with `clears=<stop>` (`machine.py:115`).
  - On restart, `stand_down.restored` treats any lifecycle row with `clears` as clearing the stop (`qmn/src/qmn/app/stand_down.py:372`).
  - So once anything produces that transition, a rule lifts a hand stop without his resume.
  - No producer exists yet. The release note nonetheless says a brake can "send a unit back to paper".
- Low: QMB attaches no stop port. In a backtest a hand row releases as soon as its block stops firing, while the node holds it until his resume. G and the judge therefore score a unit whose brakes self-release daily. That is agent decision `StopPort` docstring, and it is undisclosed to him.
- DeepSeek's other lows still stand: position-scope flatten acts unit-wide (low 5), and the stale `qmf-risk` docstring (low 8).

**Intent (owner's words).**
- 7 Nov 13:00 (M49), asked whether a rule may close a position by itself: "You are saying may a rule close position by itself? I think no. ... the unit already has QML. It has a dictionary. If you look at the dictionary has closing mechanisms."
- FUNNEL C5 marks this "dissolved". In its own words: "My reading, not his words: the old question meant a portfolio rule reducing positions ... that is a control verb `reduce` or `flatten`".
- So the flatten verb is an **agent decision that reinterprets his "no"**. The spine and this row built on that reinterpretation. Hand-row stop and `risk_stop` wiring match his "only the kill switch and the hand" ordering. Flatten does not.

**Conflicts with the intent reports.** None of A or B's items. The fixed YELLOW kill rule at `runtime.py` `guard` (Intent A, RC-41 fact 5) is untouched here.

### rc-17: ship the canary template and the records it needs

**Code.**
- OK. The canary compiles, and `ShippedStore` answers shipped records only where `main` holds no live record. DeepSeek's fix round proved both blockers closed.
- Low: `practice_start` drops `source` when it lands the shipped records on `main` under the real venue id `icmarkets-ctrader` (`practice_start.py` `NOT_ON_MAIN`).
  - When his cTrader binding later refreshes, `venue_records.land` keeps every key cTrader does not state (`{**fields, **record.facts}`), and nothing marks them QMX-invented.
  - Examples of such keys: `margin` 0.0333, leverage tier 30, `max_lot` 1000, calendar and zone.
  - DeepSeek low 6 names the label loss. The persistence after a broker merge is new here.
  - **Smallest fix:** a `note` or provenance field that the instrument kind holds.
- Low: `XAUUSD` ships with no `max_lot` and no `pip`. Check the absurd-size band's behaviour with no ceiling when RC-21+ lands.

**Intent.**
- "Canary (no brakes)" is an agent decision. He said "Brex first, accelerator second" (M8, C19).
- The template he would meet first has no brakes. The note does label it "not a unit to trade live".
- His "something ... anyone can use, right out of the box" (M49) supports a template. It does not support a brakeless one. Worth one line to him, but not an owner call.

### rc-18: let a draft reach paper on his click, with the safety half of G

**Code.**
- **Finding (medium): the G record is read from any ref, and it is now the only evidence a draft needs.**
  - `LanderLibrary.g_record` (`qmx-agents/packages/qmx-host/src/qmx_host/host.py:2007`) uses `store.with_field`, which returns objects on every ref.
  - Probe: `Store.put` as principal `agent:copilot` on `refs/agents/copilot/forged-g` accepts a `test-report` with `check: G`, `status: finished`, `safety.verdict: pass`.
  - `with_field` then finds it, and `get(operator, ...)` returns `{'verdict': 'pass'}`.
  - Before this row, a draft also needed the judge's DRAFT to TESTED move. Now this record is the whole evidence for DRAFT to PAPER, and the gate for every later move.
  - His click is still required, so no agent reaches money alone. The gate he relies on is forgeable, though.
  - Not proved: whether any model-facing tool exposes `put` of a `test-report`. `library_merge` is an agent row, and `may_advance` lets `agent` merge into `main`.
  - **Smallest fix:** have `g_record` read only `test-report` heads on `main`, or on `refs/runs/<run>` written by a `run` principal.
- Low: `test_no_agent_money_door.py` is a name match over catalog rows (DeepSeek low 1). Agent rows `apps_admin_stop`, `apps_admin_restart`, `apps_admin_rollback` (the trading node is an app) and `library_merge` pass it by name. Signing guards publish and rollback; stop and restart are not covered by the K5 list.
- The fold gate (`machine.py` `_refusal`) checks only that `evidence_ref is not None`. Promote enforces the real record, so this is fine at this row.

**Intent.**
- Supported by M49 (7 Nov 13:00): "Those are like four different types of units. All of them can trade. No one is refusing them."
- In tension with D18 (M8): "the multiple workflows that are being taken into consideration before a bot even reaches demo, not even live, but bloody demo trading", and with D15: "the first few months... that's paper trading."
- The table now allows DRAFT to PAPER by click and PAPER to LIVE by click (`machine.py:109,111`). A unit that never met the judge reaches a live lane on two clicks with placeholders ticked.
- The plan states this outright: AD-24, "PAPER -> LIVE stays his click" (agent decision). He has never been asked.

### rc-19: reach a first filled paper entry from zero, on a practice venue

**Code.**
- The practice binding (`qmn/app/practice.py`) has no socket. Every unit and order row carries `world: paper` and `venue_kind: practice`. DeepSeek proved both.
- Low: K7 lands the fake broker's account as `Stated(..., "demo", "demo")` (`k7_rehearsal.py:233`), so its run stamp reads `real_tick_share: "1"` for replayed fake prices. The PR body rejects exactly that falsehood for practice.
  - **Smallest fix:** have `_run_stamp` read the venue kind rather than the world, or state the K7 stamp as a known false field.

**Intent.**
- The PR took the plan's fallback, honestly stated: no Library account world `paper`, and no production binding.
- This sits squarely on Intent A RC-39 fact 3. His words: "paper trading is simply demo trading... paper bloody trading is demo trading" (M7, D14). The planned meaning of "paper", a practice replay or the node's virtual-fill lane, is an agent decision.

### rc-20: ready stop point A for his signature

**Code.**
- Version bumps and digests are fine. The sweep's test-literal moves were rerun by DeepSeek. The two baseline reds are named.
- Findings (low):
  1. `tools/lanes/release_note_stop_a.md:7`, the line to sign, says "One unit trades on paper from zero, with no broker". Lines 25-26 say K7 ends on the fake broker and the practice venue "is a rehearsal lane, not a shipped door". **Fix:** "One unit reaches a filled entry from zero in a rehearsal on a fake broker; a stranger cannot do this yet."
  2. `:19` says "a brake can ... send a unit back to paper". No producer exists, only a lifecycle table row. **Fix:** delete those words.
  3. `:49` says "Neither red belongs to this slice". The E501 red is rc-15's own test file. **Fix:** wrap the line, or say it is rc-15's.
  4. `evidence/rc-20/sweep.log` (2,327 lines) is committed into the product tree that lands on `main`. Clutter, by his branching rule.
- DeepSeek's low 2 is still true: the gate's blast-radius fact greps a test-only name.

**Intent.** Stop points are an agent decision he never ruled on (Intent B, last section). The signature covers the node folder, not QML (the note says so).

## What a later row will trip over

- rc-14 and rc-16: any row that reads the fold, or an agent's `risk_state`, reads BENCHED after his resume. That covers RC-22, RC-50, RC-57, RC-62 and RC-47's copilot doors.
- rc-15: RC-22's cushion ledger and RC-29's account brakes read `risk_event` history. They undercount repeat fires.
- rc-16: RC-36's `flatten` sticker is spec'd to run through the control runner's `flatten` verb (SPINE AD-16). It inherits "closes but keeps trading".
- rc-16: the first producer of STOPPED to PAPER by a rule (Intent B's restore rules, RC-51 restart rules) lifts hand stops on restart through `stand_down.py:372`.
- rc-18: RC-54's `MarketKey` change and RC-65's re-test both lean on `g_record`. The ref leak spreads with them.
- rc-19: RC-39's "every template reaches paper" (Intent A fact 3) inherits the fake-broker and demo-world stamp.

## OWNER CALLs

1. **A brake that closes your trades (rc-16).** On 7 Nov you were asked whether a rule may close a position by itself, and you said "I think no ... the dictionary has closing mechanisms." The planning agent reread that as "a brake may flatten", and rc-16 built it: a brake can now close every open trade of a unit. Should a brake be allowed to close trades? Or should brakes only stop new trades, and leave closing to the unit's own exits?
2. **Never-judged units reaching live (rc-18).** With rc-18, a unit that never passed the judge can go draft to paper on one click, then paper to live on a second click, as long as a safety check passed. You said QMB's workflows run "before a bot even reaches demo". Should moving to live require the judge's pass, or is your two clicks enough?
3. **What "paper" means at stop A (rc-19, rc-20).** You said paper trading is demo trading. Stop A's "trades on paper" is a test rehearsal on a fake broker. No demo account is used, and a newcomer cannot run it yet. Should stop A wait until a unit fills on your cTrader demo account, or be signed as "a rehearsal fill" with the demo check after you connect?
