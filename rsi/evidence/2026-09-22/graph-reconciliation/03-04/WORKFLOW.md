# Keep the repair rule fixed

Each report must contain the exact line Candidate: trial-001. The first check discovers its absence. A failed check routes to repair only if fewer than two repair slots are used. Reserve the next slot before editing, keep the failure feedback, then recheck with the same validator.

The effective fixture adds the candidate line and passes after one repair. The ineffective fixture changes only its title twice, remains invalid and exits with failure after two repairs. Five checks and three repairs occurred across the two fixtures. Both terminate; only one repairs the defect. REPORT-0/1/2 files and RESERVED records retain the intermediate states, and each trace records the same validator source hash.

This fixture aligns with the current lesson's report example. The earlier historical run repaired a CSV target column instead; it is preserved as a different teaching case. Neither case trains a model or changes a model score.
