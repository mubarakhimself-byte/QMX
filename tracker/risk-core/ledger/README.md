# Variable ledger

Every variable in the QMX risk-management and position-sizing design, old and proposed, in one machine-readable list, with how each one affects the others.

Mubarak's words (3 Nov, M12): the old systems always kept a ledger "because these variables are many ... and each affects another". The ledger carries through expansion, architecture and the simulations.

## Files

| File | What it is |
|---|---|
| `variables.yaml` | Ledger v0: every variable found in the history and the grounding, merged across generations. |
| `additions/<file-id>.yaml` | One file per expansion agent. Same schema. Never edit `variables.yaml` from an expansion run. |
| `check.py` | The checker. It validates the schema, checks every coupling, prints counts and writes `couplings.md`. |
| `couplings.md` | Generated. A Mermaid graph of the couplings by level, one graph per level, and an edge table. Do not edit by hand. |

The funnel step merges `variables.yaml` and every additions file into v1.

## Run the checker

Time-limit it like any command. From the `risk-core` folder:

```
uv run --no-project --with pyyaml python ledger/check.py
uv run --no-project --with pyyaml python ledger/check.py ledger/additions/sizing.yaml
uv run --no-project --with pyyaml python ledger/check.py --with-additions
```

- `variables.yaml` is always loaded. Extra files are checked together with it, so an additions file may point at v0 ids and at ids in other files you name.
- `--with-additions` loads every `additions/*.yaml`.
- `--strict` fails on warnings too. `--no-paths` skips the source path check. `--no-write` leaves `couplings.md` alone.
- Exit code 1 means errors. Fix every error before you hand a file over. Read every warning.

What it reports:
- **Errors:** a missing or unknown field, a value outside its list, a duplicate id, an `inputs` or `affects` id that exists in no loaded file, a default without a derivation.
- **Warnings:** a source path or line that cannot be found, a default with no `basis`, an alias that is another entry's id or alias (a sign that one idea is split in two), a seed id that is not a heading in `seeds/SEEDS.md`.
- **Counts:** by level, kind, status and basis; how many defaults have a derivation; the number of couplings; orphans (no coupling either way); roots (nothing affects them).

## The rule: a default needs a derivation

- `default` holds a value only when a source states one as a design default. Placeholders from the unit build and figures a source calls "evidence only" go in `seen_values`, not in `default`.
- A non-null `default` needs a `derivation` that is not "open". The checker refuses it otherwise.
- `basis` says how good the derivation is:
  - `formula`: computed from its `inputs` by a formula written in `derivation`.
  - `reasoned`: a source gives a reason for the value.
  - `stated`: a source gives the value with no working. Say so in `derivation`. These are the numbers he says "carry no weight" until someone derives them.
  - `open`: nobody ever said. `default` must be null and `derivation` starts with "open".
- Never invent a value. A null default with an honest derivation note is correct.
- When generations disagree, leave `default` null, list each value in `seen_values`, and name the conflict in `open_questions`.

## Schema

One YAML list. One item per variable. Unknown fields are errors.

| Field | Required | Values |
|---|---|---|
| `id` | yes | snake_case, unique across every loaded file |
| `name` | yes | plain words |
| `level` | yes | `trade`, `position`, `unit`, `book` (cluster), `methodology`, `portfolio` (BMS), `account`, `node`, `system` |
| `kind` | yes | `size_input`, `size_output`, `limit`, `brake_threshold`, `brake_reset`, `accelerator`, `cost`, `measure`, `schedule`, `evidence`, `other` (exit settings and categorical choices use `other`; say which in `notes`) |
| `measure` | yes | `R`, `USD`, `percent`, `count`, `bars`, `minutes`, `ratio`, `pips_points_ticks`, or `other: <what>` (for example `other: lots`, `other: seconds`, `other: yes or no`) |
| `applies_to` | yes | `{classes: [...], styles: [...], timeframes: all or [...]}`. Classes: `fx`, `index`, `metal`, `energy`, `crypto`, `futures`, `stock`, `all`. Styles: `scalper`, `intraday`, `swing`, `all`. `all` stands alone. |
| `default` | yes (may be null) | a value, or null |
| `basis` | recommended | `formula`, `reasoned`, `stated`, `open` (see the rule above) |
| `derivation` | yes | how the default is worked out, in words, with the formula if one exists; "open ..." if nobody ever said |
| `seen_values` | no | `[{value, gen, ref, note}]`, every value any generation used, placeholders included |
| `inputs` | yes (may be empty) | ids this variable is computed from |
| `affects` | yes (may be empty) | `[{id, direction, how}]`; direction `up`, `down` or `either`; `how` is one line |
| `configurable` | yes | `true` unless a source says it is locked |
| `changed_by` | yes | list of `operator`, `agent_proposal`, `automatic`, `none` (`none` stands alone) |
| `status` | yes | `running` (runs in the shipped stack), `built_not_running` (code exists, nothing on the unit path runs it), `docs_only`, `dropped` (an earlier generation had it and a later one removed it), `proposal`, `idea` |
| `sources` | yes | `[{gen, ref, note?}]` |
| `seed_ids` | no | his asks in `seeds/SEEDS.md`, for example `A26`, `C27` |
| `aliases` | no | every other name the same idea had in any generation |
| `notes` | no | plain words |
| `open_questions` | no | list of plain-word questions |

### Sources

- `gen` is one of `april` (the old vault and lost code, Apr-May 2026), `july` (GitBook and July wiki), `sept_docs` (current `docs/` and engine/base code), `october` (the 5-13 Oct risk sessions and the risk lab), `unit_build` (the unit plan and the stack at `D:\QMX-worktrees\bld-us-c13`, d02af358), `operator_words` (his verbatim words), `grounding` (a G-file's own finding or simulation), `research` (R1-R3 and outside sources), `expansion` (an expansion document).
- `ref` is `path`, `path:line` or `path:line-line`. A path may be absolute (forward slashes are fine) or relative to the `risk-core` folder. A URL is also accepted. The checker warns when a path or line cannot be found.
- Cite the original where you can, not only the grounding file that quotes it.

### Couplings

- `inputs` says what a variable is computed from. `affects` says what it changes, with a direction and one line on how.
- An input link with no matching `affects` entry is drawn as a dotted "feeds" arrow. Prefer to write the `affects` side too, with its direction.
- Direction is about the target when the source rises: a higher kill line pushes the runway `down`.

## How to add a file under `additions/`

1. Name it after your layer: `additions/<file-id>.yaml`. It is a YAML list in the schema above.
2. Reuse an existing id wherever the idea already exists. Search `variables.yaml` for the id, the name and the `aliases` first. If the existing entry is incomplete, do not redefine it; add a new entry only for the new variable and point at the old one in `inputs` or `affects`, or write the gap in your expansion document.
3. New ids get status `proposal` or `idea`, `sources` with `gen: expansion` or `research`, and `seed_ids` where he asked for it.
4. Run the checker on your file and fix every error: `uv run --no-project --with pyyaml python ledger/check.py ledger/additions/<file-id>.yaml`.
5. Do not edit `variables.yaml`, `check.py` or another agent's additions file.

## What v0 leaves out

- Pure infrastructure rows from the docs registry (decimal scales, backups, Python version, latency budgets, queue bounds). They do not touch risk or sizing.
- Strategy logic numbers in the dummy unit (EMA period, RSI bounds, trend floor). They belong to entries, not to risk.
- Agent-system rows (`COMP-QMA-*`).

The checker prints the full count by level, kind and status on every run.
