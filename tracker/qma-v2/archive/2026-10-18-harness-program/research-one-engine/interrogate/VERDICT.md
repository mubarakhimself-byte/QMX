# Interrogate verdict: one-engine QMA v2 design (2026-10-14)

## Intent

QMA v2 runs QMX's agents on one engine, the Claude Agent SDK, plus a small GPT translator for the operator's ChatGPT sign-in. It must behave like vanilla Claude Code on his one Max plan. The CLI owns sign-in, and QMA never reads, stores or relays the plan token. Other providers join by base URL and key. GPT runs only behind live probes. Money stays read-only in code. QMX and his personal `~/.claude` stay apart in both directions. It runs on Windows, macOS and Linux, spends nothing on any API, prefers native SDK features, caps CLI processes, and lets the old agent code be deleted in a safe order. The review target is `architect/DESIGN.md`, `SYNTHESIS.md` and `sketch/`.

## Reviewers

- Reviewer A: Opus 5.5. 28 findings (4 critical, 16 warning, 8 nit). It checked key claims against the live Claude Code docs.
- Reviewer B: Opus 5.5. 23 findings (2 critical, 16 warning, 5 nit). It also checked fit to the operator's words.

Both reviewers are the same model family, because the operator kept Fable out of this session. Agreement between them is weaker evidence than agreement across families.

## Lead judgment: one premise failed four times

A2, A3, A5 and B3 share one premise. QMA writes a `settings.json` into a Claude home the agent can write, the CLI reloads that file mid-session, and QMA trusts its own launch-time check. Four separate findings break that premise:
- API billing through `apiKeyHelper`;
- a proxy and CA through `env`;
- plugins and mods overriding the money hook;
- rules edited live.

Patching each one would be four fixes on a premise that has already failed. So the premise goes. Policy and settings move into code through the SDK's `settings` option, with `setting_sources=[]`, and plugins go through the explicit `plugins` option. QMA writes no `settings.json` that the CLI loads. A ConfigChange command hook that blocks every user-settings change stays as a second guard. The `UserTier` probe and its two-path logic are deleted.

## Act on

Each line gives the finding, which reviewers raised it, and why it matters.

1. **The plan token is readable from the Claude home.** A1 and B1 (consensus). The fix has five parts:
   - deny rules in code for Read, Grep and Glob on every credential file, QMX's and his personal one;
   - gate patterns for `.credentials` and `$CLAUDE_CONFIG_DIR`;
   - a structural stop, where the relay refuses any outbound body carrying an `sk-ant-` token prefix;
   - redaction of those prefixes before `sessions_append` stores anything;
   - an S21 extension in which the agent actually tries the read.
   
   Relayed CLIs get a home with no credentials, since settings-in-code makes that cheap. Only the transcript folder is shared, so a provider switch can still resume.
2. **The live, agent-writable `settings.json`.** A2, B3 (consensus) and A5. Fixed by settings-in-code, as above.
3. **Proxy, CA and wrapper variables.** A3. Routing and scrub lists become allow-lists, and relayed launches set `NO_PROXY` to cover loopback.
4. **`forceLoginMethod`.** A4. QMA pins `"claudeai"`, `_connect` refuses a non-subscription auth method, and `overage` and `credits_required` stop work.
5. **Writes to his personal `~/.claude`.** A6 and B8 (consensus). Deny rules and gate patterns cover that path. The design states plainly that the same OS user makes this a speed bump.
6. **The leak check for skills only.** A7. It is rewritten for the settings-in-code shape: no personal skill, agent, command, hook, MCP server or memory appears in the init message.
7. **Money MCP servers switched off from the init message.** A8 and B10 (consensus). They are refused before launch instead. MCP config is passed in code with `strict_mcp_config`, and each declared server's tool list is checked at build. The PreToolUse gate still denies money-act names from any server.
8. **Hook timeout and a busy event loop.** A9. The gate must be fast and pure, and a check proves fail-closed behaviour on timeout.
9. **Windows path matching.** A10 and B7. Paths are normalized, case-insensitive matching is used on Windows and macOS, and S6 runs on Windows.
10. **Futures resolved from a worker thread.** A11. The approve route is async.
11. **Usage counted twice.** A12. Each provider has exactly one usage source.
12. **The GPT probe can't reach P6 and P7.** A13. The lane gets a probe mode that is open only to the probe.
13. **The pid race and Linux cgroups.** A14 and B11. The CLI starts through a small launcher, passed as `cli_path`, that puts itself in the Job Object or scope first. The memory cap degrades to the live-chat cap where the OS refuses.
14. **Orphan CLIs after a crash.** A15. Kill-on-close is set per OS, and a resume refuses while an old pid for that chat is alive.
15. **Background asks and a full chat table.** A16 and B2 (consensus). Background chats use PreToolUse `defer` or a bounded ask timeout. Capacity has a defined queue-or-refuse rule. `delegate` cannot wait on a full table.
16. **Tool search and quirks on GPT.** A17 and B21. `ENABLE_TOOL_SEARCH` follows the profile, and `GptPlan` gets a quirks slot.
17. **The family guard and router slugs.** A18 and B15. Auto and router slugs are refused, and the relay checks the model that served the request against the family guard.
18. **The exposure probe fails open.** A19 and B6 (consensus). Anything unknown or unreachable counts as `SPEED_BUMP`, never as `STRUCTURAL`.
19. **The scrub breaks Git Bash.** A20 and B12. The scrub becomes an allow-list that keeps `CLAUDE_CODE_GIT_BASH_PATH`, and it covers proxy variables.
20. **The relay path and query string.** A22 and B20. These are implementation details, recorded in the sketch.
21. **Honest layering.** A25 and B14. The doc states that against agent Bash on the same OS user, only broker token scope and the relay egress stop are structural. Everything else is a tripwire.
22. **A relaunch kills background work.** A26. The quote warns, and a switch is refused while background tasks run unless he confirms.
23. **Model id parsing.** A28. One parse function serves both `ChatConfig` and the guard.
24. **Sub-agents can call `delegate`.** B4. `delegate` is removed from native sub-agent tool lists, so R33 holds.
25. **The 50% cap and overage.** B5. The design states that the cap is best effort between `RateLimitEvent` transitions, uses `/usage` if S10 proves it reachable, and treats overage as a hard stop.
26. **Per-layer checks.** B9. Each money and leak layer gets a check run with the other layers off.
27. **`started=True` bricks a chat, and transcripts are pruned at 30 days.** B13. `started` is set after the first result, and `cleanupPeriodDays` is set high in code.
28. **Probe prompts on macOS.** B16. The probe never reads the Keychain, and it runs at boot and on demand, not on every GET.
29. **SIWC background consent.** B17. Enforce it at grant time.
30. **S9 and S21 can't run.** B22. A test-only loopback http provider is allowed behind a test flag.

## Consider

- **A23.** `ChatRecord.turn` is one flag, but prompts can queue. It's fine while QMA sends one prompt at a time. Revisit if queued prompts land.
- **A24.** The `Grants` layer may duplicate a native guarantee. Keep it only for `propose_order` and `MANAGE`, and measure in the build.
- **B18.** Some defaults depart from vanilla Claude Code in a real repo, such as project settings off. Each departure must be listed for the operator, and the console check will show them.
- **B23.** Underspecified details a builder will guess. The plan names them per PR.

## Noted

- **A21.** Scrub-before-import protects nothing extra once the scrub is an allow-list, but it costs nothing.
- **A27.** A grant secret is readable from outside its chat. Same OS user. Grants are scoped to one profile, so a stolen grant gives what that chat already had.
- **B19.** `OperatorText` means whoever holds the bearer. Same-user speed bump, accepted under R21.

## Dismissed

None. Every finding pointed at something real.

## Agreement map

The reviewers agreed on eight issues:
- the token read (A1, B1);
- live settings (A2, B3);
- personal home writes (A6, B8);
- the init-message timing (A8, B10);
- the pid race and memory cap (A14, B11);
- background asks (A16, B2);
- fail-open posture (A19, B6);
- the scrub list (A20, B12).

They diverged in emphasis. A went deeper on CLI facts (proxies, `forceLoginMethod`, mods). B went deeper on the operator's words (R33, the 50% cap, consent). No finding was contradicted by the other reviewer. The pattern says the base shape holds and the weak spot was trust in agent-reachable files. That spot is now removed rather than patched.
