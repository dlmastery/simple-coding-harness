# Tools

## Allowed
- load_splits - the problem's train / val splits, its profile and its budget
- skill_memory - action tags, and action need: select the cards for the situation and rewrite working.md
- fit_recipe - fits on train scored on val; counted against the budget of 24
- score_test - the locked test split, once, after FREEZE
- scorecard - the numbers of this arm

## Forbidden
- write_card, read_traces - this pack has no card verifier; the meta pack updates cards through skill_memory --action update
- propose, apply, patch_pack, rollback - only a meta pack changes this pack
