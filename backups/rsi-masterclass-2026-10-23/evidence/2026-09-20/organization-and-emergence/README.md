# Organization and emergence walkthrough

Actual execution of an explicitly synthetic simulation. No student participated,
no worker is a coding-agent process, and no model or improvement rule learns.
The agent wrote and ran the implementation for the course activities.

Read [the prespecified protocol](PROTOCOL.md), [results](RESULTS.csv), and
the per-case event CSVs in this directory. The input CSVs retain every job.

| Case | Completion tick | Same-type fraction | Maximum lateness |
|---|---:|---:|---:|
| organization-fixed | 21 | 1.00 | 0 |
| organization-dynamic | 14 | 1.00 | 0 |
| organization-overhead | 23 | 1.00 | 0 |
| emergence-fifo | 12 | 0.00 | 0 |
| emergence-local | 8 | 0.80 | 0 |
| emergence-random | 9 | 0.70 | 0 |
| urgent-fifo | 12 | 0.00 | 1 |
| urgent-local | 8 | 0.80 | 3 |

All eight cases passed identity, duration, result, and non-overlap checks.
Clustering is useful only for the typed-job cases. With one type in the first
three cases it is trivially 1.00 and says nothing about specialization.

The fixed assignment has loads 21 and 3. Dynamic assignment reaches tick 14;
adding the declared coordination cost moves it to tick 23. The workers did
not get better at their jobs. Only the dispatch arrangement changed.

Preference for recent job type produces longer runs of similar work. The
random-history and FIFO controls change that pattern. The urgent-job pair
shows why less total completion time does not guarantee less lateness.
These are consequences of the constructed inputs and local rules, not
measurements of a production scheduler or evidence of general intelligence.

Source: `how-did-i-generate-it/rsi/scripts/run-organization-walkthrough.py`

Source SHA-256: `2e1aea528ea7a4b568ba72633cce86d81be5de6516d401d9d2fadebb43cf63a6`

Python: 3.12.12; platform: Windows AMD64.

To repeat, ask the coding agent to run the saved driver with a new output
folder. The driver refuses to overwrite an existing evidence directory.
