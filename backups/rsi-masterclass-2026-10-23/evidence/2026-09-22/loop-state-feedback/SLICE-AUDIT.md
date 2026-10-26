# Measured slice audit

Both panels use recorded selection errors. Each hour has 176–182 rows; the overall MAE is row-weighted, not a simple average of the 24 hourly means. No new fit or causal effect is estimated.

- Model change: full weighted MAE 159.947911886 → 109.807667751; worse hours [6, 22, 23].
- Feature change: full weighted MAE 109.807667751 → 99.175923787; worse hours [2, 3, 4].

Historical model change: hour 8 remains weak at MAE 260.203781 despite improving from 324.076923. At hour 6 the linear model is worse: 59.489109 versus 47.972527. A lower full score does not mean every slice improved.

This 02.01 analysis is retrospective. The old PLAN.md fixes the compared recipes, but does not retain a pre-fit diagnostic note. Do not present this later explanation as proof that that note governed the historical choice. The new 02.03 feedback and decisions, in contrast, were saved before their new fits.
