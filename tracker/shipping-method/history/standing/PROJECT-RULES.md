# QMX project rules

Every agent that builds a slice or reviews a checkpoint reads this file in full. Your brief says what to build. This file says how QMX builds anything. The brief wins on what to build. The fixed lines below win over everything.

No reviewer reads a slice before it lands. Scripts check it, and the checkpoint review reads the whole batch a few hours later. Your tests are the slice's proof.

## What QMX is for

Mubarak is not a programmer and not a trader. He asks for a baseline that works plus a layer anyone can customize. He asks two things of an idea. Is it configuration? If it is left out now, does the core get reworked later? An idea that passes neither test is content someone adds later.

- **Configuration, never caps.** Every threshold, cadence, window, size and budget is a named setting with a labelled starting default, a reason and a range. A value you ship is a placeholder for "numbers talk", and you never argue it. Reckless setups stay expressible and warn in the largest type. They are never refused. A test bound is labelled as a test bound.
- **His words.** Demo means a broker demo account (IC Markets through cTrader today). There is live and there is demo. The fake broker in tests is the test broker, never "paper".
- **Brakes prevent, they never close.** A brake stops new entries or reduces. The kill switch is a brake. Only the kill switch's top level closes positions. Exits belong to the unit and its pod's rules.
- **A unit's journey is not hard-coded.** Workflows and mini apps decide it. Build no fixed draft, demo, live gates.

## The fixed lines

1. Agents never touch money. No code lets an agent submit, change or cancel an order, promote a unit, lower a kill level or change the floor.
2. Only he promotes to live.
3. Exits are never blocked.
4. Only his hand lowers the kill switch.
5. Keys are never read, printed or copied.

Your slice's tests hold the lines it touches. The brief's safety fact proves the one it depends on.

## How to build

- **Code truth beats the plan.** When the brief and the code differ on a fact, stop and reply `BLOCKED brief-mismatch <fact id>`. Never build around a wrong brief. When the plan itself is wrong (a plan line, an element or an edge case in your chain packet cannot hold), reply `BLOCKED chain <chain id> <why>`; it goes to the planner, not to him.
- **Never rebuild a removed row.** Your brief's section 7 and `CHAIN.md` list what was removed from your files and why. If the brief seems to need one back, reply `BLOCKED chain R-<id> <why>`.
- **Say what you chose.** For every reading of the brief you picked where it allowed two, write `DECISION <chain id>: chose X because Y` in `report.md`. The checkpoint review screens each one.
- **Build only the brief.** Touch only the files its Files block names, plus your evidence folder. The ready check refuses any changed file outside that list. If the change truly forces another file (a pin, a count, a census row, a schema copy, `uv.lock`), leave it untouched and reply `BLOCKED files <path> <why>`, so the planner widens the brief. Anything you notice and do not build goes to `findings.md` in your evidence folder, with what goes wrong for him, when, and your evidence.
- **Subtract first.** The first commit removes what the slice replaces. A replaced internal API moves every caller and is deleted in the same slice, with no compatibility layer. Nothing is deleted before its replacement passes.
- **Scenario tests first.** Before any code, write the tests for every edge case in section 7a and for the `Operations:` line, each driving the failure (the part raises, returns an extreme value, goes quiet, the host stops halfway), not the working path.
- **Tests are few and real.** Test at the public door, with the literal values the brief gives. Each new test fails at the parent on an assertion and passes at the head; an import or collection error does not count. A fake is never kinder than the real neighbour. A test that would still pass if the code returned nothing is rewritten or deleted. Never weaken or skip a test to go green. If the code's record shape makes a brief literal wrong, correct it from arithmetic and say so in `report.md`.
- **The parts he guards.** The workflow engine and the mini-app core are his. Change them only where the brief says, and an engine change is a new template only. A real block in the mini-app core gets a surgical fix with a one-line reason. The Library's core stays intact. No UI code unless the brief names it.
- **Lenses.** The brief names the skills and principles to use. Use skills that run inside one agent: `tdd`, `how`, `blast-radius` without its step 6, `unslop`, `technical-writing`, and the `principle-*` skills. You spawn no subagents, so skills that spawn (`arena`, `swarm`, `interrogate`, `no-comments`, `code-review`) are out.

## The traps that keep QMX's few errors few

- **Dependency direction (AD-21).** `qml` allows only `qmf-core`, `qmf-registry` and `qmf-risk` (`tools/workspace_meta.py`, `tools/tests/test_workspace_structure.py`). `qml` imports no host, app, venue, Library or `qmf-data` module, runs no subprocess and has no console script. Row shapes live in `qml` or `qmf-risk`. `fold` and `explain_size` take plain mappings. Hosts own journal kinds and reading.
- **Exits.** No exit code path reads a chain, the fold, the readings feed, a rate or account facts. A raise becomes a `Fault`, never a refusal into `close_frontier`, because that sets `Phase.STOPPED` and ends the unit's exits.
- **`make` and `evidence`.** `make` gets starting values and `evidence` carries moved ones. A block that reads a number from `make` at answer time fails K9 6.
- **Stdlib blocks** are QML in the node's lock, so they reach the money app and need his signature. A library change does not bump `trading-node`; the stop point's release does. A change to a file under an app folder bumps that app's version in `app.toml`, and the pin in `test_shipped_apps.py` moves with its measured digest.
- **A changed compiled decision bumps `COMPILER_FORMAT_VERSION`,** once per changed decision, whether or not the brief says so. Say so in `report.md`. The bump is free until the first live deployment.
- **A new package or app** runs in CI only once its suite is in `tools/test_all.py` and its workspace in `tools/ci.py`. Tests for scripts under `tools/` go in `tools/tests/`.
- **Money arithmetic.** `tools/money_path_scan.py` fails a binary float that reaches a quantity, a price, a P&L or a balance. Use `Decimal` or the exact value types.
- **Counts and censuses move on purpose.** `qmx-tools/tests/test_tools.py` pins the tool count per server; a new row in an existing toolset changes it in your slice. The census (`_CENSUS` in `qml/tests/test_unit_refuses.py`) fails on any new schema field until it runs, refuses or is labelled; that file and its refusal table move with any slice that adds a field or lifts a refusal.
- **Tests live where their imports do.** `qml` tests import only `qml` and its packages. `qmb` tests never import `qmn`. Only the `qmx-agents` workspace holds `qmx_tools`, `qmx_host` and `qmx_library` with `qmn` and `qmb`; the root workspace has no `qmx_tools`. A new reason text needs a code, or QMB fails and the node files it as `unlisted`.
- **QMB's scaffold test bans some words** in `qmb/src/qmb/host/`, among them `snapshot` (`qmb/tests/test_qmb_scaffold.py`). Shipped tests compare Library message text, so a refusal keeps its first message as the head.
- **The credential guard.** The ship test wrapper fakes the keyring and refuses Credential Manager calls. A guard error means your code reached for the real store, so patch the call in memory for your test. Reds listed in the program's `baseline-reds.txt` are not yours.

## Environment and safety

- Windows 11 is first class: PowerShell 7 and Git Bash. Use `spawn` only, whole-then-replace file writes, and no POSIX-only calls. Work on `D:`. Never gate on memory or disk.
- Your Bash working folder resets between calls. Use absolute paths and `git -C <your worktree>` for every git command.
- Run project Python with `uv run --no-sync` inside your worktree. Never edit a file inside a venv. Run every lint, type and test command through the ship wrapper (`ship timed`), which gives it a time limit, its own temp and data folders and the fake keyring.
- Write file content with the Write and Edit tools. Bash heredocs on this host halve backslashes.
- Never name a PowerShell variable `$home`. It keeps the real user profile, so a script would write into his real home.
- Stay in your own worktree and evidence folder. Never touch the main checkout `C:/Users/Mubarak/Desktop/QMX`, another agent's worktree, `~/.claude`, his real `~/.qmx`, `C:/Users/Mubarak/Documents` or `C:/Users/Mubarak/Desktop/DATA_NARL`. A test that needs a QMX folder uses the wrapper's `QMX_HOME` and `QMX_DATA_DIR`.
- Never read the repository's `docs/` or `_docwork/` folders, which are stale, or old Hermes logs, which hold credentials.
- Never use `git stash` (shared across worktrees), rebase, force-push, or delete a branch or worktree.
- Tests use the test broker only. Never a broker account, demo or live. No Anthropic or OpenAI API spend.
- Commits and PRs carry no model or tool credit line (`Co-Authored-By:`, `Generated with`); the ready check refuses them. Commit messages read `<slice id>: <plain words>`. PR bodies hold the brief's `TRACE:` line and end "Shipped by Mubarak."
- If a hook tells you how to rerun a command, do that. If a permission check or a safety rule refuses you, stop. Change no permission setting and do not work around it. Push what works and reply `BLOCKED` with the refusal's exact text.
- If you are interrupted, commit and push what works first.
