# Turn a video, a playlist or saved posts into strategy ideas

Built from funnel stages 1 to 7 (file 19 section 7, detailed in `research/methodology/08-strategy-funnel-lineage.md` section 3) with R5 (understand and extract) and R7 (calibrate) in `15-templates-researcher.md`. Drop URLs and notes in; it keeps an inventory row for every one, captures captions and text, triages, pulls located claims and typed cards with their holes kept, audits them in a fresh context, and writes the entry into the Library as run files.

## Steps

1. `Intake` normalises each URL, expands a playlist, a channel or a saved collection into one row per member without asking, merges duplicates with all their provenance, and gives every row a stable id. `collections` names what each collection expanded to and how.
2. `Capture captions and text` gets a video's captions with `yt-dlp`, native first, then automatic. A video with no captions is recorded as `no captions` and the run goes on. A note is kept as written.
3. `Pre-filter` passes only items that say a trading word. `Triage each item` (role `triage`) buckets each one from its transcript alone and maps a video's parts in seconds.
4. `Items to understand`, `Sections`, `Read each chunk of sections` (role `reader`) and `Quotes check` are the shared `understand-extract` block: located claims tagged source-stated, inferred or unresolved, with each quote checked against its window; promo windows are skipped.
5. `Reconcile and extract cards` (role `extractor`) writes strategy, component, knowledge and hint cards. `Keep the holes` makes an entry, exit or parameter with no cited claim read `unresolved`, turns a strategy with an inferred entry into a hint, and keeps a strategy with no exit as an `entry_hypothesis`.
6. `Rules to calibrate` and the shared `calibrate` block give each card's entry and exit rules a confidence.
7. `Independent audit` (role `reviewer`, a fresh chat) re-opens the sections and tries to disprove each card. Meaning-changing ambiguities become recorded assumptions.
8. `Library entry` gives each card and source a Library id (`STRAT-`, `CMP-`, `KB-`, `HINT-`, `SRC-`) and keeps rejected cards and skipped items with their reasons. `Render and grade` checks the entry against `schemas/output.json`, and checks every number in the cards, triage reasons, gaps and assumptions against the captured transcripts and text. The cards are what it grades, never its evidence. `Write the entry to the Library` writes one file per card and source plus the inventory under `library/`; the run-end export stores each one in the Library port, linked `produced-by` to the run. No `library` node is used.

## Test runs

`{"fixture": "one-video"}` replays one synthetic video transcript, dropped twice in two URL spellings. `{"fixture": "no-captions"}` replays a video with no captions and a note with no trading words, which makes no model call. `{"fixture": "playlist"}` drops one 20-video playlist URL: intake expands it into its 20 members from the pinned `playlists` map in `fixtures/inventory.json`, and the chunked triage edge runs over all 20. `fixtures/recorded/` holds the answers for the `--fake` switch and the unit tests (`cards.json` answers the agent step in tests only).

## Left out, and why

- Whisper for videos with no captions: it needs a key.
- Logged-in sources (Instagram saves, X bookmarks) and TradingView pages: they need the browser; such rows read "not captured" with the tool they need. Their collection URLs expand only when `yt-dlp` lists them.
- PDF to Markdown for papers: it needs the PDF tool.
- Frames and the visual pass on flagged windows: no vision step is wired; claims are transcript-only.
- Pine parsing and repaint flags: TradingView capture is not built.
- Asking him about exceptions: the audit records its readings as assumptions (rulings 57 and 77).
- An audit on another model family: the role `reviewer` is whatever Settings maps it to.
- The real Library's ids, catalog lines and index rebuild: the Library is held (ruling 91), so the entry lands as run files in the fake Library.
