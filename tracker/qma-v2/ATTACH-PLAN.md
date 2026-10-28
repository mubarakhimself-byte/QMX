# QMX attach and REF2, build program

This program lets any chat (the copilot or an agent's chat) and any workflow run take references to Library items, uploaded files, files and folders on his PC, web pages and videos, whoever asks, so the UI agent only wires the paperclip, the picker, the chips, the preview panel and the full item page (`UI-HANDOFF.md` section 18).
The rules it enforces. His click and the model's own `context_add` write one list on the chat record through one writer. A chip travels with its message as a structured reference; a typed `@` is never parsed out of his text. An upload lands in the PC's own Library with no server. Each model gets an image or a PDF the way its row says it takes one, else the text QMX read from it, and a refusal names the provider, the limit and the file. QMX adds no size cap of its own.
There are 5 PRs. AT1 attaches on his click and carries chips with a message. AT2 serves the Library reads the screens use. AT3 uploads a file into the PC's Library and reads its text. AT5 sends images and PDFs to each model as it takes them. AT4 adds `@file`, `@folder`, `@url` and `@youtube` (REF2).
The stack roots on the backup program's last tip (B7 joined), which `D:/QMX-worktrees/qma-ship/wrapup/RESUME.md` records when it lands. Facts and line numbers are read at `0ee50e42`, that program's wave 2 tip. UI code, Lab, units and audio transcription are out of scope (Appendix B).

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble naming the design record, the ADs and rulings it serves, what the code does today with its file and line, and its done line with the edge cases it must survive. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands. `QA/` is `qmx-agents/packages/`. `H/` is `QA/qma-harness/src/qma/harness/`, `HO/` is `QA/qmx-host/src/qmx_host/`, `QX/` is `QA/qmx-control/src/qmx_control/`, `LB/` is `QA/qmx-library/src/qmx_library/`, `R/` is `QA/qmx-router/src/qmx_router/` and `E/` is `QA/qmx-engine/src/qmx_engine/`. Line numbers are at `0ee50e42`; the builder re-reads each one at the root before editing, because B3 to B7 move lines in files this plan does not touch only.

The store is `D:/QMX-worktrees/qma-ship/wrapup/`, whose `QUEUE.md` names this item (line 35), with `BRIEF-BUILDER.md`, `REVIEWER-BRIEF.md`, `RESUME.md`, `BACKLOG.md`, `lows.md`, `ledger.tsv`, `dispatch/`, `review/` and `evidence/`.

The program follows `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with the overrides of `LOCAL-FIRST-PLAN.md`, as `BACKUP-RESTORE-PLAN.md` did. Builders are Claude Opus 5.5 (`poteto-agent`, `model: opus`), at most two at once, never two on one file. A fresh Opus reviewer agent reviews every diff and runs the edge-case lens of `bmad-review` on AT3 and AT4, because they read his files and the web. The coordinator runs the suites, `just ci` and the lanes in the background and allows one fix round. Low findings go to `lows.md`; anything new goes to `BACKLOG.md`. He lands the stack himself.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm the shell (Windows 11, PowerShell 7.6 and Git Bash) and the root (`git rev-parse` of the backup program's last tip equals the SHA `RESUME.md` names). Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then rulings 100, 105, 106, 115, 118 and 136 to 145 in `research/methodology/26-operator-rulings-and-alignment.md`, then `UI-HANDOFF.md` sections 4, 17 and 18, then engine AD-42 and AD-63 (`architecture/workflow-engine/ARCHITECTURE-SPINE.md:340-344,466-470`), then `research/attach/` and Appendices D to F of this plan.
- [ ] No hourly `/loop 1h` tick, because builder and background-job notifications wake the coordinator. Post a short status message to the operator only when a PR opens, a verdict lands or a blocker appears.
- [ ] Never stop to ask him during the build. Stop only for a credential, a real ambiguity in this plan, or a step only he can do (`QUEUE.md`). Appendix H's one open question already carries its default.
- [ ] Before dispatch, add to `BACKLOG.md` the items this plan leaves out (Appendix B lists them).

### Spawn owners

| # | Id | PR | Wave | Branches from | Runs beside | Proving check |
|---|---|---|---|---|---|---|
| 1 | AT1 | Attach on his click, and chips with a message | 1 | the root | AT2 | a reference attached by `POST /api/sessions/{sid}/context` and one sent as a chip both sit on the chat record, and the model's next turn opens with the line naming them |
| 2 | AT2 | The Library reads the screens use | 1 | the root | AT1 | `GET /api/items?kind=source` answers cards with their object and item ids, `GET /api/items/{id}?level=page` answers the page, and `GET /api/blobs/{blob_id}` streams the bytes whose sha256 is the id |
| 3 | AT3 | Upload a file into the PC's Library | 2 | the stack tip after wave 1 | AT5 | on a home with no server a 200 MB upload cut at 100 MB resumes, lands one `source` item, a second upload of the same bytes answers `already`, and a PDF's text lands as its next version |
| 4 | AT5 | Images and PDFs reach each model as it takes them | 2 | the stack tip after wave 1 | AT3 | a haiku turn with an attached PNG answers with what the image shows, and the relay sends a PDF to a row with `pdf` false as one line naming the reference |
| 5 | AT4 | References to files, folders, web pages and videos (REF2) | 3 | the stack tip after wave 2 | none | `@file`, `@folder`, `@url` and `@youtube` attach and read in a haiku chat, a login file is refused by name, and a run started with `@url` in its inputs records the pinned object |

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Before each wave's second dispatch, record the empty Files intersection of its two PRs in `ledger.tsv` (Appendix C).
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, his real QMX folder, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, Credential Manager, a real browser or any vault value, and none starts pg0 or Hindsight against his profile. No PR edits `HO/host.py`, `HO/first_start.py`, `HO/__main__.py`, `HO/backups.py`, the `qmx_home.backup` package, `R/vault.py` or `R/key_copy.py`, which the backup program owns.

### PR mechanics, for every PR

- [ ] The coordinator creates `build/at-<id>` from the branch the table names in `D:/QMX-worktrees/bld-at-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready with `gh pr create --base <parent-branch> --head build/at-<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`.
- [ ] The builder reads the code its Files block names before editing, reproduces each gap with a failing test first, then closes it. It runs `fmt-check`, `lint` and `types` in each package it touched and `tools/secret_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push and proves the one fact its Build block names.
- [ ] Every line a person or a model reads (a refusal, a turn's header line, a doctor row) is plain words, names the file, reference or provider, and says what to do next. No QMX size cap, count cap or default-closed lock is added anywhere (rulings 106 and 137). A provider's own limit is the only limit, and its refusal is passed on with the provider's name.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, merge on his go)

- [ ] At the code-ready head the coordinator runs the touched suites with `-n 2` and lanes 1 to 4 in the background, reads every package block of each log (not its tail), and saves the logs. A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff and those logs, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go back to the same builder for one fix round. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent and patch-id.
- [ ] Parallel PRs of one wave join the stack with merge commits, never a rebase. `just ci` runs at the stack tip once at the end, under `D:/QMX-worktrees/.ci-lock`.
- [ ] He lands the stack himself from the one full list the coordinator sends when `QUEUE.md` is empty.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/at-<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`. A lane that needs the parent adds a second worktree at the parent the same way.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/qma-ship/wrapup/homes/at-<id>-<lane>/`, made with `qmx_home.resolve(..., create=True)`, with `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` on a scratch profile under the same folder, and with `QMX_HOME` unset.
- [ ] A lane that starts a host injects its bearer (never Credential Manager), turns the memory database off (`hindsight_runs` patched), and uses a port of its own, because on Windows pg0 writes his real profile (design 62 L7).
- [ ] A lane that needs a model runs `claude/haiku` through the plan login of the ship home `D:/QMX-worktrees/qma-ship/home/claude` under the lane lock, as `scripts/live/qma/e62_refs.py` does (`scripts/live/qma/common.py:21-22,82-99`); the lane's Library stays in its throwaway folder, so only chat records land in the ship home. A lane that checks what the relay sends to another provider points the row at `scripts/live/qma/fake_model.py` and reads the bodies it recorded, never a real key.
- [ ] Test files are made by the lane (`mkpdf.py` in `research/attach/probes/`, Pillow for images, a folder of generated files), never copied from his folders.
- [ ] Save captures as `evidence/at-<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude`, `yt-dlp` or `node` process from the lane is left.

## Attach on his click, and carry chips with a message (AT1)

Design record `UI-HANDOFF.md` 18.1 ("Attach from the Library", chips; "Add to copilot" on the preview panel and the full page). Engine AD-63 and H49. Rulings 115 and 118. Today the model's half is built. The five `context` reads for one chat (`chat_reads`, `HO/sessions.py:441-527`) resolve a reference through `Resolvers.add` (`QX/context.py:289-295`) and write the chat record's `attached` list through `Harness.set_attached` (`H/harness.py:510-523`), the one writer, which the host mirrors onto the session item (`HO/sessions.py:735-744`). The list is on the record beside `home` and `packs` (`H/home.py:697-700,766,819`). No HTTP route reaches those reads; the turn route takes only `{text}` (`TurnIn`, `H/routes.py:136-138`; `turn`, `H/routes.py:288-296`). A reference his click attaches would sit on the record unseen, because the model learns of one only from `context_add`'s own answer (`HO/sessions.py:462-472`). `@library:<target>` is a search that takes the first hit (`_pinned`, `QX/context.py:382-390`), so a picked item cannot be named exactly, while a workflow's `@library` is an object id (`RUN_INPUT_KINDS`, `QX/context.py:81-86`). The harness already puts claimed helper reports in front of a chat's next prompt in the same write that claims them (`_with_reports`, `H/harness.py:603,634-644`). Done when `GET`, `POST`, `POST .../refresh`, `POST .../drop` and `POST .../read` under `/api/sessions/{sid}/context` call the same five reads; `POST /api/sessions/{sid}/turns` takes `refs` beside `text` and attaches them before it sends; each entry carries `told`, false when his click or a chip attached it and true when the model's own `context_add` did; the harness's next send to that chat starts with one QMX line naming how many references he attached and which tools read them, and marks them told in the same record write; and `@library:<target>` resolves an item id or an object id exactly before it searches. Edge cases it must survive. A chat whose host holds no Library answers 409 naming that, not 500, because `context_reads` is empty there (`H/harness.py:525-530`). An unknown chat is 404. A reference that does not resolve is 400 or 404 with the resolver's own line (`_refusal`, `HO/sessions.py:435-439`). A turn with three chips whose second fails attaches none and sends nothing. The same reference attached twice keeps one entry (`HO/sessions.py:469`). A record written before `told` existed reads `told` true, so an old chat is never told twice. The QMX line holds no Library text and no `@`, because an Interactive chat is not verbatim and the CLI would read an `@path` in it (`H/chat.py:221-231`, `launch.py:105-107`). The route is a chat route, mounted by `chat_routes` (`H/routes.py:424-435`), so the host's principal door treats it as it treats the turn route (`HO/host.py:1237-1245`) and an agent's run pass cannot attach to his chat. Any chat kind takes it, a Background or Child chat of a workflow included.

**Depends on.** The root (the backup program's last tip).

**Files.**

- [ ] Edit `QX/context.py`. `AttachedRef` gains `told: bool = True`, written by `document` and read by `from_document` with true when absent (`:99-142`). `_pinned("library", target)` first takes `target` as an item id (`reads.state(target)` not None) or an object id (`reads.get` answers), and searches only when it is neither.
- [ ] Edit `HO/sessions.py`. `add` (`:462-472`) takes either `ref` or `refs` (a list of `{ref, pin}`), resolves every one before it writes, writes them in one `set_attached`, and sets `told` from a `told` argument the route passes as false; the tool path keeps true. Its answer for `refs` is `{entries: [...], excerpts: [...]}`.
- [ ] Edit `H/harness.py`. `_with_attached(chat, prompt)` runs right after `_with_reports` in `_dispatch` (`:603`). It reads the record's entries with `told` false, prefixes one line ("He attached N references to this chat since your last turn. context_list names them; context_read reads one."), and writes them back with `told` true through `set_attached` before the send.
- [ ] Edit `H/routes.py`. `TurnIn` gains `refs: list[RefIn] = []` (`RefIn` is `{ref, pin}` with `pin` `version` or `follow`). The turn route attaches `refs` through `harness.context_reads(chat)["context_add"]` with `told` false, then sends. Add the five context routes to `chat_router` (`:256`) over the same reads, with 409 `no_library` when the reads are empty.
- [ ] Add `QA/qma-harness/tests/test_context_routes.py` and `QA/qma-harness/tests/test_told.py`. Edit `QA/qmx-control/tests/test_context.py` and `QA/qmx-host/tests/test_context.py` for `told` and the exact `@library`.
- [ ] Add `scripts/live/qma/at_attach.py` (lanes 2 to 9 of this PR and of AT5 and AT4, one function per lane, `e62_refs.py` as its pattern).

**Build.**

- [ ] Reproduce first. A test posts `/api/sessions/{sid}/context` and gets 404 at the parent, and a test sends a turn with `refs` and gets 422 (`extra="forbid"`).
- [ ] Add `told` and the exact `@library`, then the batch `add`, then `_with_attached`, then the routes and `refs`, each with its test run.
- [ ] Prove the one fact. His click and the model's tool write one list. A test attaches `@library:<item>` through the route, has the model's read `context_add` attach `@run:<id>` on the same chat, then reads `context_list` and `GET .../context`, and asserts both answers hold the same two entries in the same order with `told` false and true, and that the record file on disk holds exactly those two.

**You see.**

- [ ] On a throwaway folder with one Library item, `POST /api/sessions/{sid}/context` with `{"ref": "@library:<item id>"}` answers the entry with `"told": false` and its excerpt, and the next turn's first user block in the chat's log starts with "He attached 1 reference to this chat since your last turn."

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The five routes answer as the five reads do; a host with no Library is 409 `no_library`; an unknown chat is 404; a failing reference is 400 or 404 with its line; a turn whose second chip fails attaches none and sends nothing; a repeated reference keeps one entry; an old record reads `told` true; the QMX line names the count, holds no `@` and no Library text, and is written once; `@library:<item id>` and `@library:<object id>` resolve exactly, `@library:<words>` still searches; `@unit:<item>` of another kind is still refused by kind. Run the harness, control and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The harness, control and host suites at parent and head. Save `at1-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a throwaway folder with three Library items; a haiku chat; `POST .../context` for one item; then a turn "What did I attach? Answer with its title." Save `at1-click.log`. Pass when the model calls `context_list` or `context_read` and its answer holds the item's title, and the parent answers 404 to the route.
- [ ] Lane 3. A turn with two chips (`@library:<item>` pinned and `@run:<id>/equity` following) and the text "Compare them." Save `at1-chips.log`. Pass when both entries are on the record before the CLI gets the prompt, the first user block starts with the QMX line for 2 references, and the model reads both.
- [ ] Lane 4. In one chat the model is asked to attach a run with `context_add`, then he attaches an item by the route, then both lists are read. Save `at1-one-list.log`. Pass when `GET .../context` and the model's `context_list` name the same two entries, the session item has one `mentions` edge per entry, and the QMX line on the next turn counts only his one.
- [ ] Lane 5. A turn whose chips are a good item and `@library:no-such-thing`. Save `at1-bad-chip.log`. Pass when the route answers 404 naming the second, the record holds no new entry, and the chat log has no new user block.
- [ ] Lane 6. A record file written by the parent with two attached entries, opened by the head host, then a turn. Save `at1-old-record.log`. Pass when both entries read `told` true and the turn carries no QMX line.
- [ ] Lane 7. `@library:<item id>` for an item whose title matches another item's search better. Save `at1-exact.log`. Pass when the entry names the exact item, and `@library:<title words>` names the search's first hit.
- [ ] Lane 8. A host started with no Library store (the harness opened on its own, as a test host does) answers the route. Save `at1-no-library.log`. Pass when it answers 409 `no_library` with one line.
- [ ] Lane 9. A Background chat a workflow's agent node opened gets a reference by the route, then the node's next send. Save `at1-background.log`. Pass when its next prompt starts with the QMX line and the reference resolves in its `context_list`.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `at1-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `POST .../context` of one `@library:<item id>` on a 1,000-item throwaway store, and for the model's read `context_add` of the same reference called in process; and milliseconds the turn route takes to answer with three chips and with none.
- [ ] Probe. Each fifty times, interleaved, on one warm host at head.
- [ ] Baseline. Record the in-process read's median first.
- [ ] Rule. The route's median is within 30 ms of the in-process read's median, the same work behind HTTP, or the PR fails. Three chips add under 150 ms to the turn route's median answer, an absolute budget, because the parent has no chips.

**Review gate.** None. AT1 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the root.

## Serve the Library reads the screens use (AT2)

Design record `UI-HANDOFF.md` 18.3 (the preview panel's used in, journal and logs, code and settings; the full page's tabs; Full page, Add to copilot, New version, Open in Lab), 4 (shelves generated from the kinds' schemas, previews and tabs driven by schema data) and 17.1 (a card and a full page for every item). Library AD-17 and AD-33. Ruling 127. Today the one read that serves every kind's card and page exists, `view(store, who, object_id, level)` with its computed header (`LB/view.py:533-559`), and `family` (`LB/view.py:579`), and no route serves either; probe F7 read a source's card in 6.5 ms and its page's six tabs. The header carries no object id and no item id (`Header.as_json`, `LB/view.py:107-146`), so a card in a list cannot be picked. The REST door's `GET /api/library` takes `query`, `offset` and `limit` and no kind (`library_search`, `QX/service.py:1081-1084`), while the store's search takes `kind` (`LB/store.py:1707-1716`, probe F8). Its documents read the `content` slot as JSON (`_document`, `QX/library.py:439-466`, with `SLOTS` at `:38`), so a `source` with the schema's `original` and `text` slots raises `KeyError: 'content'` (probe F6), and the same read serves the agents' `library_get`. A page tab names a blob by id, size and media type (`_slot`, `LB/view.py:490-513`), and no route on the PC streams a blob's bytes; the store has `blob_stream` (`LB/store.py:2367`). The shelves need the kinds and their classes, which the schemas hold (`LB/kinds/*.schema.json`), and no route lists them. "New version" already has `POST /api/library/{artifact_id}/branch` and the version and history reads exist (route list in Appendix A). Done when `GET /api/items` (`q`, `kind`, `offset`, `limit`, `level` card) answers each hit's card with `object_id` and `item`; `GET /api/items/{object_id}` answers the card or, with `level=page`, the page, with the same two ids; `GET /api/items/{object_id}/family` answers `family`; `GET /api/kinds` answers each kind's name, class, card and page declaration; `GET /api/blobs/{blob_id}` streams the bytes with the blob's media type and length; and the REST door's documents read any kind, giving `content` only for a JSON slot and the blob refs otherwise. Edge cases it must survive. The routes are mounted after the generated REST routes, so none sits under `/api/library/{artifact_id}`, which would swallow it (probe F10 shows the new paths are free). An archived item lists only when `archived=true` is asked, as the store's `include_archived` (`LB/store.py:1713`). A blob held only on the server (a replica's cache miss) answers 404 `not_cached` with one line, never a partial stream. A blob id that is not `sha256:<64 hex>` is 400. A 1 GB blob streams in chunks and never sits in memory (`CHUNK`, `LB/store.py:91`). Every route sits behind the bearer (`create_app`, `QX/server.py:462-465`). Run picks use the same routes (`kind=workflow-run`, then the page's Outputs tab, `walk:produced-by:in` in `workflow-run.schema.json`), so the run-start picker needs no route of its own.

**Depends on.** The root (the backup program's last tip). It shares no file with AT1.

**Files.**

- [ ] Create `QX/library_routes.py` with `library_router(service)`, the five routes over `service.library.store` (`QX/library.py:138`), `qmx_library.view.view`, `family` and `Store.blob_stream`, each with the operator principal (`OPERATOR`, `QX/library.py:34`).
- [ ] Edit `QX/server.py`. `create_app` includes `library_router(service)` behind the bearer beside the upload router (`:465`).
- [ ] Edit `QX/library.py`. `_document` reads `content` only when the slot's media type is JSON and otherwise answers `content: null` with `blobs` (slot, blob id, size, media type), so `library_get` and `library_search` read every kind.
- [ ] Add `QA/qmx-control/tests/test_library_routes.py`. Edit `QA/qmx-control/tests/test_library_store.py` for a `source` item.

**Build.**

- [ ] Reproduce first. A test puts a `source` with `original` and `text` blobs and asserts `library_get` answers it, failing at the parent with `KeyError`; a test gets `/api/items` and fails with 404.
- [ ] Fix `_document`, then the items, one item, family and kinds routes, then the blob stream, each with its test.
- [ ] Prove the one fact. The screens' reads are the schema's, not hand-built. A test walks every kind in `LB/kinds/`, puts one item of it, and asserts `GET /api/items/{id}?level=page` answers exactly the tabs its schema declares, in order, and `GET /api/kinds` lists every schema file once.

**You see.**

- [ ] On a throwaway folder with a `source` (a PDF and its text) and a `unit`, `GET /api/items?kind=source` answers one card whose `object_id` opens `GET /api/items/<id>?level=page` with the tabs Read, Original, Transcript, Derived, Used in and History, and `GET /api/blobs/<original blob id>` answers the PDF's bytes with `application/pdf`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Every kind's page answers its declared tabs; the card carries both ids; `kind` filters and an unknown kind answers an empty list; `archived=true` adds archived items; `offset` pages; the blob stream's sha256 equals its id, its length and media type are set, a bad id is 400 and a missing one 404; `library_get` reads a `source`, an `artifact` and a `backtest-result`; no new path is shadowed by `/api/library/{artifact_id}`; the routes answer 401 with no bearer. Run the control and library suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The control and library suites at parent and head. Save `at2-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a throwaway folder seeded with one item of every kind; `GET /api/kinds`, then `GET /api/items?kind=<k>` and `GET /api/items/<id>?level=page` for each. Save `at2-every-kind.log`. Pass when every kind lists one card with both ids and every page answers its schema's tabs, and the parent answers 404 to each route.
- [ ] Lane 3. A 1 GB generated blob in a `source`, streamed by `GET /api/blobs/<id>` to a file in the lane folder while the host's memory is sampled. Save `at2-big-blob.log`. Pass when the file's sha256 equals the id and the host's resident memory rises by under 64 MB during the stream.
- [ ] Lane 4. A haiku chat whose model calls `library_get` on the `source`, which failed at the parent. Save `at2-agent-get.log`. Pass when the tool answers the source with its blob refs and the model names its title, and the parent's tool answers an error.
- [ ] Lane 5. A run of a two-node workflow that lands an output, then `GET /api/items?kind=workflow-run` and the run's page. Save `at2-run-pick.log`. Pass when the Outputs tab names the landed artifact, and a run started with `@library:<that artifact's object id>` records it on `run_created`.
- [ ] Lane 6. An item archived with a reason, then listed with and without `archived=true` and opened. Save `at2-archived.log`. Pass when it lists only when asked and its card header says archived with the reason.
- [ ] Lane 7. A host whose store is a replica with a blob only on its fake server, then `GET /api/blobs/<id>` with the server stopped. Save `at2-not-cached.log`. Pass when it answers 404 `not_cached` with one line and no bytes.
- [ ] Lane 8. `GET /api/items/<id>/family` on an item with a parent, two children and a sibling. Save `at2-family.log`. Pass when each edge is named with its `what_changed`.
- [ ] Lane 9. Every route with no bearer, a wrong bearer and a run pass. Save `at2-bearer.log`. Pass when each answers 401 except where the principal door admits that pass for a read, as for the other Library reads.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `at2-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `GET /api/items?limit=50` and for one `GET /api/items/<id>?level=page` on a 10,000-item throwaway store; seconds to stream lane 3's blob by the route and by `Store.blob_stream` in process into the same drive.
- [ ] Probe. Fifty list and page reads, then three streams each way, interleaved, on one warm host at head.
- [ ] Baseline. Record the in-process stream's median first.
- [ ] Rule. The list's median is under 300 ms and the page's under 50 ms, absolute budgets, because the parent has no such routes. The route's stream median is within 1.3 times the in-process stream of the same blob to the same drive, the same bytes written the same way, or the PR fails.

**Review gate.** None. AT2 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined beside AT1 by a merge commit (the two share no file).

## Upload a file into the PC's Library and read its text (AT3)

Design record `UI-HANDOFF.md` 18.4 (the paperclip's upload, the picker's Files shelf) and 17.3 (a progress line that resumes after a cut, the item at once, then "reading", the same file twice says "already in your Library"). Library AD-10 and AD-27. Rulings 136, 140, 142 and 143. Data-round inventory row 5 found no upload door (`research/methodology/52-data-round-inventory.md:41`). Today the PC's door `POST /api/library/upload` streams every byte on to a server and refuses on a PC with none (`upload_router`, `QX/server.py:229-331`, `HubClient.connect` at `QA/qmx-library/src/qmx_library/client.py:175-181`); probe F5 got 409 "no [library] hub_url" on a home with no server, which ruling 142 forbids. The host's store is the writer while `[library] primary` is `pc`, the default (`store_role`, `HO/host.py:605-608`), and the store already has the resumable upload (`Upload`, `LB/store.py:501-560`; `begin_upload`, `complete_upload` and `discard_upload` at `:2300-2365`), which `Part` in the control door duplicates line for line (`QX/server.py:103-226`) and stages in `<data>/uploads/` beside the store, where backups do not leave it out (only `library/uploads/*.part`, `QA/qmx-home/src/qmx_home/backup/snapshot.py:45`). Neither path makes an item; the answer is a blob id (`_landed`, `QA/qmx-hub/src/qmx_hub/server.py:607-617`). The `source` kind already holds `original`, `text`, `pages/*`, `transcript` and `frames/*`, with `origin` `upload` and `media_type`, `bytes`, `pages`, `text_hash` and `extractor_version` (`LB/kinds/source.schema.json`). Text extraction exists only as the `extract-source` template running Docling, which the lock does not hold (`E/templates/extract-source/extract/scripts/extract.py:1-28`); `markitdown` 0.1.8 with its PDF, Word, PowerPoint and Excel readers is already locked through `hindsight-api-slim` (`qmx-agents/uv.lock:1475,2103`) and read a PDF's text in 262 ms (probe F9). Done when, on the writer, the door stages through `Store.begin_upload`, completes through `complete_upload`, and lands one `source` (title the file's name, `origin` `upload`, `media_type`, `bytes`, `original` the blob) in the same request, answering `{object_id, item, blob_id, bytes, already, reading}`; the same bytes again answer the existing item with `already: true`; a background job reads the text with `markitdown` into `text` and `pages/*` as the item's next version with `pages`, `text_hash` and `extractor_version`, and records `reading` as `done` or `failed` with its line on the item's annotations; on a replica the door keeps today's stream to the server, staged through the same `Upload`; and `Part` is deleted. Edge cases it must survive. A request cut mid way leaves the part, `GET /api/library/upload/{id}` answers its offset and hash, and a resume with a wrong partial hash is 409 `hash_mismatch` (`LB/store.py:524-531`). A resume after the part completed answers the landed item, not a second one. QMX sets no size limit (`QX/server.py:235-236` says so today and stays true). A file name with path parts keeps only its last part as the title, and a name that is empty takes "Upload <date>". An image lands with no text and `reading` `done`. A scanned PDF with no text lands with `reading` `failed` and "no text found; this PDF looks scanned" rather than an empty Read tab. A file `markitdown` cannot read (a zip, a binary) lands as an item with `reading` `failed` naming the type. Extraction never holds the request, and two uploads extract one after the other on one thread. A host killed mid extraction leaves the item without text, and the next start's sweep extracts every `source` whose `reading` is `pending`. The door is behind the bearer as today (`QX/server.py:465`).

**Depends on.** AT2 (`QX/server.py` mounts both routers; AT2 first).

**Files.**

- [ ] Create `QX/sources.py` with `land(store, who, *, name, media_type, blob_id, size) -> Landed` (dedupe by the `original` blob's sha256, as `by_ref` finds a blob, `QX/library.py:201-219`), `read_text(store, who, object_id) -> Reading` (markitdown in this process, pages split on its page breaks), `pending(store) -> list[str]`, and `Extractor`, one worker thread with a queue that `create_app`'s lifespan starts and stops.
- [ ] Edit `QX/server.py`. `upload_router(service)` replaces `upload_router(home)`. On a writer it stages through `Store.begin_upload`, completes and lands; on a replica it streams on as today, staged through the same `Upload`. `GET` and `DELETE /api/library/upload/{id}` read the store's `uploads/`. Delete `Part`, `STAGING` and `COPIES_REQUIRED`' local copy logic that moves into the replica branch.
- [ ] Edit `QA/qmx-control/pyproject.toml` to declare `markitdown[docx,pdf,pptx,xlsx]==0.1.8` and `pdfminer-six==20260107`, the locked versions, and run `uv lock` so `qmx-agents/uv.lock` gains only the edge.
- [ ] Edit `QA/qmx-control/tests/test_upload_door.py` for the writer path and the deleted `Part`. Add `QA/qmx-control/tests/test_sources.py`.

**Build.**

- [ ] Reproduce first. A test uploads to a home with no server and asserts a landed item, failing at the parent with 409 `storage_failure`.
- [ ] Add `land` with dedupe, then the writer branch of the door, then `Extractor` and the start sweep, then the replica branch on `Upload`, then delete `Part`, each with its test run.
- [ ] Prove the one fact. An upload is idempotent across cuts. A test sends a 50 MB file in three requests, kills the second mid way, resumes from the offset `GET` answers, then sends the whole file again as a new upload id, and asserts one blob, one `source` item, one version with text, and `already: true` on the last answer.

**You see.**

- [ ] On a throwaway folder with no server, `curl` posting `research/attach/probes/sample.pdf` with `X-Upload-Name: london.pdf` answers `"already": false, "reading": true` and an `object_id`; within five seconds `GET /api/items/<item>?level=page` answers the Read tab with "Sharpe ratio of the London breakout".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A writer lands an item from one request and from a resumed one; a wrong partial hash is 409; the same bytes answer `already`; a resume of a finished upload answers the item; a PDF, a Word file and a text file get text and pages; an image gets none and reads `done`; a scanned PDF and a zip read `failed` with their lines; extraction runs off the request thread; the start sweep extracts a `pending` item; a replica streams to a fake server as at the parent and stages under the store's `uploads/`; `Part` is gone and nothing imports it. Run the control, library and host suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The control, library and host suites at parent and head. Save `at3-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A head host on a throwaway folder with no server; a 200 MB generated file uploaded in 8 MB requests, the connection cut at 100 MB, then resumed. Save `at3-resume.log`. Pass when one `source` lands with the file's sha256, its bytes are the file's, and the parent answers 409 `storage_failure`.
- [ ] Lane 3. The same file uploaded again under a new id, then `sample.pdf` uploaded twice. Save `at3-already.log`. Pass when each second answer is `already: true` with the first item's id and the store holds one blob each.
- [ ] Lane 4. A 30-page generated PDF uploaded while `/api/health` is polled every 200 ms, then the item's page read until its Read tab is available. Save `at3-reading.log`. Pass when the upload answers before the text lands, every health call answers in under 1 s, the text lands as version 2 with `pages` 30 and 30 `pages/*` slots, and `reading` is `done`.
- [ ] Lane 5. A PNG, a scanned-style PDF (an image saved as PDF by Pillow) and a zip uploaded. Save `at3-unreadable.log`. Pass when the PNG reads `done` with no text, the PDF reads `failed` with the scanned line, and the zip reads `failed` naming its type, each still an item.
- [ ] Lane 6. The host killed while a large PDF extracts, then started again. Save `at3-killed.log`. Pass when the item has no text after the kill, and within a minute of the start it has its text and `reading` `done`.
- [ ] Lane 7. A haiku chat that attaches the uploaded PDF by AT1's route and asks what it says. Save `at3-chat.log`. Pass when the model's `context_read` returns the extracted text and its answer quotes the phrase.
- [ ] Lane 8. A host whose store is a replica of a fake server, then an upload. Save `at3-replica.log`. Pass when the bytes reach the fake server as at the parent, the staging part sits under `library/uploads/`, and nothing is written under `<data>/uploads/`.
- [ ] Lane 9. A backup round (the backup program's `run_round`) taken while an upload is half sent. Save `at3-backup.log`. Pass when the copy's manifest names no `.part` file and the landed items of earlier uploads are in it.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `at3-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for lane 2's 200 MB upload whole and for its resume after 100 MB at head, and seconds for `Store.append_upload` plus `complete_upload` of the same file in process (the same hashing and the same fsync, without HTTP); seconds for lane 4's text to land.
- [ ] Probe. Each three times, interleaved, on fresh throwaway folders on the same drive.
- [ ] Baseline. Record the in-process store upload's median first.
- [ ] Rule. The route's whole upload is within 1.3 times the in-process store upload of the same file, the same work behind HTTP, or the PR fails. The resume is under 0.7 times the whole upload. Lane 4's 30-page text lands within 30 s of the upload's answer, an absolute budget, because the parent reads no text.

**Review gate.** None. AT3 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 1 tip; AT5 joins it by a merge commit.

## Send images and PDFs to each model as it takes them (AT5)

Design record `UI-HANDOFF.md` 18.1 and 18.4 (a picked or uploaded file joins the message). Engine AD-42 (images and PDFs as native blocks when the row says `vision` or `pdf`, else derived text; one bad attachment never poisons a chat) and AD-39 (the row's capabilities are the only place consumers read). Rulings 100, 106 and 107. Today a turn reaches the CLI as one string (`Chat.send`, `H/chat.py:802-815`, `client.query(prompt.text)`), while the locked Agent SDK's `query` takes an async iterable of user messages whose content may hold image blocks (`research/attach/claude-agent-sdk-input.md`). The relay already maps a user message's image and base64 PDF document to the GPT lane's `input_image` and `input_file` (`R/gpt/translate.py:167-169,212-222`, probe F2) and its image to the chat lane's `image_url`, but the chat lane refuses a PDF document whole (`R/chat_lane.py:251-254,288-294`, probe F3). The normaliser runs before both lanes and the key lane (`R/relay.py:1032-1034,1327-1328`) and replaces an image for a row without `vision` with `[image omitted: this model cannot see images]` (`R/normalise.py:34,177-178`), but forwards a PDF to a row without `pdf` unchanged (probe F4), so OpenRouter or an OpenCode Go row gets a block it may refuse or bill through a paid OCR engine (`research/attach/openrouter-inputs.md`). Rows carry `vision`, `pdf`, `audio` and `video` (`R/registry.py:77-81`); the plan rows set `vision` and `pdf` (`R/profiles/claude.toml:10-11`), the GPT row only `vision` (`R/profiles/gpt.toml:8`) although its lane maps PDFs today. Done when a send whose chat has unannounced entries (AT1's `told` false) builds one user message with a native block per entry the chat's main row takes, ahead of the text (images first, as Anthropic advises), and the text with the AT1 line; an image goes as `image` when the row has `vision`; a PDF goes as a base64 `document` when the row has `pdf`, else as a text `document` holding its `text` slot, else, while its text is still being read, the line says so; the block's `title` names the file and its `@library` reference; the normaliser replaces a base64 PDF for a row without `pdf` with one text block `[PDF <title> not sent: <qmx_id> takes no PDFs. context_read reads its text.]`; `gpt.toml` sets `pdf = true`, which keeps today's mapping; and a turn the provider refuses ends with one line naming the provider, its message and the attached files. Edge cases it must survive. A send with no unannounced media stays a plain string, so nothing changes for text turns. QMX sends the bytes the item holds and resizes nothing; the provider's own limit refuses (10 MB per image and 32 MB per request on the Claude API, 50 MB of files on Responses, `research/attach/`), and its message reaches him with the file named. A refused turn leaves the entries told, so the next turn does not resend the same bytes, and the line says to attach a smaller copy or pick a model that takes it. A sub-agent on another row gets the same history through the normaliser, so a plan main with a PNG and a DeepSeek helper gives the helper the placeholder, never a refusal of the whole request. The CLI's replay of a block prompt still joins the waiting handle (`_join` matches by prompt text, `H/chat.py:957-966`). The chat log's user block records the text and the attached names, never the bytes. Formats the Claude API does not take as images (a TIFF, a BMP) go as no block, and the line names them so the model reads them with its tools.

**Depends on.** AT1 (`told`, `_with_attached`). It shares no file with AT3.

**Files.**

- [ ] Edit `H/chat.py`. `OperatorText` and `InjectedText` gain `blocks: tuple[Mapping[str, object], ...] = ()` (`:206-221`). `send` (`:802-815`) passes a one-message async iterable to `client.query` when `blocks` is not empty and the string otherwise, and `_note("user", ...)` records `attached` names. `_join` matches a replayed block prompt by its text part.
- [ ] Edit `H/harness.py`. `_with_attached` asks `self.attachment_blocks(chat, entries, row)` (the base returns none) and puts the blocks on the prompt; the row is the chat's main model row from the registry (`Registry.model`, `R/registry.py:164`). A failed turn whose prompt carried blocks gets the provider line.
- [ ] Edit `HO/sessions.py`. `RecordedHarness.attachment_blocks` reads each entry's object from the store and builds the block by its `media_type` and the row (Appendix D table).
- [ ] Edit `R/normalise.py`. In `_blocks` (`:160-185`) a base64 `document` whose media type is PDF, for a row without `pdf`, becomes the one text block, inside a `tool_result` too.
- [ ] Edit `R/profiles/gpt.toml`. `pdf = true` in `[defaults]`.
- [ ] Add `QA/qma-harness/tests/test_attached_blocks.py` and `QA/qmx-host/tests/test_attachment_blocks.py`. Edit `QA/qmx-router/tests/test_normalise.py`.

**Build.**

- [ ] Probe P-DOC first and record it in `evidence/at-at5/p-doc.log`. One haiku chat on the ship home gets one user message with a base64 PDF `document` block through `client.query`. When the CLI passes it and the model reads it, PDFs go natively to plan rows. When the CLI drops or refuses it, plan rows get the text `document`, and the probe's line goes in Appendix A.
- [ ] Add `blocks` and the send, then `attachment_blocks`, then the normaliser rule and `gpt.toml`, then the refusal line, each with its test run.
- [ ] Prove the one fact. Every lane gets each file as its row takes it. A test sends one request holding a PNG and a base64 PDF through `normalise` and then `to_responses`, `to_chat` or the key lane's bytes for a `vision` and `pdf` row, a `vision`-only row and a text-only row on each of the three wires, and asserts the image, PDF, placeholder and line in each of the nine bodies, with no `RefusedRequest`.

**You see.**

- [ ] A haiku chat on a throwaway folder with an uploaded PNG of a red square attached by AT1's route answers "What colour is the shape I attached?" with red, and its log's user block records `attached: ["square.png"]` with no base64 in it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] A text-only send stays a string; a PNG becomes an `image` block for a `vision` row and the line for another; a PDF becomes a base64 `document`, a text `document` or the reading line by row and state; images come before text; the nine bodies of the Build fact hold what they should and none raises; the normaliser line names the title and the row; a TIFF gets no block and is named; a refused turn's line names the provider and the files and the entries stay told; `_join` joins a replayed block prompt; the user block holds no bytes. Run the harness, host and router suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The harness, host and router suites at parent and head. Save `at5-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The You see scenario at head and parent. Save `at5-image.log`. Pass when head's answer says red and the parent's model cannot say (it saw only the AT1 line).
- [ ] Lane 3. `sample.pdf` attached to a haiku chat, then "Quote the PDF's only sentence." Save `at5-pdf.log`. Pass when the answer quotes it and the request the CLI sent (read from the CLI's transcript) holds the block P-DOC chose.
- [ ] Lane 4. The relay with rows pointed at `fake_model.py`. A request holding a PNG and a PDF sent through the key lane for an `openrouter.toml` row, the chat lane for an `opencode-go.toml` row and the GPT lane. Save `at5-lanes.log`. Pass when the fake recorded, per lane, the placeholder and the PDF line, the placeholder and the PDF line, and `input_image` and `input_file`, and no lane answered 400.
- [ ] Lane 5. An 11 MB PNG attached to a haiku chat. Save `at5-too-big.log`. Pass when the turn ends with one line naming Anthropic (or the CLI, whichever refused), its message and `big.png`, and the next turn of the chat runs.
- [ ] Lane 6. A plan main with a PNG attached whose model delegates "describe the image" to a sub-agent on a row without `vision` pointed at `fake_model.py`. Save `at5-subagent.log`. Pass when the sub-agent's request holds the placeholder and the main's turn ends ok.
- [ ] Lane 7. A 40-page PDF uploaded and attached at once, before its text lands, to a chat whose main row has no `pdf` (a fake row). Save `at5-reading.log`. Pass when the first turn's line says its text is being read, and a second attach after the text lands sends a text `document`.
- [ ] Lane 8. A TIFF attached. Save `at5-tiff.log`. Pass when no block is sent, the line names the TIFF, and the model is told how to read it.
- [ ] Lane 9. A text-only turn at head and parent, and the CLI's request bodies compared. Save `at5-text-only.log`. Pass when both bodies' user content is the same string.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `at5-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds from the turn route's call to the CLI's `query` write for a text-only turn at parent and head, and for a turn with one 5 MB PNG at head; milliseconds `normalise` takes on a 20 MB request holding one PDF at parent and head.
- [ ] Probe. Each fifty times, interleaved, on one warm host per side, the CLI's write timed by a patched transport.
- [ ] Baseline. Record the parent's text-only median first.
- [ ] Rule. Head's text-only median is within 5 % of the parent's, or the PR fails. `normalise` on the same 20 MB body is within 10 % of the parent's, the same parse and dump, or the PR fails. The 5 MB PNG adds under 300 ms to head's text-only median, an absolute budget, because the parent sends no image.

**Review gate.** None. AT5 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Joined onto AT3 by a merge commit (the two share no file).

## Attach files, folders, web pages and videos (AT4)

Design record `UI-HANDOFF.md` 18.4 (the backend refuses `@file`, `@folder`, `@url` and `@youtube` until REF2). Engine AD-63 (a file pinned by its bytes, a folder by a manifest, a URL and a video stored first by hash; bytes reach the Library only for what is read; a heavy reference reads `pending` and the turn never waits) and AD-43 (one SSRF guard on every URL tool, which no code holds yet). `HARDENING-PLAN.md` Appendix G row 2 waited on the multimodal layer, which AT3 and AT5 bring. Rulings 100, 106 and 136. Today the four kinds are refused by name (`LATER`, `QX/context.py:57-64`; `parse` at `:180-181`; probe F1), and the `context_add` row's words say they "arrive with REF2" (`QX/catalog.py:439-442`). A workflow's inputs walk every `@` string through `parse` (`references`, `QX/context.py:548-567`), so today a run with `@file:` in its inputs is refused, and once `LATER` goes, `references` would skip it silently as a plain string (`:557`). The model's own tools read files under the guard, which refuses login and key files and his own Claude home (`_read_target`, `H/guard.py:446-453`; `secret_files`, `H/tools.py:909-923`), but a `context_add` of a path is an MCP call the guard sees as `{ref}`, so the resolver must ask the guard itself. The folder budget is 200 entries, Claude's default and a Settings value (`Budget.folder_entries`, `QX/context.py:260`). Video captions through `yt-dlp`, native first then automatic, already exist in a template (`captions`, `E/templates/a-fill-the-library/scripts/capture.py:34-50`), and `yt-dlp` is not in the lock. Done when `@file:<path>[:a-b]` imports the file through AT3's `land` (origin `import`, deduped by hash) and pins its version, with a range reading only those characters; `@folder:<path>` lands one `source` whose `text` is the listing (path, size, modified time) up to the folder budget with the count left out, pinned by the listing's digest, and the model reads files through its own guarded tools; `@url:<https...>` fetches once through the guard, lands a `source` (origin `agent`, `url`, `canonical_url`, `fetched_at`, `original` and `text` through `markitdown`), and pins it; `@youtube:<id or URL>` answers `pending` at once, lands a `source` with the video's title and its captions as `transcript`, and reads `ready` when they land, or `ready` with "no captions" when the video has none; `context_read` serves each; a workflow's inputs take `@url` and `@youtube` by importing them at `workflows_run` and passing `@library:<object id>` to the engine, and refuse `@file` and `@folder` by name; and every reference that reaches a file passes the chat's guard first, so a login file, a key file and his `~/.claude` are refused with the guard's own line whoever asks. Edge cases it must survive. A path that does not exist is 404 with the path; a folder named as a file and a file named as a folder each say so. A link or junction in a folder is listed as a link and never followed. A 2 GB file imports in chunks through the store's upload path, never whole in memory. The URL guard refuses loopback, private, link-local, CGNAT and cloud metadata addresses after resolving the name, refuses a non-https scheme unless the URL is `http` to a public address, and checks every redirect again. A URL that answers 4xx or 5xx is refused with the status and the address. The same URL fetched again in one day returns the existing item, as the old `fetched_date` dedupe does (`_fetched`, `QX/library.py:395-405`), and `context_refresh` fetches again. No `yt-dlp` on the host answers `not_cached` with "yt-dlp is not installed", never a crash; the PR adds it to the lock so a fresh install has it. A video's captions run on one background thread and never hold the add. A trigger's inputs with an `@url` are refused by name at fire time with the fix, because only a start he asks for imports (Appendix B).

**Depends on.** AT3 (`QX/sources.py`) and AT5 (`H/harness.py`, `HO/sessions.py`). It is wave 3 alone.

**Files.**

- [ ] Edit `QX/context.py`. Delete `LATER`; add the four resolvers over three new `LibraryReads` methods, `imported(kind, target) -> LibraryObject` (file and URL), `listed(path) -> LibraryObject` and `video(target) -> LibraryObject | None` (None while pending); `references` returns every reference and `_pin` refuses `@file` and `@folder` by name with the fix.
- [ ] Create `QX/imports.py`. `fetch(url) -> Fetched` with the guard (`ipaddress` checks after `socket.getaddrinfo`, redirects followed one by one with `httpx`, which `qmx-control` already declares); `listing(path, entries) -> str`; `captions(url) -> Captions | None`, the template's `yt-dlp` rule as a function, run on one worker thread.
- [ ] Edit `QX/sources.py` for `land_bytes` (a file path or fetched bytes through `Store.begin_upload`) and the URL fields.
- [ ] Edit `QX/service.py`. `workflows_run` (`:1744-1749`) imports each `@url` and `@youtube` in `inputs` and replaces it with `@library:<object id>` before the engine starts the run.
- [ ] Edit `QX/catalog.py`. The `context_add` description (`:439-442`) names all eleven kinds.
- [ ] Edit `HO/sessions.py`. `StoreReads` (`:347`) implements the three reads over `QX/imports.py` and `QX/sources.py`, and `chat_reads` passes the chat's guard check.
- [ ] Edit `H/harness.py`. `read_refusal(chat, path, *, folder) -> str | None` runs `guard("Read" or "Glob", ...)` with the chat's own rules (`H/guard.py:830-860`) and answers the deny's reason.
- [ ] Edit `QA/qmx-control/pyproject.toml` to declare `yt-dlp` at the newest release at least two weeks old, and run `uv lock`.
- [ ] Add `QA/qmx-control/tests/test_imports.py` and `QA/qmx-control/tests/test_ref2.py`. Edit `QA/qmx-control/tests/test_context.py` and `QA/qmx-host/tests/test_context.py`.

**Build.**

- [ ] Reproduce first. A test attaches each of the four kinds and gets `not_yet` at the parent, and a test starts a run with `@url:` in its inputs and asserts the refusal names REF2.
- [ ] Add the guard check and `@file`, then `@folder`, then the URL guard and `@url`, then `@youtube`, then the run-start import and the `_pin` refusal, then the lock, each with its test run.
- [ ] Prove the one fact. No reference reads what the guard refuses. A test builds a chat's guard rules on a throwaway home with fake login and key files, attaches `@file` and `@folder` for each secret path, a folder holding one, and his `~/.claude` stand-in, through the route and the model's read, and asserts every one is refused with the guard's line and no `source` item was put.

**You see.**

- [ ] In a haiku chat on a throwaway folder, `POST .../context` with `@folder:<lane folder>/docs` answers the listing's first lines, and `@url:https://example.com` answers an entry whose excerpt holds "Example Domain".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `@file` imports once and pins, a range reads its slice, a 2 GB fake file streams; `@folder` lists to the budget, names the count left out, lists links unfollowed and pins by digest; the URL guard refuses each private class and a redirect into one, and fetches a public page through a patched resolver; a 404 page is refused with its status; the same URL the same day reuses the item and refresh fetches again; `@youtube` answers pending, then ready with a transcript from a patched `yt-dlp`, ready with "no captions", and `not_cached` with no `yt-dlp`; every secret path is refused through both doors; a run's `@url` input is pinned on `run_created` as `@library`, `@file` in inputs is refused with its fix, and a trigger's `@url` is refused at fire time. Run the control, host and engine suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. The control, host and engine suites at parent and head. Save `at4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. A haiku chat asked "Attach the file <lane folder>/notes.md and tell me its first heading", then "Attach the folder <lane folder>/docs and name its largest file." Save `at4-file-folder.log`. Pass when the model calls `context_add` for each, its answers are right, and the parent's `context_add` answers `not_yet`.
- [ ] Lane 3. A haiku chat asked to attach `@file` on the lane's fake `.credentials.json`, the fake `keys/` folder and the scratch profile's `.claude` folder, then the same three by his route. Save `at4-guard.log`. Pass when all six are refused with the guard's line and no `source` item exists.
- [ ] Lane 4. `@url:https://example.com` attached by the route, then the same again, then `context_refresh`, then `@url:http://127.0.0.1:<lane port>/` and `@url:http://169.254.169.254/`. Save `at4-url.log`. Pass when the first lands one item whose text holds "Example Domain", the second reuses it, the refresh fetches again, and the last two are refused naming the address class.
- [ ] Lane 5. `@youtube:<a public video with captions, named in the log>` attached, read at once and again after it lands, then a video with no captions. Save `at4-youtube.log`. Pass when the first reads `pending` within 500 ms, then `ready` with a transcript, and the second `ready` with "no captions".
- [ ] Lane 6. The same lane on a host whose `PATH` holds no `yt-dlp` and whose venv's `yt-dlp` is hidden. Save `at4-no-ytdlp.log`. Pass when the entry reads `not_cached` with "yt-dlp is not installed" and the chat goes on.
- [ ] Lane 7. A workflow started through `POST /api/workflows/<id>/run` with `{"source": "@url:https://example.com"}`, then one with `@file:<path>`. Save `at4-run-input.log`. Pass when the first run's `run_created` pins a `@library` object whose text holds "Example Domain", and the second is refused with the line naming the fix.
- [ ] Lane 8. A folder of 10,000 generated files and one junction attached as `@folder`. Save `at4-big-folder.log`. Pass when the listing holds 200 entries and "9,800 more", the junction is listed as a link and its target is not listed.
- [ ] Lane 9. A 2 GB generated file attached as `@file` while the host's memory is sampled, then `@file:<path>:0-200`. Save `at4-big-file.log`. Pass when one item lands with the file's sha256, resident memory rises by under 64 MB, and the range reads 200 characters.
- [ ] Lane 10. Gates in the touched packages, `tools/secret_scan.py`, then remove the throwaway folders and list processes. Save `at4-processes.log`. Pass when every exit code is 0 and nothing from the lanes is left, no `yt-dlp` process included.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `context_add` of `@file` on a 10 MB file and for AT3's in-process `land_bytes` of the same file; milliseconds for `@folder` on lane 8's folder; milliseconds until `@youtube` answers.
- [ ] Probe. Each twenty times, interleaved, on one warm host at head, the file on the same drive as the store.
- [ ] Baseline. Record the in-process `land_bytes` median first.
- [ ] Rule. `@file`'s median is within 1.3 times the in-process import of the same file, the same hash and fsync behind the resolver, or the PR fails. `@folder` on 10,000 files is under 2 s and `@youtube` answers under 500 ms, absolute budgets, because the parent refuses both.

**Review gate.** None. AT4 is not review-gated.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict in `ledger.tsv`.
- [ ] Stacked on the wave 2 tip.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] `UI-HANDOFF.md` section 18 is brought current on `plan/agent-system` (items 1, 2 and 4 say what landed, with Appendix E's contract), and `QUEUE.md` line 35 is checked.
- [ ] Reply to the operator with the report `autopilot-stack.md` names, and the stack list he lands from.

## Appendix A. Prototype evidence

- Probes run on 2026-10-28 at `0ee50e42` (`D:/Temp/attach-plan`) with the `bld-br3` venv's Python (`-I -B`), recorded with their scripts in `research/attach/probes-2026-10-28.md` and `research/attach/probes/`. Nothing of QMX was started; no CLI, model, pg0, Hindsight, browser or Credential Manager was touched.
  - F1. The four REF2 kinds are refused `not_yet` by name today. AT4 rests on it.
  - F2 and F3. The GPT lane maps images and PDFs; the chat lane maps images and refuses a PDF whole. AT5's normaliser rule rests on it.
  - F4. The normaliser forwards a PDF to a row without `pdf`. AT5 rests on it.
  - F5. The PC's upload door refuses with no server. AT3 rests on it.
  - F6. The REST door's document read crashes on a `source` with the schema's slots. AT2 rests on it.
  - F7 and F8. `view` serves card and page in 6.5 ms for one item and the store's search filters by kind; neither has a route. AT2 rests on it.
  - F9. `markitdown` 0.1.8, already locked, reads PDF text in 262 ms. AT3 rests on it, so no Docling download is needed for text PDFs.
  - F10. The new route paths are free at the tip.
- Facts read in the code at `0ee50e42`, each with its line in the PR that uses it. The context grammar, resolvers, `AttachedRef`, run input pins and budgets (`QX/context.py`). The chat reads, `StoreReads`, the session mirror and `RecordedHarness` (`HO/sessions.py`). `set_attached`, `_dispatch` and `_with_reports` (`H/harness.py`). `Prompt`, `Chat.send` and `_join` (`H/chat.py`). `TurnIn`, the turn route and `chat_routes` (`H/routes.py`). The guard (`H/guard.py`, `H/tools.py`). The REST door's routes (68, listed by `rest_routes(control_rows())`), `create_app`, `Part` and the upload door (`QX/server.py`), its Library documents (`QX/library.py`). The store's search, upload and blob stream (`LB/store.py`), the card and page read (`LB/view.py`), the `source` and other schemas (`LB/kinds/`). The relay's lanes and normaliser (`R/relay.py`, `R/normalise.py`, `R/gpt/translate.py`, `R/chat_lane.py`), the registry and profiles (`R/registry.py`, `R/profiles/`). The host's store role, routers and principal door (`HO/host.py`). The hub's upload (`QA/qmx-hub/src/qmx_hub/server.py`). The extract and capture templates (`E/templates/`). The locked SDK's `query` (`claude_agent_sdk/client.py:272-302`).
- Primary sources for the multimodal layer, saved with their URLs in `research/attach/`. The Agent SDK's streaming input takes image blocks in a user message; it names no PDF block, hence P-DOC. The Claude API's image and PDF limits, the Responses API's, and OpenRouter's Anthropic door and PDF engines.
- Facts the builders prove by running code (each PR's Build block). His click and the model's tool write one list (AT1). Every kind's page is its schema's (AT2). An upload is idempotent across cuts (AT3). Each lane gets each file as its row takes it (AT5). No reference reads what the guard refuses (AT4).
- Unproven until a PR runs. P-DOC, whether the CLI passes a base64 PDF `document` in a user message (AT5's first Build box decides the plan rows' block). Whether the CLI or Anthropic refuses an 11 MB image, and with what words (AT5 lane 5). Whether OpenRouter's Anthropic door applies its own PDF engine to a `document` (not relied on). Whether the ChatGPT sign-in route takes `input_file` (today's mapping is kept; a refusal reaches him through `map_error`'s named param, `R/gpt/translate.py:469-470`).

## Appendix B. Not in this program

- Logged to `BACKLOG.md` at program start. Audio and video without captions through a transcriber or local Whisper (AD-42), which is Appendix H's open question. Video frames for a vision pass (the `watch` pattern). Scanned PDFs through OCR, for which the `extract-source` template already waits on Docling. `@file` and `@folder` in a workflow's inputs and `@url` in a trigger's inputs, which a later engine packet can import at fire time. A `source` landing on a replica PC after a Library flip, which ruling 136 makes the uncommon shape. `vision` on OpenRouter rows whose model sees images (Kimi K2.5 is `vision` on its direct row, `R/profiles/kimi.toml:17`, and not on `openrouter.toml`), which needs a one-image probe on his key. The `extract-source` and `a-fill-the-library` templates moving onto `QX/sources.py` and `QX/imports.py`.
- The unit kinds' page tabs the full item page shows (Performance, Trading, Setup, evidence runs) belong to the unit session (ruling 138). Their schemas declare Logic, Results, Family tree, Markets and Versions today (`LB/kinds/unit.schema.json`); AT2 serves whatever the schema declares, so the unit session changes the schema, not a route.
- "Open in Lab" is the Lab's own screen and route. The screens themselves are the UI session's.

## Appendix C. Files two PRs share

| Pair | Shared file | Order |
|---|---|---|
| AT1, AT2 | none (AT1 is `QX/context.py`, `HO/sessions.py`, `H/harness.py`, `H/routes.py`; AT2 is `QX/library_routes.py`, `QX/server.py`, `QX/library.py`) | wave 1, side by side |
| AT2, AT3 | `QX/server.py` (AT2 includes its router, AT3 rewrites the upload router) | AT2 first |
| AT3, AT5 | none (AT3 is `QX/sources.py`, `QX/server.py`, `QA/qmx-control/pyproject.toml`, `qmx-agents/uv.lock`; AT5 is `H/chat.py`, `H/harness.py`, `HO/sessions.py`, `R/normalise.py`, `R/profiles/gpt.toml`) | wave 2, side by side |
| AT1, AT5 | `H/harness.py` (AT1 `_with_attached`, AT5 its blocks), `HO/sessions.py` (AT1 batch `add`, AT5 `attachment_blocks`) | AT1 first |
| AT1, AT4 | `QX/context.py` (AT1 `told` and exact `@library`, AT4 the resolvers), `HO/sessions.py`, `H/harness.py` | AT1 first |
| AT5, AT4 | `HO/sessions.py`, `H/harness.py` | AT5 first |
| AT3, AT4 | `QX/sources.py`, `QA/qmx-control/pyproject.toml`, `qmx-agents/uv.lock` | AT3 first |
| AT3 and AT4, backup B7 | `qmx-agents/uv.lock` (B7 adds the router's sealing dependency) | the backup program lands first; each AT PR runs `uv lock` after its rebase and commits only the lock's own lines |

No file of this program is in the backup program's B4 to B7 except `qmx-agents/uv.lock`. Its `HO/host.py`, `HO/first_start.py`, `HO/__main__.py`, `HO/backups.py`, `qmx_home.backup`, `R/vault.py` and `R/key_copy.py` are not edited here.

## Appendix D. Defaults

Each is Claude's default, with the reason. He can overrule any of them.

- One list, one writer. His click, a chip and the model's `context_add` all write the chat record's `attached` list through `Harness.set_attached`; `told` is the only new field. No second store of attachments.
- Chips travel as structured references with the message; a typed `@` is not parsed out of his text. A chip names an exact item, while a typed `@library:<words>` is a search and an `@` in text also means an email, a code decorator or, in an Interactive chat, the CLI's own file mention. The composer turns what he types after `@` into a chip from `GET /api/items`, so typing still works and the backend reads one shape.
- `@library:<target>` reads an item id or an object id exactly, then searches. An item id pinned with `follow` follows main.
- What the model sees of his attachments. One QMX line naming the count and the two tools, plus a native block for each image or PDF its row takes. Library text never goes into his prompt's text, because an Interactive chat is not verbatim.
- The block a file becomes, by its `media_type` and the chat's main row.

| File | Row has | Sent as |
|---|---|---|
| PNG, JPEG, GIF, WebP | `vision` | an `image` block, base64 |
| PNG, JPEG, GIF, WebP | no `vision` | none; the line says the model cannot see images |
| PDF | `pdf` (and P-DOC passed for plan rows) | a `document` block, base64 |
| PDF | no `pdf`, text read | a `document` block of its `text` slot |
| PDF | no `pdf`, text still being read | none; the line says its text is being read |
| any other file | any | none; `context_read` reads its text |

- No QMX cap. QMX resizes, splits and refuses nothing for size; the provider's own limit is the limit, and its refusal reaches him with the provider and the file named (ruling 106).
- Uploads land on the PC first (rulings 136 and 142), as a `source` with origin `upload`, deduped by the bytes' sha256. Text is read in the background with `markitdown`, already in the lock, one file at a time.
- The URL guard refuses loopback, private, link-local, CGNAT (100.64.0.0/10) and metadata addresses, and checks every redirect. `@url` fetches once a day per address; refresh fetches again.
- The folder listing shows 200 entries, Claude's default and the existing Settings value, with the count left out named. Files are read by the model's own tools.
- Captions only for videos, native first then automatic, as the template does; no transcription (Appendix H).

## Appendix E. The attach contract (reference)

The UI agent wires to this. Every route is behind the bearer.

- `GET /api/sessions/{sid}/context` answers `{entries, lines, ready, pending}` as `context_list` does.
- `POST /api/sessions/{sid}/context` with `{ref, pin}` or `{refs: [{ref, pin}]}` answers the entry (or entries) with its excerpt; `pin` is `version` or `follow`.
- `POST /api/sessions/{sid}/context/refresh` with `{ref}`, `POST /api/sessions/{sid}/context/drop` with `{ref}`, `POST /api/sessions/{sid}/context/read` with `{ref, range}`.
- `POST /api/sessions/{sid}/turns` with `{text, refs}` attaches `refs` and sends; a chip that fails answers 400 or 404 naming it and nothing is sent.
- An entry is `{ref, item_id, pin, version_id, artifact_id, status, note, told}`; `status` is `ready`, `pending`, `archived` or `not_cached`.
- `GET /api/items?q=&kind=&offset=&limit=&archived=` answers cards; `GET /api/items/{object_id}?level=card|page`; `GET /api/items/{object_id}/family`; `GET /api/kinds`; `GET /api/blobs/{blob_id}` streams bytes. Each card and page carries `object_id` and `item`.
- `POST /api/library/upload` with the body's bytes and `Content-Length`, `X-Upload-Id`, `X-Upload-Offset`, `X-Upload-Partial-Sha256`, `X-Upload-Total` and `X-Upload-Name` answers `{object_id, item, blob_id, bytes, already, reading}`, or 202 with the offset held; `GET /api/library/upload/{id}` answers the offset and hash to resume from.
- The references a chat or a run takes. `@pod`, `@unit`, `@bot`, `@session` by id; `@library` by id, object id or words; `@run:<id>[/<output>]`; `@app:<id>[/<name>]`; `@memory:<question>`; `@file:<path>[:a-b]`; `@folder:<path>`; `@url:<address>`; `@youtube:<id or address>`. A workflow's inputs take `@run`, `@library`, `@url` and `@youtube`.
- A refusal answers `{detail: {code, message}}` with one line; 409 `no_library` where the host holds no Library.

## Appendix F. Words

- **Attach.** Put a reference on a chat so its model reads the thing through a handle instead of pasted text.
- **Reference.** One `@kind:target` naming a Library item, a run's output, a file, a folder, a web page or a video. Its entry says ready, pending, archived or not cached.
- **Chip.** A reference he picked that travels with his message.
- **Pinned.** The reference reads the version it was attached at, and says "newer version exists" when main moves. **Following** reads main each time.
- **Upload.** His file sent into the Library on this PC, kept as an item with its original bytes and the text QMX read from it.
- **Reading.** QMX pulling a file's text out in the background after it lands.
- **Card** and **page.** The small view of an item among many and the full view when he opens one.

## Appendix G. Alternatives weighed

- Parsing a typed `@` out of his message. Rejected (Appendix D). It is ambiguous, collides with the CLI's own `@path` in Interactive chats, and makes the backend guess what the composer already knows.
- Pasting each attachment's excerpt into his prompt. Rejected. An Interactive chat is not verbatim, so Library text with an `@path` in it would make the CLI read a file; the model reads through `context_read` and gets media as blocks.
- Sending files through the Anthropic Files API by `file_id`. Rejected. The relay's other lanes have no such id, a plan chat's CLI owns its own upload path, and base64 per turn is what every lane already maps.
- Docling for every upload. Rejected. Its pin needs a large download and 7 GB of memory at peak (`extract.py:24-26`); `markitdown` is already locked and reads text PDFs. Docling stays the `extract-source` template's for scanned files.
- Keeping the server-only upload and adding a local fallback beside it. Rejected. The PC is primary by default (`HO/host.py:605-608`), so the writer path is the main one and the server stream is the replica's.
- A new `/api/library/...` path for the screen reads. Rejected. `GET /api/library/{artifact_id}` is registered first and would swallow it.
- Resizing images to fit a provider. Rejected. It is a QMX limit by another name, and the provider's refusal already names its own.
- A REF2 kind as a workflow run of its own (AD-63's heavy reference). Kept only for videos, as a background thread rather than a run, because a caption fetch is one `yt-dlp` call and a run adds a template, a trigger and a work zone for no reader.

## Appendix H. Gates and calls

- G-LAND. He lands the stack himself.
- One open question, carried on with its default. **Videos and recordings with no captions.** Transcribing them needs either local Whisper (a model download of a few GB on a PC with about 8 GB free on D, `research/methodology/52-data-round-inventory.md` summary item 11) or a transcription provider's key, which costs money. The recommendation, which this program applies, is no transcription. Such a video reads ready with "no captions" and its title and description, and the item is in `BACKLOG.md` for him to choose local or paid. He can say "use local Whisper" or "use <provider>" and the coordinator queues it.
- No other call needs him. Nothing here touches money or his brokers, the words are the design's and Appendix F's, and nothing is deleted except `Part`, which the store's `Upload` replaces line for line.
