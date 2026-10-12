# QMA v2 backlog (everything outside the first build)

This replaces `tracker/agent-system/backlog.md`, which is now archived.
- Items here are deliberately not in the first shipping slices.
- Each one stays until it gets its own slice, session or decision.
- "Easy win" marks items that are small, low-risk and useful early.

| # | Item | What and why | Trigger | Easy win? |
|---|---|---|---|---|
| B1 | **SQLite corruption-bug exposure** | Python 3.14.6 here bundles SQLite 3.50.4. The WAL-reset bug is fixed only in 3.51.3. qmx-control opens a new connection per call, so two writers can collide (HOW-WHY G2; research 30). Fix: one writer task per database file, or a newer SQLite build. | Before any QMA v2 table lands | Yes. Likely slice 0 |
| B2 | **GitHub CI has never run** | Every "green" so far is a local `just ci` (HOW-WHY). Set up a GitHub Actions run of the same suites so shipping PRs show real checks. | Early in shipping | Yes |
| B3 | **Pin both SDKs** | `openai-agents` is in no lockfile. `claude-agent-sdk` 0.2.163 is pinned only because of the old daemon; deleting the daemon drops the pin (HOW-WHY). | Slice 0 | Yes |
| B4 | **P16c finish and leftovers** | DONE 2026-10-12 night. 13 PRs (#58-#70); qma-daemon 74,104, qma-core 23,808, qma-wire 15,435 lines left, all kept alive by `qmb/src/qmb/doors/cli/host.py:104` (see START-HERE D2). Then read its final summary: lines left per package, kept modules and their blockers. Copy the Claude driver recipe (`native_claude.py`, `native_codex.py`, `native_sessions.py`) before any later deletion. | When P16c ends | Reading only |
| B5 | **Post-deletion end-to-end check** | P16 removed a lot. Check what still works end to end: mini apps, QML, QMF, QMN, the two example apps (`weekend-watcher`, `macro-daily-bias`). | After B4 | No |
| B6 | **Branches: set up `integration` and `staging`** | The operator's model is integration → staging → main. `integration` isn't ready to take code (operator, 2026-10-12), so QMA v2 ships into `rebuild/base` for now. Later: fold `rebuild/base`, create `staging`, clean up 61 worktrees and 73 local branches. Deletion only with his go, branch by branch. | After the first QMA v2 slices land | No |
| B7 | **QMB review and reorganisation** | A tamper-proof backtest tool that agents call like a tool. Many models have edited it. Dead helpers in `qmb/src/qmb/doors/cli/host.py` keep about 110k old QMA lines importable; `qmb host start` itself already runs qmx-control (PR #49). Editing QMB needs his authorisation. | Once QMX is in normal use | No |
| B8 | **Library v2** | Seam designed now: a git-style object model in SQLite (content-addressed blobs, immutable versions, refs for variants), research 30. Full refactor later. Open: the Library's real name (he said it "starts with A"). | After QMA v2 core | No |
| B9 | **QML changes** | Proposal from the risk-and-sizing session. | His other session | No |
| B10 | **WF1/WF2 rework** | Tied to risk and sizing. He handles it. | He says go | No |
| B11 | **Documentation update** | Run `/documentation-factory` in change mode once QMA v2 ships. Also: update the project `CLAUDE.md` pipeline text, and the global `CLAUDE.md` bulk-worker line (still Opus 4.8; his rule is Opus or Sonnet 5.5). Ask before editing either `CLAUDE.md`. | After the first release | Partly |
| B12 | **UI wiring session** | The SvelteKit UI on `ui-review/repair` gets wired to the QMA v2 event protocol (research 32), browser-first. Its own session. | After the turn host and event protocol land | No |
| B13 | **Lab default workflows and the research harness** | Built-in templates beyond the first set (catalogue in research 22), and the research harness rethought. | After the graph runner ships | No |
| B14 | **Phone approvals while the PC is off** | With no owned server, this needs a small paid relay or push service (HOW-WHY X9). His call. | He decides | No |
| B15 | **Voice / conversational mode; "System 1" models** | Wanted later (GPT audio). | Later | No |
| B16 | **MCP apps** | Discussed in the UI session; not designed yet. | With B12 | No |
| B17 | **cTrader screen-automation spike** | Measure how much of cTrader is drivable (UIA) before computer-use work. Was ticket 12. | Before computer-use slices | Yes, a checklist |
| B18 | **Firecrawl Alexandria** | Providers catalogue for web and documentation work. Was ticket 14. Not researched yet. | When the research tools get built | Yes, research |
| B19 | **His own backlog** | He mentioned a personal backlog beyond the UI one. It was never found in the repo (only `queue/TEMPLATE.md`). Ask where it lives. | Tomorrow's questions | Yes, a question |
| B20 | **Spin ideas not in the first build** | `USER-JOURNEYS.md` §3 proposes 25 ideas. The ones not taken into the first slices wait here for his review. | After he reads them | No |
