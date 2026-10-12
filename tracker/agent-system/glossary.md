# Glossary (agreed words)

One word per thing. Update this file when a grilling settles a term.

| Word | Means | Don't say |
|---|---|---|
| **Claude Code** | The Claude Code program, the one the operator uses every day. | "Agent SDK", "Claude Agent SDK" (the SDK is only the plug QMX would use to start Claude Code; it never appears in anything the operator reads) |
| **Claude Code worker** | QMX starting Claude Code for one job, signed in with the operator's own plan, with QMX's hooks, folders and limits applied. | "Claude Code node", "SDK agent" |
| **QMX engine** | QMX's own agent engine: LangGraph + Deep Agents, built by `build_agent`. | "harness" in operator-facing text |
| **Engine** | What runs an agent's loop: the QMX engine or a Claude Code worker. | |
| **Model** | The AI model an engine calls (Opus, GPT, Kimi, GLM, DeepSeek). Chosen separately from the engine. | |
| **Copilot** | An agent the operator chats with (main, Lab, Portfolio, per mini app; see ticket 03). | |
| **Errand** | One piece of work and its conversation (code type `Session`). | |
| **Workflow** | A Lab graph of steps; steps can be code, agents, or both (ticket 17). | |
| **Mini app / widget / plugin** | Built things the copilot can build, maintain, open and edit (ticket 18). | |
| **Modes** | Withdrawn 2026-10-09. Skills plus always-on hooks replace them. | Ask/Plan/Do |
