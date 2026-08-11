# Facial Behavior Index Definitions (Research-Only First Draft)

> **RESEARCH-ONLY DISCLAIMER**  
> This document defines a research-only framework for calculating bounded facial behavior indices from facial Action Unit (AU) activation probabilities. These indices represent **observed facial action patterns** and **perceived facial affect evidence**, NOT internal psychological states.  
> **Strict Guardrails**: NEVER claim or infer true mood, mental state, deception, psychiatric diagnosis, or intent.

---

## 1. Overview & Inputs

The Facial Behavior Index framework processes Action Unit activation probabilities produced by Py-Feat DetectorV2 (or compatible framework-neutral facial analysis pipelines) along with tracking and pose quality indicators.

### Inputs
- **AU Activation Probabilities ($p_i \in [0.0, 1.0]$)**:
  Direct activation probabilities for Action Units (e.g., AU01, AU02, AU04, AU05, AU06, AU07, AU09, AU10, AU12, AU15, AU23, AU26).
  *Note*: Py-Feat DetectorV2 outputs represent activation probabilities in $[0.0, 1.0]$, **not** FACS A–E intensity codes.
- **Tracking Quality ($Q_{\text{track}} \in [0.0, 1.0]$)**: Face detection and landmark tracking confidence.
- **Pose Quality ($Q_{\text{pose}} \in [0.0, 1.0]$)**: Head pose stability score (penalizing extreme pitch/yaw/roll angles).

---

## 2. Expression-Configuration Evidence (Geometric Aggregation)

To aggregate co-occurring Action Units into heuristic expression-configuration evidence scores $E \in [0.0, 1.0]$, geometric aggregation is used to ensure all constituent AUs must be active simultaneously:

$$\text{GeometricMean}(p_1, \dots, p_N) = \left( \prod_{i=1}^{N} p_i \right)^{\frac{1}{N}}$$

### Configuration Formulas
1. **Smile-like Configuration Evidence ($E_{\text{smile}}$)**:
   $$E_{\text{smile}} = \left( p_{\text{AU06}} \cdot p_{\text{AU12}} \right)^{1/2}$$
2. **Sad-like Configuration Evidence ($E_{\text{sad}}$)**:
   $$E_{\text{sad}} = \left( p_{\text{AU01}} \cdot p_{\text{AU04}} \cdot p_{\text{AU15}} \right)^{1/3}$$
3. **Anger-like Configuration Evidence ($E_{\text{anger}}$)**:
   $$E_{\text{anger}} = \left( p_{\text{AU04}} \cdot \max(p_{\text{AU05}}, p_{\text{AU07}}) \cdot p_{\text{AU23}} \right)^{1/3}$$
4. **Surprise-like Configuration Evidence ($E_{\text{surprise}}$)**:
   $$E_{\text{surprise}} = \left( p_{\text{AU01}} \cdot p_{\text{AU02}} \cdot p_{\text{AU05}} \cdot p_{\text{AU26}} \right)^{1/4}$$
5. **Disgust-like Configuration Evidence ($E_{\text{disgust}}$)**:
   $$E_{\text{disgust}} = \max(p_{\text{AU09}}, p_{\text{AU10}})$$

---

## 3. Bounded Affect Evidence Indices

### Facial Valence Evidence ($V \in [-100.0, 100.0]$)
Measures the balance between positive and negative facial configuration evidence. Smile-like configurations contribute positively; sad, anger, and disgust configurations contribute negatively. **Surprise is non-negative** and neutral with respect to valence.

$$V = \text{clamp}\left(100 \times \left( E_{\text{smile}} - \max(E_{\text{sad}}, E_{\text{anger}}, E_{\text{disgust}}) \right), -100.0, 100.0\right)$$

### Facial Activation Evidence ($A \in [0.0, 100.0]$)
Measures the overall magnitude of observable facial expression configuration activity:

$$A = \text{clamp}\left(100 \times \max(E_{\text{smile}}, E_{\text{sad}}, E_{\text{anger}}, E_{\text{surprise}}, E_{\text{disgust}}), 0.0, 100.0\right)$$

### Confidence Score ($C \in [0.0, 100.0]$)
Reflects data quality and completeness. Missing AUs and degraded face tracking lower the confidence score:

$$C = \text{clamp}\left(100 \times Q_{\text{track}} \times Q_{\text{pose}} \times R_{\text{coverage}}, 0.0, 100.0\right)$$

where $R_{\text{coverage}} = \frac{\text{Present Required AUs}}{\text{Total Required AUs (12)}}$.

---

## 4. Signal Processing & Calibration Utilities

- **EWMA Smoothing**: Exponentially weighted moving average $y_t = \alpha x_t + (1 - \alpha) y_{t-1}$ ($\alpha \in (0, 1]$). It reduces frame-to-frame noise but introduces temporal lag when $\alpha < 1$.
- **Hysteresis Thresholding**: Dual-threshold state gate ($T_{\text{low}}, T_{\text{high}}$) to eliminate state chatter.
- **Neutral Baseline Calibration**: Optional subject-specific resting baseline subtraction:
  $$p'_i = \max\left(0.0, \frac{p_i - b_i}{1.0 - b_i}\right) \quad \text{for } b_i < 1.0$$

## 5. Live Application Integration

The live backend adds a `facial_behavior` object to each serialized face whenever AU probabilities are available. This is an additive API field containing `facial_valence`, `facial_activation`, `confidence`, and the expression-configuration evidence breakdown. The UI labels the panel **Facial behavior evidence** and warns users not to interpret low-confidence output or treat it as internal mood.

In the current live integration, detector `FaceScore` supplies tracking quality and AU coverage supplies completeness. Pose quality is held at `1.0` until the pipeline exposes a separately validated pose-quality measure; displayed confidence therefore must not be described as a calibrated probability of correctness.

New recordings and Analyze sessions persist the same values in additive FEX columns named `facial_valence_evidence`, `facial_activation_evidence`, `facial_behavior_confidence`, and `evidence_*_like`. The Viewer reconstructs the panel from these stored columns, so replay does not re-run inference and remains reproducible for the saved detector output.
