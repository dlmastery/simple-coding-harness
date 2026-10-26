# A small confirmed estimator contribution

The selected forest/all recipe obtained MAE 98.031220506 on the full January–June 2012 selection period. The linear/all ablation obtained 99.175923787. Both checks passed. The difference is about 1.1447 rentals per hour, or 1.15% of the linear error. The declared strict-improvement rule retains forest/all at seed 17.

The comparison tests replacing the whole linear estimator with the supplied forest recipe while retaining the same inputs and preprocessing structure. It does not isolate which forest design choice caused the change. Its recorded fit-related time was 0.767477 seconds versus 0.078279 for linear. This small quality gain is not a claim of lower total cost.

Tree was not evaluated under the fuller conditions in this study. The forest's lower screen error and higher fuller error use different training and scoring periods, so those two numbers do not measure a performance regression under identical conditions. The original hypothesis about nonlinear representation remains only partly addressed by this recipe comparison.
