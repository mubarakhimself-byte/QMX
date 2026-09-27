# QMX final focused architecture closure — 24 September 2026

**Verdict: ready for one integrated Documentation Factory pass.**

C1 and C2 are closed at the architecture-document gate. This is a focused direct closure review of the latest Grok amendment, building on earlier joint reviews; no new independent subagent gate or application runtime test is claimed.

## Closure evidence

| Finding | Result | Evidence |
| --- | --- | --- |
| C1 lost host-control recovery | Closed. Stopped-daemon recovery uses the owning OS user rather than the lost token. A one-shot daemon recovery entry acquires the writer lock and updates the fingerprint; QMB does not write sqlite. Operator identity and journals survive. Normal token rotation remains separate. | Backend HOST-LIFECYCLE.md trust-root and recovery sections, T-H-01..04; spine AD-6/AD-17; AM-03/AM-10; UI BOOTSTRAP-AND-AUTH.md section 12; T-BE-27..29. |
| C2 renewal versus origin revoke | Closed. Origin revoke is a journal-sequence barrier. Renew first then revoke invalidates the new proof; revoke first then renew refuses. Single-record revoke has explicitly narrower scope. Fresh pairing after the barrier remains possible. | Backend PAIRING-AND-ADMISSION.md lifecycle table, T-P-11..14; spine AD-4; UI bootstrap revoke verbs; T-BE-30/31. |

The previous J3/J4 contracts are unchanged. J5 gains the requested explicit qualification: registered authenticated destination control connection plus a reachable allowed source; no inter-daemon discovery or relay is claimed. The remaining UI edit is confined to BOOTSTRAP-AND-AUTH.md. Storyboard layouts and the frontend stack remain unchanged.

## Validation and scope

Both architecture spine lints pass with zero findings. Preserved 93 candidate files in evidence with SHA-256 manifest and amendment diff. Reviewed the C1/C2 closure map, actual host and pairing rules, affected spine/amendment/dependency/trace references, UI reconciliation and Grok's gate summary. Grok's internal reports are supporting evidence, not a substitute for these direct checks.

One non-blocking wording cleanup belongs in Documentation Factory: AM-10's generic running-daemon token requirement should explicitly cite AD-17/HOST-LIFECYCLE's narrowly defined OS-owner stop exception when the token file is missing or unreadable. The controlling behavior is already specified; do not interpret this as a new broader unauthenticated stop path.

Readiness here means the reviewed architecture packets can be reconciled into implementation documentation. It does not mean the software exists, security tests have run, or a clean installation works. Existing epics remain planned requirements until implementation evidence establishes otherwise.

## Handoff

Use both candidate packets together with their parent-amendment and dependency maps, original UI evidence and these review closures. Documentation Factory should preserve valid existing documentation and epic IDs, incorporate named amendments explicitly, avoid duplicating Epics 60–65, and carry unexecuted traces into downstream acceptance work. Then proceed to coordinated epic/story amendments and additions, followed by factory execution through the user's established workflow.

No candidate files, parent contracts, backlog, application code, branches or active factory inputs were changed by this review. Documentation Factory has not been started.
