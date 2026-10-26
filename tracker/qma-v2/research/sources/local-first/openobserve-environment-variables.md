<!--
source_url: https://openobserve.ai/docs/administration/configuration/environment-variables/
fetched_from: https://raw.githubusercontent.com/openobserve/openobserve-docs/main/docs/administration/configuration/environment-variables.md
title: OpenObserve docs: Environment variables
fetched: 2026-10-26
fetched_by: research agent for study 62b (raw markdown as served; trimmed to the variables study 62b relies on)
-->

# OpenObserve environment variables (excerpt)

| Variable | Default | Description |
| --- | --- | --- |
| ZO_ROOT_USER_EMAIL | - | Email ID of the root user. |
| ZO_ROOT_USER_PASSWORD | - | Password for the root user. |
| ZO_LOCAL_MODE | true | If local mode is set to true, OpenObserve becomes single node deployment.If it is set to false, it indicates cluster mode deployment which supports multiple nodes with different roles. For local mode one needs to configure SQLite DB, for cluster mode one needs to configure PostgreSQL (recommended) or MySQL. |
| ZO_LOCAL_MODE_STORAGE | disk | Applicable only for local mode. By default, local disk is used as storage. OpenObserve supports both disk and S3 in local mode. |
| ZO_HTTP_PORT | 5080 | Port number on which the OpenObserve server listens for HTTP requests. |
| ZO_HTTP_ADDR | | IP address on which the OpenObserve server listens for HTTP requests. |
| ZO_GRPC_PORT | 5081 | Port number on which the OpenObserve server listens for gRPC requests. |
| ZO_DATA_DIR | ./data/openobserve/ | Defaults to "data" folder in current working directory if not provided. |
| ZO_DATA_DB_DIR | ./data/openobserve/db/ | Directory for storing the metadata database locally. |
| ZO_DATA_WAL_DIR | ./data/openobserve/wal/ | Directory for storing Write-Ahead Log (WAL) data. |
| ZO_DATA_STREAM_DIR | ./data/openobserve/stream/ | Directory for storing stream data locally. Applicable only in local mode. |
| ZO_MAX_FILE_SIZE_IN_MEMORY | 256 | Maximum memtable size in MB before it becomes immutable and is written to disk. Default is 256 MB. |
| ZO_MEM_TABLE_MAX_SIZE | 0 | Total size limit of all memtables. Multiple memtables exist for different organizations and stream types. Each memtable cannot exceed ZO_MAX_FILE_SIZE_IN_MEMORY, and the combined size cannot exceed this limit. If exceeded, the system returns a MemoryTableOverflowError to prevent out-of-memory conditions. Default is 50 percent of total memory. |
| ZO_COMPACT_DATA_RETENTION_DAYS | 3650 | Data retention days, default is 10 years. Minimal 3. eg: 30, it means will auto delete the data older than 30 days. You also can set data retention for stream in the UI. |
| ZO_WEB_URL | - | UI access URL. For example, http://localhost:5080 is used as redirect URL and alert URL. |
| ZO_TELEMETRY | true | Sends anonymous telemetry data to help improve OpenObserve. Set to false to disable telemetry. |
| ZO_DATA_CACHE_DIR | ./data/openobserve/cache/ | local query cache storage directory, applicable only for cluster mode. |
| ZO_MEMORY_CACHE_ENABLED | true | enable in-memory caching for files, default is true, the latest files are cached for accelerated queries. |
| ZO_DISK_CACHE_MAX_SIZE | - | Default 50% of the total free disk for in-disk cache, one can set it to desired amount unit: MB |
| ZO_META_STORE                       | -             | Default is sqlite for local mode, postgres or mysql for cluster mode. and supported values are: sqlite, postgres, mysql. Note that sqlite is supported only for local mode. |
