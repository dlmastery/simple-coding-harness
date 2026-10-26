# Executed graph and domain checks

| Check | Observed | Expected | Pass |
|---|---|---|---|
| 03.01 valid order | True | True | True |
| 03.01 check before fit | False | False | True |
| 03.02 valid.csv | valid: may proceed | valid: may proceed | True |
| 03.02 missing-target.csv | invalid: repair before fitting | invalid: repair before fitting | True |
| 03.02 absent.csv | unknown: stop and obtain evidence | unknown: stop and obtain evidence | True |
| 03.03 complete join | pass | pass | True |
| 03.03 missing result | incomplete | incomplete | True |
| 03.03 wrong candidate | mismatch | mismatch | True |
| 03.04 effective exit | True | True | True |
| 03.04 effective checks | 2 | 2 | True |
| 03.04 ineffective exit | False | False | True |
| 03.04 ineffective checks | 3 | 3 | True |
| 03.05 prediction reuse | 0004513ae666f36bcf4987e2b36944f1c4a8d79bf949ef09b788d0b95e6af93c | 0004513ae666f36bcf4987e2b36944f1c4a8d79bf949ef09b788d0b95e6af93c | True |
| 03.05 unchanged fit ledger | 33e495e789137568412e57a5e636e36a7df71d06bdb0f7d50f2e3b2a4ee9bcf0 | 33e495e789137568412e57a5e636e36a7df71d06bdb0f7d50f2e3b2a4ee9bcf0 | True |
| 03.05 split descendants | ['check', 'fit', 'report', 'split'] | ['check', 'fit', 'report', 'split'] | True |
| 03.05 changed bytes invalidate report | True | True | True |
| 04.04 ORIGINAL violations | 3 | 3 | True |
| 04.04 CORRECTED violations | 0 | 0 | True |
| 04.05 observed future weather | False | False | True |
| 04.05 earlier forecast release | True | True | True |
| 05.01 leaked fixture stops before fit | True | True | True |
| 05.01 no leaked fit recorded | 0 | 0 | True |
| 05.01 valid domain check | 0 | 0 | True |
| 05.01 baseline exit | 0 | 0 | True |
| 05.01 exactly one fit | 1 | 1 | True |
