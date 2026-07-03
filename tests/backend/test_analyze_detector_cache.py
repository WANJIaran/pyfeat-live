"""Consecutive queue items with the same config reuse one detector build."""

import asyncio

import pytest

from pyfeatlive_core.detector import DetectorConfig


def test_same_config_builds_once(client, monkeypatch):
    from backend.routers import analyze as analyze_router

    builds: list[DetectorConfig] = []

    def _fake_build(cfg):
        builds.append(cfg)
        return object()

    monkeypatch.setattr(analyze_router, "build_detector", _fake_build)

    app = client.app
    cfg = DetectorConfig(device="cpu")

    async def _run():
        d1 = await analyze_router._get_or_build_detector(app, cfg)
        d2 = await analyze_router._get_or_build_detector(app, cfg)
        assert d1 is d2
        d3 = await analyze_router._get_or_build_detector(
            app, DetectorConfig(device="cpu", detector_type="MPDetector"),
        )
        assert d3 is not d1

    asyncio.run(_run())
    assert len(builds) == 2  # cpu Detectorv2 once, MPDetector once
