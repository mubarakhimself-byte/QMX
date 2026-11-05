The plan is largely faithful to his rulings, and all 27 additions are justified by the record, but one plan line blocks his first real start and four rulings were lost or softened (SQS, the market journal, one-click server setup, his click toward paper).

Rulings file: `D:/QMX-worktrees/audit-ship/RULINGS-NOW.md`. Finding rows: `D:/QMX-worktrees/audit-ship/findings/plan-check.tsv`. Source short names (R, RC, TR, VAL, US, PC, T) are explained at the top of the rulings file.

## Rulings lost or contradicted

Compaction did less harm than feared. The session of 31 October re-grounded on his files, and the midday rulings reached the plan almost whole. What went missing went missing later, or between the architecture and the plan.

**Blocks his first real start (`must`)**
- Where the code counts as landed. He said "The merge target is decided later; never `main`" (US:282), and PRs 207 to 234 went into `engine/base` (T:1200). The plan roots the stack there (PC:6). C-14 then asks for "the commit on `origin/main`" (PC:3783), and the script refuses without it (`tools/first_real_start.py:567-572`). `origin/main` is from 27 September and lacks 2,277 commits of `engine/base`. No plan line or card tells him to take the stack to main. VAL:13 assumed it. Walked, not run.

**Lost**
- SQS. "Kill switch and SQS stay" (RC:320). The word appears nowhere in the plan, the placeholder list, Level 0 or the node design. The readings moved safely to `qmf-readings`, but the new node has no SQS gate, and C-20 deletes the old one (PC:4173).
- The market journal. "Separate a router journal for market-level facts" (US:219). The architecture kept it (AD-208). The plan only reads it (PC:1812), and no section writes its minute rows. So results say "costs uncalibrated" for good, and the sizer's costs have no source.

**Softened**
- One click. "His only jobs are renting and naming the server and entering its keys in its own window" (R:30). C-17 was not revised for this (PC:4005). The built setup has five cards, Tailscale, a password window, a pasted signature, an app-approval wait and a sign-in (`prs/c17.md:10-22`, `:50`). The ruling reached only C-19.
- The risk socket gives a sizer no costs and no QMB edge numbers, against "they feed Kelly" (RC:342, RC:22). The risk session owns this. It is reported because A15's slot contract makes it persist (RC:290).

**Contradicted**
- His click toward paper. "Every move toward paper or live is his click" (US:46). A9 adds `lifecycle.auto_paper` so the judge may do it (PC:1213). It ships off.
- Tests. "No 'every part must prove itself' machinery, no hundreds of tests" (US:20, R:15). Every section says a PR "is verified only when its unit, live, and perf boxes are all checked" (PC:33), with no size limit. In fairness, he also asked that shipped tests stay green (US:132), and only four lanes plus one menu lane run per PR.

**True but not worth doing (`leave`)**
- C-21's test asks for an engine refusal he said "Not yet" to (PC:4770, VAL:43). It comes later anyway.
- The Hyperliquid MCP he called missed (RC:188) is in no backlog.
- Judging is a shared step, not the skill he named (US:251). The work is done.
- C-27a changed the mini-app core for one example app (PC:4405, US:125).

**Softened, with a reason on record, and fine**
- A14's in-loop hook is "A Should, after its probe" (PC:2200, US:81). The tool row and the Library's refusal give the same feedback if the probe fails.
- C-20's kill-line lane now tests a function the new node never calls (PC:4198). VAL:15 and VAL:45 say why: the kill line stays a placeholder until the risk session.

## The additions

Every one has a source in the record. None came from a builder's own idea.

| Section | Where it came from | Does the record justify it? |
| --- | --- | --- |
| C-12d | Plan gap: the node could not bind any venue (VAL:7) | Yes. No real trade was possible |
| C-12e | Review findings B2, B3, B4 (TR:30) | Yes. Wrong position size on the money path |
| C-25 | Review HIGH on C-05e (VAL:26) | Yes. An agent could read a grant |
| C-26 | Found in the build, BACKLOG C-12a (VAL:25) | Yes. The node ran stale code |
| C-26b | Review HIGH on C-26, item D1 (TR:28) | Yes. Same fault on the money packages |
| C-27 | BACKLOG TOP (VAL:27) | Yes. An app could hold his operator bearer |
| C-27a | Plan gap: C-27 turned 12 tests red (PC:4399) | Yes, as a prerequisite. See the core change above |
| C-28 | Review low B16 (VAL:28, VAL:45) | Yes for live. Built ahead of need, since C-21 came later. His pairing-key acceptance (R:32) is a separate matter |
| C-29 | C-23 findings (VAL:29), his PR 1 (TR:16) | Yes. A deploy traded markets he did not choose |
| C-30 | C-18 findings (VAL:30), F6, A3 (TR:43, TR:44) | Yes. Alarms read every market as shut |
| C-31 | Item A1 (TR:24) | Yes. Gold landed 100 times too small. It does not breach US:160, because R:38 says a real defect is fixed |
| C-32 | Item H1 (TR:25) | Yes. The vault was readable by other users |
| C-33 | Item I1 (TR:26) | Yes. Its PR found a real host deadlock |
| C-34 | Item E1, plan gap (TR:27) | Yes. Promote had no records to read |
| C-35 | Items C1, B5, C3 (TR:31, TR:39, TR:40) | Yes. His status and kill could lie |
| C-36 | His request (PC:4683, R:37, TR:65) | Yes. Not a defect fix; he asked for it |
| C-37 | C-12d's review (TR:74) | Yes. No stop could move on cTrader |
| C-38 | C-30 findings, his ruling of 4 November (TR:10, TR:13) | Yes. An installed node could not bind |
| fix-host | Whole-repo reds at the tip | Yes. Tests only, no product change |
| fix-judge-types | Mid-program `just ci` | Yes. Types only, proven the same on 5,562 cases |
| fix-mock-scan | Scan red from C-12a | Yes. It widens the scanner by exact literal and path |
| fix-mockscan | Scan red at A7 | Yes. Same red, cured another way (line markers), so two styles now exist |
| fix-node-proofs | Plan gap: the road refused the node, and C-10 and C-11's tests hid it | Yes. Real one-click break |
| fix-phase0 | Phase-0 whole-repo check | Yes. Test name clash and the shared hash rule |
| fix-qmbapp | Suite red after B10 | Yes, but it also added a product door (`allow_gaps` on `backtest_run`). The chunk auditor should check it against TR:57: the study wins |
| fix-research-test | C-27a left 2 tests red | Yes. Test rewritten, no case dropped |
| fix-structure | Red from B7's `tzdata` | Yes. One expected-set line |

One line on shape: these 18 sections became about 18 PRs because his cluster ruling (R:26) came only on 4 November. His last three came as one PR, as he asked.

## Original sections whose text changed since `eb93a70b`

Seven changed. Nothing was removed. All other original sections match word for word.

| Section | What changed | Why |
| --- | --- | --- |
| Program checklist | Dispatch table grew to 91 rows | The additions. Its opening still says 73 PRs and 22 in phase 5, which is stale and harmless (PC:5, PC:22) |
| C-14 | Depends on the new sections; REST only; deploy read from the node; "landed" redefined against `origin/main` | VAL:13, TR:16. The last is finding 1. Depends omits C-29 though PC:3777 names it, also harmless because the stack order holds |
| C-17 | Real server steps, keys before enable, line endings pinned | VAL:14, TR:46 |
| C-19 | `safe_to_restart`, rerun upgrade, deployment blobs to a server, two servers on one PC | TR:12, TR:45 |
| C-20 | Gate evidence line, full delete and repoint lists, kill-line lane rewritten | VAL:15 |
| C-21 | More files, the engine line waits, live check reads venue and owner | VAL:16, VAL:43, TR:47 |
| Appendix C | Regenerated | The script reruns over the new sections |

## Unbuilt work

| Section | What it is for | Which ruling still wants it |
| --- | --- | --- |
| C-15 | Scripts that prove on his demo account that a tag survives, a repeated order id is safe, a network cut leaves one position, and a grant refresh is safe | TR:78 (G-DEMO order) and VAL:45 (the cut waits on it). Fully wanted. It needs his demo sign-in |
| C-19 | Update a server's node and MIS at a safe moment, and get a deployment's files to a server | R:30, TR:12, TR:45, US:110. Fully wanted. Without it a server node answers `files_missing` (PC:4120), so C-17's server cannot yet trade. It waits at G-SERVER |
| C-20 | Delete about 47,000 lines of the old node shell | US:99, R:21, VAL:45. Wanted after `c14-real.log` and `c15-demo.log` pass. Settle SQS first (finding 2) |
| C-21 | The deliberate path to bind a live account | R:31: later. The engine line stays unchanged (VAL:43). It sits uneasily with R:29, see below |

Note: `D:/QMX-worktrees/unit-ship/RESUME.md:208` shows builders once started on C-15 and C-19 with C-21, then all were frozen (RESUME, "FROZEN"). An empty branch `build/us-c15` remains.

## What is sound

- Only he promotes and deploys: A9's principal rule, C-23 is no catalog row, C-06 refuses agents on money apps.
- Only the node sends orders, and no host holds order code (C-07, Level 0 item 8).
- Agents stay out of the fast lane. The slow lane matches his list in ruling 44 item by item (B20, B21).
- The MIS is optional to trade, with defaults, room for models, and his readings stored and home in the Library (C-08, C-09, C-22, B15, B16).
- Templates read logs through `readings_query`, not the MIS model (C-24, US:164).
- Journals are one envelope with typed kinds spanning market, account, platform, machine and world (AD-208). This answers his "not one row shape".
- No lookback limit (B7). All instrument classes. Holdouts off by default (B18c).
- Plain Python: the architecture keeps it, and human Python only warns (Part A CC-08, UT-20).
- Placeholders are clearly labelled, with a 31-row rip-out list and a query that finds them (A15). Stops on every order, tighten-only and no-stop units are on that list, so they do not bind the risk session.
- No UI code. The engine and the mini-app core are changed only where named. C-33 and C-36 stop rather than touch the engine.
- The server path and C-19's blob push were written to leave local-first and the Library alone (R:30).
- Forged live record dropped, signed stop move routed to the risk session, pairing key accepted: all three match his 4 November words.
- R as a measure stays beside money, so his doubt about R fixed at entry (RC:322) costs nothing today.

## Set aside for him

- Where does he land the stack, `engine/base` or `main`? I assumed `engine/base`, as with PRs 207 to 234, so C-14's check must change. If he means main, someone must tell him to take 2,277 commits there.
- Does "live logins never in QMX" (R:29) mean a node may never hold a live grant, which is C-21's whole point? I assumed it means no agent or host store, and C-21 stays later.
- Should the MIS widen a unit to new markets (his seed, RC:329) or only narrow within what he admitted (PC:4834)? I assumed narrow, because only he admits.
- Must the new node gate entries on SQS before the demo, or only after the risk session? I assumed after, since the demo holds no money, but the old gate must not be deleted before someone decides.
