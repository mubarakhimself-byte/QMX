<!-- Source: https://raw.githubusercontent.com/grafana/mcp-grafana/main/README.md
     Fetched: 2026-10-28. Excerpt: first 200 lines (feature list), verbatim. -->

# Grafana MCP server

[![Unit Tests](https://github.com/grafana/mcp-grafana/actions/workflows/unit.yml/badge.svg)](https://github.com/grafana/mcp-grafana/actions/workflows/unit.yml)
[![Integration Tests](https://github.com/grafana/mcp-grafana/actions/workflows/integration.yml/badge.svg)](https://github.com/grafana/mcp-grafana/actions/workflows/integration.yml)
[![E2E Tests](https://github.com/grafana/mcp-grafana/actions/workflows/e2e.yml/badge.svg)](https://github.com/grafana/mcp-grafana/actions/workflows/e2e.yml)
[![Go Reference](https://pkg.go.dev/badge/github.com/grafana/mcp-grafana.svg)](https://pkg.go.dev/github.com/grafana/mcp-grafana)
[![MCP Catalog](https://archestra.ai/mcp-catalog/api/badge/quality/grafana/mcp-grafana)](https://archestra.ai/mcp-catalog/grafana__mcp-grafana)

A [Model Context Protocol][mcp] (MCP) server for Grafana.

This provides access to your Grafana instance and the surrounding ecosystem.

## Quick Start

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). Add the following to your MCP client configuration (e.g. Claude Desktop, Cursor):

```json
{
  "mcpServers": {
    "grafana": {
      "command": "uvx",
      "args": ["mcp-grafana"],
      "env": {
        "GRAFANA_URL": "http://localhost:3000",
        "GRAFANA_SERVICE_ACCOUNT_TOKEN": "<your service account token>"
      }
    }
  }
}
```

For Grafana Cloud, replace `GRAFANA_URL` with your instance URL (e.g. `https://myinstance.grafana.net`). See [Usage](#usage) for more installation options including Docker, binary, and Helm.

## Requirements

- **Grafana version 9.0 or later** is required for full functionality. Some features, particularly datasource-related operations, may not work correctly with earlier versions due to missing API endpoints.

## Features

_The following features are currently available in MCP server. This list is for informational purposes only and does not represent a roadmap or commitment to future features._

### Dashboards

- **Search for dashboards:** Find dashboards by title, folder UID, tag, or starred status
- **Get dashboard by UID:** Retrieve full dashboard details using its unique identifier. Pass optional `version` to load a saved snapshot instead of the current dashboard. _Warning: Large dashboards can consume significant context window space._
- **List dashboard versions:** List saved versions of a dashboard as compact metadata (version number, author, timestamp, save message)
- **Get dashboard summary:** Get a compact overview of a dashboard including title, panel count, panel types, variables, and metadata without the full JSON to minimize context window usage
- **Get dashboard property:** Extract specific parts of a dashboard using JSONPath expressions (e.g., `$.title`, `$.panels[*].title`) to fetch only needed data and reduce context window consumption
- **Update or create a dashboard:** Modify existing dashboards or create new ones. _Warning: Requires full dashboard JSON which can consume large amounts of context window space._
- **Patch dashboard:** Apply specific changes to a dashboard without requiring the full JSON, significantly reducing context window usage for targeted modifications
- **Get panel queries and datasource info:** Get the title, query string, and datasource information (including UID and type, if available) from every panel in a dashboard

### Run Panel Query

> **Note:** Run panel query tools are **disabled by default**. To enable them, add `runpanelquery` to your `--enabled-tools` flag.

- **Run panel query:** Execute a dashboard panel's query with custom time ranges and variable overrides. Infinity panels run when the query uses the `backend` or `jq-backend` parser (Google Sheets queries always do); the default `simple` parser and the UQL and GROQ parsers work only in the browser. Neo4j panels on the `kniepdennis-neo4j-datasource` plugin run their Cypher query through the plugin, which opens read-only sessions.

#### Context Window Management

The dashboard tools now include several strategies to manage context window usage effectively ([issue #101](https://github.com/grafana/mcp-grafana/issues/101)):

- **Use `get_dashboard_summary`** for dashboard overview and planning modifications
- **Use `get_dashboard_property`** with JSONPath when you only need specific dashboard parts
- **Avoid `get_dashboard_by_uid`** unless you specifically need the complete dashboard JSON

### Datasources

- **List and fetch datasource information:** View all configured datasources and retrieve detailed information about each.
  - _Supported datasource types: Prometheus, Loki, ClickHouse, CloudWatch, Elasticsearch, OpenSearch, Snowflake, Athena._

### Query Examples

> **Note:** Query examples tools are **disabled by default**. To enable them, add `examples` to your `--enabled-tools` flag.

- **Get query examples:** Retrieve example queries for different datasource types to learn query syntax.

### Prometheus Querying

- **Query Prometheus:** Execute PromQL queries (supports both instant and range metric queries) against Prometheus datasources.
- **Query Prometheus metadata:** Retrieve metric metadata, metric names, label names, and label values from Prometheus datasources.
- **Query histogram percentiles:** Calculate histogram percentile values (p50, p90, p95, p99) using histogram_quantile.

### Loki Querying

- **Query Loki logs and metrics:** Run both log queries and metric queries using LogQL against Loki datasources.
- **Query Loki metadata:** Retrieve label names, label values, and stream statistics from Loki datasources.
- **Query Loki patterns:** Retrieve log patterns detected by Loki to identify common log structures and anomalies.

### InfluxDB Querying

> **Note:** InfluxDB tools are **disabled by default**. To enable them, add `influxdb` to your `--enabled-tools` flag.

- **Query InfluxDB:** Execute queries against InfluxDB datasources using either InfluxQL (v1.x) or Flux (v2.x). The dialect is inferred from the datasource configuration, or can be set explicitly via the `dialect` parameter.

### SQL Datasource Querying

> **Note:** SQL tools are **disabled by default**. To enable them, add `sql` to your `--enabled-tools` flag. Back-compat aliases `clickhouse`, `snowflake`, and `athena` also work.

Unified SQL tools support **ClickHouse, Snowflake, Athena, MySQL, PostgreSQL, MSSQL, and BigQuery** through a single set of tools. Queries go through Grafana's datasource plugins, so authentication is handled by datasource configuration — credentials are never seen by the MCP server.

- **List databases/schemas/catalogs:** Discover organizational units for a SQL datasource. For Athena, omit catalog to list catalogs, or pass a catalog to list databases.
- **List tables:** List tables in a database or schema with metadata (row counts, sizes where available).
- **Describe table schema:** Get column names, types, nullability, defaults, and comments.
- **Query SQL:** Execute SQL queries with datasource-specific macro substitution (`$__timeFilter(col)`, `$__from/$__to`, `$__interval`, `${varname}`), automatic limit enforcement, and template variable support.

For **BigQuery**, configure the `grafana-bigquery-datasource` plugin in Grafana. Discovery uses `database` for the project and `schema` for the dataset. If `database` is omitted, the project defaults to datasource `defaultProject`, then the plugin's `/defaultProjects` endpoint (including GCE project discovery). Metadata is fetched through APIs only, without query jobs or table scans. Column descriptions and nested types are included; the plugin omits table descriptions/types, column nullability, and defaults.

BigQuery queries require qualified table references such as `` `my-project.my_dataset.fct_events` `` and use the datasource's billing project. Optional `location` defaults to datasource `processingLocation`. Use `${name:sqlstring}` for escaped string variables. Row limits do not limit bytes scanned or query costs.

### CloudWatch Querying

> **Note:** CloudWatch tools are **disabled by default**. To enable them, add `cloudwatch` to your `--enabled-tools` flag.

- **List CloudWatch namespaces:** Discover available AWS CloudWatch namespaces.
- **List CloudWatch metrics:** List metrics available in a specific namespace.
- **List CloudWatch dimensions:** Get dimensions for filtering metric queries.
- **Query CloudWatch:** Execute CloudWatch metric queries with time range support.
- **List CloudWatch log groups:** Discover log groups, optionally filtered by name prefix.
- **List CloudWatch log group fields:** Discover the fields available in a log group.
- **Query CloudWatch Logs:** Run CloudWatch Logs Insights queries across one or more log groups.

### Google Cloud Logging Querying

> **Note:** Google Cloud Logging tools are **disabled by default**. To enable them, add `cloudlogging` to your `--enabled-tools` flag. Requires the [Google Cloud Logging datasource plugin](https://grafana.com/grafana/plugins/googlecloud-logging-datasource/) (`googlecloud-logging-datasource`) version 1.8.0 or later, which needs Grafana 11.2+. Older plugin versions return a different response layout and `query_cloud_logging` reports an error asking for an upgrade.

- **List Cloud Logging projects:** Discover the GCP project IDs the datasource can read logs from.
- **List Cloud Logging buckets and views:** Discover log buckets and log views to scope a query.
- **Query Cloud Logging:** Run Cloud Logging query language filters (e.g. `resource.type="k8s_container" AND severity>=ERROR`) with time range and limit; returns entries newest-first with severity, body, labels, and trace ID. GCP authentication is handled by the datasource configuration.

### Graphite Querying

> **Note:** Graphite tools are **disabled by default**. To enable them, add `graphite` to your `--enabled-tools` flag.

- **Query Graphite:** Execute Graphite render API queries against a Graphite datasource.
- **List Graphite metrics:** Browse and discover Graphite metric paths.
- **List Graphite tags:** List available Graphite tags and tag values.
- **Query Graphite density:** Query Graphite metric density for a given pattern.

### Elasticsearch/OpenSearch Querying

> **Note:** Elasticsearch/OpenSearch tools are **disabled by default**. To enable them, add `elasticsearch` to your `--enabled-tools` flag.

- **Query Elasticsearch/OpenSearch:** Execute search queries against Elasticsearch or OpenSearch datasources using either Lucene query syntax or Elasticsearch Query DSL. Supports filtering by time range and retrieving logs, metrics, or any indexed data. Returns documents with their index, ID, source fields, and optional relevance score.

### Quickwit Querying

> **Note:** Quickwit tools are **disabled by default**. To enable them, add `quickwit` to your `--enabled-tools` flag.

- **Query Quickwit:** Execute search queries against Quickwit datasources using Lucene query syntax or partial Elasticsearch-compatible Query DSL. Supports filtering by time range and retrieving logs or other indexed documents. Returns documents with their index, ID, source fields, and optional relevance score.

### Agent Observability

> **Note:** Agent Observability tools are **disabled by default** and work only in Grafana Cloud. To enable them, add `agento11y` to your `--enabled-tools` flag.

- **List and search conversations:** List recent LLM conversations or search them with a filter expression (model, provider, agent, status, error type, eval results, and more) over a time range. Search results include error counts, rating summaries, evaluation summaries, and trace IDs.
- **Get conversation detail:** Fetch a single conversation with all its generations, including prompts and outputs.
- **Get generation detail and scores:** Fetch a single generation by ID, and its evaluation scores (evaluator, score key, value, passed, explanation).
- **Read the agent catalog:** List the agents that send telemetry, fetch one agent version in full (complete system prompt, every tool with its JSON schema, and the models it ran on), walk an agent's version history, and compare evaluation score aggregates per version. Effective versions are `sha256:` hashes that a tool change never affects; for an agent that reports no version of its own they hash the system prompt, so a prompt edit mints a new version. Catalog and version rows carry a `token_estimate`, which is worth checking before fetching a full prompt.
- **Inspect evaluators and templates:** Read the evaluators a score came from, the templates they were derived from, and the judge providers and models available to LLM-judge evaluators. With write tools enabled, also create, fork, test, and delete evaluators.
- **Inspect eval rules and guards:** Read the asynchronous eval rules that bind evaluators to production traffic, and the guards (hook rules) that run inline and can warn or deny. With write tools enabled, also create, update, preview, and delete them. Writes and the non-persisting `preview_rule` and `test_evaluator` operations need the `grafana-agento11y-app.eval:write` permission, granted by the Agento11y Admin role.
- **Curate saved conversations and collections:** Read the saved conversations (bookmarks that give a conversation a stable ID, name, and tags) and the collections that group them, including each collection's member count and the collections embedded in every saved-conversation row. With write tools enabled, also bookmark a conversation, create and edit collections, and add or remove members. These writes need the same `grafana-agento11y-app.eval:write` permission.
- **Read and edit test suites:** List the versioned test suites that offline experiments run against, read one with its full version history, and page through the test cases of a version. With write tools enabled, also create a suite, rename or retag it, open a draft version, publish it, and write or delete its test cases. A published version is frozen, so an edit means opening a new draft. These writes need `grafana-agento11y-app.eval:write`.
- **Read offline experiments:** List the evaluation runs over a test suite and read one with its headline pass rate, cost, and token totals. Drill down through a per-test-case report to trials, their scores with each judge's explanation, and their artifact metadata. With write tools enabled, also rename or retag an experiment and cancel a running one, which need `grafana-agento11y-app.eval:write`. Experiments are created by SDK runners, not by this tool.

### Grafana Assistant

> **Note:** Assistant tools are **disabled by default** and require the [Grafana Assistant](https://grafana.com/docs/grafana-cloud/machine-learning/assistant/) plugin (`grafana-assistant-app`) to be installed on the target Grafana instance. They are also **write tools** (the assistant may mutate stack state), so they are skipped when `--disable-write` is set. To enable them, add `assistant` to your `--enabled-tools` flag.

- **Ask the assistant:** Send a natural-language prompt to Grafana Assistant and wait for the full text reply. The assistant may use tools, metrics, logs, and other stack context—broader than firing one isolated data-source query. Pass the returned `contextId` back in a follow-up call to continue the same conversation. Complex tasks can take several minutes; the call blocks until the reply is done or the request times out (5 minutes).

### Incidents

- **Search, create, and update incidents:** Manage incidents in Grafana Incident, including searching, creating, adding activities, and reading or setting custom fields.

### Alerting

- **List and fetch alert rule information:** View alert rules and their statuses (firing/normal/error/etc.) in Grafana. Supports both Grafana-managed rules and datasource-managed rules from Prometheus or Loki datasources.
- **Create and update alert rules:** Create new alert rules or modify existing ones.
- **Delete alert rules:** Remove alert rules by UID.
- **Manage alerting routing:** View notification policies, contact points, and time intervals. Supports both Grafana-managed contact points and receivers from external Alertmanager datasources (Prometheus Alertmanager, Mimir, Cortex).

### Grafana OnCall

- **List and manage schedules:** View and manage on-call schedules in Grafana OnCall.
- **Get shift details:** Retrieve detailed information about specific on-call shifts.
- **Get current on-call users:** See which users are currently on call for a schedule.
- **List teams and users:** View all OnCall teams and users.
- **List alert groups:** View and filter alert groups from Grafana OnCall by various criteria including state, integration, labels, and time range.
- **Get alert group details:** Retrieve detailed information about a specific alert group by its ID.

### Admin

> **Note:** Admin tools are **disabled by default**. To enable them, include `admin` in your `--enabled-tools` flag.
- **List teams:** View all configured teams in Grafana.
- **List Users:** View all users in an organization in Grafana.
- **List all roles:** List all Grafana roles, with an optional filter for delegatable roles.

<!-- Further excerpt: lines 525-535 of the same file, verbatim. -->
- `--disable-incident`: Disable incident tools
- `--disable-prometheus`: Disable prometheus tools
- `--disable-write`: Disable write tools (create/update operations)
- `--disable-query`: Disable query tools (tools that execute a query against a datasource); metadata and discovery tools stay available
- `--enable-query`: Keep the raw-SQL query tools (`query_sql`, `query_influxdb`) registered even under `--disable-write`. Equivalent to `--enable-write-tools=query_sql,query_influxdb`; kept as a shorthand for that common case.
- `--enable-write-tools`: Comma separated list of individual tool names to keep registered even under `--disable-write`, for tools whose write behavior is scoped enough to opt back in independently. Has no effect on a tool whose whole category is disabled. For example, `--enable-write-tools=generate_deeplink` keeps URL shortening (`shorten=true`) working under `--disable-write`, and `--enable-write-tools=alerting_rules_write` allows alert rule changes without enabling other write tools.
- `--disable-loki`: Disable loki tools
- `--disable-elasticsearch`: Disable elasticsearch and opensearch tools
- `--disable-quickwit`: Disable quickwit tools
- `--disable-influxdb`: Disable InfluxDB tools
- `--disable-alerting`: Disable alerting tools
