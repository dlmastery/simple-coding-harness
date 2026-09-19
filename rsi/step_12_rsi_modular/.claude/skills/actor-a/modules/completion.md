# Module: completion
- After FREEZE: `python ../tools/score_test.py --pack P --task T [--arm control] --recipe model=<m>,hyper=<h>,scale=<s>,encode=<e>,class_weight=<c>` once with the best recipe, then `python ../tools/scorecard.py --pack P --task T [--arm control]`.
- Answer in text with the arm, the best val_score, the test score and the fits used. Stop.
- Never run `score_test.py` before FREEZE, never twice.
