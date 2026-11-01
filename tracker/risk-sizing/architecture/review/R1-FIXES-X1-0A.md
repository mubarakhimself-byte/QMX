# R1 fixes by X1-0A: Level 0, the connections master, part A

Fixer X1-0A, 2026-11-01, per `architecture/briefs/X1-0A-fix.md`. One line per finding and settlement in this share: fixed where, or rejected with the evidence. Files: `level-0/ARCHITECTURE-SPINE.md` (L0), `level-0/LEAD-CALLS.md` (L0 calls), `level-0/blast-radius.md` (L0 BR), `level-0/HANDOVER-TO-PARTS.md` (L0 handover), `01-connections.md` (master), and `parts/A-qml-dictionary-unit/` (A). Labels: CHECKED (path:line at `c93407ca`, or a script run) or INFERRED. Scripts: `...\scratchpad\x1-0a\`. Done.

## Findings for Level 0

| Finding | What was done |
| --- | --- |
| R1-L0-01 | Fixed. L0 "The parts" names the Level 1 part for each section, and P7, P8, P10 each gain a "Level 1 owner per case" line with R1's split (A: AG-01, -02, -03, -04, -08, -09, -11, -13, -15, -16, CA-02, -03, -07, -08, -09; B: AG-05, -07, -10, -12, -14, CA-05, -12, MA-01, -03, -04, -06 to -10; C: CA-01, -04, -06, -10, -11, MA-02, -05). CA-03 is shared on purpose, as QML-06 is: a line in A (the format, A1) and one in C (the venue's quantity, C-12a), with B6's assert (L0 call LC-X1-02); C's fixer had already added its line. L0 handover lists B's and C's new lines; A's table carries its 13. |
| R1-L0-02 | Fixed. L0 AD-5 names one run-slice handler `qmb/src/qmb/host/unit_handler.py` over `HostedUnit` (B builds it in B6, the node imports it in C-12a); AD-16 hosts units only through `construct_unit` and says `construct_bot` fails closed; seams table, diagram, P1, P11 and master C12 follow; L0 call LC-X1-01. Proven at step 4: the node's driver accepts a five-hook handler and refuses an object without the hooks (`x1-0a/br15_hosts.py`, L0 BR item 15). |
| R1-L0-03 | Fixed. L0 AD-46, LC-X0-03 and master X1 read "his click is caller kind `user`, principal `operator`; an agent `agent:<id>`, a workflow `run:<id>`". CHECKED by running `Caller("user").principal` (`'operator'`, `qmx_engine/service/context.py:59-70`, `br15_hosts.py`). |
| R1-L0-04 | Fixed as CF-2 (below). |
| R1-L0-05 | Fixed as CF-4 (below). |
| R1-L0-06 | Fixed. L0 opens with "In plain words", five sentences (the core, the three apps, units stand alone, only he promotes, everything comes home); L0 call LC-X1-04. |
| R1-L0-07 | Fixed. "Kernel:" rows read "Core:"; the paradigm paragraph, AD-1 (title, Prevents, Rule), AD-41 and L0 call LC-A0-01 say "core". "Kernel" stays only in the paradigm's name and in QMB's banned-word list. |
| R1-L0-08 | Fixed. Master X6 and §6, L0 AD-28, AD-46 and the networking row X6 read "verified by parse (Part C C9); a real two-host run in slice C-17". |

## Findings for part A

| Finding | What was done |
| --- | --- |
| R1-A-01 | Fixed. The dummy's `min_trend_strength` declares `motion.min_count` 20 (A `2-unit-template-numbers-lifecycle.md` §3, §6 and its JSON; spine AD-103, AD-118; CONTRACTS §9 notes `min_trades` 60 applies only to numbers that declare none); A5's Verify asserts no row before the 20th trade and one step after; the consumers table asks B9 to assert a calibration row from real trades; A call LC-A1-27. Found on the way and fixed: the slow rule's shrink toward zero never changed a decision (A-NEW-6, `x1-0a/shrink_sign.py`: 0 of 10,000), so it now shrinks the found edge toward the default as AD-103 says (A call LC-A1-28, A BR-A8). |
| R1-A-02 | Fixed. A4's Verify and the QML-04 case line assert the last tenth's median time per update within `update_time_growth_tolerance` 1.5 times the first tenth's (new setting in CONTRACTS §9; A call LC-A1-31). |
| R1-A-03 | Fixed. A2 depends on nothing; A1 and A2 land in either order (the unit document names no intent type, CONTRACTS §1). |
| R1-A-04 | Rejected with evidence. At `c93407ca`, `git show c93407ca:qmx-agents/packages/qma-harness/src/qma/harness/tools.py \| grep -n DOMAIN_GROUPS` gives 641 (use) and 668 (definition), and Python's `splitlines` agrees; part A's `:668` is right. Recorded in A's spine (Conflicts section) and A BR. Level 0 cites `:668`. |
| R1-A-05 | Fixed. A7 lands the dummy on first start as a `unit` draft, once per store, keyed by its fingerprint (the find-then-put pattern of `qmx_library/migrate/from_apps.py:52-57` on the draft ref only, never `place`'s merge); a fresh-folder test lists one draft and a second start adds nothing; the twins stay fixtures; spine AD-118; A call LC-A1-26; A BR-A7 (the shipped `test_migrate.py` rerun and app-import cases run: 2 passed; the catalog indexes draft-ref moves, `qmx_library/fts.py:42-45`, `:187-200`, so the find sees a draft). |
| Case table (R1-L0-01) | A's spine table gains AG-01, AG-02, AG-03, AG-04, AG-08, AG-09, AG-13, AG-16, CA-02, CA-03, CA-07, CA-08, CA-09, each with its handling, its check and its AD; A9's Verify gains the AG-13 principal test. |

## Clash settlements naming these files

| Settlement | What was done |
| --- | --- |
| A-C1 | Fixed. L0 AD-17 door table splits `put` (layer A, every problem) from publish and `compile` (A to F, refusing); AD-29 says so; L0 call LC-A0-12 restated; master C2. |
| A-C2 | Fixed. L0 AD-19: a component is an entry only when `entry.schema = "qmx.entry/1"`; other components untouched (writers CHECKED at `qmx_control/library.py:312-330`, `migrate/from_apps.py:66-70`). |
| A-C3 | Fixed (Level 0 half). L0 AD-16, AD-5; master C12. B and C halves are theirs. |
| A-C4 | Fixed. L0 AD-31 lists A's seven rows in toolsets `unit` and `blocks`; the harness derives its groups; an Amended-decisions row gives the reason; master C5. The line is `tools.py:668`, not `:664` (see R1-A-04). |
| A-C5 | Fixed. L0 AD-20: Stage 0 stays as built for research; the unit path never calls it; the 23 old-law names leave only the top-level surface. |
| A-C6 | Fixed. (1) L0 AD-22; (2) AD-16 (compiled fingerprint covers decision-changing options); (3) and (4) AD-23; (5) AD-13, with the journal taking the row id as record id (R1-B-10). |
| A-C7 | Fixed. L0 AD-9: QML owns the measure vocabulary, mapped to QMF's closed `UnitKind` by one table (`exact.py:125-144` CHECKED). |
| B-D1 | Fixed. L0 AD-34: run kinds as jobs plus `capabilities` and `instruments`; status, results and compare are the core's `backtest` rows (`supervisor.py:957-963` CHECKED); master §5. |
| B-D2 | Fixed. L0 AD-34 and P11: kind `headless` until the UI session adds its folder (`manifest.py:309-310` CHECKED). |
| B-D3 | Fixed. L0 AD-32 adds `app_op` passing `inputs` (`supervisor.py:1022` CHECKED); an Amended-decisions row; master C8. |
| B-D4 | Fixed. Master C10: the supervisor's job path with the lander `qmb-run` in `qmx-judge`; L0 AD-34 says "the core lander". |
| B-D5 | Fixed. Master C11: the core lander materialises partitions into the run folder; L0 AD-34 says QMB reads files only. |
| B-D6 | Fixed. L0 call LC-A0-21: `[qmb] agent_wait_s` 240 s, workflows wait for the whole job; master C7. |
| B-CC5 | Fixed. Master §5 gains the `try` item row. |
| B-CC7 | Fixed. Master X3 and L0 AD-28: the pull is a host upkeep job; confirmation is C's `confirmed` fingerprint list; nothing prunes in this build. |
| B-CC8 | Fixed (Level 0 half). L0 AD-46: `apps.job` carries `inputs`; the principal rides the pass; `apps.job` refuses any principal but his for a `money` app. C's CONTRACTS half is C's. |
| B-CC9 | Fixed. Master C22 and C24 ride the journal envelope as `journal-readings`, `source` in the body; L0 AD-27 says so. |
| B-CC10 | Fixed. Master §2 gains C30 (supervisor to core lander), C31 (host facts), C32 (app-log shipping). |
| B-CC11 | Fixed. Master C14: verdicts, baseline and proposal cards are records. |
| B-CC12 | Fixed. Master C13 and C23, L0 AD-27: the host's records job is the one harvester (sealed journal months; open month of bars and readings every `[records] open_harvest_s` 60; ticks every `[records] tick_harvest_s` 3,600); `series.py:6-9` CHECKED. |
| CF-1 | Fixed. L0 AD-37 and master C27: on Linux an owner-only grant file on the node's machine with QMN's refresh rule, never carried off the machine (R1-C-14); QMN's store not used (`qmn/src/qmn/secrets/store.py:1-8`, `supervisor.py:598-611` CHECKED). |
| CF-2 | Fixed. L0 AD-45, P0, the AD-52 inherited row and master §1: three roles `pc`, `node`, `server`; this build uses `pc` and `server`; role `node` unused; proven by running (`br15_hosts.py`: `('pc', 'node', 'server')`). |
| CF-3 | Fixed. Master X1 and the L0 networking row X1: `bind` replaces `mode`; `withdraw`, `confirm_same_node`, `sign_in_begin`, `sign_in_code`, `self_test`, `rotate_keys` added. |
| CF-4 | Fixed. L0 AD-33 is the one table of six mini-app core changes, each with its reason, its CHECKED line and its slice (B1, B5, C-05 split in four), plus the one interaction to test; the Amended-decisions row points to it. |
| CF-5 | Fixed. L0 AD-28 and master X3: the server's door pins node-born partitions until listed `confirmed` (`market_data.py:599-617` CHECKED); nothing prunes. |
| CF-6 | Fixed. L0 AD-40, P13 and its plain paragraph, L0 call LC-A0-02, master C22, C23 and §1: readings split by tier (tick in the node, bar, session and day in the `mis` app); series key carries source, tier and machine. |
| CF-7 | Fixed. L0 "For the risk session" netting row: at most one unit per symbol on a netting account or Hyperliquid subaccount, refused at deploy, a placeholder. The risk pack's row is A's `RISK-SIZING-POINTS.md` point 4 (see part A); `RISK-SIZING-PACK.md` at the tracker root has no netting row (grep) and is not in this share. |
| C-CC2 | Fixed as CF-5 (master X3). |
| C-CC3 | Fixed. Master C23: the read-only market root `QMX_MARKET_ROOT`, holdout seal honoured. |
| C-CC5 | Fixed. Master E8: the node's sign-in is its operations `sign_in_begin` and `sign_in_code`. |
| C-CC6, C-CC7 | Fixed as C31 and C32 (B-CC10). |
| C-CC8 | Fixed. Master X2 and L0 AD-6: tolerant cross-machine reads, optional `clock` field (`heartbeat.py:70`, `:85`, `:101` CHECKED); L0 call LC-X1-03. |

## Cross-part findings that touch these files

| Finding | What was done |
| --- | --- |
| R1-C-01 | L0 AD-23 names the promote action `units_promote` (his principal only; Part C slice C-23); L0 AD-38 and master X1 carry the starting-values rule (paper from defaults, live from the paper lane's last calibrated state). |
| R1-C-03 | L0 AD-31 and master C15 name Part C as owner of `readings_query` (C-09) and `instrument_get` (C-02). |
| R1-C-04, R1-C-12 | L0 AD-46: `apps.job` carries `inputs` and refuses agents for `money` apps. |
| R1-C-05 | L0 AD-46 and master X1: the chat path on This PC stays; the node orders changes by its own desired-state table. |
| R1-C-06 | L0 AD-38, master X1 and X5: deployment files by fingerprint, sent ahead through the hub; no size setting. |
| R1-C-11 | L0 AD-31 and master C15: a slice adding a row to an existing toolset names `qmx-tools/tests/test_tools.py:374-376` (CHECKED) and the new count. |
| R1-C-13, R1-C-14 | L0 AD-40 (holdout seal) and AD-37 (grant never leaves the machine). |
| R1-B-06, R1-B-07, R1-B-10 | L0 AD-27 (kinds `lifecycle`, `state`, `node_lifecycle`; three lifecycle writers; `source` in the reading body) and AD-13 (row id as record id); master C13, C22. |
| R1-B-09 | L0 AD-33 change 3 lists `qmb` among the apps that opt into restart with back-off; master C7. |

| R1-L0-02 in A | A AD-107, `1-qml-door-compiler-runtime.md` §3 and §4, the Seams table, the diagram, Deferred and the consumers table name Part B's one handler. |
| R1-C-10 in A | A CONTRACTS §1 gives each futures market entry a `roll` (calendar, volume or open interest) and a root; §2.3 drops `roll_rule` and lists `root`, `rolls_to`, `last_trade`; the class enum stays `spot_crypto`, which B's capabilities and C's records already spell (checked in their files); spine AD-102; A call LC-A1-29. |
| CF-6 in A | A CONTRACTS §5.3: a reading card's `tier` is its clock (`tick`, `bar`, `session`, `day`, `calendar`, Part C's words) and `concern` labels what it measures; A call LC-A1-30. |
| R1-B-06, R1-B-10 in A | A AD-115 and CONTRACTS §8: kind `lifecycle`, three writers, `principal = "operator"` on his clicks; CONTRACTS §4.2: `state` means runtime events only, `row_id` is the record id; AD-107. |
| R1-C-01 in A | A AD-103 and CONTRACTS §4.1: QMB runs and paper lanes start from defaults, live carries the paper lane's last calibrated state; AD-115 names `units_promote`; UI notes. |
| R1-C-06 in A | A CONTRACTS §6: the block folder is assembled on the node's volume from files named by fingerprint, no size setting. |
| CF-7 in A | A `RISK-SIZING-POINTS.md` point 4: at most one unit per symbol on a netting account or Hyperliquid subaccount, refused at deploy. |
| R1-C-08 in A | CA-03 line in A's table; the consumers table asks B6 and C-12a for the quantity asserts. |

## Checks run

| Check | Result |
| --- | --- |
| `lint_spine.py --workspace level-0` | 0 findings |
| `lint_spine.py --workspace parts/A-qml-dictionary-unit` | 0 findings |
| `x1-0a/cases.py` (R1's `cases.py`, its output renamed) | every non-risk case of the 267 is claimed with a non-empty handling line; P7, P8 and P10 cases each claimed by the part Level 0 names; QML-06 and CA-03 claimed by A and C on purpose; the 16 risk rows outside the part tables are the risk session's, as before |
| `l1a/quotecheck_a.py` on part A, Level 0 and the master | 16, 1 and 0 quotes of his words, all on their cited lines; no new quote added |
| `x1-0a/br15_hosts.py` on the scratch export | node driver accepts a five-hook handler (True) and refuses one without (False); `Caller("user").principal` is `'operator'`; roles `('pc', 'node', 'server')` |
| `pytest qmx-library/tests/test_migrate.py -k "rerun_writes_nothing or app_artifacts"` on the scratch export | 2 passed |
| `x1-0a/shrink_sign.py` | 0 of 10,000 cases where the old rule's shrink changed its edge |
| Stale-word grep over the owned files (`principal user`, `roll_rule`, `qmb_tool_wait_s`, `kind both`, `backtest_and_land`, `two roles`, `Kernel`) | only historical mentions inside "corrected" notes remain |
| Line endings | every amended file kept LF, as the working copy had it |

Not written here because they are outside this share: `level-0/.memlog.md` (the brief names four Level 0 files, not its memlog; the decisions are recorded in this file and in the L0 lead's calls) and `RISK-SIZING-PACK.md` (no netting row).
