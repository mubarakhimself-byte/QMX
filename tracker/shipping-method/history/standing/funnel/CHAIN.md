# The chain: ids and file shapes every funnel stage writes

Shared reference for the `funnel-*` skills and `PLANNING-FUNNEL.md`. One feature is one chain, from his words to code. Every level names the level above it, so a builder can walk from its slice back to the reasoning, and `check_chain.py` can prove the links.

## Levels and ids

| Level | Id | Written by | Lives in | Names the level above with |
|---|---|---|---|---|
| L0 his words | quote + source | funnel-expand | `SCOPE.md`, inside each ask | `(<id8>:L<line> (<session title>, <date>))` as `his_words.py` prints it, `(<file>:<line>)`, or `(agent note, <file>)` for an agent's record of his ruling |
| L1 his asks | `S1`, `S2` | funnel-expand | `SCOPE.md` as `- **S1.** "<quote>" (<where>)` | the quote |
| L2 plan lines | `S1.a`, `S1.b` | funnel-anneal (plan mode) | `PLAN.md` as `- **S1.a** <what is true when done>` | the id prefix |
| L3 architecture | `A1`, `A2` | funnel-architect | `arch/ARCH.md` as `- **A1** (S1.a, S2.b) <element>` | the plan ids in brackets |
| L4 slices | `<prefix>-01` | funnel-handoff | `SLICES.md` row, `slices/<id>/BRIEF.md` | `Serves: S1` and `Chain: S1.a; A1; E2` lines in the brief |
| L5 code | the PR | builder | PR body | the slice id |

Side records, each with its own id:

| Record | Id | Lives in | Shape |
|---|---|---|---|
| Questions (gaps in context) | `Q1`, `Q2` | `ANNEAL-LOG.md` | one row per question, see below |
| Decisions | `D1`, `D2` | `decisions/D1-<slug>.md` | see below |
| Proposals | `P1`, `P2` | `SCOPE.md` Proposals | `- **P1.** <idea>. Why: <line>. Would serve: <S-id or none>` |
| Edge cases | `E1`, `E2` | `EDGE-CASES.md` | `- **E1** (S1.a) <scenario>. Must hold: <expected behaviour>` |
| Can-change candidates | `X1`, `X2` | `CAN-CHANGE.md` | `- **X1** <delete/change/merge> <what>. Serves: ... Callers: ... Blast radius: ... Frees: ... Decider: agents/him.` |
| Removed, and why | `R-<program>-1` | planned: `<program>/REMOVED.md`; once merged: `C:/Users/Mubarak/Desktop/QMX/tracker/REMOVED.md` | `- **R-pods-1** <what>. Why: <reason>. Decided by: him (<source>) / agent. Status: planned (<program>, <date>) / removed <sha>` |

**Retired ids.** When he changes his mind, an id is never reused. Strike it where it lives (`~~S1.b~~ retired 2026-11-14: <why>`) and give the new meaning a new id. `check_chain.py` fails any brief or chain row that still cites a retired id.

**Decision numbers.** Only the lead session writes decision files. It takes the next free number by listing `decisions/` just before writing; the checker fails duplicate numbers.

## SCOPE.md additions

`SCOPE.md` follows `standing/templates/SCOPE.md`, with three additions under the title:

```markdown
Ask as given: "<the words the planner was given>" (<who gave it, where>)
Expand depth: <light|medium|deep>, because <one line>

## Restatement
<plain words: his goal and the problem>
To confirm with him: <the restatement, the depth, each open decision>
```

His words come from `python standing/funnel/his_words.py <regex>...`. It prints only the turns he typed, skipping tool output, compaction summaries and relayed messages, each with its source.

## ANNEAL-LOG.md

Append-only. One section per round, newest last. Both modes share the file, and round numbers run across both (a plan round after stage 5 takes the next number). A round is written to `rounds/round-<n>.md` while it runs and appended here only when complete, so a crash leaves a round file to delete and rerun, never a half round in the log.

```markdown
## Round 2 (plan mode, 2026-11-12)

| Q | Lens | The gap | Kind | Filled by | Context added | Source |
|---|---|---|---|---|---|---|
| Q7 | linking logic | "pod rules" is vague: rules of what, enforced where? | vague | agent, by analogy | Like a hedge-fund pod's mandate: ... | POD-DEFINITION.md:7 |
| Q8 | attack the premise | Do his two exit statements conflict? | decision-his | pending D3 | Recommendation: ... Because: ... | SCOPE.md S2, S4 |

New questions this round: 2. Stop: no.
```

- **Kind** is one of: `fact` (looked up), `vague` (grounded by analogy or reference), `edge` (became an `E` row), `change` (became an `X` row), `defect` (the subject was fixed), `decision-his`, `decision-tech`, `dup` (already asked; `dup of Q<n>`, not counted as new).
- **Filled by** is `agent`, `agent, by analogy`, `agent, by reference`, `him (D3)`, `fable (D5)`, or `pending D3`.
- Each annealing pass ends with a stop line naming its mode: `Stopped after <rounds in this mode> rounds (plan mode): round <n> raised no new question.` A re-anneal adds rounds and a new stop line; the checker reads the last one per mode.
- The words "dissolved" and "folded" never appear: a question is answered, or it is open.

## decisions/D<n>-<slug>.md

```markdown
# D3: <the question in plain words>

Status: open | settled
Mode: plan | technical
For: him | fable
Raised by: Q8 (round 2) | stage 1 | spine AD-3

## Recommendation
<the agent's best answer, in plain words>

## Why
<the reason, citing files and lines>

## Answer
<his quoted words with their source, e.g. "the pod carries it" (dd8f4ab2:L2600 (Shipping rate..., 2026-11-12));
 or "Fable decided X because Y"; or "Opus decided X because Y (Fable unavailable: <reason>)"; empty while open>
```

Who decided is data the checker reads. A settled `For: him` decision needs his quoted words with a transcript source and never the word "decided"; an agent's answer is always logged as the agent's. A decision that reaches him always carries a recommendation and its reason, and no agent settles a `For: him` decision. A `For: fable` decision is logged only after a fresh Opus check found no product call or fixed line in it; a hidden one becomes `For: him`. From stage 5 on, an open `For: fable` decision fails the check.

## Slices, checkpoints, lanes and the merge request

- **Checkpoints.** Each slice's `stop` column is its checkpoint. That is where review runs and the work merges, because the build has no reviewer per slice. Aim for 5 to 8 slices each.
- **Lanes.** Its `lane` column says who does what. Slices in different lanes of one checkpoint share no files, so their builders run at once.
- **The brief carries its links:**
  - `Serves:`, `Stop point:`, `Lane:` and `Chain:` lines;
  - part 7a, with one line per `E` id naming its test;
  - an `Operations:` line naming its test;
  - part 11, the merge request, with `TRACE: <slice> -> <plan ids> -> <ask>`. That line is the L4-to-L5 link the PR body carries.
- **The chain packet.** `chain_packet.py` generates `slices/<id>/CHAIN.md` from the files above, so the builder reads its part of the chain without opening six files.

## PROGRAM.yaml chains section

After `run_files:`, one row per ask. Never use `- id:` here: `check_plan.py` reads every `- id:` line as a stop point.

```yaml
chains:
  - ask: S1
    plan: [S1.a, S1.b]
    arch: [A1, A3]
    slices: [pd-01, pd-02]
    edge_cases: [E1, E4]
```

Check any stage with `python C:/Users/Mubarak/Desktop/QMX/tracker/shipping-method/standing/funnel/check_chain.py <program folder> --stage <expand|ground|anneal|arch|technical|handoff>`.
