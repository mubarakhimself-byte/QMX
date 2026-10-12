# How agent tools present model choice and defaults
Fetched 2026-10-12. Every claim carries its source URL. UNVERIFIED = not confirmed on a primary page.

## 1. Claude Code
Source: https://code.claude.com/docs/en/model-config (fetched 2026-10-12)
- Picker: `/model` with no argument opens it; `/model <alias|name>` switches directly. Enter saves as default; `s` = this session only.
- Aliases: `default`, `best`, `fable`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`, `opus[1m]`, `opusplan` (opus in plan mode, sonnet for execution).
- Aliases track latest: "Aliases point to the recommended version for your provider and update over time." On the Anthropic API: opus -> Opus 5.5, sonnet -> Sonnet 5.5, haiku -> Haiku 5.5.
- Default by plan: Pro, Max, Team, Enterprise, API -> Opus 5.5; Microsoft Foundry -> Sonnet 4.5. Fable is not the account default on any plan.
- Precedence (high to low): `/model`, `--model`, `ANTHROPIC_MODEL`, `model` in settings, `ANTHROPIC_DEFAULT_MODEL`. Project/managed settings override user choices; managed `availableModels` restricts the picker.
- Alias targets are env-overridable: `ANTHROPIC_DEFAULT_OPUS_MODEL`, `_SONNET_MODEL`, `_HAIKU_MODEL`, `_FABLE_MODEL`; `ANTHROPIC_CUSTOM_MODEL_OPTION` adds one picker row.
- Background/small model: "`ANTHROPIC_SMALL_FAST_MODEL` is deprecated in favor of `ANTHROPIC_DEFAULT_HAIKU_MODEL`." The Haiku var is the target for "haiku and background work".
- Effort dial: levels low/medium/high/xhigh/max (4.6 models lack xhigh). Defaults: medium on Opus/Sonnet/Haiku 5.5, high on most others. Set via `/effort` (slider, or `auto`), `--effort`, `CLAUDE_CODE_EFFORT_LEVEL`, `effortLevel`/`modelSettings` in settings, or `effort` in skill/subagent frontmatter. `ultrathink` boosts one turn.
- Fast mode: https://code.claude.com/docs/en/fast-mode . `/fast` toggles; "not a different model" (Opus only: 5.5, 5, 4.8); up to 2.5x faster; $8/$40 per MTok on Opus 5.5. On subscriptions it bills via usage credits only, not plan limits. `fastMode` setting persists; `fastModePerSessionOptIn` resets per session. A `↯` icon shows when on.
- Cost surfacing: fast-mode spend appears in Settings > Usage (claude.ai) or `/usage`; Console has a "Speed" group-by. https://code.claude.com/docs/en/fast-mode
- Subagents: https://code.claude.com/docs/en/sub-agents . Frontmatter `model` accepts `sonnet|opus|haiku|fable`, a full ID, or `inherit`. Resolution: per-invocation param > frontmatter > `CLAUDE_CODE_SUBAGENT_MODEL` > main model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model on all. Frontmatter `effort` field exists too.
- Built-ins: Explore uses main model (on subscription/Console, the `opus` alias); statusline-setup = Sonnet; claude-code-guide = Haiku. Same page.

## 2. OpenAI Codex
Docs now redirect from developers.openai.com/codex/* to learn.chatgpt.com/docs/* (308 redirect observed 2026-10-12).
- Picker: https://learn.chatgpt.com/docs/models . CLI `/model` (and `--model`/`-m`, `codex exec -m`); desktop/web has "Power presets" (e.g. Smarter/Faster) plus an Advanced pane for model, effort, speed.
- Models listed: GPT-6.1 Sol (recommended), Astra (most capable), Luna (most efficient). Plan gating: Plus/Pro/Business/Enterprise/Edu get Sol; Free/Go do not at launch. GPT-5.5 retires 2026-10-14 (same page).
- Effort: Light(=Low in CLI)/Medium/High/Extra High; "Max" gives more time on one task; "Ultra" uses subagents in parallel. Same page.
- Config reference: https://learn.chatgpt.com/docs/config-file/config-reference
  - `model`, `model_reasoning_effort` (low..xhigh, max, ultra), `plan_mode_reasoning_effort`, `service_tier` (`fast` maps to request value `priority`).
  - `review_model`: "Optional model override used by `/review`".
  - Compaction: no model key; only `model_auto_compact_token_limit` (token threshold).
  - Other slots: `memories.extract_model`, `memories.consolidation_model`.
  - `agents.default_subagent_model` and `agents.default_subagent_reasoning_effort`; "An explicit spawn model takes precedence."
  - Profiles: `--profile`, files at `$CODEX_HOME/<name>.config.toml`; project-local `.codex/config.toml` cannot set profile keys.
  - (Only first ~100k of 158k chars of this page were read.)
- Cost: API-key use is "billed at standard API rates"; ChatGPT sign-in draws on plan. https://learn.chatgpt.com/docs/auth

## 3. Hermes Agent (Nous Research)
- Model switching: `hermes model` or `/model [provider:model]` on CLI and messaging platforms. https://github.com/NousResearch/hermes-agent
- Config layout: `~/.hermes/config.yaml` (settings), `.env` (secrets), `auth.json` (OAuth creds), `SOUL.md`. Priority: CLI args > config.yaml > .env > defaults. https://hermes-agent.nousresearch.com/docs/user-guide/configuration
- Auxiliary slots under `auxiliary.<task>`: vision, approval, compression, title_generation, skills_hub, mcp, triage_specifier, tts_audio_tags (plus picker entries voice_chat, kanban_decomposer, profile_describer); `delegation.*` is separate (subagents). Same page.
- Per-slot keys: `provider` (default "auto"), `model` (default ""), `base_url`, `api_key`, `timeout`, `fallback_chain`, `max_concurrency`, `reasoning_effort`. Default: "auto" routes every aux task to the main chat model. Same page.
- Constraint: compression summary model's context must be >= main model's or middle turns are dropped. Same page.
- Web extraction is NOT an auxiliary LLM task in current docs (AUXILIARY_WEB_EXTRACT_* obsolete). Same page.

## 4. Cursor
- https://cursor.com/docs/models : two usage pools (third-party "Other Models" at API rates; "Cursor Models" separate); both visible "in your editor settings and on your usage dashboard"; prices listed per MTok.
- Auto: "three modes: Cost, Balance, and Intelligence"; each request bills at list price of the routed model; not on Start plan.
- Max Mode: legacy request-based plans only; extends context; API rate +20%.
- Cloud/background agents: https://cursor.com/docs/cloud-agent . Curated model set, selectable context window, billed at API price of chosen model; spend limit set on first use. Default model and per-mode defaults: UNVERIFIED (not stated on fetched pages).

## Common patterns (synthesis)
- Per-session choice: all four have an in-session picker plus launch flag; Claude Code and Codex also persist a default in config.
- Per-subagent choice: Claude Code frontmatter `model`/`effort` with `inherit` plus env default; Codex `agents.default_subagent_model`; Hermes `delegation.*`. Explicit per-spawn beats default beats inherit.
- Auxiliary/background slots: Hermes has the richest explicit list (each slot: provider/model/timeout/fallback); Codex has named slots (review, memories); Claude Code folds background work into the Haiku alias; compaction has no model slot in Codex.
- Effort dial: low..max across Claude Code and Codex; set per session, per profile/subagent, overridable by env.
- "Auto" routing: Cursor Auto (Cost/Balance/Intelligence); Claude Code `opusplan` and `/effort auto` are lighter analogues; Hermes provider "auto".
- Aliases over IDs: Claude Code aliases float with releases and are pinnable via env; Codex pins by name.
- Cost surfacing: Cursor dashboard pools; Claude usage page and `/usage`; Codex per-app limits and plan credits; Hermes surfaces none in the fetched pages (UNVERIFIED).
