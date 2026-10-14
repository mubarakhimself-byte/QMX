# 02. Claude Agent SDK and providers (index)

Step 3 of the one-engine runbook. The research lives in two files, written on 2026-10-14 from primary sources read in the built-in browser.

- [02a-claude-agent-sdk.md](02a-claude-agent-sdk.md) covers the whole SDK surface. It was read against Python SDK 0.2.166 (PyPI, 2026-10-14), which bundles CLI 2.1.299.
- [02b-providers-translator-policy.md](02b-providers-translator-policy.md) covers the subscription policy, the provider endpoints, mixing providers, the GPT translator, computer use and usage visibility.

## Facts that shape the design

1. **Max-plan use is allowed, on conditions.** The unmodified Claude Code CLI must own sign-in, and QMA never reads or stores the token. Heavy unattended use is gray. (02b A)
2. **The $100 Max API credit is not a fallback.** Max 5x includes $100 a month in API credits that cover the Agent SDK with a Console key (02b A, item 14). The operator ruled out all API spend, this credit included: "I don't want to pay for API ever" (10-12 17:11; BACKLOG.md rejected-ideas table). 02b's "zero-gray fallback" is withdrawn.
3. **The Consumer Terms have a trading clause.** They bar relying on the Services "to buy or sell securities". Money stays read-only for agents. The operator should still read the clause himself. (02b A, item 9)
4. **Isolation from his personal Claude Code takes four settings.** If `setting_sources` is left out, the SDK loads all of `~/.claude`. Isolation needs `CLAUDE_CONFIG_DIR`, `strict_mcp_config`, an explicit `plugins` list and a working folder outside the dev repo. (02a)
5. **Money guards must be deny rules or PreToolUse hooks.** If no permission mode is passed, a session can start in `auto`, and `can_use_tool` is skipped for anything already approved. (02a)
6. **Python has 10 of the 33 hook events as callbacks.** The rest run only as shell hooks in settings files. (02a)
7. **A subagent cannot use a different provider.** AgentDefinition has no env field, so each provider needs its own `query()` or client, or a local router. (02a; 02b C)
8. **An inherited `ANTHROPIC_API_KEY` beats the subscription.** The harness must scrub it from the environment. (02a)
9. **The Workflow tool runs from Python.** In the SDK, a workflow that hits the usage limit fails instead of waiting. Agent teams and computer use are not in the SDK. (02a)
10. **The sandbox does nothing on native Windows.** Checkpointing misses Bash and subagent edits. (02a)
11. **The six Anthropic-format providers all have Claude Code recipes.** Their quirks are in 02b B. OpenRouter guarantees only Anthropic models. (02b B)
12. **No existing translator follows the Sign in with ChatGPT rules.** Build a small one in QMA, gated by a probe. The riskiest unknown is tool namespaces and reasoning carry-over with `store:false`. (02b D)
13. **Computer use goes through MCP.** Use Playwright MCP everywhere, plus a desktop-control MCP per OS. Built-in computer use is macOS-only and interactive-only. (02b E)
14. **Usage comes from `RateLimitEvent` and `/usage` on the Claude side.** The ChatGPT side has no usage API. (02a; 02b F)
