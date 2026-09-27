---
name: Implementation sequence — pack-and-grant kit
sitting: architecture-QMX-2026-09-23
---

# Implementation sequence

Planning only. Factory later. After Documentation Factory + epics.

0. **Honesty:** treat `integration@34c148b` fixtures as connect/amend, not e2e.
1. **Host SDK:** pack manifest copilot_profile optional; authoring `app_instance_id` optional; `caller_kind` on envelope.
2. **Daemon JSON-lines + diagnosis query** (failure_class + JobHandle + correlation_id).
3. **Default retry** wired to existing effect-class matrix.
4. **Nested Mission invoke** (workflow-to-workflow) with recursion budget.
5. **Listing axes + instance health** for copilot/CLI.
6. UI chrome (GAP-0081) consumes the same queries. Not this epic set.
