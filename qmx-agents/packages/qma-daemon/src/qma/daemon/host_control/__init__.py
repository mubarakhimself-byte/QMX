"""Local host-control channel under product ``QMA_DAEMON_ROOT`` (Story 67.1).

Token-gated loopback, outside port 8765. Not CT-40 and not a new sqlite class.
"""

from __future__ import annotations

from qma.daemon.host_control.channel import (
    CT40_BIND_PORT,
    HOST_CONTROL_BIND_NAME,
    HOST_CONTROL_EXISTED_AT_INSPECT_SHA,
    HOST_CONTROL_FILE,
    HOST_CONTROL_INSPECT_SHA,
    HOST_CONTROL_IS_CT40,
    HOST_CONTROL_VERBS,
    BoundHostControl,
    HostControlChannel,
    claim_host_control_existed_at_inspect_sha,
    claim_types_absent_at_inspect_sha,
    decode_host_control_frame,
    encode_host_control_frame,
    ensure_host_control_token,
    host_control_call,
    read_host_control_bind,
    read_host_control_token,
    redact_host_surface,
    write_host_control_bind,
)
from qma.daemon.host_control.root import (
    INSPECT_CWD_RELATIVE_ROOT,
    product_daemon_root,
    resolve_daemon_root,
)

__all__ = [
    "CT40_BIND_PORT",
    "HOST_CONTROL_BIND_NAME",
    "HOST_CONTROL_EXISTED_AT_INSPECT_SHA",
    "HOST_CONTROL_FILE",
    "HOST_CONTROL_INSPECT_SHA",
    "HOST_CONTROL_IS_CT40",
    "HOST_CONTROL_VERBS",
    "INSPECT_CWD_RELATIVE_ROOT",
    "BoundHostControl",
    "HostControlChannel",
    "claim_host_control_existed_at_inspect_sha",
    "claim_types_absent_at_inspect_sha",
    "decode_host_control_frame",
    "encode_host_control_frame",
    "ensure_host_control_token",
    "host_control_call",
    "product_daemon_root",
    "read_host_control_bind",
    "read_host_control_token",
    "redact_host_surface",
    "resolve_daemon_root",
    "write_host_control_bind",
]
