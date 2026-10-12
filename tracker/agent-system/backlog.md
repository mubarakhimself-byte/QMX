# Backlog (outside the agent-system map)

These items are deliberately **not** decision tickets on the map. Some are other efforts. Some are follow-ups that start once the map's decisions are made.
Every item stays here until it gets its own map, packet or session.

| Item | Why it's here | Trigger |
|---|---|---|
| **Library v2** | The operator wants a new version of the Library. It hasn't been looked at yet. The UI gave a better picture of it. May be handled in this planning session. Open: two agents editing the same item, confirming a write really landed, reach across Lab and Portfolio (ticket 18). Today it is `library.db` (FTS5) plus `artifacts/<sha>`, and agents can write to it (`qmx-internal.md` §b.5, §d.1 item 9). | After map ticket 04 settles tool access to it. |
| **WF1/WF2 rework** | The operator handles it himself. It is tied to the risk and sizing session's changes. Origins and fate are in `qmx-internal.md` §c.1. | The operator says go. |
| **Documentation update** | The `docs/` corpus still carries old rulings (`qmx-internal.md` §e item 11). Run `/documentation-factory` in change mode once the map is ratified. | Map destination reached. |
| **pstack install and configuration** | **Installed 2026-10-12** (48 skills in `~/.claude/skills`, minus `tdd`, `teach` and `make-bot-ui`; agents `poteto-agent` and `comment-sicko`; Claude-only model roles in `~/.agents/pstack-models.md`). The standalone mirror `backnotprop/pstack` (MIT) works in Claude Code. Install it selectively before shipping starts. Skip its `tdd` and `teach`, which clash with the Pocock skills already installed. Set its models to Claude-only roles so it doesn't route work to Grok. Avoid the expensive multi-model skills (`arena`, `swarm`, `interrogate`) by default. | Before the first shipping session (map ticket 16). |
| **P16c: retire the old QMA runtime** | Running in its own Claude session. | Its own summary. |
| **UI wiring** | The UI on `ui-review/repair` gets wired to the backend in its own session. The map only fixes what the UI shows (ticket 11). | After tickets 03, 11 and 16. |
| **Lab default workflows and the research harness** | Enhance what P10, P15 and P19 shipped. Also listed in the map's "Not yet specified" section. | After the WF1/WF2 rework and tickets 02 and 04. |
| **Post-deletion check (P16a-c)** | P16 removed a lot of old code. Before trusting anything, find out what still works end to end: QMA, mini apps, and QML, QMF and QMN, because everything was connected (operator, 2026-10-12). Includes the logs and DevOps lens needed to see damage. | After P16c's final summary. |
| **QMB review** | QMB was meant to be a tamper-proof backtest CLI that agents call like a tool (built by combining QuantConnect Lean CLI, Jesse and other frameworks). Many models have edited it since. It still starts the old `qma.daemon` (`qmb/doors/cli/host.py`), keeping ~110k old lines alive, and its pair, revoke, rotate, recover and configure commands have no new replacement. The operator will retrieve the original QMB sessions. | Once QMX is in normal use. |
