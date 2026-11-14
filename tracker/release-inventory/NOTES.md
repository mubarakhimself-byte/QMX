# Working notes (release inventory, 2026-11-10)

Progress log so a later reader can see where work stopped.

- origin fetched; origin/engine/base tip 3ae41ffc (2026-11-08 20:58).
- gh: 334 merged PRs total (#12 .. #352), all merged 2026-09-28 or later. Bases: engine/base 261, rebuild/base 65, integration 8.
- Ancestry check script running (merge commit and head commit vs origin/engine/base).
- plan/risk-core exists only as a LOCAL branch (not on origin). plan/unit-system local is newer (11-05) than origin (11-03); repair plan only on local.
- MERGED-PRS.md written (334 rows, 14 programs, 13 no-plan rows). Next: JOURNEYS search, PLANS, SHIPPED.
- Journey sources read: unit-system design-thinking J1-J25, UNIT-PLAN You-see (91), REPAIR-PLAN You-see (24), qma-v2 plan You-see blocks (hardening 58, data 30, wrap-up 12, local-first 8, loose strings 7, backup 7, sync 5, mock 3), 46 domain scenarios K-01..K-34, old BMad J-UI/J-KIT/J01.., docs/scenarios SCN-0001..0035, UI-NOTES-UNITS (19 screens), UI-HANDOFF (26 sections). D:/QMX-research has no journeys.
- Not built from plans: hardening AGW, RTR7; data DEL4R?, PRB-CT, DR2E, DR5B; wrap-up WU4 (open #204), WU10; backup B7 (dropped), B6 folded into SY3; unit C-15, C-19, C-20, C-21. risk-core round 2 = open PRs 353-369.
- Code facts: no desktop shell in repo (host is a CLI with exit codes for a desktop app); UI on engine/base is the 2026-10-01 baseline; UI rebuild branch ui-review/repair is local only. First-party apps (qmb, mis, trading-node) are all kind=headless. No "getting started" state in code.
- Next: write JOURNEYS.md, SHIPPED.md, PLANS.md, README.md.
- DONE 2026-11-10: MERGED-PRS.md, PLANS.md, JOURNEYS.md (sections A-J + 2 appendices), SHIPPED.md, README.md written.
- Not done or only shallow: J18 (plain Python units) not traced end to end; template run status (which of ~55 run end to end) not checked; UI-HANDOFF section 26 gaps not rechecked one by one; worktree D:/QMX-worktrees/unit-plan has 2 uncommitted edits that were not read.
