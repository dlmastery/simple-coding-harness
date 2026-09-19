# Tools

## Allowed
- load_splits, fit_recipe, skill_memory, score_test, scorecard - the actor's tools, run as the actor pack on each arm
- read_traces, skill_memory - the meta pack's tools, run for the meta pack after each memory arm
- curve - the learning curve over the curriculum
- exam - the exam report over the seeds

## Forbidden
- propose, apply, patch_pack, rollback - nothing changes the pack in this lesson but the meta pack's card updates
- save_model - the models are not the deliverable here
