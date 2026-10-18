# 37c. Hermes Agent operations and practical guides, mapped onto QMX

Written 2026-10-18 by a research agent for the lead session. Sibling studies: `37a` (architecture and agent loop) and `37b` (extensibility). This one covers **operations**: cron, browser supervision, egress, monitoring, relay, storage and backup, platform shape, voice, the TUI and desktop app, and the best-practice guides.

**How this was read.** Every Hermes page below was read in the built-in browser (docs site, tab-scoped, no sign-in). Where the docs were thin, the source on GitHub was read the same way (`cron/AGENTS.md`, `cron/quota_hold.py`, `cron/incidents.py`, `gateway/restart_loop_guard.py`, `tools/browser_tool_eval_policy.py`, and the `cron/`, `gateway/` and `tools/` folder listings). No page needed a firecrawl fallback.

**Tags.** `[retrieved]` = read in a Hermes page or file named in the line. `[built]` = seen with `git grep` / `git show` on branch `engine/tp3`, package `qmx-agents/packages/qmx-engine`. `[designed]` = in the QMX spine or a methodology study. `[inferred]` = my reading, not stated anywhere.

**Overlap rule.** Where `37a` or `37b` already covers a topic (state DB recovery, CDP dialog policy, egress invariants, platform adapter contract, memory provider ABC), this study names the earlier proposal and adds only the operations angle.

**Short answer.** The QMX engine design already borrowed the big cron ideas (one occurrence at most, grace and one catch-up, fire leases, quota hold, monitor precheck, continuity, preflight). What QMX lacks is the **operator's side of operations**: knowing *why* something did not fire, failures grouped across runs, a health signal that works when the engine is dead, backup and update safety nets, and the UI patterns that make many agents and runs readable.

---

## 1. Cron internals (the scheduler)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/cron-internals, `cron/AGENTS.md`, `cron/quota_hold.py`, `cron/incidents.py` [retrieved].

- **Store and tick.** Jobs in `cron/jobs.json` (atomic temp-file then rename). A ticker runs every 60 s under a cross-process file lock; if the lock is taken, the tick returns 0 at once.
- **Every occurrence is accounted for.** `tick()` moves `next_run_at` past the due slot *before* dispatch and stamps `pending_slot` in the same save. A later scan that finds the stamp with a dead owner puts the slot back **once**. An executions ledger keyed by `scheduled_instant` blocks a second fire. Grace = half the period, clamped to 120 s to 2 h; past grace the backlog collapses into one `catch_up` run, or is skipped with a logged reason when `catch_up_missed: false`. "An occurrence is never dropped silently."
- **Fire-claim lease:** 300 s, refreshed every 60 s by a heartbeat thread; a lost claim is re-sampled once before it cancels a run.
- **Trigger is pluggable, execution is not.** `cron.provider` picks the built-in ticker or Chronos (a managed one-shot per job that calls the gateway back by webhook, so an idle host can scale to zero). A missing or broken provider falls back to the built-in ticker with a warning: "cron is never left without a trigger."
- **`last_status` is a closed set:** `ok`, `delivery_queued`, `error`, `delivery_failed`, `blocked_config`. "A consumer must never test `== "ok"` for 'the user got their result'." Delivery goes through a durable queue keyed by execution id; a send that died mid-way is marked `unknown` and never retried; the result is written back onto the run.
- **Timeouts.** Scripts: 3,600 s wall clock. Agent jobs: an **idle** budget (600 s with no tool call or token), so long but active jobs are never cut off; time asleep does not count on macOS and Linux.
- **Quota hold** (`cron/quota_hold.py`): when the provider says "retry after N s", the job is parked at the window end plus 60 s, and "any run that reaches the model clears the marker". The hold is anchored on the typed auth error, never on free text, "so an unrelated 'retry after' in an agent's output cannot park a job."
- **Incidents** (`cron/incidents.py`): failures are grouped by `(job_id, normalized error signature)`; durations are masked out of the signature. States `detected → alerted → resolved | closed`. A closed incident stays silent until the error text changes; repeats are withheld for `cron.failure_repeat_alert_hours`.
- **Failure routing:** `--failure-deliver local` or an ops channel keeps failure notices out of a busy results channel.
- **Recursion guard:** the cron, messaging and clarify toolsets are off inside a cron run. Cron runs pass `skip_memory=True`.
- **Stale-code yield.** A ticker whose checkout changed under it yields to a fresher process; `hermes cron status` then says "Gateway is running STALE code — its cron ticker yields every tick and fires NOTHING".
- **Headless ticks refuse, never spawn** (`cron/AGENTS.md`): a tick from an external scheduler skips agent jobs when no gateway owns the home, and stamps `last_fire_error`.
- Extras in `cron/AGENTS.md`: `context_from` (chain job A's last output into job B), `workdir` (run with that folder's `AGENTS.md`), `--interpreter` to pin a user venv for a Python script.

### What QMX has

- Spine AD-10 [designed]: triggers are rows; kinds `cron | interval | event | webhook | manual | after`; at most one fire per occurrence; lease with heartbeat; grace then one catch-up; `quota_hold_until`; `precheck` monitor ends a fire `silent`; `continuity` (Hermes style); preflight to `blocked_config`; pluggable trigger source; wakes table.
- Built [built]: `triggers/ticker.py`, `triggers/claims.py` (leases, `failure_streak`), `triggers/catchup.py` (`merged | record_only`), `triggers/quota.py` (header cites Hermes `quota_hold`), `triggers/preflight.py`, `ledger/migrations.py` (tables `triggers`, `fires`, `wakes`; `UNIQUE (trigger_id, occurrence_at)`), `settings.py` (`scheduler.tick` 60, `scheduler.grace` 900). Trigger `kind` is checked to `cron | interval | manual | after` only, so `event` and `webhook` are not built yet.
- Inbox [built]: `ledger/inbox_table.py` keys items by `UNIQUE (run_id, signature)`. The `triggers` table has an `incident_id` column; `triggers/rows.py` stores and loads it, and its docstring says "nothing reads" it, so no incident logic exists yet.

### Gap

1. **Repeats across runs.** An item is keyed per run. A trigger that fails the same way every morning makes a new item every morning. Hermes keys incidents per job across runs, with an ack that holds until the error changes. [built + inferred]
2. **Status words.** QMX has no rule that "passed" ≠ "the result reached him". Delivery outcomes are not a separate field. [inferred]
3. **Stale code.** Nothing tells him the engine is running old code after an update, or that its ticker yields. [inferred]
4. **Failure routing.** One `delivery` target per trigger; no separate failure target. Small, because QMX failures go to the inbox anyway.
5. `event` and `webhook` trigger kinds are designed but not built.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Trigger incidents:** give the stored but unread `incident_id` its logic. Group failures by `(trigger_id, signature)` with durations masked; states `open → acknowledged → resolved`. An acknowledged incident stays quiet until the signature changes; a passing run resolves it. The inbox item points at the incident, not at one run. | **Adopt** | engine (triggers, inbox) |
| **Closed status set with a delivery field**: `fire.status` keeps run outcome; add `delivery: none | queued | delivered | failed | unknown`. UI and digest never read "passed" as "delivered". | **Adopt** | engine, UI |
| **Stale-code check:** the engine stamps its code version at boot into a small state row; the CLI and Workflows screen say "engine is running old code, restart" when disk and process differ. | **Adopt** | engine, UI |
| **Fallback trigger source:** when a server or cloud trigger source is added later, keep the in-process ticker in core as the fallback that cannot be removed. | **Adopt** (rule now, code later) | engine |
| **Headless ticks refuse, never spawn:** an external tick (systemd timer, Task Scheduler) never starts an engine; it records "no engine owns this home". | **Adopt** | engine CLI |
| Idle-based agent timeout | **Already have** (AD-16 watchdog counts progress events, B-55). | — |
| `--failure-deliver` | **Skip.** The inbox already separates failures from results. | — |
| Interpreter pin per job | **Skip.** AD-24 picks the runtime by provenance; a user venv on the host breaks that rule. | — |

---

## 2. Script-only cron (no LLM)

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/guides/cron-script-only [retrieved].

- `no_agent=True`: "the script is the job". Zero tokens, same scheduler, same pause, list and run-now.
- **Output contract:** exit 0 with stdout → delivered verbatim; exit 0 and empty → silent tick; last line `{"wakeAgent": false}` → silent; non-zero exit or timeout → an error alert, "so a broken watchdog doesn't fail silently".
- Scripts must resolve inside `~/.hermes/scripts/`; traversal and symlink escapes are refused; shebangs are ignored on purpose ("keeping the interpreter set explicit and small reduces the surface the scheduler trusts"); scripts do not inherit provider credentials.
- The model chooses `no_agent` itself when "the message content is fully determined by the script".
- **The key operational rule:** "For critical system-health watchdogs that must fire even when the gateway is down, use OS-level cron with a plain curl to a Hermes webhook subscription (or any external alerting endpoint)."

### What QMX has

- Script-only workflows exist: `templates/gw-guard-watchdogs` is "Script-only: no model node, zero tokens", every 5 minutes [built].
- `monitor` node and trigger `precheck` end a fire `silent` on an unchanged hash (AD-10) [designed, built in `nodes/monitor.py`].
- Study 30 §5c: an outbound alive-ping to an off-server watcher for the server [designed].

### Gap

1. No written **output contract** for a script node used as the whole job: what "empty" means, and that a non-zero exit always reaches him.
2. The engine's own liveness: the GW README says "the engine watchdog that pushes 'kill-line watchdog down' when GW is late ... is engine work" [built], but a dead engine cannot report itself. Study 30's off-server ping is for the server, not for the PC engine.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Script output contract** for script-only workflows: empty output = `silent`; a typed `{"wake": false}` last line = `silent`; non-zero exit = failure into the ladder, never silent. Lint refuses a script-only workflow whose delivery is `silent` and that has no failure path. | **Adopt** | engine (nodes.script, lint) |
| **Dead-man switch outside the engine:** each engine instance pings an outside watcher every tick (the server one already planned in 30 §5c); a missing ping alerts by the phone route later. On the PC, a Windows Scheduled Task checks the engine's heartbeat row and writes a `black` item if it is stale. Never rely on the engine to report its own death. | **Adopt** | Contabo services, engine |
| Model picks "no agent" itself | **Adapt**: the copilot builder prefers a script-only draft when the output is fully fixed by data (a builder rule, not a runtime switch). | harness (builder skill) |

---

## 3. "Automate anything with cron" (the patterns guide)

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/guides/automate-with-cron [retrieved].

- Five patterns: website change monitor (script hashes the page, agent explains), weekly report, repo watcher, data pipeline (script collects, agent reasons), multi-skill chain.
- Rules: prompts must be **self-contained** ("Cron jobs run in fresh agent sessions with no memory of your current chat"); use `[SILENT]` "deliberately" and never ask the agent to explain the token; "Use scripts for data collection ... cheaper and more reliable than having the agent do the fetching itself"; "Test with `/cron run`" before waiting for the schedule; stagger jobs that share a minute.
- Bot Chat delivery: a job can deliver into an agent's own chat so the agent acts on it; it "costs a bot turn".

### What QMX has

- The same split is the engine's core idea: script and monitor nodes do the fetching, `llm`/`agent` nodes reason (AD-10, AD-27) [designed]. A run never sees chat history; `continuity` passes last outputs (AD-10).
- Templates exist for briefs and monitors (`db-desk-brief`, `dm-demo-monitor`) [built].

### Gap

Small. The builder (AD-22) has no explicit **self-contained brief** check, and there is no "run now" on an enabled trigger (a manual fire of the pinned version) named in the UI handoff.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Builder lint "self-contained brief":** a scheduled workflow's agent brief may not refer to "this chat", "above" or "what we discussed"; it must name its inputs. | **Adopt** | harness (builder skill), engine lint |
| **"Run now" on a trigger:** fires the pinned version once as a manual fire; it does not consume the next scheduled slot (Hermes: an off-tick fire "runs occurrence-free instead of consuming the next slot"). | **Adopt** | engine, UI |
| The five patterns as Library templates | **Adopt** where a QMX need exists (site monitor and data pipeline already match study 15/16 cards). | Library |
| Bot Chat delivery | **Skip.** QMX results land in the Library; nothing feeds a chat by default. | — |

---

## 4. Cron troubleshooting

### How Hermes does it

Source: https://hermes-agent.nousresearch.com/docs/guides/cron-troubleshooting [retrieved].

- Four buckets: timing, delivery, permissions, skill loading. Checks in order: job exists and is active; schedule parses; **is the ticker process running** ("A regular CLI chat session does not automatically fire cron jobs"); clock and time zone; delivery target; `[SILENT]` misuse; token scopes; skill names.
- Diagnostics: `hermes cron list` (state, `next_run`, `last_error`), `hermes cron run`, `hermes logs`, and in internals `hermes cron status` with the stale-code message.
- Desktop: the primary backend ticks every local profile's store, so a sleeping profile's jobs still fire.

### What QMX has

`service.explain(run_id)` explains a run [designed AD-15, built `service/explain.py`]. Nothing explains a **trigger that did not fire**. Fires carry `status` and `detail` (`claims.py`) [built].

### Gap

He cannot ask "why didn't my 9:00 workflow run?" and get one answer. The data exists (fires, preflight, quota hold, version enabled, ticker alive) but no single read joins it.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **`service.explain_trigger(trigger_id)`**, the "why didn't it fire" read: ticker heartbeat age, version enabled or not, next fire, last 10 fires with status and reason (`silent`, `merged`, `blocked_config`, `quota_hold until`, `skipped: record_only`), open incident. The copilot answers the question from it; the Workflows screen shows it. | **Adopt** | engine (service), UI, harness (copilot tool) |
| **`qmx engine doctor`** prints the same for every trigger plus store health. | **Adopt** | engine CLI |

---

## 5. Browser and the CDP supervisor

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/browser-supervisor, https://hermes-agent.nousresearch.com/docs/user-guide/features/browser, `tools/browser_tool_eval_policy.py`, `tools/` listing [retrieved].

`37b` §14 already covers the dialog queue, dialog policy and the trusted CDP capture seam. The operations points it did not cover:

- **Recent dialogs carry `closed_by`:** `agent`, `auto_policy`, `watchdog` (timeout hit) or `remote` (the backend closed it). So the trace says who closed a dialog.
- **Lifecycle:** reconnect with backoff (≤10 s), then give up after a fixed number of failures so a dead Chrome "never leaves a retrying thread behind"; a changed CDP URL means a fresh supervisor, "state is never reused across endpoints".
- **Frame tree is capped** at 30 entries and depth 2, with `truncated: true`, to bound snapshot size on ad-heavy pages.
- **Hybrid routing:** with a cloud browser configured, URLs that resolve to private or LAN ranges go to a local sidecar browser, so "the cloud provider never sees the private URL"; a redirect from a public URL onto a private one is still blocked.
- **Eval policy:** JavaScript sent to the page is pre-screened for private `http(s)://` literals, because a `fetch` to a private host never changes `location.href` (`browser_tool_eval_policy.py`).
- **Named sessions:** `session=<name>` gives each parallel agent its own browser and daemon, "so parallel subagents or simultaneous chats no longer clobber a single shared connection".
- **Real profile:** Hermes copies the active profile into a snapshot and runs the real browser binary on it; on Windows a running Chrome locks its cookie file, so the agent gets a fresh browser and a `real_profile_unavailable` reason. Turning the option off deletes the snapshot.
- Inactivity timeout and an orphan sweep close idle browsers.

### What QMX has

AD-33 Cua pack with a bounded manifest, deny-list, one native input per desktop, screenshot per action [designed]. Study 14 §3.5-3.8: one QMX Browser, a broker holding the only CDP connection, a tab per lease, take-over button, levels B0-B4 [designed]. Study 18 §3.1 on Windows profile copying [designed].

### Gap

1. The broker lease (study 14 §3.7) has no **lifecycle rules**: reconnect limit, no state reuse across endpoints, idle close, orphan sweep.
2. No **private-URL rule** for a browser that runs on a burst or server placement (a cloud browser must never be asked to open the tailnet or `localhost`).
3. Hermes's Windows finding confirms study 14 §3.6: copying his real profile while Chrome runs fails on Windows. QMX's separate "QMX Browser" profile is the right call.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Broker lifecycle:** reconnect with backoff, give up after N, never reuse a lease's state on a new endpoint, close leases idle past a TTL, sweep orphans at engine start (same sweep as AD-24's labelled containers). | **Adopt** | engine (cua pack, broker) |
| **Private-URL guard** for every non-PC browser: block private, tailnet and metadata ranges at navigate and in evaluated JS literals; block redirects onto them. | **Adopt** | engine (cua pack) |
| `closed_by` on every dialog in the trace, frame tree capped with `truncated`. | **Adopt** | engine (cua pack) |
| Named, isolated browser sessions per parallel lease (study 14 already says isolated leases may run in parallel). | **Already have** (designed) | — |
| Real-profile snapshot | **Skip** on Windows; keep the separate QMX Browser profile. | — |

---

## 6. Egress proxy

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/egress-internals, https://hermes-agent.nousresearch.com/docs/user-guide/egress/iron-proxy [retrieved].

`37b` §15 already proposes the Hermes invariant list as a test checklist. The operations points:

- **Fail closed by default:** `enforce_on_docker: true` refuses to start a sandbox when the proxy is enabled but down.
- **Re-setup keeps tokens:** re-running setup "cannot silently 401 running sandboxes"; rotation is an explicit flag. A config change stops the daemon and offers a restart, because the daemon holds config in memory.
- **Uncovered providers are named:** request-signing auth (SigV4 and similar) "cannot be covered" by a header swap, so status warns about it.
- **Default deny CIDRs** include loopback, link-local (cloud metadata `169.254.169.254`), RFC1918, IPv6 ULA and **CGNAT (`100.64.0.0/10`)**.
- **PID reuse defence:** a nonce file and the process start time are checked before a kill, so a recycled PID is never killed.
- **Scope note:** the proxy protects the sandbox only; host-side LLM calls use keys directly.

### What QMX has

AD-28 [designed]: the relay is the only key reader per host and injects keys; workers hold a run pass. AD-25: in `cli_inside` "the egress proxy is only a domain allow-list"; Contabo runs `qmx-egress` as a systemd unit.

### Gap

1. **Tailscale sits in CGNAT space** (`100.64.0.0/10`) [inferred from Tailscale's documented address range]. A Hermes-style default deny would cut a sandbox off from the relay on the tailnet; no deny at all would let a sandbox reach every tailnet host. The QMX egress design does not say which.
2. No written rule for what a sandbox does when `qmx-egress` is down.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Deny private ranges, CGNAT included, then allow exactly one tailnet address**: the relay named in the pass (`relay_url`). Metadata IPs are always denied. | **Adopt** | Contabo services (`qmx-egress`), engine (workers) |
| **Fail closed:** a container placement whose egress proxy is down goes `waiting(placement)`; never a run with open egress. | **Adopt** | engine (workers) |
| Re-setup never rotates passes or relay config silently; a config change restarts the proxy and says so. | **Adopt** | Contabo services |
| Kill by `(pid, start_time)`, never by PID alone (Hermes kanban uses the same rule for workers). | **Adopt** | engine (workers), harness |

---

## 7. Gateway monitoring

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/gateway-monitoring, https://hermes-agent.nousresearch.com/docs/user-guide/messaging, https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard, `gateway/restart_loop_guard.py` [retrieved].

- **Content-free by construction.** Exported over OTLP: gateway up, state, busy, active agents, background work; platform up and degraded; **scheduler heartbeat age, last-success age, overdue count, catch-up count**; cron execution lifecycle with a hashed job key. Never prompts, job names, destinations, raw errors or profile names.
- **Closed vocabularies:** error classes `auth_failed | rate_limited | timeout | network_error | dispatch_failed | interrupted | empty_response | invalid_config | unknown`; "an error class should map to an operator action, not to an exception subclass". Anything unlisted is coerced to `unknown`.
- **Missing-series detection:** "A process that has died cannot emit its own zero", so alert on both `up == 0` and `absent_over_time(up[5m])`.
- **Release validation, five forced cases:** cron success, cron failure, cron interrupted by a gateway stop (must recover to `unknown`), one platform down, gateway killed (missing series, then the same instance id returns).
- **Fail-open export:** a dead collector never blocks the gateway.
- **Liveness inside the process:** an event-loop watchdog probes every 30 s; after 3 missed probes it dumps all stacks, stamps `degraded` and exits with code 75 so the supervisor restarts it. Housekeeping re-stamps a state file every 60 s; older than 120 s while the process is alive → "Heartbeat stale", the "looks running but nothing is scheduled" case. Optional systemd `WatchdogSec`. `kill -USR2` dumps stacks without a restart.
- **Restart-loop breaker** (`restart_loop_guard.py`): boots are chained while gaps stay under 300 s; after 3, auto-resume of the interrupted session is skipped. "Any I/O failure fails OPEN, never wedging."
- **Dashboard resource banner:** low memory or disk, and "Your agent restarted unexpectedly, most likely because it ran out of memory", from a lifecycle ledger.

### What QMX has

- Study 30 §5 [designed]: one span shape, JSON logs to journald and Loki, Prometheus, metrics per area, off-server ping, alerts as inbox severities, node keeps its own stack.
- AD-16/17 [designed]: `black` for watchdog down or ledger corrupt. `watchdog.py` cancels stalled attempts and raises `black` on a ledger write error [built].
- `37a` §12 proposes a crash-loop counter per run.

### Gap

1. No **engine-level** health signals (ticker heartbeat age, last good tick, overdue triggers, catch-up count). Study 30 §5b lists "runs running, parked or waiting" but not the scheduler's own pulse.
2. No content-free rule for metrics and no closed error-class list for alerts.
3. No missing-series alert; no event-loop watchdog for the engine's asyncio loop; no restart-loop breaker for the engine process itself (37a's counter is per run).
4. No validation scenarios for the monitoring itself.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Engine health gauges**, content-free: `engine_up`, `scheduler_heartbeat_age_s`, `scheduler_last_success_age_s`, `triggers_overdue`, `catch_up_total`, runs by status, inbox open by severity, relay up per host. Alerts: `up == 0` **and** series absent. | **Adopt** | engine, Contabo services (Prometheus) |
| **Closed error-class set** shared by spans, incidents and alerts, each class mapped to an action (retry, rotate account, fix key, fix config). Same list feeds the failure classifier proposed in `37a` §8. | **Adopt** | engine |
| **Event-loop watchdog** in the engine host: probe the loop; on N misses dump stacks, write `degraded` with a reason, exit with a fixed code; systemd `Restart=on-failure` and `WatchdogSec` on Contabo, Task Scheduler restart on the PC. | **Adopt** | engine host, Contabo services |
| **Process restart-loop breaker:** 3 boots with gaps under 5 minutes → start in "safe mode" (ticker paused, no resumes) and raise one `black` item. Fails open. | **Adopt** | engine host |
| **Five forced validation cases** before the server goes live (run success, failure, interrupted, relay down, engine killed). | **Adopt** | Contabo services (runbook) |
| OTLP export to a vendor | **Skip.** Study 30 already picked Prometheus and Loki on the server. | — |

---

## 8. Relay (Hermes Relay connector)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/relay, the "Relay ↔ Connector Contract" page title and its contract file named there [retrieved; the contract body was not read].

- A **connector** service owns the platform bot tokens and sockets. The gateway **dials out** over one authenticated WebSocket, so it "never opens an inbound port" and works behind NAT.
- **Enrollment:** a single-use enrollment token is redeemed once for a per-gateway secret; enrollment refuses on managed installs, where the host provisions the secret.
- **Capability handshake:** the connector sends a descriptor (`supported_ops`, message length, markdown dialect, edit, thread, streaming); the gateway uses only what is advertised.
- **Buffered delivery:** when the gateway sleeps, the connector buffers inbound messages and replays them in order, "ack-gated, no loss or duplication"; an optional wake URL is poked when work arrives.
- Native buttons for approvals and clarify questions come back as authenticated responses from the clicking user.
- Explicit `enabled: false` wins over an injected URL.

### What QMX has

AD-28 [designed]: "relay" means the **model-key relay** (one per host, injects keys, takes run passes). The phone route (ruling 34) is later; `37b` §4 proposes the adapter shape for it.

### Gap

1. **Word clash:** Hermes "relay" = messaging connector; QMX "relay" = key relay. Docs that borrow from Hermes will mix them up. [inferred]
2. The PC sleeps; a phone route that targets the PC would lose messages. Hermes solves this with a connector that buffers and a gateway that dials out.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **When the phone route is built:** the bot token lives in a small connector on Contabo (always on); the PC engine dials out to it over the tailnet; the connector buffers inbox answers and replays them in order on reconnect. Approvals use native buttons and are bound to his user id. | **Adapt** (later, ruling 34) | Contabo services, engine (InboxPort route) |
| **Capability descriptor** at connect for any remote surface (phone connector, provider adapters of AD-30): use only advertised operations. | **Adopt** (rule) | engine, Contabo services |
| **Single-use enrollment token** for pairing a new placement (`qmx node pair`), redeemed once for a per-host secret. | **Adopt** | engine (placements), Contabo services |
| Keep the QMX word: call the Hermes idea "phone connector" in QMX docs. | **Adopt** | docs |

---

## 9. Database storage, migrations and backup

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/developer-guide/session-storage, https://hermes-agent.nousresearch.com/docs/developer-guide/state-db-recovery, https://hermes-agent.nousresearch.com/docs/user-guide/session-storage-recovery, https://hermes-agent.nousresearch.com/docs/reference/cli-commands (`hermes backup`, `hermes update --backup`) [retrieved].

`37a` §11-12 covers the single writer, durable admissions, the FTS detach rule and file quarantine. The operations points:

- **Migrations:** `schema_version` 31. Simple column adds are **declarative** (diff live columns against the schema text, add what is missing, idempotent); the numbered chain is only for data moves and index changes. Long backfills run in **2,000-row chunks**, each its own short write, resumable from a cursor in `state_meta`, "so a large store never holds the write lock for the whole table".
- **Write contention:** 1 s SQLite timeout, then an app-level retry with random jitter (20-150 ms, then 250 ms-1 s) inside a budget (20 s routine, 60 s transcript, 0.5 s for activity rows), `BEGIN IMMEDIATE`, a passive checkpoint every 50 writes. On a failed budget, the log names the process holding the lock.
- **Maintenance refuses while a writer is live:** optimize, vacuum and prune list the holding PIDs and refuse; `--dry-run` is never blocked; `--force` exists.
- **Backup:** `hermes backup` uses SQLite's backup API, "so it works correctly even when Hermes is running". Exit codes: **0** only when every file landed, **1** for a partial archive (kept, but older archives are not pruned), **2** when another backup is running. `--keep N` (default 3). It excludes `*-wal`, `*-shm`, regenerable model and runtime downloads, and **browser profile folders** ("Credential stores that must never enter an archive"). `--quick` snapshots only critical state.
- **Update safety:** `hermes update --backup` and the desktop updater take a snapshot (`state.db.pre-update-emergency-<ts>.bak`) before touching the store.
- **Recovery:** `hermes sessions recover --inspect-only` "never modifies the file"; the guide's "Do not" list: do not delete `-wal`/`-shm`, do not copy `state.db` alone, do not ask the agent to fix its own store.

### What QMX has

- Engine ledger [built]: forward-only steps in `ledger/migrations.py`; "A file whose version is newer than this code knows is refused, never downgraded"; SQLite version recorded at each writer open, floor 3.51.3; only the writer thread checkpoints (`store.py:276`).
- Backups [designed, study 30 §5d]: backup-API snapshots of every SQLite store, rclone to the server, bucket nightly, drills monthly.
- One writer per store (AD-23) [designed, built].

### Gap

1. No **pre-update snapshot** of `engine.sqlite`, `control.db` and the Library index before an engine or app update runs a migration.
2. No **backup exit-code contract** (partial vs complete), so a timer may report a partial archive as success. [inferred]
3. Backups do not yet name **exclusions** (the QMX Browser profile, model caches, `-wal`/`-shm`). The QMX Browser profile holds his logins.
4. No **inspect-only** recovery command and no "maintenance refuses while the engine runs" rule.
5. Future long backfills (Library index, memory rows) have no chunked, resumable pattern.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **Pre-update snapshot:** before any migration step runs, take a backup-API copy of the store next to it with a timestamp; keep the last 3. | **Adopt** | engine (ledger), harness (control.db), Library |
| **`qmx backup` exit codes 0 / 1 partial / 2 busy**, prune only after a complete backup, and the 36 h "missing backup" alert in 30 §5c reads the last **complete** one. | **Adopt** | Contabo services, engine CLI |
| **Backup exclusions list:** never archive the QMX Browser profile, the Claude plan login folder, `-wal`/`-shm`, model and runtime downloads. | **Adopt** | Contabo services, PC backup |
| **`qmx store inspect <file>`** read-only check, and maintenance (vacuum, reindex) refuses while the engine holds the file. | **Adopt** | engine CLI |
| **Chunked, resumable backfills** with a cursor in `meta`. | **Adopt** (when the first big backfill appears) | engine, Library |
| Declarative column reconcile | **Skip.** Forward-only numbered steps are simpler to review and already built. | — |
| Jittered retry budgets | **Adapt** for the few stores with more than one writer process (none in the engine; check `control.db` and apps). | harness |

---

## 10. Platform guides (Telegram and similar), shape only

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/messaging, https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram, https://hermes-agent.nousresearch.com/docs/developer-guide/adding-platform-adapters [retrieved].

`37b` §4 covers the adapter contract. The shape of a good platform guide, from the Telegram page:

- **Deny by default:** "Without [an allow-list], the gateway denies all users by default."
- **Home channel** (`/sethome`) is where scheduled results land.
- **Questions as buttons** with an "Other" choice and a timeout (default 3,600 s); on timeout the agent gets `timed_out` and adapts "rather than hanging"; if buttons fail, the same question is re-sent as a numbered list.
- **Status message edited in place** instead of a new bubble for each "Calling tool…".
- **Cold-boot backlog:** by default messages sent while the bot was off are dropped; `drop_pending_on_cold_boot: false` keeps them, for "hosts that turn off (a desktop shut down overnight)".
- Silence tokens are honoured only for internal wakes; a person's message that got a bare `[SILENT]` gets a short notice instead, "because a message that needed a reply must not vanish."
- Reactions as a cheap ack (👀 working, ✅/❌ done).

### What QMX has

Inbox as the one channel; phone later (ruling 34, AD-17) [designed]. Inbox items carry actions `retry | stronger model | skip node | open trace | stop | resume` [designed].

### Gap

None now. When the phone route comes, these are the behaviours to copy.

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| Phone route later: deny-by-default allow-list of one user id; inbox actions as buttons with a timeout and a numbered-text fallback; one status message edited in place per run; keep the backlog when the PC was asleep; an ack reaction. | **Adapt** (later) | Contabo services, UI |
| More than one platform | **Skip.** One phone route for one operator. | — |

---

## 11. Voice mode (brief; later nice-to-have, ruling 85)

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/voice-mode [retrieved].

- **Chained mode:** record → silence detection (two-stage, auto-stop after 3 s of silence) → Whisper → agent turn → TTS → recording restarts. Exit after 3 silent recordings.
- **Barge-in:** the mic stays live; speaking during generation interrupts the turn; speaking over playback cuts it.
- **Hallucination filter:** 26 known phantom phrases ("Thank you for watching") plus a regex.
- **Full-duplex mode on desktop:** a voice model talks; "it has no tools of its own. Whenever you ask for real work it delegates to Hermes", which answers with its normal model, tools, memory and approvals.

### What QMX has

BACKLOG B15, ruling 85: voice is much later.

### Proposal

**Skip now.** When B15 comes: copy the **delegate pattern** (voice model with no tools, all work through a normal copilot turn, so approvals and the money gate stay where they are) and the hallucination filter. Lands in **harness** and **UI**.

---

## 12. The TUI and desktop app: UI patterns

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/tui, https://hermes-agent.nousresearch.com/docs/user-guide/desktop, https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard [retrieved].

- **Live work dock** above the composer: sub-agents and background processes with task name, elapsed time and latest activity; expand to a roster; select one for its live transcript, details, **steer** or **stop**. "Steering acknowledges that guidance is queued for a checkpoint, not that the child has already read it."
- **Standing goal row** (`⊙ goal · 3/20 turns`) and a **queued messages** panel; a message typed while the agent works goes into a durable queue, shows as `[queued]` in every client attached to the session, and can be cancelled for every viewer.
- **Status line:** state words (`starting agent…`, `ready`, `thinking… / running…`, `interrupted`), elapsed per prompt and per session, a count of compressions, a count of background tasks, a visible **YOLO** warning badge.
- **Context meter** with a popover breaking tokens down by category (system prompt, tool definitions, skills, memory, rules, MCP, sub-agents, conversation); optional **cache hit rate** and **tokens per second**.
- **Failed turns name the failing layer** (provider, endpoint, stream, auth, billing, gateway, local runtime, disk) with matched actions: Retry (hidden when a retry would fail the same way), **Retry when the limit resets (HH:mm)** with a countdown and Cancel, Switch provider.
- **Session switcher** (only live sessions), tabs, pop-out windows (one chat, no sidebar, for a second monitor), a chat-first **Simple** interface mode.
- **Git review pane** with a **"Last turn"** scope: exactly what the agent changed in its latest turn.
- **Memory graph** of learned skills and memories over time, filter All / Used / Learned, nodes editable.
- **Cron pane:** jobs across all profiles; actions always go to the profile that owns the job. Dashboard cron list: name, prompt preview, schedule, state badge, target, last run, next run; Trigger now.
- **Logs page:** file, level, component filters, live tail. **Analytics:** tokens, cache hit, cost per day and per model.
- **Gateway badge** shows Running, Degraded (with reason) or Heartbeat stale; a **resource banner** shows only the most severe active warning.
- **Approvals:** once, session, always, deny; "Start with 'session'".
- **Multi-connection registry:** one list of every backend (local, LAN, server, SSH), each with a device name; same profile on two machines shows as `@profile-device`.

### What QMX has

UI-HANDOFF §1-§9 [designed]: sub-agents show start, end, result only (no live progress in the backend, §1 item 5); approvals with four decisions (§1 item 4); run timeline, inbox, Machines list, chunk progress, tool sub-timeline, compaction markers (§3, §9).

### Gap

The handoff lists *what data* to show but few *patterns* for reading many runs and agents at once. Missing: a live work dock, a queued-input panel, a context breakdown, failure cards that name the layer, "retry at reset time", "last turn" diff scope, a "why didn't it fire" panel, engine health badges, a resource banner.

### Proposal

See the paste-ready block in §14. Lands in **UI**, with backend reads named per row.

---

## 13. Best-practice guides: SOUL.md, skills, memory providers

### How Hermes does it

Sources: https://hermes-agent.nousresearch.com/docs/guides/use-soul-with-hermes, https://hermes-agent.nousresearch.com/docs/user-guide/which-file-does-what, https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills, https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers, https://hermes-agent.nousresearch.com/docs/guides/tips [retrieved].

**Persona (SOUL.md).**
- One global file, slot 1 of the system prompt, replaces the default identity. For tone, directness, what to avoid, how to handle uncertainty. **Not** for paths, commands, ports or project rules ("Those belong in AGENTS.md").
- Scanned for prompt injection; a hit logs a warning but still loads, because it is his own file and agent writes to it need approval. Edits apply at the next session.
- "A strong SOUL.md is stable, broadly applicable, specific in voice"; start with 4-8 lines and tune.
- **Which file does what:** SOUL = who the agent is (he writes it); USER = who he is (agent writes it); MEMORY = what the agent learned (agent writes it); AGENTS = what the project needs. Memory is a **frozen snapshot** per session to keep the prompt cache.

**Skills authoring.**
- Skill vs tool: a skill is instructions plus commands plus existing tools; a tool is for auth flows, exact logic, binary data or streaming.
- Fixed sections: When to Use, Quick Reference, Procedure, Pitfalls, Verification. Common path first ("Progressive Disclosure"). Put parsers in `scripts/`, "don't expect the LLM to write parsers inline every time."
- Conditional loading (`requires_tools`, `fallback_for_tools`), platform filter, declared env vars prompted securely at load.
- **Blueprints:** a skill can carry a schedule; installing it only *suggests* a job; "Suggestions never auto-create jobs; acceptance is always explicit"; dismissals latch.
- Hub skills pass a security scan (exfiltration, injection, destructive commands) with trust tiers.
- Tips: "Memory is for facts ... Skills are for procedures"; make a skill after a task of 5+ steps you will repeat; memory is bounded (~2,200 and ~1,375 chars); don't switch models mid-session (cache).

**Memory providers.**
- One external provider beside the built-in files; everything sent to it passes the secret scrub.
- **Hindsight** (vectorize-io, plugin catalog): long-term memory with a knowledge graph and entity resolution; tools `hindsight_retain`, `hindsight_recall`, `hindsight_reflect` ("cross-memory synthesis that no other provider offers"); modes cloud, local embedded PostgreSQL, or a local external server. Config: `bank_id`, `recall_budget low|mid|high`, `memory_mode hybrid|context|tools`, `auto_retain`, `auto_recall`, `retain_tags`, `recall_tags`. Per-profile config file; free when local.
- **Honcho** (brief): dialectic user modelling, peer cards and session summaries; five tools. He does not use it.
- Cron runs skip memory providers entirely (`cron/AGENTS.md`).

### What QMX has

- AD-18 [designed]: `MemoryPort`; rows are Library objects; frozen snapshot per run with line caps; recalled text only as a tool result or fenced block; one external provider (Hindsight named) may run beside the built-in, returning row ids only; cron and sub-agent contexts never write `home` or `operator`.
- `37b` §8-9 and §13 cover skill lint, conditional skills, the curator and the provider contract.
- **Persona:** no operator-editable identity file for copilots is designed. A search of the tracker finds only archived mentions, and none in `architecture/` [inferred from grep].

### Gap

1. No **persona file** he can edit (the Lego rule says it should be UI-editable).
2. Hindsight's settings are not mapped to QMX's rules. Its defaults (`auto_retain: true`, `memory_mode: hybrid`) would break AD-18 (writes outside `consolidate`, recalled text in context outside a fence).

### Proposal

| Idea | Verdict | Lands in |
| --- | --- | --- |
| **`persona` item:** one short operator-scope Library item, slot 1 of every copilot's system text, tone and defaults only; lint refuses paths, commands and project rules in it; edited in Settings; applies at the next chat. Workflow agents do not load it (their brief is their identity). | **Adopt** | harness, Library, UI |
| **"Which file does what" help card** in Settings: persona (he writes), operator preferences (memory rows, agent proposes), project rules (`AGENTS.md`/`CLAUDE.md`), workflow memory (runs write via `consolidate`). | **Adopt** | UI |
| **Hindsight binding for QMX:** one `bank_id` per scope (`qmx-workflow-<id>`, `qmx-home`, `qmx-operator`); `memory_mode: tools` (no auto-inject); `auto_retain: false`; retain called only by `consolidate` with row ids as tags; `recall_budget` from Settings; local embedded mode on Contabo (free); `reflect` used only inside `consolidate` to propose merges, never as evidence. | **Adopt** when an external provider is turned on | engine (memory), Contabo services |
| **Skill authoring guide** for the copilot builder: the five fixed sections, common path first, scripts for parsing, a "skill vs tool" test. (`37b` §8 has the lint; this is the human-readable guide.) | **Adopt** | Library (skill template), harness |
| Honcho | **Skip.** He does not use it. | — |

---

## 14. UI ideas for the UI session

Paste-ready for `UI-HANDOFF.md` as a new section. Each row names the backend read it needs; rows marked *(new backend)* depend on a proposal in this study.

```markdown
## 10. Operations patterns from Hermes (added 2026-10-18, study 37c)

Patterns from Hermes Agent's TUI, desktop app and dashboard that make many runs and agents readable. Sources in `research/methodology/37c-hermes-operations.md`.

1. **Live work dock** above the copilot composer: running sub-agents and workflow runs started from this chat, with name, elapsed time and latest activity; expand to a roster. Steer and Stop where the backend allows. Steer says "queued for the next checkpoint", not "read". Sub-agents still show start, end and result only until the harness emits progress (§1 item 5) [37c §12].
2. **Queued messages panel:** a message typed while the agent works shows as `queued` and can be cancelled before it starts [37c §12; harness queue].
3. **Context meter with breakdown:** % full, and a popover by category (system text, tools, skills, memory snapshot, MCP, conversation). Optional cache hit rate and tokens per second, off by default [37c §12; harness usage].
4. **Failure card names the layer:** provider, key, relay, stream, harness, engine, disk. Actions match the layer: Retry (hidden when it would fail the same way), **Retry when the limit resets at HH:mm** with a countdown and Cancel (nothing retries after he closes the window), Switch model [37c §12; error class set, 37c §7] *(new backend: closed error classes)*.
5. **"Why didn't it fire?" panel** on each trigger: ticker heartbeat age, version enabled, next fire, last 10 fires with status and reason (`silent`, `merged`, `blocked config`, `held until HH:mm`, `skipped`), open incident. The copilot answers the same question from the same read [37c §4] *(new backend: `service.explain_trigger`)*.
6. **Trigger list columns:** name, schedule in words plus the cron text, state badge, delivery, last fire (status + delivery outcome), next fire, Run now. "Passed" and "delivered" are separate badges [37c §1] *(new backend: delivery field)*.
7. **Incidents, not repeats:** one row per trigger and error signature with a count and first/last seen; Acknowledge keeps it quiet until the error changes; a passing run marks it resolved [37c §1] *(new backend: trigger incidents)*.
8. **Engine health badge** in the status bar and on the Machines list: Running, Degraded (with reason), Heartbeat stale ("looks running but nothing is scheduled"), Old code ("restart to load the update"), Safe mode (after a restart loop) [37c §1, §7] *(new backend: heartbeat row, code stamp)*.
9. **Resource banner:** only the most severe active warning (disk critical > memory critical > unexpected restart > disk low > memory low); dismissal lasts until the next engine boot [37c §7].
10. **"Last run" diff scope:** for a workflow or copilot that changed files or Library items, a view of exactly what its latest run or turn changed [37c §12; Library run branch].
11. **Pop-out a run or chat** into its own window without the sidebar, for a second monitor; live output streams into every window showing it [37c §12].
12. **Simple mode:** a chat-first layout switch that hides the status bar, rails and terminal; it changes what is shown, not what QMX can do [37c §12].
13. **Approvals:** keep the four decisions (§1 item 4). Add a visible badge whenever any auto-approve mode is on for a session, in the status bar and on session start [37c §12].
14. **Machines list:** each machine has a device name; the same agent or workflow on two machines shows as `name@machine` [37c §12].
15. **Settings, persona:** one short text box for the copilots' tone and defaults, with the "which file does what" help card beside it [37c §13] *(new backend: persona item)*.
16. **Logs page:** filter by component (engine, scheduler, relay, harness, apps) and level, live tail; analytics by day and by model (tokens, cache hit, cost estimate) [37c §12].
17. **Phone (later, ruling 34):** inbox actions as buttons with a timeout and a numbered-text fallback; one status message edited in place per run [37c §10].
```

---

## 15. Top 10 ideas to adopt (ranked by value per effort)

| # | Idea | Value | Effort | Lands in | Section |
| --- | --- | --- | --- | --- | --- |
| 1 | **Trigger incidents:** give the stored but unread `incident_id` its logic; group failures by trigger and masked signature across runs; acknowledge until the error changes. | High: stops a daily failure from making a daily item | S | engine, UI | 1 |
| 2 | **`explain_trigger` ("why didn't it fire")** read, used by the copilot, the Workflows screen and `qmx engine doctor`. | High: answers his most common scheduler question in one place | S | engine, UI, harness | 4 |
| 3 | **Dead-man switch outside the engine** (off-server ping on Contabo; a Scheduled Task on the PC that checks the heartbeat row). | High: a dead engine is otherwise silent | S | Contabo services, engine | 2, 7 |
| 4 | **Engine health gauges plus absent-series alerts** (heartbeat age, last good tick, overdue, catch-up count, `up`). | High: the scheduler's own pulse, content-free | S | engine, Contabo services | 7 |
| 5 | **Pre-update snapshot** of every store before a migration step, keep 3. | High: cheap insurance for every update | XS | engine, harness, Library | 9 |
| 6 | **Backup contract:** exit 0 / 1 partial / 2 busy, prune only after a complete one, exclusions (QMX Browser profile, plan login, `-wal`/`-shm`, caches). | Medium-high: no false "backup OK", no logins in archives | S | Contabo services | 9 |
| 7 | **Egress deny list with CGNAT, plus one allowed tailnet address (the pass's relay)**; fail closed when the proxy is down. | Medium-high: closes a tailnet-wide reach from sandboxes | S | Contabo services, engine | 6 |
| 8 | **Delivery outcome as its own field** next to run status; UI shows "passed" and "delivered" apart. | Medium: honest status words | XS | engine, UI | 1 |
| 9 | **Engine event-loop watchdog and process restart-loop breaker** (safe mode after 3 quick restarts). | Medium: no silent freezes, no crash loops | S | engine host | 7 |
| 10 | **Persona item and Hindsight binding rules** (tools-only recall, no auto-retain, one bank per scope). | Medium: Lego rule for tone; external memory kept inside AD-18 | S | harness, Library, engine | 13 |

Runners-up: stale-code badge (§1), script output contract and lint (§2), "Run now" that keeps the next slot (§3), broker lifecycle and private-URL guard (§5), single-use pairing token (§8), inspect-only store check (§9), self-contained-brief lint (§3).

## 16. What not to copy

- Twenty-plus chat platforms, Bot Chat delivery, and the Chronos scale-to-zero trigger: QMX has one operator and an always-on server.
- An interpreter pin per job: it breaks AD-24's provenance tiers.
- OTLP to a vendor collector: study 30 already chose Prometheus and Loki.
- Declarative column reconcile: forward-only numbered steps are built and easier to review.
- Copying his real Chrome profile on Windows: Hermes itself reports it fails while Chrome runs.
- Honcho.
