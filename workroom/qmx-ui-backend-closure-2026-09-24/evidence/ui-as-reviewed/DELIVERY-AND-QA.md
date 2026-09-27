---
name: Delivery and verification
sitting: architecture-QMX-UI-2026-09-23
---

# Delivery and verification

## Parallel streams (proposal)

| Stream | Base | Owns | Must not |
| --- | --- | --- | --- |
| Backend `integration` | `34c148b` | Wire server, `caller_kind`, `list_mailbox`, `cancel_job`, `stage_artifact`, `qmb host`, pairing, JSON-lines, health(), retry | UI chrome |
| UI integration | cut from same `integration` SHA | `apps/qmx-ui`, adapters | Python COMP rewrites |
| Combined candidate | merge of both when contracts match | Installer or browser+daemon smoke | Silent drift |

Recommended UI worktree path (not created here): `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui-integration`. Do not reuse `.worktrees/ui`.

Cadence: UI consumes **named** wire/query additions. If UI needs a method, it is a backend story on `integration`, not a UI BFF. Fixes flow by SHA pin in the UI client (`expected_qma_api` range already on pack manifests).

`main` moves only by the operator’s squash-merge of a **tested** candidate.

Independent backend code review is a **separate** activity. This sitting does not start it.

## Compatibility baseline

Pin UI client against inspect SHA plus the kit amends it requires. At first UI story, record: envelope fields present/absent (`caller_kind`), whether `DaemonProcess` still discards bytes, whether HTTP query exists.

## Evidence classes (keep separate)

| Class | Tool |
| --- | --- |
| Static | ruff/pyright on Python; svelte-check on UI |
| Unit / component | pytest; Svelte component tests |
| Contract | envelope/grant/view fixtures |
| Browser interaction | Reticle `reticle_act_and_wait` / `reticle_assert` only as pass |
| Failure injection | J-UI-06..09 |
| Performance | TRACE-MATRIX workloads; budgets at scaffold-plus-slice gate | unexecuted |
| Installed product | clean-machine start, update, rollback — Reticle cannot supply this alone |

`unknown` Reticle verdict is not a pass.

## Paper trading

Only where a capability executes trades or materially affects trading/risk. Data tools, headless utilities, and non-trading ML use functional/operational evaluation.

## Experiments this sitting

No isolated checkout, daemon start, install, or Reticle run. Stack pins web-checked 2026-09-23. Isolated-scaffold gate (lockfile, svelte-check, production build) remains **unexecuted**.

## Clean-machine unknowns

Bundled vs external Python, model runtimes, provider/proxy, Windows installer, VPS SSH tunnel UX. Named in `research/14-firstrun-packaging-placement.md`. Do not claim development-machine success transfers.
