# Module: completion
- After FREEZE, call `score_test` once with the best recipe, after FREEZE, then `save_model`.
- Answer in text with the best val_score, the test score and the fits used. Stop.
- Never call `score_test` before FREEZE, never twice.
