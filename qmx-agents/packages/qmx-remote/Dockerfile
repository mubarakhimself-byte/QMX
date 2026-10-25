# Same pinned Python/uv base as the P17 app image; build from the repository root.
FROM ghcr.io/astral-sh/uv:0.12.23-python3.14-trixie-slim@sha256:8e88a074b0969bdc461f681727238e109438d70771828909f9ef19cfcc96c43a
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client rclone \
    && rm -rf /var/lib/apt/lists/*
COPY . /image
ENV UV_PROJECT_ENVIRONMENT=/opt/remote-env UV_PYTHON_DOWNLOADS=never
RUN uv sync --frozen --no-dev --no-editable --project /image/qmx-agents/packages/qmx-remote
ENV PATH=/opt/remote-env/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python", "-m", "qmx_remote.sidecar"]
