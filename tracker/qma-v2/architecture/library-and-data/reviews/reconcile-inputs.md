# Reconcile inputs — what each load-bearing source asked for and whether it landed

Reviewer: this run, inline, one pass per input.

## 26-operator-rulings (binding)

| Ruling | Landed in | Gap |
| --- | --- | --- |
| 9 archived never deleted | AD-6, DOC-CHANGES (DEC-0443) | none |
| 22-25 one engine, runs anywhere | AD-15, HLD §6 | none from the Library side |
| 24 harness untouched | LLD §7 adds table rows only; §13 | none |
| 28 Library stores everything; UI and backend must match | AD-1, AD-3 roster, AD-17 | **quiet item:** "relationships" and "logic" were called out as missing in the UI (file 23); both are kinds/relations now. "Bot cards": `bot-card` kind. |
| 31 Board saved | `board` kind; DOC-CHANGES DEC-0417 | none |
| 32/40 desktop app | OPEN-1 recommendation, AD-11 | none |
| 41 previews, detail views, agents, git-like, backups | AD-17, AD-9, AD-7, AD-10/16 | none |
| 42 bucket, PC low on space | AD-10 tiering, AD-16 | none |
| 43 intermediary, DevOps layer | AD-11..14 | none |
| 44 one agent is a workflow | HLD §6 note 4 | none |
| 38 do not re-raise provider risk | not raised; CLIProxy section marked for removal from P21 README only | none |

## Task brief (the coordinator's scope list)

Every bullet maps to the Capability map in the spine. Two quiet requirements checked: "comparison view" → the `merge-conflict` object; renderer `diff` must be added (adversarial 8). "Sources (papers, videos)" → `source` kind with transcript blob; video ingest itself is a workflow, noted as out of scope in HLD.

## 23-ui-clickthrough

| Quiet requirement | Landed |
| --- | --- |
| "New version … starts as a draft; the current one stays" | `put` on `refs/variants/*` or an agent branch then merge |
| "Import a file" needs the daemon | `POST /v1/blobs` + `put` |
| "Open file" | `get(blobs="fetch")` |
| Collections in localStorage | `collection` kind |
| Copilot artifacts never reach the Library | `note`/`artifact` objects authored `agent:<session>`; "Explain it as" outputs carry `explains → source` |
| "Used in" is place-based, no item graph | `walk` over typed edges; AD-17 "Used in" is the neighbourhood |
| Apps screen and Library apps disjoint | one `mini-app` / `mini-app-instance` kind |

## 24-docs-board-library-workflows

Every row of its §2c mismatch table has a DOC-CHANGES row. Its §5 corrections to 05/10/12/19 are carried (DOC-CHANGES last row).

## 25-hermes-n8n-loadbalancer

Items 3 (n8n-shaped JSON document), 5 (pinned data, tested), 16 (one store) are addressed in HLD §6 and the Interface notes; items 7-15 (balancer, scheduler) are the engine architect's.

## 14-folders-miniapps-browser

`pending/` agent-written edits → agent branches + merge (AD-7); semver + content hash → `fp1` objects; archive with reason → AD-6; the plugin folder as the mini-app bundle → `mini-app` blob `bundle.tar` + parsed manifest fields. **Add one sentence to HLD §3 or LLD §3 saying so.**

## DESIGN.md (harness)

Protected paths do not cover `<home>/library/checkout/` (checked against the listed gate patterns: Claude homes, `settings.toml`, plugin folder, `qmx/*` names). The per-chat in-process `qmx` MCP server gives the session id for the principal. Effects reused unchanged. No harness change beyond table rows.

## Clipping

All five lessons present in AD-8 and LLD §5-6: parse-not-extract, model never emits ids, dense re-orders only, deterministic gates before generation, answers cite ids. The clipping's "verifier validated on its own benchmark" (gate six) is the only part not carried: an entailment gate after generation is a copilot-skill concern, not a Library one; noted here, not in the spine.

## Code at hp17

Kept: blob write-once by hash, hash-verified reads, `BEGIN IMMEDIATE` + lock, FTS5, memo key, `ResultsStore` layout, `ComputeProvider`, `credentials_scope` over stdin, redaction + env scrub, rclone remotes, Litestream only where it already is. Replaced: `items` mutable rows, free `kind`, free `relation`, GitHub weekly for `library.db`, the QMB projection.

**Verdict: inputs reconciled; two sentences to add (renderer `diff`; mini-app bundle mapping from file 14).**
