# Hand-off from the UI rebuild (2026-10-01 to 2026-10-04)

For the fresh session that starts the backend work. The UI lane changed only `apps/qmx-ui` on branch `ui-review/repair` (worktree `C:\Users\Mubarak\Desktop\QMX-worktrees\ui-review-repair`). Nothing has been pushed.

## Read in this order

1. `MINI-APPS-AND-COPILOT-CONTRACT.md`: how mini apps, panels and the copilot put things on screen, what the backend must provide, and the decisions needed. Start here.
2. `../BACKEND-REQUIREMENTS.md`: per-screen data needs (Lab, Portfolio, Library, Copilot). Read its first note: some parts are superseded.
3. `../UI-BACKLOG.md`: what is done and open. Start at "Session review (2026-10-04)".
4. `../UI-LEDGER.md`: passes in order, with operator rulings.
5. `research/`:
   - `session-review.md`: an independent review of the whole UI session against the code.
   - `backend-map-miniapps.md`: what the backend has today, committed and uncommitted, with paths.
   - `miniapp-sdk-ui-research.md`: prior art for add-on screens (json-render, A2UI, MCP Apps, OpenBB, LangGraph generative UI).
   - `bb-t3code-research.md`: bb, T3 Code and DeepSeek Harness (Cordis), read from source.

## The full conversation

The session transcript is `C:\Users\Mubarak\.claude\projects\C--Users-Mubarak-Desktop-QMX\063611de-0ca1-4b63-b06e-39c7614bb616.jsonl`. It runs over four days and was compacted three times; the operator's own messages are the authority.

## Where the UI stands

- **Screens:** Lab (Strategies and Pods benches), Portfolio (pods, live, road to live, kill grid), Library (shelves, where-used, templates), and Copilot (the desk: errands, sub-agents, panels the copilot builds, a drawer with activity, diff, terminal and browser).
- **Built, awaiting operator review:** Home (one tile board, Needs you), the Copilot "desk" (errands, receipts, drawer), and Settings (exchanges, servers, providers, MCP, copilots, mini apps, safety). Text base is 17px with a Text size setting.
- **Next:** Mini apps, then the start-up screen and day one with no demo data. The copilot terminal and browser are still demo (echo and iframe).
- **Data:** everything runs on labelled demo data. Every value needs a backend source before it ships.
- **Previewing:** run `pnpm build`, then `pnpm preview` (port 4173) in `apps/qmx-ui`.
