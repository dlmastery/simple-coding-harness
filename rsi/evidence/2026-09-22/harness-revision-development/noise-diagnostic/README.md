# Why the current tasks have little predictive headroom

This is a retrospective, privileged development diagnostic. It reconstructs the known generator's clean signal and noise for the six existing development tasks. No new task or model fit is created, and no final data is read. These signal values were not supplied to candidate builders.

For regression, the expected absolute Gaussian noise is 0.3 sqrt(2/pi) = 0.239365368. This is the population MAE of the known conditional median. Its realized error on a finite selection sample fluctuates; it is not a hard sample-level lower bound.

For classification, the diagnostic thresholds the noiseless signal at 0.25. It is a privileged reference, not an exact Bayes optimum for balanced accuracy. Class weighting and sampling affect that metric. Do not report it as an attainable learned baseline.

Mean parent-minus-privileged-reference normalized selection loss: 0.016685505.

The parent already represents the linear and pairwise parts of the grammar. The child mainly addresses the remaining smooth term. Read each raw score in DIAGNOSTIC.csv. A small average change is therefore compatible with a useful local feature correction. It does not justify lowering the already used gate, selecting only a favorable task, or calling this final evidence.

The next benchmark design needs documented functional diversity and sound controls, while keeping these failures and earlier exposed tasks as development evidence. Do not turn a stream of new seeds from this narrow grammar into a claim of broad RSI.
