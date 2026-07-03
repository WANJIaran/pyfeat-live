"""Runner: process a single image, yield one progress event, end DONE."""

import threading
from pathlib import Path

import pytest

from pyfeatlive_core.analyze_queue import (
    AnalyzeQueueItem, PipelineConfig, VideoParams, QueueStatus,
)
from pyfeatlive_core.analyze_runner import run_item
from pyfeatlive_core.detector import DetectorConfig, build_detector


@pytest.fixture
def detector():
    return build_detector(DetectorConfig(device="cpu"))


@pytest.fixture
def run_root(tmp_path):
    return tmp_path / "sessions"


@pytest.mark.timeout(120)
def test_run_single_image(detector, run_root):
    # Must be a fixture with a *real* detectable face: the runner only
    # writes a session when at least one face is detected (an empty Fex
    # leaves the recorder with nothing to persist, and it then removes
    # the empty session dir). sample_image.jpg is a 32x32 placeholder
    # with no face, so it would (correctly) produce no session.
    fixture = Path("tests/core/fixtures/single_face.jpg")
    item = AnalyzeQueueItem(
        id="auto",
        filename=fixture.name,
        file_path=fixture,
        pipeline=PipelineConfig(
            detector_type="MPDetector",
            face_model="retinaface", landmark_model="mp_facemesh_v2",
            au_model="mp_blendshapes",
            emotion_model=None, identity_model=None,
            preset_id=None, preset_name=None,
        ),
        video=VideoParams(),
    )
    events = list(run_item(item, detector, run_root, batch_size=1))
    # Should have at least one progress event and a final 'done' event.
    statuses = [e["type"] for e in events]
    assert "progress" in statuses
    assert "done" in statuses
    assert item.status is QueueStatus.DONE
    assert item.session_dir is not None
    # The 32×32 fixture is too small for face detection, so the recorder
    # cleans up the empty session dir (the "don't litter ~/Documents"
    # rule). When the dir survives it should contain fex.csv.
    if Path(item.session_dir).exists():
        assert (Path(item.session_dir) / "fex.csv").exists()


def test_cancel_before_first_batch(tmp_path):
    """Pre-set cancel event: runner breaks before the first detect call."""
    fixture = Path("tests/core/fixtures/sample_image.jpg")
    item = AnalyzeQueueItem(
        id="auto",
        filename=fixture.name,
        file_path=fixture,
        pipeline=PipelineConfig(
            detector_type="Detector",
            face_model="retinaface", landmark_model="mobilefacenet",
            au_model="xgb", emotion_model=None, identity_model=None,
            preset_id=None, preset_name=None,
        ),
        video=VideoParams(),
    )
    cancel = threading.Event()
    cancel.set()
    events = list(run_item(
        item, detector=None,
        sessions_root=tmp_path / "sessions",
        batch_size=8, cancel_event=cancel,
    ))
    types = [e["type"] for e in events]
    assert "cancelled" in types
    assert "done" not in types
    assert item.status is QueueStatus.CANCELLED
    assert item.progress_frames == 0
    # session_dir is set but the recorder removes empty session folders
    # (no faces ever offered) — so the dir may not exist on disk. That's
    # the recorder's "don't litter ~/Documents" rule, not a bug here.


def test_recorder_closed_when_detection_errors(tmp_path, monkeypatch):
    """A detection failure mid-run must still close the recorder (the
    finally block): its writer thread joins and the empty session dir is
    not orphaned. Regression for the pre-fix path where recorder.close()
    only ran on success."""
    import pyfeatlive_core.analyze_runner as runner

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated detection failure")

    monkeypatch.setattr(runner, "detect_pil_images", _boom)

    run_root = tmp_path / "sessions"
    fixture = Path("tests/core/fixtures/sample_image.jpg")
    item = AnalyzeQueueItem(
        id="auto",
        filename=fixture.name,
        file_path=fixture,
        pipeline=PipelineConfig(
            detector_type="MPDetector",
            face_model="retinaface", landmark_model="mp_facemesh_v2",
            au_model="mp_blendshapes",
            emotion_model=None, identity_model=None,
            preset_id=None, preset_name=None,
        ),
        video=VideoParams(),
    )
    before = {id(t) for t in threading.enumerate() if t.name == "SessionRecorder"}
    # detector arg is unused — detect_pil_images is patched to raise.
    events = list(run_item(item, object(), run_root, batch_size=1))

    assert events[-1]["type"] == "failed"
    assert item.status is QueueStatus.FAILED
    # close() ran in the finally → writer thread joined (no NEW live one).
    leaked = [t for t in threading.enumerate()
              if t.name == "SessionRecorder" and t.is_alive() and id(t) not in before]
    assert not leaked, "recorder writer thread leaked after error"
    # close() ran → the empty session dir was removed, none orphaned.
    leftover = list(run_root.iterdir()) if run_root.exists() else []
    assert leftover == [], f"orphaned session dir after error: {leftover}"


def test_effective_batch_size_scales_with_resolution():
    from pyfeatlive_core.analyze_runner import _effective_batch_size

    # 720p and below: the requested batch stands.
    assert _effective_batch_size(8, 1280, 720) == 8
    assert _effective_batch_size(8, 640, 360) == 8
    # 4K (3840x2160 = 9x the 720p pixel count): 8 -> 1 to keep the
    # float32 batch tensor within the tuned 720p budget.
    assert _effective_batch_size(8, 3840, 2160) == 1
    # 1440p (~2.7x): 8 -> 2.
    assert _effective_batch_size(8, 2560, 1440) == 2
    # Never below 1; never above the request; degenerate dims are safe.
    assert _effective_batch_size(8, 7680, 4320) == 1
    assert _effective_batch_size(2, 640, 360) == 2
    assert _effective_batch_size(8, 0, 0) == 8


import av as _av


def _make_video(path, n_frames=60, fps=30, size=(64, 64)):
    import numpy as np
    container = _av.open(str(path), "w")
    stream = container.add_stream("h264", rate=fps)
    stream.width, stream.height = size
    stream.pix_fmt = "yuv420p"
    for i in range(n_frames):
        arr = np.full((size[1], size[0], 3), (i * 4) % 255, dtype=np.uint8)
        frame = _av.VideoFrame.from_ndarray(arr, format="rgb24")
        for pkt in stream.encode(frame):
            container.mux(pkt)
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


def test_estimate_frames_close_to_actual(tmp_path):
    from pyfeatlive_core.analyze_runner import _estimate_frames
    p = _make_video(tmp_path / "v.mp4", n_frames=60, fps=30)
    c = _av.open(str(p))
    try:
        est = _estimate_frames(c.streams.video[0])
    finally:
        c.close()
    assert est is not None and abs(est - 60) <= 3


def _make_vfr_video(path, n_frames=40, size=(64, 64)):
    """Encode an mp4 with explicit, jittered PTS — mimicking this app's own
    Live recorder, which writes wall-clock-ms PTS rather than a constant
    frame rate. Gaps cycle deterministically over 80-219ms."""
    import numpy as np
    from fractions import Fraction

    container = _av.open(str(path), "w")
    stream = container.add_stream("h264", rate=30)
    stream.width, stream.height = size
    stream.pix_fmt = "yuv420p"
    stream.codec_context.time_base = Fraction(1, 1000)
    pts_ms = 0
    for i in range(n_frames):
        arr = np.full((size[1], size[0], 3), (i * 4) % 255, dtype=np.uint8)
        frame = _av.VideoFrame.from_ndarray(arr, format="rgb24")
        frame.pts = pts_ms
        frame.time_base = Fraction(1, 1000)
        for pkt in stream.encode(frame):
            container.mux(pkt)
        pts_ms += 80 + (i * 37) % 140  # jittered wall-clock-style gap
    for pkt in stream.encode():
        container.mux(pkt)
    container.close()
    return path


def test_vfr_source_yields_positional_indices(tmp_path):
    """Regression: a VFR source (wall-clock-ms PTS, like this app's own
    Live recordings) must not have its fex frame indices derived from
    round(pts*fps) — that corrupts them into duplicate/gapped values on
    non-CFR streams. With no clip_start (no seek), indexing must be plain
    positional decode order."""
    from pyfeatlive_core.analyze_runner import _iter_video_frames
    from pyfeatlive_core.analyze_queue import VideoParams

    n = 40
    p = _make_vfr_video(tmp_path / "vfr.mp4", n_frames=n)
    vp = VideoParams(skip_frames=1, clip_start=None, clip_end=None,
                     track_identities=False)
    frames = list(_iter_video_frames(p, vp))
    idxs = [i for i, _ in frames]
    assert idxs == list(range(len(idxs))), (
        f"VFR source produced non-positional indices: {idxs}"
    )
    assert len(idxs) == n


def test_clip_start_seeks_not_decodes(tmp_path):
    from pyfeatlive_core.analyze_runner import _iter_video_frames
    from pyfeatlive_core.analyze_queue import VideoParams
    p = _make_video(tmp_path / "v.mp4", n_frames=90, fps=30)
    vp = VideoParams(skip_frames=1, clip_start=2.0, clip_end=None,
                     track_identities=False)
    frames = list(_iter_video_frames(p, vp))
    # First yielded source index must be ~frame 60 (2.0s * 30fps); the
    # seek lands on the nearest PRIOR keyframe, so indices before 60 must
    # still be filtered out, and indexing must reflect SOURCE positions.
    assert frames, "no frames yielded"
    first_idx = frames[0][0]
    assert 58 <= first_idx <= 62
    # Frame indices remain source-referenced and STRICTLY increasing (no
    # duplicates — a duplicate here would mean two decoded frames mapped
    # to the same pts->position, corrupting downstream fex.csv rows).
    idxs = [i for i, _ in frames]
    assert all(b > a for a, b in zip(idxs, idxs[1:]))
    assert idxs[-1] <= 90


def test_clip_start_fractional_fps_boundary(tmp_path):
    """23.976-style rates: the first admitted frame must be the first with
    index >= clip_start*fps (truncation admitted one early + shifted stride)."""
    import math
    from fractions import Fraction
    from pyfeatlive_core.analyze_runner import _iter_video_frames
    from pyfeatlive_core.analyze_queue import VideoParams

    p = _make_video(tmp_path / "ntsc.mp4", n_frames=72, fps=Fraction(24000, 1001))
    c = _av.open(str(p))
    try:
        fps = float(c.streams.video[0].average_rate)
    finally:
        c.close()
    vp = VideoParams(skip_frames=1, clip_start=1.0, clip_end=None,
                     track_identities=False)
    frames = list(_iter_video_frames(p, vp))
    assert frames, "no frames yielded"
    assert frames[0][0] == math.ceil(1.0 * fps)
