# One proposed improver revision

Written after generation one's two fits and before either generation-two arm.

The fixed I0 improver retained the tree because training MAE was 0, versus ridge's 0.5765851464615885. Yet the tree's selection MAE was 0.6933867735470942, worse than ridge's 0.6092388935621454. The retained task recipe therefore rewards memorization in this case.

Change one instruction: rank candidate task recipes by selection MAE instead of training MAE. Keep order, model menu, strict-improvement rule, ties, features, seeds, external acceptance rule and final evaluation fixed. This edits the internal improver, not a model hyperparameter or the external definition of success. The author supplies the edit; the controller does not invent it.

Expected effect: I1 will reject a lower-training-error recipe when it has a higher selection error, and retain a better selection outcome than I0 within the same three-fit menu. A falsifying observation is that its retained recipe fails to beat I0 under the unchanged external rule. Final evaluation can still disagree with selection. Reusing one development task risks selection overfitting and does not establish transfer.

Generation two has six remaining fits: three per arm from identical saved tree task-skill bytes. This is candidate trial use; I1 has not been promoted. No extra fits, third generation, or post-final revision are allowed. If the external comparison rejects I1, retain I0 and preserve the unsuccessful edit.

The original rule is a deliberately weak teaching baseline. The model menu and the general overfitting failure are author-known. These facts limit any discovery or general effectiveness claim even if the measured outcome improves.
