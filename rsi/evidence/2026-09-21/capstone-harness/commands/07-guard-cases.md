# 07-guard-cases

Executable: C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\simple-coding-harness\.venv\Scripts\python.exe

Arguments:

- C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\rsi-work-2026-09-21-capstone-harness\package\test_guards.py
- --baseline
- C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\rsi-work-2026-09-21-capstone-harness\baseline-run
- --output
- C:\Users\abhir\Documents\Codex\2026-09-19\lo\work\rsi-work-2026-09-21-capstone-harness\guard-cases

Exit: 0; signal: null; wall seconds: 2.3559827999999996.

```text
Prepared 4898 rows, 3961 input groups, budget 1.
                             case  passed                                                     observed
                    false-summary    True                           Summary disagrees with predictions
                        wrong-row    True       Missing, reordered, duplicate, or wrong partition rows
                     wrong-target    True                            Targets differ from pinned source
                        nonfinite    True                                        Non-finite prediction
                     wrong-metric    True                        Candidate identity or metric mismatch
                     wrong-recipe    True                          Recipe differs from charged attempt
                     split-change    True                                          Saved split changed
charged-failure-and-refused-retry    True one simulated failed attempt; retry refused; zero model fits

```
