# Open items, the default the build runs on, and who decides

Nothing here waits. Every row has a default and the build continues on it. "Him" means the account owner's word or click. Sources: `round-2/funnel/QUESTIONS.md`, `round-2/arch/COMPARE.md` section 6, and this fold's own assumptions.

## His calls

| # | Item | Kind | Whose | Default the build runs on |
|---|---|---|---|---|
| 1 | **What a pod is.** A recipe stamped into units plus a thin group (this fold), or one live document that governs its members (V2). He said he would go through every overhaul (M56); this is the biggest | Scope, his words | Him | This fold. Decide by stop point B (end of slice 11); everything before is shared; `SPINE.md` section 12 prices the switch at about 4 to 7 more PRs |
| 2 | **One click per pod edit (Q6), and does that click cover a stage move up later, by rule?** | Fixed line (only he promotes) | Him | One click per plan hash covers every member and every declared stage; a stage move **up** lands a card by template default, **down** moves by rule; `move` is one field per direction |
| 3 | **An agent's de-risk reading (Q4):** does a cut inside declared bounds cross "agents never touch money"? | Fixed line | Him | A card. If he says it does not cross, the card becomes a cut-only reading inside declared bounds with expiry; raises, new markets and kill levels stay cards either way |
| 4 | **Demo sign-in, and may the probes run on his demo account (Q1)** | His account | Him | Fake broker; slice 17 (signed stop, amends, partials, trails, venue targets) and real cost calibration land after; everything else before |
| 5 | **Data he would own or pay for (Q2):** volume or tick count on bars, order flow, a futures route | Money, scope | Him | FX and gold through cTrader; tick count from quotes; no paid feed; no futures route, so `roll` stays refused and the futures week is written up as what it still needs; record fields reserved so adding them is rows |
| 6 | **Landing branch (Q5)** | His click | Him | On `engine/base` after repair's stack; `main` moves only by his squash-merge |
| 7 | **The word "desk" (Q3)** | His words | Him | "desk" in code, "department" on screen; "pod" unchanged; "Book + BMS" stays a method name |
| 8 | **Do the three stop points stand as places he may stop?** | Scope | Him | Yes: A after slice 5 (one unit trades on paper), B after slice 11 (whole single-unit baseline), C after slice 16 (groups, pods, shipping). Slices 12 to 16 are opt-in |

## The build's own defaults on things not measured

| # | Item | Default | Reopens if |
|---|---|---|---|
| 9 | Real send times at a bell, exit and entry (F1, F10) | Fake broker; meters as plain rows; serial sends accepted | Demo shows send delay harming fills: sends off the thread, or a thread per account |
| 10 | Compile time per member on a roll (about 746 ms median in V1's probe; 150 s per 200 on one worker, unmeasured at scale) | One worker on the node; several off the node | A pod edit's wait is complained about: a worker pool on the node |
| 11 | Whether a Library block reaches a live node end to end | Traced in slice 14 before "one folder, zero core edits" is promised | The trace fails: a stdlib path with his signature until fixed |
| 12 | Whether `unit_check` accepts a shipped instrument record (E5 G8) | Templates ship records labelled `source: shipped`; `unit_check` accepts them | It cannot: a core row in slice 5, said plainly |
| 13 | G's wall time per unit for K8 (COMPARE: about 17 minutes per 200 on one core for the dummy on 2,000 bars) | A worker pool for the re-test batch; the bump refused at the node until the report exists | Minutes per unit on real blocks: schedule nightly, never inline |
| 14 | A worker thread suffices to budget Python block code on Windows (G2) | Chain links and control rows wrapped in slice 10; the unit's bar step wrapped once tested | A C call holding the GIL defeats it: V3's worker process per pod is the named next step |
| 15 | 200 unit versions per pod edit are acceptable to the Library | Yes; storage per version is one document | Storage or listing slows: compact old versions, keep the plan's hash list |
| 16 | Snapshot writes on every control state change at 200 units | Control words come from the fold; the snapshot is a cache written on calibrated moves and at anchors only (G9), so no new write storm | The cache proves stale on restart: write on state change too |
| 17 | G's behaviour half is not re-required under a new risk section (Q6 default) | A pod edit costs the safety half only | He rules otherwise: a G run per member per pod edit, and the fingerprint split pays for itself less |
| 18 | Herding of sizes on a volatility shift (E5 tested filters only) | A `scaled` size cuts together, which is probably right; the fold reports `move_share`; a group total-risk cap catches a joint press | Sizes herd harmfully: a retune share cap as a shipped group row |
| 19 | Whether `execute_resting`'s `Ok(False)` path holds for a parked entry past a bar (F7) | The parked-entry fix in slice 11 with its own test | It does not: a `parked` state beside `Unknown` in `_orders` |
| 20 | Real throughput with journals and a venue at 200 units | V1's probe covers QML only (55 to 60 ms per 200-unit step) | Measured on the fake broker in slice 12's 200-member test |
| 21 | Exit code's import test on Windows path handling | Parses imports from source; no runtime import | A dynamic import slips through: add a runtime guard in `run_budgeted` |

## Hand-offs to other sessions

| To | What |
|---|---|
| **Methodology** | How a unit is proven valid per type; whether a logic record under a changed risk part is the same trades (F11, with would-have rows as the evidence); the judge rule for with-and-without motion and fixed size; canary and rollout rules; how much proof a market, window or reading needs; what "better" means in a hill climb; the harness for worst, realistic and best runs |
| **Agentic upgrade** | Who runs the fleet watch's agent layers, Shepherd, departments, memory; whether a de-risk reading may apply itself (after his Q4 answer); the `build-mini-app` and `build-pod` skills; the triage job and cause list; replay of past runs; skills that speak of one person; the copilot taking raw video; E5 section 6's nineteen flaws |
| **UI** | The data list in `SOLUTION.md`; the size trail panel; stickers and "why didn't it trade"; the pod gallery and the empty pod; one fleet screen at any size; "Needs you" fed by apps; the kill line as a warning in the largest type; first-run ticks on done, not opened; notifications and phone pushes (M49 Q7) |
| **Numbers talk** | Every labelled placeholder: fractions, floors, limits, k, allowances, strengths, widths, K and the strict bar, budget share, the time budget's length, N for every cold behaviour; the game plan; whether gold's windows hold |
| **Repair** | Claims before C-20: `sqs_baseline_producer.py` and the SQS rule text (`decision_root.py:496-510`), `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `dispatch.py`, `qmf-risk/control_window`; the signed stop distance (`known-1`); R24's demo probes (does a fill carry the stop, does a one-level amend wipe the other, what a close on a gone position answers) |
| **Release** | E5 G1 to G3: an installer a stranger can run, the launcher describing `python -m qmx_host`, the desktop app the first start hands over to |

## Assumptions carried, in one place

`[ASSUMPTION]` tags from `SPINE.md`: Q6's default on G's behaviour half; a stage move covered by the original click satisfies REVIEW M2; 200 versions per edit acceptable; a worker thread budgets block code; shipped records accepted by `unit_check`; a G run per unit cheap enough to batch. Each has a row above with its reopening condition.
