# Pack-and-grant kit — epics-and-stories handoff (2026-09-23)

Documentation Factory Stage 9 folded `architecture-QMX-2026-09-23` into `docs/`. This session does **not** run `bmad-create-epics-and-stories`. Next session does.

## Inventory

```text
python C:\Users\Mubarak\.agents\skills\documentation-factory\scripts\validate_inventory.py --root C:\Users\Mubarak\Desktop\QMX --handoff FEAT-0058
```

First epic after this fold = **FEAT-0058** (host SDK pack-and-grant). It is blocked by FEAT-0052 and FEAT-0053 (Workflows envelope/grants and product_session). `--next` still prints FEAT-0001 because earlier features remain `planned`; the operator picks the pack-and-grant slice explicitly.

| FEAT | Name | Blocked by |
|---|---|---|
| FEAT-0058 | Host SDK pack-and-grant | FEAT-0052, FEAT-0053 |
| FEAT-0059 | Daemon JSON-lines + diagnosis | FEAT-0058, FEAT-0042 |
| FEAT-0060 | Default host retry none/read | FEAT-0058, FEAT-0052 |
| FEAT-0061 | Nested Mission invoke | FEAT-0055, FEAT-0058 |
| FEAT-0062 | Listing axes + instance health | FEAT-0058, FEAT-0051 |
| FEAT-0063 | Thin kit-journey fixtures | FEAT-0058..0062, FEAT-0056 |

## Authority to cite in epics

- Rider: `_docwork/riders/pack-and-grant-kit-2026-09-23.md`
- Brief: `_docwork/pack-and-grant-increment-brief.md`
- ADR: `docs/decisions/ADR-0025-pack-and-grant-kit.md`
- Scenarios: SCN-0023..SCN-0027
- Ledger: DEC-0452..DEC-0468
- Honesty: inspect `integration@34c148b` (DEC-0465); parent freeze `270e992` for ADR-0024 original Decision (DEC-0450); fixtures not e2e (DEC-0286)

## Do not

- Mint a sixth COMP or a new CT
- Fill GAP-0081 chrome or GAP-0100 dashboard (out-of-scope as kit holes; UI is not designed)
- Invent the retry ceiling number (GAP-0108 answered as design: registry row, no number this sitting)
- Claim `caller_kind` / optional authoring instance / daemon JSON-lines exist at `34c148b`
- Claim envelope/grant/`product_session` types are absent at `34c148b`
- Rewrite ADR-0024 Decision or the 2026-09-16 QML fold
