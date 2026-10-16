# Reconcile inputs — what each load-bearing input asked for, and where it landed

| Input | Ask | Landed in | Not landed |
| --- | --- | --- | --- |
| Rulings file 26 (binding) | 6 Lab core; 12 hub keeps Lab tools; 14 unit in the node behind an adapter; 22-25 one engine; 28 one Library; 29 ends at paper; 31 board saved; 46 design for the UI; 52-53 environments | AD-1, AD-14, AD-11, AD-1/AD-4, AD-1, AD-12, AD-2/AD-9, every map row, AD-9 | — |
| The brief | editor engine; palette and validation; run this part; notebooks port; indicators/components/variants; ML + slots + machine picker with preflight; experiments/compare/scenario; copilot pack from 17 tools; QMB door; pod model; pods ↔ units ↔ node through an adapter; paper; surface API mapped to components; gaps | AD-2; AD-3; AD-4; AD-9; AD-6/AD-16 + templates D1/D4/D5; AD-7/AD-8; AD-4/AD-5/AD-6 + LLD 6; AD-14 + LLD 7; AD-5 + LLD 3; AD-10; AD-11/AD-17; AD-12; LLD 6 + UI-TO-BACKEND-MAP; HLD 7 | the "component" noun has no AD of its own; it rides AD-6, AD-16, AD-17 and the D1/D5 templates (a quiet requirement kept in the map rows for Features and "Build your own") |
| Operator correction (screenshots, not code) | requirements from screens and intent; mark each map row with its shot | UI-TO-BACKEND-MAP shot column; 23 new shots in `ui-shots/`; memlog assumption on Data/Compute/Agents depth | the Data, Compute and Agents panels were reached only as menu entries; their rows cite research 10 and carry that caveat |
| Engine spine | one format, closed kinds, memo, lifecycle, placement, three surfaces | Inherited Invariants; AD-3 uses typeVersions only; AD-4 selected-subgraph; AD-8 | the paper template's wait-on-live-bar needs an engine `wait(event)` on a market-data event (rubric medium) |
| Library spine | roster, relations, refs, port, previews | Inherited Invariants; Conventions › Drafts and refs / Reads | the `book-definition → pod` mapping conflict (surfaced) |
| Research 17 | 27 backend tools; L1-L4, D1-D10 as engine configurations; the Lab rule | DOC-CHANGES row maps all 27; templates layer; AD-13 | P1-P4 (Portfolio) belong to the Portfolio design |
| Research 09 | keep the unit loose, the pod meaning open, the identity rule as a table, benches keyed on stage | AD-11 parts-as-a-list; OPEN-1; AD-16; AD-10 stages | — |
| Research 13 | RLM kernel, failure ladder | AD-9 (the same port serves `rlm`); the ladder is the engine's | — |
| hp17 code | QMB door, qmx_remote, qmx_apps, harness public API | AD-5, AD-8, LLD 3/7 | mini-app I/O stays with the engine's AD-19 |
| docs | CT-12/22/27/28/46/47, TN-9/19/20, ADR-0024 | AD-5, AD-7, AD-11, AD-12, AD-17 | — |
