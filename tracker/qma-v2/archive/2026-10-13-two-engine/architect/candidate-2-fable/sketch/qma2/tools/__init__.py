"""QMX tools: one registry, two adapters, the OpenAI-engine tool kit.

- registry.py: `ToolSpec` is the single source of truth for a QMX tool (name, effect, schema,
  handler). `to_claude_mcp` and `to_openai_tools` are generated from it. `classify` maps any
  call (built-in, QMX, MCP) to a ToolEffect for the gate.
- kit.py: the OpenAI engine's baseline tools with Claude's names and argument shapes
  (Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, TodoWrite, AskUserQuestion,
  Agent, Skill, apply_patch). The Claude engine uses its own built-ins and gets none of these.
- qmx.py: QMX domain tools exposed to both engines: `propose_order` (MONEY_PROPOSE),
  `portfolio_proposals` (MONEY_READ), and later the data/backtest/research tools.
"""
