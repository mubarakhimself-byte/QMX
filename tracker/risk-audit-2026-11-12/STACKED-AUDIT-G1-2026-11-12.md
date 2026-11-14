# Stacked audit G1, 12 November: rc-01, rc-02, rc-05, rc-03, rc-04, rc-06, rc-07, rc-08

This is a read-only intent audit of the first eight stacked rows, in stack order. Code was read only with `git show`, `git diff` and `git grep` against `C:/Users/Mubarak/Desktop/QMX`, at each row's parent..head from `ledger.tsv` and at the stack tip `8d0a9758`. Nothing was checked out, edited or run. Every row already has a CLEAN Claude Opus code re-review in `review/`, except rc-07's three known money blockers, which are fixed on rc-26's branch. So this audit is about intent, not code.

**How intent is weighed.** Only the owner's own words count as his intent. They come from user turns in the planning transcript `2928e6ee…jsonl` (cited as `L<line>`, timestamp) and from the verbatim registers `seeds/operator-words-*.md`, `seeds/SEEDS.md` and `round-2/SEEDS-2.md` (cited by register id, such as T-59, and his message number, such as M49). User turns that paste agent text are not his words. Everything in SPINE, PLAN, FIXES and OPEN, and every builder departure, is labelled **agent decision** and judged on its merits.

**What he said about this ground.** He spoke directly to only four things these rows build:
- Lots: "Lots, why lots? Why lots? Because remember, you're not trading one instrument." (L4365, 7 Nov 13:00, M49)
- The unit of risk: "Are we going to be risking a dollar value, percentage value? What's the unit of measure?" (T-61, M8)
- A fixed 0.5 %: "when a scalper, you set it solid at 0.5%, I don't think a minary version can agree together with that, a trend following" (T-43, M7)
- Exits: "closing a trade is never blocked" (T-102, M5)

Everything else here is an agent decision. He handed it over in so many words: "Just complete it and make sure it can work. And it's maintainable, please. From a developer's perspective" (L5073, 7 Nov 15:15, M52).

## Summary

| Stack # | Row | PR | What it does | Verdict | Findings |
|---|---|---|---|---|---|
| 1 | rc-01 | 353 | Honest contract tests, no hidden 0.5 % ceiling | FINDING | 1 low |
| 2 | rc-02 | 354 | Census bites, module notes, generated developer guide | OK | 0 |
| 3 | rc-05 | 355 | `Amount`, `Fact`, one currency-aware converter | OK | 0 |
| 4 | rc-03 | 356 | Logic half and risk half, one fingerprint each | FINDING | 1 low |
| 5 | rc-04 | 357 | G covers logic, his click covers risk, exits survive a size edit | FINDING, OWNER CALL | 1 medium |
| 6 | rc-06 | 358 | `@2` answers money, `price` call, size band | FINDING | 1 medium, 2 low |
| 7 | rc-07 | 359 | Exchange rate in both hosts, money converted at the seam | FINDING | 1 medium |
| 8 | rc-08 | 360 | One decision row before the send, `explain_size`, `replay_decision` | FINDING | 1 low |

There are 8 findings: **0 high, 3 medium and 5 low**. There is 1 OWNER CALL, and one cross-row note for whoever audits rc-16.

The rows do what he asked where he asked anything. Lots now exist in one function (rc-05 and rc-06). A sizer answers money at risk, a percentage of equity turned into dollars. The hidden 0.5 % ceiling is gone (rc-01). No close reads a rate, an account fact or a chain (rc-06, rc-07). None of the four medium or low gaps contradicts his words. Three of them are promises the plan made to him that the stacked code does not yet keep end to end.

## Per-row detail

### rc-01: make the contract tests honest (PR 353, `351e7521..62e9374f`)

1. **His words.** The row removes `_CEILING = 0.005`, a hidden 0.5 % per-trade ceiling that failed every real sizer. That is his T-43 in code: one fixed 0.5 % cannot serve a scalper and a trend follower alike. It also fits his frame for the $500 goal: "how we can achieve having a large risk per trade without having a bad week wiping out everything" (L4823, 7 Nov 14:47).
2. **Agent decisions.**
   - Six stdlib exits are de-enrolled as `_UNBUILT_EXITS`. This is sound: they were passing on evidence no host gives, and they stay guarded as `exit_not_built`.
   - Exit evidence is fed at the three real host sites, not one. This is sound.
   - A sizer must declare a parameter named `fraction`, or the contract refuses it. This one is a problem (finding 1).
3. **Intent reports.** No conflict.
4. **Later rows.** Finding 1.

**Finding 1 (low).** `qml/tests/test_socket_contracts.py:176-177` and `:202-203` at the tip: "declares no fraction, so the contract cannot bound its risk".
- Every sizer that is not a fixed fraction fails CI. That covers a fixed-dollar sizer, the spine's `horizon-floor-odds@1` and `money-at-stop@1`, and RC-45's `tail-budget@1` if Intent A's DESIGN CALL 11(b) is taken.
- This is an agent rule, and it narrows his "What if I want to change the way it is derived?" (T-47, M10).
- It is test-only and fails loudly, so it is low.
- **Smallest fix:** when a sizer declares no `fraction`, bound its answer by the size band's per-trade share of equity, instead of refusing it outright.

**Verdict: FINDING.**

### rc-02: census, module notes, developer guide (PR 354, `62e9374f..b8394267`)

1. **His words.** The generated `qml/EXTENDING.md`, with a `--check` that fails when it goes stale, answers "maintainable, please. From a developer's perspective, there are lots of things you were meant to add" (L5073, M52). It also answers "The reason we have QML is the same reason there is SDKs" (T-162, M50).
2. **Agent decisions.** The generator imports only `qml`, so the journal kinds are hand-listed. That is a sound trade, and stated.
3. **Intent reports.** No conflict. Intent B already carries the gap that a new host journal kind never fails `--check` (RC-48 fact 2). Its fix is a test that reads `qmf.data.journal_kinds.unit.SPECS`.
4. **Later rows.** Covered by Intent B's RC-48 text. The Opus lows (a tautological census proof, and a probe-less refusal that renders as a dash) are code-quality items already in `lows.md`.

**Verdict: OK.**

### rc-05: typed amount and one converter (PR 355, `b8394267..c5238a54`)

1. **His words.**
   - "Why lots? Because remember, you're not trading one instrument" (L4365, M49). Lots now live only in `to_quantity`. A rule speaks in money at risk, notional or quantity.
   - "What's the unit of measure?" (T-61, M8). The answer is money at risk in the account currency.
   - "Risk is fixed in R when the trade opens" (T-62, M5). Rounding goes down, and the leftover is kept as a real `residue_r`.
2. **Agent decisions.**
   - The rate is carried as an exact `Fraction`. This is right: a `Decimal` 1/150 would floor 1.50 lots to 1.49.
   - `rate_stale_s` is 60 s, a labelled placeholder under OPEN row 25.
   - An amount on a `tail_budget` basis skips by name. This is right: no distance is invented.
3. **Intent reports.** The `tail_budget` skip is the hook for Intent A's no-stop question (DESIGN CALL 11 and its finding that he never asked for a stopless unit). The skip is safe either way.
4. **Later rows.** None beyond rc-06's band (below).

**Verdict: OK.**

### rc-03: logic half and risk half (PR 356, `c5238a54..60b75519`)

1. **His words.** He said nothing directly on a two-part fingerprint. The nearest are:
   - "they're meant to just give me the units. I click and stuff, and, you know, I promote them to live trading" (L13, 3 Nov 10:46).
   - "some are self-configuring, others are user-configured" (T-48, M8).
   Splitting what trades from how big it trades is an agent decision (AD-2) that serves both quotes.
2. **Agent decisions.**
   - The catch-all "anything not named risk is logic" is the safe default. It is sound.
   - `RISK_FIELDS` is `sizer, modifiers, gates, halts, reads, tolerations, stages` (`qml/src/qml/unit/sections.py:33`). So `halts` (brakes) are risk. See the cross-row note: since rc-16, a brake can close trades.
   - `recipe` sits outside both halves (`:38`) as `RecipeRef(pod_id, …)` (`qml/src/qml/unit/model.py:542-545`). That writes the agent's pod-is-a-recipe split into schema format 5.
3. **Intent reports.**
   - **Conflict with Intent B D3 and its RC-53 note.** `tags` and `risk_locks` fall into logic by the catch-all (`model.py:601,604`). So retagging a fleet re-proves it, and Intent B recommends moving both into `RISK_FIELDS`.
   - **Tie to Intent B D2** (what a pod is). If he rules "pod is not a recipe", `RecipeRef.pod_id` is a schema rename. It is cheap today only because `recipe` is refused at compile.
   - Intent B's F1 (`sections.py:57` ignores `exit_set` reads) and F2 (`stage_values` ignored) are this row's code. Both are already carried to RC-58 and RC-56.
4. **Later rows.** RC-49 and RC-53 must move `tags` and `risk_locks` if he takes D3. RC-56 and RC-58 carry F1 and F2.

**Finding 1 (low).** `qml/src/qml/unit/sections.py:33-38` partitions `tags` and `risk_locks` as logic, against Intent B D3 and its RC-53 note.
- **Smallest fix:** add both to `RISK_FIELDS` in the row that lifts each (RC-49, RC-53), as Intent B words it. No change to this row.

**Verdict: FINDING.**

### rc-04: G covers logic, a click covers risk (PR 357, `60b75519..5e604d6c`)

1. **His words.** "I click and stuff, and, you know, I promote them to live trading" (L13). The deployment now names both halves, and the node refuses a G record for another logic half (`g_record_missing`). Held positions are keyed by the logic half, so a size edit no longer silences exits. That last part serves "closing a trade is never blocked" (T-102).
2. **Agent decisions.**
   - "A size edit will not cost a re-test" is the plan's promise (AD-3, agent).
   - `_g_record` asks for a report naming the logic half first, then falls back to the compiled half.
   - Exits accept either fingerprint.
   - The qmb conformance pin was moved. This is sound.
3. **Intent reports.** No conflict with paper, pods or the kill table. Intent B's D5 (paper twins on `MarketKey`) is a separate key.
4. **Later rows.** Finding 1 trips RC-54 ("one pod edit, one plan, one click" over up to 200 units), RC-55 (move risk in place) and RC-65 (re-test after a bump).

**Finding 1 (medium): "trust a click for risk" is not live end to end at the tip.**
- `qmx-agents/packages/qmx-host/src/qmx_host/promote.py:639-641` asks for a G record by the logic fingerprint.
- `qmx-agents/packages/qmx-host/src/qmx_host/host.py:2007` looks records up only by the field `compiled_fingerprint`.
- No writer puts a logic fingerprint on a test report: `qmx-agents/apps/qmb/qmb_tester.py:61` and `qmx-agents/apps/qmb/jobs/backtest.py:263` write `compiled_fp` only.
- PR 357 said RC-17 owns the writer. RC-17's plan test asks for "a G record … for the logic fingerprint" (PLAN.md:1265), but its built test reads by compiled fingerprint (`qmx-agents/apps/qmb/tests/test_practice_month.py:107-108`).
- So a size-only edit is a new version with a new compiled fingerprint. It finds no record and is refused `no_g_record`, and a fresh G run is required.
- The failure is in the safe direction, so it is not high. But the plan tells him size edits skip the re-test, and the pod rows are costed on that.
- **Smallest fix:** the G check writes `logic_fingerprint` on its test report (`qmb_tester.py:61`). `host.g_record` and `landing.g_record` then match on either field. That is about 10 lines and one test that promotes a size-edited version on an existing G record.

**OWNER CALL 1** sits on this row (below).

**Verdict: FINDING, OWNER CALL.**

### rc-06: the sizer answers money, `price`, size band (PR 358, `5e604d6c..5102506f`)

1. **His words.**
   - `fixed-fraction-at-stop@2` answers `Amount(money_at_risk, equity × fraction)`, so a percentage becomes dollars, and the converter alone speaks lots. That is T-61 and his "why lots" (L4365).
   - The exits pass reads no account fact, which a test pins as the literal empty set. That is T-102.
2. **Agent decisions.**
   - The `price` call sits in the shared handler, not twice in the node. This is sound.
   - Format stays 5. This is sound.
   - `@1` stays as an old row. This is sound.
   - Band and cap values: findings 1 and 3.
   - Skip codes: finding 2.
3. **Intent reports.**
   - `SizeBand` is the `AdmitPort` that Intent A DESIGN CALL 8 widens in place. That fits.
   - The band and cap are exactly the "veto off switch" rows of Intent A DESIGN CALL 1, which recommends node settings.
   - On paper: the `ACCOUNT_CURRENCY` docstring treats "the paper lane" and "the demo account" as two things. That matches Intent A's finding that the plan's paper is not his paper. It is not a code conflict.
4. **Later rows.** RC-41 (off switches and codes), RC-27 and G-DEMO (account currency), RC-61 and RC-62 (skip counts).

**Finding 1 (low).** `qml/src/qml/protocol/unit.py:150-157` at the tip.
- `SIZE_BAND_MAX_LOTS = 100` and `PER_TRADE_CAP_SHARE = 1` are documented as "the `size_band_max_lots` setting" and "the `per_trade_cap_share` setting". They are `Final` constants, and no setting reaches them.
- At share 1, one entry may risk the whole account, so the per-trade cap only catches a bug.
- The lot band is one number across all instruments: 100 lots of gold is about 100 times 100 lots of EURUSD in money. That is the same one-instrument thinking his "why lots" challenged.
- Neither value is on `PARKED-FOR-NUMBERS-TALK.md`. He parked numbers himself ("we shall talk about numbers when we are done building", N-01), and said "risk per trade is going to be very configurable" (T-51, M5). So these are his numbers to set, and they must be on the list.
- **Smallest fix:**
  - Add both to `PARKED-FOR-NUMBERS-TALK.md` beside "8% against 1% per trade".
  - Make them node settings rows in RC-41, per Intent A DESIGN CALL 1.
  - Reword the docstrings to "starting default, not yet a setting".

**Finding 2 (low).** `qmb/src/qmb/results/journal.py:79` maps every `sizer: ` text to `sizer_skip`.
- That one code covers `size_band`, `per_trade_cap`, `rate_stale` and `rate_absent`, besides the real sizer skips.
- So a dead rate feed or a size veto counts as a sizer skip in any tally. His words are "We need to be able to know what is breaking" (T-93, M8).
- The specific word survives only in the row detail.
- **Smallest fix:** in RC-41's reason-list work, give `size_band` and `per_trade_cap` their own codes, and map `rate_stale` and `rate_absent` to the existing `feed_stale` and `reading_absent`.

**Finding 3 (medium): the account currency is hard-coded USD on both hosts, and no row owns it.**
- `qml/src/qml/protocol/unit.py:145-149` says "RC-07 brings each host's real account currency … and this default goes".
- RC-07 deferred it to RC-27 (PR 359 departures). At the tip the node still builds every `LiveAccount` with `currency=ACCOUNT_CURRENCY` (`qmn/src/qmn/app/runtime.py:2688`), and the rate supply uses the same default (`:3326`). The docstring at `:2669-2670` says "G-DEMO reads it from the demo account".
- No PLAN section or BACKLOG line owns reading the deposit asset, and nothing refuses a non-USD account.
- His words make USD the right default: "a total seed of 500 USD" (SEEDS.md:371). But if the bound account were in another currency, every size would be off by that rate, silently. A JPY account would be off about 150 times.
- **Smallest fix:**
  - At account bind, read the deposit asset.
  - Refuse to deploy, by name, when it is not `ACCOUNT_CURRENCY`.
  - Own this in RC-67, the first G-DEMO row, and add a BACKLOG line now.
  - Correct the stale docstring.

**Verdict: FINDING.**

### rc-07: exchange rate to both hosts (PR 359, `5102506f..524aec99`)

1. **His words.**
   - "trade 24/7, trade any instrument" (L4795, 7 Nov 14:32).
   - "multiple instruments lens is also key" (L1710, 3 Nov 12:20).
   - The close path reads no rate and copies the entry's stamp. That is T-102.
   Inside the code, a USDJPY unit now risks dollars.
2. **Agent decisions.**
   - One formula serves both hosts. This is sound.
   - A conversion market is subscribed but never driven. This is sound.
   - The trade row's `rate` stamp is deferred to rc-08, which did it.
   - The account currency is deferred to RC-27. See rc-06 finding 3.
   - A cross the unit does not trade cannot be subscribed, because `ConversionRef` has no symbol. This was backlogged.
3. **Intent reports.** One later trip: Intent A DESIGN CALL 3(b) gives the node a cash port for commission. Every node cash event it adds must convert at the seam, which is exactly rc-07's blocker 1 (replay cash summed unconverted). The rc-26 money fix has to cover the node's new cash too, or it reopens there.
4. **Later rows.** Finding 1, plus the landing order of the rc-26 fix.

**Finding 1 (medium): the row's own "You see" ("A unit trading USDJPY now risks what it says in dollars") cannot be reached by him, and no row owns closing the gap.**
- No shipped record quotes anything but USD (`qml/src/qml/numbers/shipped_records.json`: `eurusd` and `gold`, both USD).
- The Library's instrument kind has `additionalProperties: false` and no `conversions` key (`qmx-agents/packages/qmx-library/src/qmx_library/kinds/instrument.schema.json:10`; BACKLOG line 64). So a JPY market he adds can never convert, and every entry skips `rate_absent`.
- On the node, a conversion market the unit does not trade cannot be subscribed (`qml/src/qml/numbers/records.py:46-55`, no symbol; `qmn/src/qmn/app/runtime.py:3385-3387`; BACKLOG line 18).
- This is safe today: it refuses rather than mis-sizes. That is also why the three known money blockers are latent.
- But the day either gap is closed, those blockers become reachable, unless rc-26's fix has landed. STACK-LIST already says "Land rc-07 knowing the fix arrives with rc-26", and rc-26 is still in flight with Intent A DESIGN CALL 2 open.
- **Smallest fix:**
  - Name one row (RC-39, or a small row before it) to add `conversions` to the Library instrument kind and a symbol to `ConversionRef`.
  - Make that row depend on rc-26's "Money fix from the rc-07 re-review" commit.

**Verdict: FINDING.**

### rc-08: one decision row before every send (PR 360, `524aec99..81b90ecd`)

1. **His words.**
   - "We need to be able to know what is breaking." (T-93, M8)
   - "how do we know that this is wrong, this is right, it's working, it's up, it's on" (T-186, M12)
   - "we always have some sort of ledger to keep variables" (T-184, M12)
   `explain_size` and `replay_decision` answer "why this size" from one stored row.
2. **Agent decisions.**
   - The row is written at the decision, not at the fill. This is sound, and it closes a real hole.
   - `replay_decision` re-runs the converter, not the sizer block. This is a stated departure, defensible because a row cannot load the Library.
   - The tape is a constant, over USD markets only. This is stated.
   - I checked the Opus low 10 claim, that a refused row write still lets the send go. On the node, `Runtime.guard` refuses an entry once `journal.write_failure` is set (`qmn/src/qmn/app/runtime.py:3097-3098`, reading `qmb/src/qmb/results/journal.py:276`). So the "row before send" promise holds there for entries. Not a finding.
3. **Intent reports.** It matches Intent A DESIGN CALL 6(a): verdicts stay text in the `"<link>: <verb> (<code>)"` grammar that rc-08 set.
4. **Later rows.** Finding 1.

**Finding 1 (low): a refused fill now reads as `taken`, and the readers that later rows build on miss it.**
- A host-refused fill keeps `taken` on its signal row, and the refusal moves to a `guard` row (`qmb/src/qmb/results/journal.py:389-397` at rc-08).
- The agents' journal digest reads only `signal` and `trade` (`qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py:67`). So it reports refused entries as taken and loses the reason.
- RC-61 (apps read journals) and RC-62 (fleet watch) will inherit this unless they read `guard` rows. This is the Opus low 8, raised here because it goes against T-93.
- **Smallest fix:** add `guard` to `CONTEXT_KINDS`. RC-61's brief should name it.

**Verdict: FINDING.**

## Cross-row note, outside these eight rows

rc-03 puts `halts` in the risk half (`sections.py:33`). rc-16 (STACK-LIST row 17) then lets a brake close its own trades. Together, a brake edit that adds a closing brake reaches held positions on his click alone, with no behaviour check. That holds once rc-04's finding is fixed. Until then a fresh G run is still required.

On 7 Nov he was asked "May a rule close positions by itself, or only stop new entries?" (agent question Q1b at L4215, whose recommended answer was "Entries only at go-live"). He answered: "You are saying may a rule close position by itself? I think no. … If you look at the dictionary has closing mechanisms." (L4365, 7 Nov 13:00, M49). Whoever audits rc-16 should weigh this. It also shapes OWNER CALL 1.

## OWNER CALLs, in plain English

1. **Does a risk-only change go live on your click alone? (rc-04, with rc-03)**
   - **The plan's promise.** When you change only how much a unit risks, it moves on your one click, without re-running the behaviour check. The check proved when the unit trades, and that did not change.
   - **What the code does today.** It still demands a fresh check for every change, because the check's record does not yet carry the "trading logic" stamp the click looks for. The fix is about 10 lines.
   - **The catch.** In this design, brakes count as "risk" too. Since rc-16 a brake can close your open trades, and on 7 Nov you said a rule should not close a position by itself.
   - **Recommended:** your click alone for size and size modifiers. Any change that can close a trade, meaning a brake with a close or flatten action, re-runs the check first.
   - **Your choice:** take that split, or "my click alone for all risk changes", or "always re-run the check".
