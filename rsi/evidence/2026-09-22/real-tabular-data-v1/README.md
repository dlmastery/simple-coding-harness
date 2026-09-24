# A source exclusion caught before training

The first data preparation refused the auction schema mismatch. Its raw file
has an additional verification-outcome field that OpenML explicitly excludes.
The corrected loader honors that exclusion. No model was fitted in either
data preparation.

This archive retains 79 original files, including eight prepared tasks, nine
raw downloads, original source and the [failure record](FAILURE.md).
[The manifest](ARCHIVE-MANIFEST.csv) verifies their exact bytes.

Continue with [the corrected data panel](../real-tabular-data-v2/README.md).
