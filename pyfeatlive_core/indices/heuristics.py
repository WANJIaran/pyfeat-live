"""Facial Behavior Index - Heuristic Expression Configuration Evidence.

RESEARCH-ONLY DISCLAIMER:
This module provides a research-only framework for computing bounded, heuristic
facial behavior indices from Action Unit (AU) activation probabilities.

IMPORTANT SAFETY AND SCIENTIFIC CONSTRAINTS:
1. NEVER claim or infer true internal mood, mental state, deception, psychiatric
   diagnosis, or intent. Outputs represent strictly observed facial actions,
   expression-configuration evidence, and perceived facial affect.
2. Py-Feat DetectorV2 Action Unit outputs are activation probabilities in [0, 1],
   NOT FACS A-E intensity levels.
3. Pretrained models and heuristic rules are strictly for research exploration.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, Tuple


# Key Action Units relevant for heuristic expression configurations
REQUIRED_AUS = (
    "AU01", "AU02", "AU04", "AU05", "AU06", "AU07",
    "AU09", "AU10", "AU12", "AU15", "AU23", "AU26"
)


def normalize_au_key(key: Union[str, int]) -> str:
    """Normalize various AU key formats (e.g., 'AU06', 'AU6', '06', 6) to standard 'AU06' format."""
    s = str(key).strip().upper()
    if s.startswith("AU"):
        num_str = s[2:]
    else:
        num_str = s
    try:
        num = int(num_str)
        return f"AU{num:02d}"
    except ValueError:
        return s


def sanitize_probability(val: Any) -> float:
    """Ensure AU activation probability is a valid finite float in range [0.0, 1.0]."""
    numeric_value = _finite_float(val)
    if numeric_value is None:
        return 0.0
    return max(0.0, min(1.0, numeric_value))


def _finite_float(val: Any) -> Optional[float]:
    """Return a finite float, or ``None`` when the input is unusable."""
    try:
        result = float(val)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def extract_au_probabilities(au_input: Dict[Union[str, int], Any]) -> Tuple[Dict[str, float], float]:
    """Parse input AU mapping into standardized AU probabilities and calculate coverage ratio.

    Returns:
        (clean_map, coverage_ratio) where clean_map has normalized keys like 'AU06' with float values in [0, 1].
    """
    if not isinstance(au_input, dict):
        return {}, 0.0

    clean_map: Dict[str, float] = {}
    for k, v in au_input.items():
        norm_key = normalize_au_key(k)
        numeric_value = _finite_float(v)
        if numeric_value is not None:
            clean_map[norm_key] = max(0.0, min(1.0, numeric_value))

    # Calculate coverage of expected key AUs
    present_count = sum(1 for au in REQUIRED_AUS if au in clean_map)
    coverage_ratio = present_count / float(len(REQUIRED_AUS))

    return clean_map, coverage_ratio


def geometric_mean(values: Tuple[float, ...]) -> float:
    """Compute geometric mean of a tuple of probabilities in [0, 1].

    Formula: (p_1 * p_2 * ... * p_N) ** (1 / N)
    """
    if not values:
        return 0.0
    prod = 1.0
    for v in values:
        prod *= sanitize_probability(v)
        if prod == 0.0:
            return 0.0
    return math.pow(prod, 1.0 / len(values))


@dataclass
class ExpressionEvidence:
    """Observed facial expression-configuration evidence probabilities [0.0, 1.0].

    Note: These represent evidence for visual configuration patterns only,
    not internal emotions or psychological states.
    """
    smile_like: float = 0.0
    sad_like: float = 0.0
    anger_like: float = 0.0
    surprise_like: float = 0.0
    disgust_like: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "smile_like": self.smile_like,
            "sad_like": self.sad_like,
            "anger_like": self.anger_like,
            "surprise_like": self.surprise_like,
            "disgust_like": self.disgust_like,
        }


@dataclass
class FacialBehaviorIndices:
    """Bounded facial affect evidence indices and overall assessment.

    Attributes:
        facial_valence: Perceived valence evidence bounded in [-100.0, 100.0].
                        Positive = smile-like evidence, Negative = sad/anger/disgust evidence.
                        Surprise is neutral / non-negative.
        facial_activation: Perceived facial activation/arousal evidence bounded in [0.0, 100.0].
        confidence: Assessment confidence score bounded in [0.0, 100.0], reduced by missing AUs and low tracking quality.
        expression_evidence: Detailed heuristic expression-configuration evidence breakdown.
    """
    facial_valence: float = 0.0
    facial_activation: float = 0.0
    confidence: float = 0.0
    expression_evidence: ExpressionEvidence = field(default_factory=ExpressionEvidence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "facial_valence": self.facial_valence,
            "facial_activation": self.facial_activation,
            "confidence": self.confidence,
            "expression_evidence": self.expression_evidence.to_dict(),
        }


def calculate_expression_evidence(au_probs: Dict[str, float]) -> ExpressionEvidence:
    """Calculate geometric-aggregated heuristic configuration evidence from AU probabilities.

    Rules (Py-Feat DetectorV2 activation probabilities in [0, 1]):
    - Smile-like: AU06 + AU12 => (AU06 * AU12)^(1/2)
    - Sad-like: AU01 + AU04 + AU15 => (AU01 * AU04 * AU15)^(1/3)
    - Anger-like: AU04 + max(AU05, AU07) + AU23 => (AU04 * max(AU05, AU07) * AU23)^(1/3)
    - Surprise-like: AU01 + AU02 + AU05 + AU26 => (AU01 * AU02 * AU05 * AU26)^(1/4)
    - Disgust-like: max(AU09, AU10) => max(AU09, AU10)
    """
    p_au01 = au_probs.get("AU01", 0.0)
    p_au02 = au_probs.get("AU02", 0.0)
    p_au04 = au_probs.get("AU04", 0.0)
    p_au05 = au_probs.get("AU05", 0.0)
    p_au06 = au_probs.get("AU06", 0.0)
    p_au07 = au_probs.get("AU07", 0.0)
    p_au09 = au_probs.get("AU09", 0.0)
    p_au10 = au_probs.get("AU10", 0.0)
    p_au12 = au_probs.get("AU12", 0.0)
    p_au15 = au_probs.get("AU15", 0.0)
    p_au23 = au_probs.get("AU23", 0.0)
    p_au26 = au_probs.get("AU26", 0.0)

    smile = geometric_mean((p_au06, p_au12))
    sad = geometric_mean((p_au01, p_au04, p_au15))
    anger = geometric_mean((p_au04, max(p_au05, p_au07), p_au23))
    surprise = geometric_mean((p_au01, p_au02, p_au05, p_au26))
    disgust = max(p_au09, p_au10)

    return ExpressionEvidence(
        smile_like=smile,
        sad_like=sad,
        anger_like=anger,
        surprise_like=surprise,
        disgust_like=disgust,
    )


def calculate_indices(
    au_probabilities: Dict[Union[str, int], float],
    tracking_quality: float = 1.0,
    pose_quality: float = 1.0,
) -> FacialBehaviorIndices:
    """Calculate bounded Facial Behavior Indices from raw AU activation probabilities.

    Args:
        au_probabilities: Dict mapping AU identifiers (e.g., 'AU06' or 6) to probabilities in [0.0, 1.0].
        tracking_quality: Facial tracking quality multiplier in [0.0, 1.0].
        pose_quality: Head pose stability quality multiplier in [0.0, 1.0].

    Returns:
        FacialBehaviorIndices object containing valence [-100, 100], activation [0, 100],
        confidence [0, 100], and detailed expression evidence breakdown.
    """
    clean_au, coverage_ratio = extract_au_probabilities(au_probabilities)
    evidence = calculate_expression_evidence(clean_au)

    # Sanitize quality metrics
    t_qual = sanitize_probability(tracking_quality)
    p_qual = sanitize_probability(pose_quality)
    combined_quality = t_qual * p_qual

    # Facial Valence Evidence [-100.0, 100.0]
    # Positive contribution: smile_like
    # Negative contribution: max(sad_like, anger_like, disgust_like)
    # Surprise is non-negative and neutral regarding valence
    negative_evidence = max(evidence.sad_like, evidence.anger_like, evidence.disgust_like)
    raw_valence = 100.0 * (evidence.smile_like - negative_evidence)
    facial_valence = max(-100.0, min(100.0, raw_valence))

    # Facial Activation Evidence [0.0, 100.0]
    raw_activation = 100.0 * max(
        evidence.smile_like,
        evidence.sad_like,
        evidence.anger_like,
        evidence.surprise_like,
        evidence.disgust_like,
    )
    facial_activation = max(0.0, min(100.0, raw_activation))

    # Confidence Score [0.0, 100.0]
    # Penalized by low quality and missing AUs
    raw_confidence = 100.0 * combined_quality * coverage_ratio
    confidence = max(0.0, min(100.0, raw_confidence))

    return FacialBehaviorIndices(
        facial_valence=facial_valence,
        facial_activation=facial_activation,
        confidence=confidence,
        expression_evidence=evidence,
    )
