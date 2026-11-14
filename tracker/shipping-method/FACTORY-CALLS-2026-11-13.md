# His answers to the factory design's calls (13 Nov 2026, about 22:45 local)

He read the overview diagram and section 8, not the full design. This file records his answers in plain words. His dictation is in `HIS-WORDS-2026-11-13.md` once that file is re-extracted.

| Call | His answer |
|---|---|
| Name | **Not "QMX factory".** He wanted the factory to be independent of QMX; QMX is simply its first project. Use a neutral name and folder, not `D:/QMX-factory`. |
| Models | Other models may come later through a proxy inside Claude Code, so the factory stays Claude Code-based and needs no other harness. |
| H1 | Yes. His part ends at planning; everything after his go runs by itself. |
| H2 | Yes. Go may be given in advance. With the challenger in place, the reasoning should be clear early. |
| H3 | Yes, and keep Fable scarce. It's costly, and the promo will end; he may downgrade later. |
| H4 | Yes. Checkpoints merge themselves, as long as the review is thorough. |
| H5 | Yes (recommendation). |
| H6 | Recommendation, but he asks: should a staging branch exist, or release branches (release v1, v2)? The UI may or may not merge into engine/base. The lead answers, with a recommendation. |
| H7 | Yes (recommendation). |
| H8 | Yes (recommendation). |
| H9 | **HOLD.** A fresh-morning question. He thinks all the auditing might run in one go and be clustered. |
| H10 | **Yes and no.** He often won't know what the code does, so he can't judge removals from code. The audit must explain each change in plain words, and Fable helps make the calls. He's only asked what he can understand. |
| H11 | Depends on the audit rethink below. Code standards: "do we have any yet, who set them?" He leaves that to the lead. |
| H12 | Yes: commit `apps/qmx-desk` (the UI redesign session hasn't run for days). |
| H13 | Didn't know the term "napkin budget"; explained in chat. |
| H14 | Yes. His plan: audit first, then docs catch up after. |
| H15 | **Not a fixed rule.** Building, auditing, planning and reviewing can run at the same time, with sessions coordinating. It's circumstantial, so the factory must support it safely. |
| H16 | Left to the lead: confirmed. |

## Settled on 14 Nov (his words: "the rest, it's on you")

- **H6:** tags only, no staging branch. His "go with the recommendation" stands.
- **H9:** not a design call. Which area to audit is his choice each time he starts an audit session, so the front desk asks him then.
- **H11b and all housekeeping:** delegated to the lead. That means backing up `D:/factory` to a private repo, committing the planning docs, and moving superseded files and `standing/` into history. He knows only his QMX folder on the Desktop; folders and layout are the lead's.

## His audit model (it changes the design's audit branch)

- **The audit starts by re-clarifying intent, not by judging code.** "Auditing requires you to know what is right and what is wrong. You can't just audit without knowing what something is meant to be doing." For an area such as QMB, first recover what it is meant to do from the PRs' descriptions, the plans and his words. Find the ambiguity in that mental model, and confirm it with him in plain words. Then judge the code against it. The plans and PRs may not have delivered.
- **Quality and architecture come second:** code quality, tests, architecture, maintainability, and the DevOps layer, all against the confirmed intent.
- **Decoupling is a candidate, not a given.** He thinks mini apps and workflows should be separate from QMX, but decoupling is only worth it if it improves performance or code quality. Otherwise it wastes a day of agents. So the challenger runs inside audits too.
- **The main areas:** QMB, QML, QMA, QMF (if it still exists), the library, the mini apps, and each area's DevOps layer.
- He remembers that planning already had code removal (`funnel-subtract`).

## His diagram notes

- Simplify the planning ↔ auditing loop in the picture.
- Show where the architecture stages are; planning should look much as it did yesterday.
- He wants diagrams, not long text. In particular, how bugs are handled.
