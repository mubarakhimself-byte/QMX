<!--
source_url: https://hindsight.vectorize.io/developer/configuration
fetched_from: https://raw.githubusercontent.com/vectorize-io/hindsight/main/hindsight-docs/docs/developer/configuration.mdx
title: Hindsight docs: Configuration
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw text as served)
-->

(trimmed to the Database section, source lines 25-60 of the raw MDX)


## API Service

The API service handles all memory operations (retain, recall, reflect).

### Database

| Variable | Description | Default |
|----------|-------------|---------|
| `HINDSIGHT_API_DATABASE_URL` | PostgreSQL connection string | `pg0` (embedded) |
| `HINDSIGHT_API_READ_DATABASE_URL` | Optional read-replica PostgreSQL URL. When set, recall queries (semantic, BM25, graph, temporal) are routed through a separate connection pool against this URL, offloading the primary. Typically points to a read-only endpoint (e.g., CNPG's `<cluster>-ro` service or Aurora reader endpoint). | Unset (uses primary) |
| `HINDSIGHT_API_MIGRATION_DATABASE_URL` | Direct PostgreSQL URL for running migrations, bypassing connection poolers (e.g. PgBouncer). When set, advisory locks and Alembic migrations use this URL instead of `DATABASE_URL`. | Falls back to `DATABASE_URL` |
| `HINDSIGHT_API_DATABASE_SCHEMA` | PostgreSQL schema name for tables | `public` |
| `HINDSIGHT_API_RUN_MIGRATIONS_ON_STARTUP` | Run database migrations on API startup | `true` |
| `HINDSIGHT_API_MIGRATION_ISOLATION` | Run migrations in a subprocess instead of in the calling process: `true` (keeps Alembic's import graph and its psycopg2 sync engine out of a long-lived server process) or `false` | `false` |
| `HINDSIGHT_API_MIGRATION_CONCURRENCY` | Number of tenant schemas to migrate concurrently (PostgreSQL only). Each schema runs in its own process; within a schema migrations are always sequential. Each worker has a fixed startup cost (~1–2s to boot a fresh interpreter), so this only pays off with **many** schemas (roughly tens or more) or slow/high-latency migrations — for a handful of schemas it is slower than sequential. Each worker uses ~3 database connections, so keep `concurrency × 3` within your database's spare `max_connections` (and any PgBouncer pool limit). `1` = fully sequential. Measured at 20k schemas: the per-restart no-op resweep dropped from ~60min to ~11min (≈5×) at `concurrency=12`. | `1` |
| `HINDSIGHT_API_EXTERNALLY_OWNED_ROUTINES` | Comma-separated list of maintenance discovery routines this deployment installs itself (see [Owning a maintenance routine](#owning-a-maintenance-routine)). Migrations skip anything named here. | Empty (every routine installed) |
| `HINDSIGHT_API_DATABASE_BACKEND` | Database engine backend: `postgresql` or `oracle` (Oracle 23ai) | `postgresql` |

If not provided, the server uses embedded `pg0` — convenient for development but not recommended for production.

To tune the embedded database, add PostgreSQL settings as a query string: `pg0://hindsight?max_connections=300&shared_buffers=256MB`. They apply when the embedded database starts, so restart it after changing them.

To run against Oracle Database 23ai instead, set `HINDSIGHT_API_DATABASE_BACKEND=oracle` and use an `oracle+oracledb://…` URL. See the [Oracle Database guide](./oracle) for full setup instructions.

The `DATABASE_SCHEMA` setting allows you to use a custom PostgreSQL schema instead of the default `public` schema. This is useful for:
- Multi-database setups where you want Hindsight tables in a dedicated schema
- Hosting platforms (e.g., Supabase) where `public` schema is reserved or shared
- Organizational preferences for schema naming conventions

```bash
# Example: Using a custom schema
export HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@host:5432/dbname
export HINDSIGHT_API_DATABASE_SCHEMA=hindsight
```

