"""qmf.calendar_crypto247: the around-the-clock crypto calendar and each venue's funding clock.

Each file in `calendars/` is one `qmx.calendar/1` document named by its `calendar_ref`. The
workflow engine's `market_open:<market_id>` precheck reads them by path; nothing here runs. A
funding clock is `every` (an ISO 8601 duration) counted from `anchor` (UTC); an instrument record's
own `funding_interval` wins for a contract that differs.
"""
