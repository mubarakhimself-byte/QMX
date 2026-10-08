# Hummingbot ideas for QMX

[Connector architecture](https://hummingbot.org/connectors/connectors/architecture/)
separates authentication, market-data streams, user-state streams and order tracking.
Borrow that separation and its sequence checks: a gap needs a fresh snapshot;
reconnecting must not imply resubmitting an order. Keep symbol precision separate
from minimum size and notional limits, as QMF's spot metadata already does.

[V2 strategies](https://hummingbot.org/strategies/v2-strategies/) split continuous
controllers from finite executors and give both a market-data provider. Grid,
TWAP, DCA and cross-exchange market making are useful research patterns for QMX
workflows. Backtest them with costs and inventory limits before considering live
use. Their autonomous executors would violate QMX's operator-signature rule if
exposed to agents; retain proposals and QMN execution. No Hummingbot code or
dependency is imported.
