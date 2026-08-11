# Psychological Foundations and Scientific Rationale

> **RESEARCH-ONLY DISCLAIMER**  
> The Facial Behavior Index extension translates facial Action Unit (AU) activation probabilities into observable affect evidence. It relies on established affective computing and psychophysiological literature, adhering strictly to non-invasive, descriptive terminology.

---

## 1. Scientific Foundation & Core Frameworks

### Facial Action Coding System (FACS)
Developed by Ekman & Friesen, FACS taxonomizes human facial movements into individual Action Units (AUs) based on underlying facial muscle contractions. The present framework maps combinations of these AUs (such as cheek raiser AU06 and lip corner puller AU12) into heuristic configuration evidence.
- **Reference**: Ekman, P., & Friesen, W. V. (1978). *Facial Action Coding System*. Human Interaction Laboratory, University of California, San Francisco.
- **Stable Link**: [https://www.paulekman.com/facial-action-coding-system/](https://www.paulekman.com/facial-action-coding-system/)

### Circumplex Model of Affect (Russell, 1980)
The mapping into two dimensional dimensions—Facial Valence Evidence and Facial Activation Evidence—is directly inspired by James Russell's Circumplex Model of Affect. In this model, affective states are conceptualized along continuous neurophysiological dimensions of valence (pleasure–displeasure) and arousal/activation.
- **Reference**: Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.
- **DOI**: [https://doi.org/10.1037/h0077714](https://doi.org/10.1037/h0077714)

### Critical Epistemological Boundary: Barrett et al. (2019)
We explicitly incorporate the scientific consensus articulated by Barrett and colleagues: facial movements do not map 1-to-1 onto discrete internal emotional states or mental conditions across diverse contexts and cultures. Consequently, this library computes **observed facial expression configurations** and **perceived affect evidence**, avoiding any claims regarding internal emotional ground truth, mental state, deception, or intent.
- **Reference**: Barrett, L. F., Adolphs, R., Marsella, S., Martinez, A. M., & Pollak, S. D. (2019). Emotional Expressions Reconsidered: Challenges to Inferring Emotion From Human Facial Movements. *Psychological Science in the Public Interest*, 20(1), 1–68.
- **DOI**: [https://doi.org/10.1177/1529100619832930](https://doi.org/10.1177/1529100619832930)

---

## 2. Computational Toolkits & Datasets

### Py-Feat Toolbox
Py-Feat provides modern vision backbones (DetectorV2) for extracting AU probabilities, facial landmarks, and emotions. DetectorV2 models output AU activation probabilities in $[0.0, 1.0]$.
- **Reference**: Cheong, J. H., Jolly, E., Sul, S., & Chang, L. J. (2021). Py-Feat: Python Facial Expression Analysis Toolbox.
- **DOI**: [https://doi.org/10.31234/osf.io/256g4](https://doi.org/10.31234/osf.io/256g4) | **URL**: [https://py-feat.org](https://py-feat.org)

### OpenFace 2.0
OpenFace established benchmark methodologies for multi-task facial behavior analysis, including AU intensity and presence detection.
- **Reference**: Baltrusaitis, T., Zadeh, A., Lim, Y. C., & Morency, L. P. (2018). OpenFace 2.0: Facial Behavior Analysis Toolkit. *IEEE FG 2018*.
- **DOI**: [https://doi.org/10.1109/FG.2018.00019](https://doi.org/10.1109/FG.2018.00019)

### DISFA Database
Denver Intensity of Spontaneous Facial Action Database provides ground-truth FACS AU intensity coding for spontaneous facial expressions.
- **Reference**: Mavadati, S. M., Mahoor, M. H., Bartlett, K., Trinh, P., & Cohn, J. F. (2013). DISFA: Denver Intensity of Spontaneous Facial Action Database. *IEEE Transactions on Affective Computing*.
- **DOI**: [https://doi.org/10.1109/T-AFFC.2013.4](https://doi.org/10.1109/T-AFFC.2013.4)

### AffectNet Database
AffectNet is a large-scale database of facial expressions in the wild annotated with continuous valence and arousal values.
- **Reference**: Mollahosseini, A., Hasani, B., & Mahoor, M. H. (2017). AffectNet: A Database for Facial Expression, Valence, and Arousal Computing in the Wild. *IEEE Transactions on Affective Computing*.
- **DOI**: [https://doi.org/10.1109/TAFFC.2017.2740923](https://doi.org/10.1109/TAFFC.2017.2740923)

### Emognition Dataset
A multi-modal dataset facilitating continuous affect recognition research and physiological response validation.
- **Reference**: Kampman, O. P., et al. (2021). Emognition dataset: Wearable physiological and video dataset. *Scientific Data*.
- **DOI**: [https://doi.org/10.1038/s41597-021-00963-4](https://doi.org/10.1038/s41597-021-00963-4)
