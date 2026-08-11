"""DataFrame integration for persisted facial-behavior evidence columns."""

from typing import Any

from pyfeatlive_core.indices.heuristics import calculate_indices


INDEX_COLUMNS = (
    "facial_valence_evidence",
    "facial_activation_evidence",
    "facial_behavior_confidence",
    "evidence_smile_like",
    "evidence_sad_like",
    "evidence_anger_like",
    "evidence_surprise_like",
    "evidence_disgust_like",
)


def augment_facial_behavior_dataframe(frame: Any) -> Any:
    """Return a copy with persisted index columns when AU columns exist.

    The function intentionally uses the small DataFrame protocol needed here
    instead of importing pandas, keeping the numerical package lightweight.
    """
    if frame is None or not hasattr(frame, "columns") or not hasattr(frame, "iterrows"):
        return frame

    au_columns = [column for column in frame.columns if str(column).startswith("AU")]
    if not au_columns:
        return frame.copy()

    output = frame.copy()
    values = {column: [] for column in INDEX_COLUMNS}
    for _, row in frame.iterrows():
        tracking_quality = row.get("FaceScore", 0.0)
        result = calculate_indices(
            {column: row.get(column) for column in au_columns},
            tracking_quality=tracking_quality,
            pose_quality=1.0,
        )
        evidence = result.expression_evidence
        row_values = (
            result.facial_valence,
            result.facial_activation,
            result.confidence,
            evidence.smile_like,
            evidence.sad_like,
            evidence.anger_like,
            evidence.surprise_like,
            evidence.disgust_like,
        )
        for column, value in zip(INDEX_COLUMNS, row_values):
            values[column].append(value)

    for column in INDEX_COLUMNS:
        output[column] = values[column]
    return output
