"""/api/sessions/* — Session list, detail, video, fex."""

from __future__ import annotations

import csv as _csv
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import FileResponse

from pyfeatlive_core.recorder import default_sessions_root
from pyfeatlive_core.session_io import (
    FEX_FILENAME,
    VIDEO_FILENAME,
    load_metadata,
    session_summary,
)
from pyfeatlive_core.thumbnails import extract_face_crop


router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# (session_id-independent) mtime-keyed caches. Keyed by (path, mtime_ns) —
# nanosecond mtime, not float st_mtime, so two rewrites within the same
# float-precision instant still invalidate correctly — so any rewrite of
# the underlying file invalidates naturally; bounded by keeping only the
# most recent entry per path.
_BBOX_CACHE: dict[str, tuple[int, dict[tuple[int, int], tuple[float, float, float, float]]]] = {}
_FRAME_TIMES_CACHE: dict[str, tuple[int, list[float]]] = {}


def _bbox_index(fex_path: Path) -> dict[tuple[int, int], tuple[float, float, float, float]]:
    """(frame, face_idx) -> bbox for every row, parsed once per fex mtime.

    The Viewer's identity strip requests one thumbnail per identity; each
    previously re-scanned the whole CSV (k full parses for k identities).
    """
    key = str(fex_path)
    mtime = fex_path.stat().st_mtime_ns
    hit = _BBOX_CACHE.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    index: dict[tuple[int, int], tuple[float, float, float, float]] = {}
    with open(fex_path, newline="") as f:
        for row in _csv.DictReader(f):
            try:
                pair = (int(row["frame"]), int(row["face_idx"]))
                if pair in index:
                    continue  # first occurrence wins — the pre-index scan
                              # broke on first match; keep that contract for
                              # any file with duplicate (frame, face_idx) rows
                index[pair] = (
                    float(row["FaceRectX"]), float(row["FaceRectY"]),
                    float(row["FaceRectWidth"]), float(row["FaceRectHeight"]),
                )
            except (KeyError, ValueError):
                continue
    _BBOX_CACHE[key] = (mtime, index)
    return index


def _frame_times_cached(video_path: Path) -> list[float]:
    """Sorted per-frame presentation timestamps, demuxed once per video mtime.

    Live recordings are written with VARIABLE wall-clock PTS at the detection
    rate, so a fixed-fps `time = frame / fps` mapping drifts and the overlay
    desyncs from the video. The fex rows are written lock-step with the video
    frames (one per encoded frame, in order), so the Viewer aligns fex frame K
    to the K-th timestamp here and maps video.currentTime <-> frame by actual
    time. Demuxes packets (no full decode).
    """
    import av

    key = str(video_path)
    mtime = video_path.stat().st_mtime_ns
    hit = _FRAME_TIMES_CACHE.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]

    times: list[float] = []
    container = av.open(str(video_path))
    try:
        stream = container.streams.video[0]
        tb = stream.time_base
        for packet in container.demux(stream):
            if packet.pts is None:
                continue
            times.append(float(packet.pts * tb) if tb else float(packet.pts))
    finally:
        container.close()
    times.sort()
    _FRAME_TIMES_CACHE[key] = (mtime, times)
    return times


def _list_session_dirs() -> list[Path]:
    """Return all session subdirectories in the configured root."""
    root = default_sessions_root()
    if not root.exists():
        return []
    return sorted(
        (d for d in root.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,  # newest-first by timestamped name
    )


def _resolve_session(session_id: str) -> Path:
    """Resolve a session ID to a Path, with traversal protection.

    Raises 404 if the directory doesn't exist or escapes the sessions
    root via symlinks/relative paths.
    """
    root = default_sessions_root().resolve()
    candidate = (root / session_id).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise HTTPException(404, "session not found")
    if not candidate.is_dir():
        raise HTTPException(404, "session not found")
    return candidate


@router.get("")
def list_sessions() -> list[dict]:
    return [session_summary(d) for d in _list_session_dirs()]


@router.get("/{session_id}")
def get_session(session_id: str) -> dict:
    d = _resolve_session(session_id)
    summary = session_summary(d)
    summary["metadata"] = load_metadata(d)
    return summary


_RANGE_CHUNK = 1024 * 1024  # 1 MiB per read: bounded memory however large the range


def _serve_range(file_path: Path, range_header: str) -> Response:
    """Parse a Range header and return a 206 Partial Content response.

    Streams the range in chunks instead of materializing it — browsers
    open <video> with ``bytes=0-``, which previously buffered the whole
    recording into memory per request (and again on every scrub).
    """
    from fastapi.responses import StreamingResponse

    size = file_path.stat().st_size
    spec = range_header[len("bytes="):].split(",", 1)[0].strip()
    start_str, _, end_str = spec.partition("-")
    if start_str == "":
        # suffix range
        suffix = int(end_str)
        if suffix < 0:
            raise HTTPException(400, "negative suffix")
        start = max(0, size - suffix)
        end = size - 1
    else:
        start = int(start_str)
        end = int(end_str) if end_str else size - 1
        if start < 0 or start >= size:
            raise HTTPException(416, "range out of bounds")
    end = min(end, size - 1)
    if end < start:
        # Inverted range (e.g. bytes=500-100): previously produced a
        # negative length and a read-to-EOF body that contradicted
        # Content-Length. 416 per RFC 9110.
        raise HTTPException(416, "range out of bounds")
    length = end - start + 1

    def _iter():
        remaining = length
        with open(file_path, "rb") as f:
            f.seek(start)
            while remaining > 0:
                chunk = f.read(min(_RANGE_CHUNK, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        _iter(),
        status_code=206,
        headers={
            "Content-Range": f"bytes {start}-{end}/{size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        },
        media_type="video/mp4",
    )


@router.get("/{session_id}/video")
def get_session_video(session_id: str, request: Request) -> Response:
    d = _resolve_session(session_id)
    video = d / VIDEO_FILENAME
    if not video.is_file():
        raise HTTPException(404, "video not found")
    range_header = request.headers.get("Range") or ""
    if range_header.startswith("bytes="):
        try:
            return _serve_range(video, range_header)
        except ValueError:
            raise HTTPException(400, "bad Range header")
    # Non-Range request: stream the file instead of buffering the whole
    # (potentially hundreds of MB) recording into memory per request.
    return FileResponse(
        video,
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"},
    )


@router.get("/{session_id}/fex")
def get_session_fex(session_id: str) -> Response:
    d = _resolve_session(session_id)
    fex = d / FEX_FILENAME
    if not fex.is_file():
        raise HTTPException(404, "fex not found")
    return FileResponse(fex, media_type="text/csv")


@router.get("/{session_id}/face-thumbnail/{frame}/{face_idx}")
def face_thumbnail(session_id: str, frame: int, face_idx: int) -> Response:
    d = _resolve_session(session_id)
    video_path = d / VIDEO_FILENAME
    if not video_path.exists():
        raise HTTPException(404, "no video in session")

    fex_path = d / FEX_FILENAME
    if not fex_path.exists():
        raise HTTPException(404, "no fex.csv in session")

    bbox = _bbox_index(fex_path).get((frame, face_idx))
    if bbox is None:
        raise HTTPException(404, "face not found for that (frame, face_idx)")

    png_bytes = extract_face_crop(video_path, frame, bbox)
    if png_bytes is None:
        raise HTTPException(500, "frame extraction failed")
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{session_id}/frame-times")
def frame_times(session_id: str) -> dict[str, list[float]]:
    """Per-frame presentation timestamps (seconds) of the session video.

    Live recordings are written with VARIABLE wall-clock PTS at the detection
    rate, so a fixed-fps `time = frame / fps` mapping drifts and the overlay
    desyncs from the video. The fex rows are written lock-step with the video
    frames (one per encoded frame, in order), so the Viewer aligns fex frame K
    to the K-th timestamp here and maps video.currentTime ⇄ frame by actual
    time. Demuxes packets (no full decode) and returns them in presentation
    order.
    """
    d = _resolve_session(session_id)
    video_path = d / VIDEO_FILENAME
    if not video_path.exists():
        raise HTTPException(404, "no video in session")

    return {"times": _frame_times_cached(video_path)}


@router.post("/{session_id}/reveal")
def reveal_session(session_id: str) -> dict[str, str]:
    """Open the OS file manager with the session folder selected.

    Reuses the same sidecar-side helper the Logs drawer uses — the desktop
    WebView can't open Finder/Explorer itself, but the Python sidecar has
    full filesystem access.
    """
    from pyfeatlive_core.recorder import reveal_in_file_manager

    d = _resolve_session(session_id)
    reveal_in_file_manager(d)
    return {"path": str(d)}
