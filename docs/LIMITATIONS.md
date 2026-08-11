# System Limitations, Safety Guardrails, and Disclaimers

> **IMPORTANT NOTICE**  
> The software, algorithms, and models provided in this repository are for **research exploration only**. They are NOT certified for medical, clinical, legal, law-enforcement, recruitment, or high-stakes decision-making applications.

---

## 1. Explicit Prohibitions & Scope Limits

### 🚫 Strictly Prohibited Claims
Under NO circumstances should outputs from `pyfeatlive_core.indices` or `pyfeat-live` be described as measuring or determining:
1. **True internal mood or emotional experience**
2. **Mental state or psychiatric condition**
3. **Deception, truthfulness, or credibility**
4. **Clinical diagnosis or psychological impairment**
5. **Future intent, motivation, or disposition**

### ✅ Approved Terminology
All system outputs, documentation, UI labels, and scientific reports MUST use precise descriptive terms:
- **Observed facial actions**
- **Action Unit activation probabilities**
- **Expression-configuration evidence**
- **Perceived facial affect evidence**

---

## 2. Technical and Algorithmic Limitations

### A. AU Activation Probabilities vs. FACS Intensities
Py-Feat DetectorV2 outputs Action Unit predictions as **activation probabilities** bounded in $[0.0, 1.0]$. They reflect model confidence in AU presence, **NOT** the physical FACS A–E intensity scale (where A = trace and E = maximum intensity). High activation probability does not necessarily imply extreme muscle displacement.

### B. Domain Shift & Demographic Variability
Pretrained vision models (including Py-Feat backbones) are subject to dataset bias and performance variation across:
- **Lighting & Exposure**: Shadows, uneven illumination, and extreme contrast affect landmark alignment and AU detection.
- **Head Pose & Occlusion**: Large pitch, yaw, or roll angles, as well as partial face occlusions (hair, glasses, hands, masks), can degrade AU estimation reliability. A deployment-specific validation set is needed before choosing a numeric pose cutoff.
- **Morphology & Demographics**: Variations in facial morphology, age, skin tone, and ethnic background can alter baseline appearance and model sensitivity.

### C. Heuristic Aggregation Nature
The geometric rules for smile-like, sad-like, anger-like, surprise-like, and disgust-like evidence are simplified heuristic proxies based on FACS literature. Facial expressions in naturalistic contexts are highly dynamic, ambiguous, and culturally variable (Barrett et al., 2019). Geometric evidence scores should be evaluated as rough visual configuration indicators rather than ground-truth emotion classifiers.

### D. Confidence Degradation
The computed `confidence` score penalizes outputs when tracking quality drops or when expected Action Units are missing from the detector output. Low confidence scores ($< 50.0$) indicate that indices should be disregarded or interpreted with extreme caution.
