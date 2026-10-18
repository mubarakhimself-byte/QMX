# 35 — Architecture amendment after the first build run

Date: 2026-10-18. Author: the architect (Opus 5.5), headless, BMad architecture skill in update mode plus the codebase-design vocabulary. No sub-agents, no code edits, no commit. Fable was not used (ruling 87).

Inputs: `34-engine-run-triage.md` (amendment list and HG3 list), `qma-ship/engine/BACKLOG.md`, `lows.md`, `review/*.md`, the built code on branch `engine/tp4` (63154922, the latest engine branch), rulings 1-91 of `26` and his rulings of 2026-10-18: (a) tests run on haiku through his plan login, OpenRouter only proves other providers work, no spend cap; (b) no unplanned work during a run; (c) no Fable.

Files changed in place, all under `tracker/qma-v2/architecture/workflow-engine/`: `ARCHITECTURE-SPINE.md` (AD-24 rewritten in place, AD-36 and AD-37 appended, 20 other ADs amended), `SOLUTION-DESIGN.md` (new §5.5 and §25, E33-E41), `HARNESS-REQUESTS.md` (round HG3), `LIBRARY-REQUESTS.md` (L18-L20), `OPEN-DECISIONS.md` (D, E, F), `DOC-CHANGES.md` (rows 27-32), `PLAIN-WORDS.md`, `HEADLESS-RESULT.json`, `.memlog.md` (49 new entries, D1-D35), and `reviews/review-2026-10-18-amendment-gate.md`. `lint_spine.py`: 0 findings. AD ids are unchanged.

Labels: **[retrieved]** read today from a file, a branch or the web; **[remembered]** training knowledge, not re-checked; **[inferred]** reasoned here.

## 1. What the built code showed (ground truth)

- Script zone `<home>/workspaces/wf-<id>/runs/<run_id>`; plan login `<home>/claude`; scripts run on the engine's own interpreter with `-I`, so `keyring` and `qmn` import [retrieved `runner.py`, `nodes/script.py`, `qma/harness/home.py:122`].
- The keyring holds `qmx/control-token`, the ChatGPT sign-in, provider keys and broker credentials [retrieved `qma/console.py`, `qma/gpt/siwc.py`; remembered from his credentials note].
- The lint reads `node.type` and `parameters` only [retrieved `definition/lint.py`]. The harness gate's fuller matcher already exists: `qma.core.barriers.descriptors` [retrieved].
- A probe of that matcher [retrieved, scratchpad `probe_money.py`]: it catches `placeorder`, `flatten`, `set_leverage`, `closeAllPositions`, "place a market order" and "Flatten all positions". It passes `open_positions` and "List the open positions". It flags the bare nouns `sort_by_position` and `position_size`, and it reads "Write the order of the sections" as `write_order`.
- HG1's per-chat hooks only observe; they cannot block a call [retrieved `launch.py:117`].
- The PC runs Windows 11 Home [retrieved session environment], so Windows Sandbox is not available.

## 2. Host-script isolation (AD-24, AD-25, AD-36, AD-37)

### 2.1 Where things live

| Candidates | Choice | AD |
| --- | --- | --- |
| (a) keep zones under the home and rely on the env scrub; (b) move the plan login out of the home; (c) put zones under a separate `zones_root` and let an OS boundary grant only the zone | **(c).** (a) is what B-30 broke. (b) touches the harness (ruling 24), and a process running as him reaches any path anyway. Each run gets `<zones_root>/<run_id>/code` (a read-only, hash-checked copy) and `work/` (its cwd). `zones_root` is never the home, never inside it and never above it. | AD-24, AD-18 |

### 2.2 The OS boundary on Windows now

| Candidate | Verdict |
| --- | --- |
| Env scrub only | rejected: proven insufficient (B-30) |
| Separate low-privilege Windows user | rejected: needs an admin step and a stored password, which is one more secret; AppContainer gives the same separation without either |
| Job object | **kept as a layer**: `KILL_ON_JOB_CLOSE` with no breakaway, a process limit, a memory limit and UI limits. It controls lifetime, not reach [retrieved Microsoft Learn] |
| AppContainer | **chosen for scripts QMX shipped**: no admin, no password; files are denied unless granted, the network is off without a capability, and loopback is blocked [AppContainer isolation retrieved from Microsoft Learn; the credential and loopback rows are remembered and go to probe E33] |
| Docker/WSL hardened `runc` | **chosen as the default for every script QMX did not ship**: the same image and rules as remote placements |
| Windows Sandbox | rejected: not available on Windows 11 Home [retrieved] |

If E33 shows the AppContainer fails to deny the plan folder, `CredRead` or loopback, the host tier is switched off and shipped scripts also run in a container. Nothing ever falls back to a bare host process.

### 2.3 The other layers

- **Which scripts may run on the host.** Only those whose every `.py` file is byte-identical to the shipped template manifest of the installed engine. Any edit, import, run-made change or challenger moves the script to the container. With Docker off, those scripts wait with "Docker is off". (AD-24)
- **Refusing `keyring` and `qmn`.** Three layers. First, the scan refuses imports by statement or literal dynamic import: `keyring`, `keyrings`, `win32cred`, `win32crypt`, `qmn`, `qma`, `qmf`, `qmx_*`, `ctrader_open_api` and `MetaTrader5`. Host scripts are also refused `ctypes`, `winreg`, `subprocess`, `multiprocessing`, `exec`, `eval`, `compile`, `runpy`, `pickle`, `marshal`, `shelve`, the `os.system` family and non-literal imports. Second, scripts run on a separate script-runtime venv that does not contain those libraries, and its boot module adds an audit hook. Third, the OS boundary. (AD-24, AD-36)
- **Money-lint coverage.** The scan covers names, notes, type, parameters, settings, meta, port names, `pinData` and every file in the folder. It uses the harness gate's own matcher in a call-shaped way: AST call and def names in code, a verb plus an object within three words in prose, keys only in data. A hit counts only when the act has a verb. It fails closed with no allow-list. The rejected options were a bare identifier scan (it flags `open_positions`) and a second matcher (it would drift from the gate). (AD-36)
- **Broker credential refs.** A node may name only refs that a Settings `[credentials.tools]` row declares. A code-declared deny-list refuses `qmx/ctrader-*`, `qmx/mt5-*`, `qmx/broker-*`, `qmx/prop-*` and `qmx/venue-*`, provider key rows, the control token, the GPT sign-in and the pairing and backup keys. The check runs three times: in the lint, in the Settings validator and in the resolver. (AD-36)
- **Redaction.** One function, applied at the write seams: the ledger writer (which also covers the inbox), the `LibraryPort` adapter and the REST serializer. Two other options were rejected: redaction inside each executor (it missed cases, L-50 and L-52) and redaction at read time (the secret would already be on disk). Specific key prefixes are matched even when glued to a word. Values the engine handled are replaced by value. Redaction happens before commit, and the core reads outputs only from committed events, so a live run and its replay see the same text. (AD-37)
- **The `--mode live` CLI.** Removed. The CLI tests only, and a `fake: true` run is always `mode: test`. Live runs start only through the service, on an object on `main`, by a `user` principal, the scheduler or a live parent. Publish and enable are `user`-only; the copilot shows a card instead. The MANAGE ask alone was rejected, because qmx-control cannot tell REST from a tool call (B-65) and the service accepted `Caller("workflow")` (L-53). (AD-11, AD-22)
- **Orphans.** Job objects on the PC; containers run with `--rm --init` and labels. A sweep at start-up runs before any resume and folds lost attempts as `unknown`. Restores stay inside `work/`, and a junction there fails the attempt, not the engine. (AD-24)
- **Run context.** The script environment carries `QMX_RUN_ID`, `QMX_NODE_ID`, `QMX_ATTEMPT`, `QMX_MODE`, `QMX_FAKE`, `QMX_NOW`, `QMX_IDEMPOTENCY_KEY`, `QMX_WORK` and `QMX_CODE`, and never the home. Scripts never open stores; engine state arrives through `engine_view` reads. Network is off unless the node declares it. (AD-24)
- **Agent chats.** Built-in `Bash`, `Write`, `Edit` and `NotebookEdit` are removed through H2. Until H2 lands, those tools must raise an ask that the engine rejects (check E35), or agent nodes on the PC are held. (AD-24)

## 3. SPEC-GAP decisions (all 26 rows)

| Item | Candidates | Choice | AD |
| --- | --- | --- | --- |
| Port names (B-15) | invent per builder; ratify the registry | ratify: `in` and `main` as defaults; `rule` has `true`/`false`; `loop` has `in`/`next` in and `body`/`done` out; `grader` has `pass`/`fail`; `monitor` has `changed`/`silent`; `human_gate` has one port per option; a switch kind is deferred | AD-4 |
| Port kinds (B-14) | type them now; drop them; every v1 port carries `data` and the field is kept | the third | AD-4 |
| Agent caps (B-16) | required by the lint; a default | default from Settings, recorded on `run_created`; `max_turns` raised from 12 to 40 [inferred] | AD-4 |
| Readiness (B-24, B-87) | any input; all-live by default; `required` per edge | `required` per edge, off by default; an edge from outside a loop body is context only | AD-5 |
| Subworkflows (B-27, B-76) | child folder only; pinned object only; both | both: a block folder in the bundle or a pinned object; `caller_policy` checked at validation; a waiting child gives `waiting(child)`; cancel cascades; Library L18 | AD-5, AD-14 |
| Runaway numbers (B-38, L-49) | `settings.py` 400k / 12 / 2 h; SD §17 | SD §17: 2M tokens, 16 agents, 1,000 tool calls (a new default), 4 h | AD-16 |
| Cache reads (B-49) | count them; don't | don't: tokens = in + out + cache_write | AD-16 |
| Wall time (L-48), in flight (L-45), degrade (L-46) | — | count only while an attempt is in flight; check every tick; a breach starts nothing new; degrade releases work in waves | AD-16 |
| Join words (B-23) | — | waiting reason `join`; `direction: up / down`; an `info` line for a late failure | AD-16 |
| Enable/disable (B-68) | cascade with a count; derived | derived: a version is enabled while an enabled trigger pins it | AD-10 |
| Time `wait` wake (B-63, B-73, L-37) | — | every `resume_at` writes a wake row; the ticker resumes the run; UTC instants | AD-10 |
| Run-context env (B-78, B-80, L-84) | — | §2 above | AD-24 |
| Replay on an edited folder (B-82) | prefix replay; a fresh test run; a fork that reuses unchanged memos | the fork: `service.runs.replay`, Library edge `replay-of` (L20) | AD-7, AD-26 |
| Decision cards (B-88) vs ruling 77 | inbox cards; a waiting `human_gate`; typed proposals | proposals: a `proposal` artifact with actions he takes as `user`; nothing waits; the inbox keeps the ruling-77 classes (L19) | AD-17 |
| Typed artifacts (B-83) | — | an optional type per listed file, `run-file` by default | AD-14 |
| Fable in the ladder (L-23) | — | no default list names Fable; the strong ladder is opus → gpt | AD-13 |
| Span keys and statuses (B-18) | — | every node event carries `node_id, iteration, partition, attempt`; `gate` comes from `gate_opened`, `cancelled` from `node_failed{cancelled}` or `run_cancelled` | AD-15 |
| Layer diagram vs AD-1 (B-12) | — | redrawn to the built import graph, with the runner as driver | spine diagram |
| Monotonic clocks in core (L-20) | — | no clock of any kind in core or definition | AD-6 |
| pinData and `meta.needs` in the hash (L-26, L-75) | — | both in the hash, plus every file in the folder | AD-11 |
| WorkerPort shape (L-42) | — | `run(job, emit)` and `cancel(key, reason)`; no executor crosses the port | AD-20 |

## 4. New packets (sketched in SOLUTION-DESIGN §25; listed in DOC-CHANGES row 27 for Appendix G)

Script isolation comes first and starts with probe E33. The others are gate folding (B-28, B-32), nested fan-out (B-20; v1 refuses it at validation in the meantime), chunk retry under the ladder (B-35), grader `llm` mode (B-46, B-81), pinData (B-47), ledger-derived run state (B-40, B-73, L-68), the replay fork (B-82) and `engine_view` reads (B-80, L-84).

## 5. HARNESS-REQUESTS round HG3

The requests are H2 (re-asked, narrowed to a per-chat tools list or a deny-only PreToolUse), H18 `end_chat`, H19 `compact_at` on the chat record plus `attach_hooks`, H20 `DOMAIN_WRITE` that never asks, H21 an appended system prompt, H22 `py.typed`, H23 an `open_control` factory, H24 a REST-vs-agent principal in qmx-control, and H25 an exported chat router. Each row gives its reason, its smallest form and its fallback. The round also carries five bug fixes (L-16, L-17, L-8, L-9, B-67) and a live proof of the 40 % compaction (L-10). B-56 needs no request: once H23 exists, the engine writes the home itself.

## 6. Left open on purpose

- **D.** Whether to grant HG3. H2 matters most: the EP14 evidence suggests the fallback ask does not fire, so agent nodes on the PC may be held until H2 lands.
- **E.** Edited workflows need Docker Desktop running.
- **F.** The money scan fails closed with no allow-list.
- **0.** The two shipped templates that read the network stay host-confined.
- AppContainer versus container-only for shipped scripts is decided by probe E33, not by him.
- Port kinds beyond `data`, a switch kind, a reviewed allow-list for the scan, and a host tier on Contabo are deferred.
- The hygiene and BUG rows of `34` are not architecture. The spine gives the rule where one was missing (for example B-55's watchdog wording), and the fixes belong to the hardening plan.

## 7. Plain words: how your sign-ins and your money are now protected

In the first build, a small script inside a job ran as you. It could have opened your Claude sign-in folder and read the keys stored in Windows, including the broker ones. Nothing used that hole, and no broker is connected yet. Now:

1. **Scripts work in their own folder, away from QMX's home.** There is nothing of yours next to them.
2. **Only scripts QMX shipped, unchanged to the last byte, run on your PC directly.** Even those run inside a sealed Windows box that cannot see your sign-in, your stored keys or QMX itself. Anything edited, imported or written by an AI runs in a throw-away container instead, and waits if Docker is off.
3. **If QMX crashes, every script it started dies with it.** Nothing is left running in the background.
4. **Scripts run on a separate Python that does not contain the key-store or broker libraries.** Before any job runs, a check reads every script, prompt and name for money actions ("place an order", "close the position", "flatten") and for any broker key, and refuses the job. It uses the same checker that already guards your copilot.
5. **Anything that looks like a key is blanked before it is saved or shown.**
6. **Publishing, switching a schedule on and starting a live run are your clicks only.** The copilot and running jobs cannot do any of them, and the engine's command line can only run tests.
7. **AI agents inside jobs lose their own shell tools once the harness grants H2.** Until then they may be held on your PC, which is why H2 is the first thing to approve.
