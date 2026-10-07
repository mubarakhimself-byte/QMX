# P02: CI that actually runs

## Goal
PRs into `rebuild/base` (and later `integration`) get real automated checks, and the same checks run locally with one command.

## Known state
- Workflows in `.github/workflows/`: `battery.yml`, `skylos.yml`, `qmn-ubuntu-24.04.yml` (plus Deployment readiness, Factory test, UI quality on other branches). Triggers are `pull_request` on `main` and `integration` only.
- The GitHub API reports **0 workflow runs ever** for the repo, although Actions is enabled. PR #25 (rebuild/base → integration) got no runs either. The cause is unknown. It may be account billing or limits, which the operator must check in GitHub Settings → Billing.
- The battery is heavy: Tier-1 scanners, vulture ratchet, nightly mutmut.

## Steps
1. Add `rebuild/**` to `pull_request.branches` and `push.branches` in each workflow that should gate rebuild work. Battery `check` job: yes. Mutation: nightly only, unchanged.
2. Simplify the battery workflow to what P01's `just test-all` plus lint, format and type checks need. Keep scanners that guard real invariants (money-path float, secrets). Move anything else to a nightly job instead of deleting it.
3. Add `just ci` that runs exactly what the PR workflow runs, so a PR can be checked locally when Actions is unavailable.
4. Open the PR and report whether a workflow run appeared.
   - If none appears, run `gh api repos/MubarakHimself/QMX/actions/runs` and `gh api repos/MubarakHimself/QMX/actions/permissions`, then put the output in the PR for the operator.
   - Do not change repository settings.

## Done when
- `just ci` passes locally.
- Workflow files trigger on `rebuild/**`.
- The PR states whether GitHub ran the checks, with evidence.

## Out of scope
Branch protection changes; release and deployment gates.
