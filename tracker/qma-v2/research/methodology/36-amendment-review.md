# 36 — Adversarial review of the architecture amendment after the first run

Opus is reviewing Opus here: the amendment (`35`) and this review are both by Opus 5.5. Fable was not used. No sub-agents, no edits outside this file, no commit.

Date: 2026-10-18. Ground truth: branch `engine/tp4` (63154922) in `C:\Users\Mubarak\Desktop\QMX`, read with `git show`, `git grep` and `git archive` into the scratchpad (no checkout). Under review: `architecture/workflow-engine/*` as amended, `methodology/35`, against `methodology/34` and rulings 1-91 of `26`, plus the 2026-10-18 rulings (haiku via the plan login for tests, no spend cap, no Fable).

Probes run (scratchpad `…/5efecf49-…/scratchpad/probe/`):
- `scan36.py`: an approximation of AD-36. It runs `qma.core.barriers.descriptors` from `engine/tp4` over the 31 template folders and `_shared`, classing surfaces the way AD-36 says (identifiers, prose, AST code, data). The output is `scan36.out`.
- Spot calls of `name_money_act` and `description_money_act` on bypass spellings.
- `Get-Volume`, the ACL of `D:\`, `docker version`, `wsl -l -v` and `.venv\pyvenv.cfg` on this PC.

Ranks: **critical** means the amendment, as written, does not close the hole it claims to close or would land a broken pack. **should-fix** means a real gap with a cheap fix. **note** means record it and move on.

---

## Critical

### C1. The agent-chat layer leaves the shell open: PowerShell and Monitor are missing, and H2 names the wrong SDK option

- **Location:** spine AD-24, *Agent chats share the boundary* (`ARCHITECTURE-SPINE.md:217`); SD §5.5 layer 8 (`SOLUTION-DESIGN.md:401`); E35 (`:1139`); `HARNESS-REQUESTS.md:39` (H2); OPEN-DECISIONS D.
- **Problem 1: the list of removed tools is incomplete.** AD-24, H2 and E35 remove `Bash`, `Write`, `Edit` and `NotebookEdit`. The harness lists three built-in tools that take a command line. Two of them, `PowerShell` and `Monitor`, are not on the amendment's list, and on this Windows PC an engine agent keeps both. `WebFetch` and `Read` also stay. Together they can read user files and send them out.
- **Evidence for problem 1:** `qma-harness/src/qma/harness/money.py:46`: `SHELL_TOOLS = frozenset({"Bash", "PowerShell", "Monitor"})`. DESIGN.md:237 lists the same three.
- **Problem 2: H2 names the wrong SDK option.** H2 says "passed to the SDK's allowed-tools option". In the Agent SDK, `allowed_tools` only approves tools in advance. It does not restrict which tools exist. A list passed there would approve whatever it names and leave every other built-in tool in place.
- **Evidence for problem 2:** the Agent SDK Python reference (https://code.claude.com/docs/en/agent-sdk/python), on `allowed_tools`: "This does not restrict Claude to only these tools". On `disallowed_tools`: a bare name "removes the tool from Claude's context". The harness today builds `tools={"type":"preset","preset":"claude_code"}` and `disallowed_tools` (`launch.py:490,507`). It does not build `allowed_tools`.
- **Problem 3: the second form of H2 reopens the HG1 contract.** The "equal alternative" is a PreToolUse callback that may return `deny`. HG1's hooks are observe-only by contract: `launch.py:117-121` says they "cannot allow, deny or change anything". The alternative would make them gating.
- **Problem 4: the ask fallback can become an automatic allow.** The fallback relies on an ask that the engine rejects. Per-workspace "always allow" rules are merged into `permissions.allow` (`home.py:223`), and the user settings carry a `permissions.allow` list. If he once allowed `Bash` in a `wf-*` workspace, or allows it globally, the ask never fires.
- **Fix:**
  1. Rewrite H2 as `NewChat.tools: list[str] | None`, mapped to the SDK **`tools`** option. It gives the exact built-in set. `[]` means none, and the MCP servers stay as they are. For `llm` nodes the knob already exists: `ChatConfig.tools: bool` at `launch.py:156`, which `NewChat` does not expose. For agent nodes under `runner_outside`, specify an allow-list rather than a deny-list: no built-in tools, plus the sandbox MCP tools. If an allow-list is refused, the deny form is per-chat bare names in `disallowed_tools`: `Bash`, `PowerShell`, `Monitor`, `Write`, `Edit`, `NotebookEdit` and `WebFetch`.
  2. Drop the PreToolUse-deny alternative.
  3. Add `PowerShell` and `Monitor` to AD-24, SD layer 8, E35 and PLAIN-WORDS item 7.
  4. E35 must run with his real Settings, including the `remembered` rows, and must assert that no allow rule matches a shell tool in any `wf-*` workspace.

### C2. The AD-36 rule "a hit needs a verb" is undefined, and either reading fails

- **Location:** AD-36, *Matcher* (`ARCHITECTURE-SPINE.md:289`): "A hit counts only when the act carries a verb; a bare family noun … is ignored."
- **Problem:** the harness gate returns an act string. The spine does not say whether "carries a verb" is tested on the returned act or on the identifier's own words. Both readings fail:
  - **Reading A (on the returned act) opens a bypass.** `send_order` and `post_order` return the bare act `order`, so a filter on the act drops them. Yet `send` and `post` are both in the gate's verb sets.
  - **Reading B (no filter) refuses every template.** The matcher's suffix rule refuses the bare identifier `mode` (`match_money_path_act("mode") == "mode"`). `mode` occurs in a definition of every one of the 32 folders. `size` (from `chunk.size`) and `order` hit too.
  - The spine also says the engine uses "the harness gate's own matcher". The extra filter is a second rule, which brings back the drift AD-36 says it prevents.
- **Evidence (probe, `engine/tp4` matcher):**

  ```
  send_order -> order     post_order -> order     api_order -> order    make_order -> order
  OrderSend  -> send_order (has a verb)            ProtoOANewOrderReq -> new_order
  'send' in verbs: True   'post' in verbs: True
  mode -> mode   (all 32 folders hit; 48 hits)     chunk.size -> size (10 hits)
  ```

- **Fix:** define the rule in the spine as a predicate on the **input words**. An identifier hit counts when `name_money_act(x)` returns an act and the split words of `x` (the gate's `_words`) contain a word from `MUTATING | MONEY | STRONG_BULK | BULK` verbs. An act from the gate's own suffix list that is a bare noun or `mode` counts only for a `def` or call name, never for a JSON key. Put that predicate in `qma-core` next to `name_money_act`, as `name_money_act_called(x)`, so the gate and the engine share one function. Add `send_order`, `post_order`, `api.post_order(...)` and a key named `mode` to E36.

### C3. Once AD-24 and AD-36 land, 10 of the 31 shipped templates stop running, and only 2 of the 10 are budgeted

- **Location:** AD-24 (provenance and network off by default), AD-36 (imports and scan), DOC-CHANGES row 29, OPEN-DECISIONS 0, SD §25 *Script isolation*. Ruling 83 says each shipped template "must actually run on the engine".
- **Evidence (probe and `git grep` on `engine/tp4` templates):**

  | Template | What breaks | Budgeted? |
  | --- | --- | --- |
  | `t7-trade-journal-review` | Refused by the scan: the node name "At least 20 new trades?" (`definition.json:24`, and again in `connections`), README:10, `journal.py:4`, `too_few.py:1` and `slices.py:6` all read as `new_trade` or `stop_trade` | no |
  | `dm-demo-monitor` | Refused by the scan: `checks.py:4` docstring "…a duplicate order…" reads as `stop_order` | no |
  | `ma-mini-app-lifecycle` | Refused by the scan: `scaffold.py:4` docstring "…anything that moves money…" reads as `move_money` | no |
  | `a-fill-the-library` | `capture.py:10-11` imports `subprocess` and `shutil` and runs `yt-dlp`, which the host tier refuses. It also needs the network | no |
  | `rv-weekly-review` | `week.py:14-19` imports `qmx_engine` | yes, row 29 |
  | `db-desk-brief` | `gather.py:75-99` imports `qmx_engine`, and it uses `urlopen` with no `network: true` | partly: row 29 covers the imports, decision 0 the network |
  | `t4-research-desk-overnight` | `news.py:31` uses `urlopen` with no `network: true` | decision 0 only |
  | `rs1-paper-scout` | `fetch.py:27` and `feed_ids.py:36` use `urlopen` | **no** |
  | `rs4-literature-review` | `sources.py:28` uses `urlopen` | **no** |
  | `t3-news-calendar-watch` | `calendar.py:30` uses `urlopen` | **no** |

  No template definition declares `network` (`git grep '"network"'` finds only one script file). Decision 0 says two templates read the network; five do.
- **Fix:**
  1. Make the script-isolation packet own the pack. Its last step runs E34 and E36 over **all 31 templates**, live and fixture, and the packet is not done until every template passes.
  2. Extend the shipped manifest with a per-script `tier: host | container` and `network: bool`. The host-only refusals (`subprocess` and the others) apply only to scripts the manifest marks `host`. `capture.py` becomes `container` with `yt-dlp` in the `qmx-worker` image.
  3. Add `network: true` to the network nodes of rs1, rs4, t3, t4 and DB.
  4. Correct decision 0 to five templates.
  5. Reword the three refused templates as C2's fix allows. F6 below narrows the surfaces, which removes most of these hits.

---

## Should-fix

### S1. AD-24 cites a Microsoft Learn page that promises less than the spine claims, and E33 misses rows

- **Location:** AD-24 *`host_confined`*; `35` §2.2 ("files are denied unless granted … [retrieved Microsoft Learn]"); SD §16 row (`:932`); E33 (`:1137`).
- **Evidence:** https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation says the AppContainer "prevents the application from **modifying** files that it should not". It says nothing about denying reads. Its credential sentence is about using his credentials to reach network resources ("the application cannot impersonate the user"), not about Credential Manager `CredRead`. Loopback is blocked by Windows Filtering Platform filters, and a `CheckNetIsolation LoopbackExempt` entry can lift the block (https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall).
- **Facts from this PC:** the venv's base interpreter lives in his profile (`pyvenv.cfg`: `home = C:\Users\Mubarak\AppData\Local\Python\pythoncore-3.14-64`). A venv `python.exe` only redirects to that base, so granting read only on "the script runtime" will fail to start Python, or will tempt a grant on a folder in his profile. `D:` is NTFS and grants nothing to ALL APPLICATION PACKAGES, which is good.
- **Fix:**
  1. Label the read, credential and loopback rows **[remembered]**, and E33 alone.
  2. Make the script runtime a self-contained interpreter (an embeddable or standalone CPython copied to `%LOCALAPPDATA%\qmx-script-runtime`), not a venv.
  3. Add these E33 rows, each of which must be denied:
     - read a file under `%USERPROFILE%` (the QMX repo on the Desktop);
     - read `D:\QMX-worktrees`;
     - open `\\.\pipe\dockerDesktopLinuxEngine` and `\\.\pipe\docker_engine` (the Docker pipe is root on the WSL VM);
     - open `\\wsl.localhost\Ubuntu-24.04\`;
     - with `internetClient`, connect to a Tailscale `100.x` address and the LAN gateway;
     - a `CheckNetIsolation LoopbackExempt -s` listing that does not name `qmx-script`.

### S2. One AppContainer profile for every run lets concurrent runs read each other's `work/`

- **Location:** AD-24 *`host_confined`*: "AppContainer profile `qmx-script` … the SID is granted … modify on `work/`".
- **Problem:** the grants pile up on one SID. A shipped script in run A can read run B's `work/` and its outputs.
- **Fix:** give each attempt its own profile (`qmx-script-<run_id>-<attempt>`, deleted after the attempt), or remove the grant on `work/` when the attempt ends. Prefer a less-privileged AppContainer, which ignores ALL APPLICATION PACKAGES grants, if E33 shows Python still starts under it.

### S3. Docker Desktop on WSL2 is weaker than study 29's gVisor, and the spine does not say so

- **Location:** AD-25 isolation tiers (on the PC, "model-written code runs in hardened `runc` with no network"); SD §5.4 blast radius (`:364`).
- **Problem:** every WSL2 distro shares one utility VM and one kernel. This PC has `docker-desktop` and `Ubuntu-24.04` (`wsl -l -v`). A container escape lands in a VM that mounts his Windows drives (Docker Desktop exposes them under `/mnt/host/<drive>`) and, with WSL interop, can start Windows programs as him. That reaches the plan login file and then the keyring. Hardened `runc` stops ordinary code. It does not stop a kernel escape, which is the threat 29 named for model-written code. [remembered: the `/mnt/host` path and the interop default; the shared VM is shown by `wsl -l -v`.]
- **Fix:** make `contabo` (`runsc`) the default placement for model-written code. The PC's hardened `runc` becomes the fallback when Contabo is unreachable, with a doctor line. Add a live check that a container started the engine's way cannot see `/mnt/host` or `/mnt/c` and cannot run `cmd.exe`. Record in the spine that the PC tier offers no protection from kernel escapes.

### S4. "Docker is off" means waiting, and Docker is off on this PC right now

- **Location:** AD-24 *Provenance*; OPEN-DECISIONS E; PLAIN-WORDS item 2.
- **Evidence:** `docker version` answered "failed to connect … `//./pipe/dockerDesktopLinuxEngine` … cannot find the file", and `wsl -l -v` shows `docker-desktop` stopped. Ruling 83 has him editing templates with the copilot, so most of his workflows will soon be "edited". Ruling 77 says almost nothing waits, and ruling 55 says not to rely on his laptop.
- **Fix:** when a container attempt finds Docker down, the engine first starts Docker Desktop itself (this is his own app, so no question is asked) and waits for its health with a timeout. If Docker does not come up, it places the attempt on `contabo` (AD-30 spill), which needs only `code/` and `work/`. It goes `waiting(placement)` only when neither works. Add this to E34.

### S5. The credential deny-list is matched by prefix and is fail-open for the names that actually exist

- **Location:** AD-36 *Credential refs*.
- **Evidence:**
  - Broker connections take any `credential_ref`. The tests use `qmx/ctrader` with no suffix (`qmx-broker/tests/test_broker.py:160`, `qma-harness/tests/test_money.py:50`), which `qmx/ctrader-*` does not match.
  - Windows target names ignore case (`test_posture.py:72` uses `qmx/Ctrader`).
  - DESIGN.md:248 already sets the fail-closed posture: every `qmx/*` entry not known to be a provider key, `qmx/chatgpt` or `qmx/control-token` counts as broker.
- **Fix:**
  1. Tool credentials must live under a reserved namespace, `qmx/tool/<name>`. A node may name only those, and only when a `[credentials.tools]` row declares them.
  2. Compare names casefolded.
  3. The deny set also takes every `credential_ref` from the broker connection rows and every keyring entry the posture classes as broker.
  4. Add `qmx/ctrader`, `QMX/CTRADER-DEMO` and an operator-named broker ref to E36.

### S6. AD-36 bypasses that should be named, with the ones worth closing closed

- **Location:** AD-36 *Surfaces* and *Imports*.
- **Probe (`description_money_act`):** these phrasings pass: "Buy 1 lot of EURUSD now", "Go long EURUSD", "Liquidate the book", "Please purchase 100 shares", "Increase the lot size to 5", "Take profit on all trades now". These are refused: "Then place a market order to buy EURUSD" and "Close every open position immediately".
- **Remaining paths:**
  - A host script builds a name from strings: `getattr(c, "place"+"_order")` is not refused. Only literal arguments to `getattr` are read.
  - Container scripts are not refused `exec`, `eval`, base64 or `subprocess` at all.
  - Non-Python files have no AST and no class (`.js`, `.sh`, `.ipynb`).
  - A URL or host string literal is never read, so `requests.post("https://<broker>/orders")` passes.
  - Text injected at run time (news, web pages) never meets the scan.
- **Judgement:** the scan cannot be the boundary, and the spine should say so. What actually protects his money is that no broker credential is reachable (S5), that no money tool exists, and that the harness gate stays in force.
- **Fix:**
  1. State in AD-36 that the scan is a lint, and name the three structural layers.
  2. Refuse non-literal `getattr` and `setattr` in host scripts, as non-literal imports already are.
  3. Class every non-Python code file as code that sends the script to the container, and scan it as prose.
  4. Check string literals that look like hosts, and every declared egress host (container `egress hosts`, AppContainer `network: true` nodes), against the harness gate's broker-host list (DESIGN.md:237, `money.py` rule 7), so there is one list.
  5. Add the six missed phrasings above to E36 as expected refusals in prompts, or record them in the spine as accepted misses.

### S7. AD-37 misses four paths a key can take

- **Location:** AD-37 (`ARCHITECTURE-SPINE.md:295`); SD §5.5 launch text ("stream stdout and stderr through the redactor").
- **Paths missed:**
  1. **Agent transcripts.** A sandbox tool result (a script printed a tool key) goes back to the agent chat. From there it is written by the CLI to its JSONL and by the harness to its session rows. The harness `project` redacts only `sk-ant-` (DESIGN.md:255). The engine's own sandbox MCP server (AD-25 `runner_outside`) is the last point the engine controls before the transcript, and AD-37 does not name it.
  2. **Library blobs.** AD-37 covers "artifact metadata", not artifact contents or the mirrored transcripts L7 indexes. A script that writes a key into a `work/` file ships it as a `run-file`.
  3. **Memo rows.** Memos are stored outputs in their own table (`ledger/memo.py:1-6`), not event `data`. If they are written before redaction, replay sees raw values, which breaks AD-37's own "live and replay see the same text".
  4. **Chunk edges.** Redacting a stream chunk by chunk leaks a key that is split across two chunks.
- **Fix:**
  1. Add a fourth seam: every result the sandbox tool server returns to a chat passes `ledger.redact` first.
  2. The `LibraryPort` adapter redacts every text blob it writes, contents included, and refuses a binary blob that contains a registered value.
  3. Memo rows are written from the redacted event payload only.
  4. Stream redaction keeps a carry-over buffer of the longest key shape, or redacts only complete buffers.
  5. Registered values shorter than 12 characters are refused at resolve, so redaction never blanks common words.
  6. Add these four paths to E37.

### S8. HG3 is not minimal, and four rows clash with DESIGN.md or with the engine's own design

- **Location:** `HARNESS-REQUESTS.md:39-47`; OPEN-DECISIONS D.
- **The clashes:**

  | Row | Problem | Evidence | Fix |
  | --- | --- | --- | --- |
  | H18 `forget` | Deleting the control session row erases audit history that AD-25 keeps "outside every sandbox". It also erases the session `tool` blocks that the fallbacks for H16 and H19 read for tool spans | AD-25 rule; HARNESS H19 fallback | `end_chat(sid)` closes the CLI only. The list filters by chat kind (`GET /api/chats?kind=interactive`). Nothing is deleted |
  | H20 | An allow rule seeded for `DOMAIN_WRITE` rows also changes the copilot's Interactive chats, which breaks DESIGN's "same permission modes and rules" (DESIGN.md:23). The fallback is one Settings rule | DESIGN.md:23, 209 | Refuse or defer, and use the first-run card. If granted, scope it to Background chats |
  | H21 | The appended system prompt goes on the Windows command line (`--append-system-prompt`), under `ARGV_BUDGET` 30,000 characters, and is joined to the harness's own `append` | DESIGN.md:213-214; `launch.py:491-495` | Cap the brief (say 8,000 characters) and refuse above it. State that the harness's `append` comes first |
  | H23 | It asks to "read and write Settings", but SD §7.4 says the engine "reads them through `SettingsPort` and never edits them" | `SOLUTION-DESIGN.md:523` | Read-only, or drop it: Appendix G L1 puts the engine in `qma.serve` |
  | H25 | Needed only until Appendix G L1 | its own fallback text | Drop it |
  | H24 | It labels who acted. It is not a boundary: DESIGN accepts that "an agent with Bash could read the qmx-control bearer" | DESIGN.md:314 | Keep it as attribution only, and fix PLAIN-WORDS item 6 (S9) |

- **The minimal round:** H2 (as C1 rewrites it), H18 (close only), H19, H22 and the five bug fixes. H20, H21, H23, H24 and H25 can wait.

### S9. The plain-words promise that publish, enable and live runs are his clicks only claims too much

- **Location:** `35` §7 item 6; PLAIN-WORDS; AD-11 and AD-22.
- **Problem:** the copilot is an Interactive chat with Bash and PowerShell running as him. It can read `qmx/control-token` with code that never spells the exact entry name, then call REST as `user`. DESIGN.md:232 and :314 accept both points. H24 and the service checks stop engine code and the `qmx` tools, not the copilot's shell.
- **Fix:** reword item 6 to "the copilot's tools and running jobs cannot do any of them". Record in AD-22 that the copilot's own shell is a known gap, closed only by the later OS-account zone (DESIGN.md:287).

### S10. Some spec-gap settlements need code rewrites that no step or packet budgets

- **Location:** `35` §3; SD §25; the `34` hardening steps 1-5 (`34:361-411`).
- **Evidence:**
  - These rows are in neither a hardening step nor a §25 packet:
    - `required` edges (B-24, B-87; `core/ready.py` has no `required` today);
    - cache reads not counted (B-49);
    - wall time counted only while in flight (L-48);
    - degrade in waves (L-46);
    - the `runaway.tool_calls` default;
    - enable derived from triggers (B-68), which removes a stored flag and needs a migration;
    - event keys on every node event (B-18);
    - the `WorkerPort.run(job, emit)` shape (L-42, today `workers/local.py:53` takes `executor`);
    - templates ending in `proposal` artifacts (B-88: pp, dm and the other human points).
  - `34:411` says the spec-gap decisions "feed steps 1 and 2", but those steps list only L-45 and B-63 of these.
- **Settled with no rewrite, or only a small one:**
  - Port names match the built registry (`definition/registry.py:54-80`).
  - L-20 already holds: no `monotonic` or `perf_counter` in `core/` or `definition/` on `tp4`.
  - The `wakes` table already exists (`ledger/migrations.py:49`, `control_door.py:163`), so B-63 is an extension.
  - All 31 templates set their own `runaway` block, so the new 2M default reaches only workflows that set none.
- **Fix:** add a step "2b. Spec-gap code" to the hardening plan listing the rows above, or put each into a named §25 packet. Fix SD §2.1's example (`SOLUTION-DESIGN.md:47`: 400000, 12, 600, 7200), which contradicts §17 (`:956`) and AD-16.

### S11. Ruling 27: the harness still caps each Background chat at $5, and DOC-CHANGES does not change it

- **Location:** DOC-CHANGES row 28; SD §7.4 (`:523`).
- **Evidence:** `qma-harness/src/qma/harness/launch.py:232` sets `max_budget_usd: float = 5.0`, and `launch.py:519` applies it to every Background chat. SD says the engine-host default is raised, but no row or packet changes the shipped default. An Opus agent node on a large chunk hits $5 (estimated) and ends with `error_max_budget_usd`.
- **Fix:** add to DOC-CHANGES row 28 and to the script-isolation packet's settings step: the engine-host default for `[budgets].max_budget_usd` is `None` (unbounded), the runaway guard does the job, and the doctor line names any cap he sets himself.

### S12. Rulings 78 and 90: the 2M-token runaway default is a fixed number that one chunked run exceeds

- **Location:** AD-16; SD §17 (`:956`).
- **Problem:** ruling 78 has 1M-context models take large chunks. Each chunk agent writes most of its context as `cache_write`, so two or three chunks pass 2,000,000. Ruling 90 says "no fixed cap, configuration is key".
- **Fix:** when a workflow sets no `runaway`, derive the default from its plan: `max(2M, 1.5 × Σ planned chunk tokens + per-agent allowance)`, recorded on `run_created`. Keep 2M as the floor.

### S13. Proposal actions are service calls written by a model behind a button he clicks

- **Location:** AD-17 *Human points are proposals*; L19 (`LIBRARY-REQUESTS.md:27`).
- **Problem:** a run writes `actions` (service name and arguments), and the UI renders them as buttons for a `user` principal. A model, or injected text it read, can choose an action and its arguments and word the card. His click then carries out what the model chose: publishing a different draft, enabling another trigger, or "start a paper pod". Paper is a real venue account (`money_path.py` docstring: "Paper is an account role on a real venue").
- **Fix:**
  1. Actions come from a closed enum per proposal type. Arguments may name only objects this run produced (its draft, challenger or lesson id).
  2. The UI writes the button label from the action, never from model text.
  3. The action list passes AD-36.
  4. "Start a paper pod" is not a proposal action. The proposal links to the pods screen, where he starts the pod himself.

---

## Notes

- **N1. The audit hook is a tripwire, not a boundary.** Python says audit hooks cannot be used to build a sandbox (PEP 578; `sys.addaudithook` documentation [remembered]). SD layer 5 should call it a tripwire.
- **N2. "Byte-identical to shipped" holds up on `tp4`.** The answer to "what if a shipped script imports a user-editable module": scripts run with `-I` (`nodes/script.py:178`), so neither the script's folder nor the cwd is on `sys.path`. No template edits `sys.path` (grep finds none). Only the runtime's site-packages can be imported, and the box grants it read-only. Two gaps remain:
  - The rule must say the **set** of `.py` files equals the manifest, so an added file counts as an edit.
  - The script runtime itself should be hash-checked at engine start. The user, or the copilot's shell, can write it, even though the box confines what it then does.
- **N3. Supporting files must ship in the right place.** 33 scripts import `jsonschema`, so the runtime needs `jsonschema`, `referencing`, `rpds-py` and `attrs`. `yt-dlp` belongs in the `qmx-worker` image.
- **N4. Keys in encoded forms pass redaction.** Base64, reversed or split keys get through, as DESIGN.md:232 already accepts. State it in AD-37.
- **N5. Agent nodes held until H2 wait on him.** Holding agent nodes `waiting(placement)` until he grants H2 is a ruling-77 cost. It is acceptable for security, and it is the strongest argument for granting the corrected H2 first.
- **N6. The runaway pause mostly does not wait.** It ends the run at the next occurrence, and only the "raise and resume" button involves him. That fits ruling 57. On a manual-only workflow, `limits.alert_after` must have a default.
- **N7. The tests ruling holds.** E39 uses haiku, roles route `test_only` to `claude/haiku` through the plan, OpenRouter is used only for provider proofs, and no Fable row exists. This matches the 2026-10-18 rulings.

---

## Verdicts on the open decisions

- **D. Grant HG3: yes, narrowed.** Grant:
  - **H2 first**, rewritten per C1: SDK `tools` list, with `PowerShell`, `Monitor` and `WebFetch` covered, and no hook-deny alternative;
  - **H18** close only, no `forget`;
  - **H19** and **H22**;
  - the five bug fixes.

  Defer H20 and H21 (H21 only with a size cap), drop H23 and H25 (Appendix G L1 replaces them), and take H24 as labelling only. None of these breaks DESIGN.md once S8's changes are made. As written, H18 `forget`, the H2 alternative and H23's write access do.
- **E. Edited workflows need Docker: accept the security rule, reject "wait" as the only behaviour.** Docker is off on this PC as of this review. Under ruling 83 most workflows become edited, so waiting would idle them often, against rulings 77 and 55. Adopt S4: auto-start Docker Desktop, then spill to `contabo`, then wait. Model-written code should prefer `contabo` anyway (S3).
- **F. Fail closed with no allow-list: accept the principle, not the text.** As written, the verb rule either lets `send_order` and `post_order` through or refuses all 31 templates. Even the intended reading refuses 3 shipped templates (t7, dm, ma). Accept F with three conditions:
  - C2's predicate, placed in `qma-core`;
  - prose matching limited to text a model or a tool can act on: prompts, node `notes`, parameter values and the `actions` of proposals. Comments, docstrings and READMEs are not scanned, because they run nothing and are never sent as a prompt; they get only the secret-shape check;
  - the whole pack passing E36 before the packet lands.

  An allow-list is still not needed.
- **0 (attached to E). Network templates stay `host_confined`.** Keep them `host_confined` while the bytes are shipped, and correct the count to five (DB, T4, rs1, rs4, T3). `internetClient` is all or nothing: the AppContainer cannot limit hosts. For these five, either accept open internet or move them to the container's egress allow-list. Recommend accepting it for shipped bytes, with the S1 rows proving that loopback and the tailnet stay closed.
