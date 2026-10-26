# Synthetic scheduling protocol

This protocol is written before execution. All jobs arrive at tick zero.
Two simulated workers have identical, fixed capabilities. Job durations,
setup costs, deadlines, and coordination overhead are invented inputs.
A tick is a simulation unit, not a measured second. No ML fit is run.

Lab 07.05 uses six jobs with durations 8, 1, 7, 1, 6, 1. Compare fixed
round-robin assignment with an idle worker taking the next queued job.
The optional counterexample adds three ticks of extra coordination per
dynamic assignment; fixed assignment has no extra overhead. This assumption
tests sensitivity and is not an estimate of a real scheduler's cost.

Lab 07.06 uses twelve one-tick jobs, with types A,A,B,B repeated three times.
A worker pays one setup tick initially and whenever its job type changes.
Compare FIFO, preference for the worker's previous type, and preference
for a randomly assigned history type with seed 17. There is no central
batch plan. Ties select the lower worker ID and then the earlier queued job.

Clustering is the fraction of consecutive jobs on the same worker with
equal types, pooled across workers. It is defined before examining traces.
Report makespan and maximum lateness separately. The optional paired
counterexample gives only the first two B jobs a deadline of tick 3.
All other deadlines are tick 100. There is no claim of optimal scheduling.

Every result must retain each job exactly once, preserve its duration and
constructed result, and avoid overlapping work on a worker. Learner
predictions and teach-back are untested because this is an author walkthrough.
