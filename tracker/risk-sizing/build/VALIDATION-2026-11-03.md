# Validation of the last four node slices, 2026-11-03

Checked against the stack tip `build/us-c13` at d02af358 by the planner and two read-only Opus checkers. Every claim below was read in code at that tip. The edits are in `plan-parts/61-phase-5b.md` and `plan-parts/62-phase-5c.md`, reassembled into `UNIT-PLAN.md` (check-plan: 80 PR sections, 0 problems).

## The finding that changes all four

The new trading node cannot bind a real cTrader account. `from_environment` opens the node with no venues (`qmn/src/qmn/app/server.py:204`), and `bind`, `sign_in_begin`, `sign_in_code` and `self_test` all answer `not_set_up` (`qmn/src/qmn/app/operations.py:467-476`). `passport` always answers no checks. No plan slice built the node's sign-in or binding, and C-11's and C-05e's reviews both assumed one existed. So no real or rehearsal trade can reach a cTrader account yet. New slice **C-12d** builds it.

## Verdicts

| Slice | Verdict | Why |
|---|---|---|
| C-14 first real start | BLOCKED until C-12d and C-26, then valid with the edits made | It needs a bound venue for its test trade. Edits: the script talks to the host's REST only, checks the deploy through the node's `deployments` read (flush settles a refused deploy silently), "passport landed" names the passport file, and "landed code" means the source checkout contains the main commit that added the script, because there is no build stamp and he squash-merges. |
| C-17 server node | NEEDS EDIT, made | Server steps cannot reuse the local-supervisor steps; apps install over SSH against the server host's loopback app routes. Added `connect_logs.py` (render the address), `otelcol.service` (its loopback endpoint breaks), the `home_of` fix in `supervisor.py`, the MIS in `APP_FOLDERS`, the keys file written before enable, and the round trip measured on the server. Test commands run with `--project qmx-agents`. Depends on C-12d, C-25 and C-26. |
| C-20 old shell cut | BLOCKED on G-DEMO evidence, edits made | Its title needs a demo trade. It now depends on C-15 and C-12d and carries a gate-evidence line: dispatch only when `c14-real.log` and `c15-demo.log` read all PASS. Files now keep `_refuse.py`, rewrite `observability/__init__.py`, name the kept names to move, and list the eight other readers of `qmn/deploy`. The kill line is never called by the new node, which acts through `PLACEHOLDER_KILL_EFFECTS`. That placeholder is the risk session's to replace. |
| C-21 live path | BLOCKED on C-17, C-12d and the four safety slices, edits made | This PC never sees a server's trading profile (the check needs `place == name`), so every live-world move would answer `trading_profile_off`. Files now include `host.py` (chat routes mount unconditionally; facts hard-code chats and agent steps on), `promote.py`, `host_route.py`, `node_link.py`, the control config's missing `host` section, and the node's demo-only gate (pinned by a test first). "Release and binding cards" became "binding card", since no release card exists. The engine's agent-step refusal waits for his go. |

The other built facts (C-22 relay not started, C-16 nothing binds CCXT, C-13 snapshots not on the volume) are true and block none of the four.

## Slices added

| Slice | Before | Done when |
|---|---|---|
| C-12d bind the cTrader demo venue in the node | C-14, C-17, C-20, C-21 | A fake sign-in binds a demo account, the venue reads ready, the self-test lands five ok checks on the passport, and `QMX_STAGE=shadow` binds nothing. Folds in C-11 review L2 and L3 and the shadow-stage BACKLOG item. |
| C-26 app installs pick up fresh source | C-14, C-17 | An edit under `qmn/src` reaches a reinstalled app env without touching `pyproject.toml`. |
| C-25 keep agents out of every grants folder | C-17 | An agent read of any `data/apps/*/data/grants/*` path is refused. BACKLOG "MUST FIX BEFORE C-17". |
| C-27 refuse the host's own pass in app manifests | C-21 | A manifest naming `qmx/CONTROL-TOKEN` in any case is refused. BACKLOG TOP item. |
| C-28 each host gets its own pass key | C-21 | A server cannot mint a pass that claims This PC or `operator`. lows B16. |
| C-29 deploy only the chosen markets, show refused deploys | C-21 | One market's promote trades that market only, and a refused queued deploy shows with its reason. C-23 findings. |
| C-30 alarms read the calendar and new keys | C-21 | A risk stop in an open session pushes once, a weekend stale feed sends nothing, and `rotate_keys` re-reads the senders. C-18 findings. |

Order for the coordinator: C-12d and C-26, then C-14 (rehearsal), then C-25 and C-17. After G-DEMO comes C-14's real run and C-15. C-20 goes after both demo logs pass. C-27 to C-30 go before C-21.

## For the coordinator's own files

- `QUESTIONS-FOR-OPERATOR.md` gate 2 should read `uv run python tools/first_real_start.py`, not `python tools/first_real_start.py`.
- BACKLOG gains no new rows from this pass; each item used above is now a planned slice.

## For the operator

One decision is his. C-21 needs the workflow engine to refuse agent steps on a machine that holds a live account (`qmx_engine/runner.py` `placed()`). The engine is his (ruling 49), so that one file change waits for his go. Default if he says nothing: C-21 builds everything else and leaves that line as a labelled placeholder, and no live account can be bound without it.

**His answer, 2026-11-03: "Not yet."** The engine stays unchanged. C-21 ships that line as a labelled placeholder, and live binding stays closed until he says yes.

Decided here without asking, because it follows from his rulings: per-host pass keys come before any live account (C-28). The old-code cut waits for the full demo proof, C-14's real run and C-15 (the plan's "nothing is deleted before its replacement passes"). The kill line stays a placeholder until the risk session.
