"""Concurrent assignment writes must not lose updates."""

from concurrent.futures import ThreadPoolExecutor


def test_concurrent_assigns_all_land(client, tmp_path, monkeypatch):
    # Point sessions at tmp and fabricate a minimal session directory.
    monkeypatch.setattr(
        "backend.routers.identities.default_sessions_root", lambda: tmp_path,
    )
    monkeypatch.setattr(
        "backend.routers.sessions.default_sessions_root", lambda: tmp_path,
    )
    sid = "2026-01-01_00-00-00"
    (tmp_path / sid).mkdir()

    # One identity to assign everything to.
    r = client.post(f"/api/sessions/{sid}/identities",
                    json={"name": "A", "color": "#ff0000"})
    assert r.status_code == 201, r.text
    ident = r.json()["identity_id"]

    def _assign(frame: int):
        return client.post(
            f"/api/sessions/{sid}/identities/{ident}/assign",
            json={"frame": frame, "face_idx": 0},
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_assign, range(24)))
    assert all(r.status_code == 200 for r in results), \
        [r.status_code for r in results]

    listed = client.get(f"/api/sessions/{sid}/identities/assignments").json()
    frames = sorted(a["frame"] for a in listed)
    assert frames == list(range(24))  # pre-lock: read-modify-write lost some
