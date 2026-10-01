# CORE sitting — SDK hybrid and placement (coaching evidence)

Not a spine. Not ratified. Altitude: construction-kit core, not trading-node redesign.

## Origin (operator transcript)

QMF was meant to be extensibility. It got too specific. Daily idea → yap at copilot → tools → reusable workflow → mini-app after tests. Workflows may be deterministic, agentic, or both. Two copilot firepowers. General edits; in-app does not. Each app ships access definitions. Loops can become mini-apps. On-prem and VPS both exist; unattended is a placement, not the kit.

## Placement (not “only QMA”)

| Noun | Host | Execution owner |
|---|---|---|
| Pack / plugin / sessions / Task Graph | QMA daemon | QMA compiles/runs procedures |
| Mini-app instance | QMA roster + grants | Each operation’s COMP (QMB/QML/QMN/QMF) |
| Widget | UI host as client of wire DTOs | None — display only |
| Board layout | Client chrome | Writes nothing |
| Venue / broker | QMN only | QMA must not import venue |

SDK = host contract (Capability Operation Interface) that QMA implements. Not “everything lives in qma-daemon.”

## Hybrid recommendation: Pack-and-grant kit

Rejected: Screen kit (dashboards first; fights headless packs). Automation kit (graphs first; board becomes the runner).

**Pack-and-grant:** one pack declares operations, optional views, asked-for access, optional copilot profile. Host grants. Workflows compose operations. Widgets are views of operations. Copilot sees only grants ∩ health. Weak models fill schemas.

Donor copy/refuse lives in the dedicated researcher return (Salesforce permission-set request, Bloomberg widget vs published app, GHL snapshot ≠ live data, n8n error workflow = observe, OpenBB providers ≠ widgets ≠ apps, VS Code contributes, Slack scopes, Hermes doctor fail-closed).

## Two copilots

- Authoring / general: build and revise (granted tools).
- App-use: inspect, run exposed ops, ask why from records, mint change-request. Cannot apply.
- QMA `sess:` underneath is the engine, not a third chat.
- Hole: home with no `app_instance_id` (code requires a string today). Fold into authoring-with-nothing-selected unless operator names a third seat.

## Weak models

Pin: descriptors, grants, typed refusals, skill≠grant, hit≠grant, hooks cannot override privilege. Defer: vendor model roster and prompt essays.

## Observability relationship (CORE)

Host exposes: listing axes (published/configured/granted/reachable/healthy), instance health, JobHandle, typed refusal, correlation_id join, harness telemetry. Copilot distinguishes broken grant vs broken workflow vs broken widget. UI later only renders those queries.

## 09-18 inherit vs do not reopen

CORE inherit: AD-1..10, 12–13, 15–21, 24, 26–27, 29–30.
APP inherit, do not re-elicit: AD-11, 14, 22, 23, 25.
Over-fit as kit law: AD-28 market cutover; AD-31 full catalogue (keep identity principle).

## Already decided here

- Default host retry for ordinary failures; no app-specific live-money design in this sitting.
- No sixth COMP. No new CT.
- No grok-4.7.
