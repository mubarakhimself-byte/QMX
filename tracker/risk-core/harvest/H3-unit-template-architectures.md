# H3: the template and the structure, and the three architecture versions

Harvest for the unit, QML and its dictionary, self-configuration, extensibility, pods, mini apps, the Lab, shipping new versions, schemas, external code, observability and DevOps, and maintainability. Opus, 7 Nov 2026. Read only; no new research. "RC" is `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. "LP" is `D:\QMX-worktrees\risk-plan\tracker\qma-v2\architecture\lab-and-pods\`. "W" is the code tip `D:\QMX-worktrees\bld-repair-24` (255f3bbf). "My read" and "seat / content / other session / drop" are my opinion. No policy is decided here. Figures quoted from sims are model numbers, reported only so you can find them.

## Contents

- Section 1: what I read
- Section 2: the versions of architecture he asked for and never saw
- Section 3: the ideas, best first (T1 to T71)
- Section 4: designs and overhauls proposed, including conflicts
- Section 5: what the unit baseline must carry
- Section 6: gaps, in his words

---

## 1. What's here

| File | Read |
|---|---|
| `RC\harvest\BRIEF.md`, `RC\architecture\ARENA-BRIEF.md`, `PICK.md`, `SYNTHESIS.md`, `CHECK.md` | in full |
| `RC\architecture\candidate-1\`, `candidate-2\`, `candidate-3\`, each `SPINE.md` and `RATIONALE.md` | in full. Sim outputs not read; figures come through the spines |
| `RC\architecture\SPINE.md` (the fold) | in full |
| `RC\architecture\PRESET-NUMBERS.md` | first 20 lines only |
| `RC\expansion\X1-template-shape.md` (78 hybrids), `X6-observability.md` (47 hybrids) | in full |
| `RC\research\R1-platforms-risk-sizing-extensibility.md`, `R7-software-patterns-self-configuring.md` | in full |
| `RC\grounding\G8-unit-chassis-and-extensibility.md` | in full |
| `LP\PLAIN-WORDS.md`, `LP\ARCHITECTURE-SPINE.md` | in full (AD-10 to AD-12 closely) |
| `LP\OPEN-DECISIONS.md` | OPEN-1 only |
| `RC\linking\components\A4-template-agents-telemetry.yaml` (203 components) | **Partly.** All 203 ids and names by script; 26 components in full where they add something beyond X1 or X6. The rest reach this file through X1, X6, R1 and R7, which cite them |
| `RC\seeds\operator-words-2026-11-06.md` M49 to M53; `operator-words-2026-11-03.md` lines 10, 13, 176, 194; pod sentences of `operator-words-2026-11-01.md`; `SEEDS.md` "What the technical lens must hold" | M49 to M53 and those lines in full |
| `RC\funnel\HYBRID-FATES.md` | every X1 and X6 row; `FUNNEL.md` not re-read |
| `RC\REVIEW-2026-11-07.md`, `RC\review-2026-11-07\system-map.md` | in full |
| `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\RISK-SIZING-PLACEHOLDERS.md` | the 31 rows and the slot table |
| Code at W | spot checks only, named where used |

`unit-baseline\SWAP-CHART.md` had not landed when I read, so I checked placeholders against the plan's own list above.

---

## 2. The versions of architecture he asked for and never saw

His ask: "before architecture, you have versions of architecture because you can compare... pick up the better versions of each" (`operator-words-2026-11-03.md:176`), and "Where are they?" (M53). They are on disk.

**Plain truth about what they are.** They are three versions of one thing, not three different QMX structures. All three got the same brief (`ARENA-BRIEF.md`): design the funnel's twelve-part first increment. The funnel had already settled what goes in, using the dollar and go-live lens. The brief's ten extension walks hold no pod, no mini app, and no unit arriving from the Lab or a workflow (`REVIEW-2026-11-07.md` item 5). So they differ on two forks only:
- **F-A:** how a number moves.
- **F-B:** where the brakes live.

None of them compared "unit plus pod" with anything. That comparison has never been drawn.

| | Candidate 1 | Candidate 2 | Candidate 3 |
|---|---|---|---|
| One line | A Kubernetes-style document: people write a spec, the runtime writes status, small loops move each number inside bounds | Every number recomputed at an anchor and written on one sheet; everyone reads the sheet; cuts at once, raises wait | The unit carries its own brakes; a shared fact package hands facts to both unit and guard |
| How a number moves (F-A) | A learner proposes with bounds; an applier moves it in the number's own mode (`user_only, off, at_anchor, at_flat, at_period_open, live`) | Refresh at anchors only; the document has room for the learner later (`Resolved.low`, `high`, `Sheet.rev`) | Refresh at anchors; **facts move live, numbers do not** |
| Where brakes live (F-B) | One guard above every unit | One guard, one seam in `UnitSliceHandler.mint_intents` | **Unit's own brakes in the unit** (`halts` compile); only cross-unit rules in the guard; two cut-only stages proved equal to one table by a property test |
| Where status lives | A file beside R22's snapshot | Journal rows only; `recover` is a fold | Inside R22's snapshot |
| A sizer's interface | Wide `SizerInputs` with an `extra` map | **A sizer base is a derivation producing dollars at risk; the sizer block only turns dollars into lots** | Wide evidence plus facts like `agent_cut_factor` and `accelerator_factor` |
| Group level | "Portfolio", no contract | `risk-group` document with `display_name` and reserved `parent`, so Book, BMS or cluster stay open | Portfolio config |
| Exits | `exit_set` in the profile | `exit_set` stays on the unit; absolute stop prices at every seam; `safest_exit` | Fixed order inside the unit; exits never reach the guard |
| Agents | Direction on each operation, cut through evidence | Same, plus `run`; `risk_scenarios_run` | A cut is a fact with an expiry the sizer reads |
| Findings of its own | `live` only earns on a cost change | Level-weighted B cancels itself; `tzdata` on Windows; targets should rest at the venue; a new `Kind` per brake would be rework | 42 % of healthy units to paper under the two-warning rule; "the guard must fold state even on a refused intent" |
| Stated size | 29 PRs | 38 PRs | 28 PRs |

**What the lead did with them.** `PICK.md` used a rubric of twelve parts, extension by row, self-configuration, choke budget, code fit, "too much machine" and hard lines. The lead read candidate 1 in full and the other two "through their contracts", with no cross-judge, to save usage. The fold (`SPINE.md`) took candidate 1 as base with fourteen grafts, then fixed ten blockers from `CHECK.md`. Its size became 43 PRs.

**Which parts survive his lens (my read):**

| Part | Source | Under the lens |
|---|---|---|
| Spec and status with separate writers; `generation` stamp | C1, R7 | **Survives.** It carries nothing about numbers (`REVIEW` Keep) |
| Derivation block, fallback ladder, receipt, reason code | C1, C2 | **Survives, the heart of "how does it self configure" and "change the way it is derived"** |
| Authority mode per number | C1 | **Survives as a field.** Which modes ship on is a choice, so the field should not be cut to two |
| Sizer base as a derivation; sizer block as a converter | C2 | **Survives, and answers "why lots" in structure** (T4) |
| Registry row as a `guard` section on a dictionary entry, so a part is one folder | C2 | **Survives.** Ties new parts to QML's dictionary |
| Answer types `Refuse | Factor | CapLots | Trip` | `CHECK` B9 | **Survives.** Without these "a new brake needs no code" is false |
| Facts live, numbers at anchors | C3 | **Survives** as the plain rule for how a cost change reaches size |
| Fact kernel with `PROVIDES`, two ports, one conformance tape | C3, C2 | **Survives** |
| Shadow = same code with the action replaced by a journal write | C3 | **Survives** as a mechanism; which rows ship in shadow is policy |
| One wrapper so a guard failure cannot reach an exit | `CHECK` B3 | **Survives** |
| USD seam with `conversion_market` | `CHECK` B5 | **Survives** |
| His door for publishing risk kinds | `CHECK` B4 | **Survives** |
| `state_carry_rule` | `CHECK` B7 | **Survives as a shape; "a version never clears a brake" is a default he could change** |
| Spine's "every brake in the guard, `halts_not_built` stays" | C1, C2 | **Reopen.** See T6. Candidate 3 was rejected partly on the go-live lens, and five halt blocks ship today unable to bind. He said "look at what exactly is already there in the unit" (M49) |
| `two_live_readers` compile refusal; 0.75 choke gate in CI; level ladder and lockouts; start level from the holdout; `horizon-floor-odds@1` as the base; the 13-live and 12-shadow lists | C2, fold | **Set aside as fixed law** (`REVIEW` "Set aside"). Each can be a preset, a warning or an optional block. All were tuned on dollars |
| `stop_not_built` stays, "no unit without a price stop" | all three | Keep as a preset default at most. Note the plan's placeholder 11 asks it as a question |
| Group "bands fixed, rows never renumber" | fold | Survives as the default table; the document should own it (it does: `rank` on the group) |
| "43 PRs", slice plan, Q1 to Q9 | fold | Does not survive the recut as written (`system-map.md`) |

---

## 3. The ideas, best first

Fate shorthand: **F** is the `HYBRID-FATES.md` tier. The funnel's "core / shadow / later" followed go-live needs, and its tuning followed dollar sims. "Go-live lens" or "dollar lens" says which drove the fate.

Evidence shorthand:
- **Elsewhere** means it runs in production in another field and was never tested on a trading unit (the A4 header says the same).
- **Built** means it is in the code.
- **Proposal** means a design on disk.
- **Guess** means nobody has shown it.

Nearly every software pattern here is "elsewhere". Don't read that as proof it improves trading.

### A. What the template is

**T1. The unit is one document; numbers live on it as a spec with reasons; the runtime keeps a separate status.**
- What: He and agents write choices (which blocks, ranges, how each number derives). Only the running system writes what it learnt and did. So his edit and the machine can't overwrite each other, and an old brake state can be spotted as old.
- Source: Kubernetes (`R7` 3.1), MT5 inputs read-only (`R7` 9.1), `X1-H01`, all three candidates' AD-1.
- Touches: unit document, `NumberSpec`, status beside R22's snapshot.
- Fate: core; neither lens hurt it.
- Read: **seat.**
- Evidence: elsewhere; the snapshot's fingerprint stamp is built.

**T2. Every number carries how it is derived, and the derivation is itself a swappable block.**
- What: "If you say 10%, where does it come from?" Each number names a rule block, its inputs, and a ladder: own record, then pooled group, then preset, then refuse. Changing the rule is a new version; each resolved value keeps a receipt.
- Example: a futures week with the copilot could swap the rule for `risk_fraction` without touching the sizer.
- Source: his words (`operator-words-2026-11-03.md:13`), `X1-H08`, A4-054, A4-055, `R7` 2.6, `SPINE` 4.1.
- Touches: QML (new `derivation` role), compiler, dictionary.
- Fate: core.
- Read: **seat.** The first `preset-default@1` (a plain value treated as a derivation) gives every number one shape (`PRESET-NUMBERS.md`), which is a nice small trick.
- Evidence: proposal; the motion engine is the built cousin (`G8` 3.9). Note `R1` pattern 15: no shipped product self-tunes risk numbers under guardrails. This is open and untested ground.

**T3. The Lab's pod already is the customization layer he described, and no architecture version mentions it.**
- What: A pod is a stack of pure blocks in seven slots: inputs, guards, allocator, sizer, throttles, caps, ledger. One simulator feeds a size trail, stress board and head-to-head. Editing gives a new version; "Send to paper" and promotion follow.
- Source: `LP\ARCHITECTURE-SPINE.md` AD-10 to AD-12, `LP\PLAIN-WORDS.md`, A4-096, `REVIEW-2026-11-07.md`. His words: "question number five is really more of a pod life question" (M49).
- Touches: pod, Lab, every guard row, sizer slot.
- Fate: X1-H33 **later**, X1-H30 **later**; go-live lens pushed them out, and the arena never saw them.
- Read: **seat.** The baseline must say where each of the seven slots runs at trade time. `REVIEW` calls this open and the Lab spine waits on it (OPEN-1; Deferred rows "the unit's exact parts", "which blocks the node can run live").
- Evidence: proposal. Pods are unbuilt: `qmx_control/lab.py` says so, and the `pod` kind is only `"slots": {"type": "object"}` at W.

**T4. Dollars are the decision; lots are just how a venue spells an order.**
- What: He asks "Why lots?" because he trades many instruments. Candidate 2's split answers this: a rule decides dollars at risk, a small converter turns dollars into whatever the instrument takes. The converter reads the record's value per point and lot step: 0.01 lots, 1 contract, 0.001 BTC, 1 share. `lots` remains only as the field name the record uses.
- Source: `candidate-2\SPINE.md` 3.3, `SPINE.md` 4.3; every platform has a small sizer (`R1` pattern 1); shared converter `X1-H25`; `qml/numbers/records.py` at W (`lot_step`, `min_lot`, `contract_size`, `value_per_point`).
- Touches: sizer slot, instrument record.
- Fate: grafted into the spine; the explainer's wording still sold it as "lots".
- Read: **seat.** And consider a neutral word (`quantity`) at the seams, since `Size.lots` is what he sees. Vocabulary is his call.
- Evidence: proposal over a built converter. USDJPY fault at `block.py:52-53` shows why it matters (`CHECK` B5).

**T5. How units share capital is a declared, swappable rule, not a law.**
- What: His repeated objection: "the more units I have, the less I can trade". Platforms ship both answers. One splits by N (LEAN equal weighting, freqtrade). The other gives each unit its own size and caps only the total (LEAN insight weighting, RiskMetrics: parent limit below the sum of children, set on how often they lose together).
- Source: `R1` 1.3, 5.3, 3.2 (MQL5 14336); `X1-H38`; `SPINE` 4.3 `b_split_rule`.
- Touches: group document, sizer base.
- Fate: the funnel fixed one square-root split (DP9) on dollar sims.
- Read: **seat** for a named allocation mode on the group; **content** for each rule. Today only `flat` and `freed` are values, both square-root forms. The "own size, capped total" mode has no row in the spine, though `X1-H38` describes it.
- Evidence: LEAN checked; RiskMetrics is live bank practice. No test for scalper books.

**T6. A rule row should be movable between unit and guard: the row's shape doesn't care where it runs.**
- What: C1 and C2 put all brakes in one guard; C3 put a unit's own brakes in the unit. The spine rejected C3 but kept brake blocks in `HaltInstance` shape so "a later move is a move, not a rewrite". Under the lens this is more than a hedge: a scalper's brake and an intraday's differ, units arrive from four origins, and a pod might carry guards at its level.
- Source: `candidate-3\SPINE.md` AD-1 and F-B; `PICK.md`; `SPINE` F-B; `G8` 3.5 (five halts shipped, refused).
- Touches: registry row, compiler `halts_not_built`, guard, pod slots `guards`, `throttles`, `caps`.
- Fate: C3's home rejected. Its cost was named as "two arbitration stages"; the choice was scored on go-live.
- Read: **seat.** Add to the row where it may run, unit or above. C3's property test shows the two stages equal one table because both only cut; raises are the exception. Conflict kept in section 4.
- Evidence: proposal plus a model test (`out-c3.txt`, 20,000 random states).

**T7. Four kinds of unit, one door.**
- What: "I can have a unit made through the lab... a different type of workflow, or a unit come from a mini app. Those are like four different types of units. All of them can trade." So the template must not assume QMB's holdout, a card or a record exists. The needs list and the ladder already allow it: a missing input names a fallback.
- Source: his words (M49); `X1-H19`; `SPINE` AD-17; plain-python and Lab paths in `G8` 3.11.
- Touches: compiler, profile, admission gate, judge.
- Fate: never walked. `SPINE` 4.4's admission reads "the holdout's net low end" and a start level from it, which he rejected as out of scope ("I think no").
- Read: **seat** in that nothing in the baseline may need a QMB card. Admission and start level become optional blocks.
- Evidence: his ruling.

**T8. Every piece of the template has a typed schema beside its code; forms, the Numbers tab and checks come from it.**
- What: Name, type, default, min, max, step, group and label live next to the code. Every extensible platform does this. Unknown fields are refused, and a field the compiler doesn't read must fail loudly.
- Source: `R1` pattern 6, n8n `properties`, StrategyQuant `@Parameter`, MT5 Wizard header, Nautilus `deny_unknown_fields`; `X1-H15`, `X1-H66`; A4-069.
- Touches: `entry.json`, `qmx.risk-profile/1`, UI.
- Fate: X1-H15 core; generator X1-H66 and X6-41 later (go-live lens).
- Read: **seat** for schema and refusal; the generators are **content** but cheap wins for maintainability.
- Evidence: checked on many platforms. `G8` B6: nine fields parsed then ignored today.

**T9. Save only what differs from the preset, with the block version pinned.**
- What: n8n's core trick. A saved workflow stores overrides and each node's version, so a default can improve and old work keeps running. New behaviour sits beside old until someone moves.
- Source: `R1` 4.2, 4.3, 4.5; A4-037, A4-057; `X1-H37`, `X1-H43`.
- Touches: unit document, pin, `unit_new(template, overrides)`.
- Fate: pins core; "stores only diffs" under later X1-H37.
- Read: **seat**, because storing full copies at 200 units can't be undone later.
- Evidence: n8n checked. Warning side: Home Assistant overwrites and breaks users (`R7` 7.2).

**T10. Presets are charts: one schema, many presets, values as derivations.**
- What: A preset fills everything for a unit type; a user or the copilot starts from it, overrides and saves. "Any type" is a new preset, never a new schema. `null` removes a default on purpose; revisions are numbered.
- Source: Helm (`R7` 6.3), MQL5 18918 (`R1` 3.2), `X1-H16`, A4-053; his "one template by any type".
- Touches: Library; `qml/unit/templates/` holds only the dummy at W; the `template` Library kind is `retired: true` at W, so `SPINE`'s `role: preset` fills a real hole.
- Fate: core.
- Read: **seat** for the mechanism. The presets themselves are **content** (copilot-made, per M50).
- Evidence: Helm checked; R1 notes the MQL5 article's backtest is the author's own.

**T11. Templates for a unit's whole sizing structure: old-style, Book-style, hybrids.**
- What: "we can have versions that are literally... like the first system, then versions that are literally taking parts of both." `X1-H17` packs make this concrete: small bundles (sizing, brake, exit, accelerator, derivation) stacked in order, with a named combiner where two claim a slot.
- Source: his words (`operator-words-2026-11-01.md`; `SEEDS` B6), A4-089, A4-194, `X1-H17`. `SEEDS:1392` records it as "not addressed as stated".
- Touches: profile, pod, combiner role.
- Fate: later (go-live lens); spine refuses more than one pack.
- Read: **seat**: `packs` field and combiner list reserved and readable. Each pack is **content**.
- Evidence: LEAN chaining checked; combiner meaning on exits untested.

**T12. QML is the SDK: new roles for what agents will need.**
- What: `derivation`, `applier_mode`, `guard_statistic`, `combiner`, `restore`, `proposal_validator`, each with a protocol, contract test, two starter blocks and a dictionary family. He said QML is what stops slop, and he invited changes to it.
- Source: `X1-H67`, `X1-H25`, `SPINE` 4.2; M50, M52 ("QML is already there. You can enhance it"); `G8` 3.1 to 3.4.
- Touches: `qml/blocks/api.py`, catalogue, `component_type` list.
- Fate: X1-H67 later (go-live lens), with only `derivation` and guard rows taken up.
- Read: **seat** for any role the baseline's own parts use (`derivation`, rows, `restore`). The others are **content** when a block needs them.
- Evidence: proposal over four built slot protocols.

**T13. The dictionary already holds closing mechanisms; a rule closing a position is a block, not a question.**
- What: His correction: "the dictionary has closing mechanisms". Stdlib at W has `target-r-multiple`, `time-exit-bars`, `roi-table-exit`, `stepped-profit-stop`, `offset-gated-trailing-stop`, `profit-fraction-trailing-stop`, `peak-holdings-giveback-exit`, `swing-stop-buffer`. My search found 24 exit, 7 halt and 5 sizer entries with `component_type` set across stdlib and seed. Six exits stay silent because per-bar exits get `{}`.
- Source: M49; `G8` 3.5; `test_wave1_exits.py:343-356`; `REVIEW`.
- Touches: exit socket, `exit_not_built`.
- Fate: Q1b asked him as policy; step 2 core, step 3 waits on R24.
- Read: **seat**: exit socket step 2 and position facts. Blocks themselves are **content**. Trails and partials depend on the signed-stop fact.
- Evidence: built, by test.

**T14. Facts, responses and limits: three separate things.**
- What: Facts are measured (spread, value per point). Responses are chosen (a taper). Limits are his (floor). A frozen record of venue facts stays outside what the strategy decides. One article found three constants that "looked like configuration" but no code read.
- Source: MQL5 24237 (`R1` 3.2, pattern 8), `X1-H18`, A4-052, `SPINE` AD-6.
- Touches: instrument record, profile, group.
- Fate: core.
- Read: **seat.** Also the plain frame for his "QMX is a data analyst; I observe fees and act" (M51).
- Evidence: author's own; simple bookkeeping.

**T15. One instrument risk record per unit, instrument and broker; class differences are fields, not branches.**
- What: Money per point, lot bounds, class and bucket code, hourly costs, conversion, session clock, roll and split rules, thresholds. Futures mini and micro are just different rows. A new class is rows plus venue work.
- Source: `X1-H18`, `SPINE` section 6 walk 2, `SEEDS` lens items 9, 17; A4-179 logical instrument ids resolved per broker.
- Touches: `InstrumentRecord` (has no commission or base-currency key at W per `X1-H63`, `X6` gap 3).
- Fate: core, built for FX first; other classes go-live deferred.
- Read: **seat** for the shape; rows are **content**. Crypto and futures test it: `X1` gaps 3 and 4 (day boundary, roll) are open.
- Evidence: proposal.

**T16. Override chain: preset, style, class, bucket, instrument, account, unit, market, timeframe, session, event.**
- What: Numbers can differ by instrument or session without a new schema. Each override stores its evidence, and event overrides expire. A residual bucket catches anything unclassified. Later entries win.
- Source: `X1-H37`, A4-050, A4-051 (ISDA SIMM), A4-195, A4-185.
- Touches: profile `chain`, compile-time resolver, record.
- Fate: four keys core, seven reserved; rest later (go-live lens).
- Read: **seat.** Reserved keys parse today in `SPINE`. Keep them. "An instrument earns its override only on forward evidence" is policy, so **content**.
- Evidence: SIMM read; override thresholds are guesses.

**T17. Cascade with an "important" rule at the outer levels.**
- What: Most specific wins for normal values; an outer limit marked important can't be loosened inside; children may only tighten caps. An inspector prints who set each value.
- Source: CSS, VS Code policy, Nix priorities, ESLint (`R7` section 6), `X1-H36`, A4-043 to A4-049.
- Touches: unit, group, pod, account.
- Fate: core over four keys.
- Read: **seat.** The inspector (`risk_explain`) doubles as how a newcomer learns the system.
- Evidence: checked elsewhere; many important flags get hard to read.

**T18. The needs list: adding a piece pulls in the statistics it needs.**
- What: A brake says what it reads; the host says what it provides; compile compares them or names a fallback (`compute_here`, `treat_as_absent`, `no_new_entries`). Admitted limit: a truly new fact is code in the kernel.
- Source: Bevy (`R7` 7.1), `X1-H19`, `SPINE` AD-17; `reads` fallbacks built (`G8` 1.1).
- Touches: compiler, kernel.
- Fate: core.
- Read: **seat.** This is what lets a Lab-born or agent-born block be refused with a sentence instead of doing nothing.
- Evidence: Bevy checked.

**T19. A new unit type or brake should need one folder and zero core edits.**
- What: `SPINE` section 6 walks 1 and 2 show about 20 lines for a halving brake, and rows for a class quoted in EUR. Stated limit: `two_live_readers` refuses making it live, and a new statistic needs a kernel provider.
- Source: `SPINE` section 6; `CHECK` B9; `X1-H21` chassis stress battery ("add a level, swap the sizing basis, add a class, add a timeframe axis") as a CI test.
- Touches: registry, CI.
- Fate: stress battery later (go-live).
- Read: **seat** for the battery. It is the direct test of "handle any amount of stress" and missing walks should be added: pod, mini app, Lab-born unit.
- Evidence: proposal; the check found the first claim false until B9 was fixed.

**T20. Outside code: Python where QML can't express it.**
- What: Three doors on disk:
  - a block in the Library, checked deny-by-default and pinned by fingerprint (works in shape, no save row);
  - a trust ladder (origin × evidence) with a minimum per slot and his signature on money-path pins;
  - a quarantined `plain_python` hatch.
- Source: M50 ("It's just that it has to be something that QMX or QML rather can't pull off"), `G8` 3.3, 3.11, `X1-H22`, `X1-H24`, n8n Code node and community rules (`R1` 4.4), A4-071, A4-072.
- Touches: loader, layer F, `blocks_save`, compiler `plain_python_not_built`.
- Fate: all later; "only signed `qml` and `human` blocks size live" at go-live.
- Read: **seat** for the save-and-contract-test path (`X1-H53`, H64) and the loader's signature check. Trust levels are **content**. Note `X1` collision 20: raw sizer versus protected core.
- Evidence: built loader; n8n checked; ladder is a proposal.

**T21. A small expression form compiled to a block.**
- What: `equity * fraction / stop_distance` in a field; no calls, no loops, only known names. He and the copilot can read it. Loader sees only blocks.
- Source: n8n (`R1` 4.1), `X1-H09`, A4-056.
- Touches: derivation; `noDataExpression` for never-self-tune rows.
- Fate: later (go-live).
- Read: **content** (a generated block needs no core change). Watch `X1` collision 30: an untested side door.
- Evidence: n8n checked; QMX form is a guess.

**T22. Two adapters before a seam counts as real; contract tests in every class.**
- What: Ship two sizers and two halts per scope before calling a slot extensible. Tests run on a record per class key and on shorts. Library blocks enrol too.
- Source: `codebase-design` rule; `X1-H25`, `X1-H68`; `G8` 2.2 (long only, stdlib only).
- Touches: `test_socket_contracts.py`.
- Fate: core.
- Read: **seat.**
- Evidence: test weaknesses are built facts.

**T23. Three faces per block: trader words, machine spec, code.**
- What: Agents write trader words first; a known failure sits in the trader face (`martingale-sizing` warns before binding). Bound on an uncovered class compiles only in shadow.
- Source: `G8` 3.4, `X1-H23`, H66, H68.
- Touches: dictionary.
- Fate: later.
- Read: **content** on a built shape, but agents use it to avoid slop, so do it early.
- Evidence: built shape; "faces agree" test unwritten.

### B. Self-configuration

**T24. Learner and applier: the Vertical Pod Autoscaler model.**
- What: One part publishes a target with low and high bounds from the unit's decayed record, clamped by owner's range. A separate part moves the value only in the mode the owner set. "QMX has the learner and no applier."
- Source: `R7` 2.5, 11; `X1-H02`, H03; `candidate-1`.
- Touches: `authority` (parsed, never read, `G8` 3.10), motion engine.
- Fate: core; run in simplest modes because F-A scored on dollars and size (`candidate-1` Appendix C, `candidate-2` section 4).
- Read: **seat** for modes and bounds as fields. Which modes ship on is **content**. He said self-configuration is ours to decide (M49) and suggested an agent hill-climb it.
- Evidence: VPA checked; R9 (via `X1` roundtable): no gain on independent trades.

**T25. Facts move live, numbers move at anchors; cuts at once, raises at the anchor.**
- What: A plain rule that answers most timing questions. A broker cost rise is a fact the sizer reads at once. A learned number only changes at its clock. Permission to exceed 1.0 is itself a raise.
- Source: `candidate-3` AD-6, `candidate-2` AD-4, `SPINE` AD-6, AD-7.
- Touches: all rows, clocks.
- Fate: core; press fix came from a walk, not dollars.
- Read: **seat** as defaults of the applier. "Raises wait for the anchor" may be wrong for a scalper with accelerators (`SPINE` keeps a live-ledger multiplier inside frozen bounds), so keep it a mode, not a law.
- Evidence: proposal.

**T26. A tuned number is a guess with a guard, a trip counter that freezes, and a named way back.**
- What: Failed guard reverts to the default with a reason. Too many trips freeze it and flag someone. Like HotSpot's "stay in the interpreter" and Simplex's safe controller with a dwell.
- Source: `R7` 2.7, 7.4, 8.2; `X1-H04`; A4-006, A4-007, A4-009.
- Touches: `ValueGuard`, status.
- Fate: core; fold changed Simplex into a ladder rung.
- Read: **seat** for the field; guard conditions are **content** (numbers lens).
- Evidence: elsewhere.

**T27. Direction-split motion: windows, rate caps, cautious missing data, grow only on evidence at current size.**
- What: Each number has its own down speed and up speed. Grow only after trades were really taken at this size (Netflix AIMD). Missing data pushes the cautious way. New or long-idle units start small.
- Source: HPA, TCP, AIMD, Guava (`R7` 2.1, 2.2, 2.4, 5.4); `X1-H05`.
- Touches: `Derivation.max_step`, `cautious_direction`; candidate 2 names a future `behavior` block as "real rework".
- Fate: core in thin form.
- Read: **seat**: leave room for a per-direction `behavior` block now, since C2 itself says adding it later is rework. His "size down, but not quickly" sits here.
- Evidence: elsewhere; `X1-H05` cites a synthetic script.

**T28. A reason on every resolved value.**
- What: `user`, `default`, `calibrated`, `borrowed:<group>`, `capped_by:<rule>`, `stale_so_default`, `frozen_after_trips`. Evaluation never throws. Today's receipt is a hard-coded literal (`unit.py:829`).
- Source: OpenFeature (`R7` 4.4), `X1-H07`.
- Touches: `SizerReceipt`, UI, agents' reads.
- Fate: core.
- Read: **seat.**
- Evidence: spec checked.

**T29. The never-self-tune list.**
- What: Floor, buffer, kill line, kill level: no learner, agent or expression moves them. Blank blocks the live click only, never paper or harness.
- Source: OtterTune, MT5 `sinput` (`R7` 2.6, 9.1); `X1-H06`; A4-101.
- Touches: `owner`, `user_only`.
- Fate: core.
- Read: **seat** for the field; the list's content is his per template or pod. `X1` collision 29: "not set in stone" means he can edit the list.
- Evidence: elsewhere.

**T30. Pooled priors for a new unit.**
- What: A new unit borrows from similar units, edge shrunk toward zero, market mechanics never pooled.
- Source: OtterTune, `X1-H08`, A4-015, A4-196, A5-048.
- Touches: ladder rung `pooled:<class>`.
- Fate: core as a rung.
- Read: **content** behind a seat already in the ladder. `X1` collision 25.
- Evidence: standard method, no higher-return evidence.

**T31. Herding guard: units retuning together.**
- What: Forty units read one gold move and cut together. A share cap per cluster per window; or stagger; or pool and move once. Synchronised anchors are "a herd by construction".
- Source: `X1` P16, VPA eviction tolerance, `candidate-2` section 4, A4-008.
- Touches: applier, group; 200 units makes it real.
- Fate: deferred (fork row, dollar sim saw little).
- Read: **seat** for a per-group cadence offset; rule **content**. `X1` gap 6: no herding test exists.
- Evidence: guess; `X1` roundtable warned of it.

**T32. A few pre-approved versions as bandit arms; learned profiles; genome variants.**
- What: Wild forms of self-config.
- Source: `X1-H48`, H70, A4-182, A4-199.
- Touches: profile set; identity table.
- Fate: later or wild.
- Read: **content.** They suit his blacksmith hill-climb idea (M50) in the Lab, off the money path. Conflict with R3 §5.5 per `X1` collision 17.
- Evidence: papers without trading tests.

### C. Levels, pods, mini apps, the Lab

**T33. A pod as a shippable bundle.**
- What: A signed bundle (a mini app whose `provides` lands Library items): a group document, packs, presets, agents, skills, a self-test card. "How do we ship pods?"
- Source: his words (`operator-words-2026-11-03.md:13`), `X1-H30`, A4-094.
- Touches: `qmx_apps` manifest (`provides`, lander), Library.
- Fate: later (go-live lens); `REVIEW` says bring back.
- Read: **seat** in the host: at W, an app has one lander, and `qmb-run` is "the one core lander today" (`host.py:1912`). `G8` 6.4 found an app can't land `component` entries or templates. Without that a pod can't ship.
- Evidence: MIS proves apps run QML blocks by entry id (built).

**T34. The Risk Lab mini app.**
- What: `risk = runs`: resize replay, scenario run, profile check, derivation preview, ledger browser, drafting agents. Never in the order path.
- Source: his "combine a mini app together with the risk and sizing system", `X1-H29`, QuantAnalyzer (`R1` 2.3), A4-094.
- Touches: apps, tools.
- Fate: later; tool rows core.
- Read: **content** on the same lander seat as T33. Possibly the first proof a third party could build one.
- Evidence: proposal.

**T35. Resize a recorded trade list instead of re-backtesting.**
- What: Re-size finished trades under another rule in seconds. Nothing tests sizing alone today since the judge is size-blind. Note the vendor's own null on one equity filter.
- Source: QuantAnalyzer (`R1` 2.3, pattern 14), A4-186, `X1-H21`; `G8` 5.3; placeholder 29 ("fields to replay any sizing later").
- Touches: QMB job, trade row fields, Lab.
- Fate: core as harness; `risk_resize_replay`.
- Read: **seat** for trade-row fields (equity before, session, streak, tuned values). Tool is **content**.
- Evidence: vendor tool checked. Weak on stop recognition and fill realism.

**T36. Clusters as tags, not folders; Book and BMS replaced by three documents.**
- What: Unit profile; tag drop-ins applied to every unit with the tag, a unit in many at once; one portfolio config. Class isolation and class defaults become one mechanism. "Book" can stay as a screen word.
- Source: `X1-H40`, H42, H34; systemd, SIMM; his freedom ("If the BMS or a book system doesn't make sense... let's do that"); his "the book... It's just cleaner".
- Touches: group, scopes, Lab compile target.
- Fate: later; Q8 (go-live).
- Read: **seat**: AD-10's scope vocabulary and `tag:` key. Structure itself he said "decide later". `candidate-2`'s `group` plus `parent` keeps both open. Note hedge-fund pod and BMS-as-pod-manager (`operator-words-2026-11-01.md`) pull on the same level.
- Evidence: no QMX generation ran it.

**T37. Pods configure pod-life answers: day stop raising kill, closes by rule, press rules.**
- What: Q1, Q4, Q5 were not policy. Each is a field on a pod or group, with a default.
- Source: M49; `REVIEW` "Q1-Q9".
- Touches: group rows, effect table.
- Fate: asked him as questions (rigid framing).
- Read: **seat**: rows must hold these as data. Hard line stays: only his hand lowers a kill level.
- Evidence: his ruling.

**T38. One simulator or one guard? They must be the same evaluator.**
- What: Lab AD-10 says `qmx_lab.pods.simulator` is the one evaluator behind every pod screen and paper. The spine says the Lab runs "the same package on a replay port". X6-39 asks the simulator to write the same rows. If pods get a separate simulator, a size shown in the Lab may differ from the one live. Also a pod block is declared "pure" (Lab AD-10) while guard rows keep `block_state`.
- Source: LP AD-10, `SPINE` AD-3, `X6-39`, `X1-H33`.
- Touches: guard, Lab, block contract.
- Fate: never noticed; the arena never read the Lab spine.
- Read: **seat.** My read, and the main structural conflict in this area. State passed in and returned would reconcile "pure" with state, but no document says so.
- Evidence: reading of two documents.

**T39. One catalogue: `pod-block` and dictionary `component` should not be two block worlds.**
- What: Lab `pod-block` kind has `form | graph | code | model` and its own Library item. QML's dictionary has entries with faces. MIS shows blocks kept in one copy through one loader. A pod block should probably pin dictionary entries.
- Source: LP AD-10; `G8` 3.8, 6.3; `X1-H33`, H66; placeholder 31.
- Touches: Library kinds, loader.
- Fate: not addressed.
- Read: **seat.** My read. Form and graph kinds still need a compile path into a block.
- Evidence: reading.

**T40. A model as a block under a rule ceiling; slots on a sizer or throttle.**
- What: Plug a trained model into a named place. Plugging makes a new version, retested.
- Source: LP AD-7, `PLAIN-WORDS.md`.
- Touches: pod-block `model`, `/sizer/inputs`, loader.
- Fate: not in funnel.
- Read: **content**, after T33, T39. Baseline must not forbid it. `qml` has a `MODEL` component type.
- Evidence: proposal.

**T41. Lab family ledger counts every trial; identity table is data.**
- What: Dead tries count, so the luck warning is real. `settings.lab.identity_rule` already expects `profile -> branches-from`, and "the risk session replaces rows without a code change".
- Source: LP AD-6, AD-16; `G8` 3.6; A4-110.
- Touches: identity rows `profile_sizing_change`, `profile_exit_change`.
- Fate: not linked to the template.
- Read: **seat** for the identity vocabulary shared by Lab and unit (`SPINE` AD-19 and LP AD-16 use different words today). Methodology itself: **other session.**
- Evidence: designed.

**T42. Paper as a chain of daily finite runs; promotion is two human clicks elsewhere.**
- What: The Lab soak ends in a card; signing and activation are clicks in Portfolio; agents never promote.
- Source: LP AD-12; `PLAIN-WORDS.md`.
- Touches: paper-run, promotion card, group.
- Fate: not in the arena.
- Read: **other session** for readiness rules (methodology); **seat** for "unit parts as a list" that the card reads (`PLAIN-WORDS.md`: "read as a list of parts, so the risk session can change them later").
- Evidence: designed.

**T43. Mini apps feed each other; the only built road to a unit is one narrow board.**
- What: "mini apps can provide output and input for other mini apps." `provides` and `feeds` exist. To reach a unit: `reads` refused; MIS board relay written, not started; board can only hold back entries. His futures mini app feeding an FX one needs this.
- Source: M50; `G8` 6.1, 6.3; `compiler.py:901`; `X1-H72`.
- Touches: `reads`, feed relay, needs list.
- Fate: `reads` stays refused in spine.
- Read: **seat**: a governed path from a published reading to a unit's `reads`. Without it pods can't use their department's work.
- Evidence: built narrow path.

**T44. Budget share travels with the deployment.**
- What: Today every unit sizes from the whole account; paper from the demo balance. A share or compartment per deployment fixes it, in any capital rule.
- Source: `X1-H32`, bulkhead (`R7` 5.2), AIMD shares, `G8` 5.3.
- Touches: deployment, sizing facts.
- Fate: "core" tagged; spine's B split largely replaced it.
- Read: **seat.** Check the fold: `SPINE` has no `unit_capital_share` field, though FATES says core. Possibly lost in the fold.
- Evidence: elsewhere.

**T45. Shed by declared class; burn tiers per level; spent budget freezes versions.**
- What: Cut the newest class first, not pro rata. Fast burn acts, slow burn sizes down.
- Source: SRE (`R7` 5.5, 5.6), `X1-H41`, `X6-15`.
- Touches: group rows.
- Fate: later or shadow.
- Read: **content.** Windows need a "trading time" definition (`X6` gap 9).
- Evidence: SRE; mapping to loss budgets is a judgment.

**T46. Isolation by peer comparison with growing timeouts.**
- What: Compare a market with its peers; minimum sample; cap share isolated at once; lengthen on repeats; shadow then ramp.
- Source: Envoy (`R7` 5.3), `X1-H12`.
- Touches: scope keys, `class:` rows. Also `X1-H28`.
- Fate: isolation shadow (go-live).
- Read: **content** over scope-key seat. See H2 or brakes harvest for the rules themselves.
- Evidence: elsewhere.

**T47. Same compiled unit on PC and node; learner on PC, applier beside the order path.**
- What: PC is home; status travels; `at_flat` is decided next to orders.
- Source: `X1-H31`, P21, memory ruling, his "most of the pod stuff... on my machine".
- Touches: placement, status path, Lab AD-8's "a pod's home is a place".
- Fate: core.
- Read: **seat.** Also agents' VMs later (M50).
- Evidence: built one code path.

**T48. Two records: logic in R across versions, money per version.**
- What: A sizer swap doesn't cost the record. Judge is size-blind so it can't tell versions apart anyway.
- Source: `X1-H44`, `SPINE` AD-19.
- Touches: judge, journals.
- Fate: core.
- Read: **seat.**
- Evidence: judge built; two numbers on a card can confuse.

### D. How new versions ship

**T49. Pinned versions plus a forwarding map.**
- What: Old block and version map to new with a parameter transform, so `fixed-fraction-at-stop@1` to a real sizer is a declared migration. This is the mechanism for his "swap the placeholders" (M52). Under the default table today a swap is a new unit with a fresh record (`G8` 3.6).
- Source: Simulink (`R7` 7.3), n8n, `X1-H43`, A4-038; `tools/qml/placeholders.py`.
- Touches: identity table, `_cold_reason`, `logic_fingerprint`.
- Fate: core.
- Read: **seat.** `X1` gap 9: no transform language.
- Evidence: elsewhere.

**T50. Plan before change, refused if stale; click bound to the effect.**
- What: An agent edit shows what moves and whether the record survives; apply refuses if anything changed. His click signs the exact hash, level, markets, date.
- Source: Terraform (`R7` 3.2), `X1-H46`, A5-055.
- Touches: proposal cards, `_his_click`.
- Fate: core.
- Read: **seat.**
- Evidence: Terraform checked; controlled test in a paper.

**T51. Shadow, canary, full, with three outcomes.**
- What: A new version writes what it would have done; then runs on a share while the old runs the rest at the same time; ends pass, fail, or inconclusive (pause for him). Don't judge while another loop moves it. Declare time to promote and roll back.
- Source: Argo, Flagger, Kayenta (`R7` 4.1 to 4.3), `X1-H45`, A4-023 to A4-026.
- Touches: deployment (second deployment of one version refused, `G9`), judge.
- Fate: shadow; canary later (go-live).
- Read: **seat** for a rollout field. Analysis rules are **other session: methodology.**
- Evidence: production elsewhere.

**T52. Upgrade offers, never silent; no blind retries.**
- What: A better default arrives as a card for untouched units. A failed deploy waits for a new version. Rollback and automation can't both drive one unit.
- Source: `X1-H47`, Argo CD (`R7` 3.3), Home Assistant warning.
- Touches: lineage, inbox.
- Fate: later.
- Read: **seat** for lineage on each unit (cheap now, impossible later); offer itself **content**.
- Evidence: checked.

**T53. Self-test card per version; PASS or FAIL before live.**
- What: Contract tests, replay, scenarios, placeholders left. "How do they know that the things are correct?"
- Source: `X1-H21`; his D43; `b-build-and-prove` (built).
- Touches: card, Library.
- Fate: core.
- Read: **seat** for the card; what passes is **other session.**
- Evidence: built analogue.

**T54. Deployment controls as important as logic.**
- What: Knight Capital lost over $460 million in 45 minutes from dormant code. Versioned releases, remove dormant code, controls that stop bad flow before the market.
- Source: A4-034 (SEC order via assistant).
- Touches: DevOps, placeholders rip-out, kill.
- Fate: not a named row.
- Read: **seat**: a rip-out check that placeholders and dead versions can't linger on a node. `tools/qml/placeholders.py` is a start.
- Evidence: live failure, regulator's order.

**T55. Migration of stored shapes and config-effective timing.**
- What: Every stored shape has an upgrader chain (built). Edits take effect at a declared moment (Gen 3: next period open). A bump of compiler format moves fingerprints.
- Source: `G8` 3.7; A4-040, A4-102; `SPINE` 4.9.
- Touches: compiler format, upgraders.
- Fate: core.
- Read: **seat.** Format bumps cold-start block state; at 200 live units "nothing is live, so a cold start costs nothing" stops being true.
- Evidence: built.

### E. Agents' doors (agent jobs are H-agents' session)

**T56. A read door and a proposal door, and the guard's arithmetic no agent can reach.**
- What: Read rows carry state and receipts. Proposals are typed, expiring, with evidence; cuts apply inside bounds, loosening is a card. Direction on every operation. This is what monitoring 200 units sits on, including catching "the unit whose edge was never real" (M49).
- Source: `X1-H49`, H50, H52, H53, H55; Steward; `SPINE` 4.8; `X6-38`.
- Touches: catalog `direction` field, evidence rows.
- Fate: core thin; `accepts_evidence` empty.
- Read: **seat**; jobs are **other session (agents).** `X1` collision 19: tighten-only ratchets a unit down, which is his sitting duck. Unsettled.
- Evidence: paper-account forward runs by authors.

**T57. New-block door for agents.**
- What: `blocks_save`, `blocks_contract`, `risk_derivation_new`. Today no row saves an entry; `blocks_check` doesn't run the contract.
- Source: `G8` 4.3, B8; `X1-H53`, `SPINE` 4.8; `CHECK` should-fix 9.
- Touches: tool rows.
- Fate: mostly later.
- Read: **seat.** Without it "the unit is what agents' ideas become" stops at drafts he hand-saves.
- Evidence: gap verified; `blocks_check` real at W.

**T58. Ledger as the source of truth.**
- What: Variables with level, derivation and couplings; a check script; a compile-time snapshot in the unit; `affects` edges typed down or up.
- Source: `X1-H65`, H35, A4-098, A4-099, A4-100 ("coefficients configurable, relationships law"); `RC\ledger\v1`.
- Touches: layer H, Numbers tab.
- Fate: core check; runtime edges dropped ("too much machine").
- Read: **seat** for layer H. "Who releases a snapshot" is open (`X1` collision 10). The July phrase is worth keeping as his canvas rule: relationships fixed, values free. But under the lens even a relationship can be a swapped derivation.
- Evidence: built script for planning only.

### F. Observability and DevOps

**T59. One fold, many readers: `RiskState`.**
- What: The node reports health, not risk, today. One fold over journals gives money, exposure, each brake's distance, trading state, profile version. Node, PC, Lab, MCP run the same library, so numbers can't disagree.
- Source: `X6-01`, X6-37, R1, R4; Kubernetes status.
- Touches: journals, guard.
- Fate: core.
- Read: **seat.** The row must be pod- and tag-scope ready, not only unit, group, account. Marked equity is its weak link.
- Evidence: Gen 3 docs; unit-build journals built.

**T60. His six words made exact, plus UNKNOWN.**
- What: UP, ON, TRADING, RIGHT, WRONG, TRIPPED; each a checkable statement; a stale input shows grey. Dark when normal.
- Source: his "working, it's up, it's on... trading" (D49), `X6` section 1, X6-11.
- Touches: UI, agents' reads.
- Fate: core.
- Read: **seat** for predicates; surfaces **other session: UI.** SPINE's two word lists differ: C1's kill colours as `word`, C2's his six. The fold took colours and dropped his words. Worth restoring (my read).
- Evidence: control-room practice.

**T61. Decision trail, trace id, three weights.**
- What: Wanted size, each step with its reason, binding clamp, approved, filled. One id from reading to fill. "Explain this size" in ten words.
- Source: `X6-03`, X1-H76, X1-H54; A5-75.
- Touches: decision row, sizer receipt.
- Fate: core.
- Read: **seat.**
- Evidence: production practice; author backtest.

**T62. Trade row v2: mechanism apart from outcome; `net_r` by the true form.**
- What: Today a time exit, a signal and a cut all read `close`. Check found the first `net_r` definition double-counted spread.
- Source: `X6-04`, X1-H59; `CHECK` B1; `SPINE` AD-12, 4.6.
- Touches: `journal_kinds`, motion engine.
- Fate: core.
- Read: **seat.** Costs as measured observations fit M51 exactly.
- Evidence: built kind fields.

**T63. Closed reason codes at source.**
- What: A risk stop filed as a kill switch because text is matched. Emit codes, and delete the map. Each red adds a cause class.
- Source: Nautilus (`R1` 6.1), `X6-06`, X1-H61.
- Touches: `REASON_CODES`, QMB.
- Fate: core.
- Read: **seat**; new code families must be data rows for user-added blocks.
- Evidence: bug verified by G9.

**T64. Requested, enforced, observed.**
- What: A click shows who asked, what the node enforced, what the PC saw. Includes his lowering (not journalled today).
- Source: `X6-09`.
- Touches: kill, controls.
- Fate: core.
- Read: **seat.**
- Evidence: Gen 3, Kubernetes.

**T65. Cost cell: assumed against realised per instrument, hour, broker, order type.**
- What: "I'm not trying to remove them... I'm trying to observe them" (M51). Fill writes both; sizer reads the cell; a measured cell can refuse.
- Source: `X6-30`, X1-H63, M51.
- Touches: facts, record.
- Fate: core.
- Read: **seat.** He ruled fees part of the technical lens. Paper's zero slippage is a known hole (`X6` collision 8).
- Evidence: author backtests.

**T66. Alert tiers, wake contract, incident funnel.**
- What: Silent act, digest, ticket, page. Wake only if money is at risk, the system can't fix it, and his action matters. One root cause, one page.
- Source: `X6-14`, X6-16, X6-17; A4-157, A4-160, A4-201.
- Touches: alarm register; UI design already has "What wakes him" (`UI-NOTES-UNITS.md:185`).
- Fate: core, Q7.
- Read: **other session: UI and notifications**, with a seat for an incident key on each row. At 200 units this is what makes monitoring bearable.
- Evidence: SRE and process-industry practice. Delivery ack missing.

**T67. Family alarm budget across units.**
- What: Per-unit thresholds multiply false demotions as units grow; share a false-alarm budget.
- Source: `X6-25`, A2-152.
- Touches: drift monitor, group; 200 units.
- Fate: later (go-live; few units assumed).
- Read: **content** with high value at his scale.
- Evidence: proofs and simulation; overlapping trades break independence.

**T68. Brake scorecard, trip tax, sitting-duck meter, earned keep, growth waterfall.**
- What: Fires, precision against a random brake at same rate; what brakes cost and saved; share of hours below baseline. "This week brakes cost 1.8R and saved 3.1R."
- Source: `X6-21` to X6-24, A4-202.
- Touches: shadow twin rows.
- Fate: shadow or later.
- Read: **content**, but a seat in `would_have` bodies (open at W). The copilot needs them to tune a pod.
- Evidence: counterfactual; simulated fills warning.

**T69. Observability observes itself; DevOps stacks unresolved.**
- What: Heartbeats for watchers; node and PC checksums compared; chaos drills on demo. Liveness watched from outside. Two stacks ship, telemetry off by default, DEC-0212 against host OpenObserve; retention on a VPS at scalper rates unknown.
- Source: `X6-40`, X6 collisions 7, 9, gaps 7; A4-169; `X6` section 3.
- Touches: node, deploy.
- Fate: later.
- Read: **seat** for "risk rows are evidence, may not drop". Stack choice is his (`X6` Q4), not yet ruled.
- Evidence: Knight; controlled evaluations.

**T70. Exit capacity and locked heat; stress gauge.**
- What: Risk in a position you can't exit is shown apart; worst plausible move now against room.
- Source: `X6-20`, X6-35, Lab stress.
- Touches: RiskState field; shares maths with Lab.
- Fate: later.
- Read: **content** with a reserved field.
- Evidence: SPAN practice.

### G. Maintainability for a developer, and things to drop

**T71. What's on disk for maintainability, scattered.**
- What: Deep interface of a few verbs (`X1-H20`: `decide, on_event, state`; `SPINE` 4.4: six methods) with the deletion test; ports with fakes; conformance tape in CI; property test on rank; census test per schema field; `Windows first-class`; Lab's import rule ("arrows mean may import"); one catalog row per tool; closed vocabularies; PR sized by reviewable job.
- Source: `X1-H20`, `SPINE` AD-2, AD-17, AD-20, section 10; `candidate-2`; LP Consistency Conventions and Structural Seed; `G8` 3.8.
- Touches: all.
- Fate: pieces core.
- Read: **seat.** No single developer guide exists; see gaps.
- Evidence: built tests partly.

**Drops, with reasons:**
- Central risk oracle (`X1-H69`, RiskGate): breaks "nothing a unit needs may depend on anything outside at trade time"; same pipeline already sits in the guard. Dropped on rulings, not dollars. **Drop stands.**
- Runtime `affects` edges (`X1-H71`): too much machine. **Drop stands**; compile-time check keeps most of it.
- Permission controller (`X1-H75`) was dropped on funnel grounds. **Content** if someone wants it; nothing needs it in core.
- Virtual positions netted (`X1-H74`): **content or later**, placeholder 21 is related.
- One-tone sound map (`X6-47`), observability budget (`X6-46`), attention telemetry (`X6-26`), vital signs (`X6-44`): **UI session or drop.** Low value.
- Marketplace (`X1-H78`): **content**, depends on T20, T33. His "someone else can use QMX" makes it less silly than "wild" suggests.

---

## 4. Designs and overhauls already proposed for this area

| # | Design | Buys | Costs or conflicts |
|---|---|---|---|
| 1 | **One guard above the unit** (C1, C2, fold) | One rank table, cross-unit brakes native, one place to test | Refuses five shipped halts; every brake needs the guard version |
| 1b | **Unit carries its own brakes, guard holds only cross-unit** (C3) | Unit stands alone; same code in QMB and node; shipped halt family used; a scalper's brake travels with it | Two stages; cross-unit brake needs a kernel PR |
| 2 | **Learner and applier now** (C1) | Numbers can move between anchors; he sees bands | More fields; little gain on a healthy unit in the model |
| 2b | **Refresh at anchors** (C2, C3) | Nothing moves unexplained | A learned number can be a day stale; all numbers move at once |
| 3 | **Status file** (C1, fold) | Simple recovery | Windows `os.replace` raises under a reader (`CHECK`) |
| 3b | **Journal rows only** (C2) | One source of truth | Record holes; slower recovery |
| 3c | **In R22's snapshot** (C3) | One file | Logic and risk state die together |
| 4 | **Pod compiles to Book plus BMS** (LP AD-11, OPEN-1) | Works with old documents; `unsupported_blocks` honest | Predates units; Book and BMS docs may go |
| 4b | **Pod compiles to profile and group; Lab is a producer** (`X1-H33`) | One target | Lab and template unbuilt on both sides |
| 4c | **Pod blocks compile into socket blocks** (placeholder 31's question) | Pod and unit share one block world | Cross-unit slots have no home inside a unit |
| 4d | **Pod is a mini app bundle** (`X1-H30`) | Shippable, signed | "Pod" means several things |
| 4e | **Pod is a hedge-fund department of agents and mini apps** (M50: "I think") | Specialization, his vision | No design on disk |
| 5 | **Book and BMS stay as documents** (A4-092) | Fewer new words | No intersections |
| 5b | **Tags plus portfolio config** (`X1-H40`) | Driver clusters; one floor | New words; unproved |
| 5c | **`group` with `parent` reserved** (C2, fold) | Leaves it open | Defers, and a pod level isn't placed |
| 6 | **Trading states map onto kill levels** (`X1-H10`) | One vocabulary | Kill stays his; P15 options |
| 6b | **Kill as a fact, states separate** (fold) | Safe by type | Two machines on one node |
| 7 | **Target rests at venue** (C2, C3, fold) | Backtest equals live on a wick | Amend may wipe the stop until R24 proves otherwise (`CHECK` B6) |
| 7b | **Node closes** (C1, DP26) | Works today | Backtest and live differ |
| 8 | **Exits in profile** (C1) | One document | A profile change moves R |
| 8b | **Exits on unit, numbers in profile** (fold) | Record protected | Two places |
| 9 | **Three verbs** (`X1-H20`) vs **six methods** (`SPINE` 4.4) | Three is smaller | Six separates recover, advance, sizing |
| 10 | **Sizer base as derivation** (C2) vs **wide sizer inputs** (C1, C3, plan's slot table) | Thin socket; new base is a row | Plan's CONTRACTS section 4.3 promises wide inputs; a new base can't read position state without facts |
| 11 | **Ledger-generated UI** (`X6` R6) vs **hand screens** | Add a brake, get its meter | Ledger is a design file today |
| 12 | **RiskState is evidence, never drops** (X6) vs **VPS disk at scalper rate** | Audit | Unmeasured |
| 13 | **MIS fails open, isolation closed, evidence neutral** (fold) vs **a guard failing closed against an open board** (`X1` collision 9) | Stated together on preflight | Still inconsistent to a reader |
| 14 | **Prometheus and Grafana (DEC-0212)** vs **OpenObserve** vs **journals as risk source** (`X6` P12) | | Unresolved |

Overhauls of QML and the unit proposed so far are in T12 to T23: new roles, `reads`, `plain_python`, format bumps, and `sizing_modifier` actually changing size (22 blocks claim the role and can't today, `G8` 3.4). I found no redesign of QML's language itself on disk.

---

## 5. What the unit baseline must carry because of this area

| Must carry | Why | What breaks if missing |
|---|---|---|
| Spec and status with generation stamp | T1 | Old state sizes a trade; edits race |
| Number shape: derivation, ladder, authority, range, owner, why, cautious direction, receipt, reason code, room for `behavior` | T2, T24, T27, T28 | "Change how it's derived" needs code; blanks; rework |
| Sizer split: dollars rule, then converter over the record | T4 | Every new base changes the socket; lots mindset; USDJPY returns |
| Fact surface for sizer and exits, with timestamp and fail mode | T18, `SPINE` 4.3, 4.6 | Sizers stay starved; halts silent |
| Exit socket with `PositionFacts`, several per-bar exits, shorts | T13 | Dictionary's closing mechanisms stay dead |
| Halts able to bind, at least where reads are satisfied | T6 | Five blocks useless; unit-level brake must go through the guard |
| Row contract: answers, verbs, placement, mode, reads, numbers, restore, block state, reason codes | T6, T19, `CHECK` B9 | "New brake, no code" false |
| One seam both hosts call, one wrapper | `SPINE` AD-4 | A guard failure stops exits (`CHECK` B3) |
| Group level with display name, parent, allocation mode, rank, scope keys, tag key, once rules | T5, T36, T37 | Every pod question becomes code; capital rule is a law |
| A placed answer for each pod slot, and a pod reference on the unit or deployment | T3, T38, OPEN-1 | Lab can't compile; recut stalls |
| One evaluator for Lab and live | T38 | Lab size differs from live size |
| One block catalogue, with a lander for `component`, profile, group | T33, T39 | Pods can't ship; two block worlds |
| `reads` path from published readings to a unit | T43 | MIS and pods can't reach units beyond one board |
| Pin plus diffs plus lineage on each unit | T9, T52 | Silent breaks; can't upgrade 200 units |
| Identity rows plus forwarding map; two records | T48, T49 | Placeholder swap costs each unit its record |
| No dependence on a QMB card | T7 | Lab and mini-app units are refused or misread |
| Needs list and two-adapter contract tests per class | T18, T22 | Silent no-ops; class bugs |
| Deployment budget share | T44 | All units size from whole account; check it isn't lost |
| Rollout field and adoption rule | T51 | No canary without schema change |
| Decision row, trade row v2, `would_have` bodies, reason codes as data, `RiskState` by scope including pod | T59 to T63, T68 | Agents can't monitor 200 units; replay impossible |
| Read and propose rows with direction; save-block and contract rows | T56, T57 | Agents stop at drafts; or reach further than they should |
| His door for risk kinds | `CHECK` B4 | An agent can publish a lower floor |
| Instrument record: conversion market, cost keys, class, day boundary | T15, T65 | Costs absent; crosses wrong |
| Windows rules | `SPINE` AD-20 | `tzdata`, `os.replace` faults |

---

## 6. Gaps: what he asked for here that nothing I read answers

1. **Pod ideas and configurations.** "I remember asking you to see if you could figure out some pod ideas or configurations" (M49). Nothing I read proposes any; X1 mentions pods 12 times, all structure. Other expansion files mention them a few times each (count only, not read here).
2. **Unit plus pod as one design.** "That's why we made a system that has a baseline with a customizability layer." `REVIEW` names the recut as open. No architecture version shows it.
3. **Pod as a department.** "you are looking at a mini app that is optimized for futures... I think in a hedge fund, that's called what? A pod" (M50). Not designed; note his "I think" (M51). Word clash with the Lab's pod is unresolved.
4. **A working first day for a newcomer.** "Someone who hasn't been part of developing KMX can use tomorrow to have their own system trading" (M49). No document walks install, pick preset, get a unit, paper, live. Extension walks are written for builders.
5. **Maintainability.** "it's maintainable, please. From a developer's perspective, there are lots of things you were meant to add. I don't know how you didn't do this" (M52). Only scattered pieces (T71). No guide, no module map for the whole template, no contributor path.
6. **"Why lots?"** Structurally answered (T4), never answered to him, and `Size.lots` stays in every contract.
7. **A file format for the unit.** "You can even have a file format for it. I don't care. Now, a file extension for it." (M50). Nothing beyond `qmx.unit/1` JSON.
8. **Copilot making templates with QML.** "the Copilot is taking what you are going to give me using QML to make the unit maybe templates for a scalper" (M50). `unit_new` with one dummy template, no skill such as `build-risk-profile` built. No walk of a copilot week on futures.
9. **The hill-climb on self-configuration.** "Maybe double check, triple check... Have an agent go at it. More of a hill climb challenge" (M49). No agent attacked self-configuration itself. `X1` gap 8: no fair control for a learner and applier.
10. **Architecture overhauls beyond the unit.** "designs for the SQS systems, MIS systems, newer designs or enhancements... even QML itself" (M52). In my files: QML additions only, SQS relocation only. Check the SQS and MIS harvest for the rest.
11. **Other versions of the pod.** "can't we figure out other versions?" (M7). `SEEDS:1392` says not addressed.
12. **How agents know it's correct, for a brand-new block.** "How do they know that the things are correct?" Contract tests and cards cover shape, while methodology is a separate session, which he ruled.
13. **Multi-position units and "flat".** "several positions per unit" (`SEEDS` lens 19); `position_limit` stays 1; "flat" undefined (`X1` gap 2). Scalpers holding gold and NAS together hit this.
14. **Timing of a mid-session value change, in money** (`X1` gap 1), **a roll as a version event** (gap 4), **a persisted record for a tag** (gap 5), **applier telemetry** (gap 12), **VPS retention** (`X6` gap 7). Raised on disk, unanswered.
15. **Monitoring 200 units as a mini app.** "Why not just have an agentic workflow... As a mini app" (M49). Doors exist on paper (T56, T59). The app itself belongs to the agents' harvest; check it there.
