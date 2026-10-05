# MA-01 capability adoption status

Implementation candidate; serial installed acceptance passes. Independent parent
review remains pending. [Exact Claude handoff](MA01-DISCOVERY-CONTRACT.md).

| Capability | Mounted implementation | Product acceptance |
|---|---|---|
| list_installed_plugins | CT-40; enabled live instances only | Installed paired listener passes |
| facade_search | CT-40; literal contribution class only | Installed paired listener passes |
| facade_get | CT-40; exact live ContributionHit plus instance/revision | Installed paired listener passes |
| discovery_hit_classes | Host-owned metadata: contribution only | Installed paired listener passes |
| invoke_contribution_pin | Optional existing pin at start_mission/launch_task admission | Source and installed stale-pin refusal pass |
| get_instance_health | False/omitted; scoped owner not composed | Unavailable |
| Artifact/Knowledge facade | Explicit typed query_unavailable | Unavailable |
| get_pack_ui_request | Existing CT-40 and named HTTP read preserved | Source and installed read compatibility pass |
| Mini App candidates/validation/publish/deploy/maintenance/custom UI | MA-02 onward | Unsupported here |

No new search store, grants, mutation command, CLI or UI. This table is scoped to
MA-01; it is not a whole-release or fresh QMB-spawn reliability certification.
