---
name: ml-data-science
description: Use only for ML/data-science tasks involving model training, evaluation, prediction, or statistical metrics.
---

Applicable only when task/grader evidence includes ML/model evaluation.

Check:
- target and metric definition
- train/validation/test separation
- leakage
- seed/reproducibility
- baseline metric
- class imbalance / sampling
- missing data handling
- feature preprocessing fit scope
- inference schema
- artifact/model persistence
- compute/time limits

Never optimize an unconfirmed metric.
Record randomness and seeds when reproducibility matters.
