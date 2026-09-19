# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile, its budget
- fit_recipe - the plan's experiments (or the static list on the control arm); counted against the budget of 24
- score_test - the locked test split, once, after FREEZE
- scorecard - the numbers of this arm

## Forbidden
- write_plan - the planner writes the plan, run for the planner pack
- read_memory - the cards are the planner's input, not yours: you run experiments
- write_card, read_traces - the verifier's tools
- propose, apply, patch_pack, rollback - nothing patches this pack in this lesson
