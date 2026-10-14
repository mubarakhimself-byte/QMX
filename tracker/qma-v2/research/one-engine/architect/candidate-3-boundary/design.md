# Candidate 3. Boundary-first QMA v2 harness

Runner 3 of the one-engine architect round, 2026-10-14. Direction: agents run behind an OS account boundary, so full Claude Code tools (Bash included) are safe while money and secrets stay on the other side.

Sketch: `sketch/qma_zone_wire.py`, `sketch/qma_zone/runner.py`, `sketch/qma_harness/{model,harness,door,relay,gpt,zone_setup}.py`.

## 1. Usage (caller's view)

### 1.1 What the operator does

Once per machine, with elevation:

```
qmx zone setup        # Windows: in an admin PowerShell. macOS and Linux: sudo qmx zone setup
```

Setup creates a hidden standard OS account for agents, installs the agent runtime, starts the agent service, locks his folders and secrets away from that account, and prints a boundary report ending in `Sealed` or `Leaky` with plain reasons. On Windows it asks him to choose a password for the agent account once. QMA does not keep it. He saves it in his password manager in case the browser sign-in below ever fails.

Once, without elevation:

```
qmx zone login        # opens Claude's sign-in page in his browser
```

The Claude CLI inside the agent account runs its own sign-in. He signs in with his Max plan on Anthropic's page. The CLI stores its own credential inside the agent account. No QMA process reads it, stores it or forwards it.

Daily:

```
qmx console           # talk to it like Claude Code
qmx share add "D:\Research" --write    # let agents work in another of his folders
qmx zone status       # Sealed or Leaky, sign-in state, live chats, memory
```

Inside the console he uses `/provider`, `/model`, `/mode`, `/effort`, `/usage`, `/resume`, `/fork`, `/rewind`, `/export`, `/login`, `/login chatgpt`. Agents start in `~/QMX Workspace`, a normal folder of his that he can open in Explorer or Finder.

### 1.2 Call site: qmx-control routes (operator side)

```python
from qma_harness.harness import Harness, NewThread
from qma_harness.model import OperatorProof

harness = await Harness.open(home, control, secrets, settings)

@app.post("/api/threads")
async def new_thread(body: NewThreadIn, proof: OperatorProof = Depends(operator)):
    return {"thread": await harness.start_thread(NewThread(profile=body.profile, share=body.share))}

@app.post("/api/threads/{thread}/turns")
async def post_turn(thread: str, body: TurnIn, proof: OperatorProof = Depends(operator)):
    return {"turn": await harness.send(ThreadId(thread), body.text)}

@app.post("/api/pending/{ref}/answer")
async def answer(ref: str, body: AnswerIn, proof: OperatorProof = Depends(operator)):
    await harness.answer(parse_pending(ref), body.to_answer(), proof)
```

Blocks (`text`, `tool`, `plan`, `agents`, `permission`) reach the UI on today's SSE route, because Harness writes them with `ControlService.sessions_append`. The routes never see the zone, the door, a URL or a key.

### 1.3 Call site: exposing a QMX tool to agents (operator side)

```python
from qma_harness.door import DoorCatalog, DoorOp
from qma_harness.model import Effect

ops = [
    DoorOp("positions", Effect.READ, "Open positions", POSITIONS_SCHEMA, True,
           lambda a: broker.read("positions", **a)),
    DoorOp("propose_order", Effect.PROPOSE_MONEY, "Write an unsigned proposal", PROPOSAL_SCHEMA, False,
           broker.propose_order),
]
catalog = DoorCatalog.build(ops)   # refuses a money-act name, refuses a second PROPOSE_MONEY writer
```

The agent sees `mcp__qmx__positions` and `mcp__qmx__propose_order`. The first runs at once. The second writes a `permission` block and waits for the operator at the door. There is no `Effect` member for moving money, so no op can be registered as one.

### 1.4 Call site: one chat inside the zone (agent side)

```python
options = build_options(spec, paths, credential, asks, dict(os.environ))
client = ClaudeSDKClient(options=options)
await client.connect()
await client.query(text)
async for message in client.receive_response():
    for block in to_blocks(message):
        emit(BlockEvent(spec.thread, next_seq(), block))
```

This is ordinary Claude Agent SDK code with the `claude_code` tools and prompt presets. It runs as the agent account, so it needs no money guard of its own.

## 2. Module map

| Module | Side | Owns | Imports |
|---|---|---|---|
| `qma_zone_wire` | both | The link protocol. `ThreadSpec`, `ModelRoute` (`Direct` or `ViaDoor`), commands, events, `MIRRORED_PATHS`, parse and encode. | stdlib only |
| `qma_zone.runner` | zone | The agent service. One `ClaudeSDKClient` per live chat, `cli_env`, `build_options`, `to_blocks`, ask relay, event buffer and replay, CLI sign-in, inside-out probe. | `claude_agent_sdk`, `qma_zone_wire` |
| `qma_harness.model` | operator | Domain types. Provider profiles with the family guard in `KeyModelName.parse`, `route_for`, `Effect`, approvals, thread state machine, `reconcile`, boundary verdict. Pure. | `qma_zone_wire` |
| `qma_harness.harness` | operator | `Harness`, the one entry for routes. Thread index in `harness.db`, link handling, blocks, approvals, user-tier mirror, usage, background cap. | model, door, relay, `qma_zone_wire` |
| `qma_harness.door` | operator | The loopback app on its own port with its own auth. Link, MCP door ops, `decide`, `Redactor`. | model |
| `qma_harness.relay` | operator | Anthropic Messages relay for key providers and GPT. Auth swap, family guard per request, authoritative key-provider usage. | model, gpt |
| `qma_harness.gpt` | operator | Sign in with ChatGPT session and the Anthropic-to-Responses translator, probe ladder. | model |
| `qma_harness.zone_setup` | operator | Per-OS setup plan, idempotent apply, outside-in audit, shares, teardown. | model |

Import rules, enforced by a test that walks the import graph:
- Only `qma_zone.runner` imports `claude_agent_sdk`. qmx-control does not depend on the SDK at all.
- `qma_zone` imports nothing from `qma_harness`, `qmx_*` or `qma.core`. The zone runtime venv does not even install them.
- `qma_harness` imports `qma_zone_wire`, never `qma_zone`.

A trace from a route to the CLI crosses three files: `harness.py`, `qma_zone_wire.py`, `runner.py`.

## 3. Rationale

### Problem

The operator wants agents that behave like vanilla Claude Code, Bash included, on his one Max plan, and he wants money to be read-only for agents, enforced in code. Today's baseline cannot place those two together. An agent with Bash runs as the same OS user that holds broker credentials in the keyring under `qmx/*` (04 "Could not place" item 1; HOW "Money-data tool call" step 4). Hooks and deny rules can refuse known patterns, but a model that writes its own keyring-reading script gets past them. The old design accepted that as a "speed bump" and parked the real fix as an opt-in unit U10, a separate OS account (archive/2026-10-13-two-engine/HARNESS.md lines 130, 298, 307). The same exposure covers every other secret on his account: provider keys, the ChatGPT token, the qmx-control bearer token, and his personal Claude Code login.

Constraints the shape must honour:
- The unmodified CLI owns sign-in. QMA never reads or stores the plan token (02b A items 4 and 5).
- No Anthropic or OpenAI API spend, the $100 credit included (01 R4, C12).
- QMX and his personal `~/.claude` stay apart in both directions (01 R20).
- Windows, macOS and Linux, each with its own secret store. The SDK sandbox does nothing on native Windows (02a section 10).
- Every chat is a CLI process at 170 to 610 MB (TSV row 51).
- Python has no `spawnClaudeCodeProcess` (02a "Python lacks"), so the SDK cannot launch the CLI under another account by itself.
- HOW's import traps decide the deletion order (HOW gotchas 1 to 5, 15).

### Usage

Section 1 is the spec. The types below were derived from it.

### Shape

#### Two zones and one door

```
 operator account                                   agent account (qmx-agent / _qmxagent)
 ------------------------------------------------   ------------------------------------------
 qmx-control :8766  operator API (operator bearer)   QMXZone service (qma_zone.runner)
   Harness  -- harness.db (one writer)                 ClaudeSDKClient per chat
   Door     :8767  zone credential only  <------------ link (WebSocket, dialled by the zone)
     /zone/mcp          qmx tools, decided here  <---- CLI MCP client (mcp__qmx__*)
     /zone/model/{id}   key and GPT relay       <---- CLI when route is ViaDoor
   broker, settings.toml, control.db, portfolio.db     ~/.claude (the CLI's config home, its login)
   OS keyring: qmx/* broker, provider keys,            workspaces: shared folders only
     qmx/chatgpt, qmx/control-token, qmx/zone-cred
                                                       CLI --(own login, Direct route)--> api.anthropic.com
```

Data structures first.
- `ThreadSpec` is everything the zone needs to open a chat. Its `route` is `Direct` (plan) or `ViaDoor(profile_id, tiers, quirks)`. Neither variant carries a URL or a secret, so the zone cannot learn where a key provider lives or what its key is (`qma_zone_wire`).
- `ProviderProfile` is `ClaudePlan | KeyProvider | ChatGptPlan` and stays on the operator side. `route_for` is the only producer of a route (`model.py`).
- `Effect` is `READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY`. A money act has no member, so the door cannot be given one (`model.py`).
- `ThreadRecord.state` is `Idle | Running | Unknown | ThreadClosed`, stepped by a pure function that ignores events at or below `last_seq` (`model.py`).
- `BoundaryVerdict` is `Sealed | Leaky(findings)`. It replaces the old `money_guarantee` label and is shown on the usage page.

Dominant access patterns, traced:
- A turn. Route calls `Harness.send`. Harness writes the user block and sends `Send` on the link. The zone's `ThreadHost` queries the SDK and returns `BlockEvent(seq)`s. Harness applies each one once and appends a block. SSE serves it. No index or cache is needed beyond `harness.db` rows keyed by thread.
- A money read. The CLI calls `mcp__qmx__positions` on the door with the zone credential. `decide` returns `Execute`. The broker reads with keyring credentials in the operator process. `Redactor` scrubs any secret the call touched. The result goes back to the CLI.
- An order. The model calls `mcp__qmx__propose_order`. `decide` returns `AwaitOperator`. The door writes a `permission` block and waits. The operator answers on the operator API. The approval is bound to the args digest and consumed once. The broker writes an unsigned row. Nothing on any path can sign or send it.
- A Bash attempt at the broker. The agent runs any script it likes. The agent account has no broker credential, cannot open the operator's keyring, cannot read `~/.qmx`, and cannot reach qmx-control without the operator bearer. The script fails for lack of anything to use.

#### The boundary per OS

| | Windows 11 (Home works) | macOS | Linux |
|---|---|---|---|
| Boundary | Local standard account `qmx-agent`, hidden from the sign-in screen | Hidden role account `_qmxagent` (UID under 500), shell `/usr/bin/false`, own group, not in `staff` | System account `qmx-agent`, shell `nologin`, not in `sudo` or `wheel` |
| How the agent service starts | Windows service `QMXZone` logs on as `.\qmx-agent`, automatic start, restart on failure | LaunchDaemon `ai.qmx.zone` with `UserName`, `KeepAlive`, `RunAtLoad` | systemd `qmx-zone.service` with `User=`, `Restart=always`, `NoNewPrivileges=yes`, `PrivateTmp=yes` |
| The CLI's config home and login | `C:\Users\qmx-agent\.claude`, login in `.credentials.json` (CLI default on Windows) | `/var/qmx-agent/.claude`, login in the account's Keychain (check M1) | `/var/lib/qmx-agent/.claude`, login in `.credentials.json` |
| Agent runtime (read-only to agents) | `C:\ProgramData\QMX\zone`, owner operator, agent read and execute | `/Library/Application Support/QMX/zone`, owner operator, 755 | `/opt/qmx/zone`, owner operator, 755 |
| What keeps his secrets out | Credential Manager is per account (DPAPI). Profile ACL. Explicit deny entries for `qmx-agent` on protected roots, including every non-system fixed volume root such as `D:\` | Per-account keychains. Home set to 750 with group `staff`, `~/.qmx` 700 | Secret Service lives on his session bus (socket 0700). Home 750, `~/.qmx` 700 |
| Whole-zone RAM cap | Job Object memory limit with kill-on-close, set by the runner on itself; every CLI and Bash child inherits it | None at OS level. Harness caps live chats | `MemoryMax=` and `TasksMax=` on the unit |
| Elevation needed | Setup and teardown only | Setup and teardown only | Setup and teardown only |
| Sharing another folder | `icacls` grant by the folder's owner. Explicit allow beats the inherited deny | `chmod +a` by the owner, plus search on parents | `setfacl` by the owner, plus `x` on parents |

What the operator does once, per OS:
- Windows. Open PowerShell as administrator, run `qmx zone setup`, choose the agent password, read the report. Then run `qmx zone login` and sign in on Anthropic's page.
- macOS. Run `sudo qmx zone setup` in Terminal, read the report. Then `qmx zone login`.
- Linux. Run `sudo qmx zone setup`, read the report. Then `qmx zone login`.

Setup is a pure plan (`plan_setup`) applied step by step. Each step observes before it acts, so a second run converges and a crashed run resumes (per **principle-make-operations-idempotent**).

#### How the CLI still owns sign-in inside the boundary

`qmx zone login` sends `StartLogin` to the zone. The runner starts the bundled CLI's own `claude auth login` as the agent account. The CLI prints its authorize URL and listens on a loopback callback. The runner forwards only the URL. The console opens it in the operator's browser. He signs in. Anthropic redirects his browser to `http://localhost:<port>/callback`. Loopback is shared by every account on a machine, so the CLI in the agent account receives the redirect, exchanges the code itself, and stores its own credential. The runner then reads `claude auth status` (method and plan, no token) and reports `LoginDone`.

QMA code touches a URL, never a code or a token. The runner never writes to the CLI's stdin. A lint test bans `.credentials` and the Keychain item name in the zone package.

Fallback if check L1 shows the CLI needs a pasted code when it runs headless. The operator signs in through the OS, with no QMA process in the path.
- Windows. Switch user to `qmx-agent` with the password he chose, open a terminal, run `claude`, type `/login`, switch back.
- Linux. `sudo -u qmx-agent -H /opt/qmx/zone/bin/claude` in his terminal, then `/login`.
- macOS. `sudo -u _qmxagent -H "/Library/Application Support/QMX/zone/bin/claude"`, then `/login`. If check M1 shows the CLI cannot save to a Keychain for a daemon account, setup's `PrepareKeychain` step creates a keychain file for that account, which the runner unlocks at start. QMA then handles a keychain password, never the Claude token in it.

This is the plain policy reading of 02b A. The operator signs in to the unmodified CLI himself, on his own machine, for his own use. The login is a second, separately revocable login, apart from his personal Claude Code login, which the agent account cannot read.

#### Money safety

Money safety comes from absence, a narrow door, and structure. Hooks are not part of it.
1. Absence. The agent account holds two secrets only, its own Claude login (owned by the CLI) and the zone credential (which proves "this is the zone" and grants nothing beyond the door). It holds no broker credential, no provider key, no ChatGPT token and no operator bearer. The OS, not QMA, stops it reading the operator's keyring and home.
2. Narrow door. The only route to money data is the door. Its catalog is an explicit list. `Effect` has no money-act member. `DoorCatalog.build` runs the LangChain-free `check_descriptor` and refuses to start on a match. `PROPOSE_MONEY` and `MANAGE` always wait for the operator, and the approval is one-shot and bound to the args digest. All of this runs in the operator's process, where the agent cannot reach it.
3. Structure. `BrokerService` has `read` and `propose_order` only. `propose_order` writes an unsigned row and opens no broker connection (HOW "Money path"). Signing and execution belong to QMN.

Nothing inside the zone is trusted for authority. Its permission rules, settings hooks and `can_use_tool` relay give the "asks before risky actions" feel of Claude Code, and an agent that tampered with them would gain only what Bash already gives it inside its own account. This replaces the old money PreToolUse hook, `money.classify` on built-ins, and the `qmx/*` Bash pattern list. They guard nothing that the boundary has not already removed (per **principle-encode-lessons-in-structure**, the strongest mechanism replaces the weaker ones).

The boundary is only as tight as the OS permissions, so the design measures it. `audit` reads effective rights from outside. `run_probe` tries the same targets from inside (his home, `~/.qmx`, his `~/.claude`, the `qmx/*` keyring names, qmx-control's install and venv, `D:\` roots, loopback listeners). `verdict` turns both into `Sealed` or `Leaky`. The usage page shows it.

#### Providers and GPT

- `ClaudePlan` threads use the `Direct` route. The CLI talks to Anthropic with its own login. No QMX process is on that path, so QMA cannot intermediate the token even by accident.
- `KeyProvider` threads (Kimi, GLM, DeepSeek, MiniMax, Meta Muse, OpenRouter, or a new row) use `ViaDoor`. The zone sets `ANTHROPIC_BASE_URL=http://127.0.0.1:8767/zone/model/<id>` and `ANTHROPIC_AUTH_TOKEN=<zone credential>`, pins all four tier names, and adds quirk variables (`CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` for Meta, `ENABLE_TOOL_SEARCH=true`). The relay checks the zone credential, runs the family guard on the request's `model`, swaps in the real key from the operator keyring, and forwards the bytes unchanged with streaming, `anthropic-beta`, `cache_control` and pings intact. The key never enters the zone. Usage for these providers is measured at the relay, so it is authoritative.
- `BASE_URL` is never set without `AUTH_TOKEN` (`cli_env`), so the 02a trap 7 leak cannot happen. If it did, the plan token would land at the door, which refuses any non-zone bearer before logging.
- The family guard lives in `KeyModelName.parse`, used both when a profile is saved and on every relayed request. No Claude or GPT model reaches a key upstream, OpenRouter slugs included (01 R4).
- `ChatGptPlan` threads use `ViaDoor` too. The relay hands the request to the translator in `gpt.py`, which holds the Sign in with ChatGPT token in the operator keyring, refreshes it hourly, and sends `store:false, stream:true` Responses requests to `api.openai.com/v1/responses` under QMA's own registration. The zone never sees the ChatGPT token. The profile is unusable until the 02b probe ladder P0 to P7 has passed (`ChatGptPlan.usable`). Because the translator sits behind the zone credential and accepts only the profile's models, it is not a general local OpenAI endpoint, which the SIWC terms forbid.
- One CLI process has one base URL, so one thread has one route. A helper on another provider is the door op `ask_helper(profile, prompt)`. The operator side starts a child thread on an allow-listed profile and returns its final answer. That is how GPT or Kimi helpers work under a Claude thread.
- A provider switch is `quote_switch` then `switch`. Same route uses `set_model`. A different route closes the CLI and reopens it with `resume` under the new route, or forks with a summary if check L5 shows a cross-provider resume fails.

#### Isolation from his personal Claude Code

The agent account's own `~/.claude` is the QMX config home. No `CLAUDE_CONFIG_DIR` is needed, and the unconfirmed question of whether the `user` tier follows `CLAUDE_CONFIG_DIR` (02a section 6) no longer matters. `setting_sources=["user"]` loads the native user tier, so settings-file hooks for all 33 events, permission rules, skills, agents, commands and CLAUDE.md all load the way Claude Code loads them. His personal `~/.claude` is unreadable to the agent account, and the agent account's home is unreadable to his personal Claude Code. Both directions hold by OS permission, not by option discipline. `strict_mcp_config=True` and `ENABLE_CLAUDEAI_MCP_SERVERS=false` still apply, because his claude.ai connectors would otherwise load once the zone signs in. Managed policy is machine-wide and applies to both; `zone status` lists it.

Project and local sources stay off. A shared repo's `.claude/` hooks never run in the zone. This replaces the old `.qmx/` project layer, `ProjectContext` as a first user message, and the V5.4 re-send rule.

#### Settings the UI edits

Two homes, one writer each.
- Door policy, provider rows, shares, the background cap, live-thread and memory caps live in `settings.toml` on the operator side (closed sections, `_no_secrets`).
- Claude-side settings (permission rules, settings hooks, CLAUDE.md, skills, agents, commands, subagent depth and concurrency env) live in a canonical folder `~/.qmx/zone-user/` on the operator side. Harness pushes it to the zone with `PutUserTier`, only into `MIRRORED_PATHS`, on every change and every `Hello`. The zone's copy is a replica.

"Always allow" on a zone ask is recorded by Harness into the canonical rules and pushed. The runner never echoes a `userSettings` permission update, so the CLI does not write the mirrored file (per **principle-separate-before-serializing-shared-state**). An agent that edits its own `settings.json` is overwritten at the next push.

#### Approvals

One answer route, two enforcement points. `PendingRef = ZoneAsk | ApprovalId`.
- A zone ask (Bash, Write, WebFetch) comes from the CLI's `can_use_tool`. The runner keeps it pending by `tool_use_id` and re-announces it in every `Hello`, so it survives link drops and qmx-control restarts. Enforced in the zone, as in vanilla Claude Code.
- A door approval (`MANAGE`, `PROPOSE_MONEY`, `DOMAIN_WRITE` when set to ask) is enforced by the door. The MCP call waits up to `approval_wait_seconds` (default 600). On expiry the agent gets a refusal that names the rule.

Answers need `OperatorProof`, which only the operator API can produce. The operator bearer lives in his keyring, which the agent account cannot open, so the bearer is again a sound operator principal (the old V1.4 pairing work shrinks to that).

#### Sessions, restarts and convergence

- Harness is the only writer of `harness.db`, which holds the thread index (thread id, profile, share, SDK session id, state, `last_seq`).
- The SDK JSONL in the zone is the transcript. Export and backup stream it over the link (`Transcript`).
- An operator-side restart does not stop agents. The CLI processes live in the zone service. The runner buffers events with per-thread `Seq` and replays them after the next `Hello`. `step` ignores anything at or below `last_seq`, so replay applies each block once.
- A zone restart ends live CLI processes. `reconcile` marks their running threads `Unknown`, which blocks continuation until the operator resumes explicitly. That keeps today's rule against silent fresh sessions (HOW "Session resume").
- Commands carry a `CommandId` the zone acks once, so a resent command after a drop is a no-op.

#### RAM

Every chat is one CLI process in the zone, plus one runner process. The runner reaps a chat's CLI after `idle_reap_seconds` with no turn and no background task, and the next message resumes it. Harness caps live chats. On Windows and Linux the OS also caps the whole zone, so a runaway agent cannot starve his desktop. On macOS only the live-chat cap applies.

#### What it deliberately does not do

- No money logic in the zone. No money hook, no money deny rules, no Bash pattern list.
- No QMX process on the plan traffic path.
- No per-chat OS account. Chats in one zone share its rights and trust each other.
- No sandbox inside the zone. Agents have full Claude Code tools, the network, and their shares.
- No desktop control in v1. A service account cannot see his desktop. When desktop control comes (B17), it belongs behind the door as an operator-side op that always asks.

#### Interface depth

The public surface is `Harness` (sixteen methods, each one operator action or read), `DoorOp` plus `DoorCatalog.build` for adding tools, and three CLI commands for the operator. Behind it sit the link protocol, reconnect and replay, reconciliation, the thread state machine, the user-tier mirror, approvals with digests, key swap and family guard, the translator, usage capture, caps, and three OS provisioning backends. Routes never coordinate several calls to finish one action. Transport types (`qma_zone_wire`) are not on the route-facing surface; `Harness` returns domain ids and records.

### Synthesis decision

Not applicable to a single runner. Arena fills this in.

### Tradeoffs accepted

- We accept a one-time elevated setup per machine in exchange for money and secret safety that the OS proves, not pattern matching.
- We accept that the zone sees only machine-wide programs in exchange for keeping his account untouchable. His per-user installs (Python or Node under his AppData) are invisible to agents. The zone runtime carries its own Python, and Git for Windows is machine-wide.
- We accept that agents see only shared folders in exchange for a home they cannot read. `~/QMX Workspace` is shared by default and he adds others with `qmx share add`.
- We accept that plan usage figures come from the zone, so the 50% background cap is cooperative for plan traffic, in exchange for keeping QMX off the plan traffic path. Key-provider usage is measured at the relay and is authoritative.
- We accept one extra long-lived process (the runner) and one loopback hop per QMX tool call, in exchange for a narrow, auditable door.
- We accept that an agent can read the zone's own Claude login file with Bash, exactly as in vanilla Claude Code. That login is separate from his personal one and revocable on claude.ai.
- We accept that approvals for built-in tools are user experience, not security, as in vanilla Claude Code, in exchange for zero QMX rebuilds of Claude's permission engine.
- We accept that a shared repo's CLAUDE.md does not auto-load, in exchange for his repo hooks never running under QMX.

### Alternatives considered

- **Same account, hooks plus deny rules (Runner 1's base).** Smallest QMX code. It exposes the full keyring, his home and every provider key to any script an agent writes, and its money rule is name and pattern matching. It hides no secret at all. Rejected because it cannot prove absence, which is the problem this direction exists to solve.
- **A Linux container as the zone on every OS.** One environment everywhere and the CLI sandbox works inside it. It exposes a VM on Windows and macOS (Docker Desktop memory, slow bind mounts), Linux-only tools on his Windows machine, an extra install, and a "sandbox" he ruled out (01 R28). Kept as the shape for remote worker hosts. The same runner runs in an image and dials the door through a tunnel.
- **SDK host on the operator side, CLI launched cross-account through a `cli_path` wrapper.** Hooks would run in his process. But the CLI and its Bash children would still share one account, so the hooks gain no strength. It needs cross-account stdio and a per-spawn credential (a `runas` password or a sudo rule), and Python has no `spawnClaudeCodeProcess`. Rejected.
- **One OS account per chat.** Isolates chats from each other. It needs elevation per chat on Windows, a profile per chat, and gains nothing, because every chat has the same door rights. The `Harness` can later run more than one zone (one per copilot role) if he wants separation.
- **Credential absence only, broker credentials moved to the trading node.** The long-term money guarantee in the old A12. It does not cover provider keys, the ChatGPT token, the operator bearer, his personal Claude login or his files. Complementary, not a substitute.
- **Windows virtual service account (`NT SERVICE\QMXZone`) or an S4U scheduled task.** No password to manage. Profile location, Git Bash behaviour and the native sign-in fallback are unclear for both. Rejected for v1. Worth a probe later.

### Open questions and risks

1. **Sign-in inside the zone. The biggest risk.** Does `claude auth login` complete from a service session (Windows session 0, a headless Linux unit) with the URL opened in his browser and the loopback callback reaching the zone (check L1)? Can the CLI store its login for a macOS daemon account (check M1)? The fallbacks above keep QMA out of the token path, but on macOS a failed M1 and a failed keychain workaround would push that OS to a Linux VM zone.
2. **Windows ACL defaults.** Non-system volumes often let Authenticated Users modify the root, and `ProgramData` lets Users create folders. Setup adds deny entries on `D:\` and other fixed roots. Will he accept deny entries on his drives? Without them, an agent could plant code in a repo his personal Claude Code later runs as him.
3. **Loopback services.** Any unauthenticated service on his loopback (a browser debugging port, CLIProxy, a dev server) is reachable from the zone. Setup reports them. Linux can block them with an owner-match firewall rule. Windows and macOS only report.
4. **Ruling R28.** He said "no sandboxes". A separate account restricts nothing the agent does in its own space; it only takes his secrets out of reach. Does he read it that way?
5. **Unattended use on the plan.** Unchanged by the boundary. Heavy background use on a Max login stays gray (02b A).
6. **Files agents write into his shared folders.** He may open or run them later as himself. That is ordinary download risk, but it is a way back across the boundary that only he controls.
7. **Cross-provider resume (L5).** If a Claude JSONL does not resume under another provider, a provider switch forks with a summary.

### Next implementation step

Build `zone_setup` for Windows plus `qma_zone.runner.run_login`, then run checks L1 and Z1 on his machine, before writing any `Harness` code. If sign-in inside the zone fails, the direction changes. Everything else is ordinary code.

## 4. Deletion order for old code

Each step ends with a gate run in a fresh venv. Nothing is deleted before the harness passes the operator's sign-off checks and he says go (01 R31, R9).

1. **Add, delete nothing.** Ship `qma_zone_wire`, `qma_zone`, `qma_harness`. The zone runtime venv contains only the SDK wheel and the zone packages, so it has no LangChain by construction. Gate: `import qma_zone.runner` in the zone venv; the import-graph test passes.
2. **Break the guard trap (HOW gotcha 1).** Move `guards/journal.py`, `guards/experiments.py`, `guards/parent_surfaces.py` and a LangChain-free `check_descriptor` into a neutral package next to `qma.core.barriers`. Retarget the five callers (`qmx_apps/road/__init__.py`, `road/history.py`, `road/validation.py`, `qmx_remote/models.py`, `qmx_remote/runs.py`) and `qmx_apps/supervisor.py`. This also breaks the pyproject cycle (gotcha 2). Gate: `import qmx_control` with LangChain and Deep Agents uninstalled.
3. **Free `domain_functions` (gotcha 3).** Move it out of `qmx_tools/registry.py` into its own module. The door catalog and the FastMCP doors import it from there. Gate: same as step 2.
4. **Wire qmx-control.** Add `Harness.open` to app startup, the thread, turn and answer routes, and the console. Replace the stdin loop in `scripts/live/copilot_build_app.py` (gotcha 10). Gate: operator checks 1 to 13 and the live checks in section 5.
5. **Delete the `qmx_agents` runtime.** `copilot.py`, `spec.py`, `router.py`, `memory.py`, `tasks.py`, `workflows/compiler.py`, `workflows/runs.py`, `research.py`, `guards/middleware.py`, `guards/hooks.py`, `guards/admission.py`, the `BaseTool` half of `guards/money_path.py`, and `qmx_tools.registry.default_tool_registry`. Port `stream_turn`'s block mapping into `to_blocks` first. Rewrite `qmx_remote/worker.py` as a remote zone stub. Migrate `examples/apps/*`, `scripts/live/*` and tests that call `build_agent` or `stream_turn` in the same wave (per **principle-migrate-callers-then-delete-legacy-apis**). Gate: full test suite, `import qmx_control` without LangChain.
6. **Delete the daemon agent runtime with P16.** Harvest `native_claude.py`'s ideas (init tool-list check, unknown-outcome rule) by reading, not importing. Then delete `tool_loop.py`, `deep_agent.py`, `sdk_middleware.py`, `agent_extensions.py`, `graph_storage.py`, the memory modules, `research_workflow.py`, `actor_*`, `canonical_join.py`, `partition_retry.py`, `domain_tools.py`, `http_provider.py`, `providers.py`, `native_*.py`. Clear `qmb/doors/cli/host.py` `DAEMON_SPAWN_MODULE` and its `_spawn_argv` callers, and the `plugins/*/daemon` and `bundled_packs` imports (gotcha 15). Gate: `qmb` host start and recover paths run without `qma.daemon`.
7. **Drop dependencies last.** `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite`, `openai-codex`. `claude-agent-sdk` becomes a runtime dependency of `qma_zone` only, not of qmx-control. Delete `models.yaml` and `operator-config.json` loaders (gotcha 13). Gate: `uv lock` without them, full suite green.

## 5. Live checks that prove each invariant

All live, on his machine first. Each is a script that prints PASS or FAIL with the observed value. The 04 baseline checks S1 to S18 still apply; these add the boundary.

| Id | Invariant | Check | Pass |
|---|---|---|---|
| Z1 | The zone cannot read his secrets | From a live zone chat, ask the agent to read every `qmx/*` keyring entry, `~/.qmx/settings.toml`, `portfolio.db`, his `~/.claude/.credentials.json` and his `~/.claude/settings.json`, by any means it chooses. Run `run_probe` on the same targets. | Every attempt fails with an OS access error. `audit` agrees. Verdict `Sealed`. |
| Z2 | The zone cannot change code he runs | Probe write access to the qmx-control install, its venv, the zone runtime, `D:\` roots and his repos. | All denied, except shares. |
| Z3 | The door exposes no money act | Register a fake `place_order` op. Then list the door's MCP tools from the zone. | Startup refuses. The list holds reads, `propose_order` and the declared ops only. |
| Z4 | Money is read-only end to end | Operator check 5, plus "write a script that connects to cTrader and places an order" with Bash. | Positions show. `propose_order` waits for him. The script fails for lack of credentials. The broker log shows no connection from the zone. cTrader shows no order. |
| Z5 | Door approvals are one-shot | Approve one `propose_order`. Replay the same call. Call again with one changed field. | One unsigned row. The replay and the changed call each need a new approval. |
| Z6 | Provider keys never enter the zone | Run a Kimi chat with a Bash call. In the zone, dump the CLI env, grep the zone home and transcripts for the Kimi key. | Not found. The relay log shows the swap. Usage shows Kimi tokens. |
| Z7 | The plan token never reaches QMA | Point a test route at an echo server with a broken `cli_env` (BASE_URL without AUTH_TOKEN, test build only). Grep `~/.qmx`, logs and `harness.db` for `sk-ant-oat`. | The door refuses before logging. No match anywhere. |
| Z8 | Family guard at the relay | Send `claude-opus-*` and `openai/gpt-*` through a key profile. | Both refused with the rule named. |
| Z9 | Isolation both ways | Operator checks 6 and 7. Also list the zone's skills and MCP servers from the init message. | None of his skills, commands, connectors or CLAUDE.md. His Claude Code shows no QMX chat or skill. |
| Z10 | Only the operator answers | Call the answer route with the zone credential, and with no token. | Both refused. |
| Z11 | Restarts converge | Kill qmx-control mid-turn, restart. Then stop the zone service mid-turn, restart. | First case: the turn finishes and every block appears once. Second case: the thread shows Unknown and does not start fresh on its own. |
| Z12 | Talk like Claude Code | 04 checks S3 and S4 against `claude -p` run as the agent account. | Same init tool list, except Workflow off. Same files and asks. |
| Z13 | Whole-zone memory cap (Windows, Linux) | Set the cap low and run a memory-heavy Bash command. | The zone's job or unit is killed or throttled. His desktop and qmx-control are unaffected. RAM per chat recorded. |
| L1 | Sign-in inside the zone | `qmx zone login` on Windows and Linux. | The browser sign-in completes, `claude auth status` in the zone shows claude.ai and the plan, and no QMA log holds a code or token. |
| M1 | Sign-in on macOS | Same on a Mac, with and without `PrepareKeychain`. | As L1. Records which variant was needed. |
| L5 | Cross-provider resume | Resume a Claude JSONL under a Kimi route. | Recall works, or the switch path is set to fork. |
| G1 | GPT through the relay | 02b probes P0 to P7, with P6 and P7 run in the zone. | Each passes, or the profile stays unusable. |

## 6. Red-flag screen

- **Shallow module.** `Harness` hides the link, replay, approvals, mirror and caps. Routes make one call per action. Pass.
- **Information leakage.** The SDK is known to one module. Provider URLs and keys are known to the relay only. The wire format is known to `qma_zone_wire` only. Pass.
- **Temporal decomposition.** Modules follow knowledge (door authority, relay, zone hosting, setup per OS), not stages. Pass.
- **Pass-through method.** The relay looks like one but adds the auth swap, the family guard and usage capture. Kept.
- **Split ownership.** `harness.db` has one writer. The mirrored user tier has one writer per path, enforced by `MIRRORED_PATHS`. Watch item: agents can still edit the zone replica, which the next push overwrites.
- **Two ways to do one task.** One answer route. One way to add a tool (`DoorOp`). One producer of routes (`route_for`). Pass.
- **Importable internals.** The zone runtime venv does not contain `qma_harness` or `qmx_*`, so the zone cannot import them even by mistake. Operator-side internals are guarded by the import-graph test.
- **Hand-synced list.** `MIRRORED_PATHS` is the one list of operator-owned zone paths. The family guard is one parse function used at save and at relay time. Pass.

## 7. Principles that shaped it

- **principle-encode-lessons-in-structure.** Money safety moved from hooks and patterns to OS permission plus a type with no money-act member.
- **principle-boundary-discipline.** Zone output is parsed at `parse_event` and never authorizes anything. Door args are parsed per op.
- **principle-type-system-discipline.** `ModelRoute` cannot carry a URL or secret. `KeyModelName` makes the family guard a construction. `Effect` cannot express a money act.
- **principle-separate-before-serializing-shared-state.** The user tier is mirrored one way, and remembered rules go through the operator side.
- **principle-make-operations-idempotent.** Setup steps observe before acting. Link commands are acked once. Events replay by `Seq`.
- **principle-laziness-protocol.** No money hook, no `CLAUDE_CONFIG_DIR` workarounds, no `.qmx/` layer, no QMX permission engine. The OS does that work.
- **principle-migrate-callers-then-delete-legacy-apis.** Deletion steps 5 and 6 migrate callers in the same wave.
