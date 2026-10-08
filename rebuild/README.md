# QMX rebuild: work packets

The design is in `DESIGN.md`. Evidence and research are in `research/`. Packets are in `packets/`.
Packets are written for a coding agent (Codex) to run without further operator input. Claude reviews each PR.

## Rules for every packet

1. **Branch.** Start from the latest `rebuild/base`. Name the branch `rebuild/pNN-short-name`. Open a PR into `rebuild/base`. Never touch `main`, `integration` or `ui-integration`.
2. **Scope.** Do only what the packet says. If you find something else worth fixing, write it under "Found, not fixed" in the PR description.
3. **Tests.** Every packet ends with commands that must pass. Run them and paste the summary lines into the PR. Never lower thresholds or skip tests to make them pass. If a test is wrong, say why in the PR.
4. **No ceremony.**
   - No decision IDs in code comments.
   - No evidence folders, ledgers or reports in the repo.
   - Comments say *why*, in plain words.
   - The PR description is the only report: what changed, test summary, anything found.
5. **Keep it small.** Prefer deleting code to adding it. No new abstraction without two real callers. Use library features before writing your own (see `DESIGN.md` §3).
6. **Python.** Use `uv`. The workspace pins Python 3.14. Strict typing stays on where it is on now. Format and lint with the repo's ruff config.
7. **Secrets.** Never commit keys. Read credentials from Windows Credential Manager entries `qmx/*`. Live model calls only in scripts under `scripts/live/` that the operator runs; never in the test suite.
8. **Never guess a library API.** Before coding against any library or service, read its section in `rebuild/REFERENCES.md`. `curl` the listed docs (llms.txt or raw markdown) into a scratch folder outside the repo and follow them. If something isn't covered there, say so in the PR instead of inventing it.
9. **Backend only. No UI work, no Reticle.** `apps/qmx-ui` on this branch is the old, scrapped UI. Don't touch it, run it or verify against it. The real UI lives on `ui-review/repair` and is wired later by Claude. Prove backend work with tests and REST/MCP calls, not browser tools.
10. **Package layout.** New packages go under `qmx-agents/packages/<name>`, like `qmx-agents`. `qmx-apps` and `qmx-control` currently sit at the repo root; P16 moves them, so don't add more root-level packages.
11. **Commits.** Small commits with clear messages. Author identity: the configured Codex identity, not the operator's name.

## Order

| # | Packet | Depends on | Size |
|---|---|---|---|
| 01 | Green test baseline | — | S |
| 02 | CI that actually runs | 01 | S |
| 03 | Git and branch inventory (report only) | — | S |
| 04 | Delete dead code and clutter | 01 | M |
| 05 | Survival map of the QMA daemon (report only) | 04 | S |
| 06 | `qmx-agents` package: AgentSpec and model router | 01 (see DESIGN §12) | M |
| 07 | Memory provider | 06 | M |
| 08 | Guards: journal, admission, money path, budgets | 06 | M |
| 09 | Domain tools and MCP servers | 06 | M |
| 10 | Workflow graph spec and LangGraph compiler | 06, 09 | L |
| 11 | `qmx-control`: one service layer, REST and MCP doors | 06 | M |
| 12 | Mini-app definition, volume and T1 supervisor | 11 | L |
| 13 | App storage, backup and restore | 12 | M |
| 14 | Road to live (port MA02–MA04) | 12 | M |
| 15 | Copilot agent and first end-to-end app | 07–14 | L |
| 16 | Retire the old QMA runtime | 15 | L |
| 17 | Docker tier for nodes (T2) | 12 | M |
| 18 | Brokers, connections, accounts (cTrader/IC Markets, CCXT) + `qmx-broker` MCP | 08, 09 | M |
| 19 | Research sources: MQL5 scraper app, Firecrawl MCP | 12 | S |
| 20 | Copilot skills and hooks (skills by Claude with operator; hooks by Codex) | 11, 12 | M |
| 21 | Remote runs: own VPS first (SFTP bucket), then Amp/Modal/E2B; Git-style results, fetch and resume; GPU targets | 10, 12, 13, 17 | L |
| 22 | Library, run index, result memo, caching, weekly GitHub backup | 08, 11 | M |
| 23 | Fix the two recurring CI failures (watcher startup, Linux mklink) | 12 | S |

Packets 01–05 can start today. P05 is reviewed (DESIGN §12): read those rulings before any later packet.
