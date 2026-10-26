# Match the training objective and check distance scaling

The root coding agent wrote this proposal after inspecting the completed
48-fit development portfolio. No reserved task or final prediction was read.
The previous goal turn was progress: it published that baseline and restored
the visible course maps. This proposal continues the method repair.

## Observations that motivate the change

On solar flare, the best portfolio selection MAE is 0.365629. The training
median is zero; applying it arithmetically to selection labels gives MAE
0.325926. Most fitted tree models optimize squared error, which targets a
conditional mean. Absolute error instead favors a conditional median.
The simple reference was missing from the eight-model portfolio. Add it to
future controls as well as this diagnostic; do not credit that omission as RSI.

Abalone's selected SVR reaches MAE 1.427318, while trees have large training
versus selection gaps. Auction's random forest is strong, at 443.365057 ms
MAE, despite a skewed target. Test objective alignment without assuming every
task needs a log transform. Optical digits reaches 0.985203 balanced accuracy;
standardizing each pixel can amplify low-variance pixels. Karhunen coefficients
may benefit from scaling. Test this difference rather than encode a dataset ID
in a decision rule. Chess uses categorical inputs, so numeric scaling changes
must be a no-op there.

A first no-fit diagnostic command failed on namedtuple indexing before printing
results; the corrected command read saved predictions and public partitions.
No model attempt or hidden trial occurred in that diagnostic.

## Four new attempts per development task

Classification: RBF SVC with numeric scaling omitted; a wider RBF kernel;
Extra Trees with minimum leaf size two; more regularized histogram boosting.
Regression: a fitted training-median reference; histogram boosting with
absolute-error loss; random forest with absolute-error criterion and larger
leaves; SVR with a narrower epsilon tube. Keep training-only preprocessing,
target standardization, seed 41, one thread and 30-second subprocess limit.
Exact definitions are in engine.py and the allocation in PLAN.csv.

This admits 24 attempts, four per task, from the existing maximum of 48
revision-development attempts. Each failure is charged. No retry or task
replacement. At most four further development attempts per task remain.
Retain the original engine unchanged as parent_engine.py in the execution
snapshot. Save training and selection predictions for independent checks.

## How to interpret the result

Compare new candidates with the best original candidate and the median
reference where applicable. Report native metrics and normalized loss.
This expanded development search has extra fits: its best-of-twelve score
is not an equal-budget procedure advantage. The parent is retained when a
proposal loses. Development informs a later bounded policy; no final
promotion or recursive-success claim is authorized by this stage.

After inspecting these outcomes, write one further concrete revision and
freeze its allocation before spending any remaining development attempts.
Later task-transfer comparisons must give conventional controls the median
reference and the same resources. They must test actual retained artifacts,
not simply change labels on the same candidate list.
