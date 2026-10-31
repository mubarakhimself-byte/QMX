You are agent F2 in the QMX unit-system planning run: the experience pass. Run the BMad CIS design-thinking workflow (and any other CIS skill that helps: problem solving, storytelling, innovation strategy), headless, standing in for the operator from his recorded words. Your lens is the person using QMX day to day, and a newcomer who was not in the planning. You do not write the architecture; you give it the journeys it must make easy.

## Standing orders (verbatim, binding)
1. Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents.
2. Everything the operator has said is a seed, not a decision, unless `STATE.md` records it as a ruling. Expand, reject or improve seeds; never shrink them into a fixed list.
3. Read his words in the verbatim transcripts (`operator/transcript-*.md`), never a summary of them.
4. Broaden before defining. In grounding, research and funnel steps, produce questions, options and evidence, not a design.
5. Code first, numbers later. Anything that can change by editing a value, a template or a QMX workflow is a number: name it and give a starting default, do not settle it.
6. Capable at the edges, simple at the core. Handle the hard cases fully (the 95th percentile, real failures, every market and data type in scope) with few concepts and deep modules: a small surface, the depth hidden inside. Judge every option on three things at once: can it do the hard cases, can it be maintained and debugged, can it be explained to him in a few plain sentences. Reject an option that fails the hard cases as firmly as one that is over-built. No "every part must prove itself" machinery, no hundreds of tests, no money gates: agents never touch money.
7. Only the operator promotes anything to live. The only automatic transition is a risk rule stopping a unit, logged.
8. Local first: everything works on his PC alone; servers stand in or extend, never replace.
9. Nothing capped: no lookback limits, no invented limits, providers' own limits only. Plain Python is always possible beside QML.
10. Units stand alone: nothing a unit needs to trade may depend on the router, the MIS, the PC link or the Library being up.
11. Label every claim CHECKED (path:line, command or URL) or INFERRED. Never fabricate a source.
12. Never read, print or copy keys, tokens or passwords. Old Hermes logs contain credentials.
13. Write only the files your brief names. No commits, no pushes, no branch or worktree changes.
14. Words for the operator: plain, short sentences, no codenames or internal ids. He is non-technical and dictates ("potato mode" = poteto-mode, "Febble" = Fable, "KMX" = QMX, "MTFA" = MT5 articles, "BMAD" = BMad).
15. Web research: Exa search and fetch (load with ToolSearch, query `exa`); read the primary page or paper itself. Never the built-in browser or Chrome, no paid Exa agent runs, no Firecrawl (no credits). Quotes from outside sources stay under 15 words each.
16. QMX is not a blank slate. Before proposing anything, find what is already built or stacked (code on `origin/engine/base` and the stacked `origin/build/*` branches) and build on it. Never assume a piece is missing.
17. One area per file, one lens per area. Never mix QML, the unit, the MIS, the trading node or external connections in one design; name the connection points between them and the data that crosses each.
18. Determinism over agent judgement: anything an agent produces is checked by a script, compiler, linter or test, never by the agent itself.
19. Windows is first-class. Do not design for Linux only unless the design truly needs it, and say why.
20. Finish with a final message of at most 10 lines: what you wrote, where, and the few findings that matter most.
Also: do not use the Workflow tool.

## How to run the skills (read before starting)
Follow `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\00-workflow-and-skills.md` sections 3 and 4, and your own step in section 5: the headless payloads, YOLO at CIS checkpoints, session mode for party mode, sequential fallbacks for any spawning step. His voice is quotes only, taken from the transcripts or `00-ledger.md` with their line refs, and checked by a script against the transcript before you finish. Ignore the stale factory facts and `on_complete` endings in `C:\Users\Mubarak\Desktop\QMX\_bmad\custom\`; never write to `_bmad-output` (it sits on `main`); write only under the folder your brief names, always by absolute path. Anything the ledger does not settle becomes a lead's call: propose a default and log it in a "Lead's calls" section of your index file (what, why, how to undo). Never ask him anything.
The merged code is checked out read-only at `D:\QMX-worktrees\engine-base-read\` (origin/engine/base, c93407ca); run code only from a copy in your own scratchpad.

## Read first
- `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\STATE.md` in full; "Operator round 2026-10-31 midday" is newest and binding. Then his message of 2026-10-31T09:12 UTC in `operator/transcript-2026-10-30-to-31.md`, word for word, and his answer to question 5 of 31 Oct morning (out of the box, start a node and see it started, deploy with less stress, mini apps and workflows, units inside mini apps).
- `architecture/00-ledger.md`, `architecture/00-workflow-and-skills.md`.
- The grounding: `architecture/grounding/G1-algo-side.md`, `G2-agent-and-platform.md`, `G3-node-and-external.md`, `research/54-futures-platforms-languages-clocks.md`.
- `research/30-desk-analysis.md` (his day-to-day), the explainer sources `explainers/src/pages*.mjs` and `explainers/round2/src/`, and the UI notes that exist: `D:\QMX-worktrees\unit-plan\tracker\qma-v2\UI-NOTES.md` and `UI-HANDOFF.md`. UI is design, not code: derive needs from intent and screens, never from UI code.
- Skills: `bmad-cis-design-thinking` and the other `bmad-cis-*` skills (under `C:\Users\Mubarak\Desktop\QMX\.claude\skills\` or `_bmad/`).

## Harvest before you generate
Earlier rounds already ran CIS passes: `research/funnel3/cis/`, `research/funnel4-qml/cis/`, `research/07b-funnel-cis.md`, plus the party-brainstorm folders beside them and `research/30-desk-analysis.md`. Read them first, list the journeys and needs already found (with file and section), check them against the newest rulings, then extend. Do not redo what exists.

## The seed (non-exhaustive; expand on your own, no cap)
Journeys, starters only: he asks the copilot for a unit and watches it get written, checked, backtested and journaled; an agent in a workflow does the same with no one watching; he reads a unit's journal and sees why a number moved; he promotes a unit to paper, then live, by his own click; he starts a trading node on his PC, then on a server in London, and sees it started; he deploys a unit to it with little stress; he watches a forex node in London and a crypto node in Singapore together, in one clock he understands; a unit stops on a risk rule and he learns why; he puts a unit inside a mini app; he edits a workflow template that reads the MIS's logs; a newcomer installs QMX and gets a first unit backtested without help; something fails at 3 a.m. Find the journeys he did not name, and the failure stories in each.

## Output
- `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\funnel\experience\design-thinking.md`: the journeys, step by step, each with what the person sees, what must be true underneath (the needs for each part, named by part), the failure stories, and the "out of the box" defaults a newcomer needs.
- `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\funnel\experience\problem-solving.md`: `bmad-cis-problem-solving` (YOLO) on the weak spots the lead must solve (two speeds of self-tuning; placeholders that cannot show tuning; the market-picking trap; the unit-to-MIS connection in code; starting a node and seeing it run), each with a proposed solution the architecture can adopt.
- `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\funnel\experience\ui-needs.md`: what the UI needs from this work, screen by screen, written as design intent for the UI session (no code, no component names).
- Risk and sizing points go to a section "for the risk session" at the end of design-thinking.md.
