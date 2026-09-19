# Tools

## Allowed
- load_splits, fit_recipe, read_memory, score_test, scorecard - the actor's tools, run as the actor pack on each arm
- read_traces, write_card - the verifier's tools, run for the verifier pack after each memory arm
- read_pack, patch_pack, rollback - the fast loop's tools, run for task-skills-meta after every problem
- curve, patch_pack - the slow loop's tools, run for meta-evolver every k problems
- curve - the learning curve over the curriculum
- exam - the exam report over the seeds

## Forbidden
- propose, apply - the meta pack patches, it does not generate
- save_model - the models are not the deliverable here
