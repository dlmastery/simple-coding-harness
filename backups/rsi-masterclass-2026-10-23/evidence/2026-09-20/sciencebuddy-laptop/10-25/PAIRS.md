# Synthetic paired state

Four table values were read once and cached. The sequence M0/H0 → M0/H1 → M1/H1 → M1/H0 has invented scores 0.40 → 0.70 → 0.60 → 0.80. The best harness changes when the model label changes.

The model transition is a placeholder, not trained weights. The four evaluations are table lookups, not model executions. The re-selection step reuses the cached values rather than adding hidden evaluations. The table is fixed throughout.
