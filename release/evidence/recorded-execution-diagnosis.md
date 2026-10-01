# Persisted execution diagnosis — not acceptance

Independent Sol reproduced the actual persisted replay test after quote helper commit `3d134cfd`, with active fixture/Book consumer changes. CT-10 reads, CT-12/request resolution and HostedBot selection reached an actual entry callback and minted intent, but zero closed trades. The optimization test's zero objective is not economic acceptance.

Actual trace `/tmp/review_zero_trade.py`: first frontier HostedBot callback emits entry and Book mints a ticket; second frontier bound execution returns `NoFill(reason='empty-path')`. `DeclaredPathFillAdapter.decide` in `execution/adapters.py` rejects empty prints/no open before calling `cross_declared_path`, so the new quote boundary is unreachable through the real bound adapter. This requires an adapter repair preserving actual recorded quotes, not fabricated prints/OHLC.

The recorded fixture also needs distinct intent, fill and later protective-stop frontiers. Stop processing precedes fresh entry fills within a slice; two frontiers cannot prove that later exit. Do not change the run-loop ordering or force a terminal close.

Separately, explicitly configured nonzero slippage on quote-only data is vetoed by the existing legal-print guard. Preserve that negative control. A separate named-zero-slippage fixture plus explicitly calibrated nonzero commission can prove actual execution/economics without fallback or unrecorded price bounds. This remains a controlled provider-free fixture, not provider connectivity, financial edge or full quote-only adapter acceptance.

Owner: Luna numeric, bounded fill-adapter eligibility/fixture changes; Luna data owns the Book consumer and partial-position protection. Actual nonzero CT-29/CT-32/terminal-ledger proof remains pending until the integrated positive and identity negatives pass and Sol independently reviews them.
