> **ON HOLD (2026-10-09):** do not start. COPILOT.md is being revised; modes are withdrawn.

# P24: Copilot modes, remaining hooks, session log and skill plumbing

## Goal
Implement the machinery from `rebuild/COPILOT.md`: modes, the remaining hooks, the session log with resume, headless runs, the skill registry, per-skill settings and the Build-mode lint gate. **Not the skill content.** Claude writes the skills with the operator.

## Read first
- `rebuild/COPILOT.md` (all of it)
- `rebuild/DESIGN.md` §5 and §12b
- `rebuild/research/skills-ecosystem.md` §2.3–2.4 and §7
- `rebuild/REFERENCES.md`: Deep Agents skills (`SkillsMiddleware`, `pinned_skills`, `include_tools`, skill permissions); LangChain middleware (`HumanInTheLoopMiddleware`, `PIIMiddleware`, call limits, `SummarizationMiddleware`)
- What P08, P15 and P20 already built in `qmx_agents.guards` and the Copilot. Reuse it; don't duplicate it.

## Build
1. **Modes** (COPILOT §2):
   - `copilot_mode` lives in graph state.
   - The mode table is in config (tools allow-list, approval list, model tier per mode).
   - ModeGate middleware filters and refuses tools.
   - The Copilot gets a `suggest_mode` tool: a lower mode applies at once; a higher one raises an interrupt.
   - Slash parsing (`/ask`, `/plan`, `/build`, `/run`, `/review`, `/<skill>` → `pinned_skills`) in `qmx-control`'s session API.
   - Stance setting (do it for me / pair / coach), per task.
2. **Hooks not yet built** (COPILOT §5): GrantIntersection, SecretsGuard, PlanGate, EvidenceBeforeClaims, ArtifactEmitter, ReviewLoopCap, ReturnAfterLaunch, SkillCheck (with a Settings toggle), PhaseBoundary, Audit, SkillWriteControl.
   - Use LangChain built-ins where they exist; anything custom is small middleware.
   - Order: security first.
3. **Session log** (COPILOT §6):
   - append-only JSONL per task under the session
   - resume offer keyed by run id
   - final artifacts rebuilt from the log
4. **Headless mode:** no interrupts reach a human. It ends with a JSON status of every assumption, registered as an "assumptions to confirm" artifact.
5. **Skill registry:**
   - discover skill folders (curated read-only, plus user-editable with approval)
   - read each `customize.toml` into Settings (UI-editable)
   - `copilot-guide` can list skills plus existing artifacts to suggest the next step
6. **Build-mode lint gate** (COPILOT §7, step 5): run before any app, workflow or skill draft is saved. Checks:
   - no money-path tools
   - declared capabilities match used tools
   - tests present
   - manifest or graph valid

   Failures come back as fixable messages.
7. **Placeholder skills:** keep P15's placeholders and add empty folders for the 13 skills in COPILOT §4 (name, one-line description, TODO body), so the registry and routing can be tested.

## Tests
With fake models:
- mode filtering and refusal, including that raising a mode needs an interrupt
- slash pinning
- each hook's rule
- resume after a simulated crash
- headless run producing the assumptions artifact
- the lint gate catching each failure type
- registry discovery and settings loading
