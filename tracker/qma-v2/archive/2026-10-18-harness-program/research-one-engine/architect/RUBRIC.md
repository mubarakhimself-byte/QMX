# Arena rubric (hidden from runners; for the judge and the lead)

Score each criterion from 1 to 5, and cite the candidate file and section for every score.

1. **Operator experience.** It behaves like Claude Code on his Max plan, provider switching is simple, and the temporary-console sign-off works. He never handles tokens or edits config files by hand.
2. **Native-first and small.** It uses SDK features (permission rules, hooks, sub-agents, skills, compaction, sessions, Workflow) instead of QMX rebuilds. It has the least new QMX code and deletes the most old code. It gives a credible deletion order that respects the HOW import traps.
3. **Money and secret safety under full tools.** Money stays read-only, and broker credentials stay unreachable, even with Bash on. An agent that copies the nearest example cannot break the invariant. Guards are in types or in process boundaries, not prose.
4. **Policy and platform.** The CLI owns Claude sign-in, QMA never reads or stores the plan token, and no API spend is needed. A base URL can never leak his login token to a third party. It runs on Windows, macOS and Linux, and the operator does at most a short one-time setup.
5. **Providers and limits.** It covers the six Anthropic-format providers. GPT goes through the translator behind honest probe gates with a stated failure path. There is a sub-agent-on-another-provider story. Concurrent CLI processes are capped (170 to 610 MB each), and background use stays within the 50% editable cap.
6. **Depth and extensibility.** It has a small public surface hiding a lot. The backlog can grow without breaking invariants: workflows, organogram, plugins, the UI later and remote hosts. Every claim can be checked by a live test.
