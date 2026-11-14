# Release inventory (built 2026-11-10, read-only, from git and GitHub)

1. `JOURNEYS.md`: every journey and scenario found, checked against the code: matches, partly, or never built. Start here. Fairly sure; nothing was click-tested, because no screen is wired.
2. `SHIPPED.md`: what QMX can do now, area by area, with code paths. Sure for "it exists"; not run.
3. `MERGED-PRS.md`: all 334 merged PRs, grouped by program. Very sure: every row was proved with `git merge-base --is-ancestor` against `origin/engine/base` `3ae41ffc`.
4. `PLANS.md`: the plan behind each PR range, plus older plans that still hold. Sure about PR ranges; plan summaries were read in the documents.
5. `NOTES.md`: working notes and where the work stopped.
6. Code beats documents. Where a plan and the code differ, the files say so (`SHIPPED.md` section 14, `JOURNEYS.md` section D).
7. The repair plan and the risk-core plans are on LOCAL branches only (`plan/unit-system`, `plan/risk-core`), not on origin.
8. Not shipped: the risk-core stack (#353-#369), WU4 (#204), and unit-plan sections C-15, C-19, C-20 and C-21.
9. Nothing has run on his real folder or a real cTrader demo account yet. That waits on his one demo sign-in.
10. Tags: "git" = proved by git or gh, "code" = read in code, "PR" = read in a PR body, "doc" = read in a document.
