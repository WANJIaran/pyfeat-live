# Implementation Plan - Facial Behavior Index Extension

## Overview
This plan defines a conservative, platform-independent, framework-neutral extension module `pyfeatlive_core.indices` for Py-Feat Live. It translates DetectorV2 Action Unit (AU) activation probabilities in $[0, 1]$ and tracking quality into heuristic expression-configuration evidence, facial valence evidence, facial activation evidence, and confidence scores.

## Key Design Principles & Guardrails
1. **Terminology Guardrails**: Never infer true mood, internal emotional state, deception, psychiatric diagnosis, or intent. All outputs are strictly named as observed facial actions, expression-configuration evidence, and perceived affect evidence.
2. **Platform Independence**: Standard Python standard library only (`math`, `dataclasses`, `typing`). No external native C dependencies, no downloading weights, no camera dependencies.
3. **Research-Only**: Pretrained models and heuristic rules are for research exploration only.
4. **Py-Feat AU Probabilities**: DetectorV2 outputs AU activation probabilities in $[0, 1]$, not FACS A-E intensities.

## Data Models & Package Layout
- `pyfeatlive_core/indices/__init__.py`: Package entrypoint exporting core classes and functions.
- `pyfeatlive_core/indices/heuristics.py`:
  - `ExpressionEvidence`: Dataclass holding evidence scores for `smile_like`, `sad_like`, `anger_like`, `surprise_like`, `disgust_like`.
  - `FacialBehaviorIndices`: Dataclass holding `valence` $[-100, 100]$, `activation` $[0, 100]$, `confidence` $[0, 100]$, and `expression_evidence`.
  - `calculate_indices(au_probabilities, tracking_quality, pose_quality)`: Main calculation function. Neutral calibration is an explicit preprocessing step through `NeutralBaselineCalibration`.
- `pyfeatlive_core/indices/smoothing.py`:
  - `EWMAFilter`: Exponentially Weighted Moving Average filter.
  - `HysteresisThreshold`: Dual-threshold logic for discrete state stabilization.
  - `NeutralBaselineCalibration`: Subject baseline subtraction/normalization logic.
- `pyfeatlive_core/indices/schema.py`:
  - Minimal, safe serialization helpers (`to_dict`, `from_dict`, JSON-serializable dict output).
- `tests/core/test_indices.py`: Comprehensive test suite.
- Documentation:
  - `docs/INDEX_DEFINITIONS.md`
  - `docs/PSYCHOLOGY_BASIS.md`
  - `docs/LIMITATIONS.md`
  - `THIRD_PARTY_LICENSES.md`

## Heuristic Aggregation Formulas
1. **AU Parsing**:
   Accepts keys such as `"AU01"`, `"AU1"`, `"01"`, `1` flexibly, returning probabilities bounded in $[0.0, 1.0]$.
2. **Geometric Means**:
   - $\text{smile\_like} = (p_{\text{AU06}} \cdot p_{\text{AU12}})^{1/2}$
   - $\text{sad\_like} = (p_{\text{AU01}} \cdot p_{\text{AU04}} \cdot p_{\text{AU15}})^{1/3}$
   - $\text{anger\_like} = (p_{\text{AU04}} \cdot \max(p_{\text{AU05}}, p_{\text{AU07}}) \cdot p_{\text{AU23}})^{1/3}$
   - $\text{surprise\_like} = (p_{\text{AU01}} \cdot p_{\text{AU02}} \cdot p_{\text{AU05}} \cdot p_{\text{AU26}})^{1/4}$
   - $\text{disgust\_like} = \max(p_{\text{AU09}}, p_{\text{AU10}})$
3. **Valence Evidence $[-100, 100]$**:
   - Positive component: $\text{smile\_like}$
   - Negative component: $\max(\text{sad\_like}, \text{anger\_like}, \text{disgust\_like})$
   - Note: Surprise is neutral / non-negative with respect to valence.
   - $\text{valence} = \text{clamp}(100 \times (\text{smile\_like} - \max(\text{sad\_like}, \text{anger\_like}, \text{disgust\_like})), -100.0, 100.0)$
4. **Activation Evidence $[0, 100]$**:
   - $\text{activation} = \text{clamp}(100 \times \max(\text{smile\_like}, \text{sad\_like}, \text{anger\_like}, \text{surprise\_like}, \text{disgust\_like}), 0.0, 100.0)$
5. **Confidence $[0, 100]$**:
   - Base quality: $\text{quality\_factor} = \text{clamp}(\text{tracking\_quality} \cdot \text{pose\_quality}, 0.0, 1.0)$
   - Missing AU coverage penalty: $\text{coverage\_ratio} = \frac{\text{present\_expected\_AUs}}{\text{total\_expected\_AUs}}$
   - $\text{confidence} = \text{clamp}(100 \times \text{quality\_factor} \times \text{coverage\_ratio}, 0.0, 100.0)$

## Linux Development, Windows Delivery

The numerical core stays operating-system independent and is tested on Linux first. The desktop deliverable will target Windows x86_64 using the existing Tauri 2 + Svelte frontend + FastAPI/Python sidecar architecture.

1. Add indices to the live-frame result schema without changing existing fields.
2. Add a front-end panel that labels all values as facial-behavior evidence, including confidence and quality warnings.
3. Add recorded-session replay tests so most behavior can be verified on Linux without a physical camera.
4. Build on `windows-2022` / `x86_64-pc-windows-msvc` and produce an NSIS Windows installer in CI. The release matrix and a pull-request/manual smoke workflow are configured; their first remote run remains an acceptance gate. Do not rely on Linux-to-Windows cross-compiling native Python/PyTorch dependencies.
5. Validate the CI artifact on a real Windows 10/11 x86_64 CPU machine: first launch, model download/cache, webcam permission, offline relaunch, and sustained frame rate.
6. Evaluate ONNX Runtime/DirectML only if the measured Windows CPU performance is insufficient; it is not part of the correctness baseline.
