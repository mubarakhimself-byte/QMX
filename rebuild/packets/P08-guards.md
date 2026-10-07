# P08: Guards (journal, admission, money path, budgets)

## Goal
Port QMX's real invariants from the old daemon into small LangChain middleware and backend wrappers in `qmx_agents.guards`.

## Read first
The P05 survival map §2 (where the rules live today); `rebuild/DESIGN.md` §5.7.

## Build
- **Journal middleware**
  - Append-only JSONL per run, in the profile or app volume. It records:
    - run start and end
    - model call metadata
    - tool calls: name, a hash of the arguments, and a reference to the result
    - interrupts and approvals
  - Reuse the existing journal format if P05 shows it is simple; otherwise use a new minimal schema.
  - One writer per file.
- **Admission backend wrapper**
  - Wraps the Deep Agents backend for `/artifacts/` and for global memory writes.
  - Enforces the existing admission rules, ported from the old code.
- **Money path**
  - Tools carry a registry flag `money_path=True`. `build_agent` refuses any spec that lists such a tool.
  - The only allowed money tool is `propose_order`. It writes a proposal for the operator to sign and never sends an order.
- **Budgets**
  - `ModelCallLimitMiddleware` and `ToolCallLimitMiddleware`, set from `spec.budget` and overridable in UI config.

## Tests
- A spec listing a money-path tool is rejected.
- `propose_order` never calls a venue.
- The journal records a full fake run.
- Admission refuses a disallowed write.
- The budget stops a looping fake agent.
