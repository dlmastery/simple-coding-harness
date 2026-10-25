# Competition

{description}

# Data

The data is in ./input. Files:

{data_preview}

# Your task

Write one complete Python script that:
1. reads the data from ./input,
2. trains a model, holding out part of the training data to measure the competition metric,
3. prints the held-out metric on its own line as `VALIDATION_SCORE: <number>`,
4. writes predictions for the test set to ./submission/submission.csv in the format of the sample submission.

The script must finish within {timeout} seconds on a CPU.
Reply with the script in a single ```python block.
