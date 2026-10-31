# What X0 did with each R0 finding

Agent X0, 31 Oct 2026 (evening). The review is `architecture/review/R0-level-0.md`. "Spine" is `level-0/ARCHITECTURE-SPINE.md`; "connections" is `architecture/01-connections.md`; the hand-offs are in `level-0/HANDOVER-TO-PARTS.md` by the same id.

## The 19 findings

| Finding | What X0 did |
| --- | --- |
| R0-01 (High) | Fixed at Level 0: new AD-46, one host-pass route `POST /api/host/forward` with a closed verb set, mirroring the engine's forward route, plus `app_op` composed with its `Placements`; X1, X2, X3, X7 and X10 marked NEW on that route (connections §3, §6); AD-28, AD-31, AD-44 amended; both facts proven by running code (`blast-radius.md` items 10, 11). Verb design handed to C. |
| R0-02 (High) | Fixed at Level 0: AD-44 gains the direction rule (nothing connects into This PC); AD-42 keeps each machine's OpenObserve as built; X4 now This PC reading a server; X9 removed; LC-A0-14 reversed; the draft's engine AD-69 amendment withdrawn. Reach of a server's OpenObserve from This PC handed to C (INFERRED). |
| R0-03 (High) | Fixed at Level 0: AD-17's layer G has a safety half (the unchanged verdict) and a behaviour half (a warnings report), and the spine now says what deterministic checks can and cannot catch and where the rest is caught (the judge, paper, his click). Report design handed to A. |
| R0-04 (High) | Fixed at Level 0: AD-37 names This PC's two grants and their refreshers, and the node's own sign-in and store; AD-45 makes the trading profile one rule; an Amended decisions row lists the change to ruling 135 in code (the host's refusal and its tests stay; the sign-in gains the node as a code-relay target). Proven by a scan that the host touches only its own token name (`blast-radius.md` item 12). Build handed to C. |
| R0-05 (High) | Fixed at Level 0: AD-8 tags orders in the client order id, cTrader's `label` and Hyperliquid's `cloid`, one node per account on the account record, per-order attribution as new code; AD-38 adds the install id, his same-node confirmation and his take-over click; LC-A0-05 restated. Descriptor fields rerun by X0 (`openapi-91.pb`). Demo proofs and the build handed to C. |
| R0-06 (Medium) | Fixed at Level 0: AD-27, AD-12 and connections C13 say the before-dispatch write is the node's own append store in process; only closed partitions pass the market-data door afterwards. Handed to C (node) with B's writer library consuming it. |
| R0-07 (Medium) | Fixed at Level 0: new AD-47, one block loader; AD-19, AD-38, P1, C6 and the shapes table amended. Loader design handed to A. |
| R0-08 (Medium) | Fixed at Level 0: X10 added (updates), X3 carries the recorded feed with its size, a "nothing crosses" line for This PC's readings, E8 gains the Hyperliquid agent wallet and the node's own sign-in, E11 and E12 added. X10's install path (INFERRED) handed to C. |
| R0-09 (Medium) | Fixed at Level 0: AD-42 names the trading machine's own senders (the kept alert publisher and liveness ping), AD-36 keeps those two modules, E11 and E12 added. Wiring and default services handed to C. |
| R0-10 (Medium) | Fixed at Level 0: AD-36 names every caller the scan found, gives the kill line (per binding) a labelled placeholder action, and keeps the stop-on-every-order test before and after; the risk-session row updated. Build handed to C. |
| R0-11 (Medium) | Fixed at Level 0: one paragraph in "The parts" says the score proves properties, not cases, and requires each Level 1 file's case table, checked by script in R1. The table is handed to every part. |
| R0-12 (Medium) | Fixed at Level 0: AD-17 carries the door table (catalog row, step and hook A to F; Library save A to F; QMB run and node deploy need a recorded G verdict for the compiled fingerprint); LC-A0-12 restated. Handed to A. |
| R0-13 (Medium) | Fixed at Level 0: AD-33 enforces the secret map (only `trading-node` may name the trading-grant secrets) and the Docker allow-list instead of an unbuildable "order-capable" check; LC-A0-18 restated. Handed to C. |
| R0-14 (Medium) | Fixed at Level 0: AD-38's stand-down table (what clears each, starting defaults), the two soak settings shown not enforced, and "tested to paper: his click" in AD-23. Handed to C (table, soaks) and A (lifecycle). |
| R0-15 (Low) | Fixed at Level 0: X2 carries latest values only, read through AD-46; guard events reach This PC by the pull; the false `Last-Event-ID` claim removed from AD-44 and connections §3. Handed to C. |
| R0-16 (Low) | Fixed at Level 0: AD-45 retitled "Host roles and the trading rule": the code's two roles, and the trading profile as one derived rule; P0, P12, AD-4, the inherited AD-52 row and connections §1 follow. The glossary keeps its word "trading profile", now defined as derived state. Handed to C. |
| R0-17 (Low) | Half fixed, half rejected: AD-29, AD-27, AD-39 and C16 reuse `note` and `paper-run`; retiring `bot` and `strategy` is rejected because a retired kind refuses saves that shipped tests and the registry migration make (`blast-radius.md` item 13; LC-X0-12). Handed to B. |
| R0-18 (Low) | Fixed at Level 0: AD-23 makes the identity table a core setting handed to QML as data; C9 and C20 marked NEW; LC-A0-10 restated. Handed to A. |
| R0-19 (Low) | Fixed at Level 0, each part: QML-22 in AD-2; AD-24 takes AD-2's optional read surfaces; AD-2 names the host process and its supervisor; worlds `paper` and `demo` defined in AD-27; AD-6 gains the overlap window and the rule that cross-machine asks ride AD-46's versioned verbs; AD-26 gains the market id (EX-06); the missing words are defined in the spine's conventions ("Words this spine adds"). Handed to A (QML-22, AD-24), B (worlds), C (host on the trading path, overlap window, market id). |

## Appendix A (60 cases)

- **Given a handling line in the spine or the connections master (21):** QML-13 (AD-47), QML-19, QML-20, QB-21 (AD-5), QML-22 (AD-2), UT-01 (AD-17), MIS-10, JR-08 (AD-27), QB-23 (AD-5, AD-28, X3), TN-04, TN-15, MA-02 (AD-38), TN-23 (AD-39), TN-25, TN-26 (AD-26, AD-38), TN-31, TN-32 (X8), EX-06, LD-12 (AD-26), RS-13, RS-18 (For the risk session).
- **Handed to a part by id with a handling line (all 60, including the 21 above for their build):** A takes 15, B takes 22, C takes 23, each case to exactly one part; see `HANDOVER-TO-PARTS.md`.
- **The five R0 marked as mattering now** (QML-22, UT-01, MA-02, QB-23, TN-04) are all settled in the spine.

## The networking table, after the fix

Every cross-machine link now names who opens it and its route as it will exist (spine "Networking between machines"; connections §3 and §4): X1, X2, X3 and X7 ride AD-46's route (NEW); X4 is This PC reading a server's own OpenObserve; X5, X6 and X8 are as built; X9 is removed; X10, E11 and E12 are added; the order path is still only node to venue (E1, E3, E4).

## Notes on how this round ran

- `lint_spine.py` reports 0 findings on the amended spine.
- `scratchpad/x0/coverage.py` checks the done-when by script: all 19 findings in this file and handed over, all 60 Appendix A cases handed to exactly one part, every claimed spine line present, every X and E link in connections §3 and §4, every cross-machine link in the spine's networking table, no stale `Last-Event-ID` or into-the-PC claim left. A0's `quotecheck.py` finds his one quote on its cited line (T3:1102).
- The bmad-architecture reviewer lenses were not dispatched: the brief bars sub-agents, and R0 itself was this round's review. R1 reviews next.
- The run's memlog (`level-0/.memlog.md`) was not appended, because the brief names only the files above; this file is the record of the round's decisions.
- The glossary (`funnel/versions/GLOSSARY.md`) was not edited for the same reason; the words it lacks are defined in the spine for its next fold.
- Every new number is a named setting with a starting default and is logged as a lead's call (`LEAD-CALLS.md`, LC-X0-01 to LC-X0-17).
