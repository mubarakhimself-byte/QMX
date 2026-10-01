# Research result

**Status: Partial**

These products all keep a host workbench that consumes declared metadata: the installable unit is a pack or app, workflows and widgets are contributions the host already knows how to run and render, and a weaker developer or agent extends through an SDK plus install-time access rather than by rewriting the core. Salesforce, Bloomberg, GoHighLevel, n8n, OpenBB, VS Code, and Slack draw those five lines differently—metadata container, OAuth app, node pack, JSON backend, or extension manifest—but they agree that core, pack, automation, panel, and permission surface are separate contracts. For an internal kit whose runtime is QMA, toolbox is QMF, and specialist libraries are QML/QMB/QMN, the fitting hybrid is a VS Code–style contribution host, OpenBB’s widget-versus-app split, Slack-style install scopes, and n8n-style error-workflow observability, copied as SDK shapes only. Do not embed n8n or Salesforce.

### Platform core versus installable pack

Salesforce’s core is the subscriber org and its builders. The installable unit is a managed package—a metadata container of Apex, custom objects and fields, custom metadata types, flows, Lightning pages, and layouts—that may be a full app or a single component such as a flow; new apps are expected to use second-generation managed packages. [S1]

Bloomberg’s product core is the Terminal. Launchpad is the customizable workspace that hosts panels; BQuant Desktop is a Terminal-hosted Jupyter/Python authoring environment whose installable unit is a published interactive application pinned to Launchpad for permissioned colleagues, not a public widget catalog. [S12] Bloomberg Open API is a different surface: a Session opens `//<namespace>/<service-name>` services, issues requests or subscriptions, and gates data with an authorized Identity (EID entitlements, BPS vs NONBPS seats); Desktop API is not the same product as Server API and B-PIPE. [S11]

GoHighLevel’s live tenant is the sub-account. A snapshot is a reusable configuration template—built in a sub-account, then capturing selected assets such as workflows, funnels, calendars, forms, and custom fields for clone into other sub-accounts—not live contacts, conversations, Stripe connections, or integrations. [S4] Marketplace apps are a separate OAuth installable: the developer chooses Agency vs Sub-account as the token’s target user, who may install, and whether agencies can bulk-install; bulk-install of a sub-account app yields a Company token that must be exchanged per location, and agency-only modules (snapshots, custom-menu-link, CustomJS) are treated as incompatible with sub-account installers. Selling a snapshot on the Marketplace is a listing wrapper around a share link, not that OAuth token flow.

n8n keeps a host-owned built-in node library separate from installable node packs. Community nodes are npm packages (`n8n-nodes-` / `n8n-community-node-package`) that register nodes and credentials in `package.json`; unpublished private nodes can load from a custom directory without npm. [S13] Portable `.n8np` packages move workflow graphs and credential *references*, not node implementations or secrets, and import fails if a required node type is missing on the target instance. [S18]

OpenBB’s platform core is ODP—`openbb-core` plus installable provider and router pip packages—not the Workspace UI. Each provider is an independent extension feeding shared routers and can be inserted or removed without disturbing core; Workspace consumes HTTP backends, and `openbb-api` turns ODP/FastAPI into Workspace widget and app definitions. [S9] The published-app contract is two JSON files on that backend: `widgets.json` (one object per widget: name, description, endpoint, type, params, gridData) versus `apps.json` (name, tabs/layout, groups, prompts, optional selected agent, authentication, MCP servers), served as `GET /widgets.json` and `GET /apps.json`. [S8]

VS Code’s host stays the workbench. An installable extension is a package that statically declares contribution points in `package.json` and implements them with the `vscode` API after an activation event. [S19]

Slack’s installable unit is a Slack app whose YAML/JSON manifest separately lists display info, client features (app home, shortcuts, slash commands, unfurl domains, agent/assistant view), OAuth scopes, custom functions, and workflows; Slack applies that config, manifests hold no secrets, and `function_runtime` is remote or Slack-hosted. [S22]

### Workflow/automation versus widget/panel

A Salesforce Lightning web component becomes an App Builder or Experience Builder widget without a host rewrite only when `js-meta.xml` sets `isExposed` to true and declares at least one builder target (`lightning__AppPage`, record/home page, flow screen, utility bar); otherwise it stays private to its namespace. Managed packages also prefix component names with a namespace so they do not collide in the subscriber org. [S2]

GoHighLevel does not replace its workflow builder: custom Workflow Actions and Triggers are defined in a Marketplace app’s Workflow module and appear in a sub-account’s workflow UI only after that app is installed; they run as LC Premium pay-per-execution steps that POST field data plus `locationId` / `contactId` / `workflowId` to the developer’s API or custom code. [S6]

OpenBB Workspace’s public model is Widget (atomic data/UI unit with source, metadata, visual layer, and parameters) versus Dashboard (personal canvas) versus App (a pre-built template of linked widgets plus an agent and prompts). “Workflow” is the app’s purpose, not a separate published artifact type. [S7]

n8n’s editor panel is host-owned: the host renders node configuration from a JSON description using a fixed catalog of UI components; a sibling codex JSON only supplies nodes-panel categories and help links, not a custom editor. [S15] A node author implements `INodeType` / `ICredentialType` from `n8n-workflow`, lists compiled files under `package.json`’s `n8n.nodes` and `n8n.credentials`, and loads the pack into a running instance so the node appears in the editor without changing host code. [S14] The Workflow SDK is a different layer: it programmatically composes automations from node types the instance already has.

VS Code widgets are contributed views (`TreeView` or `WebviewView`) in built-in or custom view containers on the Activity Bar or Panel; richer HTML can also be a webview panel in an editor group. [S20] Chat is split from agent automation: `chatParticipants` are `@`-mentioned domain experts that own the user’s prompt; `languageModelTools` are separately declared functions the host agent may invoke, with user confirmation on extension tools. [S21]

Slack adds actions, link widgets, and a private app panel through host entry points: slash commands and shortcuts POST to the app; custom unfurls attach Block Kit to matching URLs (`links:read` / `links:write`); App Home’s Home tab is a Block Kit view published with `views.publish`. [S24]

### Permissions and the extender SDK

Salesforce packages do not automatically grant end-user access. Partners ship permission sets that cover custom package components (custom objects/fields/apps, Apex, custom permissions) but not standard-object or user permissions; subscribers cannot edit those packaged sets and must assign them after install. [S3]

GoHighLevel’s permission surface is the OAuth target-user choice (whose token the app ultimately needs) plus installer and bulk-install flags, with per-location token exchange after agency bulk-install. [S5]

OpenBB layers Workspace RBAC, per-backend header or query credentials, optional `apps.json` authentication and MCP OAuth-versus-token, and a widget/param `ai` flag that controls whether that unit is available to AI workflows—not entitlement IDs. [S10]

n8n credentials are a separate encrypted store from workflows and node code: nodes request a named credential type, and only node types with matching access rights can read it. Installing community packs is an instance-owner/admin action; all members may use packs already installed. [S16] Failure handling is workflow composition, not a host rewrite: each workflow may point at a separate error workflow that must start with the built-in Error Trigger (payload includes `execution.error`, last node executed, and workflow id/name), while node Settings add Retry On Fail and On Error independently of that link. [S17]

Slack permissions are install-time OAuth scopes on bot and/or user tokens. An app has no access by default; exchanging the OAuth code for tokens is what opens Web API, Events API, and interactivity (`commands` for shortcuts/slash commands; `links:read`/`write` for unfurls). [S23]

### Hybrid for QMA + QMF + QML/QMB/QMN

Keep QMA as the workbench/runtime that never gets rewritten for a new idea; keep QMF as the host-owned toolbox (the built-in node library, not an installable pack); keep QML, QMB, and QMN as independent provider/router extensions that feed shared operations the way ODP providers feed shared routers.

Ship one installable pack whose manifest (Slack/VS Code shape) declares widgets, workflows, contribution points, and a copilot integration profile as a request, not a grant. Split that pack the OpenBB way: widgets as atomic data/UI units with endpoints, params, and grid hints; apps as templates that link those widgets, bind an agent and prompts, and optionally mark which widgets/params the in-app copilot may see. Do not invent a third published “workflow file” type beside widget and app unless the workflow graph is itself a portable composition of ops the instance already has (n8n Workflow SDK / `.n8np` shape: graphs and credential references, never secrets or node implementations).

Give the two copilots different firepower through those declarations. The authoring copilot is the BQuant/extension-author seat: it may create and version packs. The app-use copilot is a bound chat participant that can inspect and invoke only exposed tools, with host confirmation on mutating tools—not a second copy of the authoring seat.

Tell that app-use copilot that something broke by composing an error workflow (Error Trigger plus per-step retry/on-error), not by patching QMA. Structured failure payload—error, last step, workflow identity—is the observability contract; widgets that fail should surface on the same channel so the in-app copilot can see a broken panel without being allowed to rewrite the app.

Gate access like Slack scopes plus Salesforce packaged permission sets: the pack lists custom ops, objects, and panels; install assigns them; the pack does not grant host-wide or specialist-library entitlements. Credentials stay an encrypted store separate from pack code. Namespace or prefix widget and op names so packs cannot collide. Expose a panel to builders only through explicit metadata (`isExposed` + target, contribution point, or `widgets.json` entry). That is the whole extender SDK: declare, install, assign, render, run, and report failure—without embedding n8n or Salesforce, and without turning QMF into the application.

## Sources
- [S1] "Use Managed Packages to Develop Your AgentExchange Solution | ISVforce Guide" — "https://developer.salesforce.com/docs/platform/isvforce/guide/managed-packaging-intro.html"
- [S2] "Add Components to Managed Packages | Lightning Web Components Developer Guide" — "https://developer.salesforce.com/docs/platform/lwc/guide/use-packaging-add.html" (independently checked against "XML Configuration File Elements | Lightning Web Components Developer Guide" — "https://developer.salesforce.com/docs/platform/lwc/guide/reference-configuration-tags.html")
- [S3] "Permission Sets and Profile Settings in Packages | First-Generation Managed Packaging Developer Guide" — "https://developer.salesforce.com/docs/platform/pkg1-dev/guide/distribution-perm-sets-profile-settings.html"
- [S4] "Creating New Snapshots in HighLevel | HighLevel Support Portal" — "https://help.gohighlevel.com/support/solutions/articles/48000982512-creating-new-snapshots-in-highlevel"
- [S5] "Marketplace App Distribution Model | HighLevel API" — "https://marketplace.gohighlevel.com/docs/oauth/AppDistribution"
- [S6] "HighLevel Marketplace Workflow Triggers & Actions | HighLevel API" — "https://marketplace.gohighlevel.com/docs/marketplace-modules/WorkflowActionsAndTriggers" (independently checked against "Creating a Marketplace Workflow Action | HighLevel API" — "https://marketplace.gohighlevel.com/docs/marketplace-modules/CustomActions")
- [S7] "OpenBB Workspace Docs" — "https://docs.openbb.co/workspace"
- [S8] "Widgets.json | OpenBB Workspace Docs" — "https://docs.openbb.co/workspace/developers/json-specs/widgets-json-reference"
- [S9] "Open Data Platform by OpenBB | ODP Docs" — "https://docs.openbb.co/odp"
- [S10] "apps.json Reference | OpenBB Workspace Docs" — "https://docs.openbb.co/workspace/developers/json-specs/apps-json-reference" (independently checked against "Widgets Overview | OpenBB Workspace Docs" — "https://docs.openbb.co/workspace/analysts/widgets/overview")
- [S11] "BLPAPI Documentation" — "https://bloomberg.github.io/blpapi-docs/"
- [S12] "BQuant | Bloomberg Professional Services" — "https://professional.bloomberg.com/products/bloomberg-terminal/research/bquant/"
- [S13] "Building community nodes" — "https://docs.n8n.io/integrations/community-nodes/building-community-nodes.md"
- [S14] "Tutorial: Build a programmatic-style node" — "https://docs.n8n.io/connect/create-nodes/build-your-node/tutorial-build-a-programmatic-style-node.md"
- [S15] "Node UI elements" — "https://docs.n8n.io/connect/create-nodes/build-your-node/reference/node-ui-elements.md"
- [S16] "Node types" — "https://docs.n8n.io/integrations/builtin/node-types.md"
- [S17] "Handle errors gracefully" — "https://docs.n8n.io/build/flow-logic/handle-errors-gracefully.md"
- [S18] "MCP server tools reference" — "https://docs.n8n.io/connect/connect-to-n8n-mcp-server/mcp-server-tools-reference.md" (independently checked against "n8n packages" — "https://docs.n8n.io/build/manage-workflows/n8n-packages")
- [S19] "Contribution Points | Visual Studio Code Extension API" — "https://code.visualstudio.com/api/references/contribution-points"
- [S20] "Contribution Points (views / viewsContainers) | Visual Studio Code Extension API" — "https://code.visualstudio.com/api/references/contribution-points#contributes.viewsContainers" (independently checked against "Tree View API | Visual Studio Code Extension API" — "https://code.visualstudio.com/api/extension-guides/tree-view")
- [S21] "Chat Participant API | Visual Studio Code Extension API" — "https://code.visualstudio.com/api/extension-guides/chat"
- [S22] "App manifest reference | Slack Developer Docs" — "https://docs.slack.dev/reference/app-manifest"
- [S23] "Scopes | Slack Developer Docs" — "https://docs.slack.dev/reference/scopes"
- [S24] "Implementing slash commands | Slack Developer Docs" — "https://docs.slack.dev/interactivity/implementing-slash-commands"

## Coverage and uncertainty
- "Question 1 uncertainty: Salesforce Help install articles still say AppExchange, while current 2GP/ISVforce developer pages say AgentExchange; both names appear on live public docs."
- "Question 1 uncertainty: Named-credential packaging was inspected (https://developer.salesforce.com/docs/platform/named-credentials/guide/nc-package-credentials.html) but not given a claim slot: credentials package as metadata without tokens; subscribers must add the package namespace to Allowed Namespaces unless the credential is in the same package; default developer-control (subscriber cannot edit URL/auth) is documented as rolling out from February 2026."
- "Question 1 uncertainty: LWC permission checks via @salesforce/customPermission (namespace__Permission for packaged custom permissions) were inspected at https://developer.salesforce.com/docs/platform/lwc/guide/create-get-permissions.html but not given a claim slot."
- "Question 1 uncertainty: GHL widget/panel/SDK surfaces were inspected but omitted under the six-claim cap: Custom Pages as HTTPS iframes in app details or left nav (https://marketplace.gohighlevel.com/docs/marketplace-modules/CustomPages); funnel-builder Web Widgets that emit HTML/CSS/JS via postmate (https://marketplace.gohighlevel.com/docs/marketplace-modules/Widgets); CustomJS AppUtils for storage, routing, and user/location/company context (https://marketplace.gohighlevel.com/docs/marketplace-modules/custom-js); custom menu links with openMode iframe|new_tab|current_tab requiring an Agency token and custom-menu-link.write (https://marketplace.gohighlevel.com/docs/ghl/custom-menus/create-custom-menu/)."
- "Question 1 uncertainty: The GHL App Creation Guide intro lists Client ID, Client Secret, scopes, and redirect URLs as intended outcomes, but the fetched page body was truncated, so those setup steps were not fully verified from that URL."
- "Question 1 uncertainty: Salesforce CustomObject post-install manageability (which attributes subscribers vs developers may edit) was not fully retrieved: the 2GP packageable-components page fetch failed, so those lock rules are omitted rather than inferred from search snippets."
- "Question 2 uncertainty: No current public BQuant/Launchpad page inspected here publishes a widget/panel JSON or SDK schema analogous to OpenBB widgets.json; BQuant “app” is described only as a published Launchpad application."
- "Question 2 uncertainty: Bloomberg App Portal and Terminal Connect marketing/SDK PDFs were not successfully retrieved as readable current pages (insights.bloomberg.com captcha; data.bloomberglp.com DNS failure; App Portal PDF download unreadable), so those product splits are omitted rather than inferred."
- "Question 2 uncertainty: BLPAPI Core Developer Guide PDF (linked from bloomberg.github.io/blpapi-docs) was not inspectable in this sitting; service catalog names such as //blp/refdata are therefore not claimed from that PDF."
- "Question 2 uncertainty: OpenBB Workspace RBAC is stated at product level only; no public role/permission matrix was inspected."
- "Question 2 uncertainty: OpenBB has no separate public workflows.json; automation is apps + agents + MCP tools (manage_apps instantiate, assign_tasks_to_agents), which is a different grain than Bloomberg BQuant scheduled jobs mentioned only as Enterprise marketing copy."
- "Question 3 uncertainty: In n8n docs, “core nodes” means built-in logic/scheduling/generic-API nodes, not the platform host; the built-in library also includes app nodes, trigger nodes, and cluster nodes (https://docs.n8n.io/integrations/builtin/node-types.md)."
- "Question 3 uncertainty: Unverified community npm packs are documented as unsandboxed (“full access to the machine that n8n runs on”); verified packs add extra constraints (no runtime dependencies, no env/filesystem access) but that is a vetting policy, not a host plugin sandbox API (https://docs.n8n.io/integrations/community-nodes/risks.md, https://docs.n8n.io/connect/create-nodes/build-your-node/reference/verification-guidelines.md)."
- "Question 3 uncertainty: Public Workflow SDK surface on docs.n8n.io is mainly the MCP tool contract; the @n8n/workflow-sdk README is a short fluent-builder example and was not a full API spec in the inspected page (https://github.com/n8n-io/n8n/blob/master/packages/%40n8n/workflow-sdk/README.md)."
- "Question 3 uncertainty: Docs inspected do not describe a supported way for a node pack to replace the host editor chrome, permissions model, or Error Trigger implementation; NODES_ERROR_TRIGGER_TYPE exists as a self-host env override of which node type is the Error Trigger (https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/use-environment-variables/nodes.md)."
- "Question 4 uncertainty: These VS Code pages do not define OAuth-style permission scopes for extensions; gating is contribution points, when clauses, Chat-view tool toggles, and a generic confirmation for extension tools (https://code.visualstudio.com/api/extension-guides/ai/tools)."
- "Question 4 uncertainty: Contribution Points lists chatAgents (.agent.md personas), not chatParticipants; the Chat Participant API still documents contributes.chatParticipants as of the 9/16/2026 page date—two parallel chat-extension shapes."
- "Question 4 uncertainty: Slack ‘shortcuts trigger workflows’ is product language for interactivity; coded workflows/functions in the manifest are a distinct automation model (function_runtime slack vs remote)."
- "Question 4 uncertainty: App Home is explicitly unavailable for Deno Slack SDK apps and workflows (https://docs.slack.dev/surfaces/app-home); panel-like UI for those apps is not specified on that page."
- "Question 4 uncertainty: Local QMX workspace was not used; claims are only from the cited public VS Code and Slack docs."
- "Question 5 uncertainty: Public docs treat 'Automation' as a catalog browse category (plugin-catalog YAML category: automation), not as a distinct runtime noun comparable to general plugin, desktop pane, or capability grant."
- "Question 5 uncertainty: Docs do not say doctor or validate run automatically as a pre-enable gate; enable is a separate plugins.enabled / Capabilities toggle after install. Doctor is documented as an authoring check; validate as catalog CI plus install-time scanning."
- "Question 5 uncertainty: A dedicated CLI reference page listing hermes plugins validate flags was not inspected; validate behavior is taken from the plugin authoring guide, Plugin Catalog page, and plugin-catalog/README.md."
- "Question 5 uncertainty: Application declarations (hermes_platform/declaration.py) gate MCP tools and skills on host-app presence/version; they are a separate availability parser, not the plugin capability-consent model."
- "Question 5 uncertainty: Agent Plugins v1 portable packages (plugin.json + skills/ + mcp.json) are a compatibility adapter that 'does not define trust, permissions, provenance, or a sandbox' and do not replace native plugin.yaml plus register(ctx) plugins."
- "Question 6 uncertainty: The 2026-09-23 ‘Pack-and-grant kit’ (reject Screen kit / Automation kit as the center) is coaching evidence, not an operator-accepted spine; architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md is still a template."
- "Question 6 uncertainty: Whether the unnamed home/general copilot is the same as ProductSessionProfile authoring or a third seat remains an open operator question (app_instance_id is required in current code)."
- "Question 6 uncertainty: Ratified ADs require health in discovery/grants but do not define a mini-app health() field roster or a copilot query that names widget-break vs workflow-break vs grant-break."
- "Question 6 uncertainty: Bloomberg, GoHighLevel, and ClickUp donor mappings were named in the 09-23 memlog but were not independently inspected from first-party docs in this pass."
- "Question 6 uncertainty: Salesforce Help HTML for installing packages failed to load; the permission-set assignment fact is taken from Salesforce Developers packaging guide content returned by search."
- "Question 6 uncertainty: ADR-0024 still records wiring honesty: product_session/GrantRecord/ContributionHit were specified, not claimed as e2e product surface at the parent freeze SHA 270e992."
- "12 malformed or over-cap candidate claim(s) were excluded before verification."
