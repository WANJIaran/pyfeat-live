"""pyfeatlive_core.indices — Framework-neutral Facial Behavior Index extension module.

RESEARCH-ONLY DISCLAIMER:
This module provides a research-only framework for computing bounded, heuristic
facial behavior indices from Py-Feat DetectorV2 Action Unit (AU) activation probabilities.

It does NOT infer true internal mood, mental state, deception, psychiatric diagnosis, or intent.
All outputs represent strictly observed facial actions, expression-configuration evidence,
and perceived facial affect.
"""

from pyfeatlive_core.indices.heuristics import (
    ExpressionEvidence,
    FacialBehaviorIndices,
    calculate_indices,
    calculate_expression_evidence,
    normalize_au_key,
    extract_au_probabilities,
    REQUIRED_AUS,
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
from pyfeatlive_core.indices.dataframe import (
    INDEX_COLUMNS,
    augment_facial_behavior_dataframe,
)

__all__ = [
    "ExpressionEvidence",
    "FacialBehaviorIndices",
    "calculate_indices",
    "calculate_expression_evidence",
    "normalize_au_key",
    "extract_au_probabilities",
    "REQUIRED_AUS",
    "EWMAFilter",
    "DictEWMAFilter",
    "HysteresisThreshold",
    "NeutralBaselineCalibration",
    "indices_to_dict",
    "indices_from_dict",
    "indices_to_json",
    "indices_from_json",
    "INDEX_COLUMNS",
    "augment_facial_behavior_dataframe",
]
