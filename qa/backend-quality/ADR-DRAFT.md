# Draft: observable backend quality gates

Status: proposal; canonical decision ID and routing reserved for the integration/documentation owner. This is not a ratified ADR or an acceptance certificate.

Problem: sequential quality tasks hid test/scanner evidence behind formatting/type failures; only Linux runtime suites were configured; mutation progress could look successful after an incomplete run; coverage path normalization could admit another checkout on Windows.

Proposed decision: run existing mandatory root/nested tasks independently after successful frozen synchronization on Ubuntu 24.04 and Windows Server 2025. Retain established aggregate result contexts, requiring every named prerequisite's success, including a verdict after cancellation without network setup. Use supported pinned Mutmut options, full classified results and command statuses; preserve core 68% and advisory QMN survivor policy. Resolve measured source paths against the exact candidate inventory. Preserve existing coverage floors and scanner categories.

Consequences: more runner work and more visible inherited failures. Frozen nested environments are separate from the parent workspace. General Linux-specific typing, isolated-wheel integration coverage and release acceptance remain distinct work. Schedule-only mutation evidence applies to default-branch code. Hosted matrices/cancellation and full mutation execution must be observed before claiming proven CI execution.

Evidence: REPORT.md, ci-inventory.json, actual workflow-boundary tests, independent SPEC/STANDARDS reviews. No runtime authority/API or component registry change was made. Existing ADR-0012 quality-infrastructure reuse guidance informs this proposal; do not rewrite historical decisions or invent DEC identities.
