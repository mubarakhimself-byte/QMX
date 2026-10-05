# MA-01 capability adoption status

Implementation candidate. The original packet has serial installed read
acceptance; MA01-R1 fixes strict discovery opt-in for absent/empty maps.
Source checks and installed negotiation replay of the repair pass.
Independent parent review remains pending. [Exact Claude handoff](MA01-DISCOVERY-CONTRACT.md).

| Capability | Mounted implementation | Product acceptance |
|---|---|---|
| list_installed_plugins | CT-40; enabled live instances only | Revised installed negotiation/read replay passes |
| facade_search | CT-40; literal contribution class only | Revised installed negotiation/read replay passes |
| facade_get | CT-40; exact live ContributionHit plus instance/revision | Revised installed negotiation/read replay passes |
| discovery_hit_classes | Host-owned metadata: contribution only | Revised installed negotiation/read replay passes |
| invoke_contribution_pin | Optional existing pin at start_mission/launch_task admission | Original source/installed stale-pin refusal pass |
| get_instance_health | False/omitted; scoped owner not composed | Unavailable |
| Artifact/Knowledge facade | Explicit typed query_unavailable | Unavailable |
| get_pack_ui_request | Existing CT-40 and named HTTP read preserved | Source and installed read compatibility pass |
| Mini App candidates/validation/publish/deploy/maintenance/custom UI | MA-02 onward | Unsupported here |

No new search store, grants, mutation command, CLI or UI. This table is scoped to
MA-01; it is not a whole-release or fresh QMB-spawn reliability certification.
