# WHY: the shapes of the 2026-10-13 QMA v2 design, and which ones the two-engine choice made

Written 2026-10-14 as the synthesis step of `/why`, before the one-engine harness redesign.

Path shorthand: paths are relative to `D:/QMX-worktrees/agent-system/tracker/qma-v2/` unless absolute. Chat citations use the investigators' short names:
- **DLG** = `trail/sources/2026-10-12-13-session-dialog.md`
- **OPS** = `trail/sources/2026-10-12-13-session-operator-messages.md`
- **EVE** = `trail/session-evening-dialog.md`
- **ASK** = the operator's AskUserQuestion answers in the session 19014dde transcript
- **TSV** = `trail/decisions.tsv`, cited by row number

All times are UTC.

---

### The Question

The 2026-10-13 design (archive/2026-10-13-two-engine/HARNESS.md, archive/2026-10-13-two-engine/BASELINE.md, archive/2026-10-13-two-engine/HARNESS-PLAN.md, the interrogate VERDICT and the `archive/2026-10-13-two-engine/sketch/`) assumed two engines: the OpenAI Agents SDK and the Claude Agent SDK. Why does each part of that design have the shape it has? Which parts exist only because of the second engine, or because one thing had to fit both engines? On 2026-10-13 at 18:33 the operator ruled one engine, the Claude Agent SDK, plus a small GPT translator for his ChatGPT sign-in. The answer ends with Preserve / Change / Avoid / Risk constraints for the redesign.

### The Code in Question

- `archive/2026-10-13-two-engine/HARNESS.md` (amendments A1 to A13; Problem lines 11-20; design lines 90-124; Tradeoffs 293-299; Alternatives 302-307), `archive/2026-10-13-two-engine/BASELINE.md` (parity matrix), `archive/2026-10-13-two-engine/HARNESS-PLAN.md` (units U0 to U10), `archive/2026-10-13-two-engine/interrogate/VERDICT.md` (rules V1 to V6), `archive/2026-10-13-two-engine/sketch/qma2/` (`model.py` `Route`, `wire.py` `CallOp`, `hooks.py`, `host/{claude,openai,tools,compact}.py`).
- Key symbols: `policy.evaluate`, `money.classify`, `Route`, `items`, `ToolSpec`, the six-verb `Adapter`, `subagents` setting, `ProjectContext`.
- Branch `plan/agent-system`, local only. Design commits: 44c62f53 (BASELINE), 942198c1 (audits, H1-H3, trail), 2c0cbea0 (HARNESS and VERDICT), 4da56ea7 (A12), c48c48f0 (A13), b2da7150 (ON HOLD). The branch has since moved to b283ce4a (one-engine requirements and research, 2026-10-14).

---

### What We Found

**Where two engines came from**

- **[Direct]** The operator proposed the two-SDK design. His stated reason was format coverage plus weight. Source: DLG:2114 (operator, 10-12 15:16:30). He says Anthropic and OpenAI "both have SDKs", other providers "design based off" them, so "we design for only two versions". In the same message he says Claude Code and Codex are too heavy to start per job, so the SDKs plus API keys are the way.
- **[Direct]** The one-engine idea was on the table first, from the operator, and was set aside. Sources: OPS:155 (10-12 10:02, "there is a high chance we can just use Anthropics agent SDK overall"); Claude adopted "Claude Code is the baseline, with one profile per provider" at 15:03 (DLG:2074-2078); `archive/2026-10-13-two-engine/BASELINE.md:370` wrote it down again on 10-13 ("run those models on the **Claude** engine and get Claude's structure for free"); the corrections box struck it ("rejected by the operator", `archive/2026-10-13-two-engine/BASELINE.md:7`).
- **[Direct]** The reasons given against one engine on 10-12 were: about 1 GB of RAM per Claude Code session, "Anthropic doesn't support running other models inside it", and GPT cannot run inside Claude Code. Sources: DLG:2110 (operator: "one gig of RAM per session ... a stupid way"; "GPT won't work because ... the competition"); DLG:2008 and DLG ~1340-1345 (Claude, from Ticket 01). Claude asked for the RAM figure to be measured "Before we ratify" (DLG:2048). No measurement was taken then.
- **[Direct]** Claude raised the "one format, not two" and translator objection, then dropped it within 11 minutes. Source: DLG:2221-2225 (Claude, 10-12 15:30:19): "Anthropic-format providers would go through a translator, so in practice it's one format, not two. ... That's my view from memory, not from the docs." The operator rebutted at 15:40 (DLG:2306). Claude replied at 15:41 "Your design is clear" (DLG:2314). **Date correction:** the brief placed this objection on 10-13. It is on 10-12. No translator objection exists in the 10-13 record before 18:25.
- **[Direct]** An independent audit flagged the two-engine choice as a proposal treated as settled. Source: `reviews/2026-10-13-forensic-session-audit.md:54`: "**Proposal treated as settled.** At 15:28 he said "I said this is a proposal". Claude's real pushback came only at 15:30, and the study (19) came after the decision was recorded." A second audit kept it: "Required by his money rule ... The OpenAI SDK accepts any `base_url`" (`reviews/2026-10-13-planning-phase-audit.md:110`), and called the translator point "weak" (`:50`).
- **[Direct]** The operator expected things from the OpenAI side that go beyond formats. Sources: OPS:100 and OPS:146 (OpenAI is "the most free", ChatGPT sign-in "has almost no problems"); ASK 10-13 04:22:52 ("Codex gives us, I think, more freedom"; "rebuilt it also in OpenAI"; GPT "especially for the sub-agents"; ChatGPT sign-in "won't fail"); DLG:2454 (audio, the eval loop cookbook); EVE:11 (OpenAI "dominated computer use"). Two of these were already contradicted before the ruling: computer use has no subscription route on either side (EVE:552; `archive/2026-10-13-two-engine/BASELINE.md:8`), and the ChatGPT plan route is restricted and untested with the Agents SDK (EVE:1059-1060).

**The reversal**

- **[Direct]** The one-engine ruling rests on one fact: every provider except GPT speaks Anthropic format, and ChatGPT sign-in is tied to a request format, not to an SDK. Sources: TSV row 38 (2026-10-13T18:33:25Z): "every provider except GPT speaks Anthropic format; Sign in with ChatGPT is format-bound, not SDK-bound, so a translator replaces the second SDK"; EVE:1097 (operator, 18:28); EVE:1104 (Claude: "'Sign in with ChatGPT' isn't tied to any SDK").
- **[Direct]** Claude admitted that it had OpenAI-side problems in hand and did not raise them, and that most of the harness work was rebuilding Claude Code on the OpenAI side. Sources: EVE:1054 ("They're in the research and the design, but I didn't put them in front of you"); EVE:1062 ("Most of the harness work was rebuilding Claude Code's structure on the OpenAI side. That's the double work you just spotted.").
- **[Direct]** The ruling reverses the 10-12 rejection of other models on the Claude engine, and the operator made that reversal himself. Source: `trail/RESUME-2026-10-14.md:22`; EVE:1077.

**The design states its own frame**

- **[Supported]** The two-engine frame was an input to every evening step, never a decision taken in them. Evidence: `archive/2026-10-13-two-engine/HARNESS.md:13` ("on two engines"); `archive/2026-10-13-two-engine/HARNESS.md:15`, where the first of the "five facts" that make the shape non-obvious is about the OpenAI SDK only; `archive/2026-10-13-two-engine/interrogate/VERDICT.md:7` ("It runs on two engines with one QMX policy point"); `archive/2026-10-13-two-engine/HARNESS-PLAN.md:5-6`; `archive/2026-10-13-two-engine/BASELINE.md:28` ("so both engines reach the baseline"); `archive/2026-10-13-two-engine/architect/FRAME.md:14` (stated as given) and `:40` (the rubric scored "behaves the same on both engines"); the trail begins at 16:05 on 10-13, after the choice (TSV first row). VERDICT says "No finding attacks the shape" (`archive/2026-10-13-two-engine/interrogate/VERDICT.md:144`), but the reviewers were never asked whether one engine changes it.

**Shape by shape**

- **[Direct] Policy point (one `policy.evaluate` in qmx-control).** It has two kinds of motive. The first stated reason is cross-engine sameness: "Both engines hit the same `policy.evaluate`, so behaviour is identical by construction" (`archive/2026-10-13-two-engine/HARNESS.md:93`). The rejected alternative names a second, engine-neutral reason: "Rejected on one policy point and on separation" (`archive/2026-10-13-two-engine/HARNESS.md:304`).
- **[Direct] Native Claude hooks and rules were given up for parity.** Source: `archive/2026-10-13-two-engine/HARNESS.md:295`: "We accept losing Claude's native settings-file hooks and rules in exchange for hooks and rules that behave the same on both engines." This is the clearest stated two-engine compromise. The morning BASELINE had planned the opposite: "**Claude engine:** native hooks; QMX only adds UI notifications" (`archive/2026-10-13-two-engine/BASELINE.md:171`), and QMX writing rules into Claude's settings (`archive/2026-10-13-two-engine/BASELINE.md:131`). The move from native to QMX-owned happened between the morning and the evening.
- **[Direct] Hooks run in qmx-control.** The design gives two reasons. One is parity (`archive/2026-10-13-two-engine/HARNESS.md:122`, "for both engines"; `:295`). The other is engine-neutral: the Python SDK lacks SessionStart, SessionEnd and PostCompact callbacks, and QMX fires them itself so "The Python SDK's missing callbacks therefore don't matter" (`archive/2026-10-13-two-engine/HARNESS.md:122`, `:16`). Post-ruling research confirms the gap: Python has 10 of 33 hook events as callbacks, and SessionStart and SessionEnd work only as settings shell hooks (`research/one-engine/02a-claude-agent-sdk.md:20`, `:66-68`).
- **[Direct] Engine derived from account kind.** It encodes the 10-12 rejection that the ruling reversed. Sources: `archive/2026-10-13-two-engine/HARNESS.md:101` ("'Claude engine on an OpenRouter key' cannot be expressed"); `archive/2026-10-13-two-engine/HARNESS.md:176` ("No other providers on the Claude engine (ruled out)"); the `Route` invariant in `archive/2026-10-13-two-engine/sketch/qma2/model.py:8-9`.
- **[Direct] `items` as the canonical transcript.** Its stated jobs are "export, cross-engine seeding and OpenAI resume" (`archive/2026-10-13-two-engine/HARNESS.md:102`). Two of the three jobs are two-engine jobs.
- **[Direct] One `ToolSpec` registry with a builder per host (A3).** Its purpose is "No second list" across a Claude MCP server and OpenAI function tools (`archive/2026-10-13-two-engine/HARNESS.md:239-240`; `archive/2026-10-13-two-engine/architect/JUDGE.md:80`).
- **[Direct] One `subagents` setting with two mechanisms (A13).** Its purpose is "The user sees the same limits on both engines" (`archive/2026-10-13-two-engine/HARNESS.md:285`). The default `max_concurrent` of 6 comes from Codex (`archive/2026-10-13-two-engine/BASELINE.md:218`, "as Codex"). Claude's native default is 20 (`archive/2026-10-13-two-engine/HARNESS.md:280`). Before A13, the design re-implemented on Claude a cap that Claude enforces itself. Commit c48c48f0 and TSV row 37 record its removal: "removed the re-implemented cap step from the Claude policy chain ... docs read in the browser show Claude enforces these natively".
- **[Direct] A pending approval dies with its host.** This was accepted for both engines with "Claude can't survive it anyway" (`archive/2026-10-13-two-engine/HARNESS.md:296`). The effect is the same with one engine.
- **[Direct] UI event envelope with `engine`, and a parity badge.** Their purpose is "Both engines are normalised into it, so the UI never knows which SDK ran" (`UI-NOTES.md:24`), plus a "both engines" or "Claude only" badge (`UI-NOTES.md:101`).
- **[Direct] OpenAI-only parts, by their own wording.** These are U4a (`host/openai.py`, `host/tools.py`, `archive/2026-10-13-two-engine/HARNESS-PLAN.md:277`), U4b (OpenAI parity tests, `:376`), the U6 local compactor (`:458`; `archive/2026-10-13-two-engine/sketch/qma2/host/compact.py:1` "Compaction for the OpenAI engine"), the U8 Agents-SDK shape of ChatGPT sign-in (`:588`), V5.1 (the OpenAI kit's shell family, `archive/2026-10-13-two-engine/interrogate/VERDICT.md:82`), V5.3 (reasoning items, `:84`), the `LoadItems` clause of V3.2 (`:57`), the `host/openai.py` ownership rule in V6.2 (`:95-98`), the `AgentTool` half of A13 and U7, and BASELINE's "OpenAI engine needs" column and H5. HARNESS-PLAN Appendix B made two scheduling choices only because units shared `host/openai.py` (`archive/2026-10-13-two-engine/HARNESS-PLAN.md:683-684`).
- **[Direct] Engine-neutral shapes, with their stated reasons.**
  - Money gate: "inherited planning law, not an incident fix" (`archive/2026-10-13-two-engine/why/WHY-harness.md:46`; `archive/2026-10-13-two-engine/architect/FRAME.md:19`). Closed `ToolEffect` with no allow branch for `MONEY_ACT` (A1, `archive/2026-10-13-two-engine/architect/JUDGE.md:25`). `propose_order` by identity (A2, TSV 17:10:07).
  - Operator principal: "One bearer token today ... The approvals answer path needs a principal agents cannot hold" (`archive/2026-10-13-two-engine/architect/FRAME.md:23`). V1: agents cannot escalate or self-approve (`archive/2026-10-13-two-engine/interrogate/VERDICT.md:143`).
  - Host as CLI launcher: it fixes the SDK env merge, holds no HTTP credential, and limits a crash to one thread (`archive/2026-10-13-two-engine/HARNESS.md:94-97`). The judge found candidate 2's in-process launch leaked inherited `ANTHROPIC_*` (`archive/2026-10-13-two-engine/architect/JUDGE.md:57`).
  - Separate `harness.db` with one writer: "A second writer connection on control.db would recreate the WAL-bug precondition" (`archive/2026-10-13-two-engine/HARNESS.md:297`).
  - `.qmx/` project layer: "so his personal Claude Code hooks in a repo never run under QMX" (`archive/2026-10-13-two-engine/HARNESS.md:244`).
  - A5 to A10 and A12 (`archive/2026-10-13-two-engine/HARNESS.md:248-277`); V4 family guard (`archive/2026-10-13-two-engine/interrogate/reviewer-A-opus.md:89`).
- **[Direct] Post-ruling facts that bear on the old shapes.** These are not evidence of 10-13 motive.
  - TSV row 51 measured live Claude CLI processes at 170 to 610 MB working set (up to 711 MB private): "high but the order of magnitude is real".
  - `02a:289` and `:294`: an omitted `setting_sources` loads the operator's `~/.claude`, and an inherited `ANTHROPIC_API_KEY` beats the subscription.
  - `02a:83-84`: Claude evaluates hooks, then deny rules, ask rules, mode, allow rules, then `can_use_tool`, and "A hook that returns allow does not skip the deny and ask rules".
  - TSV row 47: sub-agents cannot switch provider.

### What We Can Reasonably Infer

- **[Inferred]** The policy point appears to survive one engine, but its implementation may not. Reasoning: its engine-neutral reasons (money on built-ins and MCP, no bypass under permissive modes per V2 and reviewer A3, separation, `archive/2026-10-13-two-engine/HARNESS.md:304`) do not depend on engine count. Its parity reason (`:93`) does. The parity reason seems to be what pushed U2 to re-implement Claude's rule syntax, compound-command split and modes inside QMX (`archive/2026-10-13-two-engine/HARNESS-PLAN.md:235`). Given `02a:83-84`, a QMX PreToolUse decision sitting in front of native deny and ask rules is now a candidate that the 10-13 design rejected only on drift between two engines (`archive/2026-10-13-two-engine/HARNESS.md:304`).
- **[Inferred]** Hooks in qmx-control likely keep one of their two reasons. Reasoning: the Python callback gap (`02a:66-68`) still exists with one engine, so QMX firing SessionStart, SessionEnd and PostCompact remains justified. Running every other hook in QMX rather than natively rested on parity (`archive/2026-10-13-two-engine/HARNESS.md:295`). The source-control investigator tagged this shape as a pure compromise. The design text suggests it is mixed.
- **[Inferred]** `setting_sources=[]`, ProjectContext as the first user message, and the V5.4 re-send after compaction appear to form one chain of fixes. Reasoning: QMX took Claude's native config off (`archive/2026-10-13-two-engine/HARNESS.md:120`) for parity and isolation. That made CLAUDE.md a first user message, which compaction then summarises away (`archive/2026-10-13-two-engine/interrogate/reviewer-A-opus.md:115`), which then needed a re-send rule. The post-ruling isolation recipe (`CLAUDE_CONFIG_DIR` plus `strict_mcp_config`, `02a:132`) suggests isolation might be reachable without dropping native loading. That would remove the need for the chain. `02a:124` marks part of this recipe UNCONFIRMED.
- **[Inferred]** `Route` likely needs to become "provider derived from account" with the V4 family guard kept, not removed. Reasoning: the invariant at `model.py:8-9` exists to forbid key providers on Claude (`archive/2026-10-13-two-engine/HARNESS.md:176`), which the ruling now requires. The money rule behind V4 ("no API for Claude or GPT", `archive/2026-10-13-two-engine/interrogate/reviewer-A-opus.md:89`) is untouched by the ruling.
- **[Inferred]** The host process is likely more important under one engine, not less. Reasoning: key providers will now ride the Claude CLI through `ANTHROPIC_BASE_URL` and a token. Claude's credential precedence puts `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` above `/login` (`02a:194`). A per-thread allow-listed env is the place that keeps a key thread's credential away from a subscription thread.
- **[Inferred]** The 1 GB objection, which kept key providers off the Claude engine, applied to Claude threads in the two-engine design too. Reasoning: one Claude thread is one CLI process either way (`archive/2026-10-13-two-engine/H1-sdk-facts.md:64`). The two-engine design avoided it only for key-provider threads, by hosting them in-process on the OpenAI SDK (DLG:2422). Under one engine every thread pays it. TSV row 51 puts the real cost at roughly half the claimed figure.
- **[Inferred]** The A13 history is consistent with a broader pattern: the two-engine frame bent the Claude side toward QMX re-implementations. Reasoning: the caps (c48c48f0), the native hooks and rules (`archive/2026-10-13-two-engine/HARNESS.md:295`, against `archive/2026-10-13-two-engine/BASELINE.md:131`, `:171`), and the Codex-derived default of 6 all moved Claude-side behaviour away from Claude's own mechanisms, each for sameness with the OpenAI side. Only the caps were checked against Claude's docs before the ruling.
- **[Inferred]** The overnight bias of remote placement toward the OpenAI engine (DLG ~3224, ~3261) does not appear to have reached archive/2026-10-13-two-engine/HARNESS.md. Reasoning: a grep of archive/2026-10-13-two-engine/HARNESS.md for `remote|rented|VPS` finds only a LangChain import note (`:146`) and the `propose_order` rule (`:235`).

### Competing Hypotheses

**Why two engines, in the first place**

These are not exclusive. The record supports more than one.

- **Hypothesis A: format coverage.** Two SDKs were chosen because the operator believed every provider targets one of two formats, and the OpenAI SDK would host the key providers.
  - Evidence for: DLG:2114; ASK 10-12 15:22:48 ("API compatibility"); `planning-phase-audit.md:110`.
  - Evidence against: on the same day he said providers design for Claude Code (DLG:2114) and also for Codex (DLG:2306). On 10-13 he said they "all design for Claude Code" (EVE:1097). If that holds, one format covered all of them except GPT, which is Claude's 10-12 15:30 point.
- **Hypothesis B: per-session weight.** The OpenAI SDK was attractive because it runs in-process, with "no 1 GB process per session" (DLG:2422).
  - Evidence for: DLG:2110, DLG:2422, `BACKLOG.md:141`.
  - Evidence against: the figure was never measured before the decision (DLG:2048). Measured on 10-14 it is 170 to 610 MB (TSV row 51). The operator's objection may have been to a session per job, not per chat (see the contradiction below).
- **Hypothesis C: OpenAI and Codex "freedom" as goods in themselves.** He wanted ChatGPT sign-in, computer use, audio, eval loops, Codex as reference, and GPT for sub-agents.
  - Evidence for: OPS:100, OPS:146, ASK 04:22, DLG:2331, DLG:2454, EVE:11.
  - Evidence against: two of these were contradicted before the ruling (computer use, the plan route). The ruling keeps only ChatGPT sign-in, via a translator. Whether he accepts losing the rest is not recorded.
- **Hypothesis D: process failure.** The proposal hardened because Claude agreed instead of testing it.
  - Evidence for: `forensic-session-audit.md:54`; DLG:2202 ("I feel like you're not just being agreeable"); DLG:2314; EVE:1040 ("you're a little bit biased"); EVE:1054.
  - Evidence against: the operator also asked Claude to "take the wheel" and push less at times (DLG:2331). Claude did push back once (DLG:2221-2225).

**What the 10-12 rejection of "other models on Claude" meant**

- **Hypothesis 1:** he rejected any non-Claude model on the Claude engine. Evidence: `archive/2026-10-13-two-engine/BASELINE.md:7`; `archive/2026-10-13-two-engine/HARNESS.md:176`; EVE:1077 (Claude's reading).
- **Hypothesis 2:** he rejected one Claude Code session per job, and coding-plan profiles, on RAM grounds, while accepting that the providers work. Evidence: DLG:2110 ("They work, you just need to follow the bloody documentation ... I've used GLM, I've used Minimax"; "I wasn't proposing it as the actual design"). The ruling makes this moot for the design, but it matters for how many CLI processes he will accept.

### What We Don't Know

- **Why two engines, in the trail.** The trail starts at 16:05 on 10-13, after the choice (TSV first row). No commit message on the branch carries a rationale. The motive is reconstructed from the chat only.
- **Whether "two SDKs" meant the OpenAI Agents SDK or the OpenAI format.** The ledger agent flagged this at 10-12 15:38 ("Ask him directly which he means", DLG:2265). The chat investigator searched DLG 2265-2460 and all five AskUserQuestion results and found no such question asked.
- **What the Two-SDK study said about the translator.** Claude's 15:55 relay (DLG:2421-2438) omits it. `tracker/agent-system/research/19-two-sdk-study.md` was not read by either investigator.
- **Whether the operator accepts losing the OpenAI-side expectations** that a translator does not carry: Codex "freedom", audio, the eval loop, GPT-heavy sub-agents. No record after 18:33 addresses them.
- **Whether `.qmx/` (A4) was put to him.** The judge said "Flag this for the operator" (`archive/2026-10-13-two-engine/architect/JUDGE.md:82`). No trail row records the question.
- **Whether a translator works on the ChatGPT plan token.** The resume note marks it "UNPROVEN and must be probed first" (`RESUME-2026-10-14.md:20`).
- **How a provider switch inside one thread works on one engine.** One CLI process has one base URL (`02b:113`). Whether a Claude session JSONL can resume under a different provider, or must be seeded from `items`, is not established in any source read.
- **Whether the user-tier skills and agents follow `CLAUDE_CONFIG_DIR`.** `02a:124` marks this UNCONFIRMED. It decides whether native config loading can come back.
- **The operator's evening AskUserQuestion answers** (session 2cf20068, "Money; Fable; Agent guard; Global rules", EVE:934) are not in the export. Only Claude's paraphrase exists (EVE:949-958).
- **Which process is which in the RAM measurement.** TSV row 51 says the processes were not mapped.
- **Not read:** `archive/` (by instruction), `trail/agent-briefs.md` beyond briefs 1, 4 and 13-18, candidate-2 files beyond what JUDGE quotes, and `DELETION-PLAN.md`.

### Sources Consulted

- **Source control history**: branch `plan/agent-system`; 41 commits touching `tracker/qma-v2` (2026-10-12 20:57 to 2026-10-13 21:42 +0300) reviewed by title, 19 opened in full, including b2da7150, c48c48f0, 4da56ea7, 2c0cbea0, 942198c1, 44c62f53, the reverted 713534a0, and the newer b611bd71 and b283ce4a. Diffs of c48c48f0, 4da56ea7 and b2da7150. Design documents read: archive/2026-10-13-two-engine/HARNESS.md, archive/2026-10-13-two-engine/HARNESS-PLAN.md, archive/2026-10-13-two-engine/BASELINE.md, archive/2026-10-13-two-engine/interrogate/VERDICT.md and both reviewer files, archive/2026-10-13-two-engine/architect/FRAME.md, archive/2026-10-13-two-engine/architect/JUDGE.md, candidate-1 design, archive/2026-10-13-two-engine/why/WHY-harness.md, archive/2026-10-13-two-engine/H1-sdk-facts.md, the two 10-13 audits, BACKLOG.md, UI-NOTES.md, `archive/2026-10-13-two-engine/sketch/qma2/` docstrings, `trail/decisions.tsv`, `trail/RESUME-2026-10-14.md`. The synthesizer spot-checked archive/2026-10-13-two-engine/HARNESS.md 11-20, 90-124, 174-178, 229, 239-244, 279-285, 293-307; archive/2026-10-13-two-engine/BASELINE.md 7-9, 28, 37, 131, 171, 218-220, 370; both audits; JUDGE 57, 65, 82; `model.py` 1-12; UI-NOTES 24, 101; VERDICT 7, 144; TSV rows 37-51; RESUME 18-42; `02a` hook, config and credential lines; `02b` translator lines. Every spot-check matched the investigator's citation. No PRs exist: the branch was never pushed.
- **Issue / ticket tracker**: Not searched. No matching MCP is connected for this project. The GitHub MCP failed to connect. No tickets exist for this planning branch.
- **Long-form documents**: Not searched outside the repo. No matching MCP is connected. In-repo design documents are covered above.
- **Real-time team chat**: The operator's planning conversations with Claude stand in for team chat. Session 19014dde (10-12 08:13 to 10-13 04:30) and session 2cf20068 (10-13 15:50 to 18:37) were read through DLG, OPS, EVE, SUB and BRF, plus all five AskUserQuestion results from the raw transcript. Greps covered `two engines|two-engine|two lanes|two SDKs|both engines`, `translat`, `litellm`, `freedom`, `parity`, `codex`, `chatgpt`, `one engine`. The synthesizer spot-checked EVE 1040, 1054, 1062, 1070, 1077, 1097, 1104, 1115, 1127, 1180 and DLG 2048, 2110, 2216, 2223, 2314.
- **Infrastructure observability**: Not searched. No matching MCP is connected, and this is a planning branch with no runtime, so it is irrelevant.
- **Error / exception tracking**: Not searched. No matching MCP is connected, and there is no running system to produce errors.
- **Product analytics warehouse**: Not searched. No matching MCP is connected, and there is no product usage to measure.

### Confidence Summary

The origin of the two-engine choice and its reversal is well-supported by direct chat and trail evidence. Which shapes depend on two engines is direct where the design names its own motive. That covers the policy-point parity clause, the native hooks and rules trade, `Route`, `items`, A3, A13 and the OpenAI-only units and rules. Whether the mixed shapes (policy point, hooks at home, `setting_sources=[]`) can now take a simpler native form is inferred from post-ruling SDK research, part of which is UNCONFIRMED. Why "two SDKs" won over "two formats" is unknown: the clarifying question was never asked.

---

## Constraints for the redesign

Each line carries its evidence tier. "Preserve" items have engine-neutral stated motives. "Change" items have a two-engine motive that the ruling removed. A Change item says what to re-decide. It does not prescribe the answer.

### Preserve

- **[Direct] Money gate.** `money.classify` first; closed `ToolEffect`; `MONEY_ACT` never approvable; `propose_order` by identity (A1, A2, V1; `archive/2026-10-13-two-engine/why/WHY-harness.md:46`).
- **[Direct] Operator principal and the one-shot, gate-bound `CallOp` grant.** Agents can never hold the approvals answer path (`archive/2026-10-13-two-engine/architect/FRAME.md:23`; V1; V3).
- **[Direct] One QMX decision for every Claude tool call:** built-ins, MCP and sub-agents, failing closed under permissive modes (V2; `archive/2026-10-13-two-engine/interrogate/reviewer-A-opus.md:19`). Keep the money and fail-closed reasons. Drop the parity reason.
- **[Direct] Host process as the CLI launcher.** Allow-listed env, no HTTP credential, one thread per crash, idle reaping (`archive/2026-10-13-two-engine/HARNESS.md:94-97`; `archive/2026-10-13-two-engine/architect/JUDGE.md:57`, `:65`; A7). [Inferred] It matters more now that key-provider tokens ride the same CLI (`02a:194`).
- **[Direct] Separate `harness.db` with one writer** (`archive/2026-10-13-two-engine/HARNESS.md:297`).
- **[Direct] Isolation from his personal `~/.claude` and repo `.claude/` hooks** (A4 motive, `archive/2026-10-13-two-engine/HARNESS.md:244`; `02a:289`).
- **[Direct] The family guard:** no Claude or GPT model on a key row (V4.1; `archive/2026-10-13-two-engine/interrogate/reviewer-A-opus.md:89`).
- **[Direct] The engine-neutral rest:** A5 (U1 = one live Claude turn), A6, A7, A9, A10, A12, V1 to V4, V6 minus its `host/openai.py` clause, and `SwitchQuote` pinned to `cache_epoch`. For A6, see Risk.

### Change

- **[Direct] `Route`.** Engine from account kind becomes provider from account, on the one engine. "Claude engine on a key provider" must be expressible (`model.py:8-9`; `archive/2026-10-13-two-engine/HARNESS.md:101`, `:176`; TSV row 38).
- **[Direct] Re-decide the `archive/2026-10-13-two-engine/HARNESS.md:295` trade, piece by piece.** For each hook and rule mechanism, record a reason that is not parity, or use Claude's native mechanism. [Inferred] Keep QMX-fired SessionStart, SessionEnd and PostCompact on the Python-gap reason (`02a:66-68`).
- **[Direct] A13.** Drop `AgentTool`. Re-decide the `max_concurrent` default. 6 came from Codex, and Claude's native default is 20 (`archive/2026-10-13-two-engine/BASELINE.md:218`; `archive/2026-10-13-two-engine/HARNESS.md:280`).
- **[Direct] A3.** One builder, the SDK MCP server. The function-tool path goes (`archive/2026-10-13-two-engine/HARNESS.md:239-240`).
- **[Direct] `items`.** Drop the OpenAI resume and cross-engine seeding jobs, and `LoadItems` (`archive/2026-10-13-two-engine/HARNESS.md:102`; V3.2). Re-decide what a provider switch needs (see What We Don't Know).
- **[Inferred] The `setting_sources=[]` / ProjectContext / V5.4 chain.** Re-test it against the `CLAUDE_CONFIG_DIR` isolation recipe (`02a:132`, part UNCONFIRMED).
- **[Direct] Units.** Drop U4a, U4b, the U6 local compactor, V5.1's OpenAI kit, V5.3, and the `AgentTool` half of U7. U8 becomes a translator unit with its probe run early (`RESUME-2026-10-14.md:33-41`). Re-scope U2 and U3 once the hooks and rules decision is made.
- **[Direct] Framing text.** "two engines" in archive/2026-10-13-two-engine/HARNESS.md:13 and archive/2026-10-13-two-engine/interrogate/VERDICT.md:7; BASELINE's "OpenAI engine needs" column; the UI `engine` field and parity badge (`UI-NOTES.md:24`, `:101`) become a provider field or are removed. [Inferred] The "floor = vanilla Claude Code or Codex" (`archive/2026-10-13-two-engine/HARNESS.md:13`) needs a stated meaning for Codex now.

### Avoid

- **[Direct] Re-implementing in QMX what Claude enforces natively,** without a stated reason other than sameness. The A13 caps were one such case, undone an hour before the ruling (c48c48f0; TSV row 37).
- **[Direct] "Identical by construction" or "same on both engines" as a justification.** With one engine it justifies nothing (`archive/2026-10-13-two-engine/HARNESS.md:93`, `:295`; `archive/2026-10-13-two-engine/architect/FRAME.md:40`).
- **[Supported] Treating a proposal as settled.** Put the one-engine shape through its own challenge. The reviewers were never asked about engine count (`forensic-session-audit.md:54`; `archive/2026-10-13-two-engine/interrogate/VERDICT.md:144`; TSV first row).
- **[Direct] Letting an unmeasured cost decide architecture.** The 1 GB figure did (DLG:2048, DLG:2110). Use the TSV row 51 measurement and measure again for key-provider threads.
- **[Direct] Ambiguous terms left unasked.** "SDK" versus "format", and what "Codex" means (DLG:2265). These are vocabulary he cares about.
- **[Direct] Holding back negative findings.** Put each one in front of him when it is found (EVE:1054).

### Risk

- **[Direct] The translator on the ChatGPT plan token is UNPROVEN.** The route requires `store: false` and streaming, carries no system message, has no hosted tools, and uses a token that expires hourly (`RESUME-2026-10-14.md:18-20`; `02b:143-189`). Probe it before any design depends on it.
- **[Direct] Every thread is now a CLI process,** at 170 to 610 MB measured (TSV row 51). Cap concurrent processes and reap idle ones.
- **[Direct] Credential crossover.** `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` outrank `/login` (`02a:194`, `:294`), and a LiteLLM-style router may send the Claude token upstream (`02b:127`). A key thread's env must never reach the subscription thread, and the reverse.
- **[Direct] OpenRouter's Anthropic endpoint is guaranteed only for Anthropic first-party models** (`RESUME-2026-10-14.md:21`, H1 fact 20). Non-Claude models through OpenRouter may need the translator too.
- **[Direct] No per-sub-agent provider switch** (TSV row 47; `02b:113`). His "GPT especially for the sub-agents" (ASK 04:22) needs a separate session through the translator.
- **[Direct] Computer use has no subscription route** (`archive/2026-10-13-two-engine/BASELINE.md:8`; TSV row 45). He expected OpenAI to cover it (EVE:11).
- **[Direct] A6 may rest on an overstated premise.** `02a:315` calls "QMX must not keep a setup-token" overstated. Keep A6 until he rules on it.
- **[Inferred] Expectations the translator does not carry.** Codex "freedom", audio and the eval loop (Hypothesis C) may resurface as scope. Confirm them with him before the redesign closes.
