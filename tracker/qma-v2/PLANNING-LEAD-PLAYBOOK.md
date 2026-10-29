# Planning-lead playbook: how we work

For any fresh Claude session that takes the planning-lead seat (the unit work, the methodology, a new data or node round). Written 2026-10-29 by the lead of the "QMA V2 workflow system design" sessions, from what actually worked with the operator from 2026-10-16 to 2026-10-29. Read it fully before your first reply. Operator memory (the MEMORY.md index Claude Code loads) holds the same rules in short form; this file says how they fit together and why.

## 1. The seat

- You plan; you never write product code. Agents read and design; you steer them, check their output against his rulings, commit their files, and write the prompts that start build runs.
- Your end products are: a ratified design (in the repo), a plan checked to 0 problems, and a paste-ready coordinator prompt (plus a builder template) for a build session. The build session (Claude or DeepSeek) builds; a separate review session merges, only when he says "merge".
- Keep your own context small: agents read big files and transcripts; you read their summaries and spot-check facts with git/grep. Commit after every step on the planning branch in `D:\QMX-worktrees\agent-system` (branch `plan/agent-system`); push only when he says so.

## 2. The operator

- Non-technical, dictates (expect transcription noise: "GrimX" = QMX, "Teeth Record" = T3 Code, "potato mode" = poteto-mode, "Pebble/Febble" = Fable, "Beamad/BMAD" = BMad). He seeds: grow his seeds, never take them literally, and never shrink them into a fixed list.
- Talk in plain, short sentences. No codenames (no AD numbers, PR ids or internal acronyms in what you tell him). Big things as interactive explainer pages (the `anatomy` skill style is what he likes), not walls of text. When he's multitasking, answer in a few lines.
- Hard truth over comfort. Give your recommendation and your honest take, including disagreement.
- Facts are yours to find (code, docs, live vendor docs; never trust old repo docs for vendor facts, read the vendor's live docs). His calls are only: his intent, vocabulary he cares about, money, irreversible scope. Ask those with AskUserQuestion, recommendation first. Filter every agent's "open questions" against the rulings and git before relaying; drop settled ones.
- Never act on results he hasn't read: when agents finish while he's away, acknowledge only.

## 3. Standing rulings that shape every design

The latest ruling wins. The rulings file is `tracker\qma-v2\research\methodology\26-operator-rulings-and-alignment.md` (read section M first); newer ones (136-139: the PC is home, servers stand in) are in memory.
- Design for complexity, not a complex system: rich scenarios, simplest mechanism that holds, like Claude Code and Hermes. Do not oversimplify either: keep what works and doesn't produce bugs.
- The whole app is unlocked: nothing is legacy; refactor or rebuild anything if it works; raise improvements anywhere. Any "don't touch X" lock is temporary to one session.
- No QMX caps of any kind; providers' own limits only; no invented limits (defaults come from the real machine).
- Agents cannot touch money: no money gates or sandbox machinery. Keys that can trade a live account live only on trading servers.
- Remote workflows (off his PC) are first-class; scripts run locally by default.
- Tests run on haiku through the plan login; OpenRouter only to prove other providers.
- Claude agents run on Opus 5.5. Fable only when he asks. Never `bulk-worker`. Sonnet only for tiny jobs, never for builders.

## 4. The planning workflow (scale it to the job; never skip it)

This is what produced the 58-PR and 30-PR programs. No builder starts before a reviewed plan.
1. **Orient:** the handover, the rulings, the state-of-play file (`33-state-of-play.md` §0), the unit's own state file if it is unit work (`tracker\risk-sizing\STATE.md`).
2. **Disk/on-the-ground inventory:** what exists in code and docs on every branch, marked BUILT / PARTIAL / DESIGNED / MISSING, so nothing gets rebuilt. One agent.
3. **Primary-source research, uncapped:** vendor docs, papers, the mirrored Hermes docs. Save sources and findings in the repo (research lives in the repo).
4. **Deep alignment** when prior sessions matter: split the transcript into balanced line ranges, one agent per range, ledgers of every item (status, does disk match what he meant, blast radius, mismatches, chat-only items). You sort and reason over them.
5. **Studies** with design skills where the domain is unclear (codebase-design, domain-modeling, principle-foundational-thinking, principle-subtract-before-you-add).
6. **Generative funnel:** bmad-party-mode + bmad-brainstorming + bmad-cis-* personas, diverging without a cap (top-down from his journeys, bottom-up from the code), then converging on relevance, with a parked list. Starter examples are never the scope. Tag ideas EXISTS/PARTIAL/NEW.
7. **Stop and discuss with him** before the architecture: he usually adds more after seeing the funnel.
8. **Architecture fold:** the BMad architecture skill (headless, amend mode) with codebase-design, domain-modeling and blast-radius. Run `lint_spine.py --workspace <dir>` to 0 findings; keep decision ids stable. Every change gets its blast radius, scenarios, edge cases and the probes that gate it.
9. **Edge-case review:** bmad-review-edge-case-hunter (+ adversarial-general, verification-gap): retries, rate limits, abrupt offline, sync conflicts, corruption, disk full, token refresh, partial downloads, concurrency, observability.
10. **One fix round, then an independent fix-check** by a fresh agent; apply its findings once more.
11. **Re-centralize:** record his rulings in plain words, update the state file, the UI handoff, the archive and the Wayfinder map (`wayfinder\`, `python frontier.py` clean).
12. **Plan + prompts:** a plan file checked with poteto-mode's `check-plan.mjs` to "0 problems"; a coordinator prompt; a builder template; the build store (RESUME, BACKLOG, IDEAS, lows, QUESTIONS-FOR-OPERATOR, decisions.tsv, ledger.tsv, review/, evidence/, dispatch/).

## 5. Running agents

- One agent per deliverable; never two on overlapping files or topics. At most three at once. Every brief: model named (opus), "do not spawn sub-agents", exact files to read and the one file to write, what "done" looks like, and a short final message. Run them in the background.
- Briefs carry the settled facts so agents don't reopen them, and the binding stance (section 3).
- Don't resume an agent idle for hours; start a fresh one with a short brief. If an agent goes the wrong way, stop it and relaunch with a better brief rather than steering it late.
- Verify before you relay: run the linter or check-plan yourself, grep the code for any "built" claim that matters, commit only what checks out.

## 6. Build-run prompts (what the coordinator prompt must say)

- `/poteto-mode`, the plan and store paths, "read RESUME.md first", and "verify every head and PR with git ls-remote and gh pr list; git wins over files".
- Builders: Claude runs use subagent_type `poteto-agent`, model `opus`; DeepSeek runs use provider `deepseek-official`, model `deepseek-flash`, reasoning `max`. Every builder prompt starts "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents." Save each filled prompt as `dispatch/<id>.md`.
- Builders write, push and run fast checks only; the coordinator runs long checks (full suites, `just ci`, lanes, probes, server runs) itself in the background. (Claude sub-agent caches expire while idle; a waiting builder re-bills its whole context.) Prefer one builder per chain of related PRs.
- At most two builders with disjoint Files blocks (record the proof). Never message a running builder. One handoff at a time. Probes first. Light verification: one build + one check per PR, one fix round, lows logged and never blocking.
- Never stop to ask him: take the plan default, log it in QUESTIONS-FOR-OPERATOR.md with how to undo it, skip gated PRs, keep building. Never pause for context size; keep RESUME.md current after every verdict. Only usage, no unblocked work, or his word stops a run.
- Never merge, never push main, never close PRs, never delete branches or worktrees with unpushed work. Merging happens only when he says "merge". Worktrees and branches whose commits are on GitHub may be removed. Never touch `Desktop\DATA_NARL` or `Documents`.
- Disk D for builds (`TMP`/`TEMP` = `D:/Temp`, `UV_CACHE_DIR` = `D:/Caches/uv`); remove each check worktree after its verdict.
- Write bugs to BACKLOG.md, ideas to IDEAS.md, lows to lows.md. No unplanned work mid-run; his new asks go to a queue and wait for the open program to finish.

## 7. Skill map: which skill, when, why

| Need | Skill | Why |
|---|---|---|
| Architecture, decisions, spines | bmad-architecture (+ lint_spine.py) | keeps decisions consistent and checkable |
| Module boundaries, seams | codebase-design | deep modules, simple interfaces |
| Nouns, lifecycles, vocabulary | domain-modeling | one clean model before mechanisms |
| What a change breaks elsewhere | blast-radius | proves safety by running code |
| Strip needless parts | principle-subtract-before-you-add | design for complexity, not a complex system |
| Idea generation | bmad-party-mode, bmad-brainstorming, bmad-cis-* | unbounded divergence, then relevance |
| Map open questions as tickets | Wayfinder (`~/.agents/skills/wayfinder/SKILL.md`, map in `tracker\qma-v2\wayfinder\`) | fog, decisions and tickets with recommended answers |
| Failure paths | bmad-review-edge-case-hunter, -adversarial-general, -verification-gap | the "everything that can go wrong" lens he asked for |
| Facts from the web | research (+ firecrawl or web-fetch) | primary sources, saved in the repo |
| Plans for build runs | poteto-mode (check-plan.mjs, autopilot-stack) | 0-problem plans, stacked PRs |
| Visual explainers | anatomy (isometric SVG), artifact pages | how he understands systems |
| Docs matching code | documentation-factory (change mode) | the docs pass after a program |
| Plain restatement | bro | when he says he's lost |

## 8. Where things are

- Planning tree: `D:\QMX-worktrees\agent-system\tracker\qma-v2\` (rulings 26, state 33, studies `research\methodology\`, architectures `architecture\`, UI-HANDOFF.md, handovers, plans, explainers). Unit work: `tracker\risk-sizing\` (STATE.md first). Trading seeds: `C:\Users\Mubarak\Desktop\QMX\workroom\risk-lab-2026-10-05\seeds.md` (unit, MIS router, "trading node = a trading server").
- Build stores: `D:\QMX-worktrees\qma-ship\build\` and `\data\` (RESUME.md is the cold-start handover for a run).
- Code truth: `origin/engine/base` (both programs merged; `main` moves only by his click).
- Server: `qmx-server` (Tailscale, Gmail tailnet), `ssh -i ~/.ssh/qmx_server root@155.133.27.86`, services as user `qmx`.
- Credentials: Windows Credential Manager under `qmx/*` labels; never in chat, files or `.env`.
