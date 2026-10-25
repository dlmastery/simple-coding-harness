# Eight recorded hours

These are the first eight source rows on 1 January 2011, inspected without fitting. Source row IDs are zero-based; instant is a separate original identifier.

| Source row | hr | temp (normalized) | casual | registered | cnt |
|---|---:|---:|---:|---:|---:|
| 0 | 0 | 0.24 | 3 | 13 | 16 |
| 1 | 1 | 0.22 | 8 | 32 | 40 |
| 2 | 2 | 0.22 | 5 | 27 | 32 |
| 3 | 3 | 0.24 | 3 | 10 | 13 |
| 4 | 4 | 0.24 | 0 | 1 | 1 |
| 5 | 5 | 0.24 | 0 | 1 | 1 |
| 6 | 6 | 0.22 | 2 | 0 | 2 |
| 7 | 7 | 0.2 | 1 | 2 | 3 |

hr identifies the recorded hour. cnt is the total number of rentals in that hour. casual and registered are the two component counts; their sum equals cnt in all eight rows. These outcome components must be excluded as prediction inputs.

The retained original UCI Readme describes temp as normalized Celsius temperature divided by 41. We preserve the normalized field and do not treat 0.24 as 0.24 degrees or infer a forecast from it. The recorded value is observed weather. See the repository DATA-CARD.md and unchanged original Readme for source context.

The original TASK.md already specifies the retrospective prediction, allowed calendar inputs, exclusions, MAE and chronological data roles. TOMORROW-NOON-TASK.md is a separate changed brief, not an edit to that executed contract.
