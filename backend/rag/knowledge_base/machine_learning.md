# Machine Learning & Deep Learning Fundamentals

## Bias-Variance Tradeoff & Regularization
- High Bias leads to underfitting (model is too simple to capture patterns).
- High Variance leads to overfitting (model memorizes training noise and fails to generalize).
- Regularization techniques reduce model variance:
  - L1 Regularization (Lasso): Adds absolute value penalty; enforces sparsity (feature selection).
  - L2 Regularization (Ridge): Adds squared magnitude penalty; shrinks weights smoothly.
  - Dropout (Neural Networks): Randomly deactivates neurons during training to prevent co-adaptation.

## Gradient Descent & Optimizers
Gradient descent iteratively updates parameters in the direction of the negative loss gradient:
- Batch GD: Computes gradient across the entire dataset per update step.
- Stochastic GD (SGD): Updates parameters per individual training sample (noisy but fast).
- Mini-batch GD: Balances computation efficiency and gradient stability.
- Adaptive Optimizers (Adam, RMSprop): Dynamically adjust per-parameter learning rates based on first and second moments of gradients.

## Classification Evaluation Metrics
- Accuracy: Proportion of correct predictions (misleading on imbalanced datasets).
- Precision: TP / (TP + FP) — critical when false positives are costly (e.g. spam detection).
- Recall / Sensitivity: TP / (TP + FN) — critical when false negatives are dangerous (e.g. medical diagnosis).
- F1-Score: Harmonic mean of precision and recall.
- ROC-AUC: Evaluates classifier ranking capability across all probability thresholds.
