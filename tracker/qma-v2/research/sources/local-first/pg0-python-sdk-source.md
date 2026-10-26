<!--
source_url: https://github.com/vectorize-io/pg0/blob/main/sdk/python/pg0/__init__.py
fetched_from: https://raw.githubusercontent.com/vectorize-io/pg0/main/sdk/python/pg0/__init__.py
title: pg0 Python SDK source: Pg0 constructor (data_dir parameter)
fetched: 2026-10-26
fetched_by: research agent for study 62b (source excerpt, lines 180-250)
-->

```python
    """
    Embedded PostgreSQL instance.

    Args:
        name: Instance name (allows multiple instances)
        port: Port to listen on (None = auto-select available port)
        username: Database username
        password: Database password
        database: Database name
        data_dir: Custom data directory
        config: Dict of PostgreSQL configuration options

    Example:
        # Simple usage (auto-selects available port)
        pg = Pg0()
        pg.start()
        print(pg.uri)
        pg.stop()

        # Context manager with specific port
        with Pg0(port=5433, database="myapp") as pg:
            print(pg.uri)

        # Custom config
        pg = Pg0(config={"shared_buffers": "512MB"})
    """

    def __init__(
        self,
        name: str = "default",
        port: Optional[int] = None,
        username: str = "postgres",
        password: str = "postgres",
        database: str = "postgres",
        data_dir: Optional[str] = None,
        config: Optional[dict[str, str]] = None,
    ):
        self.name = name
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.data_dir = data_dir
        self.config = config or {}

    def start(self) -> InstanceInfo:
        """
        Start the PostgreSQL instance.

        Returns:
            InstanceInfo with connection details

        Raises:
            Pg0AlreadyRunningError: If instance is already running
            Pg0Error: If start fails
        """
        args = [
            "start",
            "--name", self.name,
            "--username", self.username,
            "--password", self.password,
            "--database", self.database,
        ]

        if self.port is not None:
            args.extend(["--port", str(self.port)])

        if self.data_dir:
            args.extend(["--data-dir", self.data_dir])

        for key, value in self.config.items():
```
