# Change the wine question from a threshold to an ordered rating

The current red-wine classroom target is quality at least 7. Balanced accuracy gives equal weight to recall in the two derived classes. The raw quality rating is ordinal: ratings have an order, while treating each adjacent step as exactly equal distance is an additional modeling choice.

For the proposed ordinal task, retain the original quality ratings instead of thresholding them. Preserve identical-input groups across partitions, but inspect rating coverage and freeze any new split design before comparing models. Old binary predictions cannot be reinterpreted as ordinal predictions: both a 3 and a 6 had the same binary negative label.

Consider an ordinal model or a multiclass model with an explicit cost for distant mistakes. A numerical regressor is another proposal only if the distance assumption and conversion to supported ratings are declared. The agent would generate that adapter; students need not write it. The current binary classifier is not automatically an ordinal model.

Choose the metric from the intended error cost. MAE in rating steps is easy to interpret but assumes comparable adjacent distances. A rank-based or weighted-agreement measure answers a different question and needs its own definition and baseline. Report errors by rating and a confusion matrix; binary balanced accuracy alone no longer answers the new question. Do not compare a binary accuracy number directly with an ordinal MAE.

This is a task-change plan, not a trained ordinal experiment. It creates no new score, fitted model or claim that one model family will win.
