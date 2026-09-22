# Proposed ordinal wine harness: review only

Predict the recorded red-wine quality rating from physicochemical inputs. Retain the ordered raw rating instead of converting it to quality at least 7. Keep identical input vectors in one partition and inspect rating coverage before freezing a new evaluation design. Fit transformations on training rows only.

Before implementation, agree on the error cost. MAE in rating steps assumes comparable adjacent distances. An ordinal classification or weighted-agreement objective needs its own explicit definition. Inspect errors by rating and distance, not only binary class recall. Compare a declared simple baseline and one suitable ordinal candidate only after those choices and a new budget are approved by the task instructions.

This brief allocates zero fits and asks for review only. Do not generate a new performance claim, reuse the old binary evaluator, or choose the rating formulation after seeing candidate scores. The coding agent supplies any later implementation; the student states the scientific choices in ordinary language.
