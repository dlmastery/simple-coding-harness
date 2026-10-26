# Compare improvers from the same start

Selected-method reading on 21 September 2026: [MetaRSI v2, sections 5.1 and 5.4, Figure 11](https://arxiv.org/html/2609.06396v2). No code or full experimental reproduction was completed.

The paper describes a term-2 comparison starting from the same released system. Original and revised improvers receive matched budgets and evaluation conditions. It reports average additional gains of 4.9 and 7.2 points, respectively. This comparison addresses improver quality more directly than comparing two successive systems with different starting capability.

Its five-term results distinguish cumulative totals from per-term gains. The reported increments decline on both paths while totals continue rising. Positive increments add to a total even when each addition is smaller. These source-reported results do not establish accelerating gains or unlimited improvement.

Our simulation shows a saved rule controlling later work. It has no measured later-task comparison between original and revised schedulers, no model training, and no empirical test of those paper-reported gains. The 100/50 classroom scores come entirely from our declared synthetic evaluator.
