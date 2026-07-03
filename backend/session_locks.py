"""Per-session write locks.

Identity/annotation endpoints are sync ``def`` routes, so Starlette runs
them on a threadpool (up to 40 threads) — two rapid click-to-label calls
would otherwise both read-modify-write the same CSV and silently lose one
update. One process-wide lock per session id serializes those windows.
"""

from __future__ import annotations

import threading

_REGISTRY: dict[str, threading.Lock] = {}
_REGISTRY_LOCK = threading.Lock()


def session_lock(session_id: str) -> threading.Lock:
    with _REGISTRY_LOCK:
        lock = _REGISTRY.get(session_id)
        if lock is None:
            lock = threading.Lock()
            _REGISTRY[session_id] = lock
        return lock
