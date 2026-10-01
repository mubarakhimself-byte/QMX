# Reviewer gate summary — architecture-QMX-UI-2026-09-23

**Date:** 2026-09-23  
**Lint:** `lint_spine.py` clean (0 findings) after the fix pass.  
**Seats:** rubric, adversarial, parent-consistency, currency, reconcile-inputs.

## Verdict after fixes

Independent seats originally said **holes / return for amendment / PASS with Medium / PASS / ready-for-Codex-not-Factory**.

Clear autofixes applied to the spine and companions:

| Finding | Fix |
| --- | --- |
| Home vs Copilot vs Settings | local AD-3/AD-4: one main-copilot family; Settings is destination chrome |
| Hedged “Proposal default” in ADOPTED rules | Frozen: artifact-fp1 uploads; Library as rail destination; v1 browser+daemon |
| Unique invoke issuer unnamed | `src/lib/host/dispatchInvoke`; refuse pack invoke until `caller_kind` is accepted |
| Graph Run as client MissionCompiler | Graph Run is template `start` via dispatchInvoke |
| Reconnect cursor fork | parent AD-29 `(resume_cursor, cursor_generation)` plus `wire.attach` `since_seq` plus `JobHandle.reattach` |
| UI Retry as second invoke | local AD-13: Retry is not a second dispatchInvoke |
| bits-ui 1.x stale | 2.19.3 |
| UX-08 missing | local AD-17 + EXPERIENCE §6 |
| AD numbering collision in tables | Inherited and capability map prefix `parent` / `kit` / `local` |
| Tauri close vs parent AD-17 | Window close is detach; Stop local runtime is explicit |

Unresolved (named, not silent): live JSON-RPC server is a **backend add**; `caller_kind` absent at `34c148b` blocks UI pack invoke until that amend; Tauri installer deferred; UX-06/UX-10 chrome still thinner than 03 asked (constraint law landed; screens later).

**Codex readiness:** ready for focused review. **Documentation Factory:** not started; operator launches it in a fresh session after Codex.

## Files

- `reviews/review-rubric.md`
- `reviews/review-adversarial.md`
- `reviews/review-parent-consistency.md`
- `reviews/review-currency.md`
- `reviews/reconcile-inputs.md`
