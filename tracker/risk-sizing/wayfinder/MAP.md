---
label: wayfinder:map
title: QMX unit system map
created: 2026-10-24
---

# QMX unit system map

## Destination

An agreed design, reviewed for edge cases and ready for `bmad-architecture`, covering two things:
- **The unit management system:** units, the registry, the MIS router, self-tuning sizing, and the lifecycle from source to live.
- **The kit agents and people use to build strategies of any depth, for any instrument a broker offers:** QML, the Lab, QMB, and plain Python.

## Notes

- **Three lenses on every ticket, none rigid:**
  - **Agents and code:** QML, QMB, QMF and the node must work for agents, be connected, and run.
  - **Traders:** what someone trading each instrument needs: data, indicators, sessions, complexity.
  - **Creators:** anyone can build what they imagine in plain Python. Copy what MT5, cTrader and NinjaTrader do well instead of reinventing it.
- **Where ideas land (QMX surfaces):** the Lab (building and testing), Pods (risk, sizing, portfolio management and optimisation), the Copilot (the agentic system), Mini apps (some ideas ship as mini apps; templates exist), and the algo side (QML, QMB, QMF, MIS, node). Hybrids and new lenses are welcome.
- **Scope rule (operator, 2026-10-24):** nothing is out of scope or blocked. Anything may be touched, but every proposal names what it touches and how. Never casually remove backend work that has already shipped; it took 2-3 weeks to ship.
- **Broaden before architecture.** StrategyQuant (SQ X, the What-If scenario generator, the fitness/ranking ideas, QuantAnalyzer, QuantDataManager, its AI assistant) is the anchor for testing, QMB and the Lab. Expand on it hard; look for hybrids and novel improvements. QuantConnect, NinjaTrader and MT5 are also donors.
- **Inputs, in rank order:**
  1. The operator's word.
  2. `workroom/risk-lab-2026-10-05/seeds.md` (his seeds).
  3. `decisions.md` there.
  4. `grounding/09-original-design-recovery.md`.
  5. `docs/` and `_docwork/` (QMB's intended design is there).
  6. Code, only to confirm.
- **The compounding test:** a part is good if it raises edge per trade, trade count, right size, or cuts drag, and the Judge step can prove it.
- **Skills:** `research` for research tickets; `bmad-party-mode`, `bmad-brainstorming`, `bmad-cis-*` and `bmad-forge-idea` in the funnel, uncapped; `grilling` and `domain-modeling` on HITL tickets; `bmad-review` (adversarial, edge-case, verification-gap) for the review; `bmad-architecture`, `domain-modeling` and `codebase-design` last.
- **Preferences:** plain short English; explainer pages for the operator; claims labelled checked, remembered or inferred; every number configurable; Opus agents, at most three at once.
- Frontier: `python frontier.py`.

## Decisions so far

(none yet)

## Not yet specified

- How the trading node session follows this one.
- Pods (they wait on the unit).

## Out of scope

- Nothing (operator, 2026-10-24). Changes outside the unit system name their blast radius.
