You are part agent C in the QMX unit-system planning run: the Level 1 architecture for journals, records and the Library's role. You inherit the Level 0 spine and write this part's own design with the bmad-architecture skill, headless. Four other part agents design the other parts at the same time, in their own folders; you never write in theirs.

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

## Read first
- `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\STATE.md` in full; "Operator round 2026-10-31 midday" with its rulings 1-23 is newest and binding.
- `architecture/00-ledger.md` (honour it by status; the rows for your part first) and `architecture/00-workflow-and-skills.md` sections 3 and 4 and step 5 of section 5 (your stack, payload and done-when; follow them).
- The Level 0 spine `architecture/level-0/ARCHITECTURE-SPINE.md` (binding and read-only for you; a conflict is surfaced in your file, never overridden), `architecture/01-connections.md` (the master your contracts must match), `architecture/level-0/blast-radius.md`, `architecture/level-0/LEAD-CALLS.md`, the review `architecture/review/R0-level-0.md` and how it was fixed, `architecture/funnel/versions/versions.md` and `GLOSSARY.md` (use its words).
- The funnel for your part: `architecture/funnel/solutions/00-index.md` and the journals solution file; `architecture/funnel/experience/design-thinking.md`, `problem-solving.md`, `ui-needs.md`; `architecture/funnel/edge-cases/catalogue.md` (every edge case your part owns must be handled in your design, by name).
- The second grounding `architecture/grounding/G4a-wrapup-session-node-library.md` and `architecture/grounding/G4b-qma-v2-session-agents-workflows.md` (the second grounding; where it corrects the first, it wins).
- The grounding for your part: `architecture/grounding/G1-algo-side.md` (journals, ledgers, the Library) and `architecture/grounding/G2-agent-and-platform.md` (local-first stack, storage, contracts). The grounding is today's state, not a limit: QML, the dictionary and most parts are being enhanced (his word, 31 Oct). Keep what is sound, change what blocks units, and say which is which.
- `research/12-data-feeds-lookback.md`, `33-data-depth-and-terms.md`, `research/funnel3/`, and the Library plans `D:\QMX-worktrees\unit-plan\tracker\qma-v2\DATA-PLAN.md` and `LOCAL-FIRST-PLAN.md` (read their indexes; open what journals touch).
- Skills, read each SKILL.md before use: `bmad-architecture` (`C:\Users\Mubarak\Desktop\QMX\.claude\skills\`), `codebase-design`, `principle-exhaust-the-design-space`, `blast-radius`, `principle-foundational-thinking` (`C:\Users\Mubarak\.claude\skills\`).

## His corrections of 31 Oct, late morning (STATE.md midday rulings 24-30; binding)
- Legacy code: be surgical, not frozen. QMA v2's agents, the copilot and mini apps took two weeks to ship and you lack their history: design within their realms and change only what is necessary, each change with its reason in one line (his words: if something needs to change, "we shall add it"). The copilot reaches almost the whole platform and discovers new tools on its own. Mini apps' limits exist by design for logging and monitoring; they are not bugs. At most, add a mini-app template that holds a unit, built only with what exists.
- QMB is called by agents as a tool (designed earlier; check G4 for what shipped).
- The trading node is the biggest task and may need a fresh start: about 97,000 lines is far too much for what it should do (set itself up on a server, set up the MIS and everything units need to trade autonomously, kill switches, risk and sizing). Only the node sends orders, by design, so the kill switch works. Linux because servers are VPSs. Weigh a refactor against a fresh start on the facts in G4a.
- Brokers: cTrader first; CCXT opened up beyond reading spot markets (perps, trading); Hyperliquid looked up and designed.
- Futures: design for futures accounts and every instrument now (he will likely use CME through a broker), so he is spoiled for choice later; no decision from him needed.

## Rules for running the skills
His voice is quotes only, from the transcripts or the ledger with line refs, checked by a script before you finish. Ignore the stale factory facts and `on_complete` endings in `C:\Users\Mubarak\Desktop\QMX\_bmad\custom\`; never write to `_bmad-output`; write only under your folder, by absolute path. Anything the ledger and the spine do not settle becomes a lead's call: propose a default, log it (what, why, how to undo) in your folder's `LEAD-CALLS.md`, and carry on. Never ask him anything. The merged code is checked out read-only at `D:\QMX-worktrees\engine-base-read\` (origin/engine/base, c93407ca); to run code, copy what you need into your own scratchpad, never write in that checkout. Stacked work: `git -C D:\QMX-worktrees\engine-base-read show origin/<branch>:<path>`.

## Your scope
The journal in depth, not one simple row shape: per unit from creation through backtest, stress, paper and live (units go back to paper; paper follows backtesting as its own phase), across instruments, brokers, accounts, platforms and trading nodes, with one record per instrument per broker. One writer per stream; how a unit's own journal feeds its self-tuning (the record side of the two speeds) without depending on the PC link or the Library being up (units stand alone: the node keeps a local journal and syncs later); the agent read door; recording into the Library; USD as the reporting currency; time in UTC with display per region; the views the UI needs. Historical market data is the Library's job: assume it is there, and define only what units, QMB and journals need from it.

## How to run
1. `bmad-architecture`, headless create: altitude epic, the Level 0 spine as parent (inherited decisions binding), brownfield (origin/engine/base), `doc_workspace` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\architecture\parts\C-journals-library\`. Run its reviewer gate in sequence: `lint_spine.py` to 0 findings, then the rubric and configured reviewers, each writing `reviews/review-<slug>.md` in your folder.
2. `codebase-design` on the part's modules and seams: small interfaces, depth inside, the deletion test.
3. `principle-exhaust-the-design-space` wherever a real fork exists; keep the losing options in the file with the reason.
4. `blast-radius` on the shipped files your part changes: prove by running real code the one fact each change is safe because of, or mark it unproven.
5. Research (Exa, context7) only for a fact your part owes.

## Your folder must hold
- `ARCHITECTURE-SPINE.md` (your part's spine) and, if it helps a builder, one file per sub-area, each with: what exists (path), what is added, what must not break, how it is checked (deterministic: script, compiler, linter or test), the edge cases it handles by catalogue id, the ledger rows that bind it, core or mini app with the reason, and the seam through which it grows later without rework.
- `CONTRACTS.md`: every shape your part owns or consumes, field by field, with its version rule, matched against `01-connections.md`; list any change you need there under "Contract changes" (you do not edit `01-connections.md`).
- `BUILD-SLICES.md`: the part cut into ordered, PR-sized slices a builder can take one at a time. Per slice: goal, files (paths), depends on, how it is verified (the deterministic check and the command), and what he sees when it works. The first slices make the smallest thing that runs end to end.
- `UI-NEEDS.md` (design intent for the UI session, no code) and `RISK-SIZING-POINTS.md` (every place risk and sizing plugs in, with today's placeholder).
- `LEAD-CALLS.md` and `reviews/`.

## Done when
Your spine lints to 0; every owned edge case is handled by name; every contract matches the connections master or is listed as a change; the build slices cover the whole part. Final message at most 10 lines.
