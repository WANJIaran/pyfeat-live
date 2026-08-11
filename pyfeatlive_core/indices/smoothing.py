"""Smoothing, Hysteresis, and Calibration Utilities for Facial Behavior Indices.

RESEARCH-ONLY DISCLAIMER:
These temporal filters and calibration utilities are designed for research signal processing
to stabilize noise and account for individual baseline differences in Action Unit activations.
"""

import math
from typing import Dict, Union, Optional, Any

from pyfeatlive_core.indices.heuristics import normalize_au_key


def _finite_float(value: Any) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


class EWMAFilter:
    """Exponentially Weighted Moving Average (EWMA) filter for scalar signals or AU dicts.

    Formula: y_t = alpha * x_t + (1 - alpha) * y_{t-1}
    """

    def __init__(self, alpha: float = 0.3):
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"Alpha must be in range (0.0, 1.0], got {alpha}")
        self.alpha = float(alpha)
        self._state: Optional[float] = None

    def reset(self, initial_value: Optional[float] = None) -> None:
        """Reset the filter state."""
        self._state = _finite_float(initial_value)

    def filter(self, sample: float) -> float:
        """Update filter with a new scalar sample and return smoothed output."""
        numeric_sample = _finite_float(sample)
        if numeric_sample is None:
            return self._state if self._state is not None else 0.0

        if self._state is None:
            self._state = numeric_sample
        else:
            self._state = self.alpha * numeric_sample + (1.0 - self.alpha) * self._state
        return self._state


class DictEWMAFilter:
    """EWMA filter operating on dictionaries of AU probabilities or evidence values."""

    def __init__(self, alpha: float = 0.3):
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"Alpha must be in range (0.0, 1.0], got {alpha}")
        self.alpha = float(alpha)
        self._state: Dict[str, float] = {}

    def reset(self) -> None:
        self._state.clear()

    def filter(self, sample_dict: Dict[str, float]) -> Dict[str, float]:
        """Apply EWMA smoothing to every key in sample_dict."""
        if not isinstance(sample_dict, dict):
            return dict(self._state)

        result: Dict[str, float] = {}
        for k, v in sample_dict.items():
            numeric_value = _finite_float(v)
            if numeric_value is None:
                val = self._state.get(k, 0.0)
            else:
                val = numeric_value

            if k not in self._state:
                self._state[k] = val
            else:
                self._state[k] = self.alpha * val + (1.0 - self.alpha) * self._state[k]

            result[k] = self._state[k]
        return result


class HysteresisThreshold:
    """Dual-threshold hysteresis gate to prevent rapid toggling of discrete evidence states.

    Properties:
    - Standard low_threshold <= high_threshold.
    - If current state is True, transitions to False if value < low_threshold.
    - If current state is False, transitions to True if value > high_threshold.
    """

    def __init__(self, low_threshold: float, high_threshold: float, initial_state: bool = False):
        if low_threshold > high_threshold:
            raise ValueError(f"low_threshold ({low_threshold}) must be <= high_threshold ({high_threshold})")
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)
        self.state = bool(initial_state)

    def update(self, value: float) -> bool:
        """Update hysteresis state with new value and return active state."""
        numeric_value = _finite_float(value)
        if numeric_value is None:
            return self.state

        val = numeric_value
        if self.state:
            if val < self.low_threshold:
                self.state = False
        else:
            if val > self.high_threshold:
                self.state = True

        return self.state


class NeutralBaselineCalibration:
    """Neutral baseline calibration for subject-specific resting facial action probabilities.

    Baseline-subtracted probability calculation:
    p_calibrated = max(0.0, (p_raw - b_au) / (1.0 - b_au)) if b_au < 1.0 else 0.0
    """

    def __init__(self, baseline_aus: Optional[Dict[str, float]] = None):
        self.baseline: Dict[str, float] = {}
        if baseline_aus:
            self.set_baseline(baseline_aus)

    def set_baseline(self, baseline_aus: Dict[str, float]) -> None:
        """Set baseline resting AU activation probabilities."""
        self.baseline.clear()
        if isinstance(baseline_aus, dict):
            for k, v in baseline_aus.items():
                numeric_value = _finite_float(v)
                if numeric_value is not None:
                    self.baseline[normalize_au_key(k)] = max(0.0, min(1.0, numeric_value))

    def calibrate(self, au_probabilities: Dict[str, float]) -> Dict[str, float]:
        """Calibrate input AU probabilities relative to subject neutral baseline."""
        if not isinstance(au_probabilities, dict):
            return {}

        calibrated: Dict[str, float] = {}
        for k, v in au_probabilities.items():
            normalized_key = normalize_au_key(k)
            numeric_value = _finite_float(v)
            if numeric_value is None:
                p_raw = 0.0
            else:
                p_raw = max(0.0, min(1.0, numeric_value))

            b_au = self.baseline.get(normalized_key, 0.0)

            if b_au >= 1.0:
                p_cal = 0.0
            elif p_raw <= b_au:
                p_cal = 0.0
            else:
                p_cal = (p_raw - b_au) / (1.0 - b_au)

            calibrated[k] = max(0.0, min(1.0, p_cal))

        return calibrated
