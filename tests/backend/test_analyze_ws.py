"""Analyze WS: subscribers are reaped on disconnect; terminal events survive overflow."""

import asyncio


def test_subscriber_removed_after_disconnect(client):
    app = client.app
    assert len(app.state.analyze_subscribers) == 0
    with client.websocket_connect("/api/analyze/ws") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "snapshot"
        assert len(app.state.analyze_subscribers) == 1
    # Context exit closes the socket; the handler must observe the close
    # (via its receive task) and remove the subscriber promptly.
    assert len(app.state.analyze_subscribers) == 0


def test_broadcast_overflow_keeps_newest(client):
    from backend.routers import analyze as analyze_router

    app = client.app
    q: asyncio.Queue = asyncio.Queue(maxsize=2)
    app.state.analyze_subscribers.append(q)
    try:
        analyze_router._broadcast(app, {"type": "progress", "n": 1})
        analyze_router._broadcast(app, {"type": "progress", "n": 2})
        analyze_router._broadcast(app, {"type": "done"})  # queue full here
        drained = [q.get_nowait(), q.get_nowait()]
        assert {"type": "done"} in drained  # newest survived (oldest evicted)
    finally:
        app.state.analyze_subscribers.remove(q)
