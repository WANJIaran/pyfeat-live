"""Unit tests for pyfeatlive_core.indices package.

Tests bounds, missing data handling, monotonicity, quality impact, smoothing,
hysteresis, calibration, and numerical safety (no NaN/inf).
"""

import math
import pytest
from pyfeatlive_core.indices.heuristics import (
    calculate_indices,
    calculate_expression_evidence,
    normalize_au_key,
    extract_au_probabilities,
    FacialBehaviorIndices,
    ExpressionEvidence,
)
from pyfeatlive_core.indices.smoothing import (
    EWMAFilter,
    DictEWMAFilter,
    HysteresisThreshold,
    NeutralBaselineCalibration,
)
from pyfeatlive_core.indices.schema import (
    indices_to_dict,
    indices_from_dict,
    indices_to_json,
    indices_from_json,
)


def test_normalize_au_key():
    assert normalize_au_key("AU06") == "AU06"
    assert normalize_au_key("AU6") == "AU06"
    assert normalize_au_key("06") == "AU06"
    assert normalize_au_key(6) == "AU06"
    assert normalize_au_key("au12") == "AU12"


def test_bounds_and_ranges():
    # Test full activation across all AUs
    full_aus = {f"AU{i:02d}": 1.0 for i in range(1, 30)}
    res = calculate_indices(full_aus, tracking_quality=1.0, pose_quality=1.0)

    assert -100.0 <= res.facial_valence <= 100.0
    assert 0.0 <= res.facial_activation <= 100.0
    assert 0.0 <= res.confidence <= 100.0
    assert res.confidence == 100.0

    # Test all zero activation
    zero_aus = {f"AU{i:02d}": 0.0 for i in range(1, 30)}
    res_zero = calculate_indices(zero_aus, tracking_quality=1.0, pose_quality=1.0)

    assert res_zero.facial_valence == 0.0
    assert res_zero.facial_activation == 0.0
    assert res_zero.confidence == 100.0


def test_missing_data():
    # Empty AU dictionary
    res_empty = calculate_indices({}, tracking_quality=1.0, pose_quality=1.0)
    assert res_empty.facial_valence == 0.0
    assert res_empty.facial_activation == 0.0
    assert res_empty.confidence == 0.0  # 0% coverage ratio

    # Partial AU dictionary (only smile AUs)
    partial_aus = {"AU06": 0.8, "AU12": 0.8}
    res_partial = calculate_indices(partial_aus, tracking_quality=1.0, pose_quality=1.0)
    assert res_partial.expression_evidence.smile_like == pytest.approx(0.8)
    assert res_partial.confidence < 100.0  # Missing other required AUs reduces confidence
    assert res_partial.confidence > 0.0


def test_monotonicity():
    # Increasing AU06 and AU12 must monotonically increase smile_like evidence and valence
    base_aus = {"AU06": 0.2, "AU12": 0.2}
    res_base = calculate_indices(base_aus)

    higher_aus = {"AU06": 0.9, "AU12": 0.9}
    res_higher = calculate_indices(higher_aus)

    assert res_higher.expression_evidence.smile_like >= res_base.expression_evidence.smile_like
    assert res_higher.facial_valence >= res_base.facial_valence


def test_quality_impact():
    full_aus = {f"AU{i:02d}": 0.5 for i in range(1, 30)}

    high_qual = calculate_indices(full_aus, tracking_quality=1.0, pose_quality=1.0)
    low_qual = calculate_indices(full_aus, tracking_quality=0.4, pose_quality=0.5)

    assert high_qual.confidence == 100.0
    assert low_qual.confidence == pytest.approx(20.0)  # 100 * 0.4 * 0.5 * 1.0


def test_surprise_non_negative_valence():
    # Pure surprise (AU01 + AU02 + AU05 + AU26) should NOT reduce valence into negative numbers
    surprise_aus = {"AU01": 0.9, "AU02": 0.9, "AU05": 0.9, "AU26": 0.9}
    res = calculate_indices(surprise_aus)

    assert res.expression_evidence.surprise_like == pytest.approx(0.9)
    assert res.facial_valence >= 0.0
    assert res.facial_activation == pytest.approx(90.0)


def test_disgust_max_aggregation():
    # Disgust is max(AU09, AU10)
    disgust_aus1 = {"AU09": 0.3, "AU10": 0.7}
    res1 = calculate_indices(disgust_aus1)
    assert res1.expression_evidence.disgust_like == pytest.approx(0.7)

    disgust_aus2 = {"AU09": 0.8, "AU10": 0.2}
    res2 = calculate_indices(disgust_aus2)
    assert res2.expression_evidence.disgust_like == pytest.approx(0.8)


def test_nan_inf_robustness():
    nan_aus = {
        "AU01": float("nan"),
        "AU04": float("inf"),
        "AU06": -0.5,
        "AU12": 1.5,  # Should be clamped to 1.0
    }
    res = calculate_indices(nan_aus, tracking_quality=float("nan"), pose_quality=float("inf"))

    assert not math.isnan(res.facial_valence)
    assert not math.isinf(res.facial_valence)
    assert not math.isnan(res.facial_activation)
    assert not math.isnan(res.confidence)
    assert res.expression_evidence.smile_like == 0.0  # AU06 negative -> clamped to 0.0
    _, coverage = extract_au_probabilities(nan_aus)
    assert coverage == pytest.approx(2 / 12)  # invalid AU01/AU04 do not count as observed


def test_ewma_filter():
    filt = EWMAFilter(alpha=0.5)
    assert filt.filter(10.0) == 10.0
    assert filt.filter(20.0) == 15.0
    assert filt.filter(20.0) == 17.5

    # Filter with NaN
    assert filt.filter(float("nan")) == 17.5
    assert filt.filter("invalid") == 17.5

    # Dict EWMA Filter
    dict_filt = DictEWMAFilter(alpha=0.5)
    res1 = dict_filt.filter({"valence": 10.0, "activation": 50.0})
    assert res1["valence"] == 10.0
    assert res1["activation"] == 50.0

    res2 = dict_filt.filter({"valence": 20.0, "activation": 50.0})
    assert res2["valence"] == 15.0
    assert res2["activation"] == 50.0


def test_hysteresis_threshold():
    hyst = HysteresisThreshold(low_threshold=0.3, high_threshold=0.7, initial_state=False)

    assert not hyst.update(0.5)  # Under high_threshold, stays False
    assert hyst.update(0.8)      # Exceeds high_threshold, becomes True
    assert hyst.update(0.4)      # Above low_threshold, stays True
    assert not hyst.update(0.2)  # Below low_threshold, becomes False


def test_neutral_baseline_calibration():
    calib = NeutralBaselineCalibration({"AU06": 0.2, "AU12": 0.2})
    raw_aus = {"AU06": 0.6, "AU12": 0.1}

    calibrated = calib.calibrate(raw_aus)
    # AU06: (0.6 - 0.2) / (1 - 0.2) = 0.4 / 0.8 = 0.5
    assert calibrated["AU06"] == pytest.approx(0.5)
    # AU12: raw (0.1) <= baseline (0.2) -> 0.0
    assert calibrated["AU12"] == 0.0

    # Equivalent AU key spellings must share one baseline.
    calib.set_baseline({"AU6": 0.2})
    assert calib.calibrate({"AU06": 0.6})["AU06"] == pytest.approx(0.5)


def test_schema_serialization():
    indices = calculate_indices({"AU06": 0.8, "AU12": 0.8})

    # Dict roundtrip
    d = indices_to_dict(indices)
    assert isinstance(d, dict)
    recovered = indices_from_dict(d)
    assert recovered.facial_valence == indices.facial_valence
    assert recovered.expression_evidence.smile_like == indices.expression_evidence.smile_like

    # JSON roundtrip
    j_str = indices_to_json(indices)
    assert isinstance(j_str, str)
    recovered_j = indices_from_json(j_str)
    assert recovered_j.facial_valence == indices.facial_valence


def test_schema_rejects_non_finite_and_invalid_values():
    recovered = indices_from_dict({
        "facial_valence": float("nan"),
        "facial_activation": float("inf"),
        "confidence": "invalid",
        "expression_evidence": {"smile_like": float("nan"), "sad_like": "invalid"},
    })
    assert recovered.facial_valence == 0.0
    assert recovered.facial_activation == 0.0
    assert recovered.confidence == 0.0
    assert recovered.expression_evidence.smile_like == 0.0
    assert recovered.expression_evidence.sad_like == 0.0
