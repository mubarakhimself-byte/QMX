# Agent-system research pass, 2026-10-12

This is a fresh research pass from primary sources, run for the agent-system Wayfinder map (`tracker/agent-system/map.md`).
Each findings file ends with a section listing corrections to the older `rebuild/research/*.md` studies. Where the two disagree, these findings win.

## Findings

| File | Lane |
|---|---|
| `qmx-internal.md` | QMX's own designs. Covers the UI screen by screen (the errand, the desk, the organogram), the pre-August, August, September and October agent designs, the WF1, WF2 and WF3 origins, what the code really implements, and 15 open contradictions. |
| `langchain-stack.md` | LangChain v1, LangGraph, Deep Agents and LangSmith. Covers pinned versions, what we get for free vs what we must build, licensing (MIT libraries; Agent Server needs a licence), Opus 5.5 compaction safety, and the 2026 blog index. |
| `harnesses.md` | Hermes Agent, OpenAI Codex (from source), Vercel Eve and agent-as-a-folder, Pi, bb, Prime Agent, DeepSeek Harness (Cordis), computer and browser use, and the cTrader and MT5 risks. |
| `memory.md` | Memory vs knowledge vs ledger. Covers Hindsight, Mem0, Hermes, Deep Agents, Letta, Zep, Honcho and Supermemory, a provider-neutral interface, and a bake-off plan. |
| `models-routing.md` | Vendor terms per account type, CLIProxyAPI facts, prices dated 2026-10-12, defaults per role, routers compared (thin router, LiteLLM, LangSmith Gateway), the picker UI, and a verification checklist. |
| `cookbooks.md` | Claude and OpenAI cookbook patterns: caching, compaction, memory, subagents, budgets, scheduled agents, HITL, evals, the 10 to copy first and the ones to skip. |

## Notes (researchers' working extracts)

- `notes/deepagents-core.md`, `notes/deepagents-extensions.md`, `notes/langchain-langgraph-core.md`: per-page extraction notes for the LangChain docs.
- `notes/harnesses/`: notes on Hermes (core and extensions), Codex, Eve, computer use, and Cordis's architecture.
- `notes/models/`: CLIProxyAPI notes, pricing as of 2026-10-12, LangChain model mechanics, model-picker UI patterns, and subscription terms.
- `notes/cookbook-batches/`: per-batch reading notes. Batches 01, 02 and 06 were stopped before they wrote notes.
- `notes/cookbooks-index.md`: one line per agent-relevant cookbook item (270 items).

## Raw sources, kept outside the repo

These are third-party pages and clones, read only. They stay on `D:\QMX-research\`:
- `sources\langchain\`: LangChain docs pages and about 67 blog posts saved as markdown.
- `sources\harnesses\hermes\pages\`: 239 Hermes docs pages.
- `sources\memory\`: Hindsight's full docs, plus Hermes, Mem0, Letta, Zep, Honcho and Supermemory pages.
- `sources\text\` and `sources\mdonly\`: text extracts from the cookbooks.
- `sources\repos\`: shallow clones of claude-cookbooks, openai-cookbook (partial), codex, CLIProxyAPI, deepagents and langchain.

If the D: drive is lost, every findings file still cites its URLs, so the sources can be fetched again.
