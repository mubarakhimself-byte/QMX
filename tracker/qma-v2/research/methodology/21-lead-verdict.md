> STATUS 2026-10-16 (rubric walk): SUPERSEDED. See 27-rubric-walk.md. Rulings in 26 win.

# 21 — Lead verdict on reviews A and B

Written 2026-10-16 by the lead session after reading `20-review-a-operator-fit.md` and `20-review-b-feasibility.md`. Apply this to `19-centralized-design.md` and the Wayfinder map. Where this file and either review disagree, this file wins.

## Accepted from review A (operator fit)

1. **Invented numbers.** Remove "his number" from every figure he never gave, including $20/run, 12 variants and 5 dead ends. Each becomes a labelled Claude default ("Claude's default, change in Settings"). Spend per run defaults to "always ask" until he picks a number.
2. **Lab first.** The build order puts the Lab and Board first, one mini app as a plugin second, the paper scout third. Portfolio and desk briefs come later.
3. **Freedom.** Gate and grader rules bind agents only. He may drop any check in his own workflows, and the result carries a badge. Board tweaks he makes himself are not counted as trials. Only agent-run variants are counted.
4. **Node.** Delete node depth from 19: decision 6, `unit.tighten`, the direction table, auto-revert, and the 30%/3R and 10%/1R thresholds. All of it moves to a "waits on the risk session" list. C7 shrinks to a read adapter for named facts.
5. **Account guard.** Agents may READ guard facts through C7. They may never write or change the guard. Reword the lock-out ticket to "no agent write path, ever."
6. **Decisions.** Adopt A's seven yes/no questions plus the blank spend number, word for word. Everything else is Claude's call, recorded as an assumption he can overrule.
7. **Output.** 19 stays as the agents' reference. He gets a separate explainer page (the lead builds it).
8. **"Fewest iterations".** Two is Claude's starting goal, not his. Rename L1 to "Idea to first result" and show an iteration counter on the Board.
9. **C0 Methodology.** Add it. A methodology is a pack that sets autonomy rows, gates, role tiers, the organogram and starter templates. QMX ships one default. He or the copilot copies and edits it with the builder. Versions are kept and archived, never deleted.
10. **Minimal workflow builder in wave 2.** He describes, the copilot writes the folder, it is dry-run on a fake model, and it installs disabled until he says yes.
11. **A combined-session pilot.** A Lab-born session loads a workflow pack and the pilot mini app's pack, is opened in the hub, keeps its Lab home, and shows a Portfolio proposal as a card.
12. **Cut list.** Merge to about 30 user-facing templates per A's table. Blocks are not templates. Contracts keep their shape and cut weight for waves 1-2 per A's table.
13. **Usage.** At most one heavy job per night, chosen by a night planner (a script). RS7 calibrates headline claims only (at most 5 per run). Note that a second model family means a paid key.
14. **Slips.** The template count is 48 → about 30 after the merge, so fix MAP. Fix the section pointers.

## Accepted from review B (feasibility)

1. **Wave 1 prerequisites (outside this map, named in it).** Merge the HP stack, run D1-D4, fix B1 (one writer per SQLite file). No harness edits before that, per `DELETION-PLAN.md:43`.
2. **Harness extension packets come before the engine.**
   - a `home` field and origin;
   - structured JSON output per chat;
   - per-chat tool allow-list and max turns;
   - an app-plugin registry of approved hashes beside the SHA-locked core;
   - REST start for background chats.
3. **Lab "never asks" vs MANAGE.** The engine performs runs, schedules and app actions itself as script steps under a standing allow rule, which is decision 1. Agents only propose. MANAGE stays as it is for chats. Unattended asks never wait 300 s; they go to the inbox and the run parks.
4. **The `model` step on the plan.** It becomes a one-turn, no-tool chat through the SDK on the plan, or a direct call on a key provider. Redefine the B1 budget class accordingly.
5. **Folder plugins.** App and workflow folders may not carry hooks, monitors, `bin/` or in-process `tools/*.py`. Their tools run through the harness tool path inside the money gate. `pending/` lives outside the hashed folder.
6. **Browser safety.** The broker owns Chrome through a pipe, not an open debug port; agents with Bash can't reach it. The money gate extends to browser navigation (broker hosts blocked). The first step is read-only, which is decision 4.
7. **Fan-out within the 4-chat cap.** Other-family reviewers run as engine `model`/`agent` steps on key providers, not as native sub-agents.
8. **Pause-at-cap.** The Python SDK has no usage report, so use rate-limit events and reset times. Keep probe 1 for the TS report.
9. **Sandbox.** Windows 11 Home has no sandbox and Docker isn't running. RLM, L4 unattended and model-written Lab code wait on probe 6. The mini-app pilot runs at a trust level that needs no Docker, or waits; probe it.
10. **QMB door.** L1 needs QMB to accept a config, and QMB is another session's area. Open a door ticket for that session. Until it closes, L1 runs on pre-registered configs ("B-lite").
11. **Node-dependent templates move to wave 4:** RK1, RK2, RK3, RK5, RK6, T5, T6, T7, T9, P1, P3, P4. P2 stays in wave 2 only as a broker-reads-only renderer proof, and only if it is cheap.
12. **Server work** (`runs_on`, the cloud browser) waits for B44.
13. **Facts.** The code has four approval answers, not five; fix 19 and the UI list.
14. **Map.** `build-plan-into-qma-v2` must not wait on wave 2 or 3 tickets. Split it into "wave 1 packets" (waits on the decisions and specs only) and later per-wave packet tickets.

## Merged wave order

| Wave | Contents |
|---|---|
| 0 (now, parallel) | The seven decisions plus the spend number. Specs: C0, C1, C5, C7 (read only), C8, C9. B's probes as scripts under `scripts/live/`. Research tickets. The guard "no write path" lock. |
| 1 | Prerequisites: HP merge, D1-D4, B1. Then harness extensions (item B2), then the thin engine core (A's cut), folder loader, renderer, night planner, inbox. |
| 2 (pilots, in order) | RS1 with headline-only RS7 (proves engine, cap, grader). L1 Board on B-lite. One mini app as a plugin. Minimal workflow builder. Combined-session pilot. P2 broker-reads-only if cheap. |
| 3 | The rest of the merged catalogue; agent, skill, pack and methodology builders; funnel A and B in full once the QMB door closes; browser read-as-me after decision 4 and probe. |
| 4 | Node-dependent templates (B item 11), mini apps needing Docker, server runs, cloud browser, Library lineage after Strats v2. |

## Rejected or modified

- **B: "every template reading the guard goes to wave 4".** Kept, except reading guard facts through C7 is allowed once a node read model exists. No wave changes because of this.
- **A: "Decisions 1, 3, 7, 8 are Claude's call".** Accepted, but each one is listed as a visible assumption on the explainer page so he can overrule it.
