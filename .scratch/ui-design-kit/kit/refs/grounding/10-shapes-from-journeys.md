# 10 What the journeys ask of the UI

Written by the design lead, 2026-11-10, to answer one question before any new concept is built: **does the widget board still stand as QMX's skeleton, and if we change, why?** It reasons from QMX's own journeys and the owner's words, not from other products. Product research is in `09-extensible-ui-models.md`.

Sources: the 15 journeys in `08-qmx-today-for-design.md` section 5; the normal day in 08 section 1; `INTENT.md`; `refs/his-words-october.md` (message numbers as M); backend code at `3ae41ffc`.

## 1. What he is doing in each journey

Each journey gets its main shape and, where it has one, a second.

- **Converse:** say what he wants and steer an agent that does it.
- **Decide:** look at evidence and click yes or no.
- **Read:** take in one thing in depth (a result, a journal, a unit).
- **Flow:** go through set steps once (sign in, connect, publish).
- **Watch:** keep an eye on several live things at once.
- **Configure:** set something up and leave it.

| # | Journey | Main shape | Second |
|---|---|---|---|
| 1 | First start | Flow | |
| 2 | Idea to a judged unit | Converse | Read |
| 3 | Copilot writes a unit with live checks | Converse | Watch |
| 4 | Overnight agent builds units; morning proposals | Decide | Read |
| 5 | Promote to paper on his click | Decide | Read |
| 6 | Start a trading node, sign in to the broker | Flow | |
| 7 | Deploy a unit to a node, then withdraw | Flow | Decide |
| 8 | "Why didn't it trade at 08:00?" | Converse | Read |
| 9 | A unit stops on a risk rule; resume, back to paper or retire | Decide | Read |
| 10 | Build and publish a workflow from one sentence | Converse | Flow |
| 11 | Watch runs and fix a failure | Watch | Decide |
| 12 | Watch the copilot work: helpers, tools, approvals | Watch | Decide |
| 13 | Install a mini app and use its tools in chat | Configure | Converse |
| 14 | Download data and see its coverage | Flow | Read |
| 15 | Usage and providers | Read | Configure |

**Count of main shapes:** Converse 4, Decide 3, Flow 4, Watch 2, Read 1, Configure 1.
**Counting main and second together:** Read 7, Decide 6, Converse 5, Flow 5, Watch 3, Configure 2.

The normal day says the same (08 section 1): workflows run overnight; in the morning he reads what needs him and the proposals; he asks the copilot for something; he clicks to promote what passed; he "glances at nodes and alarms".

## 2. What a board of widgets is for

A tiling board is built for **Watch**: many live things at once, arranged by the person watching. It is also good at **Compare** when two things sit side by side.

It is a poor fit for the rest:
- **Converse** wants one conversation with room, and the thing being made beside it.
- **Decide** wants the evidence and the button together, one decision at a time.
- **Read** wants one thing with room and depth.
- **Flow** wants steps in order.

So the board's home shape is the main shape of 2 of the 15 journeys, and a part of 3. Used as the skeleton of every place, it forces the other 13 into tiles. That matches his own complaints about the board-based screens: "more words than actual intentionality", cramped panels, detail views that were "very poor", settings he "can't click a thing" in.

His own words already point the same way:
- Portfolio: "one of the few pages I would rarely interact with… it's just for me to see" (M28). That is Watch, and the board suits it.
- "I really do prefer using the copilot… it should be able to control anything" (M32). That is Converse.
- The Lab: "do we need the lab?"; its role may be "a representation of complex artifacts" (11-09). That is Read and Compare.
- Starting something new: "think of it like a survey… walk me through" (M23). That is Flow.

## 3. Why widgets were chosen, and whether that reason still holds

He chose widgets for three reasons (storyboard; M19; M21):
1. **Extensibility.** Widgets were the one pattern he knew where new things slot in.
2. **Space management.** Minimise one thing and the rest fill.
3. **Many things open at once.**

What is true in the backend now:
- **There is no widget, layout or dashboard object in the code.** Checked by search. Two traces only: the backtester strips fields named `ui_widget` and `ui_view` from its stream on purpose, and one workflow template describes a planned check of "each widget" of a mini app "fitting its slot". The intent existed; nothing implements it.
- **What a mini app adds today** is a whole screen (sandboxed HTML), tools the copilot can call, skills, jobs and workflows. A whole screen is a page, not a tile.
- **What else is extensible today**: workflows and their templates, Library item kinds with schemas, providers, machines, data sources, rules. None of these is a tile either.
- The copilot can put fixed block kinds into a chat (`panel`, `table`, `entity`, `artifact` and others).

So reason 1 no longer needs widgets: extension already happens by other units. Reasons 2 and 3 are real needs, but they belong to Watch screens, not to every screen.

Keeping widgets as the unit of extension also has a cost the template itself names: every mini app must design each piece to fit an arbitrary slot and be checked in four states. That is work for every app, forever.

## 4. What must stay true whatever the structure

These are his standing rules; none of them requires a tiling board.
- The Lego rule: defaults everywhere, and he can add, remove and rearrange.
- One component set, used by the screens and by the copilot.
- Preview first, detail one level down.
- The Library as the one database, reachable from anything.
- Send anything to the copilot from where it is.
- Every job shows where it runs.
- Colour means state (live, paper, needs you, problem).
- The stop for trading is always in view.
- Mini apps are guests with their own colour and their own screens.

## 5. The lead's position, to be tested

**Change the skeleton; keep the board as one kind of page.**
- The app's skeleton should be organised around his objects and his day: what needs him, his sessions with the copilot, his units, his runs, his Library. Each gets the shape its journeys need.
- A board of widgets stays where he watches: a dashboard he arranges (Home), live trading, and side-by-side comparison. There, resizing, minimising and rearranging remain.
- A mini app adds pages and tools first. It may offer a small card for a dashboard, as an option and not as a duty.

**What would make this wrong:**
- If, when clicking the options, he misses arranging things on most screens. The October Lab was his proudest screen and it was a board.
- If the non-board screens come out as generic pages. Then the board's density and character were doing more than expected.
- If the research shows a model that gives both without a split.

**What is not known yet:** how the Lego rule feels on a non-board page (adding and reordering sections), and what the copilot is allowed to build on each kind of page. Those need to be clicked, not argued.
