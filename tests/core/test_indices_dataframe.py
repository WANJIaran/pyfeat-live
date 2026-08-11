import pandas as pd
import pytest

from pyfeatlive_core.indices import INDEX_COLUMNS, augment_facial_behavior_dataframe


def test_augment_dataframe_persists_replayable_indices():
    original = pd.DataFrame({
        "frame": [4],
        "face_idx": [0],
        "FaceScore": [0.9],
        "AU06": [0.8],
        "AU12": [0.8],
    })

    augmented = augment_facial_behavior_dataframe(original)

    assert not any(column in original.columns for column in INDEX_COLUMNS)
    assert all(column in augmented.columns for column in INDEX_COLUMNS)
    assert augmented.loc[0, "facial_valence_evidence"] == pytest.approx(80.0)
    assert augmented.loc[0, "facial_activation_evidence"] == pytest.approx(80.0)
    assert augmented.loc[0, "facial_behavior_confidence"] == pytest.approx(100 * 0.9 * 2 / 12)


def test_augment_dataframe_without_aus_remains_compatible():
    original = pd.DataFrame({"frame": [0], "FaceScore": [0.8]})
    augmented = augment_facial_behavior_dataframe(original)
    assert list(augmented.columns) == list(original.columns)
