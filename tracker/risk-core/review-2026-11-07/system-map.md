Read at build/repair-24, 255f3bbf, the newest code tip (17:53, 7 Nov). I read only. The `how` skill calls for subagents, but your brief bars them, so I ran its roles myself.

Paths: W=D:\QMX-worktrees\bld-repair-24, S=D:\QMX-worktrees\repair-ship, U=D:\QMX-worktrees\unit-ship, A=D:\QMX-worktrees\audit-ship, P=D:\QMX-worktrees\unit-plan\tracker\risk-sizing, RC=D:\QMX-worktrees\risk-plan\tracker\risk-core.

**Headline:** the chassis is real, but the risk half mostly does not run. One sizer, one stop, one target and one time exit run. Halts, the six other exits and the guard do not. "60 percent" cannot be measured from anything I read. "Icing" undersells it, because sockets must change, not only blocks.

## 1. A unit today
| Step | Fact | State |
|---|---|---|
| Written as | One JSON document, `qmx.unit/1`; model `W\qml\src\qml\unit\model.py`, generated schema | Built, proven |
| Slots | 18 roles (`model.py:89-109`), 7 run (`compile\compiler.py:107-117`). `sizer`, `exit_set` and `halts` are separate fields | Partly built |
| Compile | Format 4 refuses whatever cannot run (`compiler.py:896-1014`): reads, halts, sessions, context, routes, plain Python, roll, per-market settings, more than one position or stream, non-time bars, quotes and ticks. 17 block pins are refused (`:120-138`) | Built, proven (R04) |
| Python | A block is `entry.json` plus `block.py`. Agents check one with `blocks_check(entry, source)` (`qmx_tools\functions.py:1106`). The unit-level `plain_python` is refused (`compiler.py:924-929`) | Blocks real; plain Python missing. I did not trace a Library block through to compile |
| QMB | `qmb\host\unit_handler.py`; runs through `qmx_host\host.py` | Built. The audit matched 63 of 63 decisions against the node on synthetic bars, before the repair (`A\MORNING-REPORT.md:28`). R08 and R09 real-data lanes still owed (`S\STACK-LIST.md:70`) |
| Node | `qmn\app\runtime.py`, 3,161 lines | Built, proven on a fake broker only: 12 of 12 walls (`S\STACK-LIST.md:50`). Never run against a real broker |

## 2. Risk and sizing state
**What sizes a trade**
- Only `fixed-fraction-at-stop@1`, called at `W\qml\src\qml\protocol\unit.py:785-793`. It reads equity, entry, stop and record only.
- `block.py:52-53` divides account money by a quote-currency loss. The audit calls this wrong on USDJPY (`A\REPAIR-SCOPE.md:134`).
- The receipt residue is the literal `"0/1"` (`unit.py:829`).
- Sizer inputs are refused (`compiler.py:930-936`).
- QMB equity moves with trades (`unit_handler.py:372`). The node's equity call sites I found are at start (`runtime.py:1614,2843`). The hand-off says the balance is read once at sign-in (`RC\handoff\FOR-REPAIR-SOCKET.md:57`). I did not trace further.

**What stops trading**
- The stops are in `Runtime.guard` (`runtime.py:2623-2675`): kill level, pause, withdrawn, journal failure, MIS board, venue not ready, reconcile, orphan position, stand-downs. It has no spread or news check.
- Other stops: `effect_matrix.py:137-146` (placeholder), `risk_stop` (`runtime.py:2696`, no producer per the hand-off), and the stop gate (`:1102`).
- The hook passes everything (`runtime.py:1100,1148`).
- `qmn\capital\kill_line.py` is not called from `qmn\app`.
- The old SQS gate lives in the old node (`decision_root.py:493-510`).
- `packages\qmf-risk\...\guard` does not exist.

**Hand-offs, all of them**
- `P\build\RISK-SIZING-PLACEHOLDERS.md:17-47`: 31 rows, plus slot contracts and 4 questions.
- `P\build\repair\plan-parts\90-appendices.md:184-207`: Appendix F.
- `A\REPAIR-SCOPE.md:134`; `A\FOR-HIM.md:17-19`: SQS, flatten/RED, R and costs.
- `U\RISK-NOTE-2026-11-04.md`: the signed stop. Its delivery failed, per `RC\grounding\G12...:133`.
- `RC\grounding\G12-audit-and-repair-for-risk.md:34-112`: 37 items, the fullest list. It also names findings never filed (`:142-145`). It predates R14 and R17-R24, so its lines are stale.
- Code markers: `compiler.py:362,505`; `runtime.py:37,181-187,1357`; `qmn\app\server.py:321`; `qmx_judge\judge.py:253`; `qmf\risk\unit_intent.py:16`; four block docstrings.
- Agent-held demo positions need a `foreign` scope (`RC\handoff\FOR-REPAIR-CLAIMS-BEFORE-C20.md:25`).

## 3. Making and changing units
| Thing | State | Evidence |
|---|---|---|
| Copilot tools | Real | `unit_new/check/explain`, `blocks_*`, `backtest_*`, `library_save`, `propose_order` in `qmx_tools\functions.py:632-657,843-887,1131-1134`. R14's live check: a chat on haiku builds, checks, backtests and gets a verdict |
| Hooks | Real, narrow | `qmx-agents\plugin\hooks\hooks.json`: "After a Write or Edit of a unit document... run the QMX unit checker" |
| Unit templates | One only | `qml\unit\templates\dummy-trend-pullback.json` |
| Presets | Judge only | `qmx_judge\presets.py`: pass thresholds. No risk preset exists; `role: preset` is only in the set-aside `RC\architecture\SPINE.md` slice 3 |
| Workflow templates | Real | `qmx_engine\templates\` (`rk2`, `rk5`, `dc-decay`, `p1`, `pp`, `b-build-and-prove`). I did not run them; G12 says `rk2`, `rk5`, `p1` and `pp` drafts wait on risk data (`:101`) |
| Mini apps | Real | `qmx_apps`; `manifest.py:234` risk is shows, runs or money; `:61-64` only the trading node holds grants. A mini app "cannot sit in the money path" (G8:21) |
| Library kinds | Unit real, others shells | `unit.schema.json` is 42 KB. `template`, `bms` and `book` are about 700 bytes. `pod` is `"slots": {"type": "object"}` |
| Lab | Real workspace, no pods, no copilot | `qmx_control\lab.py:22`: "Pods are not part of this backend (Lab AD-10 to AD-12 stay designed and unbuilt)"; "on no model's surface" |
| Pods | Design only | `D:\QMX-worktrees\risk-plan\tracker\qma-v2\architecture\lab-and-pods\` (1 Nov), seven slots. The UI is a demo |

## 4. Order flow and costs
**Order flow:** no data path exists.
- `A\FOR-HIM.md:27`: "has no plan and nobody is working on it."
- Dictionary pages only: `W\qml\catalogue-seed\wave-1\beyond-fx\` (`bar-delta`, `stacked-imbalance`, `depth-bands`).
- Databento is a key probe: "one metadata call proves the key" (`providers\databento.py:1`).
- My search found no cTrader depth subscription.
- Futures: `futures_feed` is unwired (`U\BACKLOG.md:244`); roll is refused (`compiler.py:938`).
- The enums `tick`, `volume`, `quotes` and `ticks` exist but are refused (`compiler.py:976-987`).

**RVOL blocker:**
- `QuoteBar` carries bid and ask OHLC and no volume (`unit.py:120-125`).
- Compile says "volume, which no bar carries yet" (`compiler.py:118`).
- `relative-volume.json` has no stdlib block and says the runtime "does not yet pass a bars input its volume or its time".
- Nobody owns this.

**Costs and observations:**
- QMB charges cost profiles (`qmx_host\host.py:2034-2185`). Instrument records hold margin, swap and conversion.
- MIS has `spread_state@v1`. R19 plans the `minute` journal rows (`repair\plan-parts\r19.md:27`); the only file my search matched was `qmn\app\feed_keeper.py`, and I did not read it.
- **But a unit or rule cannot read any of it:** `reads` is refused (`compiler.py:900`) and the sizer gets none.
- News: the `calendar` tool and `t3-news-calendar-watch` exist. `qmn\data\news_calendar*.py` is not imported by `qmn\app`, and the risk session has claimed it to keep.

## 5. Shipping
- **Merged:** `engine/base` at c93407ca, last merges 31 Oct. `build/repair-24` is 691 commits ahead.
- **Stacked, 0 merged:** 94 `build/us-*` PRs plus R01-R24 (PRs #329-352), 118 in one line. `gh` shows 120 open; the other two are `base` and `wu4` branches I did not inspect. All 24 gates pass (`S\STACK-LIST.md:51,76`). Every branch from R05 on must be squashed (`:5`).
- **214:** this count appears only in his own words (`RC\seeds\operator-words-2026-11-06.md:72`). Documents give 73, then 91 sections (`P\CLEAN-HOUSE-CONTEXT.md:18`), then 94, then 118. 30 must plus 184 should findings (`A\REPAIR-SCOPE.md:26`) also sum to 214, which may be coincidence; that link is my inference. SPINE's estimate of 43 risk PRs would make 161.
- **In flight:** the whole-repo run at the tip had no result when I last read it. Read `S\evidence\whole\fix-tip\SUMMARY.txt`.
- **Unbuilt:** C-19, C-20 and C-21 per `A\REPAIR-SCOPE.md:105-107`, written before the repair. I found no later sign of them, but did not search for one.
- **Frozen:** per memory, the build froze on 4 Nov, then repair ran on DeepSeek. No PRs were added.

**What blocks starting today:**
1. Risk slices "start on landed tips" (`FOR-REPAIR-SOCKET.md:82`). Nothing has landed, the landing branch is his call (`A\FOR-HIM.md:7`), and merges need his word.
2. He rejected the template. The recut around unit plus pod waits for his go (`RC\REVIEW-2026-11-07.md:42-44`).
3. Demo sign-in is pending, so R24 lanes 5 and 6 cannot run (`S\STACK-LIST.md:60`). Stop moves and resting targets need those facts.
4. I found no reference to either hand-off in repair's top-level notes, decisions, dispatch or plan. No amend question appears in `dispatch\r24*`, `first_real_start.py` or `proof_foundation.py`. I could not locate a separate demo-probe file. `RC\STATE.md:20` still lists passing them on as a next step.

## 6. Smallest true list
**For risk and sizing** (technical only, no policy or numbers):
1. Sizer socket: costs, record and conversion inputs, the receipt residue, a real sizer in place of the placeholder.
2. Exit socket: position facts, per-bar exits, side-correct exits (`timer()`), lift the refusals. Then trails, partials and the signed stop, after the demo facts.
3. Halts: a host that runs them and computes their statistics, then lift `halts_not_built`.
4. One guard seam in both hosts, replacing the hook, where a guard failure can never stop exits. Fact feed: live equity, margin, conversion quote, spread.
5. Template and customization layer: more than the dummy, plus the pod shape. Open: where each slot runs at trade time, and how the guard hosts throttles and caps (`REVIEW:44`).
6. Records: `net_r` and `gross_r`, exit mechanism, risk event kinds, reason codes.
7. Moves before C-20: SQS, the news window, the kill table, and the claimed files.
8. Target resting at the venue, once R24 answers.
9. Stronger socket contract tests, then rip out placeholders using `tools/qml/placeholders.py`.
10. Agents monitoring many units as a mini app or workflow, which `REVIEW:44` requires in the recut.

**Others'**
- Agentic upgrade and QMA: including the `foreign` positions flag.
- Methodology: `A\RULINGS-NOW.md:114`.
- UI: `UI-NOTES-UNITS.md:236`, "No separate risk screens".
- Repair: finishing its stack.
- C-19 and C-21.
- The numbers argument, which he placed after the technical work.
- Unowned, needs his call: volume on bars, order-flow data, futures routes.

**Disagreements and uncertainty**
- `blocks\api.py:198` says "No host calls it yet", but the node has its own stub. Placeholder row 6 says the hook sits in QMB too; my search found no call there.
- Placeholder row 12 says residue is recorded; the code writes a literal.
- Placeholder row 17 says equity is balance plus unrealised P&L, while `FOR-REPAIR-SOCKET.md:57` says balance read once. Unresolved.
- Appendix F seats SQS in `Runtime.guard`; `FOR-REPAIR-SOCKET.md:47` puts it in the guard package. "The risk session needs nothing" (Appendix F) conflicts with "agree the socket first" (`A\REPAIR-SCOPE.md:76`).
- `S\STACK-LIST.md:66`: the skill's build order differs from plan line 1266.
- The pod doc compiles to "Book and BMS" (`PLAIN-WORDS.md:23`), which predates units and is possibly stale.
- `REVIEW`'s quote "Several throttle and cap blocks..." is not in `PLAIN-WORDS.md` or `ARCHITECTURE-SPINE.md` under my "risk session" search; I did not search the LLD. `:23` says something similar.
- SPINE's 43 PRs and its slices may not survive the recut.
- G8 read an older tip, but what I re-checked held: the dummy is the only template, and the pod kinds are shells.
- Not read: full `UNIT-PLAN.md`, `qmf-readings\liquidity.py`, `U\QUEUE.md`, `U\LOOSE-ENDS.md` beyond a search, `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair\apps\qmx-ui\UI-BACKLOG.md` beyond a search.
