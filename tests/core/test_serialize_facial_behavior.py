import math

import pandas as pd
import pytest

from backend import serialization


def test_serialization_adds_bounded_facial_behavior_indices(monkeypatch):
    monkeypatch.setattr(serialization, "_blendshape_region_cols", lambda: ())
    fex = pd.DataFrame({
        "face_idx": [0],
        "FaceScore": [0.8],
        "AU06": [0.81],
        "AU12": [0.81],
    })

    face = serialization.serialize_faces(fex, mp_landmarks=False)[0]
    behavior = face["facial_behavior"]

    assert behavior["facial_valence"] == pytest.approx(81.0)
    assert behavior["facial_activation"] == pytest.approx(81.0)
    assert behavior["confidence"] == pytest.approx(100 * 0.8 * 2 / 12)
    assert behavior["expression_evidence"]["smile_like"] == pytest.approx(0.81)


def test_invalid_aus_lower_confidence_without_nan_output(monkeypatch):
    monkeypatch.setattr(serialization, "_blendshape_region_cols", lambda: ())
    fex = pd.DataFrame({
        "FaceScore": [1.0],
        "AU06": [float("nan")],
        "AU12": [float("inf")],
    })

    behavior = serialization.serialize_faces(fex, mp_landmarks=False)[0]["facial_behavior"]
    assert behavior["confidence"] == 0.0
    assert all(
        math.isfinite(number)
        for key, number in behavior.items()
        if key != "expression_evidence"
    )
