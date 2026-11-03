# X7 problem solving (bmad-cis-problem-solving, run headless)

Stage B, layer X7 (agents for risk and sizing). Date: 2026-11-03. No human present; this agent played every role. The workflow's steps ran in order for each problem: define and refine, diagnose (is / is not, root cause), generate at least two solutions, weigh them, name what to monitor. Opinions are marked **[judgment]**. Nothing here ranks; the funnel judge ranks.

Component ids are short forms: `A4-104` is `A4-template-agents-telemetry-104`, and so on for A1 to A5. Hybrid ids (`X7-H..`) point at `expansion/X7-agents.md`.

---

## P1. Ruling 2 forbids automatic size-down from agent evidence

- **Refined statement.** G2 ruling 2 says the only automatic change in trading is a unit's own risk rule stopping it. The research consensus (A1-132, A2-018, A3-145, A4-104) wants agents to emit de-risk multipliers that a deterministic service applies at once. Drift handling (A2-133, his "size down, but not quickly") also needs automatic size steps. As written, ruling 2 blocks both.
- **Is / is not.** It is a governance gap, not a technical one: the node can already stand a unit down. It is not about agents trading: no option lets an agent send an order.
- **Root cause.** Ruling 2 was written when the only automatic actor was a stop. It names one direction (stop) and one owner (the unit's own rule). Size steps and outside evidence were not in view.
- **Solution A: evidence as a declared fact (X7-H03).** The unit's template lists the evidence kinds its own rules may read, with a per-kind largest cut and time to live. The agent's record is an input; the unit's rule decides and acts. Missing or stale evidence means no change. *Trade-off:* keeps ruling 2's letter; needs a feed path to the node (like the MIS board relay, unbuilt) and a new template section; he must still accept that an outside opinion can shrink a unit.
- **Solution B: amend ruling 2 to "automatic changes are monotone toward less risk."** Any declared rule at unit, Book or BMS level may cut automatically; raising stays with him. *Trade-off:* simpler and covers drift steps, isolation and BMS breakers in one sentence; it is a change to a binding ruling, so it is his call (question 1).
- **Solution C: cards only.** Every agent-sourced cut is a card he clicks. *Trade-off:* no ruling change; but cuts that matter arrive hours late (he sleeps; P11), and the queue floods (P2).
- **Monitor.** Share of agent-driven cuts that preceded a loss (precision), and the cost of the cuts (A5-073, A4-202).

## P2. Noise: agents flood him with cards he ignores

- **Refined statement.** Agents are cheap to run and can file a card for every unit every night (A4-147's own failure note: "one card per night per unit can flood him across forty units"). Alarm studies show 85-99 % of alarms needing no action leads people to mute them (A2-030, A4-202). A muted queue is no queue.
- **Root cause.** Proposal cost is near zero for the agent and high for him. Nothing prices his attention.
- **Solution A: one attention budget (X7-H15).** A hard cap on cards per day, set by him or measured from his review rate (A5-056 queue telemetry); cards ranked by expected money per minute of reading; overflow becomes digest lines or expires. *Trade-off:* simple and visible; a low cap can starve a good but low-ranked card.
- **Solution B: per-agent credit (X7-H18, H10).** Each agent profile holds a quota or testing wealth; accepted-and-held cards refill it, reversals and ignores drain it (AIMD on quota). *Trade-off:* self-tuning and fair across agents; adds variables and can starve a new agent with no record.
- **Solution C: graduation (X7-H16).** A card type he accepts often with no reversal is offered as a pre-authorised rule, so it stops being a card. *Trade-off:* removes repeat clicks at the source; risks rules he approved once and forgot.
- **Solution D: dedupe and digest (X7-H17).** Group cards by root cause (A4-160) and the hours clause (A2-026); one incident, one card. *Trade-off:* cheap; grouping can hide two real problems under one.
- **Monitor.** Queue burn rate (A5-053), ignore rate per card type, reversal rate (A5-056).

## P3. Agents raise risk by stealth

- **Refined statement.** "LLM output may only lower risk" is easy for a multiplier. It leaks through side doors: a tuning proposal that widens a range, a window that lifts size, a restore step, a derivation swap, a scenario set gamed to pass, a block that passes safety checks yet sizes wrong.
- **Root cause.** Direction is checked on one channel (the multiplier), not on every effect.
- **Solution A: monotone action lattice (X7-H02).** Every tool and app operation carries a declared direction (read, propose, de-risk, re-risk, money); the host refuses any re-risk or money effect from an agent principal, as it already refuses `manage` operations (`qmx_host/host_route.py` `admits`). *Trade-off:* structural and testable; needs a direction field on catalog rows and app operations (QMA flag).
- **Solution B: effect descriptor lists every ledger id touched (X7-H04).** Layer H walks the ledger's `affects` edges from the edited ids; any edge whose direction raises risk marks the card re-risk, whatever the agent called it. *Trade-off:* catches indirect raises; depends on the ledger's couplings being complete.
- **Solution C: shadow before anything sizes (A4-030, A2-145).** Every proposal runs as would-have rows first. *Trade-off:* catches wrong sizes in practice; slow for low-frequency units.
- **Monitor.** Count of cards re-labelled re-risk by layer H; approvals later reversed.

## P4. Search luck in agent tuning, windows and isolation rules

- **Refined statement.** Agents can try thousands of windows, arms and thresholds. The best of many tries looks good by chance (A2-202: every LLM-discovered strategy failed honest evaluation; the bar rises faster than the best in-sample Sharpe).
- **Solution A: one search ledger for alpha and risk (X7-H09).** Every risk trial gets a trial id; a risk-profile promotion is deflated by its family's tries, as strategies are. *Trade-off:* honest; slows promotion of real improvements.
- **Solution B: funded tests (A4-121 Promote) on fresh results only.** *Trade-off:* controls false promotion for the whole life of the system; near zero power for very small edges (5 bp never crosses).
- **Solution C: plateau-only tuning with locked parameters (A4-198) and a conservative bandit among few arms (A4-199).** *Trade-off:* fewer trials by design; may miss a narrow real optimum.
- **Monitor.** Trials per family per month; deflated bar; share of promoted risk changes later reversed.

## P5. Poisoned inputs: fake news, prompt injection, tool content

- **Refined statement.** Fabricated news moved LLM agents 62 % of the time in a sandbox; two 30-word templates 100 % (A4-108). Prompt injection travels through logs, headlines and source files (A4-138, MQL5 24265).
- **Solution A: de-risk-only with a single-item cap and corroboration widening (X7-H39).** *Trade-off:* a fake can only cut a little and expires; repeated fakes still cost trades.
- **Solution B: strip credibility cues and route through hierarchical aggregation (A4-108).** *Trade-off:* the only tested defence that reduced attack success; adds a preprocessing stage.
- **Solution C: red team on a schedule (A4-138, A5-058).** *Trade-off:* finds paths before they cost money; only listed attacks are tested.
- **Monitor.** Injected-fault recall (A5-050), contagion map (A5-058).

## P6. Slow isolation: who switches a class off on twenty days of evidence

- **Refined statement.** His protocol "should kick in with the evidence" (C27, C28), including "analysis... over 20 days". A minute tell cannot see a slow bleed (A3-113, A3-203). An agent must not switch a class off by itself.
- **Solution A: nominate, confirm, apply (X7-H21).** The agent files a nomination with evidence; a deterministic two-tell check (A3-109) runs on the same window; if it passes and he has pre-authorised class isolation, the BMS applies it with a time to live and staged resume (A3-107); otherwise it becomes a card. *Trade-off:* acts without waiting for him on confirmed evidence; needs class and region scopes the node lacks (G9 4.4).
- **Solution B: card only (A3-113 as written).** *Trade-off:* simple and within today's rules; waits for his click.
- **Solution C: the MIS publishes isolation and placement fails closed (A3-115).** *Trade-off:* the MIS already has a board; collides with "the MIS never switches" (A3-184).
- **Monitor.** Isolation precision (did a loss follow in the class?), false isolation cost (A3-199).

## P7. The de-risk-only ratchet starves growth

- **Refined statement.** If agents can only cut, and cuts are automatic while raises need clicks, units drift toward minimum size: the "sitting duck" he rejects (M33). A tighten-only ratchet on noisy estimates drives every unit to minimum (A1-064).
- **Solution A: restore with equal standing (X7-H05).** A pre-authorised restore ladder runs on an e-value over post-cut trades plus a minimum time (A1-064, A2-221); no click per step. *Trade-off:* growth comes back without him; one more ruling question (question 4).
- **Solution B: an advocate agent (X7-H32).** Its only job is restore and accelerator cards carrying the money braked units missed (A5-073). *Trade-off:* puts growth on the same footing as safety in his queue; adds cards.
- **Solution C: every cut carries its own release rule (A5-103 definition of restore).** *Trade-off:* no cut is permanent by design; release rules need their own tests.
- **Monitor.** Under-baseline share and missed return per unit (A5-073).

## P8. Plug-in readiness: Lab, MCP agents and the department without rework

- **Refined statement.** He wants the design to adapt now so nothing is rebuilt later (M36). Tools could live as `qmx_control` catalog rows (X1-43) or as a risk mini app's MCP server.
- **Solution A: risk mini app with an MCP server (X7-H36).** `risk = "runs"`, declared operations with direction and approval, typed `provides` for cards and evidence. *Trade-off:* any MCP client uses the same surface; apps cannot yet land component entries or reach the node beyond the board relay (G8 6.4).
- **Solution B: catalog rows only (X1-43).** *Trade-off:* fastest to build on the shipped rows; chat agents get them, outside MCP agents do not without a bridge.
- **Solution C: both, one implementation.** Rows call the app's operations. *Trade-off:* one code path; two names for one tool.
- **Monitor.** Count of tool definitions duplicated across catalog and app.

## P9. Proving an agent adds value

- **Solution A: ablation (A4-137):** no agent, features only, agent, agent plus service. *Trade-off:* the clean test; needs a fixed tape.
- **Solution B: matched random de-risker (X7-H11, A2-135):** an agent's cuts must beat random cuts of the same count and size, per class. *Trade-off:* the strongest single filter; needs enough cuts to judge.
- **Solution C: alerting scorecard (A5-050):** precision, recall, lead time, cost per incident against a simple detector. *Trade-off:* ReguSim's logistic regression beat the best LLM (F1 89.2 % against 70.9 %), so agents may lose their detection jobs; that is the point.

## P10. Which styles may receive agent evidence at all

- **Refined statement.** LLM decisions took about 187 s in a crypto paper study (A3-087). A 1-minute scalper's next bar arrives before the evidence does.
- **Solution A: style eligibility list:** evidence may reach a unit only if its time to live is longer than the unit's typical holding time times a factor; scalpers get only session-level evidence (open caution, class isolation). *Trade-off:* honest about latency; scalpers get little agent help.
- **Solution B: evidence acts on the next session, not the next bar.** *Trade-off:* simple; slow for intraday shocks.

## P11. He is away or asleep

- **Solution A: three rules by direction:** de-risk evidence acts through unit rules at once; re-risk and structural cards wait; nothing raises risk while he is away. *Trade-off:* safe; growth waits.
- **Solution B: card time to live counted in his waking hours,** plus a morning brief that batches the night (X7-H46). *Trade-off:* cards do not die unread; he must say his hours.

## P12. Model upgrades change agent behaviour

- **Solution A: re-qualification on model change:** a model or prompt change is a new agent version; its autonomy level resets to advise-only until it passes the replay and random-control tests again (A4-113 pinned snapshots, A5-078 autonomy). *Trade-off:* safe; slows adoption of better models.
- **Solution B: shadow the new model beside the old one on the same tape** and promote it by the scorecard. *Trade-off:* cheaper re-qualification; doubles inference while shadowing.

## P13. Many agents, one model or one feed

- **Solution A: count evidence once per model family and per feed** in corroboration (A1-132's note, A4-108). *Trade-off:* honest; reduces what corroboration can unlock.
- **Solution B: measure agent independence** from the correlation of their records over time; corroboration counts effective agents. *Trade-off:* adds a measure (gap: no component has it).

## P14. Money MCPs as a second road

- **Refined statement.** The build session is shipping a cTrader MCP (and he wants Hyperliquid). At the stack tip, the trading-node app's MCP server lists `kill`, `pause`, `resume`, `flatten`, `deploy` and `bind` as `manage` operations, and the host answers those only to the operator. An MCP server outside the host door would not have that guard. Not checked: what the build session's cTrader MCP exposes.
- **Solution A: one road:** venue MCPs live only inside the trading-node app; agents reach the venue only through read operations. *Trade-off:* keeps the guard; outside tools that expect a direct broker MCP must go through the app.
- **Solution B: a read-only broker MCP for agents** (quotes, symbols, history, account read), never order tools. *Trade-off:* agents get market data directly; the read-only scope must be enforced by credentials, not by tool lists.

## P15. When should an agent stop doing a job

- **Solution A: graduation by recurrence (X7-H27):** a finding the agent repeats N times is drafted as a deterministic detector block and goes through the block trust ladder; the agent then only explains it. *Trade-off:* cheaper and testable over time; agents shrink their own role.
- **Solution B: job registry with a razor review:** each agent job states why a script cannot do it; the review repeats quarterly. *Trade-off:* light; relies on someone running the review.

---

## Lessons from the run

- Most problems split cleanly by **direction**: cuts can be automatic and deterministic; raises need evidence and his consent, once or per step. Every solution above is a version of that split.
- The two scarce resources are **his attention** and **honest evidence**. Agents are cheap; both scarce things need budgets.
- **[judgment]** The single highest-leverage change is solving P1 (ruling 2), because P6, P7 and drift all hang on it.
