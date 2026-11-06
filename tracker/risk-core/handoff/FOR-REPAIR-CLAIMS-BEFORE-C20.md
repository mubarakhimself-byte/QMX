# For the repair program: keep these files before C-20 and the deletion sweep

From the risk-and-sizing session, 6 Nov 2026 (funnel decisions DP24, DP25 and DP33; source `funnel/FUNNEL.md` on branch `plan/risk-core`).

The audit's call graph reads these as having no callers, so the deletion sweep would remove them. The risk template builds on them. Please do not delete them until the risk session has moved what it needs.

## Claimed files

- `qmn/data/news_calendar.py`: the news calendar.
- `qmn/protection/windows.py`: the news and protection windows.
- `sqs_baseline_producer.py`: the SQS baseline. It must move before the old gate goes.
- `labelers.py`: its SQS rule text.
- `qmn/replay/port.py`: its SQS replay rule.
- `qmn/protection/dispatch.py`, the `control_window` module in `qmf-risk`, and `registry_catalog.py`: named by the funnel's news and SQS decisions.

The old SQS gate's rule text (`qmn/src/qmn/host/decision_root.py:493-510`) is already copied verbatim into `grounding/G12-audit-and-repair-for-risk.md` section 2, so C-20 can still remove that gate when its time comes.

## A flag for the QMA side

Agents with cTrader's MCP on the node's own demo account open positions that no unit holds. The funnel's reading is that those positions must count under a `foreign` scope in the account numbers, so the rules can see them. This session flags it and does not design it.

## Not asked of the repair

Nothing here changes a repair PR before C-20. These are claims to honour when the deletion runs. Risk and sizing rules stay with the risk session.
