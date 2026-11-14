# CI intent check, 13 November 2026

Read-only check of the CI built today against what he asked for and agreed to on 12 November. Built state: `origin/ci/github` frozen at `9eb140303` (PR #1 into `engine/base`, open, not merged), and `ship/kit` at `51d95409a`, plus the stopped GitHub backend in the ship-kit stash (`stash@{0}`, "WIP GitHub CI backend, stopped 13 Nov before grounding"). Line numbers below point at those commits. `qmx-ci.yml` means `.github/workflows/qmx-ci.yml` and `qci.py` means `tools/ci/qci.py`, both on `origin/ci/github`.

**Verdict in one line:** the CI shape matches what he agreed to, but it can't give a green deep run yet. Nothing enforces the merge gate, release is thinner than agreed, the scheduled mutation walk never fires, the review prompts still say "CI paused", and no backlog loop exists.

## Where the intent comes from

His words (transcript `dd8f4ab2`, 12 Nov unless marked):
- L1482, 10:43: "rerunning an entire repo test, well, you have 40 plus PRs going. Doesn't make sense." He also asked "What is CI for?"
- L1657, 10:52: "Especially when I'm starting to release ... we are close to our very first release version, a combined one with the UI."
- L1769, 11:08: "after a coordinator and the stack list is merged to engine/base, the CI pipeline has to run, which means now the agent that is merging has to wait." Also: "The release can be a tagged version ... Let's not use staging." "Main is literally the branch I wanted to keep clean with no code." "Windows and Linux, I think, first."
- L1816, 11:29: "Skylos, Vulture, and Mutmut. Like, don't they have to come in on the CI and release? ... code quality ... part of the CI and release workflow?"
- L3951, 17:08: "So Mutmut is going to go not only on money and other things, man. I think it's global."
- L4143, 17:24: "Can't we design the CI pipeline up around just those three things ... speed is still an issue."
- L4285, 17:51: run Skylos, mutmut and Vulture, "it sort of finds the issues ... then we combine them with today's bugs".
- L4312 and L4354, 17:56 and 18:01: bugs from the runs "feed the planning". He accepted the three doors (mechanical, contained, design-level) "then we triage against blast radius".
- 13 Nov, L4891: "I'm not going to pay for compute ... When there is a free option that I can use, I'm willing to risk it."
- 13 Nov, L5926: "I don't think we need the old workflows ... The repo now is set to work with the CI pipeline."
- Today, quoted by the coordinator: "the shipping and then the review step were mostly rotating around the CI"; "quality is very paramount"; "perhaps even the release versions"; "is there any backlog coming from the runs, and how will we handle it?"

Proposals he answered:
- L3899, 16:33 (CI levels): slice, landing, full suite, stop point into `engine/base` with Skylos, Vulture and mutmut, and release ("Everything above, plus building the installer and starting QMX once with no data, and a browser test of the UI"). Also: "quality thresholds only ever tighten; the known-failures list only ever shrinks."
- L3945, 17:03: "Windows only from landing onwards as you approved."

Rulings, from the evening of 12 Nov (`BUILD-PHASE-REDESIGN.md:7`, `SHIPPING-METHOD.md:11-13`, memory `shipping-method-v3-rethink`):
- No AI reviewer per slice.
- Skylos, Vulture and mutmut work as a ratchet: "only new findings block and baseline findings become backlog rows".
- Vulture and Skylos run per slice. mutmut runs at checkpoints and globally on a schedule.
- Windows runs the whole suite at every checkpoint.
- The checkpoint review merges when the review is clean and the deep run is green.

13 Nov (memory `qmx-github-home-2026-11-13`): the new public repo, free runners, `qmx-ci.yml` the only pipeline, the ship scripts get a GitHub backend, and the local Windows run is the fallback.

## 1. Intent against the build

| Intent (source) | Built today | Match |
|---|---|---|
| **Per slice: cheap checks** (format, lint, types, touched tests, fail-at-parent). Linux in CI, Windows on the laptop (L3899, L3945; `SHIPPING-METHOD.md:73`, `:112`) | `qmx-ci.yml:31-32` triggers on `slice/**`. `lint` (`:84-86`) covers only touched folders (`qci.py:443-482`), `fail-at-parent` `:129-131`, `tests-linux` 3 shards `:140-157`. No Windows at slice, as agreed | Match |
| **Per slice: Vulture and Skylos, only new findings in the slice's files block** (redesign `:7`) | `qmx-ci.yml:107-127` at slice. Skylos uses `--diff-base` (`qci.py:748-749`). `ratchet_verdict` blocks only in changed files (`qci.py:571-590`). The ship-kit `slice_checks` also runs both locally against its own baseline | Partial: works, but twice (see section 4) |
| **Who waits on the slice run** (CI-DESIGN §2: the coordinator, before the next step) | `slice_checks` waits on nothing from CI. The stash adds a "Linux slice run" that `land` waits for, up to `ci_slice_grace_s = 3600` (stash `settings.py`) | Partial: not built yet (stash only) |
| **Landing: touched tests on the merged batch, Linux and Windows; only new reds block** (L3899; `SHIPPING-METHOD.md:75`, `:113`) | `qmx-ci.yml:31-32` on `build/**`: `tests-linux` and `tests-windows`, 3 shards each (`:140-179`). Base is the push's `before` (`qci.py:269-273`). Known reds don't block (`qci.py:429-441`) | Match in CI. `ship land` doesn't read it yet (stash only) |
| **Checkpoint deep run: whole suite on both systems, plus Vulture, Skylos and mutmut on changed functions** (`BUILD-PHASE-REDESIGN.md:57`, `SHIPPING-METHOD.md:81`, `:114`) | Level `deep` is started by hand (`workflow_dispatch`, `qmx-ci.yml:36-42`). `suite-linux` and `suite-windows` 8 shards each (`:181-218`), lint, Vulture, Skylos, mutmut on changed functions (`qci.py:790-816`), `docker-node`, `qmn-lane`. `deep-verdict` runs only when every job passed (`:394-410`) | Partial. The shape matches, but it can't be green: (a) lint fails on Linux types (T-22), and lint has no ratchet; (b) Skylos scans the whole repo at deep with a 40-minute cap and times out (`qci.py:728`, `:750`; run 43474050888); (c) `known-reds.txt` has no Windows rows (taken from a GitLab run whose Windows shards never finished), so old Windows reds count as new (run 43474050888: 7 "new" Windows reds) |
| **Merge gate: "before merging, CI has to work"; the merging agent waits** (L1769; `SHIPPING-METHOD.md:13`) | `gate` job on a PR into `engine/base` (`qmx-ci.yml:412-427`) passes only if a green deep run has a verdict for the PR's exact head (`qci.py:955-967`). **`engine/base` has no branch protection** (`gh api .../branches/engine%2Fbase/protection` → 404), so nothing makes the gate required. `STOP-REVIEW.md:73` still says "CI is paused, so the gate is local" and `:77` "Linux: not run (CI paused)" | Partial: the gate exists but isn't enforced, and the merge step doesn't read it |
| **Ratchet: baselines; only new findings block** (redesign `:7`) | `ratchet.py` (keyed without line numbers, counted). Baselines in `ci/baselines/`. `vulture.txt` holds 21 findings. **`skylos.txt` is empty** ("NO BASELINE TAKEN YET"). `mutmut.txt` covers qmf-core and qmf-risk only; qmn wasn't run. ship-kit keeps a **second** baseline in `ship-quality` (README `:59-67`), never taken; the folder doesn't exist | Partial: two ratchets, one with no Skylos baseline, the other empty |
| **Baselines only shrink; thresholds only tighten** (L3899) | Nothing checks it. A finding that is fixed stays in the baseline, so it can come back without blocking. `pull_reds.py` rewrites `known-reds.txt` wholesale from one run, so it can grow | Missing |
| **mutmut on changed functions at checkpoints** (redesign `:7`) | `mutate_targets` takes every function holding a changed line since the merge-base with `engine/base` (`qci.py:790-816`); new survivors beyond the baseline block (`:922`) | Match |
| **mutmut "global", on a schedule** (L3951; redesign `:7`; `SHIPPING-METHOD.md:115`) | Level `walk` on cron `23 3 * * *` (`qmx-ci.yml:43-44`), 1 of 24 parts per night (`ci_mutate.py:18`), "not a gate" (`qci.py:918-920`). **GitHub runs schedules only from the default branch, which is `main`, and `main` has no `.github` folder**, so it never fires. Survivors go only to a 30-day artifact | Missing in practice |
| **Known reds: a committed list that may only shrink; release ignores it** (CI-DESIGN §3, Q3) | `ci/baselines/known-reds.txt`: 57 lines, Linux only (shards 2-8 of GitLab pipeline 3061230259). The release level reads it too (`qci.py:429-441`, no release case) | Partial: incomplete, and release doesn't block on known reds as designed |
| **Flaky tests** (none agreed; CI-DESIGN §6 allowed one rerun for runner or network failures) | Nothing. Timing tests such as `test_health_answers_in_under_a_second_all_through_a_round` show up as "NEW RED" on Linux (run 43474050888) | Missing |
| **Release = a tag `v*`** (L1769), "a combined one with the UI" (L1657), with "everything above, plus building the installer and starting QMX once with no data, and a browser test of the UI" (L3899), "no baseline reds" (CI-DESIGN §2) | Tag `v*` runs `deep` jobs plus `smoke-linux` and `smoke-windows` (`qmx-ci.yml:258-279`): host start, status, stop on a fresh folder (`qci.py:1050-1067`). Missing: an installer build, the UI build and browser test, `docker-node` and `qmn-lane` (deep only, `:285`, `:338`), a release verdict, a GitHub Release with notes, and any rule about which branch a tag may sit on | Partial: a smoke start only |
| **Power and outage** (`SHIPPING-METHOD.md:100`; CI-DESIGN §6 step 5: no run within 5 minutes means fall back to local and write `CI DOWN`) | CI runs in GitHub's cloud, so a laptop power cut doesn't stop a deep run, which is the main gain. In the stash, `ci.start` falls back to local when `gh`, the network or the workflow is missing, and `ci_status` returns "PENDING ... the run goes on there" while GitHub is unreachable. `STOP-REVIEW.md:26` restarts a deep run only if `summary.txt` is missing and "its command is not running", which still describes a local command | Partial: the design is right, it's only in the stash, and the review prompt doesn't know CI |
| **Cost: free, public, no pay-per-use** (13 Nov ruling) | Public repo `mubarakhimself-byte/QMX`, standard `ubuntu-24.04` and `windows-2025` runners: free. A deep run has 23 jobs, over the free plan's 20 at once, so a few queue (slower, still free). No secrets, no paid runners | Match |
| **Old workflows go; `qmx-ci.yml` is the only pipeline** (13 Nov L5926) | Done in `9eb140303`: battery, skylos, docker-nodes and qmn-ubuntu deleted, their checks folded in | Match |
| **The ship scripts get a GitHub backend; local Windows is the fallback** (13 Nov ruling; CI-DESIGN §6 said `local` should stay the default until CI works) | Stash only. It defaults to `ci = "github"` (stash `settings.py`), while CI can't be green yet. `ship quality` stays local, so CI's Vulture, Skylos and mutmut results are not what the review reads | Partial |

## 2. The backlog from runs

What happens to each kind of finding today:

| Kind | Where it goes today | Who picks it up |
|---|---|---|
| Baseline findings (Vulture 21, mutmut about 1,145 survivors, Skylos none) | `ci/baselines/*.txt` on `ci/github`. ship-kit's `BACKLOG.md` would be generated in `D:/QMX-worktrees/ship-quality`, but that folder doesn't exist and its baseline was never taken | Nobody. The 12 Nov `ISSUES-2026-11-12.md` copied them once, by hand (T-15 to T-20) |
| New findings that don't block (notes outside the slice's files) | `ci-out/<tool>-new.txt` inside a 30-day artifact | Nobody |
| New findings that block | Fail the slice or deep run. The builder or fixer must clear them | The build loop. This part works |
| Surviving mutants from the walk | `mutmut-findings-<n>.txt` in a 30-day artifact, and the walk never runs | Nobody |
| Known reds | `ci/baselines/known-reds.txt` | Nobody. No rule says who fixes them |
| Flaky tests | Counted as new reds, so they block | A builder would chase a test that isn't theirs |
| Review Pre-existing and Nit findings | `stop-review/<X>/REVIEW.md`, "list them for the next plan" (`STOP-REVIEW.md:49`) | The next plan, if someone reads it |

**The loop is not closed.** `SHIPPING-METHOD.md:11` promises "backlog rows for a later fixer", but no step names that fixer, and there are three places a finding can sit (CI baselines, the ship-quality folder, review files), plus tracker files (`tracker/BUGS.md`, `ISSUES-2026-11-12.md`).

**The smallest closed loop that fits the method:**

1. **One ratchet, one backlog.** `ci/baselines/` in the repo is the only baseline. ship-kit's `quality` reads it instead of keeping its own (or calls `tools/ci/qci.py` locally, which already runs on a laptop).
2. **One backlog file.** A small script, `tools/ci/backlog.py`, writes `tracker/BACKLOG-QUALITY.md` from: `ci/baselines/*.txt`, `known-reds.txt`, the last deep run's non-blocking notes and the last walk's survivors (pulled with `gh run download`, like `pull_reds.py`), plus a "flaky" list. Each row gets a stable id, the tool, the file, what it is, the first-seen date, `touches` (money, exits, brakes, kill) and a door (mechanical, contained or design). The door is set by rule where it can be (a Vulture unused import, a lint error: mechanical) and left as `triage` otherwise.
3. **Fed at fixed points.** The checkpoint review appends its Pre-existing and Nit findings and every known red its deep run saw. `ship merged` runs `backlog.py` after each merge. The nightly walk is fixed to run (fix item 4) and feeds survivors.
4. **Picked up by planning, never by builders.** "Plan the next work" (`plan-feature`) reads `BACKLOG-QUALITY.md` with the issues list. It triages through the three doors he accepted (L4348, L4354): mechanical rows go in one batch to one agent with no planning; contained rows get a light funnel (ground, blast radius, fix brief); design rows get the full funnel. Builders never see the backlog, so nobody is blocked.
5. **Closed by the ratchet.** When a fix lands, `baseline` level rewrites the baseline, the row disappears, and a guard (fix item 6) fails any PR whose baseline file grows. A fixed finding can't return quietly.

## 3. The review step and CI

**No, not yet.**
- `STOP-REVIEW.md:32-34` starts `ship nightly` and `ship quality` "on this Windows laptop ... Linux is not run until CI runs it".
- `:73` says the merge gate is local because "CI is paused".
- `:77` and `:79` write "Linux: not run (CI paused)" into the PR and the merge record.
- `MERGE.md` has the same assumption.

The stash would make `ship nightly` dispatch the CI deep run and write its result into `checks/_nightly/<tip8>/summary.txt`, which the review already reads (`:48`). So test reds would reach the review indirectly.

Three gaps remain:
- **Quality deltas.** `ship quality` stays local with its own (empty) baseline, so CI's Vulture, Skylos and mutmut verdicts never reach the review.
- **Thin deep verdict.** `verdict.json` (`qci.py:927-939`) holds only sha, ref, run id, host and level. It has no reds, no new findings and no mutant counts, and it exists only when everything is green. A red run leaves no verdict.
- **Merge doesn't check the gate.** The merge step never runs `gh pr checks --required`, and GitHub won't refuse the merge because there is no branch protection.

What the method intends (`BUILD-PHASE-REDESIGN.md:239`, `:268`) is that the review "reads the deep run through the chain": every red, every new quality line, and survivors under a fixed-line test. That needs one summary file from the CI run that lists all three.

## 4. Built today, not agreed, and he might not want

1. **Two quality ratchets.** CI keeps `ci/baselines/` in the repo. ship-kit keeps TSV baselines and `BACKLOG.md` in `D:/QMX-worktrees/ship-quality`. They key findings differently, and both run Vulture and Skylos per slice (laptop and CI). Nobody chose two. It doubles the work and can give two answers.
2. **The gate is "a green deep run on this exact commit", not required checks per system.** It is reasonable, but it differs from CI-DESIGN §3 (`gate-linux` and `gate-windows` as required contexts with branch protection). Without protection, nothing stops a merge on red.
3. **The deep run is only started by hand** (`workflow_dispatch`). A push to `build/**` runs only the landing tests. That fits his "not every PR" (L1482), but it means a checkpoint gets a deep run only when the ship script or an agent starts one.
4. **The stash makes GitHub the default backend** (`ci = "github"`) while CI can't be green. Every checkpoint would come back red until T-22, the Skylos timeout and the Windows known reds are fixed. CI-DESIGN §6 said `local` stays the default until CI works.
5. **Product code and tests changed by a CI branch.** `qmn/src/qmn/host/qa_debt_matrix.py` (2 lines), `qmn/tests/test_qmn_deploy_switch.py` (1 line) and `tools/tests/test_readiness_gate.py` (rewritten); `tools/tests/test_mutation_workflow.py` deleted; one `pyproject.toml` line. These are small, but they are product-repo edits inside a CI PR, and the agent itself flagged the fourth file as "outside your list of three".
6. **`.gitlab-ci.yml` kept as a fallback** (195 lines), calling the same `qci.py`. He said GitLab is the fallback only. Keeping a second pipeline costs upkeep and is never run, so it will rot.
7. **`qmn-lane` and `docker-node` run again at the PR gate**, though the deep run already ran them on the same head. That is more minutes than needed (free, but slower to merge).
8. **The mutmut kill-rate floor (68%) is gone,** replaced by "no new survivors". That follows the ratchet ruling, but OR-10's "never worse than today" floor from 27 Aug is no longer stated anywhere. Worth one line to him.
9. **Release reads `known-reds.txt`,** so a release can ship with known reds. CI-DESIGN §2 said "no baseline reds are allowed" on a release.

## 5. Prioritized fix list

| # | Fix | Where | Kind | His call? |
|---|---|---|---|---|
| 1 | Make the deep run able to pass. Fix Linux typing (T-22: platform guards around `ctypes.WinDLL`, `CREATE_NO_WINDOW` and credential code in qma-harness, qmx-apps, qmx-engine, qmx-home, qmx-host and qmn; qmx-apps format and unused import). The `fix/linux-typing` branch was never created | product packages listed in T-22 | product code | No (he ruled QMX must run on Linux and Windows alike) |
| 2 | Skylos at deep: scan with `--diff-base <checkpoint start>` like the slice does, and keep the whole-repo scan for the `baseline` level only, split by top folder so each part finishes under the cap. Then take the Skylos baseline on a `baseline/**` push | `qci.py:728` (`base` only for SLICE), `:750` | script | No |
| 3 | Retake `known-reds.txt` from one full GitHub deep run on `engine/base` with both systems (`pull_reds.py <run id>`), after #1. Add a release rule: at level `release`, known reds block | `ci/baselines/known-reds.txt`; `qci.py:429-441` | script | Ask once: "release blocks on every red", as CI-DESIGN Q3 proposed |
| 4 | Make the nightly walk actually run: put a small scheduler workflow on `main` that dispatches `qmx-ci.yml --ref engine/base -f level=walk`, or make `engine/base` the default branch | `.github/workflows/nightly.yml` on `main`, or repo settings | CI config | **Yes**: CI-DESIGN Q2 was never answered, and `main` "no code" is his rule |
| 5 | Protect `engine/base`: require the `gate` check, require up-to-date branches, no bypass (`enforce_admins`) | GitHub branch protection | CI config | **Yes** (admin setting on his repo) |
| 6 | Ratchet guard: a test fails when any `ci/baselines/*.txt` gains lines, unless the commit is on a `baseline/**` branch. `ratchet_verdict` also reports baseline rows no longer found ("gone"), so the next baseline can drop them | `tools/tests/test_ci_driver.py`; `qci.py:571-590` | script | No |
| 7 | One ratchet: ship-kit `quality` and `slice_checks` read `ci/baselines/` (or call `qci.py vulture/skylos/mutmut` locally) and stop writing `ship-quality`. When the backend is `github`, `quality` reads the CI run's `*-new.txt` and `mutmut-findings-*.txt` instead of rerunning | `tools/ship/quality.py`, `slice_checks.py`, README `:59-67` | script | No |
| 8 | A rich deep verdict: always write `ci-out/summary.json` and `summary.md` (`if: always()`), listing every red with new or known, every new quality line, mutant counts per changed function, skipped and failed jobs, and the run URL. `deep-verdict` stays the green stamp the gate reads | new `summary` job in `qmx-ci.yml` with `needs:` all deep jobs and `if: always()`; `qci.py` `job_summary` | CI config + script | No |
| 9 | Point the review and merge prompts at CI: start the deep run through `ship nightly` (GitHub backend), read `summary.md` as the deep-run evidence, wait for `gh pr checks <pr> --required --watch` before `gh pr merge`, replace "Linux: not run (CI paused)" with the CI run ids and conclusions, and keep "Linux not run" only when the backend fell back to local. Do the same for `MERGE.md` | `standing/prompts/STOP-REVIEW.md:26`, `:32-34`, `:48`, `:73`, `:77`, `:79`; `MERGE.md` | script (prompt text) | No |
| 10 | Finish the ship GitHub backend from the stash, but default `ci = "local"` until one deep run on `engine/base` is green. Then switch, and keep the fall-back-to-local and `CI DOWN` line | ship-kit stash `settings.py`, `ci.py`, `nightly.py`, `land.py`, `suite.py` | script | No |
| 11 | The backlog loop: `tools/ci/backlog.py` writes `tracker/BACKLOG-QUALITY.md` with door tags. `ship merged` and the review append to it, and `plan-feature` reads it at "plan the next work" | new script; `standing/prompts/STOP-REVIEW.md:49`; `plan-feature` skill; `SHIPPING-METHOD.md:11` | script | Light: tell him where it lives |
| 12 | Flaky tests: on a red, rerun only the red tests once in the same shard. A test that passes on the rerun is reported `FLAKY`, doesn't block, and goes to the backlog as a mechanical row | `qci.py` `job_tests` (`:369-423`), `tests_verdict` | script | No |
| 13 | Release, as he described it (L3899): a `release` job that builds the installer, builds the UI and runs its browser smoke test, runs `docker-node` and `qmn-lane`, writes a release verdict, and creates a GitHub Release with notes from merged checkpoint records. Tags only on `engine/base` commits that passed the gate | `qmx-ci.yml:258-279` plus new jobs; `qci.py` `job_smoke` | CI config + script | **Yes**: what a "release" means for him (UI included? installer for Windows only, or both?) and which branch tags come from |
| 14 | Remove `.gitlab-ci.yml`, or keep it and run it once a month, so the fallback works when needed | repo root | CI config | **Yes**: fallback kept or dropped |
| 15 | Skip `qmn-lane` and `docker-node` at the gate when a green deep run on the same head already ran them | `qmx-ci.yml:285`, `:338` | CI config | No |
| 16 | Write `tools/ci/durations.json` from the first green deep run so shards balance by time, not file count (CI-DESIGN §5) | `tools/ci/` | script | No |
| 17 | Say plainly to him that the mutmut floor became "no new survivors" (OR-10 said "never worse than today") | one line in `SHIPPING-METHOD.md:11` | docs | Confirm only |

Order: 1 and 2 first (nothing goes green without them), then 3, 8, 9 and 10 (the review reads CI), then 5 and 4 (needs his yes), then 6, 7, 11 and 12 (closing the loop), then 13 (release).
