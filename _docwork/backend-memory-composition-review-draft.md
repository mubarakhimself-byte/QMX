# Independent bounded memory composition review

Reviewed 2026-10-04. Candidate HEAD: `4400ac05cd863eee74a683a1c96f3b4ea3d496b1`, following `99c47991d19b67e00adc7524f177aeb67c8bb671`. Scope: reviewed memory patch preservation, integration with admitted research requests, optional-dependency behavior, and pending packaging/documentation/runner changes. No runtime/shared source, original checkout or dependency environment was edited. No credential reads, model/embedding calls, network activity, publication, trading or deployment were performed by this reviewer. The sole independent executable probe was a local import check that deliberately blocks optional extraction imports.

**Verdict: approve the bounded runtime composition and the reviewed optional-extra/lock changes. No actionable runtime integration defect found. One CI integration prerequisite remains before this is a reproducible full nested gate: explicitly install the optional extraction extra for that test environment and retain it during test execution.** This is a bounded memory milestone, not whole-platform acceptance.

## Exact source equivalence and ownership

Reviewed source commit `916832bdbc0a28aec00d8a22ca3b8a239c8ba564` and applied candidate `4400ac05cd863eee74a683a1c96f3b4ea3d496b1` produce the identical stable patch ID:

`f3ad8a9621136a962911f0b269913d1872c59992`

`git diff 916832bdbc0a28aec00d8a22ca3b8a239c8ba564 HEAD` returned no changes for the three runtime modules and three new memory test files. Comparing `99c47991` to candidate HEAD also returned no changes for shared `process.py`, `provider_config.py`, `domain_tools.py`, or `research_workflow.py`. The existing workflow gains typed behavior through its already established `ScopedResearchMemory` facade; there is no competing startup/wire authority implementation.

At review time the only uncommitted files were the daemon optional-extra manifest, nested lock, two documentation pointers, repaired `MEMORY_INTEGRATION_DRAFT.patch`, and integration runner. The runtime cherry-pick was clean and unchanged. The revised illustrative patch passes `git apply --reverse --check` against the currently applied manifest/documentation pointers. It intentionally describes those additions, not the generated lock.

## Runtime and lifecycle review

* **Authority remains host-owned.** Research namespace derives from principal, application, profile, current authority binding and exact corpus pins; it is independent of invocation/thread identity. Separate `ActorMemoryScope` requires explicit host actor/principal/collection/source identity but is not automatically joined to actor routing. Memory candidates cannot retarget the provider namespace, source, snapshot, locators or authority binding. Live validation is retained before storage, retrieval and disclosure.
* **One canonical writer and atomic state.** `JournalMemoryProvider` persists bounded typed revisions through the existing daemon journal. The SDK `InMemoryStore` is rebuilt as a disposable search projection, not a second durable owner. Shared per-journal locks serialize local provider instances. A predecessor's superseded revision and successor admission enter one journal append; capacity refusal leaves existing state intact. Exact repeated admission is idempotent, and tombstones cannot be resurrected by reusing an ID.
* **Admission and hooks remain real.** `DurableMemory.admit` uses the existing CT43 gate, gate-computed confidence and before/after memory hooks. Proposals are not automatically canonical facts. Hooks cannot bypass the provider's source/authority checks. The provider API is trusted host infrastructure; this change does not install model-facing mutation tools or grant new wire operations.
* **Request context remains distinct.** The facade retains the workflow's existing summary field while canonical storage records typed memory and supersession history. The workflow continues to freeze cross-job recall into `delegation_input` before entering the resumable child graph. Later canonical memory changes do not replace that interrupted invocation snapshot. Terminal request reads do not repeat inference or retained effects.
* **Legacy behavior is conservative.** Exact-scope historical summary recall is read-only and checks admitted state plus source/authority pins. Once typed state exists, legacy fallback stops even when no active typed summary remains; invalidation cannot resurrect historical bytes. Legacy records remain in the journal rather than being silently migrated or deleted.
* **TTL, search and context remain bounded.** Active heads alone enter retrieval; terminal or expired records remain available only through host-authorized history. Current canonical heads/TTL are rechecked after indexing and tokenization. Context budgets omit whole records without modifying memory. Semantic search requires explicit injected embeddings and dimensions; ordinary recall does not create embeddings or call a model.
* **Extraction remains opt-in.** No production module imports `memory_extraction` or constructs `LangMemExtractor` through startup/request/skills/retain/recall paths. Constructor rejects model-name strings and requires an explicit `BaseChatModel`. Extraction validates the host binding before/after processing, imposes input/candidate bounds, proposes stable content-derived IDs and writes nothing. Separate admission is still required. This is not a paid-call count, wall-time, cancellation or semantic-truth guarantee for arbitrary injected models.

## Optional dependency and lock review

The new daemon extra contains exactly `langmem==0.0.30`, `trustcall==0.0.39`, and `dydantic==0.0.8`. It does not alter the nested workspace's default `dev`/`qma-runtime` groups or mandatory daemon dependencies.

Independent parsing of old/current package identities found **79 prior packages, 86 current packages, zero prior pin changes and zero removals**. Seven added packages are:

| Package | Locked version |
|---|---|
| dydantic | 0.0.8 |
| langchain-openai | 1.6.7 |
| langmem | 0.0.30 |
| openai | 3.24.0 |
| regex | 2026.9.29 |
| tiktoken | 0.14.0 |
| trustcall | 0.0.39 |

The new dependencies are reachable through the optional extra; ordinary daemon installation retains the existing mandatory dependency graph. The integrator's `evidence/memory-lock-audit.json` agrees with this result and records complete prior package-entry preservation except daemon optional metadata. Earlier failed offline resolution logs remain preserved; subsequent registry resolution records all 86 packages, and the isolated seven-package installation records the exact additions. The integrator's later `uv lock --check --offline` succeeds with 86 packages (`evidence/memory-lock-check.txt`). `evidence/pip-check-memory-locked.txt` reports no broken requirements. The earlier `pip-check-memory.txt` missing-langchain-openai report describes the previous incomplete overlay, not final locked-overlay evidence.

Independent absence probe: using the final memory-run interpreter and explicit candidate-first import paths, a `MetaPathFinder` raised `ModuleNotFoundError` for `langmem`, `trustcall`, and `dydantic`. Imports of `qma.daemon.process`, `scoped_memory`, and `durable_memory` succeeded, and none of those optional package names entered `sys.modules`. The loaded durable module path resolved inside this candidate. Output and exit 0 are preserved in `evidence/memory-review-default-import.txt`. This establishes ordinary runtime import behavior without the extraction packages; it does not claim a clean-machine installation or full test gate without extras.

## Material CI prerequisite

The nested `agents` CI job currently uses `uv sync --frozen`, then `uv run poe check`. `test_memory_extraction.py` intentionally constructs the released extractor without an optional-dependency skip. A default sync therefore leaves that new test without LangMem. This is a real environment integration prerequisite, not a reason to delete/skip the extraction tests or make extraction mandatory in the runtime.

Recommended nested test-only commands, from `qmx-agents`:

```text
uv sync --frozen --all-packages --extra memory-extraction
uv run --no-sync poe check
```

Alternatively repeat `--frozen --all-packages --extra memory-extraction` on the subsequent `uv run` command. The `--all-packages` selects the workspace daemon member that declares the extra; the root project itself declares none. `--no-sync` prevents subsequent default syncing from stripping the explicitly installed test extra. Local `uv sync --help` and `uv run --help` confirm the used switches. The integrator was notified and owns joining this setup with the separate reviewed quality/CI series. Candidate full-QMA runner invocations likewise must include the final locked optional dependency overlay in their recorded dependency paths. Neither changing default runtime groups nor lowering a gate is needed.

## Inspected evidence and acceptance limits

The integrator's first memory roster at `evidence/memory-6234316471de46948fd6bbeb84e1e7b5` reports **94 passed, no skips, one upstream Trustcall deprecation warning**. The subsequent exact locked-overlay run at `evidence/memory-2cc753c29a4942d38e4d5b3e612c125d` reports **94 passed, no skips, one warning, exit 0** in 42.24 seconds. Its roster includes actual daemon request/disk restart, workflow/skills and the paired combined spot/QMB composition test. This reviewer inspected the tests and completed artifacts; these suites were executed by the integrator, not rerun by the reviewer. Current memory lint/format evidence reports all checks passed / seven files formatted; strict type evidence reports zero errors/warnings.

The paired memory test executes ordinary request admission and services with only inference replaced by deterministic supplied text: a fresh second job recalls the first summary, disk reopening restores typed history, and a third job recalls the second summary. Fetching an older terminal request leaves the provider call count unchanged. The source module tests separately exercise admission denial, scope isolation, supersession, journal-ack loss, TTL, embedding revocation, context changes and legacy fallback. These are bounded local behavior evidence, not evaluated learning quality.

Remaining limits are explicit and material:

1. Default memory caps count retained unique IDs and revisions, including history. A same-scope research sequence eventually exhausts them and refuses further retention; there is no automatic eviction, consolidation or journal compaction. Current per-scope bounds do not cap total journal growth or scan cost. Long-running research needs a separately reviewed capacity/retention design rather than treating these bounded tests as endurance acceptance.
2. Actor identity has an explicit host namespace type but lacks combined actor selection/routing/configuration. Research application/profile memory remains a separate scope; it is not actor lifecycle completion.
3. Cross-source collection retrieval, contradiction evaluation, automatic extraction, learned procedural changes, privacy erasure, quality evaluation, general conversation compaction, knowledge indexing, and agent-authored ledgers remain unfinished. Extraction proposals and gate confidence do not prove source truth or authorize execution.
4. Fresh frozen optional installation and full component gates after the quality-series join remain distinct evidence. Historical red QMN/QMB/QMA gates, real authenticated native providers, remote endurance, legitimate CT47 authoring and public projection gaps are not closed by this memory increment.

Reviewed uncommitted packaging/runner bytes:

| File | SHA-256 |
|---|---|
| `qmx-agents/packages/qma-daemon/pyproject.toml` | `124E59946B7BB392AFF8054C4D099ED27B77FC58C4A2202E4EF8D655D153E23A` |
| `qmx-agents/uv.lock` | `5DFEDCE6DBADCCE375AEE9216D48FF237FD3A752911CD9376062D80F60E97A21` |
| `tools/backend-integration-check.ps1` | `9EB002D3B500E1A3BBA3301A4F412EC8F04DEBA274835073916BB31F77B810F3` |

No merge, push, publication or deployment is approved by this review.
