# Fixed routes

| Task | Target type | Data card | Baseline | Metric | Required check |
|---|---|---|---|---|---|
| bike | regression | BIKE-DATA-CARD.md | training median | MAE | selection rows, target identity, leakage |
| wine | classification | WINE-DATA-CARD.md | training majority | balanced accuracy | grouped duplicate inputs, both class recalls |

Reject an unknown task. A missing or conflicting target type needs clarification before fitting. A fixed table selects procedures; it does not learn routing.
