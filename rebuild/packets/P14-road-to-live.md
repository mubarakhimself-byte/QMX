# P14: Road to live (port MA02–MA04)

## Goal
Apps move Build → Tests → Sandbox → Shadow run → Live, with an evidence record at each step and rules by risk class. Reuse the good parts of the October mini-app work instead of rewriting it.

## Read first
- `rebuild/DESIGN.md` §7.2
- The P05 survival map §4
- Existing code: `qma/daemon/staging/app_candidate.py`, `app_validation.py`, `app_publication.py`, `qma-core/app_candidate.py`
- `rebuild/research/ui-model-and-baseline-audit.md` §1.4 (the UI's stages and rules)

## Build (`qmx_apps.road`)
- Port the immutable version chain and compare-and-swap head updates (from MA02), plus the validation approach (from MA03). Drop the "inert, data-only" restrictions: a published app now runs, through P12.
- **Stage machine per app version:**
  - **Build:** the definition is valid.
  - **Tests:** the app's own tests pass in its venv.
  - **Sandbox:** runs on recorded data in an isolated volume copy.
  - **Shadow:** runs on live data; its outputs are logged and consumed by nothing.
  - **Live:** goes live according to the risk class:
    - *shows things*: automatic after Shadow passes
    - *runs work*: automatic, inside its budget
    - *touches money*: only proposals; operator signature required
- **Evidence record per step:** inputs, versions, results, duration. Store it in the app volume and expose it via `qmx-control`.
- Rollback: re-activate the previous version.
- Keep the files small: one module per concern, each under about 400 lines.

## Tests
- every transition, including refusals
- risk-class rules
- rollback
- compare-and-swap conflict on a concurrent publish
- ported MA02–MA04 tests that still apply (adapted, not deleted wholesale)
