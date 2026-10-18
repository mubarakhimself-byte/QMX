---
title: Data decisions from study 30
type: grilling
mode: HITL
status: open
blocked_by: [data-deeper-study]
claimed_by: ""
created: 2026-10-16
---

## Question

Study 30 section 6 questions not settled by rulings or architectures: (1) trading node on its own small VPS; (4) instruments and depth to start; (5) no tick database for now; (9) MIS training on his server as an engine workflow; (11) retire the PC news recorder once the server timer runs; (12) two observability stacks. Questions 2, 3, 6 follow rulings 56, 81 and Library AD-12; 7 waits for node deploy; 10 goes to the risk session; 13, 14 are code-level.

## Recommended answer

Accept study 30's recommendation on each; the build lives in `ENGINE-PLAN.md`'s data track.

## Sources

`30-data-and-devops.md` section 6; rulings 42, 56, 58, 81; `ENGINE-PLAN.md` data track.

## Update (2026-10-18 evening, re-centralize)

Data is held (rulings 91, 111): nothing ships on data until the deeper data study is explained to him. `ENGINE-PLAN.md`'s data track was removed and the file is archived. This ticket now waits on "Data deeper study, explained to him".
