> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 11 - References: research harnesses, schedules, animated documents

Read 2026-10-16 in the built-in browser (Firecrawl used only to find the Kimi K3 and Claude Design pages). Plain English. Each section ends with "Copy for QMX".

---

## 1. alphaXiv, arXiv q-fin, open research harnesses

### alphaXiv
- Site: https://www.alphaxiv.org — a feed of papers with AI one-line summaries, "Researchers to follow", discussion threads on each paper, and three AI entry points: "What's worth reading?", "Who's working on it?", "Grounded literature review".
- MCP server docs: https://www.alphaxiv.org/docs/mcp
  - Endpoint `https://api.alphaxiv.org/mcp/v1`, Streamable HTTP, MCP v1.0.0.
  - Auth: OAuth sign-in by default. For headless agents and cron jobs, use an API key from Settings > API Keys, sent as `Authorization: Bearer <key>`.
  - Native MCP clients only (Claude Code, Codex CLI, Cursor, VS Code, Zed, `mcp-remote` bridge). Browser-hosted clients are blocked by CORS.
  - 21 tools in three groups. The ones that matter for QMX:
    - `get_hot_feed`, `get_for_you_feed`: paper IDs only. Free; they use no assistant quota. **Use these as the cheap pre-check.**
    - `discover_papers(keywords[3-4], question, difficulty 1-10, published_after/before, prioritize)`: runs alphaXiv's own retrieval loop and returns a ranked list of 5-15 papers. Counts against quota.
    - `get_paper_content(url, fullText?)`: returns an AI-made structured report by default, or the raw text.
    - `answer_pdf_queries(paper, queries[])`: returns only the relevant pages as `<paper><page num>` XML, ready for citation. Asking several questions about the same paper costs almost nothing extra, so batch them into one call.
    - `read_files_from_github_repository(githubUrl, path)`: reads the paper's code. `/` returns the whole file tree.
    - Researcher tools (find_researchers, get_researcher, and others) plus library management.
- Docs also have a "Blog formatting" page (publishing paper blogs). Not needed.

### arXiv quantitative finance
- Archive: https://arxiv.org/archive/q-fin. Categories: q-fin.CP, EC, GN, MF, **PM** (portfolio management), PR, **RM** (risk), **ST** (statistical finance), **TR** (trading and microstructure). Each has new, recent, and current-month listings.
- Feeds and API: RSS per category (`https://rss.arxiv.org/rss/q-fin.TR`), plus the legacy API `http://export.arxiv.org/api/query?search_query=cat:q-fin.TR&sortBy=submittedDate`.
- API terms: https://info.arxiv.org/help/api/tou.html. **No more than 1 request every 3 seconds, one connection at a time**, across all your machines. You may store metadata. Do **not** re-serve the PDFs; link to the abstract page instead.

### Open research harnesses worth copying
- **LangChain open_deep_research**: https://github.com/langchain-ai/open_deep_research
  - Built on LangGraph, which is QMX's agent stack, so it fits directly.
  - Has four separate model slots (summarization, research, compression, final report), each set through `init_chat_model`, so any provider works.
  - Search is pluggable (Tavily, native search, any MCP server).
  - Evaluated on Deep Research Bench with an LLM judge (RACE score). One run of 100 tasks costs about $20-100.
  - **This is the best base for QMX's paper-research agent.** Point its MCP config at alphaXiv.
- **OpenAI Agents SDK research_bot**: https://github.com/openai/openai-agents-python/tree/main/examples/research_bot. The smallest working shape: planner (list of search terms, each with a reason) → parallel searchers (each summarizes) → writer.

**Copy for QMX:**
- Paper source = alphaXiv MCP with an API key, plus the arXiv q-fin RSS feed as the free first pass.
- Engine pre-check = diff the feed IDs against the IDs already seen. Wake the model only when there are new IDs.
- Paper reading = `answer_pdf_queries` with batched questions. Its page-tagged output becomes the citation evidence.
- Respect the 3-second arXiv rate limit inside the script step, not inside the agent.

---

## 2. Cookbooks: the research-harness shape

### Anthropic
- Post: "How we built our multi-agent research system": https://www.anthropic.com/engineering/multi-agent-research-system
- Prompts (open source): https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents/prompts. Three files: `research_lead_agent.md`, `research_subagent.md`, `citations_agent.md`.
- Pattern notebooks: https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents. Covers prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer, async multi-agent, and teams under latency budgets.

**Findings from the post:**
- **Shape.** The lead agent plans and saves the plan to memory. It spawns 3-5 subagents in parallel, each with its own context. It synthesizes and decides whether more research is needed, looping if so. A separate CitationAgent then ties every claim to a source location.
- **Why it works.** Token spend explains about 80% of quality. Multi-agent runs use about 15x the tokens of a chat, so use them only for high-value questions.
- **The brief each subagent gets:** one objective, the output format, the tools and sources to use, which sources to avoid, and hard scope boundaries. Vague briefs led to duplicated work.
- **Effort scaling, written into the prompt:**
  - Simple fact: 1 agent, 3-10 tool calls.
  - Comparison: 2-4 subagents, 10-15 calls each.
  - Complex: 10 or more subagents. Hard cap of 20.
- **Subagent budget and stop rule:**
  - Plan a "research budget": under 5 calls for simple tasks, about 10 for hard, up to 15 for very hard.
  - Absolute limit: 20 tool calls or 100 sources, after which the subagent is killed.
  - Stop early at diminishing returns, then report.
- **Source quality.** Flag speculation, aggregators, and marketing. Report conflicts instead of resolving them silently. Early agents preferred SEO content farms over primary PDFs; prompts had to fix this.
- **Evals.**
  - Start with about 20 real queries.
  - Use one LLM judge with a rubric: factual accuracy, citation accuracy, completeness, source quality, tool efficiency. It scores 0-1 and gives pass/fail.
  - Humans still catch things the judge misses.
- **Production lessons:**
  - Resume from checkpoints rather than restarting.
  - Keep full traces.
  - Subagents write artifacts to a filesystem and pass back only references ("avoid the game of telephone").
  - For agents that change state, judge the end state rather than each turn.

### OpenAI
- Deep research guide: https://developers.openai.com/api/docs/guides/deep-research
  - Three steps: a cheap model asks the user clarifying questions → a cheap model rewrites the prompt → the deep research model runs in the background and reports back by webhook.
  - The output lists every search, code, and MCP call the model made, which works as a ready-made trace.
  - The o3/o4-mini deep-research models were shut down on 2026-07-23. **Copy the shape, not the model.**
- Per-run spending controller: https://developers.openai.com/cookbook/articles/per_run_spending_controller_responses_api
  - Each run gets its own dollar budget.
  - Before each call, reserve the worst-case cost (input tokens at the highest input price, plus max output tokens). After the call, refund the unused part.
  - Stop if the next call cannot be afforded.
- Agent improvement loop: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop
  - Traces, plus human feedback, plus LLM feedback, become generated evals (Promptfoo).
  - An optimizer (HALO) ranks harness changes and writes one handoff file for a coding agent.
  - A human approves the diff.
- Index of agent recipes (memory and compaction, macro evals, sessions): https://developers.openai.com/cookbook/topic/agents

**Copy for QMX: the research harness, as engine steps**

| Role | Step kind | Rule |
|---|---|---|
| Clarifier | model call (cheap) | Only for operator-started runs. Skip on cron. |
| Planner | model call | Classifies the question (straight, breadth, or depth). Writes a plan file and N subagent briefs. |
| Searchers | agent × N, parallel | Brief = objective, format, sources, scope. Budget is 5-15 calls; hard stop at 20. Each writes a findings file. |
| Synthesizer | model call | Reads only the findings files. Can loop back to the planner once. |
| Citation checker | grader | Every claim must map to a source passage. Uncited claims are dropped or flagged. |
| Judge | grader | Rubric 0-1 plus pass/fail: accuracy, citations, completeness, source quality, efficiency. |
| Budget | engine | A dollar cap per run, using reserve-then-refund. Stop and deliver partial results when the cap is hit. |

---

## 3. Hermes Agent (Nous Research): what to copy for schedules

Docs: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron (also /features/memory and /features/skills).

**Scheduling**
- **Schedules** can be written as "in 30m", "every 2h", "every day 7am", a cron expression, or an ISO timestamp.
- Jobs can be paused, resumed, edited, triggered, or removed. A job can be **created paused** to act as a safe canary. One switch (`hermes pause`) pauses everything.
- **Model per job:**
  - Lookup order: the job's own pin → a fleet default → the main model.
  - The agent cannot change a job's model; that choice belongs to the user.
  - Reasoning effort can be set per job: heavy jobs on high, cheap jobs on minimal.
- **Pre-dispatch validation.** Before spending tokens, the scheduler checks that:
  - the provider key resolves,
  - skills have what they need,
  - the delivery target exists,
  - the MCP servers resolve.
  - If any check fails, the job goes to `blocked_config`, sends ONE alert, and makes no model call.

**Running without a model**
- **No-agent mode:** a script on a schedule.
  - Its stdout is delivered word for word.
  - Empty stdout means silence.
  - A non-zero exit or a timeout sends an alert, so a broken watchdog cannot fail quietly.
  - Zero tokens.
- **wakeAgent pre-check:**
  - A script runs first. If its last line is `{"wakeAgent": false}`, the tick is skipped.
  - `{"wakeAgent": true, "context": {...}}` passes data into the run.
  - Documented recipes: file changed, external flag set, and a SQL count of new rows.
  - **This is exactly QMX's "cheap pre-check before waking a model".**

**Delivery and output**
- **Silent success:** if the output contains `[SILENT]`, the run is saved for audit but not delivered. Failures always deliver.
- **Delivery targets:** origin, local file, chat platforms, email, `all`, or a comma-separated fan-out.
  - Output is secret-redacted on the way out.
  - A failed delivery gets its own status. An unconfirmed one is marked UNVERIFIED.

**Chaining jobs**
- **`context_from`:** a job reads the latest successful output of named upstream jobs. Example: a daily digest built from the news-fetch and PR-fetch jobs.
- **`continuity=true`:** a job sees its own last output so it can skip repeats. Silent ticks are ignored when picking that context.

**Failures and recovery**
- **Failure handling:**
  - Incidents are keyed by the job plus the error signature. The first failure alerts, repeats are held back, and a reminder comes after N hours.
  - The operator can acknowledge an incident.
  - A failure streak of 3 or more adds a "fix, pause, or remove?" nudge.
  - Transient network failures re-run automatically at 5, 15, and 30 minutes.
- **Recovery:**
  - Every fire has an identity. A finished result is never re-run, only re-delivered.
  - An interrupted run pauses for operator review and is not retried blindly.
  - Missed fires are caught up after a grace window.
- **Safety:**
  - Cron runs cannot create cron jobs.
  - Scripts must live in one scripts folder.
  - The script environment is cleaned of provider keys. Named credentials are passed through by explicit opt-in.
- **Storage:** jobs are plain JSON. Each run's output is saved as `output/{job}/{timestamp}.md`.

**Memory and skills**
- **Memory:** two small capped files.
  - MEMORY.md, about 2,200 characters, holds agent notes.
  - USER.md, about 1,375 characters, holds the user profile.
  - Both are injected as a frozen snapshot at session start.
  - If a write would go over the cap, it fails and the agent must consolidate. Nothing is dropped silently.
- **Skills:**
  - SKILL.md files (agentskills.io standard) with progressive disclosure: a list (~3k tokens), then the full skill, then a reference file.
  - Jobs attach skills by name, so the cron prompt stays short.

**Copy for QMX:**
- Job definition fields: trigger; pre-check script; steps; model pin; effort pin; skills; delivery target; `context_from`; `continuity`.
- Engine rules: no-agent mode, `wakeAgent`, `[SILENT]`, preflight that blocks with one alert, signature-keyed incidents, fire identity, and "cron cannot create cron".
- UI must show, per job: last status (ok / silent / blocked_config / failed / delivery_failed / unverified), failure streak, open incidents, and next fire time.

---

## 4. Animated documents

### What Kimi K3 launched
- Blog: https://www.kimi.com/blog/kimi-k3 (section "Research with Interactive Visualization"). Repo: https://github.com/MoonshotAI/Kimi-K3
- Shown in "Kimi Work":
  1. An **interactive research website**: 42 years of the AI ASIC industry, built with drill-down, bespoke charts, animated diagrams, and "interactive visual narratives". It drew on 2.8k+ searches, 1.1k+ terminal data pulls, and 99 PDFs, with 120+ self-improvement rounds.
  2. A **consulting-style report** with timeline, funnel, range-bar, and Gantt charts, plus slides.
  3. A **science analysis**: 391 events, 20+ parallel subagents, 7 visualizations, a literature synthesis.
  4. **Widgets and Dashboard**: interactive components in chat connected to live data, which can be pinned to a persistent dashboard per topic.
  5. A **3Blue1Brown-style motion explainer** of K3's own architecture, plus a teaser video it edited itself.
- What the operator saw is items 1 and 5: a research report that is a scrollable, animated web page, plus a short motion explainer.

### What Claude has
- **Inline visuals** (Mar 2026; started as the "Imagine with Claude" preview): https://claude.com/blog/claude-builds-visuals and https://support.claude.com/en/articles/13979539-custom-visuals-in-chat-and-cowork
  - Temporary charts and diagrams inside the answer; they change as the chat moves on.
- **Claude Design** (Apr 2026): https://www.anthropic.com/news/claude-design-anthropic-labs
  - Prototypes, slides, and one-pagers built from your design system.
  - Refined by chat, inline comments, direct edits, or Claude-made sliders.
  - Exports to PPTX or Canva.
  - Since Sep 2026 it lives inside every Claude chat.
- **Claude Dashboards and Claude Motion** (beta, 2026-10-08): https://claude.com/resources/articles/dashboards-and-motion
  - **Motion** turns a report into a roughly 30-second animated explainer.
    - **It is written as code** that animates your text, charts, shapes, and images.
    - It uses no video model, so every word, number, and timing can be edited.
    - It exports to MP4.
  - **Dashboards**:
    - Clicking any number shows the query behind it.
    - Each chart shows when it was last refreshed.
- So: yes, Claude has the same idea. Its key design choice is **animation as editable code over real data, with provenance on every number**.

### Tools to build it ourselves
| Tool | What | License / cost | Use in QMX |
|---|---|---|---|
| HTML + inline SVG + CSS transitions | Native | free | Default for every report |
| Scrollama (https://github.com/russellsamora/scrollama) | Scrollytelling: steps fire as you scroll, using a sticky graphic | MIT | "Story" reports |
| Mermaid | Text-to-diagram (flow, sequence, gantt, timeline) | MIT | Pipelines, timelines; models write it reliably |
| Motion Canvas (https://github.com/motion-canvas/motion-canvas) | TypeScript code-driven vector animation with an editor, built for explainers synced to voice-over | MIT | Optional short explainers |
| Manim (manim.community) | Python, 3Blue1Brown style | MIT | Math-heavy explainers only |
| Remotion (https://www.remotion.dev/docs/license/pricing) | React to MP4 | Free only for organizations of up to 3 people. Then $25/seat/month, or $0.01/render with a $100/month minimum | Avoid as a core dependency |

### What makes them readable without reading
1. **One headline claim per screen.** The number or verdict comes first; the prose is a caption.
2. **The picture carries the argument.** The diagram shows the actual mechanism or flow, not decoration.
3. **Progressive reveal.** Animation or scroll steps add one idea at a time, so the eye always knows where to look.
4. **Drill-down instead of length.** The summary sits on top; detail, sources, and raw data are one click away.
5. **Provenance on every number.** Click a number to see the query, file, or paper page behind it (as in Claude Dashboards).
6. **Consistent visual grammar.** The same colours mean the same things, such as pass/fail, long/short, or the model's opinion versus measured data.

### How an agent can make one reliably
- **Never let the model write free-form HTML for each report.** Instead:
  - QMX ships a small set of **fixed report templates**: React/HTML components with sanctioned motion.
  - The agent emits **structured JSON**: claims, numbers, chart specs, Mermaid source, citations, step order.
  - A deterministic renderer turns the JSON into the animated page.
  - This is the Kimi/Claude lesson ("data in, design fixed") plus Anthropic's "subagents write artifacts, pass references".
- **Grader step before delivery:**
  - The JSON validates against its schema.
  - Every number resolves to a source.
  - Mermaid parses.
  - The page renders headless without console errors, and a screenshot is taken.
- **Video (MP4) is optional and comes later.** Use Motion Canvas over the same JSON, and only for "explain this to someone else" moments.

---

## Templates QMX should ship first

Step kinds: script, rule, model, agent, human gate, sub-workflow, grader.

### T1. Morning brief (daily routine)
- **Trigger:** cron, every weekday 1 hour before the operator's main session opens.
- **Pre-check:** script. Wake only if something changed overnight: new positions, fills, alerts, calendar events, new papers in the watched categories. Otherwise `[SILENT]`.
- **Steps:**
  1. script: pull positions, P&L, economic calendar, overnight moves.
  2. rule: flag threshold breaches (drawdown, exposure, stale data).
  3. sub-workflow: run T4 macro snapshot (`context_from` its last output if it ran recently).
  4. model: write the brief JSON.
  5. grader: every number must trace to a script output.
- **Gates:** none. The brief is read-only.
- **Output:** a **one-screen dashboard card**: 3-5 headline tiles plus "what changed" plus links. No prose block.

### T2. Paper scout to research note (academic research)
- **Trigger:** cron every 6 hours, plus manual "research this paper/topic".
- **Pre-check:** script. Diff the arXiv q-fin.TR/PM/ST/RM RSS feed and the alphaXiv hot feed (free tools) against seen IDs. Wake only on new IDs.
- **Steps:**
  1. model (cheap): triage titles and abstracts against the operator's watch-topics; keep the top N. `continuity=true` avoids repeats.
  2. agent × N (parallel): read each kept paper via `answer_pdf_queries` with batched questions (claim, data, sample period, costs, out-of-sample result, code link). Budget 10 calls each.
  3. grader (citation checker): each claim must cite a page.
  4. model: synthesize the note JSON. State "testable as a strategy: yes/no, why".
  5. rule: if testable, propose T3 with the paper attached.
- **Gates:** **human gate** before anything enters T3.
- **Output:** an **explainer document**: a mechanism diagram, a key-results chart, a "will it survive costs?" box, and page-linked citations.

### T3. Strategy funnel: idea to paper trading
- **Trigger:** manual (video, paper, or TradingView idea), or from T2.
- **Steps:**
  1. agent: extract rules from the source into a strict strategy-spec JSON (entries, exits, sizing, universe, timeframe). For video, use a transcript plus frames.
  2. grader: the spec is complete and unambiguous. If not, a human gate asks the operator to fill the gaps.
  3. script: backtest with costs.
  4. script: out-of-sample run plus walk-forward.
  5. script: robustness checks (parameter jitter, a second market).
  6. rule: kill criteria (Sharpe after costs, max drawdown, trade count, OOS decay).
  7. model: write the verdict JSON.
  8. **human gate:** promote to paper trading?
  9. script: deploy to the paper account.
- **Gates:**
  - Kill rules are hard; the model cannot override them.
  - The human gate is required before paper trading.
  - Live trading is out of scope for templates.
- **Output:** a **funnel scorecard**: a funnel diagram showing which stage it reached, an equity curve, an IS-vs-OOS comparison, and the kill-rule table with ticks and crosses.

### T4. Macro snapshot
- **Trigger:** cron daily or weekly, plus an event trigger on a calendar release (CPI, NFP, central-bank decision).
- **Pre-check:** script. Wake only if the release is out and its data is fetched.
- **Steps:**
  1. script: fetch series.
  2. rule: compute surprise against consensus and z-scores.
  3. agent (research harness, budget 3 searchers): find the drivers and what the market priced.
  4. grader: citations and numbers check.
  5. model: write the regime JSON.
- **Gates:** none.
- **Output:** a **scrollytelling page**:
  1. the number,
  2. the surprise,
  3. what moved,
  4. the regime map,
  5. what it means for open positions.

### T5. Portfolio check (script-only watchdog)
- **Trigger:** cron every 5-15 minutes in market hours.
- **Steps:** a single script in **no-agent mode**: exposure, drawdown, data staleness, broker connectivity.
- **Behaviour:** silent unless a rule trips. On a trip it delivers the alert and can **wake** an agent with `context` to explain. Repeated alerts are grouped as one incident.
- **Gates:** none for alerts. A human gate for any action.
- **Output:** an alert card plus an incident entry. Zero tokens on quiet ticks.

### T6. Weekly harness review (self-improvement)
- **Trigger:** cron weekly.
- **Steps:**
  1. script: collect traces, costs, grader scores, and operator thumbs from the week.
  2. model: cluster failures.
  3. grader: rerun the eval set (about 20 cases per template).
  4. model: propose prompt or rule changes.
  5. **human gate:** approve the diff.
- **Output:** a **change card**: what failed, the proposed fix, and the score before and after.

---

## Output methodology proposal

Rule: **agents produce structured JSON; QMX renders it with fixed templates.** Prose is a caption or a drill-down, never the main body.

### Formats, ranked by default preference
1. **Dashboard card / tile row.** For routines and monitoring (T1, T5). One screen, numbers first, status colours, "what changed".
2. **Explainer document.** An animated page: headline claim, a mechanism diagram that builds step by step, 2-4 charts, a collapsible evidence section. For research results (T2, T3 verdict, T6).
3. **Scrollytelling story.** A sticky graphic that updates as you scroll through 4-7 steps. For narratives where order matters (T4 macro, "how this strategy makes money").
4. **Scorecard / funnel view.** Stage diagram plus pass/fail table. For any gated pipeline (T3).
5. **Short motion explainer (MP4, 20-40 seconds).** Motion Canvas rendered from the same JSON. Only when the operator wants to share or present. Later phase.
6. **Plain text.** Only for alerts and logs, one line each.

### When to use each
| Situation | Format |
|---|---|
| "Is anything wrong / what changed?" | Dashboard card |
| "What did you find?" | Explainer document |
| "Why did this happen / how does it work?" | Scrollytelling or explainer with an animated diagram |
| "Did it pass?" | Scorecard |
| "Show someone else" | Motion explainer |
| "Something broke" | One-line alert plus incident |

### What the UI must render
- **Report renderer:** takes report JSON and draws it with a fixed component set:
  - headline, KPI tile, chart (line, bar, range, funnel, heatmap, equity curve), Mermaid diagram, timeline, step-reveal block, scroll-story, kill-rule table, citation chip, collapsible detail.
- **Motion rules:**
  - Reveal one idea at a time; no autoplay loops.
  - Respect reduced-motion settings.
  - A "show all" switch for static reading.
- **Provenance on click:** every number and claim opens its source: script output row, query, file, or paper page (alphaXiv/arXiv link plus page number).
- **Freshness stamp** on every chart.
- **Run-status chrome** around each report:
  - template, trigger, cost, model per step, grader scores;
  - gate decisions with who approved and when;
  - link to the trace.
- **Human gate UI:** the report plus Approve / Reject / Ask-for-more buttons inline.
- **Job panel** (from Hermes): status, failure streak, open incidents, next fire, pause/resume, "run now".
- **Export:** HTML (self-contained), PDF, and later MP4.
- **Validation before display:**
  - The renderer rejects JSON that fails its schema, or numbers with no source.
  - The grader step catches these first, so the operator never sees a broken page.
