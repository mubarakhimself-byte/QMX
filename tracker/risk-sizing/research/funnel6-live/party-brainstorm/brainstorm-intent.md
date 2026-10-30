# Brainstorm intent: the live side

Source: `.memlog.md` (141 entries, status complete). Headless run, 2026-10-30. Full field in `live-field.md`.

**Topic.** The trading node, live market access and outside connections, the data units and agents read, and the journals.

**Goal.** Widen the field before any design. Ideas, options and questions only. Ruling 135 is left open.

**What came out.** 120 ideas over ten domains (node setup, PC first, failure, live feeds, data versus execution, journals, what agents read, UI, keys, wildcards), each by a different technique. 66 grow a seed, 56 are new (122 counting two party ideas).

**Directions that matter (not choices).**
1. The node exists for one state, lid closed. PC first already fails for the node today, because QMN is Linux and systemd only.
2. Ruling 135 and PC first collide only when "run" means "run with the live key". Demo rehearsal with twin and shadow runs, and a brain and arm split, keep both rules. They cost different things.
3. Data and execution as two roles of one connection covers futures, perps and proxy-data units with one concept.
4. The simplest journal is one row shape over a few streams with one writer each. The open question is the store of record, not the fields.
5. Under ruling 135 as written, nothing stands in for the trading server when it is down.

**Assumptions.** The brief served as the topic and goal. The skill's `on_complete` line (recommend the PRD) was not run, because this planning run has its own order in `STATE.md`. HTML and intent were written by this agent from the memlog, not by sub-agents, because the standing orders forbid sub-agents.

```json
{
  "status": "complete",
  "intent": "brainstorm",
  "memlog": "research/funnel6-live/party-brainstorm/.memlog.md",
  "html": "research/funnel6-live/party-brainstorm/brainstorm.html",
  "intent_doc": "research/funnel6-live/party-brainstorm/brainstorm-intent.md",
  "assumptions": ["topic and goal taken from the lead's brief", "on_complete PRD hand-off skipped for this planning run", "artifacts written without sub-agents per standing order 1"],
  "external_handoffs": []
}
```
