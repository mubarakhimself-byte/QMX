# Why the October UI looks the way it does

Written 2026-11-10 by the redesign lead after reading the originals in full: the decoded storyboard (`refs/storyboard-text.md`) and every message he sent in the October session (`refs/his-words-october.md`, 44 messages, pulled by script). Each line is an intention of his, with the message number in `his-words-october.md` (M) or the storyboard (SB). A change to the UI should say which intention it serves better. A change that breaks one needs a reason he accepts.

## The mental models

1. **A box of Legos, "ricing Linux".** QMX must never be limited by what the UI shows. Defaults exist, and he can add, remove or edit any of them. His test question on every screen is "what if I want to add this, remove that, edit this?" (M21). This is why there is a tiling board, one panel frame, a catalog, edit layout, + Panel and templates on every building page.
2. **One component set, because the copilot builds with it.** The copilot must make panels and mini apps from the same parts the screens use. "If you are not consistent in here I don't think the co-pilot will be" (M14). New things must fit in without showing an error (M14). Inconsistent components were his first complaint, before any look.
3. **The layout is VS Code and OpenBB, on purpose** (SB): a thin rail, a tab strip on top, a grid of widgets, a copilot column. "The layout is what I'm picking." The tab strip is a reusable part whose menus change per mini app.
4. **A widget is a summary; expanding it gives the detail** (SB). He pictured expand opening a new tab "like a browser" with the detailed view. Every widget carries a message icon that sends it to the copilot, and a link that jumps to its Library item. The Library is "the database of the application", reachable from anywhere.
5. **Bloomberg is for space management, not for looks.** Minimise sends a tile to the bottom and the rest fills the space (M19). Many apps run at once: a main dashboard that is always there, then a thick line on the rail, then the apps that are open (SB). He has never used a Bloomberg terminal; it is a mental model.
6. **The copilot is a desktop-class agent app**, "not so different from the Codex desktop app or the Claude desktop app" (M35). The main copilot reaches everything. One session can start an experiment in the Lab, touch a pod, then look at Portfolio (M32), and can run for days (M29). Beside the chat sits a preview pane for anything: browser, terminal, diff, a mini app, a strategy card, sub-agents (SB). He would rather do most things through the copilot: "it should be able to control anything" (M32).
7. **Three kinds of agents** (M14): the copilot, its sub-agents, and agents that work inside workflows. He must be able to see what each is doing, and where it runs.
8. **Work runs in many places.** His laptop cannot hold everything, so jobs run on this PC, a VPS, Colab or any provider he adds (M26). The UI shows where a thing runs. Switching machine changes what the board shows, and an empty machine shows an honest empty state, "not like a 404" (M25).

## Why each place exists

- **Lab.** Authoring, backtesting and ML were merged because "they all serve the same goal: experimenting, testing and making sure things can work in paper and then live" (M19). Its tabs are layouts for a task. Resources is "the menu to the library" (M23). "Start something new" is a guided journey per experiment, and bringing outside work in should start as a main copilot session that changes the tabs for him (M25).
- **Portfolio.** "A lab, but for risk management and sizing" (M27). Things only appear here once they start paper trading (M28). He will rarely act here: "it's just for me to see" (M28). Pods replaced books because there is more than one way to do risk and sizing (M28). Every pod has a live side and a paper side (M29). The kill switch must always be in view (M29). The trading node was folded in as Live (M27).
- **Library.** The global database. Preview first, full page second. Cards carry real measures, never ratings (M13). Where-used links, journals inside the item, a reading mode for text-heavy items (M32).
- **Home.** "My dashboard": his own tabs, previews that lead to the real places, news with room, notifications with space on top, and a "while you were away" that can hold many jobs (M19).
- **Mini apps.** A composition of widgets and workflows with its own top menus (SB). Some have no screen (M12). After the Lab took over research he was "lost of words" for what they do; his answer was variants of built-in places, plus news, screeners, charting and monitoring (M29, M30).
- **Settings.** "A settings panel is a settings panel": real controls and depth, not text to read (M19). Global settings plus settings per app, after the Factory reference in the storyboard, which October never used.

## The tests he applies to every screen

- Full-screen desktop: no empty space, no cramming (M14, M19).
- Text big enough for his eyes (M11, M40).
- More to click than to read: "more words than actual intentionality" is a failure (M19).
- Fresh out of the box with no demo data (M14, M32).
- Many accounts and brokers, many jobs at once (M19).
- Everything shown has a real source in the backend (M28).
- Click through it like a user; screenshots alone do not count (M19).
- One screen at a time, finished, before the next (M19).
- Own spin: inspiration yes, another product's look no (M40).

## Drawn or asked for, never built

Expand into a detail tab. Widget history. Open apps on the rail under a divider. Top menus that change per mini app. The Factory-style settings page. A real terminal and browser in the preview pane. Sub-agents and workflow agents streaming live. Per-app settings.

## Corrections to the lead's first read (kept so they are not repeated)

- Tile border colours are not decoration. Orange means paper, blue means live, and link groups have their own colours (M14, M19, M23). Any new look keeps that meaning readable.
- "Where does the agent sit" was the wrong first question. His model already has all three at once: a main copilot place, a hand-off from every widget, and a preview pane. The open question is how boards and sessions hand work to each other.
