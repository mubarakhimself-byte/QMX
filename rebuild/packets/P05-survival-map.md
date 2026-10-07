# P05: Survival map of the QMA daemon (report only)

## Goal
Before new packages are built, know exactly which parts of `qmx-agents` survive, which get replaced by a library (DESIGN §3), and who calls what. This report drives P06–P16. **Change no code.**

## Scope
Every subpackage and root module under:
- `qmx-agents/packages/qma-daemon/src/qma/daemon/`
- `qma-core`
- `qma-wire`

The daemon subpackages include `request_runtime`, `taskgraph`, `plugins`, `staging`, `sessions`, `envs`, `backtest`, `hooks`, `journal`, `persistence`, `ledgers`, `artifacts`, `discovery`, `scheduler`, `host_control`, `bus`, `experiments`, `knowledge`, `proxy`, `tools`, `memory`, plus the root modules (`process.py`, `pairing.py`, `http_pair.py`, …).

## Output
Create `rebuild/reports/survival-map.md` with:
1. **Table.** One row per module:
   - path, LOC
   - what it does (one line, plain words)
   - production callers, and callers outside `qma-daemon` (QMB, QMN, UI contract)
   - verdict:
     - **keep** (port into a new package)
     - **replace** (name the library feature from DESIGN §3)
     - **delete**
   - target packet
2. **Invariants.** Where the evidence journal, ledgers, admission gate and money-path barrier are implemented, which functions hold the actual rules, and what a minimal port to middleware or a backend wrapper needs.
3. **External contracts.** Anything QMB, QMN or the UI depends on (wire schemas, CLI, HTTP routes), and which must keep working during the strangler phase.
4. **Mini-app code from MA01–MA04** (`staging/app_*`, `qma-core/app_candidate.py`, `qma-wire/app_*`, `panel_composition.py`, `discovery/queries.py`): which functions and data types to port into `qmx_apps.road` (P14).

## Method
Use static analysis: imports, `rg`, entry points. Use the call graph where cheap. Do not guess: mark "unknown" where unclear.

## Done when
The report covers every module. Claude reviews it before P06 starts.
