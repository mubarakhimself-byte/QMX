# UI host plus backend-delta — epics-and-stories handoff (2026-09-27)

Documentation Factory Stage 9 folded `architecture-QMX-UI-2026-09-23` plus `architecture-QMX-UI-BACKEND-2026-09-24` into `docs/` on 2026-09-25 (ADR-0026). This sitting wrote the BMAD epic/story slice. It did **not** launch a factory lane, reopen architecture, or re-run Documentation Factory.

## Artifact

`_bmad-output/planning-artifacts/epics-UI-2026-09-27.md`

8 epics (66–73), 36 stories, FR-UI-01..56, UX-DR-UI-01..21. Phase-1 `epics.md` and earlier slice files stay untouched.

## Inventory

```text
python C:\Users\Mubarak\.agents\skills\documentation-factory\scripts\validate_inventory.py --root C:\Users\Mubarak\Desktop\QMX --handoff FEAT-0064
```

`--next` still prints FEAT-0001 because earlier features remain `planned`. The operator picks this slice explicitly.

| Epic | FEAT | Wave | Weight | Lane | Destination |
|---|---|---|---|---|---|
| 66 | FEAT-0064 chrome | 12 | H | `/run-ui-epics 66` | `ui-integration` |
| 67 | FEAT-0065 host lifecycle | 10 | H | `/run-epics 67` | `integration` |
| 68 | FEAT-0066 pairing | 11 | H | `/run-epics 68` | `integration` |
| 69 | FEAT-0067 mailbox field | 12 | H | `/run-epics 69` | `integration` |
| 70 | FEAT-0068 artifacts | 12 | H | `/run-epics 70` | `integration` |
| 71 | FEAT-0069 drafts | 13 | H | `/run-epics 71` | `integration` |
| 72 | FEAT-0070 PackUiRequest | 12 | H | `/run-epics 72` | `integration` |
| 73 | FEAT-0071 cancel | 19 | H | `/run-epics 73` | `integration` |

Independent planned epics 60–65 continue. Do not reverse the two factory destinations.

## Authority

- Rider: `_docwork/riders/ui-and-backend-delta-2026-09-25.md`
- Brief: `_docwork/ui-backend-increment-brief.md`
- ADR: `docs/decisions/ADR-0026-ui-host-and-backend-delta.md`
- Scenarios: SCN-0028..SCN-0035
- Ledger: DEC-0469..DEC-0510
- Honesty: inspect `integration@34c148be` (DEC-0507); parent freeze `270e992` for ADR-0024 original Decision; fixtures not e2e (DEC-0286)

## Do not

- Run bare `/run-epics` (drains FEAT-0001)
- Run bare `/run-ui-epics` without naming **66** (this file also contains backend epics 67–73)
- Merge UI chrome to `integration` or backend work to `ui-integration`
- Touch `main`
- Mint COMP-UI, a sixth COMP, or a new CT
- Mint TTL or `stage_max_bytes` numbers (GAP-0109, GAP-0110)
- Pin CodeMirror vs Monaco (GAP-0111), require Tauri in v1 (GAP-0112), ship trading-ticket chrome (GAP-0113), or expand `qma-ui-contract` past the stub (GAP-0114)
- Duplicate FEAT-0058..0063 / Epics 60–65
- Hold Epic 60.1; nest `copilot_profile` in PackUiRequest
- Map cancel to `stop_run`
- Claim live CT-40 / pairing / `qmb host` / Svelte host exist at `34c148be`
- Claim envelope/grant/`product_session` types are absent there

## Paste-ready factory prompts (later sitting)

Chrome:

```text
/run-ui-epics 66
```

Backend (pick unblocked units; 67 is the first host-lifecycle unit once FEAT-0042 is available):

```text
/run-epics 67
```

Do not start those from this planning sitting.
