# Improver v0

Generation 1: propose a tree with calendar fields. Generation 2: keep the retained model family and add observed weather.

Decision partition: training.
Minimum relative gain: 0.

Fit and check the parent and proposed task skills under equal resources. Promote a child only when its MAE on the named partition is strictly lower and its relative reduction reaches the minimum. Keep the parent on a tie. Preserve failures, rejected skills, hashes, and costs. Stop at the generation limit. The outer evaluator remains fixed.
