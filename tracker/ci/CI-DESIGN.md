# CI design: CI as the merge gate (draft, 12 November 2026)

Status: draft, not ratified. Nothing here is built. The only change made on GitHub was the approved probe, and it has been removed.

## 1. Diagnosis: GitHub Actions does not run on this account

**Short version.** GitHub has very likely flagged the account. The repo settings are fine. Actions ran in August and September, but GitHub now creates no run for any push, and it hides the old runs. Only GitHub Support can lift a flag. He has to file the appeal himself.

What I checked, with no side effects:

| Check | Result |
|---|---|
| Repo Actions permissions | `enabled: true`, `allowed_actions: all`. Not the cause. |
| Registered workflows | 6, all `active` (QA Battery, Deployment readiness, Factory test, QMN ubuntu-24.04 lane, Skylos, UI quality). |
| Runs, artifacts, caches | 0 runs, 0 artifacts, 0 caches. |
| Old runs we know existed | Runs 36274010671 and 36274010704 (27 Sep) and 33445431924 (31 Aug) are recorded in `workroom/ci-reconciliation-2026-09-27/START-HERE.md`. The API now returns 404 for each one. The history is hidden, not just empty. |
| Account and repo seen by a logged-out visitor | `github.com/MubarakHimself`, `github.com/MubarakHimself/QMX` and the matching API calls all return **404**, even though the repo says `visibility: public`. That is the known sign of a flagged account. |
| Other symptoms | He can't fork repos, and he has seen HTTP errors for about two months. Both match a flag. |
| Billing endpoint | Not readable: it needs the `user` token scope. I did not widen the token. |
| githubstatus.com | "All Systems Operational". This is not an outage. |

**The probe (approved test).** At 13:57:36 UTC I pushed branch `ci-probe` (commit `cde34d432`, "ci probe") from `main`. It added `.github/workflows/ci-probe.yml` with `on: [push, workflow_dispatch]` and two jobs, one on `ubuntu-latest` and one on `windows-latest`, each running `echo ok`.

- I polled `gh run list --branch ci-probe` every 30 seconds for 5 minutes. Every poll returned `[]`, and no run ever appeared.
- GitHub never registered the new workflow. The workflow list stayed at the same 6.
- `gh workflow run ci-probe.yml --ref ci-probe` failed with: `HTTP 404: workflow ci-probe.yml not found on the default branch`. That error is expected for a file that is not on `main`, so it proves nothing alone.
- The commit got **no GitHub Actions check suite at all.** Its only check suite came from the `cursor` app, and it sat at `queued`. Commit status: `pending`, with 0 statuses.
- Cleanup: I deleted the remote branch, the local branch and the worktree. `git ls-remote origin refs/heads/ci-probe` prints nothing.

**Correction to the brief.** `main` has no `.github` folder at all. The 6 workflows are left over from pushes to other branches in August and September. A scheduled run only fires from a workflow file on the default branch, so the missing cron runs on `main` were expected. The zero runs ever is still explained by the flag: real runs existed and are now hidden.

**Two consequences.**
- Self-hosted runners for GitHub Actions will very likely not help. GitHub's Actions service hands jobs to runners, and right now it does not even create a check suite. I have not tested this.
- The method's line "the repo is public, so Actions minutes are free" is on hold. While the flag stands, the repo is hidden from the public.

**What fixes it.** He files GitHub's appeal and reinstatement form: support.github.com, choose account restriction or flag. Include the username, the logged-out 404, the missing Actions runs and the fork error. Mention the ChatGPT connector he linked around the time it started. Community reports say replies take days to weeks.

## 2. The shape: one CI, four stages

CI is one set of workflows. The same jobs run at each stage; the stages differ in how much runs and who waits on it.

| Stage | Branch | Trigger | What runs | Who waits on it |
|---|---|---|---|---|
| Slice | `slice/<id>` | push, and PR into `build/**` | Lint, types and format for the touched packages. Tests of the touched packages. Linux and Windows. | The coordinator, before it spawns the reviewer (replaces the test part of `slice_checks`). |
| Landing candidate | `land/<program>/<batch>` | push (made by `ship land`) | The full sharded suite on Linux and Windows, plus the money-path and secret scans. | `ship land`, before it fast-forwards the build branch. |
| Program build branch | `build/**` | push, plus the nightly at each stop point | The full sharded suite on both systems, Skylos, Vulture, and mutmut on changed money modules. | `ship nightly` and the stop-point review. |
| Engine | PR into `engine/base`, then push to `engine/base` | PR, push, nightly | Everything: full suite on both systems, Skylos, Vulture, mutmut on all money modules, the QMN Linux lane, the UI checks. | The merge session. Branch protection enforces it. |
| Release | tag `v*` on branch `release` | tag push | Everything again, plus building the installer. No baseline reds are allowed. | His release click. |

- `main` stays plans and docs only. No code workflow runs on it.
- A workflow needs a file on the default branch for a schedule (nightly) or a manual run (`workflow_dispatch`). Either `engine/base` becomes the default branch, or `main` holds one small scheduler file that checks out `engine/base`. That is question 2.
- The fail-at-parent check stays on the laptop. It needs the parent commit and the slice's new tests, so the local scripts keep it.

## 3. Required checks on Linux and Windows

Each operating system gets one gate job that needs every shard and fails if any shard failed, was skipped or was cancelled. The existing `mandatory_verdict` script in `battery.yml` already does this, and it gets reused.

Required contexts on `engine/base` and `release`:

| Context | Runs on | What it proves |
|---|---|---|
| `gate-linux` | ubuntu-24.04 | Every Linux shard and the lint, types and format job are green. |
| `gate-windows` | windows-2025 | The same on Windows. |
| `skylos` | ubuntu-latest | Skylos gate (section 4). |
| `vulture` | ubuntu-latest | Dead-code ratchet. |
| `mutmut-money` | ubuntu-24.04 | Mutation gate on money modules. |
| `qmn-ubuntu-24-04` | ubuntu-24.04 | The existing node Linux lane. |
| `ui` | ubuntu-latest | The UI checks in `apps/qmx-ui`. |

Protection on `engine/base`: these contexts required, "require branches to be up to date" on, and "do not allow bypassing" on (`enforce_admins: true`). Once that exists, `ship preflight --protection-push-test` can run on every arm.

Reds already on the tip: build-branch reds keep using the program's `baseline-reds.txt`, which `ship` reads from the JUnit artifacts. The engine gate cannot see the program folder. So it reads a committed `ci/known-reds.txt`. That file starts as whatever is red on `engine/base` at the first CI run, and it may only shrink. The release gate ignores it: any red blocks a release. That is question 3.

## 4. Quality tools as merge gates

All three already exist in `battery.yml` and `skylos.yml` on `engine/base`. Every one is **schedule-only** today (`if: github.event_name == 'schedule'`), so none of them has ever gated a PR. The change is to run them on the engine PR, on the build branch at each stop point, and on release tags.

| Tool | Today's settings | As a gate |
|---|---|---|
| **Skylos** | `skylos==4.33.2` on Python 3.12, a whole-repo `-a --no-upload` scan, free tier only. Gate in `[tool.skylos.gate]`: zero critical, high, security, reliability, secrets, dependency CVEs and AI defects. Quality and dead code are annotations only (his ruling, 2026-09-28). A 20-minute limit. It strips agent-instruction files from excluded trees before scanning. | Keep the settings. Run on engine PRs, `build/**` stop points and release tags. On slice PRs, run only as annotations. It needs the network (OSV.dev), so one rerun is allowed on a network failure. |
| **Vulture** | `vulture==2.14`, `--min-confidence 80`. A ratchet: it fails only if the count rises above `qa/_trace/battery/vulture/gate-baseline-min80.txt`. Scope: `packages extensions qml qmb qmn tools`. **It does not scan `qmx-agents`.** | A gate on engine PRs and the build branch. Add `qmx-agents/packages` and `qmx-agents/apps` to the scope with their own baseline, so new agent code is covered. |
| **mutmut** | `mutmut==3.3.0`, Linux only, two jobs of 60 minutes each. (a) `qmf.core.exact` and `qmf.core.chrono`, with a kill-rate floor of 68%. (b) Node money modules `qmn.order.door`, `qmn.order.path`, `qmn.ledger.binding_ledger`, `qmn.reconcile.residuals`, `qmn.capital.kill_line`, `qmn.ledger.virtual`. Zero classified mutants fails closed, and survivors are advisory. | On the engine PR and release: both jobs, as `mutmut-money`. On the build branch: only the money modules a slice changed. Risk and sizing modules join the list as they land. The method's "mutation on changed lines for money, exit and kill-switch code" is this. |

The battery's other parts become part of `gate-<os>`: format, lint and types for all 17 workspaces, `money-path-scan`, `secret-scan`, and the corpus gate. `tools/ci.py` runs these one after another today and stops at the first failure. In CI they run as a separate `lint-<os>` job, so one failure doesn't hide the rest.

## 5. Sharding the 2 to 3 hour suite

Measured from `origin/engine/base` by counting `def test_` in test files. These are counts, not timings; no per-suite timings are recorded anywhere in the repo.

| Area | Test files | Tests | Share |
|---|---|---|---|
| `packages` (qmf) | 135 | 2,696 | 26% |
| `qmb` | 121 | 1,469 | 14% |
| `qa/tests` | 175 | 1,400 | 14% |
| `qmn` | 135 | 1,228 | 12% |
| `qmx-agents/packages` (15 packages) | 380 | 2,492 | 24% |
| `qml` + `extensions` | 55 | 581 | 6% |
| `tools/tests` | 23 | 381 | 4% |
| `qmx-agents/apps` (qmb, trading-node) | 4 | 57 | <1% |
| **Total** | **1,028** | **10,304** | |

The biggest agent packages are `qmx-engine` (586), `qmx-host` (470), `qma-harness` (409), `qmx-home` (191) and `qmx-router` (182).

**Estimate.** The laptop took 2.3 to 3 hours with two workers, about 5 to 6 worker-hours, or roughly 2 seconds per test on average. GitHub's hosted runners for public repos have 4 cores, and the suites already use `pytest-xdist` (`-n auto --dist worksteal`). A shard of about 1,300 tests then takes about 10 to 12 minutes of tests, plus 3 to 6 minutes of setup (`uv sync`; Windows is slower).

**Plan: 8 shards per operating system, 16 test jobs.**

1. `packages`, first half
2. `packages`, second half
3. `qmb`
4. `qa/tests`
5. `qmn`
6. `qmx-engine`, `qmx-host`, `qma-harness` (1,465)
7. The other 12 agent packages and the agent apps (1,141)
8. `qml`, `extensions`, `tools/tests` (962)

- Shards follow the existing `tools/test_all.py` suites. Each one runs in its own workspace (the root or `qmx-agents`), so the uv environments stay as they are.
- Splitting `packages` in half needs a small `tools/ci_shard.py` that splits files by recorded duration. After the first green run, CI saves each test's time from the JUnit files in `ci/durations.json`, and the split rebalances from that.
- The job limit goes from 60 to 90 minutes. The hosted maximum is 6 hours.
- Expected wall time: about 20 to 25 minutes per system, both systems side by side.
- The 16 test jobs plus Skylos, Vulture, mutmut and the QMN lane make 20 jobs, the free plan's limit. On the engine PR, mutmut starts after the test gates pass, so it never queues behind them.
- Each shard uploads its JUnit XML as an artifact named `junit-<os>-<shard>`. `ship` reads those, not the logs.

## 6. How the coordinator and merge sessions use CI

**In the ship scripts (to build later).** `suite.run_packages` gets a GitHub backend, chosen by `ci_backend = "github"` or `"local"` in `ship.toml`, with `"local"` as the default until CI works:

1. Push the candidate commit to `land/<program>/<batch>` (or use the slice branch).
2. Find its run: `gh run list --commit <sha> --workflow ci.yml --json databaseId,status,conclusion`.
3. Wait, time-limited through the wrapper: `gh run watch <id> --exit-status`.
4. Get the results: `gh run download <id> --pattern "junit-*"`, then parse them with the existing `parse_junit` and return the same `TestRun` shape.
5. No run within 5 minutes of the push means `FAIL ci-missing`. The script then falls back to `local` and writes a `CI DOWN` line, so a dead CI never stalls a night.

**Reading checks by hand** (merge session):
- `gh pr checks <pr> --required --json name,state,bucket` lists the gate contexts.
- `gh pr checks <pr> --required --watch --fail-fast` waits for them. Run it as a background command.
- `gh run view <id> --log-failed` shows what failed. `gh run rerun <id> --failed` reruns runner or network failures once.

**Exact line changes in `standing/prompts/MERGE.md`:**

| Line | Today | Becomes |
|---|---|---|
| 15 | "CI exists when the list holds the test battery's jobs on both Linux and Windows. Run `gh pr checks <pr> --watch` as a background command and wait for it." | "CI exists when `gh pr checks <pr> --required` lists `gate-linux` and `gate-windows`. Run `gh pr checks <pr> --required --watch --fail-fast` as a background command and wait for it." |
| 16 | "**No CI yet.** ... `WAITS FOR HIS WORD: CI does not run on this branch yet`" | "**CI down.** No required check reported within 30 minutes of the PR's last push. Write ... `WAITS FOR HIS WORD: CI did not run`." (The fallback stays while GitHub is unreliable; delete it once CI has been green for a full program.) |
| 17 | "Read the failures (`gh run view <run id> --log-failed`)." | Add: "A red test listed in `ci/known-reds.txt` does not run on this gate; any other red blocks." |
| 19 | `gh pr merge <pr> --merge` | Unchanged. With protection on, GitHub refuses the merge while a required check is red, which is a second lock. |
| 20 | "the CI result" | "the CI run ids and the `gate-linux` / `gate-windows` conclusions". |

**Exact line changes in `standing/prompts/COORDINATOR.md`:**

| Line | Today | Becomes |
|---|---|---|
| 8 | `{PROTECTION_TEST}`: "`yes` once he has turned on 'do not allow bypassing'..." | Unchanged in wording. Once `engine/base` protection exists, it is `yes` by default. |
| 23 (Arm 1) | Pushes the build branch if missing. | Add: "Then check CI answers: `gh run list --branch <build_branch> --limit 1 --json status` shows a run within 5 minutes. If not, set `ci_backend = \"local\"` in `{PROGRAM}/ship.toml` and write `CI DOWN` in `WAITS-ON-YOU.md`." |
| 28 (Arm 6) | `ship preflight` | Add: "Preflight's `ci` line must read PASS, or `ci_backend` must be `local`." |

The coordinator never reads CI directly; the rules card routes it. So `standing/RULES-CARD.md` changes too:
- **Line 9:** "Run `slice_checks`, `land` and `nightly` as background shell commands". Unchanged: with the GitHub backend they wait on CI themselves.
- **Lines 29, 34 and 35:** unchanged. Their exit codes keep the same meaning.
- **New row:** "`land` or `nightly` prints `FAIL ci-missing` | Log it, add a `WAITS-ON-YOU.md` line, and carry on; the script already fell back to local."

## 7. Retiring the stale `integration` protection and old triggers

What exists now:
- `integration` protection requires `skylos`, `check`, `vulture`, `agents` and `qmn-ubuntu-24-04`, with admins enforced.
- `ui-integration` requires the same contexts plus `ui`.
- Three of those (`skylos`, `vulture`, `agents`) run only on a schedule, so they never report on a PR. Even with Actions working, no PR into `integration` could merge.
- The triggers point at `main`, `integration`, `rebuild/**` and `factory-candidate/**` tags. `docker-nodes.yml` points at `rebuild/base`. None of these matches `engine/base` or `build/**`.
- The registered workflows `Factory test`, `UI quality` and `Deployment readiness` come from old branches and are on neither `main` nor `engine/base`.

Steps, in order. All of them need his yes (question 5):
1. Replace the workflows on `engine/base` with the new `ci.yml` (shards, gates, Skylos, Vulture, mutmut). Keep `qmn-ubuntu-24.04.yml` and `docker-nodes.yml`, with their triggers moved to `engine/base`, `build/**` and `release`.
2. Disable the 3 orphan workflows: `gh workflow disable "Factory test"`, and the same for the other two.
3. Remove protection from `integration` and `ui-integration`: `gh api -X DELETE repos/MubarakHimself/QMX/branches/integration/protection`. Deleting the branches themselves is a separate yes.
4. Add protection to `engine/base` and `release` with the contexts from section 3.

## 8. If Actions stays blocked

| Option | How it works | Cost | Fit |
|---|---|---|---|
| **Self-hosted GitHub runners** (laptop on Windows, VPS on Linux over Tailscale) | The runner agent polls GitHub for jobs. | Free. | **Very likely does not work.** The flag stops GitHub creating runs, and a runner only gets jobs GitHub creates. It also keeps the Windows suite on the laptop. |
| **GitLab CI** | Push the repo to a GitLab project as a second remote (`ship land` pushes to both). Register two self-managed runners: the laptop with the Windows shell executor, the VPS with the Docker executor. `glab ci status --live` stands in for `gh pr checks --watch`. | Self-managed runners are free and don't use GitLab's 400 free compute minutes a month. Reporting status back into GitHub PRs ("CI/CD for external repos") needs a paid tier, so the merge session reads GitLab directly. | Mature Windows runner. Good logs and UI. Works no matter what GitHub does. |
| **Bitbucket Pipelines** | Same pattern: a second remote and self-hosted runners on the laptop and the VPS. | Atlassian says self-hosted runners use no build minutes. A reported bug (BCLOUD-23916) blocked free workspaces with 0 minutes left from rerunning self-hosted pipelines. | Windows runners are newer (they were in beta). Weaker CLI for the merge session to read. |

**Recommendation: GitLab CI with his laptop and VPS as runners**, used only while the flag stands, with the appeal filed first. It has the most mature Windows runner, a usable CLI, and nothing to pay. The Linux shards move to the VPS. Be honest about the limit: Windows still runs on the laptop, so a Windows run competes with the builders. That is the price until GitHub's hosted Windows runners come back.

Even simpler is no third party at all: the ship scripts run Linux shards on the VPS over Tailscale SSH and Windows on the laptop. It adds nothing new, but there is no log UI and no second place enforcing the gate. GitLab is worth its setup only if the flag lasts more than about a week.

## 9. Questions for him

1. **Appeal.** Will you file GitHub's appeal and reinstatement form? Only you can. Everything in sections 2 to 7 waits on it.
2. **Default branch.** Nightly and manual runs need a workflow file on the default branch. Make `engine/base` the default branch, or allow one small scheduler file on `main`?
3. **Existing reds on `engine/base`.** Gate with a committed known-reds list that may only shrink, or fix every red before CI gates merges?
4. **If the flag lasts.** After how many days without an answer from GitHub should we set up GitLab with your laptop and VPS as runners? That needs a GitLab account and a second remote.
5. **Cleanup.** OK to remove protection from `integration` and `ui-integration` and disable the 3 orphan workflows (`Factory test`, `UI quality`, `Deployment readiness`)?
