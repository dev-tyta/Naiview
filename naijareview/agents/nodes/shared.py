"""Shared node implementations used by both Agent A and Agent B.

See §6.3 and §7 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import time
from typing import Any


def trace_node(node_name: str, state: dict, summary: str) -> dict:
    """Helper to append a trace entry to state after a node runs."""
    trace_entry = {
        "node": node_name,
        "started_at": time.time(),
        "duration_ms": 0,  # Caller should update
        "status": "ok",
        "summary": summary,
    }
    existing_trace = state.get("trace", [])
    return {**state, "trace": [*existing_trace, trace_entry]}


def append_error(state: dict, error_msg: str) -> dict:
    """Helper to append an error to state."""
    existing_errors = state.get("errors", [])
    return {**state, "errors": [*existing_errors, error_msg]}
