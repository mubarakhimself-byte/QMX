# Backend asks raised by the redesign

Things the design needs that the backend (engine/base at `3ae41ffc`) does not give a screen today. Added as they come up; the build-and-wire session turns them into work. "Have" facts are from `refs/grounding/08-qmx-today-for-design.md`.

| # | The design needs | Have today | Raised |
|---|---|---|---|
| 1 | Saved board layouts per place: which widgets, their order, their sizes, which are minimised | Nothing; no widget or layout object exists | Round 1 |
| 2 | A "something new since you last looked" mark per widget | Nothing; needs a last-seen time per widget and a change feed per data source | Round 1 |
| 3 | Sort and filter on list reads (inbox, runs, units, news) | Library list has no kind filter; run list has no placement | Round 1 |
| 4 | Every "needs you" item carries where it leads: a session, a mini app, an agent inside an app | Inbox items carry a closed action set, no target link | Round 1 |
| 5 | A push stream for the inbox and for jobs | Inbox is poll only; the `jobs` topic is never written | Round 1 |
| 6 | Trading state at a glance over REST: nodes, their units, positions, heartbeats | Model tools only; no nodes strip at REST | Round 1 |
| 7 | Stop levels callable from a screen: pause new entries, stop a node, flatten and stop, per node and for all | Node operations pause, resume, kill and flatten exist behind the app-call door; no "all nodes" call | Round 1 |
| 8 | Market session times and the user's chosen time zones as a setting | Nothing found | Round 1 |
| 9 | Getting-started state: which first steps are done | No backend | Round 1 |
| 10 | Mini apps declare a colour and an icon for the dock | `app.toml` has kind and risk class; no colour | Round 1 |
| 11 | A decision on who draws mini-app screens: raw HTML with published style rules, or screens the app only describes and QMX draws from its own components | Apps can ship only sandboxed HTML (`ui://`); no declared-view format | Round 2 research |
| 12 | Pods for screens: each pod's units, live and paper sides, today's result, room before its stop, and which pods trade in each market session | Being built in another session; not merged | Round 4 verdict (his-words #19) |
| 13 | Scheduled economic events and headlines per market and instrument, for Markets today and the clock popover | Nothing found for screens; "news sorting" still open | Round 4 verdict (his-words #19) |
| 14 | Search that reaches inside mini apps' own content | Not checked | Round 4 verdict (his-words #19) |
| 15 | Day one filled from what the backend already knows (a template the backend fills in) | Only #9 above; no facts feed for day one | Round 4 verdict (his-words #19) |
