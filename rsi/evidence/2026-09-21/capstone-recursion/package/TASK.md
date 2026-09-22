# Predict white-wine quality after laboratory measurement

For one recorded Portuguese white-wine sample, estimate its original sensory quality score using eleven measured physicochemical inputs. This is a retrospective tabular regression benchmark. It is new relative to the course's red-wine binary classification question: different wine population, original target, and MAE instead of balanced accuracy.

All eleven measurements must be available when predicting. The target quality is forbidden as an input. Do not infer causation, future-vintage generalization, or commercial suitability. Quality is ordinal and subjective; MAE treats a one-point error consistently but does not establish equal perceived differences between score levels.

Use the pinned UCI white table. Assign identical numeric input vectors to the same partition using the feature-only SHA-256 rule in task.py. Fixed hash ranges allocate approximately 60% training, 20% selection, and 20% evaluation. Do not optimize the split. No time, producer, or subject grouping is available; the split cannot protect against all latent dependencies.

Start with the training median. Allowed later candidates are standardized Ridge(alpha=10), an unrestricted regression tree, and a forty-tree forest with minimum leaf size five. Tree seeds are 11001. These are bounded teaching choices, not tuned defaults. Fit every transform on training only. Report continuous predictions without clipping or rounding.

Primary metric: mean absolute error, lower is better. Propose and select on development evidence only. Keep final evaluation for a separately declared closing step; this package currently produces selection predictions only. Its public raw data remains readable to the host, so this is a procedural boundary, not secret evaluation.

The surrounding lab allocates the total budget. Each experiment freezes its own allocation at preparation, from one to eight attempts. Creating another workspace does not grant extra lab attempts. An admitted failure remains charged. Refused malformed requests consume no fit. Run one process at a time per workspace.
