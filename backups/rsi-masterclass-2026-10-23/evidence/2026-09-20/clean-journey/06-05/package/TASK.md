# Wine harness brief

Classify red-wine quality >= 7. Use physicochemical inputs only. Keep identical input vectors together using the pinned wine-v1 hash split. Fit preprocessing on training rows. Use balanced accuracy and both class recalls; larger balanced accuracy is better. Baseline: majority class; compare balanced logistic regression.

Use the repository-pinned UCI data and attribution. Allow two admitted attempts, including failures; refuse a third. Refuse changed task, metric, or split. Keep candidates, predictions, checks, failures, and measured costs. Default to CPU with sequential commands capped at 60 seconds. The data and evaluator are visible to the host agent. Students type ordinary language; the coding agent supplies code.
