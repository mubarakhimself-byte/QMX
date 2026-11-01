"""qmf.calendar_indices: index sessions and their per-index breaks as versioned data.

Each file in `calendars/` is one `qmx.calendar/1` document named by its `calendar_ref`. The
workflow engine's `market_open:<market_id>` precheck reads them by path; nothing here runs.
"""
