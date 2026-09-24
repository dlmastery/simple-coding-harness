# Inspect both the action and the aggregate

With correct rewards, the probability of each rewarded action rises from 0.25 to about 0.274917. Expected true reward rises from 0.5 to 0.549834. Equal observed rewards give zero centered advantages and leave every probability at 0.25.

In the corrupted case, action 0 is incorrectly rewarded. Its probability rises to 0.263589 even though its declared true reward is zero. That is a wrong update direction for that action. However, expected true reward still rises to 0.527178 because the other rewards retain useful information. The corrupted update helps less than the correct-reward update; it does not make aggregate expected reward worse than the starting policy in this example.

The finite-difference and analytic gradients agree within 8e-11 in the three cases. Probabilities remain finite and sum to one. These checks establish the small calculation, not the correctness of its rewards or the quality of a scientific answer.

OBJECTIVE.md identifies the toy objective and missing training machinery. The larger-training plan is a draft only. No LLM checkpoint was trained or evaluated.
