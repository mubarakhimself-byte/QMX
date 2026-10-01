# Stage 7 pass-1 consistency review — pack-and-grant kit (2026-09-23)

Date: 2026-09-23. Reviewer: grok-4.6 (fresh; did not draft). Scope: increment docs listed in `_docwork/pack-and-grant-increment-brief.md` against ledger DEC-0452..DEC-0467, `_docwork/gaps.yaml` GAP-0081/0100/0093/0096 and GAP-0101..GAP-0108, and the Pass 1 checklist (normative trace, no two-doc disagreement, ADR-0024 original Decision unrewritten, wiring honesty, dead list, deferred chrome). No production code. No architecture invention.

Authority read: `_docwork/ledger.yaml` (DEC-0452..DEC-0467 and parent DEC-0421/0437/0442/0450/0286), `_docwork/gaps.yaml` (GAP-0081/0100/0093/0096/0101..0108), `_docwork/pack-and-grant-increment-brief.md`, `docs/` (ADR-0025, SCN-0023..0027, SCN-0019 honesty note, ADR-0024 follow-up, ADR-0020 follow-up, constitution L7, AGENTS, qma-core/qma-daemon/qma-wire/qmb, CT-40, logging-spec, glossary, gap-report, overview, stack, dependencies notes, changelog, index, traceability). Did not read architecture sitting transcripts, chunks, or `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/` body.

## Desk-fix (2026-09-23, same session)

Majors 1–4 applied: CT-40 pack-and-grant named-amendment invariant; `qma-wire` FM-12 duplicate renumbered to FM-14; GAP-0101..0108 split under pack-and-grant heading; wire/daemon Related SHA-qualified; GAP-0081/0093/0096 public cells updated; SCN-0024 chrome wording; index 141/93; frontmatter DECs on increment docs. Re-lint CLEAN.

## Verdict: FAIL-with-amendments (as filed; desk-fixed same session)

**No critical / no blocking vocabulary disagreements.** Across the fold, `caller_kind` is `user | agent | workflow`; authoring may omit `app_instance_id` and app-use may not; `failure_class` is `grant | workflow | view | dependency | host` (`view` = wire DTO, not widget, not invoke); envelope `instance_id` remains required on invoke; no third `ProductSessionProfile`; no sixth COMP; no new CT id; live-graph merge refused; json-render / MCP Apps unpinned; GAP-0081 chrome and GAP-0100 dashboard stay deferred; ADR-0024 original Decision is dated-follow-up only; inspect SHA is `34c148b` CONNECT vs ABSENT with parent freeze `270e992`; fixtures are not e2e (DEC-0286).

Amendments are required before Pass 1 is green: CT-40 never gained a pack-and-grant named-amendment invariant; `qma-wire.md` has two different FM-12 rows; kit gaps GAP-0101..0108 sit under the Workflows heading; wire/daemon Related footers still say envelope/grant/`product_session` are absent without the `34c148b` CONNECT qualifier.

## Hunt results (checklist)

| # | Check | Result |
|---|---|---|
| 1 | New normative sentences trace to DEC-0452..DEC-0467 and say what the entry says | **PASS** on ADR-0025, SCN-0023..0027, component pack-and-grant sections, glossary kit nouns, L7 annotation, AGENTS hard rules, overview honesty. **FAIL (narrow)** — CT-40 has only a `wiring_status` comment, not an invariant; SCN-0024 Then (2) cites DEC-0454/0442 for a `failure_class` diagnosis sentence that is DEC-0456. |
| 2 | No two docs disagree on `caller_kind`, optional authoring instance, `failure_class`=`view` not widget, envelope `instance_id` required, no third profile, no sixth COMP, no new CT | **PASS** |
| 3 | ADR-0024 original Decision not rewritten | **PASS** — 2026-09-23 follow-up only; original AD-8/AD-24 bullets unchanged |
| 4 | Honesty: `34c148b` CONNECT vs ABSENT; `270e992` parent freeze for ADR-0024 original; DEC-0286 fixtures ≠ e2e | **FAIL (narrow)** — body sections are SHA-qualified; `qma-wire.md` / `qma-daemon.md` Related footers and gap-report GAP-0093/0096 recommendation cells are not |
| 5 | Dead list: no sixth COMP, no live-graph merge, adapters unpinned | **PASS** |
| 6 | GAP-0081 / GAP-0100 still deferred | **PASS** (status). **FAIL (narrow)** — YAML GAP-0081 note was updated 2026-09-23; gap-report QMA table row was not |
| 7 | Frontmatter `decisions` include DECs the body cites | **FAIL** — systematic miss of DEC-0452..0467 on AGENTS, qma-core, qma-wire, qma-daemon, ADR-0024, index, gap-report, overview, CT-40, logging-spec, SCN-0019 |

## Findings

### 1. major — `docs/contracts/ct-40-qma-wire-envelope.yaml`

**Finding.** DEC-0464 requires an additive CT-40 family annotation for `caller_kind` (no new CT number) until a format mint under FEAT-0058. ADR-0025 Consequences says public kit types (`caller_kind`, `failure_class`, optional authoring `app_instance_id`, `selected_refs` kind `instance_id`, `copilot_profile`) are specified in prose **and CT usage annotations**. The Workflows named amendment (DEC-0449) landed as a dedicated `invariants` bullet (`WORKFLOWS NAMED AMENDMENT`). Pack-and-grant only added a `wiring_status` comment. `invariants:`, `schema.fields`, `provenance_note`, `decisions:`, and `gaps:` do not carry `caller_kind`, closed `failure_class`, envelope `instance_id` remains required, or GAP-0101/0105. An implementer reading the contract body (the load-bearing list) never sees the named parent AD-24 amendment.

**Contradicts.** DEC-0464; ADR-0025 Consequences; the Workflows fold pattern on the same file; `docs/architecture/dependencies.yaml` COMP-QMA-WIRE notes (“caller_kind and diagnosis failure_class are additive CT-40 usage annotations”).

**Suggested fix.** Add a `PACK-AND-GRANT NAMED AMENDMENT (2026-09-23)` invariant matching the Workflows bullet: closed `caller_kind` `user | agent | workflow`; envelope `instance_id` remains required; diagnosis `failure_class` `grant | workflow | view | dependency | host` with `view` = wire-DTO mount/stale/unhealthy, not an invoke; no new CT number; fields are usage annotations not `schema.fields` until FEAT-0058; CONNECT types exist at `34c148b`, `caller_kind` / kit `failure_class` absent (DEC-0464, DEC-0456, DEC-0465, GAP-0101, GAP-0105). Append those DECs/GAPs to frontmatter. Do not mint `schema.fields`.

### 2. major — `docs/components/qma-wire.md` (Failure modes)

**Finding.** Two distinct refusal laws share `FM-12`. Pack-and-grant inserted FM-12 (json-render/MCP) and FM-13 (`caller_kind`) **above** the existing Workflows product_session CAS row, which is still numbered FM-12.

```
| FM-12 | **[Pack-and-grant 2026-09-23]** A json-render catalog entry adds fields...
| FM-13 | **[Pack-and-grant 2026-09-23]** A public call omits `caller_kind`...
| FM-12 | **[Workflows 2026-09-19]** A `product_session` mutate omits `expected_revision`...
```

Citing FM-12 is now ambiguous.

**Contradicts.** Component-spec house rule (one FM id, one condition). Not a ledger disagreement — a fold defect in an increment-touched table.

**Suggested fix.** Keep pack-and-grant as FM-12 / FM-13. Renumber the Workflows CAS row to FM-14. Do not merge the two conditions.

### 3. major — `docs/gap-report.md` (Workflows deferred section)

**Finding.** Heading is `## Deferred by the Workflows construction-kit fold (2026-09-19) — 9`. The table then continues through GAP-0101..GAP-0108 (pack-and-grant, DEC-0452..0467). There is **no** `## Deferred by the pack-and-grant kit fold (2026-09-23) — 8` section (`grep` of that heading: no matches). Intro bullet and navigation table correctly split the two folds; the detailed catalog does not. Heading count “9” is false (17 rows). Kit gaps are attributed to the 2026-09-19 sitting.

Separately, navigation claims “GAP-0081/0100/0093/0096 notes updated in place”:

- `_docwork/gaps.yaml` GAP-0081/0093/0096 **were** updated 2026-09-23 (`34c148b` CONNECT; authoring `app_instance_id` optionality; chrome still deferred).
- gap-report GAP-0100 recommendation **was** updated.
- gap-report GAP-0093 / GAP-0096 recommendation cells still say only “Absent at `270e992`” with no `34c148b` CONNECT qualifier.
- gap-report QMA table GAP-0081 still stops at the 2026-09-19 Workflows chrome note.

**Contradicts.** DEC-0461 (kit spine is a child of Workflows, not Workflows itself); DEC-0465 (do not claim envelope/grant/`product_session` types are absent at `34c148b`); changelog “notes on GAP-0081/0100/0093/0096 in place”; the same page’s intro/nav rows.

**Suggested fix.** Split GAP-0101..0108 into a pack-and-grant deferred section (8 rows, DEC-0461, inspect `34c148b`). Leave GAP-0092..0100 under Workflows — 9. Copy the YAML 2026-09-23 sentences into GAP-0081 / GAP-0093 / GAP-0096 public cells. Keep all four **deferred**.

### 4. major — `docs/components/qma-wire.md` (Related); also `docs/components/qma-daemon.md` (Related)

**Finding.** Pack-and-grant body sections on both specs are SHA-honest (`34c148b` CONNECT vs ABSENT; parent freeze `270e992`; DEC-0286). The Related footers were not folded:

- `qma-wire.md` Related still: “`InvocationEnvelope` / `GrantRecord` absent (`GAP-0096`)” and “`product_session` runtime absent (`GAP-0093`)” with **no SHA**. It does not name ADR-0025, DEC-0464/0465, or SCN-0023..0027. Workflows DEC list stops at DEC-0450.
- `qma-daemon.md` Related still: “`product_session` runtime absent (GAP-0093)” unqualified; ADRs stop at ADR-0024; no pack-and-grant DEC paragraph despite FM-26..FM-28 in the same file.

`qma-core.md` Related **was** updated (GAP-0096 “absent at `270e992`; types exist as fixtures at `34c148b`”). Three QMA specs now disagree in the footer an implementer actually copies.

**Contradicts.** DEC-0465 (“Do not claim envelope/grant/`product_session` types are absent at `34c148b`”); `qma-core.md` Related; ADR-0025 / overview honesty blocks.

**Suggested fix.** Mirror `qma-core.md`: GAP-0093/0096 remain deferred; types/fixtures CONNECT at `34c148b`; class/test ≠ e2e; `caller_kind` / optional authoring instance / daemon JSON-lines ABSENT. Add ADR-0025 plus DEC-0452..0467 (owner-scoped). Keep `270e992` only as parent-freeze absence for ADR-0024 original text.

### 5. minor — frontmatter `decisions` vs body (systematic)

**Finding.** Bodies cite DEC-0452..0467; YAML `decisions:` lists often stop at DEC-0451 or earlier.

| Doc | Frontmatter ends | Body cites pack-and-grant |
|---|---|---|
| `docs/AGENTS.md` | DEC-0451 | hard rules DEC-0452..0467 |
| `docs/components/qma-core.md` | DEC-0450 | DEC-0452..0465 |
| `docs/components/qma-wire.md` | DEC-0450 | DEC-0456/0459/0461/0462/0464/0465 |
| `docs/components/qma-daemon.md` | DEC-0450 | DEC-0452..0465 |
| `docs/decisions/ADR-0024-workflows-construction-kit.md` | DEC-0451 | follow-up DEC-0461..0465 |
| `docs/index.md` | DEC-0451 | ADR-0025 / SCN-0023..0027 |
| `docs/gap-report.md` | DEC-0451 | DEC-0452..0467 |
| `docs/architecture/overview.md` | DEC-0450 | DEC-0453..0465 |
| `docs/contracts/ct-40-qma-wire-envelope.yaml` | DEC-0450 | wiring_status DEC-0464/0456/0465 |
| `docs/lenses/observability/logging-spec.md` | DEC-0286 | DEC-0456/0465 |
| `docs/scenarios/SCN-0019-app-use-change-request.md` | DEC-0450; `verified: 2026-09-19` | honesty note DEC-0463/0465 |
| `docs/components/qmb.md` | DEC-0450; `verified: 2026-09-19` | DEC-0453 |

Glossary and changelog **did** add kit DECs. Constitution L7 frontmatter includes DEC-0452/0453/0461/0462.

**Contradicts.** House citation protocol (frontmatter lists DECs the body uses). Not a law disagreement.

**Suggested fix.** Append the DECs each body actually cites. Set SCN-0019 and qmb `verified: 2026-09-23`.

### 6. minor — `docs/index.md` (count + history paragraph)

**Finding.** “The corpus contains 140 files: 92 Markdown documents and 48 YAML artifacts.” Disk under `docs/` is **93** Markdown + **48** YAML = **141**. The long history paragraph still ends at the 2026-09-19 Workflows sitting; ADR-0025 and SCN-0023..0027 are linked later but never named in that paragraph.

**Contradicts.** The same page’s ADR/SCN lists (ADR-0025, SCN-0023..0027 present). Prior fold’s count-drift class.

**Suggested fix.** Set 141 files / 93 Markdown / 48 YAML (re-count if another file lands). One sentence in the history paragraph: 2026-09-23 pack-and-grant kit (ADR-0025, DEC-0452..0467, SCN-0023..0027, no new COMP, no new CT).

### 7. minor — `docs/scenarios/SCN-0024-optional-copilot-headless.md`

**Finding.** Given: “Optional in-app panel, when present, is **chrome** over an app-use `psess:`.” GAP-0103 / AGENTS / ADR-0025: the optional panel is a **contract**, **not GAP-0081 chrome**. Then (2) mentions `failure_class` diagnosis but cites only DEC-0454 and DEC-0442 (apply/mint law). Diagnosis class is DEC-0456.

Not a third-profile or chrome-fill — the sentence also says “not a second copilot product” — but “chrome” here collides with the deferred GAP-0081 noun.

**Contradicts.** DEC-0456 (citation); GAP-0103 note; DEC-0467 (GAP-0081 chrome later).

**Suggested fix.** Say “optional in-app panel is a contract surface over an app-use `psess:`, not GAP-0081 chrome.” Cite DEC-0456 on the diagnosis clause.

### 8. minor — `docs/scenarios/SCN-0019-app-use-change-request.md`

**Finding.** Honesty paragraph is correct (parent freeze `270e992` absence; DEC-0463 does not relax app-use; types/fixtures at `34c148b`; not e2e). Branch E still only forbids claiming runtime at `270e992`. Frontmatter `verified: 2026-09-19` and `decisions:` omit DEC-0463/0465.

**Contradicts.** None on law. Completeness vs SCN-0023..0027, which add a `34c148b` “not executed proof” branch.

**Suggested fix.** Keep Branch E. Add Branch F: treating fixtures at `34c148b` as e2e (DEC-0465, DEC-0286). Update frontmatter.

## Checks that passed (do not re-open)

- **caller_kind** closed `user | agent | workflow` in ADR-0025, SCN-0023/0025, qma-core, qma-wire, glossary, AGENTS, overview. Absent at `34c148b` (GAP-0101). No fourth kind.
- **Optional authoring `app_instance_id`** + exactly-one `selected_refs` kind `instance_id` on invoke; app-use still required; no third profile (DEC-0463). SCN-0023, qma-daemon, ADR-0024 follow-up, glossary `product_session` agree.
- **Envelope `instance_id` remains required** on every invoke (DEC-0464). SCN-0023 Branch C forbids optional envelope instance.
- **`failure_class` uses `view` not `widget`.** Glossary, SCN-0027, qma-wire, qma-daemon, logging-spec, AGENTS, ADR-0024 follow-up, ADR-0025 all use `grant | workflow | view | dependency | host` with the wire-DTO gloss.
- **No sixth COMP / no new CT.** L7 annotation, ADR-0025 preflight, overview, stack, dependencies notes, changelog. CT-40 remains the family; no CT-52 file.
- **ADR-0024 original Decision** (AD-1..AD-31 bullets, Options, cheap-veto A1–A6) unchanged. Follow-up starts at “Follow-up — 2026-09-23”. Original Context still freezes inspect at `270e992`.
- **ADR-0020** 2026-08-29 Decision stands; 2026-09-23 follow-up only (host not owner, JSON-lines ≠ journals, one copilot).
- **Honesty CONNECT at `34c148b`:** InvocationEnvelope, GrantRecord, `product_session` types as fixtures — ADR-0025, overview, SCN-0019, glossary, qma-core/daemon pack-and-grant sections, gaps.yaml GAP-0093/0096 notes.
- **Honesty ABSENT at `34c148b`:** `caller_kind`, optional authoring instance, daemon JSON-lines, kit `failure_class`, default host retry loop, nested Mission invoke as first-class, `copilot_profile` — SCN-0023..0027 branches, ADR-0025, AGENTS.
- **DEC-0286** restated wherever CONNECT is claimed.
- **Dead list:** live-graph merge refused (SCN-0025, qma-daemon FM-27, qma-core FM-16); adapters unpinned (stack, qma-wire, ADR-0025 kit AD-8); no QMB/QML core fork; do not extend `qmn/FAILURES.md`.
- **GAP-0081 / GAP-0100** status remains `deferred`. GAP-0100 recommendation restates later UI. Do not treat the optional panel as filling chrome.
- **ADR-0023** stays `status: provisional`.

## Suggested Pass 1 gate

Treat as **not green** until findings 1–4 are amended (CT-40 invariant, FM-12 collision, gap-report kit section, Related honesty). Findings 5–8 are house-keeping and may ride the same desk-fix. No blocking (critical) kit-law contradiction was found.
