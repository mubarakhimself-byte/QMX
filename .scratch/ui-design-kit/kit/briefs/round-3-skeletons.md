# Round 3 builders: three skeletons to compare

You are one of three builders. Read `round-2-shared.md` in this folder first; every rule in it applies to you (the owner, the skills to invoke, the app, the data, what you may touch, how to check, how to report). This file adds the question of this round and what all three builders must build so the results can be compared.

## The question

QMX's UI was a tiling board of widgets on every screen. Grounding now says that is the wrong skeleton. Read these two files before designing; they are the reason this round exists:
- `../refs/grounding/10-shapes-from-journeys.md`: what the owner is doing in each of QMX's 15 journeys. Watching several live things, which is what a board is for, is the main shape of 2 of them. Conversing, deciding on evidence, guided steps and reading in depth are the rest.
- `../refs/grounding/09-extensible-ui-models.md`: how extensible interfaces are structured, from the problem first, then design principles, then products as evidence. Note its findings: no real product uses one model alone; what keeps extension UI consistent is who draws it; QMX's backend already has typed objects with actions (Library kinds, the unit lifecycle, app operations) and a chat that can open views.

So nobody is asked to replace the board with one other thing. Each builder builds a **hybrid with a different thing at the centre**. The board survives in each as one kind of page, where he watches and arranges. Do not copy the earlier Board route; reuse its components.

The three options:
- **Objects first** (`/concepts/objects`): the app is organised around his things. A unit, a run, a session, a workflow each has its own page with its state, its evidence, its history and its actions. Lists lead to pages. Two places are boards he arranges.
- **Copilot first** (`/concepts/copilot`): the conversation, and what it opens beside it, is the skeleton. He must never have to type to see his money: pinned views open by themselves.
- **Day first** (`/concepts/day`): what needs him, what happened and what is coming is the front door, and it leads into pages for his things. Boards are a view he switches to.

## What every builder builds, so the three can be compared

The same five moments, with the same demo data (`src/lib/shell/data.ts`), each reachable by clicking from the first screen:

1. **Morning.** He opens the app. Two proposals and one approval wait, a workflow failed overnight, one unit is live and three are on paper, jobs are running on This PC and one server.
2. **Decide.** He opens the proposal "Promote Gold breakout to paper", sees the evidence (the judge's verdict, tries counted, a result chart, costs), and clicks Promote or Not yet. One decision, evidence and button together.
3. **A unit in depth.** Gold breakout's own page: state per market (live on XAUUSD), results, journal, where it runs, its actions (pause, back to paper, retire). Preview first, detail one level down.
4. **Converse.** A copilot session that is working: two helpers visible with what each is doing and where it runs, tool calls folded to a line, one inline approval he can allow or reject, a result opening beside the chat. Scripted is fine; say "demo" on screen in a word or two.
5. **Watch.** Live trading: the units trading, open positions, the nodes. This is where a board he can arrange belongs; show it as one.

Plus, in every option:
- **Navigation** that fits your skeleton: short, floating or inset, never scrolls, collapsible, mini apps as a detached group in their own colours. A fast way to reach anything (the command field with Ctrl+K, or your better answer).
- **The Lego proof, working in the demo**: one thing he adds, one he removes, one he rearranges, and one piece contributed by a mini app, marked as a guest. Say in your report what the unit of extension is in your skeleton (a page, a section on an object's page, an action on an object, a view the copilot opens, a card kind) and what a mini app would have to supply.
- **Always in view**: where work runs, what is running, what waits for him, market clocks, and a stop for trading with levels (pause new trades, stop a node, close everything).
- **Day one** (`?data=first`) for the Morning screen, and the **worst case** (`?data=worst`) holding up on all five moments.
- `src/lib/concepts/ConceptPicker.svelte` rendered with your `current` value (`objects`, `copilot` or `day`), so the reviewer can flip between options.

## What you own

Only `src/routes/concepts/<your option>/` and `src/lib/concepts/<your option>/`. Everything else is read-only, including `src/lib/shell/` (another builder is finishing work there) and `src/lib/qmx/`. If you need a component changed or a new icon, build what you need inside your own folder and say so in the report.

## Depth over breadth

Five moments done properly beat nine places sketched. Journeys are hints: where a moment needs something the data file lacks (a journal line, a verdict detail, a helper's status), add realistic demo values in your own folder. Take one real visual risk you can defend and keep the rest quiet. In your report, add one honest line on what your skeleton does worse than the other two.
