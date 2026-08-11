"""Minimal serialization and schema hook for Facial Behavior Indices.

RESEARCH-ONLY DISCLAIMER:
This schema provides minimal, safe JSON-compatible serialization helpers without altering
or coupling to live pipeline implementations.
"""

import json
import math
from typing import Dict, Any, Optional
from pyfeatlive_core.indices.heuristics import FacialBehaviorIndices, ExpressionEvidence


def _bounded_finite(value: Any, low: float, high: float) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric_value):
        return 0.0
    return max(low, min(high, numeric_value))


def indices_to_dict(indices: FacialBehaviorIndices) -> Dict[str, Any]:
    """Serialize FacialBehaviorIndices to a plain JSON-compatible dictionary."""
    if not isinstance(indices, FacialBehaviorIndices):
        return FacialBehaviorIndices().to_dict()
    return indices.to_dict()


def indices_from_dict(data: Dict[str, Any]) -> FacialBehaviorIndices:
    """Safely deserialize dictionary into FacialBehaviorIndices with bound enforcement."""
    if not isinstance(data, dict):
        return FacialBehaviorIndices()

    v = data.get("facial_valence", 0.0)
    a = data.get("facial_activation", 0.0)
    c = data.get("confidence", 0.0)

    facial_valence = _bounded_finite(v, -100.0, 100.0)
    facial_activation = _bounded_finite(a, 0.0, 100.0)
    confidence = _bounded_finite(c, 0.0, 100.0)

    ev_data = data.get("expression_evidence", {})
    if isinstance(ev_data, dict):
        ev = ExpressionEvidence(
            smile_like=_bounded_finite(ev_data.get("smile_like", 0.0), 0.0, 1.0),
            sad_like=_bounded_finite(ev_data.get("sad_like", 0.0), 0.0, 1.0),
            anger_like=_bounded_finite(ev_data.get("anger_like", 0.0), 0.0, 1.0),
            surprise_like=_bounded_finite(ev_data.get("surprise_like", 0.0), 0.0, 1.0),
            disgust_like=_bounded_finite(ev_data.get("disgust_like", 0.0), 0.0, 1.0),
        )
    else:
        ev = ExpressionEvidence()

    return FacialBehaviorIndices(
        facial_valence=facial_valence,
        facial_activation=facial_activation,
        confidence=confidence,
        expression_evidence=ev,
    )


def indices_to_json(indices: FacialBehaviorIndices) -> str:
    """Serialize FacialBehaviorIndices to JSON string."""
    return json.dumps(indices_to_dict(indices))


def indices_from_json(json_str: str) -> FacialBehaviorIndices:
    """Deserialize JSON string into FacialBehaviorIndices."""
    try:
        data = json.loads(json_str)
        return indices_from_dict(data)
    except (json.JSONDecodeError, TypeError):
        return FacialBehaviorIndices()
